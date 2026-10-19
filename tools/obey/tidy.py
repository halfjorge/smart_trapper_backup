# 1) No pixel inked twice by the same colour: drop from TRAP__X any pixel already in CLEAN__X or an earlier
#    TRAP__X (separations identical - it only stops darker "dashes" in a multiply preview).
# 2) Close pin-hole gaps under the key: key pixels within the key trap width of a colour that no colour covers
#    go to that nearest colour's TRAP__X_under_Key.
import numpy as np, json, sys
from scipy import ndimage
D=sys.argv[1]; W,H=9600,12000
vis=json.load(open(f'{D}/vis_layers.json')); names=['Yellow','Cream','Red','Light Blue','Blue','Dark blue']
ld=lambda n: np.unpackbits(np.load(f'{D}/j_{n}.npy'))[:W*H].astype(bool)
sv=lambda n,m: np.save(f'{D}/j_{n}.npy',np.packbits(m))
for X in names:
    ls=[n for n in vis if n!='Key' and n.split('__')[1].split('_under_')[0]==X]
    seen=ld(f'CLEAN__{X}')
    for n in ls:
        if n.startswith('CLEAN__'): continue
        m=ld(n); dup=m&seen
        if dup.any(): sv(n,m&~dup); print(n,'doubled px removed',int(dup.sum()))
        seen|=m&~dup
L=np.load(f'{D}/labels.npy'); cov=np.zeros(H*W,bool)
for n in vis:
    if n!='Key': cov|=ld(n)
cov=cov.reshape(H,W); filled={X:np.zeros((H,W),bool) for X in names}
for y0 in range(0,H,1500):
    a,b=max(0,y0-20),min(H,y0+1520); sub=L[a:b]
    d,(iy,ix)=ndimage.distance_transform_edt(sub==7,return_indices=True); near=sub[iy,ix]
    g=(sub==7)&(d<=11)&(near>=1)&(near<=6)&~cov[a:b]; g[:y0-a]=False; g[min(H,y0+1500)-a:]=False
    for i,X in enumerate(names): filled[X][a:b]|=g&(near==i+1)
for X in names:
    if filled[X].any():
        n=f'TRAP__{X}_under_Key'; m=ld(n).reshape(H,W)|filled[X]; sv(n,m.ravel()); print(n,'gap px filled',int(filled[X].sum()))
