# Measure a REAL panel run (a TrapJobs\<doc>__UXP__<time> folder copied from Sara's PC) against
# the client file. Useful when Sara says "read latest": copy the run folder's job.json, traps.json,
# trapper_bridge_log.txt, clean_masks/ and traps/ here, extract the client before file with
# extract.py / tifflayers.py, then:
#   python3 runcheck.py <run folder> <client before dir (from extract.py)> [--save final.npy]
# Reports: visible change vs client (outside key), butt px, trap px at open edges, % of key area
# with colour under it, total ink. Assumes all colours are Normal/opaque (easy files); overlay
# (Multiply/Darken) files need a blend-aware composite - see PROJECT_NOTES "Next session".
import sys, json, argparse, numpy as np, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
ap = argparse.ArgumentParser(); ap.add_argument('run'); ap.add_argument('client'); ap.add_argument('--save')
a = ap.parse_args()
j = json.load(open(a.run + '/job.json'))
print({k: j.get(k) for k in ['alphaThreshold', 'edgeBiasPx', 'keyTrapPullbackPx', 'colorTrapPullbackPx', 'trapShape', 'closeKeyHaloPx']})
cols = [c['name'] for c in j['colors']]
meta = json.load(open(a.client + '/meta.json'))
names = [x[1] for x in meta['layers']]
lb = {n: np.load(f'{a.client}/{i}.npy', mmap_mode='r') for i, n in enumerate(names)}
TH = int(j.get('alphaThreshold') or 90)
K = np.asarray(lb[j['keyLayerName']][..., 3]) >= TH
san = lambda s: ''.join('_' if ch in '/\\:*?"<>|' else ch for ch in s)
F = {c: np.array(Image.open(f'{a.run}/clean_masks/CLEAN__{san(c)}.png'))[..., 3] > 0 for c in cols}
for t in json.load(open(a.run + '/traps.json'))['traps']:
    if t['source'] in F: F[t['source']] |= np.array(Image.open(a.run + '/' + t['png']))[..., 3] > 0
B = {c: np.asarray(lb[c][..., 3]) >= TH for c in cols}
H, W = K.shape
def top(S):
    t = np.zeros((H, W), np.int16)
    for i, c in enumerate(cols): t[S[c]] = i + 1
    return t
vf, vb = top(F), top(B); nK = ~K; k3 = np.ones((3, 3), np.uint8)
butt = np.zeros((H, W), bool); oe = np.zeros((H, W), bool)
for i, c in enumerate(cols):
    vi = vf == i + 1
    butt |= cv2.dilate(vi.astype(np.uint8), k3).astype(bool) & (vf > i + 1) & ~F[c] & nK
    hid = F[c] & (vf > i + 1) & nK
    oe |= hid & cv2.dilate(((vf < i + 1) & nK).astype(np.uint8), k3).astype(bool)
anyc = np.zeros((H, W), bool)
for c in cols: anyc |= F[c]
print(f'visible change vs client {((vf != vb) & nK).sum():,} | butt px {butt.sum():,} | trap at open edge {oe.sum():,} | '
      f'colour under key {(anyc & K).sum() / max(K.sum(), 1) * 100:.1f}% | ink {sum(int(F[c].sum()) for c in cols):,}')
if a.save: np.save(a.save, np.stack([F[c] for c in cols]))
