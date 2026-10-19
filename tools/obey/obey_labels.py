import sys,numpy as np,gc
sys.path.insert(0,'/home/claude/psdsrc/src')
from psd_tools import PSDImage
P=PSDImage.open('auto.psb'); W,H=P.size
names=['Yellow','Cream','Red','Light Blue','Blue','Dark blue','Key']
L=np.zeros((H,W),np.uint8)
for l in P.descendants():
    if l.kind=='pixel' and l.name in names:
        i=names.index(l.name)+1
        a=np.asarray(l.topil().getchannel('A')) if l.topil().mode=='RGBA' else None
        x0,y0,x1,y1=l.bbox
        sub=L[y0:y0+a.shape[0],x0:x0+a.shape[1]]
        sub[a>127]=i; print(l.name,flush=True); del a; gc.collect()
np.save('labels.npy',L)
