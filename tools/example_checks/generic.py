# Generic before/after trap analysis. Layers matched by name; stack order taken from the AFTER file.
import numpy as np, json, cv2, sys
job=sys.argv[1]; strip=sys.argv[2:]  # suffixes to strip from after-names
def load(d):
    m=json.load(open(f'{job}/{d}/meta.json')); return [x[1] for x in m['layers']],[x[2] for x in m['layers']]
nb,mb=load('before'); na,ma=load('after')
clean=lambda n: (lambda s: [s:=s.replace(x,'') for x in strip][-1] if strip else s)(n).strip()
na_c=[clean(n) for n in na]
def alpha(v,i): return np.asarray(np.load(f'{job}/{v}/{i}.npy',mmap_mode='r')[...,3])
order=na_c[1:]; key=order[-1]
ov={n: ('NORMAL' not in mb[nb.index(n)]) for n in order}
Bα={n:alpha('before',nb.index(n)) for n in order}; B={n:Bα[n]>127 for n in order}
A={n:alpha('after',na_c.index(n))>127 for n in order}
H,W=B[key].shape
print('stack (after order, bottom->top):',' | '.join(f'{n}{" [OVERLAY "+mb[nb.index(n)].split(".")[-1]+"]" if ov[n] else ""}' for n in order))
print('client order:',' | '.join(nb[1:]))
opaque_above=lambda n: [u for u in order[order.index(n)+1:] if not ov[u]]
for n in order[:-1]:
    upO=np.zeros((H,W),bool)
    for u in opaque_above(n): upO|=B[u]
    vis=B[n]&~upO                       # what would show if only opaque layers hide it
    kept=A[n]&~vis; removed=vis&~A[n]
    d=cv2.distanceTransform((~vis).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    h=np.bincount(np.minimum(np.round(d[kept]).astype(int),30),minlength=31); t=max(1,kept.sum())
    print(f'\n## {n}{" (OVERLAY)" if ov[n] else ""}: client {B[n].sum():,} -> yours {A[n].sum():,}; overlap under opaque layers {kept.sum():,}; visible-but-removed {removed.sum():,}')
    print('   overlap depth (px):',' '.join(f'{k}:{h[k]/t*100:.0f}%' for k in range(1,11)),f'>10:{h[11:].sum()/t*100:.1f}%')
    for u in order[order.index(n)+1:]:
        o=B[n]&B[u]
        if o.sum()>1000: print(f'   overlap with {u}{" (overlay)" if ov[u] else ""}: client {o.sum():,} -> kept {(o&A[n]).sum()/o.sum()*100:.0f}%')
    s=(Bα[n]>0)&(Bα[n]<255)&~upO
    if s.sum():
        bins=[0,32,64,96,128,160,192,224,256]; b=np.digitize(Bα[n][s],bins)-1
        k=np.bincount(b,weights=A[n][s],minlength=8)[:8]; c=np.bincount(b,minlength=8)[:8]
        print('   soft edge pixels -> solid, by client opacity:',' '.join(f'{bins[i]*100//255}%:{k[i]/max(1,c[i])*100:.0f}' for i in range(8)))
kα=Bα[key]; s=(kα>0)&(kα<255)
if s.sum():
    bins=[0,32,64,96,128,160,192,224,256]; b=np.digitize(kα[s],bins)-1
    k=np.bincount(b,weights=A[key][s],minlength=8)[:8]; c=np.bincount(b,minlength=8)[:8]
    print(f'\n## key {key}: client {B[key].sum():,} -> yours {A[key].sum():,}; soft -> solid by opacity:',' '.join(f'{bins[i]*100//255}%:{k[i]/max(1,c[i])*100:.0f}' for i in range(8)))
