import numpy as np, json, cv2
from PIL import Image
import sys; J=sys.argv[1]
names=['Layer 1','ORANGE','RED','SHADOW PURPLE','SHADOW KEY']; op=[1,1,1,128/255,128/255]
T=json.load(open(f'{J}/traps.json'))['traps']; mc=json.load(open(f'{J}/mask_colors.json'))
s=2
L=lambda i: np.asarray(np.load(f'Luke/before/{i}.npy',mmap_mode='r')[::s,::s]).astype(np.float32)
paper=L(0)[...,:3]
# client composite (true pixels, layer opacity)
o=paper.copy()
for k in range(5):
    a=L(k+1); A=a[...,3:4]/255*op[k]; o=o*(1-A)+a[...,:3]*A
key=L(6); KA=key[...,3:4]/255
client=o*(1-KA)+key[...,:3]*KA
# panel result: CLEAN + traps filled with mask colour, group opacity
rd=lambda p: (np.array(Image.open(p))[::s,::s,3]>0)
fin={}
o=paper.copy()
for k,n in enumerate(names):
    m=rd(f'{J}/clean_masks/CLEAN__{n}.png'); clean=m.copy()
    for t in T:
        if t['source']==n: m|=rd(f"{J}/{t['png']}")
    fin[n]=m
    c=np.array([mc[n][x] for x in 'rgb'],np.float32)
    A=m[...,None].astype(np.float32)*op[k]; o=o*(1-A)+c*A
res=o*(1-KA)+key[...,:3]*KA
import cv2
d=np.abs(cv2.GaussianBlur(client,(0,0),1.5)-cv2.GaussianBlur(res,(0,0),1.5)).max(-1); ch=d>12
K=key[...,3]>=90
print(f'visible change: {100*ch.mean():.2f}% of print ({int(ch.sum())*s*s:,} px)')
# causes
cl={k:L(k+1)[...,3] for k in range(5)}
soft=np.zeros_like(ch)
for k in range(5): soft|=(cl[k]>0)&(cl[k]<250)
print(f'  in soft-edge zones of any layer {100*(ch&soft).mean():.2f}% | in solid areas {100*(ch&~soft).mean():.2f}%')
# per layer: where layer's final != client presence (solid areas, visible)
for k,n in enumerate(names):
    cpres=cl[k]>=128; fpres=fin[n]
    above_opaque=np.zeros_like(ch)
    for j in range(k+1,5):
        if op[j]>0.99: above_opaque|=cl[j]>=128
    above_opaque|=K
    lost=ch&~soft&cpres&~fpres&~above_opaque
    added=ch&~soft&~cpres&fpres
    print(f'  {n:14s}: solid visible area LOST {int(lost.sum())*s*s:>9,} | ADDED {int(added.sum())*s*s:>9,}')
np.save(sys.argv[2],ch)
