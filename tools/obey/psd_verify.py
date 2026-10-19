# Read a written .psd (v1) back and compare every layer's alpha with the expected masks.
# Usage: python3 psd_verify.py out.psd LDIR FIXDIR
import sys, struct, json, os, numpy as np
from PIL import Image
psd, LD, FD = sys.argv[1:4]; W, H = 9600, 12000
Ls = [l for l in json.load(open(f'{LD}/layers.json')) if l['name'] != 'Layer 1']
d = open(psd, 'rb').read()
assert d[:4] == b'8BPS' and struct.unpack('>H', d[4:6])[0] == 1
ch, h, w = struct.unpack('>HII', d[12:22]); assert (h, w) == (H, W)
p = 26; p += 4 + struct.unpack('>I', d[p:p+4])[0]                  # colour mode
rl = struct.unpack('>I', d[p:p+4])[0]; res = d[p+4:p+4+rl]; p += 4 + rl
i = res.find(b'8BIM\x03\xed'); dpi = struct.unpack('>I', res[i+12:i+16])[0] >> 16
lm = struct.unpack('>I', d[p:p+4])[0]; p += 4; lm_end = p + lm
li = struct.unpack('>I', d[p:p+4])[0]; p += 4
n = abs(struct.unpack('>h', d[p:p+2])[0]); p += 2
assert n in (len(Ls), len(Ls) + 1), (n, len(Ls))
recs = []
for k in range(n):
    t, l, b, r = struct.unpack('>4i', d[p:p+16]); p += 16
    nc = struct.unpack('>H', d[p:p+2])[0]; p += 2
    cs = [struct.unpack('>hI', d[p+6*j:p+6*j+6]) for j in range(nc)]; p += 6 * nc
    el = struct.unpack('>I', d[p+12:p+16])[0]; p += 16 + el
    recs.append(((t, l, b, r), cs))
bad = 0
for k, ((t, l, b, r), cs) in enumerate(recs):
    ww, hh = r - l, b - t; a = None
    for cid, ln in cs:
        c = d[p:p+ln]; p += ln
        if cid == -1 and ww > 0 and hh > 0:
            comp = struct.unpack('>H', c[:2])[0]
            a = (np.asarray(Image.frombytes('L', (ww, hh), c[2+2*hh:], 'packbits', 'L')) if comp == 1
                 else np.frombuffer(c[2:], np.uint8).reshape(hh, ww))
    if k >= len(Ls): continue
    meta = Ls[k]; idx = meta['index']
    if not meta.get('pixels'): continue
    f = f'{FD}/m_{idx}.npy' if os.path.exists(f'{FD}/m_{idx}.npy') else f'{LD}/m_{idx}.npy'
    exp = np.unpackbits(np.load(f))[:W*H].reshape(H, W).astype(bool)
    got = np.zeros((H, W), bool)
    if a is not None:
        y0, x0 = max(t, 0), max(l, 0); y1, x1 = min(b, H), min(r, W)
        got[y0:y1, x0:x1] = a[y0-t:y1-t, x0-l:x1-l] > 127
    diff = int((got != exp).sum()); bad += diff
    if diff: print('MISMATCH', meta['name'], diff)
assert p <= lm_end
p = lm_end
comp = struct.unpack('>H', d[p:p+2])[0]; counts = struct.unpack(f'>{3*H}H', d[p+2:p+2+6*H])
img = np.asarray(Image.frombytes('L', (W, 3*H), d[p+2+6*H:], 'packbits', 'L'))
print(f'layers {n}, dpi {dpi}, layer mismatches {bad}, composite decoded {img.shape}, file ends ok {p+2+6*H+sum(counts)==len(d)}')
Image.fromarray(np.stack([img[k*H:(k+1)*H] for k in range(3)], -1)).resize((960, 1200), Image.BILINEAR).save('composite_small.png')
