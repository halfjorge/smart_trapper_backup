# Independent reference for "bevel trap corners next to paper", same definition as the engine.
import json, sys, numpy as np
from PIL import Image
base, new = sys.argv[1], sys.argv[2]       # job WITHOUT bevel (box off), job WITH bevel
j=json.load(open(f'{base}/job.json')); T=json.load(open(f'{base}/traps.json'))['traps']
W,H=j['widthPx'],j['heightPx']; cols=[c['name'] for c in j['colors']]; key=j['keyLayerName']; trap_px=5
rd=lambda p: np.array(Image.open(p))[...,3]
K=rd(f"{base}/"+[f for f in j['files'] if f['kind']=='KEY'][0]['png'])>=j['alphaThreshold']
clean={n: rd(f'{base}/clean_masks/CLEAN__{n}.png')>0 for n in cols}
def nearest(mask, ys, xs, r):
    best=np.full(len(ys),10**9,np.int64); bx=np.zeros(len(ys),np.int64); by=np.zeros(len(ys),np.int64)
    for dy in range(-r,r+1):
        for dx in range(-r,r+1):
            d2=dx*dx+dy*dy
            if d2>r*r: continue
            ny,nx=ys+dy,xs+dx; ok=(ny>=0)&(ny<H)&(nx>=0)&(nx<W)
            hit=np.zeros(len(ys),bool); hit[ok]=mask[ny[ok],nx[ok]]
            upd=hit&(d2<best); best[upd]=d2; bx[upd]=dx; by[upd]=dy
    return best,bx,by
r_own=trap_px+2; r_open=int(np.ceil(1.5*r_own))+1; total=0; bad=0
for i,n in enumerate(cols):
    hidden=clean[n]|K
    for c in cols[i+1:]: hidden|=clean[c]
    showing=~hidden
    for t in T:
        if t['source']!=n or t['target']!=key: continue
        old=rd(f"{base}/{t['png']}")>0
        ys,xs=np.nonzero(old)
        do,ox,oy=nearest(clean[n],ys,xs,r_own); dp,px,py=nearest(showing,ys,xs,r_open)
        valid=(do<10**9)&(dp<10**9)
        d_own=np.sqrt(do.astype(float)); d_open=np.sqrt(dp.astype(float))
        cos=(ox*px+oy*py)/np.maximum(d_own*d_open,1e-9)
        cut=valid&(d_open<1.5*d_own)&(cos>-np.sqrt(0.5))
        want=old.copy(); want[ys[cut],xs[cut]]=False
        got=rd(f"{new}/{t['png']}")>0
        d=int((want^got).sum()); bad+=d; total+=int(cut.sum())
        print(f'{n:8s} under key: reference removes {int(cut.sum()):>6,}, engine removes {int((old&~got).sum()):>6,}, differ {d} px')
    for t in T:
        if t['source']==n and t['target']!=key:
            same=np.array_equal(rd(f"{base}/{t['png']}")>0, rd(f"{new}/{t['png']}")>0)
            if not same: print('  CHANGED non-key trap', t['png']); bad+=1
print('ENGINE == REFERENCE' if bad==0 else f'DIFFER {bad}')
