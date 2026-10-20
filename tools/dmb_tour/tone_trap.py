# Content-aware trapping for tonal (grayscale-alpha) inks under a textured key (DMB Fall Tour 2026).
# Offline what-if, NOT in the engine.
#
# Rules (Sara 2026-10-20):
#  - each ink grows TRAP px (5 @300 ppi) under the key, ONLY where the key is solid line work:
#    key alpha == 255, after an opening (radius 2) that drops stipple, and 1 px back from any non-solid key
#    (line edges, paper specks inside lines) so a trap never peeks out at the far side or through a hole
#  - growth is step by step through solid key only (square trap), all inks at once, so a line between two
#    inks is split down the middle; an ink never grows into another ink or onto paper/highlights
#  - the grown pixels carry the ink's own tone and grain: each one copies the ink pixel mirrored across the
#    ink's edge (same distance inside), falling back to the nearest ink pixel
#  - nothing else changes (key, tones, paper showing through)
# Usage: python3 tone_trap.py LAYERDIR x0 y0 x1 y1 OUTDIR [trap_px]
import sys, json, os, numpy as np
from scipy import ndimage
LD = sys.argv[1]; X0, Y0, X1, Y1 = map(int, sys.argv[2:6]); OD = sys.argv[6]
TRAP = int(sys.argv[7]) if len(sys.argv) > 7 else 5
PAD = 3 * TRAP + 8
os.makedirs(OD, exist_ok=True)
Ls = json.load(open(f'{LD}/layers.json'))
INKS = [i for i, l in enumerate(Ls) if l['name'] in ('Orange', 'Light Red', 'Purple', 'Dark Red', 'Layer 1')]
KEY = [i for i, l in enumerate(Ls) if l['name'] == 'Black/keyline'][0]
x0, y0, x1, y1 = X0 - PAD, Y0 - PAD, X1 + PAD, Y1 + PAD

def crop(i, c):
    l, t, r, b = Ls[i]['bbox']; out = np.zeros((y1 - y0, x1 - x0), np.uint8)
    f = f'{LD}/L{i}_{c}.npy'
    if not os.path.exists(f): return out
    a = np.load(f, mmap_mode='r')
    ya, yb, xa, xb = max(y0, t), min(y1, b), max(x0, l), min(x1, r)
    if ya < yb and xa < xb: out[ya-y0:yb-y0, xa-x0:xb-x0] = a[ya-t:yb-t, xa-l:xb-l]
    return out

K = crop(KEY, -1)
A = {i: crop(i, -1) for i in INKS}
RGB = {i: np.stack([crop(i, c) for c in range(3)], -1) for i in INKS}
lab = np.zeros(K.shape, np.int16)
for k, i in enumerate(INKS): lab[A[i] > 0] = k + 1
cross = ndimage.generate_binary_structure(2, 1)
solid = K == 255
lines = ndimage.binary_opening(solid, structure=cross, iterations=2)
allowed = ndimage.binary_erosion(lines, structure=np.ones((3, 3), bool)) & (lab == 0)
# the soft (anti-aliased) edge of a key line on the INK side: key >= 50%, touching solid line work, within
# 2 px of the ink - otherwise a 2 px key shift opens a hairline there. Never the far side of a line.
nearink = ndimage.binary_dilation(lab > 0, structure=np.ones((3, 3), bool), iterations=2)
soft = (K >= 128) & (lab == 0) & nearink & ndimage.binary_dilation(lines, structure=np.ones((3, 3), bool))
allowed |= soft

# simultaneous square growth through allowed pixels, TRAP steps
own = lab.copy(); step = np.zeros(K.shape, np.uint8)
for s in range(1, TRAP + 1):
    free = allowed & (own == 0)
    best = np.zeros(K.shape, np.int16); bestn = np.zeros(K.shape, np.int16)
    for k in range(1, len(INKS) + 1):
        nk = ndimage.convolve((own == k).astype(np.int16), np.ones((3, 3), np.int16), mode='constant')
        better = free & (nk > bestn)
        best[better] = k; bestn[better] = nk[better]
    new = free & (best > 0)
    own[new] = best[new]; step[new] = s
trap = (own > 0) & (lab == 0)

# tone / grain: mirror across the ink edge, fallback nearest ink pixel
TA = {i: np.zeros(K.shape, np.uint8) for i in INKS}; TRGB = {i: np.zeros(K.shape + (3,), np.uint8) for i in INKS}
mirrored = 0; fallback = 0
for k, i in enumerate(INKS):
    m = trap & (own == k + 1)
    if not m.any(): continue
    _, (iy, ix) = ndimage.distance_transform_edt(lab != k + 1, return_indices=True)
    py, px = np.nonzero(m); qy, qx = iy[py, px], ix[py, px]
    sy, sx = 2 * qy - py, 2 * qx - px
    ok = (sy >= 0) & (sy < K.shape[0]) & (sx >= 0) & (sx < K.shape[1])
    ok[ok] = lab[sy[ok], sx[ok]] == k + 1
    sy = np.where(ok, sy, qy); sx = np.where(ok, sx, qx)
    TA[i][py, px] = A[i][sy, sx]; TRGB[i][py, px] = RGB[i][sy, sx]
    mirrored += int(ok.sum()); fallback += int((~ok).sum())

c = (slice(PAD, PAD + (Y1 - Y0)), slice(PAD, PAD + (X1 - X0)))
np.save(f'{OD}/trap_owner.npy', own[c] * trap[c]); np.save(f'{OD}/trap_step.npy', step[c] * trap[c])
for i in INKS:
    np.save(f'{OD}/T{i}_-1.npy', TA[i][c]); np.save(f'{OD}/T{i}_rgb.npy', TRGB[i][c])
log = dict(box=[X0, Y0, X1, Y1], trap_px=TRAP, inks=[Ls[i]['name'] for i in INKS],
           trap_pixels={Ls[i]['name']: int((TA[i][c] > 0).sum()) for i in INKS},
           mirrored=mirrored, fallback=fallback,
           allowed_px=int(allowed[c].sum()), solid_px=int(solid[c].sum()))
json.dump(log, open(f'{OD}/log.json', 'w'), indent=1); print(json.dumps(log, indent=1))
