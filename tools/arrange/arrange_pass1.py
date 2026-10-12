# Rebuild a messy layered PSD into one layer per ink (standard "before" structure).
# Pass 1: walk the stack bottom->top honouring visibility, layer masks, group masks and
# clipping; for every visible pixel pick the nearest ink; keep each ink's full coverage
# (union of its alpha) and which ink is visible on top. Saves arrays for pass 2.
import sys, json, warnings, numpy as np; warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/claude/psdsrc/src')
from psd_tools import PSDImage
src, out = sys.argv[1], sys.argv[2]
p = PSDImage.open(src); W, H = p.width, p.height
INKS = json.loads(sys.argv[3])            # name -> hex
ALIAS = json.loads(sys.argv[4])           # extra hex -> ink name
names = list(INKS); pal = np.array([[int(INKS[n][i:i+2],16) for i in (0,2,4)] for n in names], np.float32)
alias_rgb = {k: np.array([int(k[i:i+2],16) for i in (0,2,4)]) for k in ALIAS}
cover = np.zeros((len(names), H, W), np.uint8)
def _Lstar(c):
    c=c/255; c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4); Y=0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
    return 116*(Y**(1/3) if Y>0.008856 else 7.787*Y+16/116)-16
LST = [999.0 if n=='paper' else float(_Lstar(pal[i])) for i,n in enumerate(names)]   # bigger = lower in the new stack
plate = np.zeros((len(names), H, W), np.uint8)   # replayed result in the NEW order (paper slot unused)
vis = np.full((H, W), -1, np.int8)        # ink visible on top (alpha>=128)
LAYER_NO = [0]
comp = np.zeros((H, W, 3), np.uint8)
log = []; far_px = 0; alias_px = {k:0 for k in ALIAS}

def place(img_bbox, arr, default=0):
    """Put an array with bbox (x0,y0,x1,y1) onto a full canvas, cropping outside."""
    full = np.full((H, W), default, arr.dtype)
    x0,y0,x1,y1 = img_bbox
    cx0, cy0, cx1, cy1 = max(x0,0), max(y0,0), min(x1,W), min(y1,H)
    if cx1 > cx0 and cy1 > cy0:
        full[cy0:cy1, cx0:cx1] = arr[cy0-y0:cy1-y0, cx0-x0:cx1-x0]
    return full

def mask_of(l):
    if not l.has_mask() or l.mask.disabled: return None
    m = l.mask; im = m.topil()
    if im is None or m.bbox[2] <= m.bbox[0]:
        return np.full((H, W), m.background_color, np.uint8)
    return place(m.bbox, np.asarray(im.convert('L')), m.background_color)

def walk(container, gmask, path):
    global far_px
    base = None
    for l in container:                     # bottom -> top
        nm = path + '/' + l.name
        if l.is_group():
            base = None
            if not l.visible: log.append(f'skip hidden group {nm}'); continue
            m = mask_of(l)
            g = gmask if m is None else (m if gmask is None else (gmask.astype(np.uint16)*m//255).astype(np.uint8))
            walk(l, g, nm); continue
        if l.kind == 'solidcolorfill' and l.name == 'DELETE ME':
            log.append(f'skip {nm} (white fill named DELETE ME)'); continue
        if l.kind != 'pixel':
            log.append(f'UNHANDLED {l.kind} {nm}'); continue
        if not l.visible:
            log.append(f'skip hidden {nm}')
            if not l.clipping: base = None
            continue
        im = l.topil()
        if im is None: continue
        rgba = np.asarray(im.convert('RGBA'))
        a = place(l.bbox, rgba[...,3]).astype(np.uint16)
        if l.opacity != 255: a = a*l.opacity//255
        m = mask_of(l)
        if m is not None: a = a*m//255
        if gmask is not None: a = a*gmask//255
        if l.clipping:
            if base is None: log.append(f'clipped layer without base {nm}'); continue
            a = a*base//255
        else:
            base = a.astype(np.uint8)
        a = a.astype(np.uint8)
        x0,y0,x1,y1 = l.bbox
        cx0, cy0, cx1, cy1 = max(x0,0), max(y0,0), min(x1,W), min(y1,H)
        # one ink per layer: the main ink of its solid pixels (own alpha >= 250)
        sub = rgba[cy0-y0:cy1-y0, cx0-x0:cx1-x0]
        sol = sub[...,3] >= 250
        if sol.sum() < 50: sol = sub[...,3] > 0
        rgb = sub[...,:3][sol].astype(np.float32)
        if len(rgb) == 0: continue
        if len(rgb) > 400000: rgb = rgb[::len(rgb)//400000 + 1]
        d = np.stack([((rgb - pal[i])**2).sum(1) for i in range(len(names))], 0); ink_px = d.argmin(0)
        for k,v in alias_rgb.items():
            hit = np.abs(rgb - v).max(1) <= 6; ink_px[hit] = names.index(ALIAS[k]); alias_px[k] += int(hit.sum())
        far_px += int((np.sqrt(d.min(0)) > 40).sum())
        share = np.bincount(ink_px, minlength=len(names)) / len(ink_px)
        i = int(share.argmax())
        second = sorted(((share[j], names[j]) for j in range(len(names)) if j != i), reverse=True)[0]
        if second[0] > 0.02: log.append(f'WARNING {nm}: {second[0]*100:.1f}% of solid px are {second[1]} (whole layer treated as {names[i]})')
        # coverage, top ink, composite in ink colours, and the original look (layer's own rgb)
        cv = cover[i, cy0:cy1, cx0:cx1]; av = a[cy0:cy1, cx0:cx1]
        np.maximum(cv, av, out=cv)
        # replay: a solid paint of this ink wipes every ink that will sit ABOVE it in the new
        # (darkest-on-top) order, because in the original this ink covered them here.
        solid_here = av >= 128
        for j in range(len(names)):
            if j != i and names[j] != 'paper' and LST[j] < LST[i]:
                pj = plate[j, cy0:cy1, cx0:cx1]; pj[solid_here] = 0
        if names[i] != 'paper':
            pi = plate[i, cy0:cy1, cx0:cx1]; np.maximum(pi, av, out=pi)
        vv = vis[cy0:cy1, cx0:cx1]; vv[av >= 128] = i
        LAYER_NO[0] += 1; k = LAYER_NO[0]
        for r0 in range(0, cy1-cy0, 256):
            r1 = min(cy1-cy0, r0+256)
            af = (av[r0:r1].astype(np.float32)/255)[..., None]
            cc = comp[cy0+r0:cy0+r1, cx0:cx1].astype(np.float32)
            comp[cy0+r0:cy0+r1, cx0:cx1] = (cc*(1-af) + sub[r0:r1,:,:3].astype(np.float32)*af + .5).astype(np.uint8)
        counts = {names[i]: int((av > 0).sum())}
        log.append(f'{nm}: {sum(counts.values()):,} px -> {counts}' + (' [clipped]' if l.clipping else '') + (' [mask]' if m is not None else ''))

walk(p, None, '')
np.save(out+'_cover.npy', cover); np.save(out+'_plate.npy', plate); np.save(out+'_vis.npy', vis); np.save(out+'_comp.npy', comp)
json.dump(dict(names=names, inks=INKS, W=W, H=H, log=log, far_px=far_px, alias_px=alias_px), open(out+'_meta.json','w'), indent=1)
print('\n'.join(log[-12:])); print('far-from-any-ink px:', far_px, 'alias px:', alias_px)
for i,n in enumerate(names): print(f'{n:8s} coverage {int((cover[i]>0).sum()):>11,}  visible on top {int((vis==i).sum()):>11,}')
print('nothing visible:', int((vis<0).sum()))
