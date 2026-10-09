exec(open('methane.py').read().split("H,W=B['key'].shape")[0])
H,W=B['key'].shape
K=B['key']; anyB=np.zeros((H,W),bool)
for n in cl[:-1]: anyB|=B[n]
paperB=~anyB&~K
upAll={}
newvis=np.zeros((H,W),bool)
for n in mine[:-1]:
    upA=np.zeros((H,W),bool)
    for u in mine[mine.index(n)+1:]: upA|=A[u]
    newvis|=A[n]&paperB&~upA
dK=cv2.distanceTransform((~K).astype(np.uint8),cv2.DIST_L2,cv2.DIST_MASK_PRECISE)
newvis&=dK>6
edge=np.zeros((H,W),bool); edge[:40]=edge[-40:]=True; edge[:,:40]=edge[:,-40:]=True
print(f'new visible ink >6px from key: {newvis.sum():,}px; within 40px of canvas edge: {(newvis&edge).sum():,}')
n,lab,st,_=cv2.connectedComponentsWithStats(newvis.astype(np.uint8),connectivity=8)
sz=st[1:,4]; print(f'pieces: {n-1:,}; median size {np.median(sz):.0f}px; pieces <=20px: {(sz<=20).sum():,} totalling {sz[sz<=20].sum():,}px; biggest {sorted(sz)[-5:]}')
# were these pinholes (paper fully enclosed by one colour) in the client?
holes=0; holepx=0
for k in range(1,n):
    x,y,w,h,a=st[k]
    if a>400: continue
    sub=lab[max(0,y-2):y+h+2,max(0,x-2):x+w+2]==k
    ring=cv2.dilate(sub.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&~sub
    region=anyB[max(0,y-2):y+h+2,max(0,x-2):x+w+2]
    if region[ring].all(): holes+=1; holepx+=a
print(f'pinholes (paper speck completely surrounded by colour in the client) now filled: {holes:,} pieces, {holepx:,}px')
big=np.argsort(sz)[::-1][:3]+1
for k in big:
    x,y,w,h,a=st[k]; print(f'   big piece {a:,}px at x {x}-{x+w}, y {y}-{y+h}')
