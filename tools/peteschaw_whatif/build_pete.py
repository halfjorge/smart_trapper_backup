# Layered Peteschaw PSD from an engine run folder (same layer structure as Prepare Import).
import sys, json, gc, numpy as np
sys.path.insert(0,'/home/claude/psdsrc/src')
from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer, Group
from psd_tools.constants import Compression
run, saras, outp = sys.argv[1:4]
job=json.load(open(f'{run}/job.json')); key=job['keyLayerName']; paper=job['paperLayerName']
cols=[c['name'] for c in job['colors']]; mc=json.load(open(f'{run}/mask_colors.json')); T=json.load(open(f'{run}/traps.json'))['traps']
W,H=job['widthPx'],job['heightPx']
rd=lambda p: np.array(Image.open(p))[...,3]>0
psd=PSDImage.new('RGBA',(W,H),color=(255,255,255,255))
def add(mask,parent,name,rgb,visible=True):
    ys=np.where(mask.any(1))[0]; xs=np.where(mask.any(0))[0]
    if len(ys)==0: print('empty',name); return
    y0,y1,x0,x1=ys[0],ys[-1]+1,xs[0],xs[-1]+1
    sub=mask[y0:y1,x0:x1]; a=np.zeros(sub.shape+(4,),np.uint8); a[...,:3]=rgb; a[...,3]=sub*255
    l=PixelLayer.frompil(Image.fromarray(a,'RGBA'),parent,name,top=int(y0),left=int(x0)); l.visible=visible; print(' layer',name); return l
add(np.ones((H,W),bool),psd,paper,(255,255,255))
final=[]
top_new=np.zeros((H,W),np.int8)
for i,n in enumerate(cols):
    rgb=(mc[n]['r'],mc[n]['g'],mc[n]['b']); g=Group.new(psd,f'COLOR__{n}')
    c=rd(f'{run}/clean_masks/CLEAN__{n}.png'); add(c,g,f'CLEAN__{n}',rgb); U=c.copy()
    for t in T:
        if t['source']!=n: continue
        m=rd(f"{run}/{t['png']}"); add(m,g,f"TRAP__{n}_under_{t['target']}",rgb); U|=m
    final.append((U,np.array(rgb,np.float32))); top_new[U]=i+1; gc.collect()
keyrgba=np.array(Image.open(f"{run}/masks/KEY_{key}.png").convert('RGBA'))
K=keyrgba[...,3]>=90
kr=tuple(int(v) for v in np.median(keyrgba[K][:,:3],axis=0))
add(K,psd,key,kr)
# hidden check layer: spots where your 14:12 run had olive/marigold butting visible blue
import cv2
Ts=json.load(open(f'{saras}/traps.json'))['traps']; top_s=np.zeros((H,W),np.int8)
for i,n in enumerate(cols):
    m=rd(f'{saras}/clean_masks/CLEAN__{n}.png')
    for t in Ts:
        if t['source']==n: m|=rd(f"{saras}/{t['png']}")
    top_s[m]=i+1
V=np.where(K,-1,top_s); dB=cv2.distanceTransform((V!=3).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
pink=K&(dB<=1.5)&(top_s>0)&(top_s<3)
add(pink,psd,'CHECK - butted blue in your 14:12 run (fixed here)',(255,0,200),visible=False)
print('pink in her run',int(pink.sum()),' pink here',int((K&(dB<=1.5)&(top_new>0)&(top_new<3)).sum()))
planes=[np.empty((H,W),np.uint8) for _ in range(3)]
for y0 in range(0,H,256):
    y1=min(H,y0+256); o=np.full((y1-y0,W,3),255,np.float32)
    for U,c in final:
        A=U[y0:y1,:,None].astype(np.float32); o=o*(1-A)+c*A
    A=K[y0:y1,:,None].astype(np.float32); o=o*(1-A)+np.array(kr,np.float32)*A
    o=np.clip(o+.5,0,255).astype(np.uint8)
    for ci in range(3): planes[ci][y0:y1]=o[...,ci]
psd._record.header.channels=3
psd._record.image_data.compression=Compression.RLE
psd._record.image_data.set_data([p.tobytes() for p in planes],psd._record.header)
psd._update_preview=lambda: None
psd.save(outp); print('saved',outp)
