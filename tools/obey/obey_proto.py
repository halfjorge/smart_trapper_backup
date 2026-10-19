import numpy as np,sys,json
from scipy import ndimage
from PIL import Image,ImageDraw
W,H=9600,12000
names=['Yellow','Cream','Red','Light Blue','Blue','Dark blue']
L=np.load('labels.npy',mmap_mode='r')
def mask(n,box):
    x0,y0,x1,y1=box
    a=np.load(f'a_{n}.npy',mmap_mode='r')
    # unpack rows
    rowbytes=W//8
    rows=np.unpackbits(np.asarray(a[y0*rowbytes:y1*rowbytes])).reshape(y1-y0,W)
    return rows[:,x0:x1].astype(bool)
order=['CLEAN__Yellow','TRAP__Yellow_under_Key','TRAP__Yellow_under_Blue','TRAP__Yellow_under_Light Blue','TRAP__Yellow_under_Red','TRAP__Yellow_under_Cream',
'CLEAN__Cream','TRAP__Cream_under_Key','TRAP__Cream_under_Blue','TRAP__Cream_under_Light Blue','TRAP__Cream_under_Red',
'CLEAN__Red','TRAP__Red_under_Key','TRAP__Red_under_Blue','TRAP__Red_under_Light Blue',
'CLEAN__Light Blue','TRAP__Light Blue_under_Key','TRAP__Light Blue_under_Blue',
'CLEAN__Blue','TRAP__Blue_under_Key','TRAP__Blue_under_Dark blue',
'CLEAN__Dark blue','TRAP__Dark blue_under_Key','Key']
col={'Yellow':(234,180,73),'Cream':(239,226,194),'Red':(195,33,36),'Light Blue':(57,180,198),'Blue':(76,137,166),'Dark blue':(14,63,93),'Key':(7,26,41)}
cn=lambda n:'Key' if n=='Key' else n.split('__')[1].split('_under_')[0]
def render(M,keyshow):
    h,w=M['Key'].shape
    img=np.zeros((h,w,3),np.uint8); img[:]=(248,239,229)
    for n in order:
        m=M[n]
        if n=='Key':
            if keyshow: img[m]=(img[m]*0.45+np.array(col['Key'])*0.55).astype(np.uint8)
        else: img[m]=col[cn(n)]
    return img
def fitline(P):
    c=P.mean(0); _,_,vt=np.linalg.svd(P-c); return c,vt[0],vt[1]
def resplit(M,box,jx,jy,A,B,fitR,R=40,trap=12,shallow=25):
    x0,y0,x1,y1=box
    Ls=np.asarray(L[y0:y1,x0:x1]); K=Ls==7
    a_id,b_id=names.index(A)+1,names.index(B)+1
    SA=Ls==a_id; SB=Ls==b_id
    gx,gy=jx-x0,jy-y0
    # sub-pixel A|B edge points: midpoints between 4-neighbour A/B pairs, outside the key
    pts=[]
    for dy,dx in((0,1),(1,0)):
        a=SA[:SA.shape[0]-dy,:SA.shape[1]-dx]; b=SB[dy:,dx:]
        a2=SB[:SA.shape[0]-dy,:SA.shape[1]-dx]; b2=SA[dy:,dx:]
        ys,xs=np.nonzero((a&b)|(a2&b2)); pts.append(np.stack([xs+dx/2,ys+dy/2],1))
    P=np.vstack(pts).astype(float)
    d=np.hypot(P[:,0]-gx,P[:,1]-gy); P=P[d<fitR]
    c,dirv,nrm=fitline(P)
    # does the extended A|B line actually head into the key? (not running along the key edge)
    dS=ndimage.distance_transform_edt(~(SA|SB))
    ok=False
    for sgn in (1,-1):
        px,py=gx+sgn*dirv[0]*4,gy+sgn*dirv[1]*4
        if 0<=int(py)<K.shape[0] and 0<=int(px)<K.shape[1] and K[int(py),int(px)]:
            qx,qy=gx+sgn*dirv[0]*trap,gy+sgn*dirv[1]*trap
            if 0<=int(qy)<K.shape[0] and 0<=int(qx)<K.shape[1]:
                ok = K[int(qy),int(qx)] and dS[int(qy),int(qx)]>=trap*0.42
    ang=90 if ok else 0
    yy,xx=np.mgrid[0:y1-y0,0:x1-x0]
    dA=ndimage.distance_transform_edt(~SA); dB=ndimage.distance_transform_edt(~SB)
    TA=M[f'TRAP__{A}_under_Key'];TB=M[f'TRAP__{B}_under_Key']
    zone=(np.hypot(xx-gx,yy-gy)<R)&K
    U=zone&(TA|TB|((np.minimum(dA,dB)<=trap)))
    if ang>=shallow:
        side=(xx-c[0])*nrm[0]+(yy-c[1])*nrm[1]
        if side[SA&(np.hypot(xx-gx,yy-gy)<15)].mean()<0: side=-side
        ownA=side>=0
    else:
        ownA=dA<dB+0.01
        ownA=ndimage.median_filter(ownA.astype(np.uint8),size=5).astype(bool)
    newA=U&ownA; newB=U&~ownA
    M=dict(M)
    M[f'TRAP__{A}_under_Key']=(TA&~zone)|newA
    M[f'TRAP__{B}_under_Key']=(TB&~zone)|newB
    for X,keep in ((A,ownA),(B,~ownA)):
        cl=M[f'CLEAN__{X}']; M[f'CLEAN__{X}']=cl&~(zone&~keep)
    return M,ang
def load(box): return {n:mask(n,box) for n in order}
