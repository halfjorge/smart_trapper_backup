# Independent check (doesn't trust the engine's own compare): every trap/clean PNG alpha, pixel by pixel.
import json,sys,os,numpy as np
from PIL import Image
a,b=sys.argv[1],sys.argv[2]
ta=json.load(open(a+'/traps.json')); tb=json.load(open(b+'/traps.json'))
assert ta==tb, "traps.json differs"
files=[t['png'] for t in ta['traps']]+['clean_masks/'+f for f in sorted(os.listdir(a+'/clean_masks'))]
bad=0; total_on=0
for f in files:
    x=np.array(Image.open(f'{a}/{f}'))[...,3]>0; y=np.array(Image.open(f'{b}/{f}'))[...,3]>0
    d=int((x!=y).sum()); total_on+=int(x.sum()); bad+=d
    if d: print('DIFF',f,d)
print(f"{len(files)} files compared, {total_on:,} ink pixels, {bad} pixels different")
