import numpy as np,sys,gc
sys.path.insert(0,'/home/claude/psdsrc/src')
from psd_tools import PSDImage
A=PSDImage.open('auto.psb'); B=PSDImage.open('clean.psb')
la=[l for l in A.descendants() if l.kind=='pixel']; lb=[l for l in B.descendants() if l.kind=='pixel']
W,H=A.size
def full(l):
    im=l.topil(); 
    if im.mode!='RGBA': im=im.convert('RGBA')
    a=np.asarray(im)
    x0,y0,x1,y1=l.bbox
    out=np.zeros((H,W,4),np.uint8); out[y0:y1,x0:x1]=a; return out
for x,y in zip(la,lb):
    if x.name in('Layer 1','__ORIGINAL_FLATTENED__'): continue
    p=full(x); pa=p[...,3]>127
    vis=pa
    c=p[...,:3][vis]; u,cnt=np.unique(c[::50],axis=0,return_counts=True)
    top=[(tuple(int(v) for v in u[i]),int(cnt[i])) for i in np.argsort(-cnt)[:2]]
    q=full(y); qa=q[...,3]>127
    added=qa&~pa; removed=pa&~qa
    colch=pa&qa&(np.abs(p[...,:3].astype(np.int16)-q[...,:3]).sum(2)>6)
    del p
    n=(int(added.sum()),int(removed.sum()),int(colch.sum()))
    np.save(f"a_{x.name}.npy",np.packbits(pa))
    np.save(f"b_{x.name}.npy",np.packbits(qa))
    if sum(n):
        ys,xs=np.nonzero(added|removed|colch)
        print(f"{x.name:32s} +{n[0]:7d} -{n[1]:7d} col{n[2]:6d} box x{xs.min()}-{xs.max()} y{ys.min()}-{ys.max()} {top}",flush=True)
    else: print(f"{x.name:32s} same {top}",flush=True)
    del q; gc.collect()
