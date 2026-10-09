import numpy as np, json, os, sys, shutil, subprocess, cv2
from PIL import Image
ENGINE='/home/claude/vend/build_new/target/release/smart_trapper_b1'
B='Byrne/before'; m=json.load(open(f'{B}/meta.json')); names=[x[1] for x in m['layers']]; H,W=m['H'],m['W']
cols=names[1:-1]; key=names[-1]
base='byrnejob'
if not os.path.exists(base+'/masks/0.png'):
    os.makedirs(base+'/masks',exist_ok=True)
    for i,n in enumerate(names[1:]): Image.fromarray(np.load(f'{B}/{i+1}.npy')).save(f'{base}/masks/{i}.png',compress_level=1)
def run(tag,cpull,trap=5):
    out=f'byrnerun_{tag}'; shutil.rmtree(out,ignore_errors=True); shutil.copytree(base,out)
    files=[dict(kind='KEY',name=key,blendMode='normal',opacity=100,fillOpacity=100,png=f'masks/{len(cols)}.png')]
    files+=[dict(kind='COLOR',name=n,blendMode='normal',opacity=100,fillOpacity=100,png=f'masks/{i}.png') for i,n in enumerate(cols)]
    job=dict(docName='Byrne',widthPx=W,heightPx=H,resolution=300,preflightCleanup=True,alphaThreshold=90,edgeBiasPx=1,keyTrapPullbackPx=1,keyLayerName=key,paperLayerName=names[0],colors=[dict(name=n,blendMode='normal',opacity=100,fillOpacity=100) for n in cols],files=files)
    if cpull is not None: job['colorTrapPullbackPx']=cpull
    json.dump(job,open(out+'/job.json','w'))
    r=subprocess.run([ENGINE,out,str(trap)],check=True,capture_output=True,text=True); print(tag, r.stdout.strip().splitlines()[-1])
    return out
