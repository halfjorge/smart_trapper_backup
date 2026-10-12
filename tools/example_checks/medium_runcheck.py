# Measure a real Photoshop run (TrapJobs folder) against the client file, blend-aware.
#   python3 medium_runcheck.py <TrapJobs run folder> <example dir with before/ from extract.py>
import json, sys, numpy as np, cv2
from PIL import Image
run, ex = sys.argv[1], sys.argv[2]
m = json.load(open(f'{ex}/before/meta.json'))['layers']
L = [np.load(f'{ex}/before/{i}.npy', mmap_mode='r') for i in range(len(m))]
H, W = L[0].shape[:2]
def ink(l):
    a = np.asarray(l[...,3]) > 127
    return np.array([np.median(np.asarray(l[...,c])[a]) for c in range(3)])
paper = ink(L[0]); names = [x[1] for x in m]
mode = {n: ('MULTIPLY' if 'MULTIPLY' in x[2] else 'DARKEN' if 'DARKEN' in x[2] else 'NORMAL') for n, x in zip(names, m)}
col = {n: ink(l) for n, l in zip(names, L)}
alpha = {n: np.asarray(l[...,3]) for n, l in zip(names, L)}
cols = names[1:-1]; key = names[-1]
def comp(layers):
    o = np.empty((H, W, 3), np.float32); o[:] = paper
    for a, c, md in layers:
        A = (a.astype(np.float32) / (1 if a.dtype == bool else 255))[..., None]
        top = o * c / 255 if md == 'MULTIPLY' else np.minimum(o, c) if md == 'DARKEN' else np.broadcast_to(c, o.shape)
        o = o * (1 - A) + top * A
    return np.clip(o + .5, 0, 255).astype(np.uint8)
client = comp([(alpha[n], col[n], mode[n]) for n in names[1:]])
rd = lambda p: np.array(Image.open(p))[..., 3]
T = json.load(open(f'{run}/traps.json'))['traps']
final = {}
for n in cols:
    f = rd(f'{run}/clean_masks/CLEAN__{n}.png') > 0
    for t in T:
        if t['source'] == n: f |= rd(f"{run}/{t['png']}") > 0
    final[n] = f
res = comp([(final[n], col[n], mode[n]) for n in cols] + [(alpha[key], col[key], 'NORMAL')])
soft = np.zeros((H, W), np.uint8)
for n in names[1:]: soft |= ((alpha[n] > 0) & (alpha[n] < 255)).astype(np.uint8)
soft = cv2.dilate(soft, np.ones((5, 5), np.uint8)).astype(bool)
ch = np.abs(res.astype(np.int16) - client.astype(np.int16)).max(2) > 12
print(f'visible change: total {ch.sum():,} ({ch.mean()*100:.2f}%), soft-edge zone {(ch&soft).sum():,}, solid areas {(ch&~soft).sum():,} ({(ch&~soft).mean()*100:.3f}%)')
# MPK check: exported masks vs client alpha
B = {n: alpha[n] >= 128 for n in names[1:]}
K = B[key]
msk = {n: rd(f'{run}/masks/{i+1}_{n}.png') >= 128 for i, n in enumerate(cols)}
for n in cols:
    for g in cols:
        if names.index(g) <= names.index(n) or mode[g] == 'NORMAL': continue
        z = B[n] & B[g] & ~K
        print(f'  {n} under overlay {g} (outside key): client {z.sum():,} px, kept by knockout {(z & msk[n]).sum()/max(z.sum(),1)*100:.1f}%, kept in final {(z & final[n]).sum()/max(z.sum(),1)*100:.1f}%')
    kz = B[n] & K
    print(f'  {n} under key: client {kz.sum():,} px, after knockout {(kz & msk[n]).sum():,}')
dk = cv2.distanceTransform(K.astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
for n in cols:
    k = final[n] & K
    if k.any(): d = dk[k]; print(f'  {n} under key depth p50/p90/p99: {np.percentile(d,50):.1f} / {np.percentile(d,90):.1f} / {np.percentile(d,99):.1f}')
