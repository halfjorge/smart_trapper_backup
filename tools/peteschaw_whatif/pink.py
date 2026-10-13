import json, sys, numpy as np, cv2
from PIL import Image
R=sys.argv[1]
j=json.load(open(f'{R}/job.json')); key=j['keyLayerName']; cols=[c['name'] for c in j['colors']]; T=json.load(open(f'{R}/traps.json'))['traps']
rd=lambda p: np.array(Image.open(p))[...,3]
K=rd(f"{R}/masks/KEY_{key}.png")>=90
L={}
for n in cols:
    m=rd(f'{R}/clean_masks/CLEAN__{n}.png')>0
    for t in T:
        if t['source']==n: m|=rd(f"{R}/{t['png']}")>0
    L[n]=m
top=np.zeros(K.shape,np.int16)
for i,n in enumerate(cols): top[L[n]]=i+1
V=np.where(K,-1,top)
# raw nearest visible (no sliver absorption), exact
best=np.full(K.shape,1e9,np.float32); raw=np.zeros(K.shape,np.int16)
for c in range(0,len(cols)+1):
    d=cv2.distanceTransform((V!=c).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    u=d<best-1e-4; best[u]=d[u]; raw[u]=c
# key px directly touching visible blue (<=1.5) where olive or marigold is on top
for o in (2,1):
    bad=K&(raw==3)&(best<=1.5)&(top==o)&(top!=3)
    print(cols[o-1],'on top right next to visible blue (<=1.5px):',int(bad.sum()))
bad=K&(raw==3)&(best<=1.5)&(top<3)
touch=K&(raw==3)&(best<=1.5)
print('key px touching visible blue:',int(touch.sum()),' wrong colour on top:',int(bad.sum()))
# is the blue next to them a thin part (<3px) lying near lower colour -> absorbed?
vb=(V==3).astype(np.uint8)
thick=cv2.morphologyEx(vb,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)).astype(bool)
thin=(V==3)&~thick
near_thin=cv2.dilate(thin.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
print('  of those, next to a thin (<3px) part of the blue shape:',int((bad&near_thin).sum()))
np.save('pink_bad.npy',bad)
ys,xs=np.nonzero(bad); idx=np.random.default_rng(0).choice(len(xs),6,replace=False); print([(int(xs[i]),int(ys[i])) for i in idx])
