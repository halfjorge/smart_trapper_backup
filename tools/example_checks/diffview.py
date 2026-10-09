import numpy as np, json, sys, cv2
from PIL import Image
job=sys.argv[1]; off=int(sys.argv[2]); cname=sys.argv[3]; x0,y0,w,h=map(int,sys.argv[4:8]); zoom=int(sys.argv[8]) if len(sys.argv)>8 else 4
def load(d):
    m=json.load(open(d+'/meta.json')); return [x[1] for x in m['layers']],[np.load(f'{d}/{i}.npy',mmap_mode='r') for i in range(len(m['layers']))]
nb,lb=load(f'{job}/before'); na,la=load(f'{job}/after')
H,W=lb[0].shape[:2]
colors=nb[1:-1]; key=nb[-1]
fin=np.load(f'sim_{job}_final.npy',mmap_mode='r')[colors.index(cname)]
sl=(slice(y0,y0+h),slice(x0,x0+w))
A=la[na.index(cname)][...,3][off+y0:off+y0+h, off+x0:off+x0+w]>127
Bc=lb[nb.index(cname)][...,3][sl]>127
K=lb[nb.index(key)][...,3][sl]>127
T=np.asarray(fin[sl])
img=np.full((h,w,3),235,np.uint8)
img[K]=(60,60,60)                        # line work (key)
img[Bc&~K]=(190,190,255)                 # client colour (pale)
both=A&T; img[both&K]=(40,140,40); img[both&~K]=(120,200,120)
img[A&~T]=(230,30,30)                    # manual only
img[T&~A]=(30,90,240)                    # trapper only
Image.fromarray(img).resize((w*zoom,h*zoom),Image.NEAREST).save(sys.argv[9] if len(sys.argv)>9 else 'diff.png')
