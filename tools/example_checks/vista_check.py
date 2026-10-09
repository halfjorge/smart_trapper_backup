import numpy as np, cv2, json
from PIL import Image
names=['Layer 2','Pink','Red','LighT Green','Dark Green','Black','OG']
cols=[(255,255,255),(222,48,139),(222,30,51),(199,221,129),(128,195,72),(0,0,0)]
M=[np.asarray(np.load(f'Vista/{i}.npy',mmap_mode='r')[...,3])>127 for i in range(1,6)]
og=np.load('Vista/6.npy',mmap_mode='r')
ogm=np.asarray(og[...,3])>127
H,W=M[0].shape
# visible ink per pixel (top-most)
top=np.zeros((H,W),np.int8)  # 0 paper, 1..5
for i,m in enumerate(M): top[m]=i+1
pal=np.array(cols,np.uint8)
comp=pal[top]
ogrgb=np.asarray(og[...,:3])
d=(np.abs(comp.astype(int)-ogrgb.astype(int)).max(-1)>40)&ogm
print('seps vs OG: pixels that differ %.3f%% of OG area'%(d.sum()/ogm.sum()*100))
# which ink OG expects vs seps give
ogtop=np.full((H,W),-1,np.int8)
for k,c in enumerate(cols): ogtop[(np.abs(ogrgb.astype(int)-np.array(c)).max(-1)<=40)&ogm]=k
import collections
c=collections.Counter(zip(ogtop[d].tolist(),top[d].tolist()))
for (a,b),n in c.most_common(8): print('  OG says',names[a] if a>=0 else 'other','-> seps show',names[b] if b>0 else 'paper',n)
np.save('/tmp/claude-0/-home-claude/b32582e0-6a71-52fc-8cea-4d712cf57558/scratchpad/vista_diff.npy',d)
# butt check: boundary between visible lower i and visible upper j, j not black-covered
k3=np.ones((3,3),np.uint8)
print('pairs (lower under upper): edge px, butt px (lower does not run under upper), typical trap px')
butt_all=np.zeros((H,W),bool)
for j in range(len(M)):
    vj=top==j+1
    for i in range(j):
        vi=top==i+1
        edge_j=vj & cv2.dilate(vi.astype(np.uint8),k3).astype(bool)   # upper pixels touching visible lower
        if edge_j.sum()==0: continue
        butt=edge_j & ~M[i]
        # trap width: distance into upper region that lower extends
        under=M[i]&vj
        dist=cv2.distanceTransform((~vi).astype(np.uint8),cv2.DIST_L2,3)
        tw=dist[under & (dist<30)]
        tws=np.percentile(tw,90) if len(tw) else 0
        butt_all|=butt
        print(f'  {names[i+1]:12s} under {names[j+1]:12s} edge {edge_j.sum():>8,} butt {butt.sum():>8,} ({butt.sum()/edge_j.sum()*100:5.1f}%)  trap ~{tws:.1f}px')
np.save('/tmp/claude-0/-home-claude/b32582e0-6a71-52fc-8cea-4d712cf57558/scratchpad/vista_butt.npy',butt_all)
# lower colors extending past upper onto paper? (trap showing)
