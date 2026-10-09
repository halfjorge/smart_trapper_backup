import numpy as np, json, cv2, sys
exec(open('generic.py').read().split("opaque_above=lambda")[0].replace("job=sys.argv[1]; strip=sys.argv[2:]","job=sys.argv[1]; strip=sys.argv[2:]"))
opaque_above=lambda n: [u for u in order[order.index(n)+1:] if not ov[u]]
for g in [n for n in order if ov[n]]:
    print(f'\n### overlay {g!r}')
    for n in order[:order.index(g)]:
        upO=np.zeros((H,W),bool)
        for u in opaque_above(n): upO|=B[u]
        zone=B[n]&B[g]&~upO
        if zone.sum()<500: continue
        print(f'   {n} under the overlay (nothing opaque above): {zone.sum():,}px -> kept {(zone&A[n]).sum()/zone.sum()*100:.1f}%')
    # overlay vs opaque layers above it
    for u in order[order.index(g)+1:]:
        o=B[g]&B[u]
        if o.sum()<500: continue
        d=cv2.distanceTransform(B[u].astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
        kept=o&A[g]; deep=kept&(d>6)
        print(f'   overlay under opaque {u}: {o.sum():,}px -> kept {kept.sum()/o.sum()*100:.0f}%; kept deeper than 6px inside {u}: {deep.sum():,}px')
