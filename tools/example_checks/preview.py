import numpy as np, json, sys
from PIL import Image, ImageDraw
def load(d):
    m=json.load(open(d+'/meta.json')); return m,[np.load(f'{d}/{i}.npy') for i in range(len(m['layers']))]
def composite(layers, scale, skip=()):
    H,W=layers[0].shape[:2]
    out=np.full(layers[0][::scale,::scale,:3].shape,255,np.float32)
    for i,l in enumerate(layers):
        if i in skip: continue
        s=l[::scale,::scale].astype(np.float32); a=s[...,3:4]/255
        out=out*(1-a)+s[...,:3]*a
    return Image.fromarray(out.clip(0,255).astype(np.uint8))
job=sys.argv[1]; scale=int(sys.argv[2])
mb,lb=load(f'{job}/before'); ma,la=load(f'{job}/after')
composite(lb,scale).save(f'{job}_before_comp.png'); composite(la,scale).save(f'{job}_after_comp.png')
# per-layer masks side by side
rows=[]
for i in range(1,len(lb)):
    nb=mb['layers'][i][1]
    j=[k for k,x in enumerate(ma['layers']) if x[1]==nb]
    a=Image.fromarray(255-lb[i][::scale,::scale,3])
    b=Image.fromarray(255-la[j[0]][::scale,::scale,3]) if j else Image.new('L',a.size,128)
    row=Image.new('L',(a.width+b.width+10,max(a.height,b.height)+16),200); row.paste(a,(0,16)); row.paste(b,(a.width+10,16))
    ImageDraw.Draw(row).text((2,2),f'{nb}: before | after',fill=0); rows.append(row)
W=max(r.width for r in rows); Ht=sum(r.height for r in rows)
sheet=Image.new('L',(W,Ht),200); y=0
for r in rows: sheet.paste(r,(0,y)); y+=r.height
sheet.save(f'{job}_layers.png'); print(sheet.size)
