import numpy as np, json, sys
from PIL import Image
d=sys.argv[1]; out=sys.argv[2]; crop=None if len(sys.argv)<4 else tuple(map(int,sys.argv[3].split(','))); scale=float(sys.argv[4]) if len(sys.argv)>4 else 0.15
m=json.load(open(f'{d}/meta.json'))
x0,y0,x1,y1=crop if crop else (0,0,m['W'],m['H'])
o=None
for i,name,mode,_ in m['layers']:
    a=np.load(f'{d}/{i}.npy',mmap_mode='r')[y0:y1,x0:x1].astype(np.float32)
    if o is None: o=a[...,:3].copy(); continue
    A=a[...,3:4]/255; c=a[...,:3]
    top=o*c/255 if 'MULTIPLY' in mode else c
    o=o*(1-A)+top*A
im=Image.fromarray(np.clip(o,0,255).astype(np.uint8))
im=im.resize((int(im.width*scale),int(im.height*scale)),Image.LANCZOS if scale<1 else Image.NEAREST); im.save(out)
