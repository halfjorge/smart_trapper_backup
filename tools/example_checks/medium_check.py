# Medium-file check (overlay layers: Multiply / Darken / under 100% opacity).
# Runs today's panel steps on a client "before" file - Manual Progressive Knockout (optional) and the
# real engine with Sara's settings - and compares BLEND-AWARE composites (what the print looks like
# with all layers on) against the client file. Also measures Sara's hand-trapped after file the same way.
#
#   python3 medium_check.py <job dir with before/ [after/]>   (dirs made by extract.py)
#   env ENGINE=<path to smart_trapper_b1>   (default: the cloud build kit)
#
# Composite model (8-bit, per layer bottom -> top, a = layer alpha * opacity):
#   Normal:   out = out*(1-a) + c*a
#   Multiply: out = out*(1-a) + (out*c/255)*a
#   Darken:   out = out*(1-a) + min(out,c)*a
# Every layer is drawn in its single ink colour (median of its solid pixels), so differences come
# from shape and blend changes only, not from colour noise in the client art.
#
# Scenarios for the trapper result:
#   "blend kept": CLEAN__/TRAP__ layers keep the overlay's blend mode (what rule 3 needs).
#   "blend lost": CLEAN__/TRAP__ layers come in Normal 100% (what Prepare Import's code reads like:
#                 new layers are made with no blend mode, inside a pass-through group).
import re, sys, os, json, shutil, subprocess, argparse
import numpy as np, cv2
from PIL import Image

ENGINE = os.environ.get('ENGINE', '/home/claude/vend/build_new/target/release/smart_trapper_b1')
SARA = dict(preflightCleanup=True, alphaThreshold=89, edgeBiasPx=1, keyTrapPullbackPx=1,
            colorTrapPullbackPx=0, trapShape='round', closeKeyHaloPx=0)
ap = argparse.ArgumentParser(); ap.add_argument('job'); ap.add_argument('--trap', default='5')
ap.add_argument('--diff', type=int, default=12, help='visible change = any channel differs by more than this (0-255)')
ap.add_argument('--keep', action='store_true', help='keep the engine job folders')
ap.add_argument('--overlay', action='store_true', help="simulate the panel box 'File has transparent / overlay layers' ticked: MPK skips overlay cutters, engine overlayMode on")
ap.add_argument('--paper', default='', help='override paper colour r,g,b (e.g. 255,255,255) - the paper layer is only a screen preview')
a = ap.parse_args(); job = a.job.rstrip('/')
TH = SARA['alphaThreshold']; DIFF = a.diff
if a.overlay: SARA['overlayMode'] = True

def load(d):
    m = json.load(open(f'{d}/meta.json'))
    L = m['layers']
    return [x[1] for x in L], [np.load(f'{d}/{i}.npy', mmap_mode='r') for i in range(len(L))], L

def mode_of(meta):          # extract.py meta: (index, name, 'BlendMode.X', inkpx[, opacity, fill])
    s = str(meta[2]).upper()
    for k in ('MULTIPLY', 'DARKEN', 'NORMAL'):
        if k in s: return k
    return s
def opac_of(meta):
    op = meta[4] if len(meta) > 4 else 255; fl = meta[5] if len(meta) > 5 else 255
    return (op / 255.0) * (fl / 255.0)

nb, lb, mb = load(f'{job}/before'); H, W = lb[0].shape[:2]
order = list(range(1, len(nb)))          # bottom -> top, paper (0) excluded
key = order[-1]; cols = order[:-1]
alpha = {i: np.ascontiguousarray(lb[i][..., 3]) for i in order}
def inkcol(L, al):
    m = np.asarray(al) > 127
    if not m.any(): return np.zeros(3)
    return np.array([np.median(np.asarray(L[..., c])[m]) for c in range(3)])
colour = {i: inkcol(lb[i], alpha[i]) for i in order}
paper_rgb = np.array([float(v) for v in a.paper.split(',')]) if a.paper else inkcol(lb[0], np.full((H, W), 255, np.uint8))
mode = {i: mode_of(mb[i]) for i in order}
opac = {i: opac_of(mb[i]) for i in order}
overlay = {i: (mode[i] != 'NORMAL' or opac[i] < 0.999) for i in order}
print(f'== {job}: {W}x{H}, paper rgb {tuple(int(v) for v in paper_rgb)}')
for i in order:
    print(f'   {i}: {nb[i]:24s} rgb {tuple(int(v) for v in colour[i])}  {mode[i]:8s} opacity {opac[i]*100:.0f}%'
          f'{"  OVERLAY" if overlay[i] else ""}{"  (key)" if i == key else ""}')

# ---------------- composite (row chunks, to keep memory low on big files)
def composite(layers):
    """layers: list of (alpha HxW uint8 or bool, rgb(3,), mode, opacity) bottom->top over paper."""
    out = np.empty((H, W, 3), np.uint8)
    CH = 512
    for y0 in range(0, H, CH):
        y1 = min(H, y0 + CH)
        o = np.empty((y1 - y0, W, 3), np.float32); o[:] = paper_rgb
        for al, c, md, op in layers:
            A = np.asarray(al[y0:y1])
            A = (A.astype(np.float32) * (255.0 if A.dtype == bool else 1.0) / 255.0 * op)[..., None]
            c = np.asarray(c, np.float32)
            if md == 'MULTIPLY': top = o * c / 255.0
            elif md == 'DARKEN': top = np.minimum(o, c)
            else: top = np.broadcast_to(c, o.shape)
            o = o * (1 - A) + top * A
        out[y0:y1] = np.clip(o + 0.5, 0, 255).astype(np.uint8)
    return out

def client_layers():
    return [(alpha[i], colour[i], mode[i], opac[i]) for i in order]
CLIENT = composite(client_layers())

# soft-edge zone: within 2 px of any partial-alpha pixel in the client (where thresholding is a
# deliberate fix). Changes here are reported separately from changes in solid areas.
soft = np.zeros((H, W), np.uint8)
for i in order:
    al = alpha[i]; soft |= ((al > 0) & (al < 255)).astype(np.uint8)
soft = cv2.dilate(soft, np.ones((5, 5), np.uint8)).astype(bool)
Kc = alpha[key] >= 128
Bc = {i: alpha[i] >= 128 for i in order}       # client solid ink, for explanations

def vis_change(img):
    d = np.abs(img.astype(np.int16) - CLIENT.astype(np.int16)).max(axis=2) > DIFF
    return d

def explain(final, ch):
    """Break a visible-change mask into causes: ink removed / added per colour, and what covers it."""
    rows = []
    for i in cols:
        rem = ch & Bc[i] & ~final[i]
        add = ch & final[i] & ~Bc[i]
        if rem.sum() > 200:
            parts = []
            for j in order:
                if j <= i: continue
                n = int((rem & Bc[j]).sum())
                if n > 200: parts.append(f'under {nb[j]} {n:,}')
            parts.append(f'under nothing {int((rem & ~np.any([Bc[j] for j in order if j > i] or [np.zeros((H,W),bool)], axis=0)).sum()):,}')
            rows.append(f'      {nb[i]} removed {int(rem.sum()):,} px ({", ".join(parts)})')
        if add.sum() > 200:
            parts = []
            for j in order:
                if j <= i: continue
                n = int((add & Bc[j]).sum())
                if n > 200: parts.append(f'under {nb[j]} {n:,}')
            rows.append(f'      {nb[i]} added {int(add.sum()):,} px ({", ".join(parts) or "on open paper"})')
    return rows

# ---------------- rule-3 checks on a set of final colour masks (bool, before-file coordinates)
dk_inside = cv2.distanceTransform(Kc.astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
def rule3(final):
    out = {}
    for g in cols:
        if not overlay[g]: continue
        for n in cols:
            if n >= g: continue
            opaque_above = np.zeros((H, W), bool)
            for u in order:
                if u > n and not overlay[u]: opaque_above |= Bc[u]
            zone = Bc[n] & Bc[g] & ~opaque_above
            if zone.sum() < 500: continue
            out[f'{nb[n]} under overlay {nb[g]}'] = (int(zone.sum()), float((zone & final[n]).sum() / zone.sum() * 100))
        # overlay under the key: how deep it still runs inside the key
        kept = final[g] & Kc
        if kept.any():
            d = dk_inside[kept]
            out[f'{nb[g]} under key depth p50/p90/p99 px'] = (int(kept.sum()), (float(np.percentile(d, 50)), float(np.percentile(d, 90)), float(np.percentile(d, 99))))
    return out

# ---------------- hand-trapped after file (optional), aligned by key
A = None; Aalpha = None
if os.path.exists(f'{job}/after/meta.json'):
    na, la, ma = load(f'{job}/after')
    aorder = list(range(1, len(na))); akey = aorder[-1]
    ka_full = np.asarray(la[akey][..., 3]) > 127
    Ha, Wa = ka_full.shape
    K = Kc
    s = 4
    pad = np.zeros((max(H, Ha), max(W, Wa)), np.float32); padb = pad.copy()
    padb[:H, :W] = K; pad[:Ha, :Wa] = ka_full
    (dx, dy), _ = cv2.phaseCorrelate(cv2.resize(padb, (padb.shape[1] // s, padb.shape[0] // s)),
                                    cv2.resize(pad, (pad.shape[1] // s, pad.shape[0] // s)))
    ox, oy = int(round(dx * s)), int(round(dy * s)); best = None
    for ddy in range(-s, s + 1):
        for ddx in range(-s, s + 1):
            X, Y = ox + ddx, oy + ddy
            y0, x0 = max(Y, 0), max(X, 0); y1, x1 = min(Y + H, Ha), min(X + W, Wa)
            if y1 <= y0 or x1 <= x0: continue
            sc = (ka_full[y0:y1, x0:x1] ^ K[y0 - Y:y1 - Y, x0 - X:x1 - X]).mean()
            if best is None or sc < best[0]: best = (sc, X, Y)
    _, ox, oy = best
    def crop(arr):
        out = np.zeros((H, W), arr.dtype)
        y0, x0 = max(oy, 0), max(ox, 0); y1, x1 = min(oy + H, Ha), min(ox + W, Wa)
        out[y0 - oy:y1 - oy, x0 - ox:x1 - ox] = arr[y0:y1, x0:x1]
        return out
    covered = crop(np.ones((Ha, Wa), bool))     # part of the before canvas the after file covers
    print(f'   after file aligned at offset ({ox},{oy}); key differs on {(crop(ka_full) ^ K)[covered].mean()*100:.3f}% of covered px; covers {covered.mean()*100:.1f}% of canvas')
    if len(aorder) != len(order): print('   WARNING: after file has a different layer count - matched by position')
    A = {}; Aalpha = {}
    for j, i in zip(aorder, order):
        al = crop(np.ascontiguousarray(la[j][..., 3]))
        Aalpha[i] = al; A[i] = al >= 128
        print(f'   after layer {j} "{na[j]}" -> client "{nb[i]}" ({mode_of(ma[j])})')

# ---------------- Manual Progressive Knockout, as Photoshop does it: top layer down, each layer's
# (already knocked-out) transparency is loaded as a selection and cleared from every layer below it
# except paper. Overlays included - this is what main.js does today.
def mpk():
    cur = {i: alpha[i].astype(np.float32) for i in order}
    for s_i in reversed(order):
        if a.overlay and s_i != key and overlay[s_i]: continue   # overlay mode: overlays don't cut
        sel = cur[s_i] / 255.0
        for d_i in order:
            if d_i < s_i: cur[d_i] = cur[d_i] * (1 - sel)
    return {i: np.clip(cur[i] + 0.5, 0, 255).astype(np.uint8) for i in order}

def run_engine(masks, tag):
    out = f'{job}_med_{tag}'; shutil.rmtree(out, ignore_errors=True); os.makedirs(out + '/masks')
    def save(al, path, c):
        x = np.zeros((H, W, 4), np.uint8); x[..., :3] = c.astype(np.uint8); x[..., 3] = al
        Image.fromarray(x).save(path, compress_level=1)
    names = {i: f'c{i}_{re.sub(r"[^A-Za-z0-9]", "_", nb[i])[:30]}' for i in cols}
    bm = lambda i: mode[i].lower()
    files = [dict(kind='KEY', name='KEY', blendMode=bm(key), opacity=round(opac[key]*100), fillOpacity=100, png='masks/KEY.png')]
    save(masks[key], out + '/masks/KEY.png', colour[key])
    cl = []
    for i in cols:
        save(masks[i], f'{out}/masks/{i}.png', colour[i])
        files.append(dict(kind='COLOR', name=names[i], blendMode=bm(i), opacity=round(opac[i]*100), fillOpacity=100, png=f'masks/{i}.png'))
        cl.append(dict(name=names[i], blendMode=bm(i), opacity=round(opac[i]*100), fillOpacity=100))
    j = dict(docName=os.path.basename(job), widthPx=W, heightPx=H, resolution=300, keyLayerName='KEY', paperLayerName='paper',
             colors=cl, files=files, **SARA)
    json.dump(j, open(out + '/job.json', 'w'))
    r = subprocess.run([ENGINE, out, a.trap], capture_output=True, text=True)
    if r.returncode: print(r.stdout[-1500:], r.stderr[-1500:]); sys.exit(1)
    T = json.load(open(out + '/traps.json'))['traps']
    inv = {v: k for k, v in names.items()}
    clean = {i: np.array(Image.open(f'{out}/clean_masks/CLEAN__{names[i]}.png'))[..., 3] > 0 for i in cols}
    traps = {i: np.zeros((H, W), bool) for i in cols}
    pairs = []
    for t in T:
        if t['source'] in inv:
            m = np.array(Image.open(out + '/' + t['png']))[..., 3] > 0
            traps[inv[t['source']]] |= m
            tgt = inv.get(t['target'], key if t['target'] == 'KEY' else None)
            pairs.append((inv[t['source']], tgt, t['target'], int(m.sum())))
    if not a.keep: shutil.rmtree(out, ignore_errors=True)
    final = {i: clean[i] | traps[i] for i in cols}
    return final, clean, traps, pairs

# ---------------- measure one result
area = H * W
def report(label, img, final):
    ch = vis_change(img)
    tot = int(ch.sum()); body = int((ch & ~soft).sum()); edge = tot - body
    print(f'\n -- {label}')
    print(f'    visible change vs client: {tot:,} px ({tot/area*100:.2f}% of print)'
          f' = soft-edge zone {edge:,} + solid areas {body:,} ({body/area*100:.2f}%)')
    if final is not None:
        for r in explain(final, ch & ~soft): print(r)
        r3 = rule3(final)
        for k, v in r3.items():
            if 'depth' in k: print(f'    {k}: {v[1][0]:.1f} / {v[1][1]:.1f} / {v[1][2]:.1f}  ({v[0]:,} px)')
            else: print(f'    rule 3: {k}: client {v[0]:,} px, kept {v[1]:.1f}%')
    return dict(label=label, change=tot, change_pct=tot/area*100, solid=body, solid_pct=body/area*100, soft=edge)

results = []
if A is not None:
    hand = composite([(Aalpha[i], colour[i], mode[i], opac[i]) for i in order])
    hand[~covered] = CLIENT[~covered]
    results.append(report('HAND (Sara\'s after file)', hand, {i: A[i] for i in cols}))
    del hand

for use_mpk in (True, False):
    masks = mpk() if use_mpk else {i: alpha[i] for i in order}
    tag = ('mpk' if use_mpk else 'nompk') + ('_ov' if a.overlay else '')
    final, clean, traps, pairs = run_engine(masks, tag)
    print(f'\n== trapper {"WITH" if use_mpk else "WITHOUT"} Manual Progressive Knockout: trap layers made:')
    for s_i, t_i, tname, n in pairs:
        flag = '  <- under an OVERLAY' if (t_i is not None and t_i != key and overlay[t_i]) else ''
        print(f'     TRAP {nb[s_i]} under {nb[t_i] if t_i is not None else tname}: {n:,} px{flag}')
    keyL = (alpha[key], colour[key], mode[key], opac[key])
    for kept in (True, False):
        layers = [(final[i], colour[i], mode[i] if kept else 'NORMAL', opac[i] if kept else 1.0) for i in cols] + [keyL]
        img = composite(layers)
        r = report(f'TRAPPER {"with" if use_mpk else "without"} MPK, overlay blend {"KEPT on import" if kept else "LOST on import (Normal)"}', img, final)
        results.append(r); del img
    if A is not None:
        mo = sum(int((A[i] & ~final[i] & covered).sum()) for i in cols); to = sum(int((final[i] & ~A[i] & covered).sum()) for i in cols)
        print(f'    vs hand masks: ink only in hand {mo:,} px, only in trapper {to:,} px')
    del final, clean, traps, masks
json.dump(results, open(f'{job}_medium_check{"_overlay" if a.overlay else ""}.json', 'w'), indent=1)
