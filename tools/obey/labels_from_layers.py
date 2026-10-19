# labels.npy = top-most visible art colour per pixel (COLOR__ layers, stack order), Key = 7, paper = 0.
# Usage: python3 labels_from_layers.py LDIR   (writes labels.npy in cwd)
import sys, json, numpy as np
W, H = 9600, 12000; LD = sys.argv[1]
Ls = json.load(open(f'{LD}/layers.json')); idx = {l['name']: l['index'] for l in Ls}
ld = lambda i: np.unpackbits(np.load(f'{LD}/m_{i}.npy'))[:W*H].reshape(H, W).astype(bool)
names = ['Yellow', 'Cream', 'Red', 'Light Blue', 'Blue', 'Dark blue']
L = np.zeros((H, W), np.uint8)
for i, n in enumerate(names): L[ld(idx[f'COLOR__{n}'])] = i + 1
L[ld(idx['Key'])] = 7
np.save('labels.npy', L); print(np.bincount(L.ravel(), minlength=8))
