# Offline what-if (no app change): bevel traps under the key where they run up to bare paper.
# Keep a trap px under the key only if  dist_to_paper >= RULE(dist_to_own_colour).
import json, sys, numpy as np, cv2
from PIL import Image, ImageDraw
R, outp = sys.argv[1], sys.argv[2]
j=json.load(open(f'{R}/job.json')); mc=json.load(open(f'{R}/mask_colors.json')); T=json.load(open(f'{R}/traps.json'))['traps']
W,H=j['widthPx'],j['heightPx']; cols=[c['name'] for c in j['colors']]; key=j['keyLayerName']
rd=lambda p: np.array(Image.open(f'{R}/{p}'))[...,3]
K=rd([f for f in j['files'] if f['kind']=='KEY'][0]['png'])>=j['alphaThreshold']
clean={n: rd(f'clean_masks/CLEAN__{n}.png')>0 for n in cols}
other={n: np.zeros((H,W),bool) for n in cols}
for s in T:
    if s['target']!=key: other[s['source']]|=rd(s['png'])>0
RULES={'NOW':None, 'A  45deg+1 (keep if paper >= own+1)':lambda o,p: p>=o+1, 'B  1.5:1 (keep if paper >= 1.5 x own)':lambda o,p: p>=1.5*o}
trapK={}; dd={}
for i,n in enumerate(cols):
    t=np.zeros((H,W),bool)
    for s in T:
        if s['source']==n and s['target']==key: t|=rd(s['png'])>0
    hidden=clean[n]|K
    for c in cols[i+1:]: hidden|=clean[c]
    dd[n]=(cv2.distanceTransform((~clean[n]).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE),
           cv2.distanceTransform(hidden.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE))
    trapK[n]=t
kept={}
for name,f in RULES.items():
    tot=0; cut=0; kept[name]={}
    for n in cols:
        t=trapK[n]
        if f is None: k=t
        else:
            o,p=dd[n]; k=t&f(o,p)
        kept[name][n]=k; tot+=t.sum(); cut+=(t&~k).sum()
    print(f'{name:42s} trap under key removed: {int(cut):>7,} of {int(tot):,} ({cut/tot*100:.2f}%)')
def view(box,sc,name):
    x0,y0,x1,y1=box; sl=(slice(y0,y1),slice(x0,x1))
    img=np.empty((y1-y0,x1-x0,3),np.float32); img[:]=(242,238,215)
    for n in cols:
        m=clean[n][sl]|other[n][sl]|kept[name][n][sl]
        img[m]=[mc[n][c] for c in 'rgb']
    ka=(K[sl]*0.68)[...,None]; img=img*(1-ka)+np.array([30,15,35])*ka
    return cv2.resize(np.clip(img,0,255).astype(np.uint8),((x1-x0)*sc,(y1-y0)*sc),interpolation=cv2.INTER_NEAREST)
boxes=[(2598,6850,2650,6890),(2728,6828,2780,6868)]
rows=[]
for name in RULES:
    tiles=[view(b,9,name) for b in boxes]
    r=np.concatenate([tiles[0],np.full((tiles[0].shape[0],12,3),255,np.uint8),tiles[1]],1)
    lab=np.full((26,r.shape[1],3),255,np.uint8); rows+= [lab, r]
im=Image.fromarray(np.concatenate(rows,0)); d=ImageDraw.Draw(im)
y=4
for name in RULES: d.text((6,y),name,fill=(0,0,0)); y+=26+40*9
im.save(outp)
