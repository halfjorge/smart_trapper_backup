import numpy as np, json, sys, cv2
job=sys.argv[1]; off=int(sys.argv[2]) if len(sys.argv)>2 else 0
def load(d):
    m=json.load(open(d+'/meta.json')); return [x[1] for x in m['layers']],[np.load(f'{d}/{i}.npy',mmap_mode='r') for i in range(len(m['layers']))]
nb,lb=load(f'{job}/before'); na,la=load(f'{job}/after')
H,W=lb[0].shape[:2]
def m(l):
    x=l[...,3]>127
    if x.shape!=(H,W): x=x[off:off+H,off:off+W]
    return np.ascontiguousarray(x).astype(np.uint8)
B={n:m(lb[i]) for i,n in enumerate(nb) if i>0}; A={n:m(la[na.index(n)]) for n in na[1:] if n in B}
order=[n for n in na[1:] if n in B]
for n in order[:-1]:
    above=order[order.index(n)+1:]
    upB=np.zeros((H,W),np.uint8)
    for u in above: upB|=B[u]
    vis=B[n]&(1-upB)
    inv=(1-vis).astype(np.uint8)
    d2=cv2.distanceTransform(inv,cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    dc=cv2.distanceTransform(inv,cv2.DIST_C,3)
    d1=cv2.distanceTransform(inv,cv2.DIST_L1,3)
    zone=(upB==1)  # where this colour could be kept (under something)
    print(f'## {n!r}: share of pixels kept, by distance from visible edge (only places under other colours)')
    for name,d in [('round (L2)',d2),('square (chessboard)',dc),('diamond (L1)',d1)]:
        line=[]
        for k in range(1,13):
            sel=zone&(d>k-0.5)&(d<=k+0.5) if name.startswith('round') else zone&(np.round(d)==k)
            t=sel.sum()
            line.append(f'{k}:{(A[n][sel].sum()/t*100 if t else 0):.0f}%')
        print(f'   {name:20s}',' '.join(line))
