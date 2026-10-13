# Offline what-if (no app change): "under the key, the nearest visible colour owns the trap zone".
#  1. what shows with all layers on (V): paper / marigold / olive / blue
#  2. thin slivers of a higher colour lying against a lower colour count as the lower colour
#  3. every key px within TRAP px of the key edge belongs to its nearest visible colour (paper -> nothing)
#  4. that colour must be on top there: add it if missing, remove higher colours there
import json, sys, numpy as np, cv2
from PIL import Image
R=sys.argv[1]; S=sys.argv[2]; TRAP=5
j=json.load(open(f'{R}/job.json')); key=j['keyLayerName']; T=json.load(open(f'{R}/traps.json'))['traps']
cols=[c['name'] for c in j['colors']]; n_=len(cols)
rd=lambda p: np.array(Image.open(p))[...,3]
K=rd(f"{R}/masks/KEY_{key}.png")>=90
clean={n: rd(f'{R}/clean_masks/CLEAN__{n}.png')>0 for n in cols}
F={}
for n in cols:
    m=clean[n].copy()
    for t in T:
        if t['source']==n: m|=rd(f"{R}/{t['png']}")>0
    F[n]=m
H,W=K.shape
top=np.zeros((H,W),np.int8)
for i,n in enumerate(cols): top[F[n]]=i+1
V=np.where(K,-1,top).astype(np.int8)                    # what shows; -1 = key
# 2. absorb thin slivers: visible px of colour c that are < 3 px thick and touch a visible LOWER colour
Vp=V.copy(); absorbed=0
for ci in range(2,n_+1):
    vis_c=(V==ci).astype(np.uint8)
    thick=cv2.morphologyEx(vis_c,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)).astype(bool)
    thin=(V==ci)&~thick
    for li in range(1,ci):
        near_l=cv2.dilate((V==li).astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
        sel=thin&near_l&(Vp==ci)
        Vp[sel]=li; absorbed+=int(sel.sum())
print(f'thin slivers absorbed into the colour they lie against: {absorbed:,} px')
# 3. nearest visible label for key px
src=(Vp==-1).astype(np.uint8)          # zeros = visible pixels
dist,lab=cv2.distanceTransformWithLabels(src,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
zy,zx=np.nonzero(src==0); lut=np.zeros(lab.max()+1,np.int8); lut[lab[zy,zx]]=Vp[zy,zx]
owner=lut[lab]
zone=K&(dist<=TRAP)
dpap0=cv2.distanceTransform(((Vp!=0)).astype(np.uint8),cv2.DIST_L2,5)
GUARD=len(sys.argv)>3
if GUARD: zone&=dpap0>1.5   # pullback guard: never touch within 1 px of paper
print('guard', GUARD)
# nothing changes within 1 px of paper (pullback): owner paper -> leave as is
before_top=top.copy()
L={n:F[n].copy() for n in cols}
changed_add={n:0 for n in cols}; changed_rm={n:0 for n in cols}
for i,n in enumerate(cols):
    o=zone&(owner==i+1)
    add=o&~L[n]; L[n]|=add; changed_add[n]=int(add.sum())
    for c in cols[i+1:]:
        rm=o&L[c]; L[c]&=~rm; changed_rm[c]+=int(rm.sum())
after=np.zeros((H,W),np.int8)
for i,n in enumerate(cols): after[L[n]]=i+1
for i,n in enumerate(cols):
    own=zone&(owner==i+1)
    print(f'{n:16s} key px it should own: {int(own.sum()):>9,}  wrong colour on top NOW: {int((own&(before_top!=i+1)).sum()):>8,}  after: {int((own&(after!=i+1)).sum())}   (+{changed_add[n]:,} added, -{changed_rm[n]:,} removed)')
vis_after=np.where(K,-1,after)
print('visible change with all layers on:', int((vis_after!=V).sum()), 'px')
dpap=cv2.distanceTransform(((V!=0)).astype(np.uint8),cv2.DIST_L2,5)
newpx=np.zeros((H,W),bool)
for n in cols: newpx|=L[n]&~F[n]
print('new ink px within 1.5 px of paper:', int((newpx&(dpap<=1.5)).sum()))
np.savez_compressed(f'{S}/pete_owner'+('_g' if GUARD else '')+'.npz', **{n:L[n] for n in cols})
# specifically the olive case Sara described: olive-owned key px with blue on top
o=zone&(owner==2)
print(f'olive-owned key px with BLUE on top: now {int((o&(before_top==3)).sum()):,} -> after {int((o&(after==3)).sum()):,}')
