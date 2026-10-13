# Compare two finished job folders (A = today's engine, B = with "key traps follow the colour you see").
# Key moved SH px in 8 directions: where the key used to be, which colour peeks out? "Right" = the colour
# seen next to that spot in register (thin slivers count as the colour they lie against). Paper-owned spots skipped.
import json, sys, numpy as np, cv2
from PIL import Image
A,B=sys.argv[1],sys.argv[2]; SH=int(sys.argv[3]) if len(sys.argv)>3 else 2
j=json.load(open(f'{A}/job.json')); key=j['keyLayerName']; cols=[c['name'] for c in j['colors']]
ov=[bool(j.get('overlayMode')) and (c['blendMode'].lower()!='normal' or c['opacity']<100 or c['fillOpacity']<100) for c in j['colors']]
rd=lambda p: np.array(Image.open(p))[...,3]
K=rd(f"{A}/masks/KEY_{key}.png")>=max(1,j.get('alphaThreshold',0) if j.get('preflightCleanup') else 1)
def layers(R):
    T=json.load(open(f'{R}/traps.json'))['traps']; L={}
    for n in cols:
        m=rd(f'{R}/clean_masks/CLEAN__{n}.png')>0
        for t in T:
            if t['source']==n:
                p=rd(f"{R}/{t['png']}")>0; m|=p
        L[n]=m
    return L
def topof(L):
    t=np.zeros(K.shape,np.int16)
    for i,n in enumerate(cols):
        if not ov[i]: t[L[n]]=i+1
    return t
LA,LB=layers(A),layers(B); tA,tB=topof(LA),topof(LB)
V=np.where(K,-1,tA).astype(np.int16); Vp=V.copy()
for ci in range(2,len(cols)+1):
    vis=(V==ci).astype(np.uint8)
    if not vis.any(): continue
    thin=(V==ci)&~cv2.morphologyEx(vis,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)).astype(bool)
    for li in range(1,ci):
        near=cv2.dilate((V==li).astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool); Vp[thin&near&(Vp==ci)]=li
best=np.full(K.shape,1e9,np.float32); owner=np.zeros(K.shape,np.int16)
for c in range(0,len(cols)+1):
    m=(Vp==c)
    if not m.any(): continue
    d=cv2.distanceTransform((~m).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    upd=d<best-1e-4; best[upd]=d[upd]; owner[upd]=c
pb=j.get('keyTrapPullbackPx',1)
dpap=cv2.distanceTransform((Vp!=0).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
pull=dpap<=pb+0.5     # key pullback next to paper: showing nothing there is intended
ex_tot=0; bad={'A':0,'B':0}
for dy in (-SH,0,SH):
  for dx in (-SH,0,SH):
    if dx==dy==0: continue
    Ks=np.zeros_like(K); H,W=K.shape
    Ks[max(dy,0):H+min(dy,0), max(dx,0):W+min(dx,0)] = K[max(-dy,0):H+min(-dy,0), max(-dx,0):W+min(-dx,0)]
    ex=K&~Ks&(owner>0)&~pull; ex[:SH]=0; ex[-SH:]=0; ex[:,:SH]=0; ex[:,-SH:]=0; ex_tot+=int(ex.sum())   # canvas edge excluded (shift artefact)
    bad['A']+=int((ex&(tA!=owner)).sum()); bad['B']+=int((ex&(tB!=owner)).sum())
visA=np.where(K,-1,tA); visB=np.where(K,-1,tB)
# full visible check including overlays: every layer's pixels outside the key
vis_change=sum(int(((LA[n]^LB[n])&~K).sum()) for n in cols)
new=np.zeros(K.shape,bool)
for n in cols: new|=LB[n]&~LA[n]
print(f"{A.split('/')[0]:16s} cols {len(cols)} overlays {sum(ov)} | key off {SH}px: wrong colour peeking out  today {100*bad['A']/max(ex_tot,1):5.1f}%  new {100*bad['B']/max(ex_tot,1):5.1f}%"
      f" | change outside key {vis_change} px | new ink within {pb+0.5} px of paper {int((new&(dpap<=pb+0.5)).sum())}")
