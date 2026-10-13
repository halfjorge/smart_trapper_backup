# Compare the gray-aware result with the client file (blend-aware, pink at its opacity).
import sys, json, numpy as np, cv2
EX, OUT = sys.argv[1], sys.argv[2]; s = 2
m = json.load(open(f'{EX}/before/meta.json')); L = m['layers']; order = [l[0] for l in L][1:]; key = order[-1]; cols = order[:-1]
opac = {l[0]: (l[4] if len(l) > 4 else 255) / 255 for l in L}
raw = {i: np.load(f'{EX}/before/{i}.npy', mmap_mode='r') for i in order}
al = {i: np.asarray(raw[i][::s, ::s, 3]) for i in order}
rgb = {i: np.median(np.asarray(raw[i][::8, ::8, :3])[np.asarray(raw[i][::8, ::8, 3]) > 240], axis=0) for i in order}
R = np.load(f'{OUT}/result.npz'); tg = json.load(open(f'{OUT}/result_targets.json'))
fin = {}
for i in cols:
    a = R[f'clean_{i}'][::s, ::s].astype(np.float32)
    for k in range(len(tg[str(i)])): a = np.maximum(a, R[f'trap_{i}_{k}'][::s, ::s])
    fin[i] = a / 255
def comp(get):
    o = np.full(al[key].shape + (3,), 255, np.float32)
    for i in order:
        A = get(i)[..., None] * opac[i]; o = o * (1 - A) + rgb[i] * A
    return o
c = comp(lambda i: al[i] / 255.)
r = comp(lambda i: al[key] / 255. if i == key else fin[i])
ch = np.abs(c - r).max(-1) > 12
part = np.zeros_like(ch)
for i in cols: part |= (al[i] > 0) & (al[i] < 243)
print(f'visible change vs client: {100*ch.mean():.2f}% of print (soft edges/grays {100*(ch&part).mean():.2f}%, solid areas {100*(ch&~part).mean():.2f}%)')
K = al[key] >= 90
for i in cols:
    lost = (al[i] >= 90) & (fin[i] == 0) & ~K
    print(f'  colour {i}: client ink (>=35%) gone outside the key {int(lost.sum())*s*s:,} px')
for i in cols:
    g_above = np.zeros_like(K)
    for j in cols:
        if j > i and opac[j] > 0.999:
            g = (al[j] > 0) & (al[j] < 243)
            g = g & (cv2.blur(g.astype(np.float32), (3, 3)) >= 0.6)
            g_above |= g
    solid_above = np.zeros_like(K)
    for j in cols:
        if j > i and opac[j] > 0.999: solid_above |= al[j] >= 243
    under = g_above & ~K & (al[i] >= 90) & ~solid_above
    kept = under & (fin[i] > 0)
    print(f'  colour {i} under a gray part of a colour above (outside key): client {int(under.sum())*s*s:,} px, kept {100*kept.sum()/max(1,under.sum()):.1f}%')
