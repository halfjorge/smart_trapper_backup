import numpy as np, json, cv2
from PIL import Image
R='Bourbon_med_mpk_ov'
ma=json.load(open('Bourbon/after/meta.json')); na={n:i for i,n,_,_ in ma['layers']}
mb=json.load(open('Bourbon/before/meta.json')); nb={n:i for i,n,_,_ in mb['layers']}
j=json.load(open(f'{R}/job.json')); T=json.load(open(f'{R}/traps.json'))['traps']
names=['Yellow','Orange','Red','Green','Transparent Grey']; eng=[c['name'] for c in j['colors']]
rd=lambda p: np.array(Image.open(p))[...,3]>0
F={}
for n,e in zip(names,eng):
    m=rd(f'{R}/clean_masks/CLEAN__{e}.png')
    for t in T:
        if t['source']==e: m|=rd(f"{R}/{t['png']}")
    F[n]=m
A={n:np.load(f"Bourbon/after/{na[n]}.npy",mmap_mode='r')[...,3]>127 for n in names+['Black']}
Kc=np.load(f"Bourbon/before/{nb['Black']}.npy",mmap_mode='r')[...,3]
Ka=A['Black']
print('KEY: trapper leaves client key (soft):', int(((Kc>0)&(Kc<255)).sum()),'soft px; hand key is hard. hand key = client alpha>=112 except',int(((Kc>=112)^Ka).sum()),'px')
Kt=Kc>=89
def top(L,excl_overlay=True):
    t=np.zeros(Ka.shape,np.int8)
    for i,n in enumerate(names):
        if excl_overlay and n=='Transparent Grey': continue
        t[L[n]]=i+1
    return t
tF=top(F); tA=top(A)
vis_diff=(tF!=tA)&~Ka&~Kt
print('opaque colour showing differs (outside both keys):',int(vis_diff.sum()))
for n in names:
    f,a=F[n],A[n]
    only_h=a&~f; only_t=f&~a
    # classify by where: under key(hand), at visible edge zone
    print(f'{n:17s} hand {int(a.sum()):>10,} trapper {int(f.sum()):>10,} | only hand {int(only_h.sum()):>9,} (under key {int((only_h&Ka).sum()):,}) | only trapper {int(only_t.sum()):>9,} (under key {int((only_t&Ka).sum()):,})')
# trap depth under key: hand vs trapper, per opaque colour
for n in names:
    for lab,L,K in (('hand',A,Ka),('trapper',F,Kt)):
        vis=L[n]&~K
        d=cv2.distanceTransform((~vis).astype(np.uint8),cv2.DIST_L2,5)
        u=L[n]&K
        if u.sum(): print(f'   {n:17s} {lab:7s} under key: {int(u.sum()):>9,} px  depth p50/p90/p99 {np.percentile(d[u],[50,90,99]).round(1)}')
# paper showing
anyA=Ka.copy()
for n in names: anyA|=A[n]
anyF=Kt.copy()
for n in names: anyF|=F[n]
mx=np.zeros(Ka.shape,np.uint8)
for n in names+['Black']:
    mx=np.maximum(mx,np.load(f"Bourbon/before/{nb[n]}.npy",mmap_mode='r')[...,3])
for lab,an in (('hand',anyA),('trapper',anyF)):
    pap=~an
    print(f'{lab}: paper px {int(pap.sum()):,}; of which client had some ink (max alpha 30-111) {int((pap&(mx>=30)&(mx<112)).sum()):,}, strong ink >=112 {int((pap&(mx>=112)).sum()):,}')
# speck check: tiny islands in hand vs thresholded client
for n in ['Black','Orange']:
    a=(A[n]).astype(np.uint8); c=(np.load(f"Bourbon/before/{nb[n]}.npy",mmap_mode='r')[...,3]>=112).astype(np.uint8)
    for lab,m in (('hand',a),('client>=112',c)):
        k,_,st,_=cv2.connectedComponentsWithStats(m,connectivity=8)
        s=st[1:,4]; print(f'  {n} {lab}: islands {k-1:,}, under 10 px {(s<10).sum():,}')
