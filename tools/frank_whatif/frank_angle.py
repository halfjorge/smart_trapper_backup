import json, sys, numpy as np, cv2
from PIL import Image
R=sys.argv[1]
j=json.load(open(f'{R}/job.json')); T=json.load(open(f'{R}/traps.json'))['traps']
W,H=j['widthPx'],j['heightPx']; cols=[c['name'] for c in j['colors']]; key=j['keyLayerName']
rd=lambda p: np.array(Image.open(f'{R}/{p}'))[...,3]
K=rd([f for f in j['files'] if f['kind']=='KEY'][0]['png'])>=j['alphaThreshold']
clean={n: rd(f'clean_masks/CLEAN__{n}.png')>0 for n in cols}
ys_all=np.arange(H)[:,None]; xs_all=np.arange(W)[None,:]
def nearest(mask_is_target):
    # distance and nearest target pixel coords (target = zero pixels of src)
    src=(~mask_is_target).astype(np.uint8)
    d,lab=cv2.distanceTransformWithLabels(src,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
    zy,zx=np.nonzero(src==0); ly=np.zeros(lab.max()+1,np.int32); lx=np.zeros(lab.max()+1,np.int32)
    ly[lab[zy,zx]]=zy; lx[lab[zy,zx]]=zx
    return d, ly[lab], lx[lab]
res={'A':[0,0,0],'B':[0,0,0]}; shallow={'A':0,'B':0}; tot=0
for i,n in enumerate(cols):
    t=np.zeros((H,W),bool)
    for s in T:
        if s['source']==n and s['target']==key: t|=rd(s['png'])>0
    if not t.any(): continue
    hidden=clean[n]|K
    for c in cols[i+1:]: hidden|=clean[c]
    do,oy,ox=nearest(clean[n]); dp,py,px=nearest(~hidden)
    yy,xx=np.nonzero(t); tot+=len(yy)
    vo=np.stack([oy[yy,xx]-yy, ox[yy,xx]-xx],1).astype(np.float32); vp=np.stack([py[yy,xx]-yy, px[yy,xx]-xx],1).astype(np.float32)
    cosang=(vo*vp).sum(1)/np.maximum(np.linalg.norm(vo,axis=1)*np.linalg.norm(vp,axis=1),1e-6)
    lateral = cosang > np.cos(np.radians(135))   # paper beside / ahead, not straight across
    o=do[yy,xx]; p=dp[yy,xx]
    for name,f in (('A',lambda o,p: p>=o+1),('B',lambda o,p: p>=1.5*o)):
        cut=~f(o,p)
        res[name][0]+=int(cut.sum()); res[name][1]+=int((cut&lateral).sum()); res[name][2]+=int((cut&~lateral).sum())
        shallow[name]+=int((cut&(o<=3)&~lateral).sum())
print(f'trap under key total {tot:,} px')
for k,v in res.items():
    print(f'rule {k}: cuts {v[0]:,} px = corners/paper beside {v[1]:,} + across key lines (paper on far side) {v[2]:,}; of those across-line cuts, within 3 px of the colour: {shallow[k]:,}')
