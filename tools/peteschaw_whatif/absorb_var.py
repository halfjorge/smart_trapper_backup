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
V=np.where(K,-1,top); nc=len(cols)
def owner_of(Vp):
    best=np.full(K.shape,1e9,np.float32); o=np.zeros(K.shape,np.int16)
    for c in range(0,nc+1):
        d=cv2.distanceTransform((Vp!=c).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
        u=d<best-1e-4; best[u]=d[u]; o[u]=c
    dp=cv2.distanceTransform((Vp!=0).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    z=K&(best<=5)&(o>0)&(dp>1.5)
    return np.where(z,o,0), best
def absorb(core_r):
    Vp=V.copy(); info={}
    for ci in range(2,nc+1):
        vis=(V==ci).astype(np.uint8)
        thick=cv2.morphologyEx(vis,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
        thin=(V==ci)&~thick.astype(bool)
        if core_r is not None and core_r>0:
            k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*core_r+1,2*core_r+1))
            thin&=~cv2.dilate(thick,k).astype(bool)
        for li in range(1,ci):
            near=cv2.dilate((V==li).astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool); Vp[thin&near&(Vp==ci)]=li
    return Vp
raw,_=owner_of(V)
# true sliver cases: key px whose raw owner is blue, next to blue that is thin AND far from any thick blue (>3px), olive within 3px of that blue
vb=(V==3).astype(np.uint8); thick=cv2.morphologyEx(vb,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
for name,cr in [('now (any thin bit)',0),('thin bits >2px from a thick part',2),('thin bits >3px from a thick part',3),('no sliver rule',-1)]:
    Vp=V.copy() if cr==-1 else absorb(cr)
    o,_=owner_of(Vp)
    # resulting top after rule
    t=top.copy()
    for c in range(1,nc+1):
        sel=(o==c); t[sel]=c
    pink=K&(raw==3)&(t!=3)&(t>0)
    # touching visible blue <=1.5
    dB=cv2.distanceTransform((V!=3).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    pink&=dB<=1.5
    olive_fix=int(((o==2)&(top==3)).sum())
    print(f'{name:36s} lower colour right against visible blue: {int(pink.sum()):>7,} | key px where olive replaces blue on top: {olive_fix:>8,}')
print('--- keep a ring of each visible colour next to itself (sliver rule kept) ---')
Vp=absorb(0); o,_=owner_of(Vp)
dist_vis={c:cv2.distanceTransform((V!=c).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE) for c in range(1,nc+1)}
for ring in (1.5,2.0,2.3):
    o2=o.copy()
    for c in range(1,nc+1):
        o2[(dist_vis[c]<=ring)&(o2>0)&(o2<c)]=c      # first ring next to a visible colour stays that colour
    t=top.copy()
    for c in range(1,nc+1): t[o2==c]=c
    dB=dist_vis[3]
    pink=K&(dB<=1.5)&(t!=3)&(t>0)&(raw==3)
    print(f' ring {ring} px: lower colour right against visible blue {int(pink.sum()):>6,} | olive replaces blue on top {int(((o2==2)&(top==3)).sum()):>8,}')
    np.save(f'own_ring{ring}.npy',o2)
np.save('own_now.npy',o)
