# Simulate the panel: Manual Progressive Knockout -> engine (real binary) -> compare with manual "after".
import re, numpy as np, json, sys, os, subprocess, shutil, cv2
from PIL import Image
job=sys.argv[1]; off=int(sys.argv[2]); trap=sys.argv[3]; extra=json.loads(sys.argv[4]) if len(sys.argv)>4 else {}
ENGINE='/home/claude/vend/build_new/target/release/smart_trapper_b1'
def load(d):
    m=json.load(open(d+'/meta.json')); return [x[1] for x in m['layers']],[np.load(f'{d}/{i}.npy',mmap_mode='r') for i in range(len(m['layers']))]
nb,lb=load(f'{job}/before'); na,la=load(f'{job}/after'); na=[x.replace(' *OVERLAY*','') for x in na]
H,W=lb[0].shape[:2]
def m(l):
    x=l[...,3]>127
    if x.shape!=(H,W): x=x[off:off+H,off:off+W]
    return np.ascontiguousarray(x).astype(np.uint8)
order=[n for n in nb[1:]]          # client stack bottom->top (what the panel sees)
key=order[-1]; colors=order[:-1]
B={n:m(lb[nb.index(n)]) for n in order}
# Manual Progressive Knockout: top-down, cut every layer above out of each lower layer
GAP=int(extra.pop('_gap',0))
if GAP:
    # Fill thin paper gaps between colour and line work: paper pixels within GAP px of the key
    # and within GAP px of some colour get the nearest colour.
    kd=cv2.distanceTransform((1-B[key]).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    anyc=np.zeros((H,W),np.uint8)
    for n in colors: anyc|=B[n]
    paper=(anyc==0)&(B[key]==0)
    ds=np.stack([cv2.distanceTransform((1-B[n]).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE) for n in colors])
    near=ds.argmin(0); dmin=ds.min(0)
    fill=paper&(kd<=GAP)&(dmin<=GAP)
    for i,n in enumerate(colors): B[n]=B[n]|(fill&(near==i)).astype(np.uint8)
    print('gap pixels filled:',int(fill.sum()))
K={}; above=np.zeros((H,W),np.uint8)
for n in reversed(order):
    K[n]=B[n]&(1-above); above|=B[n]
out=f'sim_{job}'; shutil.rmtree(out,ignore_errors=True); os.makedirs(out+'/masks')
def save(mask,path,rgb=(255,255,255)):
    a=np.zeros((H,W,4),np.uint8); a[...,0],a[...,1],a[...,2]=rgb; a[...,3]=mask*255; Image.fromarray(a).save(path,compress_level=1)
files=[dict(kind='KEY',name=key,blendMode='normal',opacity=100,fillOpacity=100,png='masks/KEY.png')]; save(B[key],out+'/masks/KEY.png')
cols=[]
for i,n in enumerate(colors):
    p=f'masks/{i+1}.png'; save(K[n],out+'/'+p)
    files.append(dict(kind='COLOR',name=n,blendMode='normal',opacity=100,fillOpacity=100,png=p)); cols.append(dict(name=n,blendMode='normal',opacity=100,fillOpacity=100))
jobj=dict(docName=job,widthPx=W,heightPx=H,resolution=300,preflightCleanup=True,alphaThreshold=90,edgeBiasPx=1,keyTrapPullbackPx=1,keyLayerName=key,paperLayerName='paper',colors=cols,files=files)
jobj.update(extra)
json.dump(jobj,open(out+'/job.json','w'))
r=subprocess.run([ENGINE,out,trap],capture_output=True,text=True); print(r.stdout.splitlines()[-1], r.stderr[-300:])
T=json.load(open(out+'/traps.json'))['traps']
final={n:np.array(Image.open(f'{out}/clean_masks/CLEAN__{re.sub(r'[/\\:*?"<>|]','_',n)}.png'))[...,3]>0 for n in colors}
for t in T:
    final[t['source']]|=np.array(Image.open(out+'/'+t['png']))[...,3]>0
A={n:m(la[na.index(n)]).astype(bool) for n in colors}
Kk=B[key].astype(bool)
anyB=np.zeros((H,W),bool)
for n in colors: anyB|=B[n].astype(bool)
print(f'\n{"colour":22s} {"manual px":>11s} {"trapper px":>11s} {"manual-only":>12s} {"trapper-only":>12s}   where manual-only sits')
tot_mo=tot_to=0
for n in colors:
    mo=A[n]&~final[n]; to=final[n]&~A[n]
    under_key=(mo&Kk).sum(); paper=(mo&~Kk&~anyB).sum(); under_col=mo.sum()-under_key-paper
    tot_mo+=mo.sum(); tot_to+=to.sum()
    print(f'{n:22s} {A[n].sum():>11,} {final[n].sum():>11,} {mo.sum():>12,} {to.sum():>12,}   under key {under_key:,} | paper gap {paper:,} | under colours {under_col:,}')
print(f'TOTAL manual-only {tot_mo:,}  trapper-only {tot_to:,}')
np.save(f'{out}_final.npy', np.stack([final[n] for n in colors]))
