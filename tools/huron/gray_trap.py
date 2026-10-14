# Offline what-if for files with grays (gradients that the RIP halftones), Huron 2026-10-13.
# Not in the app. Steps:
#  1. per colour layer: solid (>=95%), soft edge (thin rim), GRAY (patch of in-between values)
#  2. knockout (MPK) as the panel does it, except gray parts and overlays (pink) don't cut
#  3. real engine with Sara's settings; grays count as ink for it (so their edges get traps)
#  4. after: CLEAN keeps the gray values; traps carry the value of the nearest own pixel;
#     no colour's trap stays under a GRAY part of a colour above (it would show between dots)
import sys, os, re, json, shutil, subprocess, numpy as np, cv2
from PIL import Image
EX, OUT = sys.argv[1], sys.argv[2]           # extracted job dir (before/), work dir
ENGINE = os.environ.get('ENGINE', '/home/claude/vend/build_new/target/release/smart_trapper_b1')
SET = dict(preflightCleanup=True, alphaThreshold=90, edgeBiasPx=0, keyTrapPullbackPx=1, colorTrapPullbackPx=0,
           trapShape='round', closeKeyHaloPx=0, overlayMode=True, smoothKeyTraps=True, bevelKeyCorners=True,
           keyTrapsFollowVisible=True)
TH = SET['alphaThreshold']
m = json.load(open(f'{EX}/before/meta.json')); L = m['layers']
PAPER = [int(x) for x in os.environ.get('PAPER_LAYERS', '0').split(',')]
order = [l[0] for l in L if l[0] not in PAPER]; key = order[-1]; cols = order[:-1]
names = {l[0]: l[1] for l in L}; opac = {l[0]: (l[4] if len(l) > 4 else 255) / 255 for l in L}
ov = {i: opac[i] < 0.999 or 'NORMAL' not in L[i][2] for i in order}
raw = {i: np.load(f'{EX}/before/{i}.npy', mmap_mode='r') for i in order}
H, W = raw[key].shape[:2]
alpha = {i: np.ascontiguousarray(raw[i][..., 3]) for i in order}
def inkcol(i):
    a = np.asarray(raw[i][::8, ::8]); s = a[..., 3] > 240
    return np.median(a[..., :3][s], axis=0).astype(np.uint8)
colour = {i: inkcol(i) for i in order}
# 1. gray = in-between values that fill a patch (not a 1-2 px rim)
gray = {}
for i in cols:
    part = ((alpha[i] > 0) & (alpha[i] < 243)).astype(np.uint8)
    gray[i] = (part > 0) & (cv2.blur(part.astype(np.float32), (5, 5)) >= 0.6)
    print(f'{names[i]!r}: gray {100*gray[i].sum()/max(1,(alpha[i]>0).sum()):.1f}% of its ink' + ('  OVERLAY' if ov[i] else ''))
# 2. knockout, top down; gray parts and overlays don't cut (the key always cuts)
cur = {i: alpha[i].copy() for i in order}
for s in reversed(order):
    if s != key and ov[s]: continue
    sel = cur[s].copy()
    if s != key: sel[gray[s]] = 0
    for d in order:
        if d >= s: continue
        for y0 in range(0, H, 512):
            c = cur[d][y0:y0+512].astype(np.uint16)
            cur[d][y0:y0+512] = ((c * (255 - sel[y0:y0+512].astype(np.uint16)) + 127) // 255).astype(np.uint8)
# 3. engine; gray px still present after knockout count as solid ink for the engine
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT + '/masks')
nm = {i: f'c{i}_' + re.sub(r'[^A-Za-z0-9]', '_', names[i]).strip('_')[:30] for i in cols}
def save(al, path, c):
    x = np.zeros((H, W, 4), np.uint8); x[..., :3] = c; x[..., 3] = al; Image.fromarray(x).save(path, compress_level=1)
save(alpha[key], OUT + '/masks/KEY.png', colour[key])
files = [dict(kind='KEY', name='KEY', blendMode='normal', opacity=100, fillOpacity=100, png='masks/KEY.png')]; cl = []
for i in cols:
    eng = cur[i].copy(); eng[gray[i] & (cur[i] > 0)] = 255
    save(eng, f'{OUT}/masks/{i}.png', colour[i])
    d = dict(name=nm[i], blendMode=L[i][2].split('.')[-1].lower(), opacity=round(opac[i]*100), fillOpacity=100)
    cl.append(d); files.append(dict(kind='COLOR', png=f'masks/{i}.png', **d))
json.dump(dict(docName='Huron', widthPx=W, heightPx=H, resolution=300, keyLayerName='KEY', paperLayerName='paper',
               colors=cl, files=files, **SET), open(OUT + '/job.json', 'w'))
r = subprocess.run([ENGINE, OUT, '5'], capture_output=True, text=True); open(OUT + '/engine.log', 'w').write(r.stdout + r.stderr)
if r.returncode: print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(1)
# 4. gray-aware layers
T = json.load(open(OUT + '/traps.json'))['traps']; inv = {v: k for k, v in nm.items()}
gray_above = {i: np.zeros((H, W), bool) for i in cols}
for i in cols:
    for j in cols:
        if j > i and not ov[j]: gray_above[i] |= gray[j] & (cur[j] > 0) & (cur[j] < 243)   # after knockout (none under the key)
Kin = alpha[key] >= TH
for i in cols: gray_above[i] &= ~Kin   # under the key the key hides it: traps there stay
res = {}
for i in cols:
    c = np.array(Image.open(f"{OUT}/clean_masks/CLEAN__{nm[i]}.png"))[..., 3] > 0
    ca = np.where(c, 255, 0).astype(np.uint8)
    g = gray[i] & (cur[i] > 0); ca[g] = cur[i][g]           # keep the gray value
    # nearest own pixel (clean incl. grays) -> value carried by traps
    src = (ca == 0).astype(np.uint8)
    _, lab = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    zy, zx = np.nonzero(src == 0); lut = np.zeros(lab.max() + 1, np.uint8); lut[lab[zy, zx]] = ca[zy, zx]
    near = lut[lab]; del lab, lut, zy, zx
    traps = []
    for t in T:
        if inv.get(t['source']) != i: continue
        tm = np.array(Image.open(OUT + '/' + t['png']))[..., 3] > 0
        cut = tm & gray_above[i]; tm &= ~gray_above[i]
        ta = np.where(tm, near, 0).astype(np.uint8)
        traps.append((t['target'], ta, int(cut.sum())))
    res[i] = (ca, traps)
    print(f"{names[i]!r}: gray px kept as tones {int(g.sum()):,} | traps: " + ', '.join(f"under {tg} {int((ta>0).sum()):,} (removed under grays {cu:,})" for tg, ta, cu in traps))
np.savez_compressed(OUT + '/result.npz', **{f'clean_{i}': res[i][0] for i in cols},
                    **{f'trap_{i}_{k}': ta for i in cols for k, (tg, ta, cu) in enumerate(res[i][1])})
json.dump({str(i): [tg for tg, _, _ in res[i][1]] for i in cols}, open(OUT + '/result_targets.json', 'w'))
print('done')
