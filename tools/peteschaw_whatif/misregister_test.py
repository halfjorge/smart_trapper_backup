# Whole-file misregistration test: shift the key 2 px in 8 directions; where the key used to be and no longer covers,
# which colour peeks out? "right" = the colour you see next to that spot when in register (nearest visible colour,
# thin slivers counted as the colour they lie against). Compare NOW vs NEW RULE.
import json, sys, numpy as np, cv2
from PIL import Image
R=sys.argv[1]; SH=int(sys.argv[2])
j=json.load(open(f'{R}/job.json')); key=j['keyLayerName']; T=json.load(open(f'{R}/traps.json'))['traps']
cols=[c['name'] for c in j['colors']]; n_=len(cols)
rd=lambda p: np.array(Image.open(p))[...,3]
K=rd(f"{R}/masks/KEY_{key}.png")>=90
F={}
for n in cols:
    m=rd(f'{R}/clean_masks/CLEAN__{n}.png')>0
    for t in T:
        if t['source']==n: m|=rd(f"{R}/{t['png']}")>0
    F[n]=m
G=np.load('pete_owner_g.npz')
def topof(L):
    t=np.zeros(K.shape,np.int8)
    for i,n in enumerate(cols): t[L[n]]=i+1
    return t
tN=topof(F); tG=topof({n:G[n] for n in cols})
V=np.where(K,-1,tN).astype(np.int8); Vp=V.copy()
for ci in range(2,n_+1):
    vis=(V==ci).astype(np.uint8); thin=(V==ci)&~cv2.morphologyEx(vis,cv2.MORPH_OPEN,np.ones((3,3),np.uint8)).astype(bool)
    for li in range(1,ci):
        near=cv2.dilate((V==li).astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool); Vp[thin&near&(Vp==ci)]=li
src=(Vp==-1).astype(np.uint8)
dist,lab=cv2.distanceTransformWithLabels(src,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
zy,zx=np.nonzero(src==0); lut=np.zeros(lab.max()+1,np.int8); lut[lab[zy,zx]]=Vp[zy,zx]; owner=lut[lab]
names=['paper']+cols
tot={'N':0,'G':0}; exp_all=0; conf={}
for dy in (-SH,0,SH):
  for dx in (-SH,0,SH):
    if dx==dy==0: continue
    Ks=np.zeros_like(K); Ks[max(dy,0):K.shape[0]+min(dy,0), max(dx,0):K.shape[1]+min(dx,0)] = K[max(-dy,0):K.shape[0]+min(-dy,0), max(-dx,0):K.shape[1]+min(-dx,0)]
    ex=K&~Ks&(owner>0)          # exposed spots next to ink (paper-owned spots: pullback, not counted)
    exp_all+=int(ex.sum())
    for tag,t in (('N',tN),('G',tG)):
        bad=ex&(t!=owner); tot[tag]+=int(bad.sum())
        if tag in 'NG':
            for o in range(1,n_+1):
                for s in range(0,n_+1):
                    if s==o: continue
                    c=int((bad&(owner==o)&(t==s)).sum())
                    if c: conf[(tag,names[o],names[s])]=conf.get((tag,names[o],names[s]),0)+c
print(f'key shifted {SH} px, 8 directions: {exp_all:,} exposed spots next to ink')
print(f'  wrong colour peeking out  NOW: {tot["N"]:,} ({100*tot["N"]/exp_all:.1f}%)   NEW RULE: {tot["G"]:,} ({100*tot["G"]/exp_all:.1f}%)')
for k,v in sorted(conf.items(),key=lambda x:-x[1])[:12]: print('  ',k,f'{v:,}')
