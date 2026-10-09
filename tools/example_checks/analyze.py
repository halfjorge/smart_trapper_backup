import numpy as np, json, sys, cv2
job=sys.argv[1]; offx=int(sys.argv[2]) if len(sys.argv)>2 else 0; offy=offx
def load(d):
    m=json.load(open(d+'/meta.json')); return m,[np.load(f'{d}/{i}.npy',mmap_mode='r') for i in range(len(m['layers']))]
mb,lb=load(f'{job}/before'); ma,la=load(f'{job}/after')
nb=[x[1] for x in mb['layers']]; na=[x[1] for x in ma['layers']]
H,W=lb[0].shape[:2]
def col(l):
    a=l[...,3]>200
    if a.sum()==0: return None
    px=l[...,:3][a]; v,c=np.unique(px.reshape(-1,3),axis=0,return_counts=True); return tuple(int(t) for t in v[c.argmax()])
def amask(l, crop=True):
    m=l[...,3]>127
    if crop and l.shape[:2]!=(H,W): m=m[offy:offy+H, offx:offx+W]
    return np.ascontiguousarray(m)
print('paper/bottom:',nb[0],'->',na[0])
B={n:amask(lb[i]) for i,n in enumerate(nb) if i>0}
A={n:amask(la[na.index(n)]) for n in nb[1:] if n in na}
order_b=nb[1:]; order_a=[n for n in na[1:]]
print('stack before (bottom->top):',order_b); print('stack after  (bottom->top):',order_a)
for n in order_b: print(f'  colour {n!r}: before {col(lb[nb.index(n)])}  after {col(la[na.index(n)]) if n in na else None}')
def dist_from(mask):  # distance (px) of every pixel to nearest True pixel of mask
    return cv2.distanceTransform((~mask).astype(np.uint8), cv2.DIST_L2, 5)
res={}
for n in order_a:
    if n not in B: continue
    above=[m for m in order_a[order_a.index(n)+1:]]
    upper=np.zeros((H,W),bool)
    for m in above: upper|=A[m]   # what covers it in the final print
    upper_b=np.zeros((H,W),bool)
    for m in order_b[order_b.index(n)+1:]: upper_b|=B[m]
    vis_b = B[n] & ~upper_b      # what showed in the client file
    a=A[n]
    extra = a & ~vis_b           # ink kept/added that doesn't show in client art
    missing = vis_b & ~a
    outside = a & ~B[n]          # ink added where client had none of this colour
    d=dist_from(vis_b)
    de=d[extra]
    hist=np.bincount(np.minimum(np.ceil(de).astype(int),40), minlength=41)
    tot=extra.sum()
    print(f'\n### {n!r}: before {B[n].sum():,}px  visible-in-client {vis_b.sum():,}  after {a.sum():,}')
    print(f'  kept/added under other colours: {tot:,}px; of that added outside client art: {outside.sum():,}px; visible-but-removed: {missing.sum():,}px')
    if tot:
        cum=np.cumsum(hist)/tot
        print('  distance from visible edge (px): ', ' '.join(f'{k}:{hist[k]/tot*100:.1f}%' for k in range(0,12)), f'>12:{hist[12:].sum()/tot*100:.1f}%')
        for p in (0.5,0.9,0.99): print(f'   {int(p*100)}% of the overlap is within {int(np.searchsorted(cum,p))}px')
        # under what?
        for m in above:
            u=(extra & A[m]).sum()
            if u: print(f'   under {m!r}: {u:,}px')
        u=(extra & ~upper).sum()
        if u: print(f'   on open paper (not covered by anything): {u:,}px')
