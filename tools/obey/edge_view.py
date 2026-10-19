# Render a right-edge strip of the bleed result, multiply view like Sara's, chosen layers only.
import numpy as np, sys, json
sys.path.insert(0,'/home/claude/ex'); sys.path.insert(0,'/home/claude/smart_trapper_backup/tools/obey')
from obey_proto import order,col,cn
from bleed_apply import load_map
from PIL import Image
W,H=9600,12000;RB=1200
def right_strip(mapf,y0,y1,inner=250):
    mp=load_map(mapf); Bt=int(mp['Bs'][0]); Br=int(mp['Bs'][3]); x1i=int(mp['box'][3]); y0i=int(mp['box'][0])
    def layer(n):
        P=np.load(f'j_{n}.npy',mmap_mode='r'); out=np.zeros((y1-y0,inner+Br),bool)
        oy=np.arange(y0,y1)-Bt   # inner-row index
        rows=np.unpackbits(np.asarray(P[(y0i+oy.min())*RB:(y0i+oy.max()+1)*RB])).reshape(-1,W)
        out[:,:inner]=rows[:, x1i-inner:x1i]
        # bleed columns
        allr=None
        for d in range(1,Br+1):
            sy=mp['Mr'][d-1][oy]; sx=x1i-1-mp['Dr'][d-1][oy]
            need=np.unique(sy)
            out[:,inner+d-1]=[ (np.unpackbits(np.asarray(P[(y0i+a)*RB:(y0i+a+1)*RB]))[b]) for a,b in zip(sy,sx)]
        return out
    return layer
def render(mapf,y0,y1,only,keyop=None):
    lay=right_strip(mapf,y0,y1); img=None
    for n in order:
        if cn(n) not in only: continue
        m=lay(n)
        if img is None: img=np.zeros(m.shape+(3,),np.float32); img[:]=(248,239,229)
        c=np.array(col[cn(n)])/255.0
        img[m]=img[m]*((1-0.66)+0.66*c) if n=='Key' else img[m]*c
    return img.astype(np.uint8)
