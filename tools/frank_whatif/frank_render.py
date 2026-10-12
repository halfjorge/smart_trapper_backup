import json, sys, numpy as np, cv2
from PIL import Image
R, outp = sys.argv[1], sys.argv[2]
crop = [int(v) for v in sys.argv[3].split(',')] if len(sys.argv)>3 else None   # x0,y0,x1,y1
scale = int(sys.argv[4]) if len(sys.argv)>4 else 1
mode = sys.argv[5] if len(sys.argv)>5 else 'result'
j=json.load(open(f'{R}/job.json')); mc=json.load(open(f'{R}/mask_colors.json')); T=json.load(open(f'{R}/traps.json'))['traps']
W,H=j['widthPx'],j['heightPx']; x0,y0,x1,y1 = crop or (0,0,W,H)
rd=lambda p: np.array(Image.open(f'{R}/{p}'))[y0:y1,x0:x1,3]
img=np.empty((y1-y0,x1-x0,3),np.float32); img[:]=(242,238,215)   # cream paper
cols=[c['name'] for c in j['colors']]
key=j['keyLayerName']
for n in cols:                      # bottom -> top
    if mode=='client': m=rd(f'masks/{[f for f in j["files"] if f["name"]==n][0]["png"].split("/")[1]}')>=90
    else:
        m=rd(f'clean_masks/CLEAN__{n}.png')>0
        for t in T:
            if t['source']==n: m|=rd(t['png'])>0
    img[m]=[mc[n][c] for c in 'rgb']
ka=rd([f for f in j['files'] if f['kind']=='KEY'][0]['png']).astype(np.float32)/255*0.68
img=img*(1-ka[...,None])+np.array([30,15,35],np.float32)*ka[...,None]
im=np.clip(img,0,255).astype(np.uint8)
if scale!=1: im=cv2.resize(im,(im.shape[1]*scale,im.shape[0]*scale),interpolation=cv2.INTER_NEAREST if scale>1 else cv2.INTER_AREA)
Image.fromarray(im).save(outp)
