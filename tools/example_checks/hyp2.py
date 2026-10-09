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
K=lambda shape,r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE if shape=='disk' else cv2.MORPH_RECT,(2*r+1,2*r+1))
ero=lambda x,r,s: cv2.erode(x,K(s,r),borderType=cv2.BORDER_REPLICATE) if r>0 else x
dil=lambda x,r,s: cv2.dilate(x,K(s,r)) if r>0 else x
def score(pred,act): 
    fp=int((pred&(1-act)).sum()); fn=int((act&(1-pred)).sum()); return (fp+fn)/act.sum(),fp,fn
for n in order[:-1]:
    above=order[order.index(n)+1:]
    upB=np.zeros((H,W),np.uint8); upA=np.zeros((H,W),np.uint8)
    for u in above: upB|=B[u]; upA|=A[u]
    vis=B[n]&(1-upB)
    print(f'## {n!r} actual {A[n].sum():,}')
    rows=[]
    for s in ['disk','square']:
        for r in range(3,10):
            rows.append(('grow-visible',s,r)+score(B[n]&dil(vis,r,s),A[n]))
            rows.append(('grow-visible-any',s,r)+score(dil(vis,r,s)&(1-(1-B[n])*(1-upB)) ,A[n]))
            cut=np.zeros((H,W),np.uint8)
            for u in above: cut|=ero(A[u],r,s)
            rows.append(('cut-each-after',s,r)+score(B[n]&(1-cut),A[n]))
            rows.append(('cut-union-after',s,r)+score(B[n]&(1-ero(upA,r,s)),A[n]))
    rows.sort(key=lambda t:t[3])
    for t in rows[:5]: print(f'   {t[0]:18s} {t[1]:6s} r={t[2]}: {t[3]*100:.2f}% off  (extra {t[4]:,} / missing {t[5]:,})')
