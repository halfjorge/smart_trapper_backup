# Read the raw Photoshop "Layr" block (from pdf2psb.py) without psd-tools.
# Usage: python3 layr_read.py new.bin OUTDIR
# Writes OUTDIR/layers.json (name, bbox, visible, colour, order bottom->top) and
# OUTDIR/m_<i>.npy = packed full-size alpha>127 mask for each pixel layer.
import sys, struct, json, os, numpy as np
from PIL import Image

def unpack_rows(buf, w, h):
    if h == 0 or w == 0:
        return np.zeros((h, w), np.uint8)
    return np.asarray(Image.frombytes('L', (w, h), buf, 'packbits', 'L'))

def read(path, outdir, W=None, H=None):
    raw = open(path, 'rb').read()
    assert raw[:8] == b'8BIMLayr'
    p = 16
    n = struct.unpack('>h', raw[p:p+2])[0]; p += 2
    n = abs(n)
    recs = []
    for i in range(n):
        t, l, b, r = struct.unpack('>4i', raw[p:p+16]); p += 16
        nc = struct.unpack('>H', raw[p:p+2])[0]; p += 2
        chans = []
        for _ in range(nc):
            cid, ln = struct.unpack('>hQ', raw[p:p+10]); p += 10
            chans.append((cid, ln))
        assert raw[p:p+4] == b'8BIM', (i, raw[p:p+4])
        blend = raw[p+4:p+8].decode('latin1'); opac = raw[p+8]; flags = raw[p+10]
        p += 12
        el = struct.unpack('>I', raw[p:p+4])[0]; p += 4
        e = p; end = p + el
        ml = struct.unpack('>I', raw[e:e+4])[0]; e += 4 + ml
        bl = struct.unpack('>I', raw[e:e+4])[0]; e += 4 + bl
        nl = raw[e]; name = raw[e+1:e+1+nl].decode('latin1'); e += ((1 + nl + 3) // 4) * 4
        while e + 12 <= end:
            sig, key = raw[e:e+4], raw[e+4:e+8]
            big = key in (b'LMsk', b'Lr16', b'Lr32', b'Layr', b'Mt16', b'Mt32', b'Mtrn', b'Alph',
                          b'FMsk', b'lnk2', b'FEid', b'FXid', b'PxSD')
            if big:
                ln = struct.unpack('>Q', raw[e+8:e+16])[0]; d0 = e + 16
            else:
                ln = struct.unpack('>I', raw[e+8:e+12])[0]; d0 = e + 12
            if key == b'luni':
                k = struct.unpack('>I', raw[d0:d0+4])[0]
                name = raw[d0+4:d0+4+2*k].decode('utf-16-be')
            e = d0 + ln + (ln % 2 if False else 0)
            e += (-(e - d0)) % 4 if False else 0
        p = end
        recs.append(dict(name=name, bbox=[l, t, r, b], chans=chans, visible=not (flags & 2),
                         opacity=opac, blend=blend))
    # channel image data
    out = []
    for i, rc in enumerate(recs):
        l, t, r, b = rc['bbox']; w, h = r - l, b - t
        ch = {}
        for cid, ln in rc['chans']:
            comp = struct.unpack('>H', raw[p:p+2])[0]
            data = raw[p+2:p+ln]; p += ln
            if cid == -2 or w <= 0 or h <= 0:
                continue
            if comp == 0:
                a = np.frombuffer(data, np.uint8)[:w*h].reshape(h, w)
            elif comp == 1:
                a = unpack_rows(data[4*h:], w, h)
            else:
                raise ValueError(f'compression {comp} in layer {rc["name"]}')
            if cid in (-1, 0, 1, 2):
                ch[cid] = a
        rc['index'] = i
        if -1 in ch and W:
            m = np.zeros((H, W), bool)
            a = ch[-1] > 127
            x0, y0 = max(l, 0), max(t, 0); x1, y1 = min(r, W), min(b, H)
            m[y0:y1, x0:x1] = a[y0-t:y1-t, x0-l:x1-l]
            np.save(f'{outdir}/m_{i}.npy', np.packbits(m))
            if 0 in ch:
                rgb = np.stack([ch[0], ch[1], ch[2]], -1)[a]
                if len(rgb):
                    u, c = np.unique(rgb[::97], axis=0, return_counts=True)
                    rc['colour'] = [int(v) for v in u[c.argmax()]]
            rc['pixels'] = int(a.sum())
        del rc['chans']
        out.append(rc)
        print(i, rc['name'], rc['bbox'], rc.get('pixels'), rc.get('colour'), rc['visible'], flush=True)
    json.dump(out, open(f'{outdir}/layers.json', 'w'), indent=1)

if __name__ == '__main__':
    os.makedirs(sys.argv[2], exist_ok=True)
    W = int(sys.argv[3]) if len(sys.argv) > 3 else 9600
    H = int(sys.argv[4]) if len(sys.argv) > 4 else 12000
    read(sys.argv[1], sys.argv[2], W, H)
