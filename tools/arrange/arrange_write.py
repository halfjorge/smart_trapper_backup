import sys, json, gc, numpy as np
sys.path.insert(0,'/home/claude/psdsrc/src')
from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Compression
S, src, outp = sys.argv[1:4]
m=json.load(open(f'{S}/wilco_meta.json')); o=json.load(open(f'{S}/wilco_order.json')); H,W=m['H'],m['W']
order=o['order']; names=m['names']
plate=np.load(f'{S}/wilco_plate.npy', mmap_mode='r')
hexrgb=lambda h: tuple(int(h[i:i+2],16) for i in (0,2,4))
orig=PSDImage.open(src)
psd=PSDImage.new('RGBA',(W,H),color=(255,255,255,255))
psd._record.image_resources[1005]=orig._record.image_resources[1005]   # keep 300 ppi
def add(alpha, rgb, name):
    ys,xs=np.nonzero(alpha); y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    a=np.zeros((y1-y0,x1-x0,4),np.uint8); a[...,:3]=rgb; a[...,3]=alpha[y0:y1,x0:x1]
    PixelLayer.frompil(Image.fromarray(a,'RGBA'),psd,name,top=int(y0),left=int(x0)); print('  layer',name,(x0,y0,x1,y1))
paper=m['inks']['paper']
add(np.full((H,W),255,np.uint8), hexrgb(paper), f'paper (green {paper})')
for n in reversed(order):            # lightest first = bottom
    i=names.index(n); al=np.ascontiguousarray(plate[i])
    nm=f"{n} {m['inks'][n]}" + (' (key)' if n==order[0] else '')
    add(al, hexrgb(m['inks'][n]), nm); del al; gc.collect()
new=np.load(f'{S}/wilco_new.npy', mmap_mode='r')
psd._record.header.channels=3
psd._record.image_data.compression=Compression.RLE
psd._record.image_data.set_data([np.ascontiguousarray(new[...,c]).tobytes() for c in range(3)], psd._record.header)
psd._update_preview=lambda: None
psd.save(outp); print('saved', outp)
