import numpy as np, json, cv2
def L(v,i): return np.ascontiguousarray(np.load(f'Methane/{v}/{i}.npy',mmap_mode='r')[...,3]>127)
bn={'green':1,'skyu':2,'hatch':3,'shack':4,'org':5,'key':6}
an={'org':1,'green':2,'hatch':3,'skyu':4,'shack':5,'key':6}
B={k:L('before',i) for k,i in bn.items()}; A={k:L('after',i) for k,i in an.items()}
cl=['green','skyu','hatch','shack','org','key']; mine=['org','green','hatch','skyu','shack','key']
print('client colour-on-colour overlaps (excluding key):')
for i,a in enumerate(cl[:-1]):
    for b in cl[i+1:-1]:
        o=(B[a]&B[b]).sum()
        if o: print(f'   {a} & {b}: {o:,}px')
H,W=B['key'].shape
dist=lambda m: cv2.distanceTransform((~m).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
for n in mine[:-1]:
    upA=np.zeros((H,W),bool); upB=np.zeros((H,W),bool)
    for u in mine[mine.index(n)+1:]: upA|=A[u]
    for u in cl[cl.index(n)+1:]: upB|=B[u]
    vis=B[n]&~upB
    extra=A[n]&~vis; removed=vis&~A[n]; outside=A[n]&~B[n]
    d=dist(vis); h=np.bincount(np.minimum(np.round(d[extra]).astype(int),30),minlength=31)
    print(f'\n## {n}: client {B[n].sum():,} visible {vis.sum():,} -> yours {A[n].sum():,}; overlap kept {extra.sum():,} (outside client art {outside.sum():,}); visible removed {removed.sum():,}')
    print('   overlap by distance from visible edge:',' '.join(f'{k}:{h[k]/max(1,extra.sum())*100:.0f}%' for k in range(1,12)),f'>11:{h[12:].sum()/max(1,extra.sum())*100:.1f}%')
    for u in mine[mine.index(n)+1:]:
        x=(extra&A[u]).sum()
        if x: print(f'     under {u}: {x:,}')
    x=(extra&~upA).sum()
    if x: print(f'     on visible paper/not covered: {x:,}')

print('\n--- ink added on what was paper in the client file, by distance to the key ---')
K=B['key']; dK=cv2.distanceTransform((~K).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
anyB=np.zeros((H,W),bool)
for n in cl[:-1]: anyB|=B[n]
paperB=~anyB&~K
for n in mine[:-1]:
    add=A[n]&paperB
    upA=np.zeros((H,W),bool)
    for u in mine[mine.index(n)+1:]: upA|=A[u]
    vis_add=add&~upA
    d=dK[vis_add]
    print(f'{n}: {vis_add.sum():,}px now visible ink on former paper; within 2px of key {(d<=2).sum():,}, 3-6px {((d>2)&(d<=6)).sum():,}, further {(d>6).sum():,}')
