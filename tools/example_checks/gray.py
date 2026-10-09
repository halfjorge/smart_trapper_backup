import numpy as np, json, cv2
mb=json.load(open('Ocean/before/meta.json'))['layers']; ma=json.load(open('Ocean/after/meta.json'))['layers']
nb=[x[1] for x in mb]; na=[x[1].replace(' *OVERLAY*','') for x in ma]
mode={x[1]:x[2] for x in mb}
order=['L BLUE','BLUE D','OCHRE','coral','blue 3','DATE BLK']
al=lambda v,names,n: np.asarray(np.load(f'Ocean/{v}/{names.index(n)}.npy',mmap_mode='r')[...,3]).astype(np.int16)
B={n:al('before',nb,n) for n in order}; A={n:al('after',na,n) for n in order}
H,W=B['DATE BLK'].shape
opaque=lambda n: 'NORMAL' in mode[n]
for n in order[:-1]:
    b=B[n]; a=A[n]; ink=b>0
    above=[u for u in order[order.index(n)+1:] if opaque(u)]
    up=np.zeros((H,W),bool)
    for u in above: up|=B[u]>127
    same=ink&(np.abs(a-b)<=2); zero=ink&(a==0); other=ink&~same&~zero
    added=(b==0)&(a>0)
    print(f'\n## {n} ({mode[n].split(".")[-1]}): ink px {ink.sum():,} (soft/gray {((b>0)&(b<255)).sum():,})')
    print(f'   unchanged {same.sum()/ink.sum()*100:.1f}% | cut to zero {zero.sum()/ink.sum()*100:.1f}% | value changed {other.sum()/ink.sum()*100:.1f}% | added where client had none {added.sum():,}')
    vis=ink&~up
    print(f'   where nothing opaque is above: unchanged {(same&vis).sum()/max(1,vis.sum())*100:.1f}%, cut {(zero&vis).sum()/max(1,vis.sum())*100:.2f}%, changed {(other&vis).sum()/max(1,vis.sum())*100:.2f}%')
    if other.sum():
        ch=other&vis
        if ch.sum(): print(f'     changed visible px: before->after mean {b[ch].mean():.0f}->{a[ch].mean():.0f}; became solid(255): {(a[ch]==255).sum():,}; before was <128: {(b[ch]<128).sum():,}')
    # under opaque layers: depth of kept gray inside the upper layer
    if up.sum():
        d=cv2.distanceTransform(up.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
        under=ink&up
        kept=under&(a>0)
        h=np.bincount(np.minimum(np.round(d[kept]).astype(int),20),minlength=21); hu=np.bincount(np.minimum(np.round(d[under]).astype(int),20),minlength=21)
        print('   under opaque layers: share kept by depth inside them:',' '.join(f'{k}:{h[k]/max(1,hu[k])*100:.0f}%' for k in range(1,11)))
        kk=kept&(d<=6)
        print(f'   in the trap band (<=6px): kept value equals client value {(np.abs(a-b)<=2)[kk].mean()*100:.0f}%, made solid {(a[kk]==255).mean()*100:.0f}% (client was solid there {(b[kk]==255).mean()*100:.0f}%)')
    # overlays above (non-opaque): kept?
    for u in order[order.index(n)+1:]:
        if not opaque(u):
            z=ink&(B[u]>127)&~up
            if z.sum(): print(f'   under overlay {u} (nothing opaque above): kept {(a[z]>0).mean()*100:.1f}%')
