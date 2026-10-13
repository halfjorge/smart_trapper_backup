import json, sys, numpy as np, cv2
from PIL import Image
for R in sys.argv[1:]:
    j=json.load(open(f'{R}/job.json')); key=j['keyLayerName']; cols=[c['name'] for c in j['colors']]; T=json.load(open(f'{R}/traps.json'))['traps']
    rd=lambda p: np.array(Image.open(p))[...,3]
    K=rd(f"{R}/masks/KEY_{key}.png")>=90
    depth=cv2.distanceTransform(K.astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
    print(f"== {R.split('T')[-1][:12]}  key pullback {j['keyTrapPullbackPx']}")
    anyink=np.zeros(K.shape,bool)
    for n in cols:
        c=rd(f'{R}/clean_masks/CLEAN__{n}.png')>0
        t=np.zeros(K.shape,bool)
        for tt in T:
            if tt['source']==n and tt['target']==key: t|=rd(f"{R}/{tt['png']}")>0
        anyink|=c|t
        # gap: key px not covered by this colour, touching its clean (3x3) AND touching its key trap (3x3)
        nc=cv2.dilate(c.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
        nt=cv2.dilate(t.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
        gap=K&~c&~t&nc&nt
        print(f'   {n:17s} clean reaches {np.percentile(depth[c&K],99) if (c&K).any() else 0:.1f} px into key | 1-px gaps between colour and its key trap: {int(gap.sum()):,} px  (depth p50 {np.median(depth[gap]) if gap.any() else 0:.1f})')
    g=K&~anyink
    for c in cols:
        pass
    # white line: key px with no ink at all that sit between ink on both sides within 2px
    hole=K&~anyink&cv2.dilate(anyink.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&(depth>1.0)&(depth<=2.5)
    print(f'   key px with NO ink at depth 1-2.5 px next to ink (the white line): {int(hole.sum()):,}')
