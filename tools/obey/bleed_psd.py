# Add bleed to a .psd (v1) written by psd_write.py WITHOUT changing anything inside the original canvas.
# Every layer (hidden ones too) and the flattened image go through the same bleed map (bleed.py); then the
# original canvas pixels are pasted back exactly, so the separations inside the trim are untouched.
# Usage: python3 bleed_psd.py in.psd bleed_map.npz out.psd
import sys, io, struct, numpy as np
sys.path.insert(0, '/home/claude/smart_trapper_backup/tools/obey')
from PIL import Image
from bleed_apply import load_map, apply
src, mapf, outp = sys.argv[1:4]
mp = load_map(mapf); y0i, y1i, x0i, x1i = [int(v) for v in mp['box']]; Bt, Bb, Bl, Br = [int(v) for v in mp['Bs']]
d = open(src, 'rb').read()
assert d[:4] == b'8BPS' and struct.unpack('>H', d[4:6])[0] == 1
nchan, H, W = struct.unpack('>HII', d[12:22])
H2, W2 = (y1i - y0i) + Bt + Bb, (x1i - x0i) + Bl + Br
oy, ox = Bt - y0i, Bl - x0i                     # where the original canvas sits in the new one
print('canvas', W, H, '->', W2, H2, 'offset', ox, oy)

def packbits_rows(a):
    h, w = a.shape
    buf = io.BytesIO()
    Image.fromarray(np.ascontiguousarray(a), 'L').save(buf, 'TIFF', compression='packbits', tiffinfo={278: 1})
    t = Image.open(io.BytesIO(buf.getvalue())); offs = t.tag_v2[273]; cnts = t.tag_v2[279]
    if isinstance(offs, int): offs, cnts = (offs,), (cnts,)
    v = buf.getvalue()
    return list(cnts), b''.join(v[o:o+c] for o, c in zip(offs, cnts))
def rle(a):
    c, b = packbits_rows(a); return struct.pack('>H', 1) + struct.pack(f'>{len(c)}H', *c) + b
def decode(c, w, h):
    comp = struct.unpack('>H', c[:2])[0]
    if comp == 1: return np.asarray(Image.frombytes('L', (w, h), c[2+2*h:], 'packbits', 'L'))
    return np.frombuffer(c[2:2+w*h], np.uint8).reshape(h, w)
def grow(full):
    out = apply(full, mp)
    out[oy:oy+H, ox:ox+W] = full                 # original canvas back, exactly
    return out

p = 26; p += 4 + struct.unpack('>I', d[p:p+4])[0]
rl = struct.unpack('>I', d[p:p+4])[0]; res = d[p:p+4+rl]; p += 4 + rl
lm = struct.unpack('>I', d[p:p+4])[0]; p += 4; lm_end = p + lm
p += 4
cnt = struct.unpack('>h', d[p:p+2])[0]; p += 2; n = abs(cnt)
recs = []
for k in range(n):
    rect = struct.unpack('>4i', d[p:p+16]); p += 16
    nc = struct.unpack('>H', d[p:p+2])[0]; p += 2
    cs = [list(struct.unpack('>hI', d[p+6*j:p+6*j+6])) for j in range(nc)]; p += 6 * nc
    el = struct.unpack('>I', d[p+12:p+16])[0]; rest = d[p:p+16+el]; p += 16 + el
    recs.append(dict(rect=rect, cs=cs, rest=rest))
for r in recs:
    r['data'] = []
    for cid, ln in r['cs']: r['data'].append(d[p:p+ln]); p += ln
img_p = lm_end

for k, r in enumerate(recs):
    t, l, b, rr = r['rect']; w, h = rr - l, b - t
    if w <= 0 or h <= 0: continue
    touches = t <= y0i or l <= x0i or b >= y1i or rr >= x1i
    if not touches:
        r['rect'] = (t + oy, l + ox, b + oy, rr + ox); continue
    planes = {}
    for (cid, _), c in zip(r['cs'], r['data']):
        full = np.zeros((H, W), np.uint8); full[t:b, l:rr] = decode(c, w, h)
        planes[cid] = grow(full); del full
    al = planes.get(-1)
    ys = np.nonzero(al.any(1))[0]; xs = np.nonzero(al.any(0))[0]
    nt, nb, nl, nr = int(ys[0]), int(ys[-1]) + 1, int(xs[0]), int(xs[-1]) + 1
    r['rect'] = (nt, nl, nb, nr)
    r['data'] = [rle(planes[cid][nt:nb, nl:nr]) for cid, _ in r['cs']]
    del planes, al
    print(' bleed layer', k, flush=True)

# flattened image
comp = struct.unpack('>H', d[img_p:img_p+2])[0]; assert comp == 1
counts = struct.unpack(f'>{nchan*H}H', d[img_p+2:img_p+2+2*nchan*H])
q = img_p + 2 + 2 * nchan * H; outc, outd = [], []
for c in range(nchan):
    ln = sum(counts[c*H:(c+1)*H])
    a = np.asarray(Image.frombytes('L', (W, H), d[q:q+ln], 'packbits', 'L')); q += ln
    cc, bb = packbits_rows(grow(a)); outc += cc; outd.append(bb)
imgdata = struct.pack('>H', 1) + struct.pack(f'>{len(outc)}H', *outc) + b''.join(outd)

li = io.BytesIO(); li.write(struct.pack('>h', cnt))
for r in recs:
    li.write(struct.pack('>4i', *r['rect'])); li.write(struct.pack('>H', len(r['cs'])))
    for (cid, _), c in zip(r['cs'], r['data']): li.write(struct.pack('>hI', cid, len(c)))
    li.write(r['rest'])
for r in recs:
    for c in r['data']: li.write(c)
lib = li.getvalue()
if len(lib) % 2: lib += b'\0'
lmi = struct.pack('>I', len(lib)) + lib + struct.pack('>I', 0)
hdr = b'8BPS' + struct.pack('>H', 1) + b'\0' * 6 + struct.pack('>HIIHH', nchan, H2, W2, 8, 3)
with open(outp, 'wb') as f:
    f.write(hdr); f.write(struct.pack('>I', 0)); f.write(res); f.write(struct.pack('>I', len(lmi)) + lmi); f.write(imgdata)
print('saved', outp, W2, H2)
