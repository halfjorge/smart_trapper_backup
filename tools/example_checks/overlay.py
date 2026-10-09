import numpy as np, json, cv2
def load(d):
    m=json.load(open(d+'/meta.json')); return [x[1] for x in m['layers']],[x[2] for x in m['layers']],[np.load(f'{d}/{i}.npy',mmap_mode='r') for i in range(len(m['layers']))]
nb,mb,lb=load('Mempho/before'); na,ma,la=load('Mempho/after')
H,W=lb[0].shape[:2]
B=[np.ascontiguousarray(l[...,3]>127) for l in lb]; A=[np.ascontiguousarray(l[...,3]>127) for l in la]
names=[n.replace(' *OVERLAY*','') for n in na]
mult=['MULTIPLY' in m for m in mb]
KEY=len(B)-1
for i in range(1,len(B)):
    removed=B[i]&~A[i]; added=A[i]&~B[i]
    print(f'\n### {names[i]} ({"MULTIPLY" if mult[i] else "normal"})  before {B[i].sum():,}  after {A[i].sum():,}')
    print(f'  removed {removed.sum():,}px:', ', '.join(f'under {names[j]} {(removed&B[j]).sum():,}' for j in range(i+1,len(B)) if (removed&B[j]).sum()), f'| not under anything {(removed&~np.any([B[j] for j in range(i+1,len(B))],axis=0)).sum() if i<KEY else removed.sum():,}')
    print(f'  added {added.sum():,}px')
    # kept under each upper layer: how much of the overlap with that upper layer survived?
    for j in range(i+1,len(B)):
        ov=B[i]&B[j]
        if ov.sum(): print(f'    overlap with {names[j]} ({"mult" if mult[j] else "normal"}): client {ov.sum():,} -> kept {(ov&A[i]).sum():,} ({(ov&A[i]).sum()/ov.sum()*100:.0f}%)')
    # trap width under key: distance of kept-under-key pixels from the key's edge
    if i<KEY:
        dk=cv2.distanceTransform(B[KEY].astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)  # distance inside key to key edge
        kept=A[i]&B[KEY]
        h=np.bincount(np.minimum(np.round(dk[kept]).astype(int),30),minlength=31)
        print('   kept under key, by depth inside the key (px):',' '.join(f'{k}:{h[k]:,}' for k in range(0,12)),'>11:',f'{h[12:].sum():,}')
