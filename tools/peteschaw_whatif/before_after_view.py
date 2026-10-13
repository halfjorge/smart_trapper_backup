import json, sys, numpy as np, cv2
from PIL import Image, ImageDraw
R, outp = sys.argv[1], sys.argv[2]; spots=[(int(a),int(b)) for a,b in (s.split(',') for s in sys.argv[3:])]
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
    sl=(slice(cy-r,cy+r),slice(cx-r,cx+r)); K=Kf[sl]
    def view(after, key_op):
        img=np.full(K.shape+(3,),255,np.float32)
        for n in cols:
            m=(own[n][sl] if after else F[n][sl])
            img[m]=[mc[n][c] for c in 'rgb']
        a=(K*key_op)[...,None]; img=img*(1-a)+np.array([16,28,48])*a
        t=cv2.resize(np.clip(img,0,255).astype(np.uint8),(2*r*sc,2*r*sc),interpolation=cv2.INTER_NEAREST)
        return t
    t=[view(False,1.0),view(False,0.56),view(True,0.56)]
    sep=np.full((2*r*sc,10,3),255,np.uint8)
    rows.append(np.concatenate([t[0],sep,t[1],sep,t[2]],1)); rows.append(np.full((10,rows[-1].shape[1],3),255,np.uint8))
im=Image.fromarray(np.concatenate([np.full((24,rows[0].shape[1],3),255,np.uint8)]+rows[:-1],0)); d=ImageDraw.Draw(im)
w=2*r*sc+10
for k,s in enumerate(['all layers (key 100%)','NOW - key at 56%','NEW RULE (paper guard) - key at 56%']): d.text((k*w+6,6),s,fill=(0,0,0))
im.save(outp)
