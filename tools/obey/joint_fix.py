# Offline what-if: "straight / follow-the-edge joints" for every trap zone (under the key AND under every colour).
# Input: packed full-size masks a_<layer>.npy (from obey_diff.py) + labels.npy (top-most visible source colour).
# Output: j_<layer>.npy packed masks + joint_log.json
import numpy as np, json, sys
from scipy import ndimage
D=sys.argv[1] if len(sys.argv)>1 else '.'
W,H=9600,12000; RB=W//8
names=['Yellow','Cream','Red','Light Blue','Blue','Dark blue','Key']   # stacking order bottom->top
L=np.load(f'{D}/labels.npy')
import glob,os
layers=[os.path.basename(p)[2:-4] for p in glob.glob(f'{D}/a_*.npy')]
P={n:np.load(f'{D}/a_{n}.npy').copy() for n in layers}           # packed, modified in place
def get(n,box):
    x0,y0,x1,y1=box
    return np.unpackbits(P[n][y0*RB:y1*RB]).reshape(y1-y0,W)[:,x0:x1].astype(bool)
def put(n,box,m):
    x0,y0,x1,y1=box
    rows=np.unpackbits(P[n][y0*RB:y1*RB]).reshape(y1-y0,W); rows[:,x0:x1]=m
    P[n][y0*RB:y1*RB]=np.packbits(rows.ravel())
def sh(a,dy,dx):
    o=np.zeros_like(a); h,w=a.shape
    o[max(-dy,0):h+min(-dy,0),max(-dx,0):w+min(-dx,0)]=a[max(dy,0):h+min(dy,0),max(dx,0):w+min(dx,0)]; return o
def fitline(Q):
    c=Q.mean(0); _,_,vt=np.linalg.svd(Q-c); return c,vt[0],vt[1]
FITR=12; R=40; log=[]
for ti,T in enumerate(names):
    tid=ti+1
    under=[X for X in names[:ti] if f'TRAP__{X}_under_{T}' in P]
    if len(under)<2: continue
    Tm=L==tid; nearT=ndimage.binary_dilation(Tm,iterations=3)
    J=np.zeros((H,W),bool); pair=np.zeros((H,W),np.uint8)
    ids=[names.index(X)+1 for X in under]
    isU=np.isin(L,ids)
    for dy,dx in((0,1),(1,0),(0,-1),(-1,0)):
        n=sh(L,dy,dx); m=isU&np.isin(n,ids)&(n!=L)&nearT
        J|=m; pair[m]=(np.minimum(L,n)*10+np.maximum(L,n))[m]
    del nearT,isU
    lab,nj=ndimage.label(ndimage.binary_dilation(J,iterations=2))
    cents=[]
    for s in ndimage.find_objects(lab):
        jy,jx=np.nonzero(J[s]); 
        if len(jy)==0: continue
        pv=np.bincount(pair[s][J[s]]).argmax()
        cents.append((jx.mean()+s[1].start,jy.mean()+s[0].start,pv//10,pv%10))
    del J,pair,lab,Tm
    print(T,'joints',len(cents),flush=True)
    C=np.array([[c[0],c[1]] for c in cents]) if cents else np.zeros((0,2))
    for k,(jx,jy,a,b) in enumerate(cents):
        A,B=names[a-1],names[b-1]
        others=np.delete(C,k,0)
        r=R
        if len(others): r=min(R,max(6,np.hypot(*(others-[jx,jy]).T).min()/2))
        pad=60
        box=(int(max(0,jx-pad)),int(max(0,jy-pad)),int(min(W,jx+pad)),int(min(H,jy+pad)))
        x0,y0,x1,y1=box; gx,gy=jx-x0,jy-y0
        Ls=L[y0:y1,x0:x1]; K=Ls==tid; SA=Ls==a; SB=Ls==b
        pts=[]
        for dy,dx in((0,1),(1,0)):
            h,w=SA.shape
            m=(SA[:h-dy,:w-dx]&SB[dy:,dx:])|(SB[:h-dy,:w-dx]&SA[dy:,dx:])
            ys,xs=np.nonzero(m); pts.append(np.stack([xs+dx/2,ys+dy/2],1))
        Q=np.vstack(pts).astype(float); Q=Q[np.hypot(Q[:,0]-gx,Q[:,1]-gy)<FITR]
        if len(Q)<4: log.append([T,A,B,int(jx),int(jy),'skip-few-points']); continue
        c,dirv,nrm=fitline(Q)
        # only clearly straight edges get a straight joint: the A|B edge must stay within 1 px of one
        # straight line for 30 px back from the joint. Curvy pattern joints keep the trapper's split.
        Q30=np.vstack(pts).astype(float); Q30=Q30[np.hypot(Q30[:,0]-gx,Q30[:,1]-gy)<30]
        straight=False
        if len(Q30)>=20:
            c30,d30,n30=fitline(Q30); straight=float(np.abs((Q30-c30)@n30).max())<=1.0
        TA=get(f'TRAP__{A}_under_{T}',box); TB=get(f'TRAP__{B}_under_{T}',box)
        CA=get(f'CLEAN__{A}',box); CB=get(f'CLEAN__{B}',box)
        dA=ndimage.distance_transform_edt(~SA); dB=ndimage.distance_transform_edt(~SB)
        trap=max(dA[TA].max() if TA.any() else 0, dB[TB].max() if TB.any() else 0)
        if trap<1: continue
        dS=np.minimum(dA,dB); ok=False
        for sgn in (1,-1):
            px,py=int(gx+sgn*dirv[0]*min(4,trap)),int(gy+sgn*dirv[1]*min(4,trap))
            if 0<=py<K.shape[0] and 0<=px<K.shape[1] and K[py,px]:
                qx,qy=int(gx+sgn*dirv[0]*trap),int(gy+sgn*dirv[1]*trap)
                if 0<=qy<K.shape[0] and 0<=qx<K.shape[1]:
                    ok = bool(K[qy,qx] and dS[qy,qx]>=trap*0.42) and straight
        yy,xx=np.mgrid[0:y1-y0,0:x1-x0]
        if ok:
            # the line must go INTO T fairly squarely (within 45 deg of straight in); a line that only grazes
            # T's edge would hand a long wedge of the trap zone to one colour
            dK=ndimage.distance_transform_edt(K)
            gyy,gxx=np.gradient(ndimage.gaussian_filter(dK,1.5))
            disk=K&(np.hypot(xx-gx,yy-gy)<=min(6,trap))
            nv=np.array([gxx[disk].mean(),gyy[disk].mean()]) if disk.any() else np.zeros(2)
            if np.hypot(*nv)>1e-6:
                nv=nv/np.hypot(*nv)
                if abs(float(dirv@nv))<0.707: ok=False
        # only the joint itself is re-split: about one trap width around it. Further along the edge the
        # nearest colour keeps its trap (otherwise a slanted line hands neighbouring trap to the wrong colour)
        zone=(np.hypot(xx-gx,yy-gy)<min(r,1.5*trap+1))&K
        cur=(TA|TB|CA|CB)&zone
        U=cur   # never grow a trap here; pin-holes are closed separately (tidy.py)
        if ok:
            side=(xx-c[0])*nrm[0]+(yy-c[1])*nrm[1]
            sel=SA&(np.hypot(xx-gx,yy-gy)<15)
            if sel.any() and side[sel].mean()<0: side=-side
            ownA=side>=0; mode='line'
        else:
            # not a joint the line can run into: keep the trapper's split, only remove stray pixels
            Uc=(TA|TB|CA|CB)&zone
            ownB=(TB|CB)&Uc            # B sits above A in the stack, so where both exist B is what shows
            flipped=0
            for _ in range(3):
                nb=ndimage.convolve(ownB.astype(np.uint8)&Uc,np.ones((3,3),np.uint8),mode='constant')
                nu=ndimage.convolve(Uc.astype(np.uint8),np.ones((3,3),np.uint8),mode='constant')
                toB=Uc&~ownB&(nb*2>nu); toA=Uc&ownB&(nb*2<nu-1)
                if not (toB.any() or toA.any()): break
                flipped+=int(toB.sum()+toA.sum()); ownB=(ownB|toB)&~toA
            if flipped==0:
                log.append([T,A,B,int(jx),int(jy),'split-clean-already',0]); continue
            showB0=(TB|CB)&Uc
            toBf=Uc&ownB&~showB0; toAf=Uc&~ownB&showB0
            nA=(TA&~toBf)|toAf; nB=(TB&~toAf)|toBf
            nCA=CA&~toBf; nCB=CB&~toAf
            ch=int((nA!=TA).sum()+(nB!=TB).sum()+(nCA!=CA).sum()+(nCB!=CB).sum())
            put(f'TRAP__{A}_under_{T}',box,nA); put(f'TRAP__{B}_under_{T}',box,nB)
            put(f'CLEAN__{A}',box,nCA); put(f'CLEAN__{B}',box,nCB)
            log.append([T,A,B,int(jx),int(jy),'despeckle',ch]); continue
        zA=U&ownA; zB=U&~ownA
        inner=ndimage.binary_erosion(zone,iterations=2)
        st=np.ones((3,3),bool)
        thinA=zA&~ndimage.binary_opening(zA,st)&inner; thinB=zB&~ndimage.binary_opening(zB,st)&inner
        zA=(zA&~thinA)|thinB; zB=(zB&~thinB)|thinA
        nA=(TA&~zone)|zA; nB=(TB&~zone)|zB
        nCA=CA&~(zone&~ownA); nCB=CB&~(zone&ownA)
        ch=int((nA!=TA).sum()+(nB!=TB).sum()+(nCA!=CA).sum()+(nCB!=CB).sum())
        if ch:
            put(f'TRAP__{A}_under_{T}',box,nA); put(f'TRAP__{B}_under_{T}',box,nB)
            put(f'CLEAN__{A}',box,nCA); put(f'CLEAN__{B}',box,nCB)
        log.append([T,A,B,int(jx),int(jy),mode,ch])
for n,p in P.items(): np.save(f'{D}/j_{n}.npy',p)
json.dump(log,open(f'{D}/joint_log.json','w'),indent=0)
from collections import Counter
print(Counter((l[0],l[5]) for l in log))
print('pixels changed',sum(l[6] for l in log if len(l)>6))
