# Key-halo test: run the real engine on a before/after example with closeKeyHaloPx = 0..3
# and compare paper gaps around the key with the manual "after".
import re, numpy as np, json, sys, os, subprocess, shutil, cv2
from PIL import Image
job=sys.argv[1]; off=int(sys.argv[2]); trap=sys.argv[3]; halos=[int(x) for x in sys.argv[4].split(',')]
ENGINE='/home/claude/vend/build_new/target/release/smart_trapper_b1'
def load(d):
    m=json.load(open(d+'/meta.json')); return [x[1] for x in m['layers']],[np.load(f'{d}/{i}.npy',mmap_mode='r') for i in range(len(m['layers']))]
nb,lb=load(f'{job}/before'); na,la=load(f'{job}/after')
H,W=lb[0].shape[:2]
order=nb[1:]; key=order[-1]; colors=order[:-1]
alpha={n:np.ascontiguousarray(lb[nb.index(n)][...,3]) for n in order}
rgb={n:np.ascontiguousarray(lb[nb.index(n)][...,:3]) for n in order}
TH=90
# Manual Progressive Knockout (top-down, selection = alpha >= threshold) - colours only, key kept
above=alpha[key]>=TH; ko={}
for n in reversed(colors):
    a=alpha[n].copy(); a[above]=0; ko[n]=a; above=above|(alpha[n]>=TH)
def aft(n):
    x=la[na.index(n)][...,3]; return np.ascontiguousarray(x[off:off+H,off:off+W])>127
K=alpha[key]>=TH
anyc=np.zeros((H,W),bool)
for n in colors: anyc|=alpha[n]>=TH
# reference halo = paper in client (no colour, no key) that the manual after filled with a colour
manual_any=np.zeros((H,W),bool)
for n in colors: manual_any|=aft(n)
ref_halo=~anyc&~K&manual_any
print(f'client paper filled by hand (outside key): {ref_halo.sum():,} px')
for hp in halos:
    out=f'{job}_halo{hp}'; shutil.rmtree(out,ignore_errors=True); os.makedirs(out+'/masks')
    def save(a,path,c):
        x=np.zeros((H,W,4),np.uint8); x[...,:3]=c; x[...,3]=a; Image.fromarray(x).save(path,compress_level=1)
    files=[dict(kind='KEY',name=key,blendMode='normal',opacity=100,fillOpacity=100,png='masks/KEY.png')]
    save(alpha[key],out+'/masks/KEY.png',rgb[key])
    cols=[]
    for i,n in enumerate(colors):
        p=f'masks/{i+1}.png'; save(ko[n],out+'/'+p,rgb[n])
        files.append(dict(kind='COLOR',name=n,blendMode='normal',opacity=100,fillOpacity=100,png=p)); cols.append(dict(name=n,blendMode='normal',opacity=100,fillOpacity=100))
    jobj=dict(docName=job,widthPx=W,heightPx=H,resolution=300,preflightCleanup=True,alphaThreshold=TH,edgeBiasPx=1,
              keyTrapPullbackPx=1,colorTrapPullbackPx=0,trapShape='round',closeKeyHaloPx=hp,
              keyLayerName=key,paperLayerName='paper',colors=cols,files=files)
    json.dump(jobj,open(out+'/job.json','w'))
    r=subprocess.run([ENGINE,out,trap],capture_output=True,text=True)
    log=[l for l in r.stdout.splitlines() if 'halo' in l]
    if r.returncode: print(r.stdout[-500:],r.stderr[-500:]); sys.exit(1)
    T=json.load(open(out+'/traps.json'))['traps']
    clean={n:np.array(Image.open(f'{out}/clean_masks/CLEAN__{re.sub(r"[/\\:*?\"<>|]","_",n)}.png'))[...,3]>0 for n in colors}
    final={n:clean[n].copy() for n in colors}
    for t in T:
        if t['source'] in final: final[t['source']]|=np.array(Image.open(out+'/'+t['png']))[...,3]>0
    fin_any=np.zeros((H,W),bool)
    for n in colors: fin_any|=final[n]
    # paper still showing next to the key (within 3 px), outside the key
    near_key=cv2.dilate(K.astype(np.uint8),np.ones((7,7),np.uint8)).astype(bool)&~K
    gap_left=near_key&~fin_any&manual_any       # paper where the manual file has colour
    filled=ref_halo&fin_any
    # visible change vs client outside the key (who shows on top), excluding the halo itself
    def top(stack):
        t=np.zeros((H,W),np.int16)
        for i,n in enumerate(colors): t[stack[n]]=i+1
        return t
    vis_before=top({n:alpha[n]>=TH for n in colors}); vis_after=top(clean)
    changed=(vis_before!=vis_after)&~K
    halo_added=changed&(vis_before==0)
    other=changed&~halo_added
    # are halo fills only in narrow gaps? width of each added blob's distance to key
    dk=cv2.distanceTransform((~K).astype(np.uint8),cv2.DIST_L2,5)
    far=(halo_added&(dk>hp+1.5)).sum()
    print(f'halo {hp}px: engine says {log[0].split(":",1)[-1].strip() if log else "off"} | hand-filled paper now filled {filled.sum():,}/{ref_halo.sum():,} '
          f'({filled.sum()/max(ref_halo.sum(),1)*100:.1f}%) | paper left next to key where hand file has colour {gap_left.sum():,} | '
          f'visible change outside key: halo fill {halo_added.sum():,}, other {other.sum():,}, fill farther than {hp+1.5}px from key {far}')
    np.save(f'{out}_added.npy',halo_added)
