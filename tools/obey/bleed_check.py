# Compare a bleed PSD with its source PSD. Usage: python3 bleed_check.py src.psd bleed.psd LDIR [inset_bottom_rows]
import sys, struct, json, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
src, ble, LD = sys.argv[1:4]; ib = int(sys.argv[4]) if len(sys.argv) > 4 else 0
def read_psd(path):
    d = open(path, 'rb').read(); nch, H, W = struct.unpack('>HII', d[12:22])
    p = 26; p += 4 + struct.unpack('>I', d[p:p+4])[0]; p += 4 + struct.unpack('>I', d[p:p+4])[0]
    p += 4; p += 4; n = abs(struct.unpack('>h', d[p:p+2])[0]); p += 2; recs = []
    for k in range(n):
        rect = struct.unpack('>4i', d[p:p+16]); p += 16; nc = struct.unpack('>H', d[p:p+2])[0]; p += 2
        cs = [struct.unpack('>hI', d[p+6*j:p+6*j+6]) for j in range(nc)]; p += 6 * nc
        el = struct.unpack('>I', d[p+12:p+16])[0]; recs.append([rect, cs, {}]); p += 16 + el
    for r in recs:
        for cid, ln in r[1]: r[2][cid] = d[p:p+ln]; p += ln
    return W, H, recs
def plane(r, cid, W, H):
    (t, l, b, rr), cs, dd = r; w, h = rr - l, b - t; out = np.zeros((H, W), np.uint8)
    if w <= 0 or h <= 0 or cid not in dd: return out
    c = dd[cid]; comp = struct.unpack('>H', c[:2])[0]
    a = np.asarray(Image.frombytes('L', (w, h), c[2+2*h:], 'packbits', 'L')) if comp == 1 else np.frombuffer(c[2:], np.uint8).reshape(h, w)
    out[t:b, l:rr] = a; return out
W1, H1, R1 = read_psd(src); W2, H2, R2 = read_psd(ble); oy = (H2 - H1) // 2; ox = (W2 - W1) // 2
Ls = [l for l in json.load(open(f'{LD}/layers.json')) if l['name'] != 'Layer 1']
bad = 0; inset_changed = 0; cov = np.zeros((H2, W2), bool); seps = {}
for k, (r1, r2) in enumerate(zip(R1, R2)):
    for cid, _ in r1[1]:
        a = plane(r1, cid, W1, H1); b = plane(r2, cid, W2, H2)[oy:oy+H1, ox:ox+W1]
        diff = b != a
        bad += int(diff[:H1-ib].sum()); inset_changed += int(diff[H1-ib:].sum()) if ib else 0
        if k < len(Ls) and cid == -1 and Ls[k]['visible'] and Ls[k].get('pixels') and Ls[k]['name'].startswith(('CLEAN__', 'TRAP__', 'Key')):
            m = plane(r2, cid, W2, H2) > 127; cov |= m
            if Ls[k]['name'] != 'Key':
                c = Ls[k]['name'].split('COLOR__')[1].split('_under_')[0]
                seps[c] = seps.get(c, np.zeros((H2, W2), np.uint8)) + m
ring = np.ones((H2, W2), bool); ring[oy:oy+H1-ib, ox:ox+W1] = False
print('size', W2, H2, '| changed inside trim (excluding inset rows):', bad, '| changed in inset rows:', inset_changed)
print('bare paper in bleed + inset rows:', int((~cov & ring).sum()))
print('doubled ink in bleed + inset rows:', {c: int(((v > 1) & ring).sum()) for c, v in seps.items()})
