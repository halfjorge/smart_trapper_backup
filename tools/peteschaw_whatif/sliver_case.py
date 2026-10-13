import json, sys, numpy as np, cv2
from PIL import Image
A=sys.argv[1]; Bs=sys.argv[2:]
exec(open("own_eval.py").read().split("ex_tot=0")[0].split("SH=int(sys.argv[3]) if len(sys.argv)>3 else 2",1)[1].replace("LA,LB=layers(A),layers(B); tA,tB=topof(LA),topof(LB)","LA=layers(A); tA=topof(LA)"))
# raw owner (no sliver rule)
bestr=np.full(K.shape,1e9,np.float32); raw=np.zeros(K.shape,np.int16)
for c in range(0,len(cols)+1):
    d=cv2.distanceTransform((V!=c).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE); u=d<bestr-1e-4; bestr[u]=d[u]; raw[u]=c
case=K&(best<=5)&~pull&(raw>owner)&(owner>0)    # key px behind a thin line of a later colour
dline=bestr  # distance to that thin line
print(f'key px behind a thin line of a later colour (olive behind blue etc): {int(case.sum()):,}')
for B in [A]+Bs:
    t=topof(layers(B))
    ok=case&(t==owner)
    print(f'  {B.split("/")[-1]:5s}: colour behind the line on top {100*ok.sum()/case.sum():5.1f}%   | at 1 px from the line {100*(ok&(dline<=1.5)).sum()/max(1,(case&(dline<=1.5)).sum()):5.1f}%  | 2-5 px {100*(ok&(dline>1.5)).sum()/max(1,(case&(dline>1.5)).sum()):5.1f}%')
