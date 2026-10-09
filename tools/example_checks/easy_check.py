# Easy-file check: run the panel steps (Manual Progressive Knockout -> real engine) on a client
# "before" file with Sara's settings and measure the result; compare with the hand-trapped "after"
# file when there is one.
#   python3 easy_check.py <job dir with before/ [after/]> [--halo 0,2] [--no-mpk]
# Layers: bottom = paper, top = key (by position, not name). After-file layers are matched to
# before-file colours by ink colour, and the after file is aligned to the before file by its key.
import re, sys, os, json, shutil, subprocess, argparse
import numpy as np, cv2
from PIL import Image
ENGINE = '/home/claude/vend/build_new/target/release/smart_trapper_b1'
SARA = dict(preflightCleanup=True, alphaThreshold=89, edgeBiasPx=1, keyTrapPullbackPx=1,
            colorTrapPullbackPx=0, trapShape='round')
ap = argparse.ArgumentParser(); ap.add_argument('job'); ap.add_argument('--halo', default='0,2')
ap.add_argument('--no-mpk', action='store_true'); ap.add_argument('--trap', default='5'); ap.add_argument('--shape', default='round'); ap.add_argument('--tag', default='')
a = ap.parse_args(); job = a.job.rstrip('/'); SARA['trapShape'] = a.shape; TH = SARA['alphaThreshold']

def load(d):
    m = json.load(open(f'{d}/meta.json'))
    return [x[1] for x in m['layers']], [np.load(f'{d}/{i}.npy', mmap_mode='r') for i in range(len(m['layers']))], m['layers']
nb, lb, mb = load(f'{job}/before'); H, W = lb[0].shape[:2]
order = list(range(1, len(nb)))          # bottom -> top, paper excluded
key = order[-1]; cols = order[:-1]
alpha = {i: np.ascontiguousarray(lb[i][..., 3]) for i in order}
rgb = {i: np.ascontiguousarray(lb[i][..., :3]) for i in order}
def inkcol(L, al):
    m = al > 127
    return np.array([np.median(L[..., c][m]) for c in range(3)]) if m.any() else np.zeros(3)
colour = {i: inkcol(lb[i], alpha[i]) for i in order}
blend = {i: mb[i][2] for i in order}
print(f'== {job}: {W}x{H}, {len(cols)} colours + key "{nb[key]}"')
for i in cols: print(f'   {i}: {nb[i]:40s} rgb {tuple(int(v) for v in colour[i])} {blend[i]}')
if any('NORMAL' not in blend[i] for i in order): print('   NOTE: non-Normal blend present - not an easy file')

K = alpha[key] >= TH
inkB = {i: alpha[i] >= TH for i in cols}
def top_of(stack):   # visible colour index per pixel (0 = paper), key ignored
    t = np.zeros((H, W), np.int16)
    for i in cols: t[stack[i]] = i
    return t
client_top = top_of(inkB)

# --- hand-trapped after file (optional)
A = None
if os.path.exists(f'{job}/after/meta.json'):
    na, la, ma = load(f'{job}/after')
    aorder = list(range(1, len(na)))
    akey = aorder[-1]
    # align by key (phase correlation on 1/4 size)
    kb = cv2.resize(K.astype(np.float32), (W // 4, H // 4))
    ka_full = np.asarray(la[akey][..., 3]) > 127
    Ha, Wa = ka_full.shape
    pad = np.zeros((max(H, Ha), max(W, Wa)), np.float32); padb = pad.copy()
    padb[:H, :W] = K; pad[:Ha, :Wa] = ka_full
    s = 4; (dx, dy), _ = cv2.phaseCorrelate(cv2.resize(padb, (padb.shape[1] // s, padb.shape[0] // s)),
                                            cv2.resize(pad, (pad.shape[1] // s, pad.shape[0] // s)))
    ox, oy = int(round(dx * s)), int(round(dy * s))
    best = None
    for ddy in range(-s, s + 1):         # refine to the pixel on the key
        for ddx in range(-s, s + 1):
            X, Y = ox + ddx, oy + ddy
            y0, x0 = max(Y, 0), max(X, 0); y1, x1 = min(Y + H, Ha), min(X + W, Wa)
            if y1 <= y0 or x1 <= x0: continue
            sub = ka_full[y0:y1, x0:x1]; ref = K[y0 - Y:y1 - Y, x0 - X:x1 - X]
            sc = (sub ^ ref).mean()
            if best is None or sc < best[0]: best = (sc, X, Y)
    _, ox, oy = best
    def crop(arr):
        out = np.zeros((H, W), arr.dtype)
        y0, x0 = max(oy, 0), max(ox, 0); y1, x1 = min(oy + H, Ha), min(ox + W, Wa)
        out[y0 - oy:y1 - oy, x0 - ox:x1 - ox] = arr[y0:y1, x0:x1]
        return out
    key_mismatch = (crop(ka_full) ^ K).mean() * 100
    print(f'   after file aligned at offset ({ox},{oy}); key differs on {key_mismatch:.3f}% of pixels')
    A = {}; used = set()
    for j in aorder[:-1]:
        aj = np.asarray(la[j][..., 3]) > 127
        if not aj.any(): continue
        c = inkcol(la[j], np.asarray(la[j][..., 3]))
        d = {i: np.abs(colour[i] - c).sum() for i in cols}
        i = min(d, key=d.get)
        if d[i] > 60: print(f'   after layer "{na[j]}" rgb {tuple(int(v) for v in c)} matches no client colour - ignored'); continue
        A[i] = A.get(i, np.zeros((H, W), bool)) | crop(aj)
        used.add(i)
    for i in cols:
        if i not in A: print(f'   client colour "{nb[i]}" not found in after file'); A[i] = np.zeros((H, W), bool)

# --- Manual Progressive Knockout (top-down, selection = alpha >= threshold); key stays
ko = {}
above = K.copy()
for i in reversed(cols):
    al = alpha[i].copy()
    if not a.no_mpk: al[above] = 0
    ko[i] = al; above |= alpha[i] >= TH

def run(halo):
    out = f'{job}_run{halo}'; shutil.rmtree(out, ignore_errors=True); os.makedirs(out + '/masks')
    def save(al, path, c):
        x = np.zeros((H, W, 4), np.uint8); x[..., :3] = c.astype(np.uint8); x[..., 3] = al
        Image.fromarray(x).save(path, compress_level=1)
    names = {i: f'c{i}_{re.sub(r"[^A-Za-z0-9]", "_", nb[i])[:30]}' for i in cols}
    files = [dict(kind='KEY', name='KEY', blendMode='normal', opacity=100, fillOpacity=100, png='masks/KEY.png')]
    save(alpha[key], out + '/masks/KEY.png', colour[key])
    cl = []
    for i in cols:
        save(ko[i], f'{out}/masks/{i}.png', colour[i])
        files.append(dict(kind='COLOR', name=names[i], blendMode='normal', opacity=100, fillOpacity=100, png=f'masks/{i}.png'))
        cl.append(dict(name=names[i], blendMode='normal', opacity=100, fillOpacity=100))
    j = dict(docName=job, widthPx=W, heightPx=H, resolution=300, keyLayerName='KEY', paperLayerName='paper',
             colors=cl, files=files, closeKeyHaloPx=halo, **SARA)
    json.dump(j, open(out + '/job.json', 'w'))
    r = subprocess.run([ENGINE, out, a.trap], capture_output=True, text=True)
    if r.returncode: print(r.stdout[-800:], r.stderr[-800:]); sys.exit(1)
    T = json.load(open(out + '/traps.json'))['traps']
    inv = {v: k for k, v in names.items()}
    clean = {i: np.array(Image.open(f'{out}/clean_masks/CLEAN__{names[i]}.png'))[..., 3] > 0 for i in cols}
    final = {i: clean[i].copy() for i in cols}
    for t in T:
        if t['source'] in inv: final[inv[t['source']]] |= np.array(Image.open(out + '/' + t['png']))[..., 3] > 0
    shutil.rmtree(out, ignore_errors=True)
    return final

k3 = np.ones((3, 3), np.uint8)
notK = ~K
def measure(final, label):
    vis = top_of(final)
    ch = (vis != client_top) & notK
    filled = ch & (client_top == 0); lost = ch & (vis == 0); swapped = ch & ~filled & ~lost
    # butt joins: an upper visible colour pixel next to a visible lower colour, where the lower
    # colour does not run underneath it (outside the key)
    butt = np.zeros((H, W), bool)
    for i in cols:
        vi = (vis == i)
        near = cv2.dilate(vi.astype(np.uint8), k3).astype(bool)
        butt |= near & (vis > i) & ~final[i] & notK
    # trap at an open edge: hidden ink of colour i touching paper or a lower colour (outside key)
    #   - this is where a trap would peek out if the covering colour moves (rule 10 / Byrne)
    open_edge = np.zeros((H, W), bool)
    for i in cols:
        hid = final[i] & (vis > i) & notK
        if not hid.any(): continue
        low = ((vis < i) & notK).astype(np.uint8)
        open_edge |= hid & cv2.dilate(low, k3).astype(bool)
    # paper hairlines: paper pixels (outside key) closed by a 1 px closing of all ink incl. key
    anyink = K.copy()
    for i in cols: anyink |= final[i]
    hair = cv2.morphologyEx(anyink.astype(np.uint8), cv2.MORPH_CLOSE, k3).astype(bool) & ~anyink
    # how far lower colours run under what covers them (trap width)
    widths = []
    for i in cols:
        vi = vis == i
        under = final[i] & ~vi
        if not under.any() or not vi.any(): continue
        d = cv2.distanceTransform((~vi).astype(np.uint8), cv2.DIST_L2, 5)
        w = d[under & (d < 40)]
        if len(w): widths.append(w)
    w = np.concatenate(widths) if widths else np.zeros(1)
    ink = sum(int(final[i].sum()) for i in cols)
    return dict(label=label, filled=int(filled.sum()), lost=int(lost.sum()), swapped=int(swapped.sum()),
                butt=int(butt.sum()), hair=int(hair.sum()), oedge=int(open_edge.sum()), w50=float(np.median(w)), w90=float(np.percentile(w, 90)),
                ink=ink), butt

res = []
if A is not None:
    r, _ = measure(A, 'hand (after file)'); res.append(r)
fin = {}
for h in [int(x) for x in a.halo.split(',')]:
    fin[h] = run(h)
    r, butt = measure(fin[h], f'trapper, key halo {"on" if h else "off"}'); res.append(r)
    np.save(f'{job}_butt{h}{a.tag}.npy', butt)
print(f'   {"":28s} {"visible change vs client (outside key)":>44s} | {"butt px":>8s} {"trap@open edge":>14s} | trap width p50/p90 | total ink px')
print(f'   {"":28s} {"paper->ink":>12s} {"ink->paper":>11s} {"colour swap":>12s}      |')
for r in res:
    print(f'   {r["label"]:28s} {r["filled"]:>12,} {r["lost"]:>11,} {r["swapped"]:>12,}      | {r["butt"]:>8,} {r["oedge"]:>14,} | {r["w50"]:5.1f} / {r["w90"]:4.1f}      | {r["ink"]:,}')
if A is not None:
    for h, F in fin.items():
        hidden_t = sum(int((F[i] & (top_of(F) != i)).sum()) for i in cols)
        hidden_h = sum(int((A[i] & (top_of(A) != i)).sum()) for i in cols)
        mo = sum(int((A[i] & ~F[i]).sum()) for i in cols); to = sum(int((F[i] & ~A[i]).sum()) for i in cols)
        fl = (top_of(F) != client_top) & notK & (client_top == 0)
        if fl.any():
            ag = (fl & (top_of(A) > 0)).sum()
            print(f'   halo {h}: paper filled by trapper {fl.sum():,} px, hand file also has ink there in {ag:,} ({ag/fl.sum()*100:.0f}%)')
        print(f'   vs hand (halo {h}): hidden ink trapper {hidden_t:,} vs hand {hidden_h:,}; ink only in hand {mo:,}, only in trapper {to:,}')
json.dump(res, open(f'{job}_check.json', 'w'), indent=1)
