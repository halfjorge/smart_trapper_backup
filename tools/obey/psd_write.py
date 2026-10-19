# Write a normal .psd (v1) from the trapper's raw Layr block (PSB-style, from pdf2psb.py), copying every
# layer record as-is and swapping in fixed masks for changed CLEAN__/TRAP__ layers. Drops the PDF's white
# "Layer 1". Adds a flattened composite (paper, colours, key at its own opacity) and the resolution.
# Usage: python3 psd_write.py new.bin LDIR FIXDIR out.psd [dpi]
#   LDIR: layers.json from layr_read.py; FIXDIR: m_<index>.npy for changed layers (may be empty dir)
import sys, os, io, struct, json, numpy as np
from PIL import Image, TiffImagePlugin
src, LD, FD, outp = sys.argv[1:5]; DPI = int(sys.argv[5]) if len(sys.argv) > 5 else 600
W, H = 9600, 12000
raw = open(src, 'rb').read()
Ls = json.load(open(f'{LD}/layers.json'))

def packbits_rows(a):
    """PackBits-encode each row of a 2-D uint8 array (via libtiff, one row per strip)."""
    h, w = a.shape
    if h == 0 or w == 0: return [], b''
    buf = io.BytesIO()
    Image.fromarray(np.ascontiguousarray(a), 'L').save(buf, 'TIFF', compression='packbits',
                                                         tiffinfo={278: 1})
    t = Image.open(io.BytesIO(buf.getvalue()))
    offs = t.tag_v2[273]; cnts = t.tag_v2[279]
    if isinstance(offs, int): offs, cnts = (offs,), (cnts,)
    assert len(cnts) == h, (len(cnts), h)
    d = buf.getvalue()
    return list(cnts), b''.join(d[o:o+c] for o, c in zip(offs, cnts))

def const_rows(v, w, h):
    row = b''; n = w
    while n > 0:
        k = min(128, n)
        row += bytes([257 - k, v]) if k > 1 else bytes([0, v]); n -= k
    return [len(row)] * h, row * h

def rle_channel(counts, data):
    return struct.pack('>H', 1) + struct.pack(f'>{len(counts)}H', *counts) + data

# ---- parse records (PSB) ----
p = 16
cnt = struct.unpack('>h', raw[p:p+2])[0]; p += 2; n = abs(cnt)
recs = []
for i in range(n):
    rect = struct.unpack('>4i', raw[p:p+16]); p += 16
    nc = struct.unpack('>H', raw[p:p+2])[0]; p += 2
    ch = []
    for _ in range(nc):
        cid, ln = struct.unpack('>hQ', raw[p:p+10]); p += 10; ch.append([cid, ln])
    el = struct.unpack('>I', raw[p+12:p+16])[0]
    rest = raw[p:p+16+el]; p += 16 + el
    recs.append(dict(rect=rect, ch=ch, rest=rest))
for r in recs:
    t, l, b, rr = r['rect']; h = b - t
    datas = []
    for cid, ln in r['ch']:
        d = raw[p:p+ln]; p += ln
        comp = struct.unpack('>H', d[:2])[0]
        if comp == 1 and h > 0 and (rr - l) > 0:
            counts = struct.unpack(f'>{h}I', d[2:2+4*h])
            datas.append(rle_channel(counts, d[2+4*h:]))
        else:
            datas.append(d)
    r['data'] = datas

# ---- swap in fixed layers ----
for i, r in enumerate(recs):
    f = f'{FD}/m_{i}.npy'
    if not os.path.exists(f): continue
    m = np.unpackbits(np.load(f))[:W*H].reshape(H, W)
    col = Ls[i]['colour']
    ys = np.nonzero(m.any(1))[0]; xs = np.nonzero(m.any(0))[0]
    if len(ys) == 0:
        r['rect'] = (0, 0, 0, 0); r['data'] = [struct.pack('>H', 0)] * len(r['ch']); continue
    t, b, l, rr = int(ys[0]), int(ys[-1]) + 1, int(xs[0]), int(xs[-1]) + 1
    sub = m[t:b, l:rr] * np.uint8(255); w, h = rr - l, b - t
    r['rect'] = (t, l, b, rr); new = []
    for cid, _ in r['ch']:
        if cid == -1: new.append(rle_channel(*packbits_rows(sub)))
        elif cid in (0, 1, 2): new.append(rle_channel(*const_rows(col[cid], w, h)))
        else: raise SystemExit(f'unexpected channel {cid} in layer {i}')
    r['data'] = new
    print('swapped', Ls[i]['name'], flush=True)

# ---- drop the PDF's white top layer ----
keep = [r for i, r in enumerate(recs) if Ls[i]['name'] != 'Layer 1']
kept_meta = [Ls[i] for i in range(n) if Ls[i]['name'] != 'Layer 1']

# ---- optional hidden magenta layer: every changed pixel (FIXDIR/changed.npy) ----
if os.path.exists(f'{FD}/changed.npy'):
    cm = np.unpackbits(np.load(f'{FD}/changed.npy'))[:W*H].reshape(H, W)
    ys = np.nonzero(cm.any(1))[0]; xs = np.nonzero(cm.any(0))[0]
    t, b, l, rr = int(ys[0]), int(ys[-1]) + 1, int(xs[0]), int(xs[-1]) + 1
    sub = cm[t:b, l:rr] * np.uint8(255); ww, hh = rr - l, b - t
    nm = 'CHANGED PIXELS (mitre pass) - hidden, not for print'
    pn = nm.encode('latin1'); pas = bytes([len(pn)]) + pn; pas += b'\0' * ((-len(pas)) % 4)
    u = nm.encode('utf-16-be'); luni = struct.pack('>I', len(nm)) + u
    if len(luni) % 4: luni += b'\0' * ((-len(luni)) % 4)
    extra = struct.pack('>I', 0) + struct.pack('>I', 0) + pas + b'8BIMluni' + struct.pack('>I', len(luni)) + luni
    rest = b'8BIMnorm' + bytes([255, 0, 2, 0]) + struct.pack('>I', len(extra)) + extra
    data = [rle_channel(*packbits_rows(sub))] + [rle_channel(*const_rows(v, ww, hh)) for v in (255, 0, 255)]
    keep.append(dict(rect=(t, l, b, rr), ch=[[-1, 0], [0, 0], [1, 0], [2, 0]], rest=rest, data=data))
    print('added changed-pixels layer', int(cm.sum()), 'px')

# ---- layer info (PSD v1) ----
li = io.BytesIO()
li.write(struct.pack('>h', len(keep) if cnt > 0 else -len(keep)))
for r in keep:
    li.write(struct.pack('>4i', *r['rect'])); li.write(struct.pack('>H', len(r['ch'])))
    for (cid, _), d in zip(r['ch'], r['data']): li.write(struct.pack('>hI', cid, len(d)))
    li.write(r['rest'])
for r in keep:
    for d in r['data']: li.write(d)
lib = li.getvalue()
if len(lib) % 2: lib += b'\0'
lmi = struct.pack('>I', len(lib)) + lib + struct.pack('>I', 0)

# ---- flattened composite (what the layers show) ----
comp = np.empty((H, W, 3), np.uint8)
STRIP = 1000
order = [(m_['index'], m_) for m_ in kept_meta if m_['visible'] and m_.get('pixels') and
         (m_['name'].startswith(('CLEAN__', 'TRAP__')) or m_['name'] in ('Key', 'Cougar Natural 100#C'))]
masks = {}
def mask(i):
    f = f'{FD}/m_{i}.npy' if os.path.exists(f'{FD}/m_{i}.npy') else f'{LD}/m_{i}.npy'
    return np.load(f, mmap_mode='r')
RB = W // 8
for y0 in range(0, H, STRIP):
    y1 = min(H, y0 + STRIP)
    c = np.empty((y1 - y0, W, 3), np.float32); c[:] = (248, 239, 229)
    for i, m_ in order:
        mm = np.unpackbits(np.asarray(mask(i)[y0*RB:y1*RB])).reshape(y1 - y0, W).astype(bool)
        a = m_['opacity'] / 255
        c[mm] = c[mm] * (1 - a) + np.array(m_['colour'], np.float32) * a
    comp[y0:y1] = np.clip(c + 0.5, 0, 255).astype(np.uint8)
allc, alld = [], []
for k in range(3):
    cn, dd = packbits_rows(comp[..., k]); allc += cn; alld.append(dd)
img = struct.pack('>H', 1) + struct.pack(f'>{len(allc)}H', *allc) + b''.join(alld)
del comp

# ---- resources: resolution ----
res = struct.pack('>IhhIhh', DPI << 16, 1, 1, DPI << 16, 1, 1)
ir = b'8BIM' + struct.pack('>H', 0x03ED) + b'\0\0' + struct.pack('>I', len(res)) + res
hdr = b'8BPS' + struct.pack('>H', 1) + b'\0' * 6 + struct.pack('>HIIHH', 3, H, W, 8, 3)
with open(outp, 'wb') as f:
    f.write(hdr); f.write(struct.pack('>I', 0)); f.write(struct.pack('>I', len(ir)) + ir)
    f.write(struct.pack('>I', len(lmi)) + lmi); f.write(img)
print('saved', outp, os.path.getsize(outp))
