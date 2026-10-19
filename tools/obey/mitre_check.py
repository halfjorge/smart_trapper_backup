# Checks for mitre.py output. Usage: python3 mitre_check.py LDIR FDIR  (labels.npy in cwd)
import sys, json, os, numpy as np
from scipy import ndimage
LD, FD = sys.argv[1:3]; W, H = 9600, 12000; D = 12
Ls = json.load(open(f'{LD}/layers.json'))
L = np.load('labels.npy'); K = L == 7
zones = np.unpackbits(np.load(f'{FD}/zones.npy'))[:W*H].reshape(H, W).astype(bool)
names = ['Yellow', 'Cream', 'Red', 'Light Blue', 'Blue', 'Dark blue']
def ld(i, fixed):
    f = f'{FD}/m_{i}.npy' if fixed and os.path.exists(f'{FD}/m_{i}.npy') else f'{LD}/m_{i}.npy'
    return np.unpackbits(np.load(f))[:W*H].reshape(H, W).astype(bool)
covB = np.zeros((H, W), bool); covA = np.zeros((H, W), bool)
ok = True
for i, n in enumerate(names):
    lays = [l['index'] for l in Ls if l['visible'] and l.get('pixels') and l['name'].split('__')[0] in ('CLEAN', 'TRAP')
            and l['name'].split('COLOR__')[1].split('_under_')[0] == n]
    cb = np.zeros((H, W), np.uint8); ca = np.zeros((H, W), np.uint8)
    for j in lays: cb += ld(j, False); ca += ld(j, True)
    SB, SA = cb > 0, ca > 0
    out_k = int(((SB != SA) & ~K).sum())
    lost = SB & ~SA; gained = SA & ~SB
    lost_out = int((lost & ~zones).sum())
    print(f'{n:10s} separation changed outside key: {out_k} px | under key +{int(gained.sum())} -{int(lost.sum())} '
          f'(lost outside joint zones: {lost_out}) | doubled before {int((cb>1).sum())} after {int((ca>1).sum())}')
    ok &= out_k == 0 and int((ca > 1).sum()) == 0
    covB |= SB; covA |= SA
    del cb, ca
band = ndimage.maximum_filter((~K & (L > 0)).view(np.uint8), size=2*D + 1).astype(bool) & K
bb, ba = int((band & ~covB).sum()), int((band & ~covA).sum())
print('bare key pixels inside the trap band: before', bb, 'after', ba)
print('ALL CHECKS PASS' if ok and ba <= bb else 'CHECK FAILED')
