# Simulate key misregistration (key shifted dx,dy) with the key at 100%: NOW vs NEW RULE
import json, sys, numpy as np
from PIL import Image, ImageDraw
R,outp,dx,dy=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4]); spots=[tuple(map(int,s.split(','))) for s in sys.argv[5:]]
j=json.load(open(f'{R}/job.json')); key=j['keyLayerName']; T=json.load(open(f'{R}/traps.json'))['traps']; mc=json.load(open(f'{R}/mask_colors.json'))
cols=[c['name'] for c in j['colors']]; own=np.load('pete_owner_g.npz')
rd=lambda p: np.array(Image.open(p))[...,3]
Kf=rd(f"{R}/masks/KEY_{key}.png")>=90
F={}
for n in cols:
    m=rd(f'{R}/clean_masks/CLEAN__{n}.png')>0
    for t in T:
        if t['source']==n: m|=rd(f"{R}/{t['png']}")>0
    F[n]=m
r=26; sc=10; rows=[]
for cx,cy in spots:
    sl=(slice(cy-r,cy+r),slice(cx-r,cx+r))
    Ks=Kf[cy-r-dy:cy+r-dy, cx-r-dx:cx+r-dx]
    def view(L,K):
        img=np.full(K.shape+(3,),255,np.uint8)
        for n in cols: img[L[n][sl]]=[mc[n][c] for c in 'rgb']
        img[K]=[mc[key][c] for c in 'rgb'] if key in mc else [16,24,48]
        return img
    panels=[view(F,Kf[sl]),view(F,Ks),view(own,Ks)]
    row=np.concatenate([np.pad(np.kron(p,np.ones((sc,sc,1),np.uint8)),((0,0),(0,10),(0,0)),constant_values=255) for p in panels],1)
    rows.append(np.pad(row,((24,6),(0,0),(0,0)),constant_values=255))
im=Image.fromarray(np.concatenate(rows,0)); d=ImageDraw.Draw(im); w=2*r*sc+10
for k,s in enumerate(['in register',f'key off by {dx},{dy} px - NOW',f'key off by {dx},{dy} px - NEW RULE']): d.text((k*w+6,6),s,fill=(0,0,0))
im.save(outp)
