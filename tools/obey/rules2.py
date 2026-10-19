# Two more what-if rules, run after joint_fix.py + tidy.py.
# 1) Stray pixels under the key: a tiny island (<= 6 px) of one colour's ink inside another colour's trap
#    under the key goes to the colour around it (fixes the tie "dots").
# 2) Trap bands carry into the key: where A traps under B (TRAP__A_under_B) and that band runs into the key,
#    the band is carried straight on under the key, as deep as the key trap, as TRAP__A_under_Key.
import numpy as np, json, sys
from scipy import ndimage
D=sys.argv[1]; W,H=9600,12000; KT=12
names=['Yellow','Cream','Red','Light Blue','Blue','Dark blue']
vis=json.load(open(f'{D}/vis_layers.json'))
ld=lambda n: np.unpackbits(np.load(f'{D}/j_{n}.npy'))[:W*H].reshape(H,W).astype(bool)
sv=lambda n,m: np.save(f'{D}/j_{n}.npy',np.packbits(m.ravel()))
L=np.load(f'{D}/labels.npy'); K=L==7
# ---------- 1) stray pixels under the key
# Each pixel under the key gets a "which colours are here" code. A tiny island (<= 6 px) whose code differs from
# what clearly surrounds it (>= 60% of its under-key neighbours) takes the surrounding code: missing colours are
# added as TRAP__X_under_Key, extra colours are taken off. Under the key only, so the print does not change.
S=np.zeros((H,W),np.uint8)
for n in vis:
    if n=='Key': continue
    X=n.split('__')[1].split('_under_')[0]; S|=(ld(n).astype(np.uint8)<<names.index(X))
Su=np.where(K,S,255).astype(np.uint8)
addm={X:np.zeros((H,W),bool) for X in names}; remm={X:np.zeros((H,W),bool) for X in names}
st=np.ones((3,3),bool); total=0
for code in np.unique(Su[K]):
    m=Su==code
    lab,nl=ndimage.label(m,st)
    if nl==0: continue
    sizes=ndimage.sum(m,lab,range(1,nl+1)); sl=ndimage.find_objects(lab)
    for c in np.nonzero(sizes<=6)[0]+1:
        s=sl[c-1]; ys=slice(max(0,s[0].start-1),s[0].stop+1); xs=slice(max(0,s[1].start-1),s[1].stop+1)
        comp=lab[ys,xs]==c; ring=ndimage.binary_dilation(comp,st)&~comp&K[ys,xs]
        nb=Su[ys,xs][ring]
        if len(nb)<3: continue
        vals,cnt=np.unique(nb,return_counts=True); mcode=int(vals[np.argmax(cnt)])
        if cnt.max()<0.6*len(nb) or mcode==code: continue
        for bi,X in enumerate(names):
            had=(code>>bi)&1; want=(mcode>>bi)&1
            if want and not had: addm[X][ys,xs]|=comp
            if had and not want: remm[X][ys,xs]|=comp
        total+=int(comp.sum())
for X in names:
    if addm[X].any():
        n=f'TRAP__{X}_under_Key'; sv(n,ld(n)|addm[X])
    if remm[X].any():
        for n in [f'CLEAN__{X}']+[v for v in vis if v.startswith(f'TRAP__{X}_under_')]:
            m=ld(n); r=m&remm[X]
            if r.any(): sv(n,m&~r)
print('stray pixels evened out',total,flush=True)
del S,Su,addm,remm
# ---------- 2) carry trap bands into the key
nearK=ndimage.binary_dilation(K,iterations=2)
dS=None
added=0
for n in vis:
    if not n.startswith('TRAP__') or n.endswith('_under_Key'): continue
    A=n.split('__')[1].split('_under_')[0]
    band=ld(n)&~K
    ends=band&nearK
    if not ends.any(): continue
    lab,nl=ndimage.label(ndimage.binary_dilation(ends,iterations=2),st)
    add=np.zeros((H,W),bool)
    for s in ndimage.find_objects(lab):
        y0,y1=max(0,s[0].start-30),min(H,s[0].stop+30); x0,x1=max(0,s[1].start-30),min(W,s[1].stop+30)
        b=band[y0:y1,x0:x1]; Kw=K[y0:y1,x0:x1]; e=ends[y0:y1,x0:x1]&(lab[y0:y1,x0:x1]>0)
        ey,ex=np.nonzero(e)
        if len(ey)==0: continue
        cy,cx=ey.mean(),ex.mean()
        by,bx=np.nonzero(b); near=np.hypot(by-cy,bx-cx)<16
        if near.sum()<6: continue
        P=np.stack([bx[near],by[near]],1).astype(float); c=P.mean(0); _,sv_,vt=np.linalg.svd(P-c)
        if sv_[0]<1.5*max(sv_[1],1e-6): continue        # no clear band direction here
        d=vt[0]
        # point the direction into the key
        f=lambda sg: sum(Kw[int(round(cy+sg*d[1]*k)),int(round(cx+sg*d[0]*k))] for k in range(2,8)
                         if 0<=int(round(cy+sg*d[1]*k))<Kw.shape[0] and 0<=int(round(cx+sg*d[0]*k))<Kw.shape[1])
        sg=1 if f(1)>=f(-1) else -1
        if max(f(1),f(-1))==0: continue
        # distance into the key from the non-key art: never go deeper than the key trap
        dk=ndimage.distance_transform_edt(Kw)
        a=np.zeros_like(Kw)
        for k in range(0,KT+3):
            yy=np.rint(ey+sg*d[1]*k).astype(int); xx=np.rint(ex+sg*d[0]*k).astype(int)
            ok=(yy>=0)&(yy<Kw.shape[0])&(xx>=0)&(xx<Kw.shape[1])
            yy,xx=yy[ok],xx[ok]; keep=Kw[yy,xx]&(dk[yy,xx]<=KT)
            a[yy[keep],xx[keep]]=True
        a=ndimage.binary_closing(a,st)&Kw&(dk<=KT)
        add[y0:y1,x0:x1]|=a
    if add.any():
        # the band is where A and B overlap, so under the key the carried band gets BOTH colours
        B=n.split('_under_')[1]
        for X in (A,B):
            t=f'TRAP__{X}_under_Key'; cur=ld(t); new=add&~cur
            for o in [f'CLEAN__{X}']+[v for v in vis if v.startswith(f'TRAP__{X}_under_') and v!=t]:
                new&=~ld(o)
            sv(t,cur|new); added+=int(new.sum()); print(n,'-> carried into key as',X,int(new.sum()),flush=True)
print('band px added under key',added)
