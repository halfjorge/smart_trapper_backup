# Fix the bleed map (from bleed.py) in busy pattern areas (the Obey flower texture): there, every bleed pixel is
# a pure mirror of the art about the trim line (continuous at the trim), instead of a mix of mirrored pieces and
# straight-carried lines. Solid shapes crossing the pattern (yellow band, key stroke) stay carried straight.
# Rule per bleed pixel, in a pattern zone: straight source is a non-pattern colour -> keep straight;
#   else mirror source is pattern -> mirror; else keep straight.
# Usage: python3 bleed_pattern_fix.py bleed_map.npz labels.npy out_map.npz
import sys, numpy as np
from scipy import ndimage
mf, lf, outf = sys.argv[1:4]
z = np.load(mf); mp = {k: z[k] for k in z.files}
L = np.load(lf, mmap_mode='r'); H, W = L.shape
y0i, y1i, x0i, x1i = [int(v) for v in mp['box']]; Bt, Bb, Bl, Br = [int(v) for v in mp['Bs']]
PAT = (4, 5)                                     # Light Blue, Blue
I = np.asarray(L[y0i:y1i, x0i:x1i]); h, w = I.shape
DEPTH = max(Bt, Bb, Bl, Br) + 8

def zone(S):
    """S[k,t] labels k lines in from the edge. Pattern zone per t: busy light blue/blue texture."""
    lb = (S == 4).astype(np.float32); pt = np.isin(S, PAT).astype(np.float32)
    win = (1, 201)
    flb = ndimage.uniform_filter(lb, (S.shape[0], 201)).mean(0) if False else ndimage.uniform_filter1d(lb.mean(0), 201)
    fpt = ndimage.uniform_filter1d(pt.mean(0), 201)
    # busy: many light-blue/blue changes along the first 60 lines
    ch = (S[:60, 1:] != S[:60, :-1]) & np.isin(S[:60, 1:], PAT) & np.isin(S[:60, :-1], PAT)
    fch = ndimage.uniform_filter1d(np.concatenate([ch.mean(0), [0]]), 201)
    zt = (flb > 0.15) & (flb < 0.85) & (fpt > 0.8) & (fch > 0.006)
    return ndimage.binary_closing(zt, np.ones(101, bool)) & (fpt > 0.5)

def solid_carry(S, Bn):
    """Straight-carry map built ONLY from edges of solid (non-pattern) shapes, so pattern edges can't pin them."""
    n = S.shape[1]; e = S[0]
    cr = np.nonzero((e[1:] != e[:-1]) & (~np.isin(e[1:], PAT) | ~np.isin(e[:-1], PAT)))[0] + 1
    p = cr.astype(float); sl = np.zeros(len(p)); ok = np.zeros(len(p), bool)
    for i, c in enumerate(cr):
        a, b = e[c-1], e[c]; cur = float(c); pos = [(0, cur)]
        for k in range(1, min(40, S.shape[0])):
            lo, hi = int(max(1, cur - 3)), int(min(n - 1, cur + 4))
            cand = [u for u in range(lo, hi) if S[k][u-1] == a and S[k][u] == b]
            if not cand: break
            cur = float(min(cand, key=lambda u: abs(u - cur))); pos.append((k, cur))
        if len(pos) >= 10:
            ks = np.array([q[0] for q in pos]); ts = np.array([q[1] for q in pos])
            sl[i] = float(np.clip(np.polyfit(ks, ts, 1)[0], -3, 3)); ok[i] = True
    for i in np.nonzero(~ok)[0]:                  # untraced: borrow from the nearest traced solid edge
        j = np.nonzero(ok)[0]
        if len(j): sl[i] = sl[j[np.argmin(np.abs(p[j] - p[i]))]]
    M = np.zeros((Bn, n), np.int32); t = np.arange(n, dtype=float)
    for d in range(1, Bn + 1):
        if len(p):
            q = np.maximum.accumulate(p - sl * d)
            xs = np.concatenate([[q[0] - 1e6], q, [q[-1] + 1e6]]); ys = np.concatenate([[p[0] - 1e6], p, [p[-1] + 1e6]])
            M[d-1] = np.clip(np.rint(np.interp(t + 0.5, xs, ys) - 0.5), 0, n - 1)
        else: M[d-1] = t
    return M

def fix(M, Dp, S, name):
    Z = zone(S); n = S.shape[1]; t = np.arange(n); changed = 0
    if Z.any():
        M2 = solid_carry(S, M.shape[0])
        # widen the zone over any solid shape it touches (e.g. a key stroke half inside the texture) plus a
        # bleed-width margin, so the whole shape is carried by one map
        Zs = Z.copy(); e = S[0]; solid = ~np.isin(e, PAT)
        lab, k = ndimage.label(solid)
        touch = np.unique(lab[ndimage.binary_dilation(Z, np.ones(3, bool)) & solid])
        Zs |= np.isin(lab, touch[touch > 0])
        Zs = ndimage.binary_dilation(Zs, np.ones(2 * M.shape[0] + 21, bool)) & (Zs | ~solid | np.isin(lab, touch[touch > 0]))
        for d in range(1, M.shape[0] + 1):      # inside the (widened) zone, solid shapes follow their own edges
            M[d-1][Zs] = M2[d-1][Zs]; Dp[d-1][Zs] = 0
    else:
        Zs = Z
    fb = 0
    for d in range(1, M.shape[0] + 1):
        if d - 1 >= S.shape[0]: break
        st = S[Dp[d-1], M[d-1]]                  # straight-carried source label
        mi = S[d - 1]                            # mirrored source label
        use = Zs & np.isin(st, PAT) & np.isin(mi, PAT)
        changed += int((use & ((M[d-1] != t) | (Dp[d-1] != d - 1))).sum())
        M[d-1][use] = t[use]; Dp[d-1][use] = d - 1
        # mirror would reflect a solid shape (e.g. next to the yellow band): use the plain blue background
        # nearest along the same mirrored line instead of a straight-carried bit of pattern
        bad = Zs & np.isin(st, PAT) & ~np.isin(mi, PAT)
        if bad.any() and (mi == 5).any():
            _, (ix,) = ndimage.distance_transform_edt(mi != 5, return_indices=True)
            M[d-1][bad] = ix[bad]; Dp[d-1][bad] = d - 1; fb += int(bad.sum())
    print(name, 'background fallback px', fb)
    print(name, 'pattern zone px along edge', int(Z.sum()), 'bleed px switched to mirror', changed, flush=True)

# left / right: S[k, row] (k in from the edge)
SL = I[:, :DEPTH].T.copy(); SR = I[:, ::-1][:, :DEPTH].T.copy()
fix(mp['Ml'], mp['Dl'], SL, 'left'); fix(mp['Mr'], mp['Dr'], SR, 'right')
# top / bottom use the extended rows (after left/right bleed), exactly as bleed.py does
W2 = w + Bl + Br
def ext_row(yi):
    row = np.empty(W2, I.dtype); row[Bl:Bl + w] = I[yi]
    for d in range(1, Bl + 1): row[Bl - d] = I[mp['Ml'][d-1][yi], mp['Dl'][d-1][yi]]
    for d in range(1, Br + 1): row[Bl + w - 1 + d] = I[mp['Mr'][d-1][yi], w - 1 - mp['Dr'][d-1][yi]]
    return row
ST = np.array([ext_row(k) for k in range(DEPTH)]); SB = np.array([ext_row(h - 1 - k) for k in range(DEPTH)])
fix(mp['Mt'], mp['Dt'], ST, 'top'); fix(mp['Mb'], mp['Db'], SB, 'bottom')
np.savez(outf, **mp); print('saved', outf)
