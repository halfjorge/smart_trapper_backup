import numpy as np, json, sys
from PIL import Image, ImageDraw
x0,y0,w,h,sc=map(int,sys.argv[1:6]); out=sys.argv[6]
tiles=[]
for side in ['before','after']:
    m=json.load(open(f'{side}/meta.json'))
    row=[]
    # composite
    o=None
    for i,name,mode,_ in m['layers']:
        a=np.load(f'{side}/{i}.npy',mmap_mode='r')[y0:y0+h,x0:x0+w].astype(np.float32)
        if o is None: o=a[...,:3].copy(); continue
        A=a[...,3:4]/255; c=a[...,:3]; o=o*(1-A)+(o*c/255 if 'MULTIPLY' in mode else c)*A
    row.append(('composite',np.clip(o,0,255).astype(np.uint8)))
    names={n:i for i,n,_,_ in m['layers']}
    for n in ['Yellow','Orange','Red','Green','Transparent Grey','Black']:
        a=np.load(f'{side}/{names[n]}.npy',mmap_mode='r')[y0:y0+h,x0:x0+w]
        al=a[...,3:4].astype(np.float32)/255; img=255*(1-al)+a[...,:3]*al
        row.append((n,img.astype(np.uint8)))
    tiles.append((side,row))
cw=w*sc; ch=h*sc
im=Image.new('RGB',(7*(cw+6),2*(ch+20)),'white'); d=ImageDraw.Draw(im)
for r,(side,row) in enumerate(tiles):
    for c,(n,img) in enumerate(row):
        im.paste(Image.fromarray(img).resize((cw,ch),Image.NEAREST),(c*(cw+6),r*(ch+20)+16)); d.text((c*(cw+6)+2,r*(ch+20)+2),f'{side} {n}',fill=(0,0,0))
im.save(out)
