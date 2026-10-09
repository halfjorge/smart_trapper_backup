# Extract each top-level layer of a PSD as full-canvas RGBA uint8 .npy (alpha + colour).
import sys, numpy as np, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/claude/psdsrc/src')
from psd_tools import PSDImage
src, out = sys.argv[1], sys.argv[2]
import os; os.makedirs(out, exist_ok=True)
p = PSDImage.open(src)
W,H = p.width, p.height
meta=[]
for i,l in enumerate(p):
    img = l.topil()
    full = np.zeros((H,W,4),np.uint8)
    if img is not None:
        img = img.convert('RGBA'); a=np.array(img)
        x0,y0,x1,y1 = l.bbox
        full[y0:y1, x0:x1] = a[:y1-y0,:x1-x0]
    np.save(f'{out}/{i}.npy', full)
    al=full[...,3]
    meta.append((i,l.name,str(l.blend_mode),int((al>127).sum())))
    print(i, repr(l.name), l.blend_mode, 'ink px >50%:', int((al>127).sum()), 'partial px:', int(((al>0)&(al<255)).sum()))
import json; json.dump(dict(W=W,H=H,layers=meta), open(f'{out}/meta.json','w'))
