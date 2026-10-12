import json, sys, numpy as np, cv2
from PIL import Image
R, outp = sys.argv[1], sys.argv[2]; x0,y0,x1,y1=[int(v) for v in sys.argv[3].split(',')]; sc=int(sys.argv[4])
j=json.load(open(f'{R}/job.json')); T=json.load(open(f'{R}/traps.json'))['traps']; key=j['keyLayerName']
rd=lambda p,th=1: np.array(Image.open(f'{R}/{p}'))[y0:y1,x0:x1,3]
keyf=[f for f in j['files'] if f['kind']=='KEY'][0]['png']
Ka=rd(keyf); K=Ka>=j['alphaThreshold']
vio_client=rd('masks/4_violet.png')>=90; vio_clean=rd('clean_masks/CLEAN__violet.png')>0
tv=np.zeros_like(K)
for t in T:
    if t['source']=='violet' and t['target']==key: tv|=rd(t['png'])>0
img=np.empty(K.shape+(3,),np.uint8); img[:]=(242,238,215)          # paper
img[K]=(95,80,98)                                                  # key (as at 68%)
img[vio_clean & ~K]=(132,22,120)                                    # violet showing
img[vio_clean & K]=(80,20,75)                                       # violet under key (clean, incl. edge-bias growth)
img[tv]=(0,220,255)                                                 # violet TRAP under key
img=cv2.resize(img,(img.shape[1]*sc,img.shape[0]*sc),interpolation=cv2.INTER_NEAREST)
for k in range(0,img.shape[1],sc): img[:,k]=(img[:,k]*0.85).astype(np.uint8)   # pixel grid
for k in range(0,img.shape[0],sc): img[k,:]=(img[k,:]*0.85).astype(np.uint8)
Image.fromarray(img).save(outp)
