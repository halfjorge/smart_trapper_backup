import numpy as np, json, os, sys, shutil, subprocess, cv2
from PIL import Image
ENGINE='/home/claude/vend/build_new/target/release/smart_trapper_b1'
off=150; H,W=7200,5400
mb=json.load(open('BTS2/before/meta.json'))['layers']; ma=json.load(open('BTS2/after/meta.json'))['layers']
nb=[x[1] for x in mb]; na=[x[1] for x in ma]
san=lambda s: ''.join('_' if c in '/\\:*?"<>|' else c for c in s)
cols=nb[1:-1]; key=nb[-1]
def build(out):
    if os.path.exists(out+'/masks'): return
    os.makedirs(out+'/masks',exist_ok=True)
    for i,n in enumerate(nb[1:]):
        l=np.load(f'BTS2/before/{i+1}.npy'); Image.fromarray(l).save(f'{out}/masks/{i}.png',compress_level=1)
build('btsjob')
def run(tag,pull,trap=5,bias=1):
    out=f'btsrun_{tag}'; shutil.rmtree(out,ignore_errors=True); shutil.copytree('btsjob',out)
    files=[dict(kind='KEY',name=key,blendMode='normal',opacity=100,fillOpacity=100,png=f'masks/{len(cols)}.png')]
    files+=[dict(kind='COLOR',name=n,blendMode='normal',opacity=100,fillOpacity=100,png=f'masks/{i}.png') for i,n in enumerate(cols)]
    job=dict(docName='BTS',widthPx=W,heightPx=H,resolution=300,preflightCleanup=True,alphaThreshold=90,edgeBiasPx=bias,keyTrapPullbackPx=pull,keyLayerName=key,paperLayerName='White',colors=[dict(name=n,blendMode='normal',opacity=100,fillOpacity=100) for n in cols],files=files)
    json.dump(job,open(out+'/job.json','w'))
    subprocess.run([ENGINE,out,str(trap)],check=True,capture_output=True)
    T=json.load(open(out+'/traps.json'))['traps']
    R={n:np.array(Image.open(f'{out}/clean_masks/CLEAN__{san(n)}.png'))[...,3]>0 for n in cols}
    for t in T: R[t['source']]|=np.array(Image.open(f"{out}/{t['png']}"))[...,3]>0
    return R
K=np.asarray(np.load(f'BTS2/before/{nb.index(key)}.npy',mmap_mode='r')[...,3])>127
A={n:np.ascontiguousarray(np.asarray(np.load(f'BTS2/after/{na.index(n)}.npy',mmap_mode='r')[off:off+H,off:off+W,3])>127) for n in cols}
Bc={n:np.asarray(np.load(f'BTS2/before/{nb.index(n)}.npy',mmap_mode='r')[...,3])>127 for n in cols}
for tag,pull in (('p1',1),('p0',0)):
    R=run(tag,pull)
    print(f'--- key trap pullback {pull}')
    for n in cols:
        mine=(A[n]&K&~Bc[n]); tr=(R[n]&K&~Bc[n])
        d=cv2.distanceTransform((~Bc[n]).astype(np.uint8),cv2.DIST_L2,5); near=d<=8
        print(f'   {n.split(" - ")[0]:16s} under key (within 8px): yours {(mine&near).sum():>9,} trapper {(tr&near).sum():>9,}  missing {(mine&near&~tr).sum():>8,}')
