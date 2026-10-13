import numpy as np, json, sys
from PIL import Image, ImageDraw
R='Bourbon_med_mpk_ov'; out=sys.argv[1]; spots=[tuple(map(int,s.split(','))) for s in sys.argv[2:]]
ma=json.load(open('Bourbon/after/meta.json')); mb=json.load(open('Bourbon/before/meta.json'))
na={n:i for i,n,_,_ in ma['layers']}; nb={n:i for i,n,_,_ in mb['layers']}
j=json.load(open(f'{R}/job.json')); T=json.load(open(f'{R}/traps.json'))['traps']
names=['Yellow','Orange','Red','Green','Transparent Grey']; eng=[c['name'] for c in j['colors']]
cols={n:np.median(np.load(f"Bourbon/after/{na[n]}.npy",mmap_mode='r')[...,:3][np.load(f"Bourbon/after/{na[n]}.npy",mmap_mode='r')[...,3]>127][:200000],axis=0) for n in names}
r=60; sc=5; rows=[]
for cx,cy in spots:
    sl=(slice(cy-r,cy+r),slice(cx-r,cx+r))
    def comp(get, key_al, keyon=True):
        o=np.full((2*r,2*r,3),255,np.float32)
        for n in names:
            al=get(n)[...,None]; c=cols[n]
            o=o*(1-al)+((o*c/255) if n=='Transparent Grey' else c)*al
        if keyon: o=o*(1-key_al[...,None])
        return np.clip(o,0,255).astype(np.uint8)
    cl=lambda n: np.load(f"Bourbon/before/{nb[n]}.npy",mmap_mode='r')[sl][...,3]/255.
    hd=lambda n: (np.load(f"Bourbon/after/{na[n]}.npy",mmap_mode='r')[sl][...,3]>127).astype(float)
    def tr(n):
        e=eng[names.index(n)]; m=np.array(Image.open(f'{R}/clean_masks/CLEAN__{e}.png'))[sl][...,3]>0
        for t in T:
            if t['source']==e: m|=np.array(Image.open(f"{R}/{t['png']}"))[sl][...,3]>0
        return m.astype(float)
    kc=cl('Black'); kh=hd('Black')
    p=[comp(cl,kc),comp(hd,kh),comp(tr,kc),comp(hd,kh,False),comp(tr,kc,False)]
    row=np.concatenate([np.pad(np.kron(x,np.ones((sc,sc,1),np.uint8)),((0,0),(0,6),(0,0)),constant_values=255) for x in p],1)
    rows.append(np.pad(row,((18,4),(0,0),(0,0)),constant_values=255))
im=Image.fromarray(np.concatenate(rows,0)); d=ImageDraw.Draw(im); w=2*r*sc+6
for k,s in enumerate(['client before','your hand after','trapper today','hand - key off','trapper today - key off']): d.text((k*w+4,4),s,fill=(0,0,0))
im.save(out)
