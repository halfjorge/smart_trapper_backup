# Read a raw Photoshop "Layr" block (from pdf2psb.py) in PSD (4-byte) or PSB (8-byte) layout and keep the
# real channel values (grayscale/soft edges), not just on/off masks.
# Usage: python3 layr_read_full.py block.bin OUTDIR
# Writes OUTDIR/layers.json and OUTDIR/L<i>_<cid>.npy (uint8, cropped to the layer's bbox; cid -1 = alpha)
import sys, struct, json, os, numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
src, OD = sys.argv[1:3]; os.makedirs(OD, exist_ok=True)
raw = open(src, 'rb').read(); assert raw[:8] == b'8BIMLayr'
L4 = struct.unpack('>I', raw[8:12])[0]
psb = not (L4 + 12 <= len(raw) and L4 > 1000)          # PSD layout: 4-byte block length
p = 16 if psb else 12
cnt = struct.unpack('>h', raw[p:p+2])[0]; p += 2; n = abs(cnt)
CL = 8 if psb else 4; RC = 4 if psb else 2
recs = []
for i in range(n):
    t, l, b, r = struct.unpack('>4i', raw[p:p+16]); p += 16
    nc = struct.unpack('>H', raw[p:p+2])[0]; p += 2
    ch = []
    for _ in range(nc):
        cid = struct.unpack('>h', raw[p:p+2])[0]; ln = struct.unpack('>Q' if psb else '>I', raw[p+2:p+2+CL])[0]
        p += 2 + CL; ch.append((cid, ln))
    assert raw[p:p+4] == b'8BIM'
    blend = raw[p+4:p+8].decode('latin1'); opac = raw[p+8]; clip = raw[p+9]; flags = raw[p+10]
    el = struct.unpack('>I', raw[p+12:p+16])[0]; e = p + 16; end = e + el
    ml = struct.unpack('>I', raw[e:e+4])[0]; mask = raw[e+4:e+4+ml]; e += 4 + ml
    bl = struct.unpack('>I', raw[e:e+4])[0]; e += 4 + bl
    nl = raw[e]; name = raw[e+1:e+1+nl].decode('latin1'); e += ((1 + nl + 3) // 4) * 4
    keys = []
    while e + 12 <= end:
        key = raw[e+4:e+8].decode('latin1'); ln = struct.unpack('>I', raw[e+8:e+12])[0]
        if key == 'luni':
            k = struct.unpack('>I', raw[e+12:e+16])[0]; name = raw[e+16:e+16+2*k].decode('utf-16-be')
        keys.append(key); e += 12 + ln
    p = end
    recs.append(dict(index=i, name=name, bbox=[l, t, r, b], chans=ch, visible=not (flags & 2), opacity=opac,
                     blend=blend, clipping=clip, keys=keys, mask_len=ml,
                     mask_rect=list(struct.unpack('>4i', mask[:16])) if ml >= 16 else None))
for rc in recs:
    l, t, r, b = rc['bbox']; w, h = r - l, b - t; info = {}
    for cid, ln in rc['chans']:
        c = raw[p:p+ln]; p += ln
        if cid == -2 and rc['mask_rect']:
            mt, ml_, mb, mr = rc['mask_rect']; ww, hh = mr - ml_, mb - mt
        else:
            ww, hh = w, h
        if ww <= 0 or hh <= 0: continue
        comp = struct.unpack('>H', c[:2])[0]
        if comp == 1:
            a = np.asarray(Image.frombytes('L', (ww, hh), c[2+RC*hh:], 'packbits', 'L'))
        elif comp == 0:
            a = np.frombuffer(c[2:2+ww*hh], np.uint8).reshape(hh, ww)
        else:
            raise SystemExit(f'compression {comp} in {rc["name"]}')
        np.save(f'{OD}/L{rc["index"]}_{cid}.npy', a)
        info[cid] = dict(min=int(a.min()), max=int(a.max()), mean=round(float(a.mean()), 1),
                         partial=round(float(((a > 0) & (a < 255)).mean()), 4))
    rc['stats'] = info; del rc['chans']
    print(rc['index'], repr(rc['name']), rc['bbox'], rc['blend'], rc['opacity'], 'vis' if rc['visible'] else 'hidden',
          'clip' if rc['clipping'] else '', {k: v for k, v in info.items()}, flush=True)
json.dump(recs, open(f'{OD}/layers.json', 'w'), indent=1)
