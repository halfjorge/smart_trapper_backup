# Layered PSD from gray_trap.py output (Prepare Import layout): paper, COLOR__ groups (CLEAN__ + TRAP__), key.
import sys, os, json, gc, numpy as np
sys.path.insert(0, '/home/claude/psdsrc/src')
from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer, Group
from psd_tools.constants import Compression, BlendMode
EX, OUT, outp = sys.argv[1:4]
m = json.load(open(f'{EX}/before/meta.json')); L = m['layers']; PAPER = [int(x) for x in os.environ.get('PAPER_LAYERS', '0').split(',')]
order = [l[0] for l in L if l[0] not in PAPER]; key = order[-1]; cols = order[:-1]
names = {l[0]: l[1].strip() for l in L}; opac = {l[0]: (l[4] if len(l) > 4 else 255) for l in L}
raw = {i: np.load(f'{EX}/before/{i}.npy', mmap_mode='r') for i in order}
H, W = raw[key].shape[:2]
rgb = {i: np.median(np.asarray(raw[i][::8, ::8, :3])[np.asarray(raw[i][::8, ::8, 3]) > 240], axis=0).astype(np.uint8) for i in order}
R = np.load(f'{OUT}/result.npz'); tg = json.load(open(f'{OUT}/result_targets.json'))
tname = lambda t: 'KEY' if t == 'KEY' else names[int(t.split('_')[0][1:])]
psd = PSDImage.new('RGBA', (W, H), color=(255, 255, 255, 255))
def add(alpha, parent, name, c, visible=True):
    ys = np.where(alpha.any(1))[0]; xs = np.where(alpha.any(0))[0]
    if len(ys) == 0: return
    y0, y1, x0, x1 = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
    a = np.zeros((y1 - y0, x1 - x0, 4), np.uint8); a[..., :3] = c; a[..., 3] = alpha[y0:y1, x0:x1]
    l = PixelLayer.frompil(Image.fromarray(a, 'RGBA'), parent, name, top=int(y0), left=int(x0)); l.visible = visible
    print(' layer', name, flush=True)
pp = PAPER[-1]; paper_rgb = np.median(np.asarray(np.load(f'{EX}/before/{pp}.npy', mmap_mode='r')[::16, ::16, :3]).reshape(-1, 3), axis=0).astype(np.uint8)
mult = {i: 'MULTIPLY' in L[i][2] for i in order}
add(np.full((H, W), 255, np.uint8), psd, names[pp].strip() if pp else 'WHITE PAPER', paper_rgb)
fin = {}
for i in cols:
    g = Group.new(psd, f'COLOR__{names[i]}')
    if opac[i] < 255: g.opacity = opac[i]
    if mult[i]: g.blend_mode = BlendMode.MULTIPLY
    ca = R[f'clean_{i}']; add(ca, g, f'CLEAN__{names[i]}', rgb[i]); U = ca.copy()
    for k, t in enumerate(tg[str(i)]):
        ta = R[f'trap_{i}_{k}']; add(ta, g, f'TRAP__{names[i]}_under_{"KEY " + names[key] if t == "KEY" else tname(t)}', rgb[i]); U = np.maximum(U, ta)
    fin[i] = U; gc.collect()
ka = np.ascontiguousarray(raw[key][..., 3]); add(ka, psd, names[key] + ' (KEY, client layer)', rgb[key])
planes = [np.empty((H, W), np.uint8) for _ in range(3)]
for y0 in range(0, H, 256):
    y1 = min(H, y0 + 256); o = np.broadcast_to(paper_rgb.astype(np.float32), (y1 - y0, W, 3)).copy()
    for i in cols:
        A = fin[i][y0:y1, :, None].astype(np.float32) / 255 * opac[i] / 255; o = o * (1 - A) + ((o * rgb[i] / 255) if mult[i] else rgb[i]) * A
    A = ka[y0:y1, :, None].astype(np.float32) / 255; o = o * (1 - A) + rgb[key] * A
    o = np.clip(o + .5, 0, 255).astype(np.uint8)
    for c in range(3): planes[c][y0:y1] = o[..., c]
psd._record.header.channels = 3
psd._record.image_data.compression = Compression.RLE
psd._record.image_data.set_data([p.tobytes() for p in planes], psd._record.header)
psd._update_preview = lambda: None
psd.save(outp); print('saved', outp)
