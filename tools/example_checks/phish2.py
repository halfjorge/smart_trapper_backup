import numpy as np, json, cv2
off=150
def load(d):
    m=json.load(open(d+'/meta.json')); return [x[1] for x in m['layers']],[np.load(f'{d}/{i}.npy',mmap_mode='r') for i in range(len(m['layers']))]
nb,lb=load('Phish/before'); na,la=load('Phish/after')
H,W=lb[0].shape[:2]
def m(l):
    x=l[...,3]>127
    if x.shape!=(H,W): x=x[off:off+H,off:off+W]
    return np.ascontiguousarray(x).astype(np.uint8)
B={n:m(lb[i]) for i,n in enumerate(nb) if i>0}; A={n:m(la[na.index(n)]) for n in na[1:] if n in B}
key='Line work'; colors=[n for n in na[1:] if n!=key]
K=B[key]
anyB=np.zeros((H,W),np.uint8)
for n in colors: anyB|=B[n]
anyA=np.zeros((H,W),np.uint8)
for n in colors: anyA|=A[n]
paper_b=(1-anyB)&(1-K)          # paper showing in client file
paper_a=(1-anyA)&(1-K)
filled=paper_b&(1-paper_a)
dK=cv2.distanceTransform((1-K).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
print(f'paper showing in client file: {paper_b.sum():,}px; after: {paper_a.sum():,}px; filled with colour: {filled.sum():,}px')
h=np.bincount(np.minimum(np.ceil(dK[filled==1]).astype(int),30),minlength=31)
print('filled paper: distance to nearest Line work px:', ' '.join(f'{k}:{h[k]}' for k in range(0,16)), '>15:',h[16:].sum())
# paper gaps in client: how wide are the halos? distance of client paper pixels to key, and to colour
dC=cv2.distanceTransform((1-anyB).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
# halo pixels = client paper pixels that are within 6px of both key and some colour
halo=paper_b&(dK<=6)&(dC<=6)
print(f'client paper within 6px of both line work and a colour (the halo): {halo.sum():,}px, of which filled now: {(halo&filled).sum():,}px')
other=paper_b&~((dK<=6)&(dC<=6)).astype(bool)
print(f'other client paper: {other.sum():,}px, of which filled now: {(other&filled).sum():,}px')
# Was colour grown out onto paper away from key? colour after pixels on paper_b with dK>8
for n in colors:
    g=A[n]&paper_b&(dK>8)
    print(f'  {n!r}: grown onto paper more than 8px from line work: {int(g.sum()):,}px')
# halo width stats: for each halo pixel, dK+dC ~ gap width
gw=(dK+dC)[paper_b&(dK<=12)&(dC<=12)==1]
print('gap width between colour and line work (dK+dC), percentiles 50/90/99:',np.percentile(gw,[50,90,99]).round(1))
# shape of spread under key: chessboard vs L2 for a few colours
for n in ['Neon (?) Green','Purple']:
    vis=B[n]
    inv=(1-vis).astype(np.uint8)
    d2=cv2.distanceTransform(inv,cv2.DIST_L2,cv2.DIST_MASK_PRECISE); dc=cv2.distanceTransform(inv,cv2.DIST_C,3)
    zone=K==1
    for name,d in [('round',d2),('square',dc)]:
        line=[]
        for k in range(1,11):
            sel=zone&((d>k-0.5)&(d<=k+0.5) if name=='round' else (np.round(d)==k)); t=sel.sum()
            line.append(f'{k}:{(A[n][sel].sum()/t*100 if t else 0):.0f}%')
        print(f'  {n!r} under line work, share kept by distance ({name}):',' '.join(line))
