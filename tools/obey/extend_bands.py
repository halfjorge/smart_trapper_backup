# Carry trap bands into the key: where A's trap under B (TRAP__A_under_B) runs into the key, continue that band
# straight on under the key (its own direction over the last few px) up to the key trap depth. Adds to
# TRAP__A_under_Key only. This covers the corner where A, B and the key meet.
import numpy as np, json, sys
from scipy import ndimage
D=sys.argv[1]; W,H=9600,12000; RB=W//8; KT=12
names=['Yellow','Cream','Red','Light Blue','Blue','Dark blue']
L=np.load(f'{D}/labels.npy',mmap_mode='r')
def full(n): return np.unpackbits(np.load(f'{D}/j_{n}.npy'))[:W*H].reshape(H,W).astype(bool)
added_total=0
KF=np.asarray(L)==7
KF2=ndimage.binary_dilation(KF,iterations=2)
for ai,A in enumerate(names):
    tgt=f'TRAP__{A}_under_Key'
    try: TK=full(tgt)
    except FileNotFoundError: continue
    add=np.zeros((H,W),bool)
    for B in names:
        n=f'TRAP__{A}_under_{B}'
        try: band=full(n)
        except FileNotFoundError: continue
        bi=names.index(B)+1
        # band pixels touching the key
        lab,k=ndimage.label(ndimage.binary_dilation(band,iterations=1)&KF2&band,np.ones((3,3)))
        for s in ndimage.find_objects(lab):
            cy=(s[0].start+s[0].stop)//2; cx=(s[1].start+s[1].stop)//2; r=40
            y0,y1,x0,x1=max(0,cy-r),min(H,cy+r),max(0,cx-r),min(W,cx+r)
            Ls=np.asarray(L[y0:y1,x0:x1]); K=Ls==7; bd=band[y0:y1,x0:x1]&~K
            gx,gy=cx-x0,cy-y0
            ys,xs=np.nonzero(bd)
            if len(ys)<15: continue
            dd=np.hypot(xs-gx,ys-gy); sel=dd<15
            if sel.sum()<10: continue
            Q=np.stack([xs[sel],ys[sel]],1).astype(float); c=Q.mean(0); _,_,vt=np.linalg.svd(Q-c); dv=vt[0]
            # direction pointing into the key
            sgn=0
            for sg in (1,-1):
                px,py=int(round(gx+sg*dv[0]*5)),int(round(gy+sg*dv[1]*5))
                if 0<=py<K.shape[0] and 0<=px<K.shape[1] and K[py,px]: sgn=sg
            if sgn==0: continue
            dv=dv*sgn
            # how far the colours reach into the key (trap depth limit)
            src=(Ls==ai+1)|(Ls==bi)
            dS=ndimage.distance_transform_edt(~src)
            edge=band[y0:y1,x0:x1]&ndimage.binary_dilation(K,iterations=2)
            ey,ex=np.nonzero(edge)
            sub=np.zeros_like(K)
            for k in range(0,KT+2):
                py=np.rint(ey+dv[1]*k).astype(int); px=np.rint(ex+dv[0]*k).astype(int)
                ok=(py>=0)&(py<K.shape[0])&(px>=0)&(px<K.shape[1])
                sub[py[ok],px[ok]]=True
            sub=ndimage.binary_closing(sub,iterations=1)&K&(dS<=KT)
            add[y0:y1,x0:x1]|=sub
    new=add&~TK
    if new.any():
        np.save(f'{D}/j_{tgt}.npy',np.packbits((TK|add).ravel())); print(tgt,'band carried into key, px',int(new.sum()))
        added_total+=int(new.sum())
    del TK,add
print('total',added_total)
