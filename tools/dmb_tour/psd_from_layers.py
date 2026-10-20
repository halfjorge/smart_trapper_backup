# Minimal layered PSD (v1, RGB 8-bit, RLE) writer from numpy layers.
# write_psd(path, W, H, layers, composite, dpi) ; layers bottom->top: dict(name, rgb (H,W,3) or (3,) const,
#   alpha (H,W) uint8, visible=True, opacity=255). Layers are cropped to their alpha bbox.
import io, struct, numpy as np
from PIL import Image

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

def record(name, rect, chans, visible=True, opacity=255):
    pn = name.encode('latin1', 'replace')[:255]; pas = bytes([len(pn)]) + pn; pas += b'\0' * ((-len(pas)) % 4)
    u = struct.pack('>I', len(name)) + name.encode('utf-16-be'); u += b'\0' * ((-len(u)) % 4)
    extra = struct.pack('>I', 0) + struct.pack('>I', 0) + pas + b'8BIMluni' + struct.pack('>I', len(u)) + u
    flags = 0 if visible else 2
    head = struct.pack('>4i', *rect) + struct.pack('>H', len(chans))
    for cid, d in chans: head += struct.pack('>hI', cid, len(d))
    return head + b'8BIMnorm' + bytes([opacity, 0, flags, 0]) + struct.pack('>I', len(extra)) + extra

def write_psd(path, W, H, layers, composite, dpi=300):
    recs, data = [], []
    for L in layers:
        a = L['alpha']; ys = np.nonzero(a.any(1))[0]; xs = np.nonzero(a.any(0))[0]
        if len(ys) == 0:
            rect = (0, 0, 0, 0); chans = [(cid, struct.pack('>H', 0)) for cid in (-1, 0, 1, 2)]
        else:
            t, b, l, r = int(ys[0]), int(ys[-1]) + 1, int(xs[0]), int(xs[-1]) + 1; rect = (t, l, b, r)
            rgb = L['rgb']; chans = [(-1, rle(a[t:b, l:r]))]
            for c in range(3):
                plane = (np.full((b - t, r - l), rgb[c], np.uint8) if np.ndim(rgb) == 1 else rgb[t:b, l:r, c])
                chans.append((c, rle(plane)))
        recs.append(record(L['name'], rect, chans, L.get('visible', True), L.get('opacity', 255)))
        data.append(b''.join(d for _, d in chans))
    li = struct.pack('>h', len(layers)) + b''.join(recs) + b''.join(data)
    if len(li) % 2: li += b'\0'
    lmi = struct.pack('>I', len(li)) + li + struct.pack('>I', 0)
    cn, cd = [], []
    for c in range(3):
        x, y = packbits_rows(composite[..., c]); cn += x; cd.append(y)
    img = struct.pack('>H', 1) + struct.pack(f'>{len(cn)}H', *cn) + b''.join(cd)
    res = struct.pack('>IhhIhh', dpi << 16, 1, 1, dpi << 16, 1, 1)
    ir = b'8BIM' + struct.pack('>H', 0x03ED) + b'\0\0' + struct.pack('>I', len(res)) + res
    hdr = b'8BPS' + struct.pack('>H', 1) + b'\0' * 6 + struct.pack('>HIIHH', 3, H, W, 8, 3)
    with open(path, 'wb') as f:
        f.write(hdr); f.write(struct.pack('>I', 0)); f.write(struct.pack('>I', len(ir)) + ir)
        f.write(struct.pack('>I', len(lmi)) + lmi); f.write(img)
