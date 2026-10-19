# Print a per-pixel map of which colour layers (clean/trap) cover each pixel in a small box.
import sys, json, numpy as np
sys.path.insert(0, '/home/claude/smart_trapper_backup/tools/obey')
from render import crop, ink_layers
D, pre = sys.argv[1], sys.argv[6] if len(sys.argv) > 6 else 'm_'
x0, y0, x1, y1 = map(int, sys.argv[2:6])
code = {'Yellow': 'y', 'Cream': 'c', 'Red': 'r', 'Light Blue': 'l', 'Blue': 'b', 'Dark blue': 'd'}
grid = [['' for _ in range(x1-x0)] for _ in range(y1-y0)]
key = None
for l in ink_layers(D):
    m = crop(f'{D}/{pre}{l["index"]}.npy', x0, y0, x1, y1)
    if l['name'] == 'Key': key = m; continue
    col = l['name'].split('COLOR__')[1].split('_under_')[0]
    ch = code[col].upper() if l['name'].startswith('CLEAN') else code[col]
    for y, x in zip(*np.nonzero(m)): grid[y][x] += ch
for y in range(y1-y0):
    print(f'{y0+y:5d} ' + ''.join(('#' if key[y, x] else ' ') + (g[:2].ljust(2) if g else '..') for x, g in enumerate(grid[y])))
