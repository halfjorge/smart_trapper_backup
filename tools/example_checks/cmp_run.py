import numpy as np, json, sys, cv2
from PIL import Image
J=sys.argv[1]; off=150
mb=json.load(open('BTS2/before/meta.json'))['layers']; ma=json.load(open('BTS2/after/meta.json'))['layers']
nb=[x[1] for x in mb]; na=[x[1] for x in ma]
job=json.load(open(J+'/job.json')); T=json.load(open(J+'/traps.json'))['traps']
san=lambda s: ''.join('_' if c in '/\\:*?"<>|' else c for c in s)
cols=[c['name'] for c in job['colors']]; key=job['keyLayerName']
H,W=7200,5400
Bm={n:np.asarray(np.load(f'BTS2/before/{nb.index(n)}.npy',mmap_mode='r')[...,3])>127 for n in cols+[key]}
A={n:np.ascontiguousarray(np.asarray(np.load(f'BTS2/after/{na.index(n)}.npy',mmap_mode='r')[off:off+H,off:off+W,3])>127) for n in cols}
R={}
for n in cols:
    R[n]=np.array(Image.open(f'{J}/clean_masks/CLEAN__{san(n)}.png'))[...,3]>0
for t in T: R[t['source']]|=np.array(Image.open(f"{J}/{t['png']}"))[...,3]>0
anyB=np.zeros((H,W),bool)
for n in cols+[key]: anyB|=Bm[n]
short=lambda n:n.split(' - ')[0]
print(f'{"colour":16s} {"client":>10s} {"yours":>10s} {"trapper":>10s} {"you-only":>10s} {"trapper-only":>12s}  you-only that is >8px from client edge')
tot=[0,0,0]
for n in cols:
    mo=A[n]&~R[n]; to=R[n]&~A[n]
    d=cv2.distanceTransform((~Bm[n]).astype(np.uint8),cv2.DIST_L2,5)
    deep=(mo&(d>8)).sum()
    tot[0]+=mo.sum(); tot[1]+=to.sum(); tot[2]+=deep
    print(f'{short(n):16s} {Bm[n].sum():>10,} {A[n].sum():>10,} {R[n].sum():>10,} {mo.sum():>10,} {to.sum():>12,}  {deep:,}')
print(f'TOTAL you-only {tot[0]:,} (of which flat-fill style >8px: {tot[2]:,}); trapper-only {tot[1]:,}')
# trapper visible-change check: composite with trapper result in client order
def comp(masks, order):
    out=np.zeros((H,W),np.int16)-1
    for i,n in enumerate(order): out[masks[n]]=i
    return out
ordc=cols+[key]
Rk=dict(R); Rk[key]=Bm[key]; Bk=dict(Bm)
cb=comp(Bk,ordc); cr=comp(Rk,ordc)
print('visible pixels that changed colour (trapper vs client):',int((cb!=cr).sum()))
