import json, sys, numpy as np, cv2
from PIL import Image
for R in sys.argv[1:]:
    j=json.load(open(f'{R}/job.json')); key=j['keyLayerName']; cols=[c['name'] for c in j['colors']]; T=json.load(open(f'{R}/traps.json'))['traps']; pb=j['keyTrapPullbackPx']
    rd=lambda p: np.array(Image.open(p))[...,3]
    K=rd(f"{R}/masks/KEY_{key}.png")>=90
    ink=np.zeros(K.shape,bool); top=np.zeros(K.shape,np.int8)
    for i,n in enumerate(cols):
        m=rd(f'{R}/clean_masks/CLEAN__{n}.png')>0
        for t in T:
            if t['source']==n: m|=rd(f"{R}/{t['png']}")>0
        ink|=m; top[m]=i+1
    paper=~K&(top==0)
    dpap=cv2.distanceTransform((~paper).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    nearink=cv2.dilate(ink.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    hole=K&~ink&nearink&(dpap>pb*1.5+0.5)
    # sandwiched: ink on both sides within 3 px
    k,lab=cv2.connectedComponents(hole.astype(np.uint8),connectivity=8)
    print(f"{R.split('/')[-1]:5s} pullback {pb} follow={j.get('keyTrapsFollowVisible')}: key px with no ink, next to ink, NOT near paper: {int(hole.sum()):>9,}  (pieces {k-1:,})")
    np.save(f"{R}/hole.npy",hole)
