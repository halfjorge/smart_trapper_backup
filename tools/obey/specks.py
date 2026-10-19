# Stray-pixel cleanup under the key: inside the key, any tiny island (<= MAXPX) of one colour's trap that is
# surrounded by another colour's trap is handed to the surrounding colour. Only TRAP__*_under_Key changes.
import numpy as np, json, sys
from scipy import ndimage
D=sys.argv[1]; W,H=9600,12000; RB=W//8; MAXPX=12
names=['Yellow','Cream','Red','Light Blue','Blue','Dark blue']
vis=json.load(open(f'{D}/vis_layers.json'))
L=np.load(f'{D}/labels.npy',mmap_mode='r')
P={n:np.load(f'{D}/j_{n}.npy') for n in vis if n!='Key'}
def rows(n,y0,y1): return np.unpackbits(P[n][y0*RB:y1*RB]).reshape(y1-y0,W).astype(bool)
def put(n,y0,y1,m): P[n][y0*RB:y1*RB]=np.packbits(m.ravel())
moved=0; S=1500; PAD=20
for y0 in range(0,H,S):
    a,b=max(0,y0-PAD),min(H,y0+S+PAD)
    K=np.asarray(L[a:b])==7
    if not K.any(): continue
    top=np.zeros((b-a,W),np.int8)
    for n in vis:
        if n=='Key': continue
        i=names.index(n.split('__')[1].split('_under_')[0])+1
        top[rows(n,a,b)]=i
    top[~K]=0
    changed={}
    for i in range(1,7):
        lab,k=ndimage.label(top==i)
        if k==0: continue
        sz=ndimage.sum(np.ones_like(lab),lab,range(1,k+1))
        for j in np.nonzero(sz<=MAXPX)[0]:
            m=lab==j+1
            ring=ndimage.binary_dilation(m,np.ones((3,3)))&~m
            nb=top[ring]; nb=nb[nb>0]
            if len(nb)==0: continue
            vals,cnt=np.unique(nb,return_counts=True); o=int(vals[np.argmax(cnt)])
            if o==i or cnt.max()<0.75*len(nb): continue
            # inside the strip interior only
            ys=np.nonzero(m)[0]
            if ys.min()+a<y0 or ys.max()+a>=min(H,y0+S): continue
            changed.setdefault((i,o),np.zeros_like(K))
            changed[(i,o)]|=m
    for (i,o),m in changed.items():
        src=f'TRAP__{names[i-1]}_under_Key'; dst=f'TRAP__{names[o-1]}_under_Key'
        if src not in P or dst not in P: continue
        r=rows(src,a,b); put(src,a,b,r&~m)
        r2=rows(dst,a,b); put(dst,a,b,r2|m); moved+=int(m.sum())
for n,p in P.items(): np.save(f'{D}/j_{n}.npy',p)
print('stray px handed to the surrounding colour:',moved)
