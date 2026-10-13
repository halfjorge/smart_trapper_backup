import numpy as np, json, cv2
mb=json.load(open('before/meta.json')); ma=json.load(open('after/meta.json'))
nb={n:i for i,n,_,_ in mb['layers']}; na={n:i for i,n,_,_ in ma['layers']}
L=lambda d,m,n: np.load(f"{d}/{m[n]}.npy",mmap_mode='r')[...,3]
order=['Yellow','Orange','Green','Red','Transparent Grey','Black']   # after's stack, bottom->top
A={n:L('after',na,n)>127 for n in order}
B={n:L('before',nb,n)>=112 for n in order}
for i,n in enumerate(order[:-1]):
    above=[m for m in order[i+1:]]
    opq=[m for m in above if m!='Transparent Grey']
    covA=np.zeros_like(A[n]); 
    for m in opq: covA|=A[m]
    gone=B[n]&~A[n]; new=A[n]&~B[n]
    print(f'== {n}: before {int(B[n].sum()):,}  after {int(A[n].sum()):,}')
    print(f'   removed {int(gone.sum()):,}: under an opaque colour above (after) {int((gone&covA).sum()):,} | not covered (would show) {int((gone&~covA).sum()):,}')
    for m in above:
        print(f'      removed & under after-{m}: {int((gone&A[m]).sum()):,}')
    # trap width: how far the after layer extends under the opaque colours above beyond the uncovered part
    vis=A[n]&~covA
    if vis.sum():
        d=cv2.distanceTransform((~vis).astype(np.uint8),cv2.DIST_L2,5)
        u=A[n]&covA
        if u.sum(): print(f'   under colours above: {int(u.sum()):,} px; distance from its visible part p50/p90/p99: {np.percentile(d[u],[50,90,99]).round(1)}')
    print(f'   added {int(new.sum()):,}: under opaque colour above {int((new&covA).sum()):,} | showing {int((new&~covA).sum()):,}')
