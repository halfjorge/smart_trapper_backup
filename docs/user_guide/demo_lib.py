"""Run the REAL Smart Trapper engine on small test art and render pictures for the user guide."""
import json, os, shutil, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ENGINE = '/home/claude/work/kit/build_new/target/release/smart_trapper_b1'
WORK = '/home/claude/work/guide/jobs'
PAPER = np.array([246, 240, 226], float)          # cream poster paper
BASE = dict(preflightCleanup=True, alphaThreshold=90, edgeBiasPx=1, keyTrapPullbackPx=1, colorTrapPullbackPx=0,
            trapShape='round', closeKeyHaloPx=0, overlayMode=False, smoothKeyTraps=False, bevelKeyCorners=False,
            keyTrapsFollowVisible=False, tonalInks=False)

def run(name, H, W, colors, key, settings, trap_px=5):
    """colors: list bottom->top of dict(name, rgb, alpha uint8 HxW, blend='normal', opacity=100).
    key: dict(rgb, alpha). Masks must already be knocked out the way the panel's knockout would leave them.
    Returns dict with per-colour final coverage (clean + traps, 0..1), clean, traps list, key alpha."""
    out = os.path.join(WORK, name); shutil.rmtree(out, ignore_errors=True); os.makedirs(out + '/masks'); os.makedirs(out + '/traps')
    def save(a, p, rgb):
        x = np.zeros((H, W, 4), np.uint8); x[..., :3] = rgb; x[..., 3] = a; Image.fromarray(x).save(out + '/' + p)
    files = [dict(kind='KEY', name='key', blendMode='normal', opacity=100, fillOpacity=100, png='masks/KEY.png')]
    save(key['alpha'], 'masks/KEY.png', key['rgb'])
    cols = []
    for i, c in enumerate(colors):
        p = f'masks/{i+1}.png'; save(c['alpha'], p, c['rgb'])
        bm = c.get('blend', 'normal'); op = c.get('opacity', 100)
        files.append(dict(kind='COLOR', name=c['name'], blendMode=bm, opacity=op, fillOpacity=100, png=p))
        cols.append(dict(name=c['name'], blendMode=bm, opacity=op, fillOpacity=100))
    job = dict(docName=name, widthPx=W, heightPx=H, resolution=300, keyLayerName='key', paperLayerName='paper',
               colors=cols, files=files); job.update(BASE); job.update(settings)
    json.dump(job, open(out + '/job.json', 'w'), indent=1)
    r = subprocess.run([ENGINE, out, str(trap_px)], capture_output=True, text=True)
    if r.returncode: raise SystemExit(name + ' ENGINE FAILED\n' + r.stdout[-800:] + r.stderr[-800:])
    traps = json.load(open(out + '/traps.json'))['traps']
    res = dict(H=H, W=W, colors=colors, key=key, clean={}, trap={}, traps=traps, job=job)
    for c in colors:
        n = c['name']; cp = f"{out}/clean_masks/CLEAN__{re.sub(r'[/:*?<>|]', '_', n)}.png"
        if os.path.exists(cp): a = np.array(Image.open(cp).convert('RGBA'))[..., 3].astype(float) / 255
        else: a = c['alpha'].astype(float) / 255
        res['clean'][n] = a; res['trap'][n] = np.zeros((H, W))
    for t in traps:
        a = np.array(Image.open(out + '/' + t['png']).convert('RGBA'))[..., 3].astype(float) / 255
        res['trap'][t['source']] = np.maximum(res['trap'][t['source']], a)
    res['trap_px'] = int(sum((res['trap'][c['name']] > 0).sum() for c in colors))
    return res

def _shift(a, dy, dx):
    if a is None: return None
    b = np.zeros_like(a); H, W = a.shape
    ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
    xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
    b[yd, xd] = a[ys, xs]; return b

def composite(res, shifts=None, key_alpha_scale=1.0, show_traps=False, key_outline=False):
    """Print simulation: paper, then each colour (clean + trap) bottom->top, key on top.
    shifts: {name or 'key': (dy, dx)} to simulate the press being off register."""
    H, W = res['H'], res['W']; img = np.ones((H, W, 3)) * PAPER
    shifts = shifts or {}
    for c in res['colors']:
        n = c['name']; rgb = np.array(c['rgb'], float)
        clean = res['clean'][n]; trap = res['trap'][n]
        if n in shifts: clean = _shift(clean, *shifts[n]); trap = _shift(trap, *shifts[n])
        cov = np.maximum(clean, trap)[..., None]
        if c.get('blend') == 'multiply':
            img = img * (1 - cov) + (img * rgb / 255) * cov
        else:
            img = img * (1 - cov) + rgb * cov
    k = res['key']['alpha'].astype(float) / 255
    if 'key' in shifts: k = _shift(k, *shifts['key'])
    k = (k * key_alpha_scale)[..., None]
    img = img * (1 - k) + np.array(res['key']['rgb'], float) * k
    if show_traps:   # draw each hidden trap ON TOP, in its own colour with white stripes
        yy, xx = np.mgrid[:H, :W]; white = (((yy + xx) // 2) % 2 == 0)
        for c in res['colors']:
            n = c['name']; t = (res['trap'][n] > 0) & (res['clean'][n] < 0.5)
            if n in shifts: t = _shift(t.astype(np.uint8), *shifts[n]) > 0
            img[t & ~white] = np.array(c['rgb'], float)
            img[t & white] = 255
    if key_outline:
        kb = res['key']['alpha'] > 127
        if 'key' in shifts: kb = _shift(kb.astype(np.uint8), *shifts['key']) > 0
        edge = kb & ~(np.roll(kb, 1, 0) & np.roll(kb, -1, 0) & np.roll(kb, 1, 1) & np.roll(kb, -1, 1))
        img[edge] = [20, 20, 20]
    return np.clip(img, 0, 255).astype(np.uint8)

def zoom(img, s):
    return np.repeat(np.repeat(img, s, 0), s, 1)

def font(sz, bold=False):
    for p in (['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'] if bold else []) + ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()

def panel_grid(rows, col_titles, path, scale=4, row_titles=None):
    """rows: list of lists of HxWx3 uint8 images. Writes one PNG with titles."""
    ims = [[Image.fromarray(zoom(im, scale)) for im in r] for r in rows]
    w = max(i.width for r in ims for i in r); h = max(i.height for r in ims for i in r)
    pad, top, left = 14, 34, (150 if row_titles else 0)
    G = Image.new('RGB', (left + len(col_titles) * (w + pad) + pad, top + len(ims) * (h + pad) + pad), 'white')
    d = ImageDraw.Draw(G)
    for j, t in enumerate(col_titles):
        d.text((left + pad + j * (w + pad), 8), t, fill=(20, 20, 20), font=font(18, True))
    for i, r in enumerate(ims):
        if row_titles:
            d.multiline_text((8, top + i * (h + pad) + h // 2 - 20), row_titles[i], fill=(60, 60, 60), font=font(14), spacing=3)
        for j, im in enumerate(r):
            x, y = left + pad + j * (w + pad), top + i * (h + pad)
            G.paste(im, (x, y)); d.rectangle([x - 1, y - 1, x + im.width, y + im.height], outline=(170, 170, 170))
    G.save(path); return path

# ---- drawing helpers ----
def blank(H, W): return np.zeros((H, W), np.uint8)
def rect(a, y0, y1, x0, x1, v=255): a[y0:y1, x0:x1] = v; return a
def disk(H, W, cy, cx, r):
    yy, xx = np.mgrid[:H, :W]; return (((yy - cy) ** 2 + (xx - cx) ** 2) <= (r + 0.5) ** 2).astype(np.uint8) * 255
def poly(H, W, pts):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).polygon(pts, fill=255); return np.array(im)
def line(H, W, pts, width):
    im = Image.new('L', (W, H), 0); ImageDraw.Draw(im).line(pts, fill=255, width=width); return np.array(im)
def knockout(order_bottom_to_top, key=None, skip_cutters=()):
    """What the panel's Manual Progressive Knockout does: every layer above cuts the ones below
    (key included), except overlay layers (skip_cutters) which don't cut."""
    names = [n for n, _ in order_bottom_to_top]; out = {n: a.copy() for n, a in order_bottom_to_top}
    above = (key > 127) if key is not None else np.zeros_like(order_bottom_to_top[0][1], bool)
    for n in reversed(names):
        out[n][above] = 0
        if n not in skip_cutters: above = above | (out[n] > 127)
    return out

def diff_img(r_off, r_on, key_alpha_scale=0.25):
    """Show r_on with trap pixels REMOVED by the setting in magenta and ADDED in green."""
    img = composite(r_on, key_alpha_scale=key_alpha_scale, key_outline=True).astype(float)
    rem = np.zeros((r_on['H'], r_on['W']), bool); add = rem.copy()
    for c in r_on['colors']:
        n = c['name']
        a = (r_off['trap'][n] > 0) | (r_off['clean'][n] > 0.5); b = (r_on['trap'][n] > 0) | (r_on['clean'][n] > 0.5)
        rem |= a & ~b; add |= b & ~a
    img[rem] = [230, 0, 200]; img[add] = [0, 200, 90]
    return img.astype(np.uint8), int(rem.sum()), int(add.sum())

def crop(img, y0, y1, x0, x1): return img[y0:y1, x0:x1]
