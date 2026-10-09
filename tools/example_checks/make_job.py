import numpy as np, json, os, sys
from PIL import Image, ImageDraw, ImageFilter
W,H=int(sys.argv[2]),int(sys.argv[3]); out=sys.argv[1]
os.makedirs(out+'/masks',exist_ok=True)
rng=np.random.default_rng(1)
names=['Yellow','Mustard','Green','Teal','Dark Blue','Dark Purple']
cols=[(240,255,110),(202,189,76),(115,153,75),(51,117,121),(47,71,87),(63,35,65)]
# draw label map: progressive knockout -> each pixel owned by top-most colour
owner=np.full((H,W),-1,np.int16)
for ci in range(len(names)):
    img=Image.new('L',(W,H),0); d=ImageDraw.Draw(img)
    for _ in range(25):
        x,y=rng.integers(0,W),rng.integers(0,H); r=rng.integers(W//40,W//6)
        if rng.random()<0.5: d.ellipse([x-r,y-r,x+r,y+r],fill=255)
        else: d.polygon([(x+rng.integers(-r,r),y+rng.integers(-r,r)) for _ in range(5)],fill=255)
    owner[np.array(img)>0]=ci
# small paper gaps: carve thin lines of paper
gap=Image.new('L',(W,H),0); d=ImageDraw.Draw(gap)
for _ in range(40): d.line([tuple(rng.integers(0,[W,H])),tuple(rng.integers(0,[W,H]))],fill=255,width=int(rng.integers(1,4)))
owner[np.array(gap)>0]=-1
def save(mask,rgb,path):
    a=Image.fromarray((mask*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    arr=np.zeros((H,W,4),np.uint8); arr[...,0],arr[...,1],arr[...,2]=rgb; arr[...,3]=np.array(a)
    Image.fromarray(arr,'RGBA').save(path,compress_level=1)
files=[]
key=Image.new('L',(W,H),0); d=ImageDraw.Draw(key)
for _ in range(60): d.line([tuple(rng.integers(0,[W,H])),tuple(rng.integers(0,[W,H]))],fill=255,width=int(rng.integers(3,20)))
save(np.array(key)>0,(20,20,40),out+'/masks/KEY_Dark Midnight Blue.png')
files.append(dict(kind='KEY',name='Dark Midnight Blue',blendMode='normal',opacity=100,fillOpacity=100,png='masks/KEY_Dark Midnight Blue.png'))
colors=[]
for i,(n,c) in enumerate(zip(names,cols)):
    p=f'masks/{i+1}_{n}.png'; save(owner==i,c,out+'/'+p)
    files.append(dict(kind='COLOR',name=n,blendMode='normal',opacity=100,fillOpacity=100,png=p))
    colors.append(dict(name=n,blendMode='normal',opacity=100,fillOpacity=100))
cleanup=sys.argv[4]=='1'
job=dict(docName='Synthetic.psd',widthPx=W,heightPx=H,resolution=300,preflightCleanup=cleanup,alphaThreshold=90,edgeBiasPx=1,keyTrapPullbackPx=1,keyLayerName='Dark Midnight Blue',paperLayerName='Background',colors=colors,files=files)
json.dump(job,open(out+'/job.json','w'),indent=2)
