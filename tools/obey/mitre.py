# Offline what-if (NOT in the engine): joint-mitre cleanup under the KEY for square-trap runs
# (Sara 2026-10-19: Round traps OFF, follow-visible OFF, trap 5 px @300 -> 12 px under key @600).
#
# What Sara does by hand (her before/after screenshots of the top-left frame):
#  1. Joints: where colours A and B share an edge that runs into the key, the trap zone under the key is
#     split along the continuation of the A|B edge (A's trap ends on its own edge line = mitred end).
#     Only near the joint (zone ~2 trap widths); further along each colour keeps its own trap.
#  2. Corners: trap corners are crisp and square (no bevel) - bare key pixels inside a colour's square
#     trap band, where that colour is the only nearby colour, are filled.
#  3. Dots: loose specks of a colour's key trap, cut off from its own colour and already covered by another
#     colour, are removed.
#  4. No doubled ink: a pixel is never in two layers of the same colour.
# Only pixels under the key change; what prints visibly (top-most colour) cannot change.
#
# Usage: python3 mitre.py LDIR OUTDIR    (LDIR from layr_read.py + labels.npy in cwd)
import sys, json, numpy as np
from scipy import ndimage
LD, OD = sys.argv[1], sys.argv[2]
W, H = 9600, 12000
D = 12                 # trap depth under key (measured: chessboard depth 1..12)
MIN_ANGLE = 25         # degrees between a colour edge and the key edge needed for a mitre
names = ['Yellow', 'Cream', 'Red', 'Light Blue', 'Blue', 'Dark blue']
KID = 7
Ls = json.load(open(f'{LD}/layers.json')); idx = {l['name']: l['index'] for l in Ls}
ld = lambda i: np.unpackbits(np.load(f'{LD}/m_{i}.npy'))[:W*H].reshape(H, W).astype(bool)
L = np.load('labels.npy'); K = L == KID
TR = {n: ld(idx[f'TRAP__COLOR__{n}_under_Key']) for n in names}
CL = {n: ld(idx[f'CLEAN__COLOR__{n}']) for n in names}

log = []

def fitline(Q):
    c = Q.mean(0); _, _, vt = np.linalg.svd(Q - c); return c, vt[0], vt[1]

# ---------- 1. joints ----------
nearK = ndimage.binary_dilation(K, iterations=3)
isC = (L >= 1) & (L <= 6)
J = np.zeros((H, W), bool); pair = np.zeros((H, W), np.uint8)
for dy, dx in ((0, 1), (1, 0)):
    a = L[:H-dy, :W-dx]; b = L[dy:, dx:]
    m = isC[:H-dy, :W-dx] & isC[dy:, dx:] & (a != b) & nearK[:H-dy, :W-dx]
    J[:H-dy, :W-dx] |= m; pair[:H-dy, :W-dx][m] = (np.minimum(a, b)*10 + np.maximum(a, b))[m]
del nearK
lab, nj = ndimage.label(ndimage.binary_dilation(J, iterations=2))
cents = []
for s in ndimage.find_objects(lab):
    jy, jx = np.nonzero(J[s])
    if len(jy) == 0: continue
    pv = np.bincount(pair[s][J[s]]).argmax()
    cents.append((jx.mean() + s[1].start, jy.mean() + s[0].start, pv // 10, pv % 10))
del J, pair, lab
# one joint can show up as 2 pieces a few px apart (pixel steps) - merge same-pair pieces within one trap width
merged = []
for c_ in cents:
    for mm in merged:
        if mm[2:] == list(c_[2:]) and np.hypot(mm[0] - c_[0], mm[1] - c_[1]) <= D:
            mm[0], mm[1] = (mm[0] + c_[0]) / 2, (mm[1] + c_[1]) / 2; break
    else:
        merged.append(list(c_))
cents = [tuple(m_) for m_ in merged]
print('key joints found', len(cents), flush=True)
C = np.array([[c[0], c[1]] for c in cents])
zones = np.zeros((H, W), bool)          # where the joint pass was allowed to work (for the checks)
for k, (jx, jy, a, b) in enumerate(cents):
    A, B = names[a-1], names[b-1]
    others = np.delete(C, k, 0)
    R = 2.0 * D
    if len(others): R = min(R, max(6.0, np.hypot(*(others - [jx, jy]).T).min() / 2))
    pad = 60
    x0, y0 = int(max(0, jx - pad)), int(max(0, jy - pad)); x1, y1 = int(min(W, jx + pad)), int(min(H, jy + pad))
    gx, gy = jx - x0, jy - y0
    Ls_ = L[y0:y1, x0:x1]; Kb = Ls_ == KID; SA = Ls_ == a; SB = Ls_ == b
    pts = []
    for dy, dx in ((0, 1), (1, 0)):
        h, w = SA.shape
        m = (SA[:h-dy, :w-dx] & SB[dy:, dx:]) | (SB[:h-dy, :w-dx] & SA[dy:, dx:])
        ys, xs = np.nonzero(m); pts.append(np.stack([xs + dx/2, ys + dy/2], 1))
    Q0 = np.vstack(pts).astype(float); dq = np.hypot(Q0[:, 0] - gx, Q0[:, 1] - gy)
    Q = Q0[dq < 14]
    yy, xx = np.mgrid[0:y1-y0, 0:x1-x0]
    mode = 'mitre'
    if len(Q) < 8: mode = 'nearest-short-edge'
    else:
        c, dirv, nrm = fitline(Q)
        if float(np.abs((Q - c) @ nrm).max()) > 1.0: mode = 'nearest-curved'
    disk = Kb & (np.hypot(xx - gx, yy - gy) <= 6)
    if not disk.any(): log.append([A, B, int(jx), int(jy), 'skip-no-key', 0]); continue
    if mode == 'mitre':
        # the edge must meet the key edge at >= MIN_ANGLE (25 deg, Sara 2026-10-20; was 45). Below that the
        # trap end would run more than ~2 trap widths along the key -> gentle cleanup instead.
        dK = ndimage.distance_transform_edt(Kb)
        gyy, gxx = np.gradient(ndimage.gaussian_filter(dK, 1.5))
        nv = np.array([gxx[disk].mean(), gyy[disk].mean()])
        if np.hypot(*nv) < 1e-6 or abs(float(dirv @ (nv / max(np.hypot(*nv), 1e-9)))) < np.sin(np.radians(MIN_ANGLE)):
            mode = 'nearest-shallow'
    TA, TB = TR[A][y0:y1, x0:x1], TR[B][y0:y1, x0:x1]
    CA, CB = CL[A][y0:y1, x0:x1], CL[B][y0:y1, x0:x1]
    if not (TA | CA)[Kb].any() or not (TB | CB)[Kb].any():
        log.append([A, B, int(jx), int(jy), 'skip-one-has-no-key-trap', 0]); continue
    # zone: key pixels near the joint, in the A/B square trap band, closer to A or B than to any 3rd colour
    dAB = ndimage.distance_transform_cdt(~(SA | SB), metric='chessboard')
    oth = (Ls_ >= 1) & (Ls_ <= 6) & ~SA & ~SB
    dO = ndimage.distance_transform_edt(~oth) if oth.any() else np.full(SA.shape, 1e9)
    dABe = ndimage.distance_transform_edt(~(SA | SB))
    Z = Kb & (np.hypot(xx - gx, yy - gy) < R) & (dAB <= D) & (dABe < dO)
    if mode == 'mitre':
        side = (xx - c[0]) * nrm[0] + (yy - c[1]) * nrm[1]
        near = np.hypot(xx - gx, yy - gy) < 14
        if (side[SA & near]).mean() < 0: side = -side
        sideA = side >= 0
    else:
        # shallow / curved / short joints: no line (it could hand a long wedge to one colour). Keep the
        # trapper's own idea - each pixel to the nearer colour - and smooth away single-pixel flips/dots.
        dA = ndimage.distance_transform_edt(~SA); dB = ndimage.distance_transform_edt(~SB)
        sideA = dA < dB
        tie = dA == dB
        sideA[tie] = ((TA | CA) & ~(TB | CB))[tie]
        for _ in range(2):
            nA = ndimage.convolve((sideA & Z).view(np.uint8), np.ones((3, 3), np.uint8), mode='constant')
            nZ = ndimage.convolve(Z.view(np.uint8), np.ones((3, 3), np.uint8), mode='constant')
            sideA = np.where(Z & (nA * 2 > nZ + 1), True, np.where(Z & (nA * 2 < nZ - 1), False, sideA))
    bandA = ndimage.distance_transform_cdt(~SA, metric='chessboard') <= D
    bandB = ndimage.distance_transform_cdt(~SB, metric='chessboard') <= D
    U0 = (TA | TB | CA | CB) & Z
    S = np.zeros_like(Z); wband = 0.0
    if mode == 'mitre':
        NA = (U0 | (bandA & Z)) & sideA & Z
        NB = (U0 | (bandB & Z)) & ~sideA & Z
        # "blue line" (Sara 2026-10-20): A is the LOWER colour; where A traps under B (band of A ink inside
        # B along their edge), A's band carries on under the key at the same angle, to the key trap depth.
        # B (upper) still ends on its own edge line; under the key they overlap by the band width, as above it.
        bn = f'TRAP__COLOR__{A}_under_COLOR__{B}'
        if bn in idx:
            Pb = np.load(f'{LD}/m_{idx[bn]}.npy', mmap_mode='r')
            BA = np.unpackbits(np.asarray(Pb[y0*(W//8):y1*(W//8)])).reshape(y1-y0, W)[:, x0:x1].astype(bool)
            dj = np.hypot(xx - gx, yy - gy)
            ring = BA & ~ndimage.binary_dilation(Kb, iterations=3) & (dj >= 4) & (dj <= 24) & (side < 0)
            if ring.sum() >= 10:
                wband = float(np.percentile(-side[ring], 90))
                S = Kb & (side < 0) & (side >= -wband - 0.5) & (dAB <= D) & (dj <= 3 * D) & (dABe < dO)
                NA = NA | S
    else:
        # conservative: keep solid overlap (no trap taken away); remove only slivers/dots (< 5 px wide)
        # of one colour sitting on the other colour's side; fill bare pixels on each colour's own side.
        curA, curB = (TA | CA) & Z, (TB | CB) & Z
        st = np.ones((5, 5), bool)
        thinA = curA & ~sideA & ~ndimage.binary_opening(curA, st)
        thinB = curB & sideA & ~ndimage.binary_opening(curB, st)
        NA = (curA & ~thinA) | (thinB & ~curA) | (bandA & Z & sideA & ~U0)
        NB = (curB & ~thinB) | (thinA & ~curB) | (bandB & Z & ~sideA & ~U0)
    nCA = (CA & ~Z) | (CA & NA); nCB = (CB & ~Z) | (CB & NB)
    nTA = (TA & ~Z) | (NA & ~nCA); nTB = (TB & ~Z) | (NB & ~nCB)
    ch = int((nTA != TA).sum() + (nTB != TB).sum() + (nCA != CA).sum() + (nCB != CB).sum())
    TR[A][y0:y1, x0:x1] = nTA; TR[B][y0:y1, x0:x1] = nTB
    CL[A][y0:y1, x0:x1] = nCA; CL[B][y0:y1, x0:x1] = nCB
    zones[y0:y1, x0:x1] |= Z
    zones[y0:y1, x0:x1] |= S
    log.append([A, B, int(jx), int(jy), mode, ch, round(wband, 1)])
from collections import Counter
print(Counter(l[4] for l in log), 'px changed', sum(l[5] for l in log), flush=True)
print('band carried into key at', sum(1 for l in log if len(l) > 6 and l[6] > 0), 'joints', flush=True)

# ---------- 2. square corners: fill bare key pixels in exactly one colour's square band ----------
cov = np.zeros((H, W), bool)
for n in names: cov |= TR[n] | CL[n]
paper = L == 0
dPaper = ndimage.distance_transform_cdt(~paper, metric='chessboard') if paper.any() else None
nb = np.zeros((H, W), np.uint8); band = {}
for i, n in enumerate(names):
    band[n] = ndimage.maximum_filter((L == i + 1).view(np.uint8), size=2*D + 1).astype(bool)
    nb += band[n]
farPaper = (dPaper > D + 2) if dPaper is not None else None; del dPaper
# real corners only: a non-key pixel on the key edge where the key wraps around it (non-key fills <= 1/3
# of a 13x13 window; a straight or gently curved edge is ~1/2). Fill only within the trap depth of those.
NK = (L != KID).view(np.uint8)
frac = ndimage.uniform_filter(NK.astype(np.float32), 13)
seed = (L != KID) & ndimage.binary_dilation(K, iterations=1) & (frac <= 0.33)
del frac, NK
cornerR = ndimage.maximum_filter(seed.view(np.uint8), size=2*D + 3).astype(bool)
print('corner seeds', int(seed.sum()), flush=True); del seed
corner = {}
for n in names:
    f = K & ~cov & band[n] & (nb == 1) & cornerR
    if farPaper is not None: f &= farPaper
    # only small pockets (bevelled corners / notches), never a long strip along an edge
    lab, k = ndimage.label(f, structure=np.ones((3, 3)))
    if k:
        sz = ndimage.sum(f, lab, range(1, k + 1))
        f &= np.isin(lab, 1 + np.nonzero(sz <= 4 * D)[0])
    corner[n] = f; TR[n] |= f
    print(n, 'corner px filled', int(f.sum()), 'pockets', int(ndimage.label(f, structure=np.ones((3,3)))[1]), flush=True)
del nb, band

# ---------- 3. loose dots ----------
cov = np.zeros((H, W), np.uint8)
for n in names: cov += (TR[n] | CL[n])
for i, n in enumerate(names):
    own = ndimage.binary_dilation(CL[n] | (L == i + 1), iterations=1)
    lab, k = ndimage.label(TR[n], structure=np.ones((3, 3)))
    if not k: continue
    touch = ndimage.maximum(own, lab, range(1, k + 1))
    sz = ndimage.sum(TR[n], lab, range(1, k + 1))
    cand = np.nonzero((~touch.astype(bool)) & (sz <= 200))[0] + 1
    rm = np.isin(lab, cand) & K
    others_cover = cov - (TR[n] | CL[n]) > 0
    keep = rm & ~others_cover          # removing these would leave bare key: keep them
    rm &= others_cover
    TR[n] &= ~rm
    print(n, 'loose dot px removed', int(rm.sum()), 'kept (would leave a gap)', int(keep.sum()), flush=True)
del cov

# ---------- 4. no doubled ink ----------
out = {}
for n in names:
    lays = [l for l in Ls if l['visible'] and l.get('pixels') and l['name'].split('__')[0] in ('CLEAN', 'TRAP')
            and l['name'].split('COLOR__')[1].split('_under_')[0] == n]
    seen = CL[n].copy()
    for l in lays:
        nm = l['name']
        if nm.startswith('CLEAN'): out[l['index']] = CL[n]; continue
        m = TR[n] if nm.endswith('_under_Key') else ld(l['index'])
        dup = m & seen
        if dup.any(): m = m & ~dup; print(nm, 'doubled px removed', int(dup.sum()))
        seen |= m; out[l['index']] = m
import os; os.makedirs(OD, exist_ok=True)
for i, m in out.items():
    if not np.array_equal(m, ld(i)):
        np.save(f'{OD}/m_{i}.npy', np.packbits(m)); print('changed layer', i, flush=True)
np.save(f'{OD}/zones.npy', np.packbits(zones))
json.dump(log, open(f'{OD}/joint_log.json', 'w'))
