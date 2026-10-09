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
def erode(x,r,shape):
    if r<=0: return x
    if shape=='disk': k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*r+1,2*r+1))
    elif shape=='square': k=np.ones((2*r+1,2*r+1),np.uint8)
    else: k=cv2.getStructuringElement(cv2.MORPH_CROSS,(3,3)); return cv2.erode(x,k,iterations=r)
    return cv2.erode(x,k,borderType=cv2.BORDER_REPLICATE)
for n in order[:-1]:
    above=order[order.index(n)+1:]
    print(f'## {n!r} (above: {above})  actual after: {A[n].sum():,}px')
    best=None
    for mode in ['each','union']:
        for shape in ['disk','square','diamond']:
            for r in range(3,8):
                if mode=='each':
                    cut=np.zeros((H,W),np.uint8)
                    for u in above: cut|=erode(B[u],r,shape)
                else:
                    un=np.zeros((H,W),np.uint8)
                    for u in above: un|=B[u]
                    cut=erode(un,r,shape)
                pred=B[n]&(1-cut)
                fp=int((pred&(1-A[n])).sum()); fn=int((A[n]&(1-pred)).sum())
                score=(fp+fn)/max(1,A[n].sum())
                if best is None or score<best[0]: best=(score,mode,shape,r,fp,fn)
                print(f'   {mode:5s} {shape:7s} r={r}: predicted-but-absent {fp:>9,}  present-but-not-predicted {fn:>9,}  ({score*100:.2f}% mismatch)')
    print('  BEST:',best)
