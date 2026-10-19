# Layered PSD from joint_fix.py output, laid out like the trapper's own output.
import sys, gc, numpy as np
sys.path.insert(0,'/home/claude/psdsrc/src')
from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer, Group
from psd_tools.constants import Compression
D,pre,outp=sys.argv[1:4]
W,H=9600,12000;RB=W//8
names=['Yellow','Cream','Red','Light Blue','Blue','Dark blue']
col={'Yellow':(234,180,73),'Cream':(239,226,194),'Red':(195,33,36),'Light Blue':(57,180,198),'Blue':(76,137,166),'Dark blue':(14,63,93),'Key':(7,26,41)}
import glob,os
avail=[os.path.basename(p)[len(pre)+1:-4] for p in glob.glob(f'{D}/{pre}_*.npy')]
def full(n,p=pre): return np.unpackbits(np.load(f'{D}/{p}_{n}.npy'))[:W*H].reshape(H,W).astype(bool)
psd=PSDImage.new('RGBA',(W,H),color=(255,255,255,255))
def add(m,parent,name,c,visible=True,opacity=255):
    ys=np.where(m.any(1))[0]; xs=np.where(m.any(0))[0]
    if len(ys)==0: return
    y0,y1,x0,x1=ys[0],ys[-1]+1,xs[0],xs[-1]+1
    a=np.zeros((y1-y0,x1-x0,4),np.uint8); a[...,:3]=c; a[...,3]=m[y0:y1,x0:x1]*255
    l=PixelLayer.frompil(Image.fromarray(a,'RGBA'),parent,name,top=int(y0),left=int(x0)); l.visible=visible; l.opacity=opacity
    print(' layer',name,flush=True)
add(np.ones((H,W),bool),psd,'Cougar Natural 100#C',(248,239,229))
comp=np.zeros((H,W,3),np.uint8); comp[:]=(248,239,229)
changed=np.zeros((H,W),bool)
for X in names:
    g=Group.new(psd,f'COLOR__{X}')
    for n in [f'CLEAN__{X}']+sorted(a for a in avail if a.startswith(f'TRAP__{X}_under_')):
        m=full(n); add(m,g,n,col[X]); comp[m]=col[X]
        changed|=m^full(n,'a'); del m; gc.collect()
k=full('Key'); add(k,psd,'Key',col['Key']); comp[k]=col['Key']
add(changed,psd,'JOINT_FIX_CHANGES (magenta, turn on to see what moved)',(255,0,255),visible=False)
del k,changed; gc.collect()
psd._record.header.channels=3
psd._record.image_data.compression=Compression.RLE
psd._record.image_data.set_data([np.ascontiguousarray(comp[...,c]).tobytes() for c in range(3)],psd._record.header)
psd._update_preview=lambda: None
psd.save(outp); print('saved',outp)
