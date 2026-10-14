# "Cut back" what-if (Sara 2026-10-14, Ocean): start from the client layers exactly as they are;
#  - remove a colour's ink only where it is more than DEPTH px inside the key or inside a SOLID
#    (>=95%, non-overlay) colour above it; the first DEPTH px are never touched; values never change
#  - "big gray" layers (mostly gradient) are left completely alone
#  - overlays don't cover anything (but are cut back themselves)
#  - fill real client butts: an EMPTY key px within DEPTH px of a visible colour (and not next to
#    paper) gets that colour, at the value of its nearest visible pixel
import sys, os, json, numpy as np, cv2
EX, OUT = sys.argv[1], sys.argv[2]; DEPTH = float(os.environ.get('DEPTH', 5)); TH = 90
BIGGRAY = float(os.environ.get('BIGGRAY', 0.5))
m = json.load(open(f'{EX}/before/meta.json')); L = m['layers']
PAPER = [int(x) for x in os.environ.get('PAPER_LAYERS', '0').split(',')]
order = [l[0] for l in L if l[0] not in PAPER]; key = order[-1]; cols = order[:-1]
names = {l[0]: l[1] for l in L}; opac = {l[0]: (l[4] if len(l) > 4 else 255) / 255 for l in L}
ov = {i: opac[i] < 0.999 or 'NORMAL' not in L[i][2] for i in order}
al = {i: np.ascontiguousarray(np.load(f'{EX}/before/{i}.npy', mmap_mode='r')[..., 3]) for i in order}
K = al[key] >= TH; H, W = K.shape
big = {}
for i in cols:
    part = ((al[i] > 0) & (al[i] < 243)).astype(np.uint8)
    gray = (part > 0) & (cv2.blur(part.astype(np.float32), (5, 5)) >= 0.6)
    big[i] = gray.sum() / max(1, (al[i] > 0).sum()) > BIGGRAY
    print(f'{names[i]!r}: gray {100*gray.sum()/max(1,(al[i]>0).sum()):.0f}%' + ('  BIG GRAY - left alone' if big[i] else '') + ('  OVERLAY' if ov[i] else ''))
out = {}
for i in cols:
    a = al[i].copy()
    if not big[i]:
        cover = K.copy()
        for j in cols:
            if j > i and not ov[j]: cover |= al[j] >= 243
        depth = cv2.distanceTransform(cover.astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        cut = (a > 0) & (depth > DEPTH)
        a[cut] = 0
        print(f'  {names[i]!r}: cut back {int(cut.sum()):,} px (deeper than {DEPTH:g} px under the key / solid colours above)')
    out[i] = a
# butt fill under the key
vis = np.zeros((H, W), np.int16); val = np.zeros((H, W), np.uint8)
for i in cols:
    if ov[i]: continue
    s = out[i] >= TH; vis[s] = i; val[s] = out[i][s]
V = np.where(K, -1, vis)
src = (V == -1).astype(np.uint8)
dist, lab = cv2.distanceTransformWithLabels(src, cv2.DIST_L2, cv2.DIST_MASK_PRECISE, labelType=cv2.DIST_LABEL_PIXEL)
zy, zx = np.nonzero(src == 0)
lutc = np.zeros(lab.max() + 1, np.int16); lutc[lab[zy, zx]] = V[zy, zx]
lutv = np.zeros(lab.max() + 1, np.uint8); lutv[lab[zy, zx]] = val[zy, zx]
own = lutc[lab]; ownv = lutv[lab]; del lab
dpap = cv2.distanceTransform((V != 0).astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
anyink = np.zeros((H, W), bool)
for i in cols:
    if not ov[i]: anyink |= out[i] >= TH
empty = K & ~anyink & (dist <= DEPTH) & (dpap > 1.5) & (own > 0)
traps = {}
for i in cols:
    t = np.zeros((H, W), np.uint8); sel = empty & (own == i); t[sel] = ownv[sel]
    traps[i] = t
    if sel.any(): print(f'  {names[i]!r}: filled {int(sel.sum()):,} empty key px next to it (client butt)')
os.makedirs(OUT, exist_ok=True)
np.savez_compressed(OUT + '/result.npz', **{f'clean_{i}': out[i] for i in cols}, **{f'trap_{i}_0': traps[i] for i in cols})
json.dump({str(i): ['KEY'] for i in cols}, open(OUT + '/result_targets.json', 'w'))
print('done')
