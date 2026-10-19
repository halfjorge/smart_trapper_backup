import numpy as np,json,sys
from PIL import Image,ImageDraw
sys.path.insert(0,'/home/claude/ex')
W,H=9600,12000;RB=W//8
from obey_proto import order,col,cn
def get(pre,n,box):
    x0,y0,x1,y1=box; P=np.load(f'{pre}_{n}.npy',mmap_mode='r')
    return np.unpackbits(np.asarray(P[y0*RB:y1*RB])).reshape(y1-y0,W)[:,x0:x1].astype(bool)
def render(pre,box,T):
    x0,y0,x1,y1=box; img=np.zeros((y1-y0,x1-x0,3),np.uint8); img[:]=(248,239,229)
    for n in order:
        m=get(pre,n,box); c=cn(n)
        if c in(T,'Key'): img[m]=(img[m]*0.5+np.array(col[c])*0.5).astype(np.uint8)
        else: img[m]=col[c]
    return img
log=json.load(open('joint_log.json'))
sel=[l for l in log if len(l)>6 and l[6]>0]
want=sys.argv[1]; out=sys.argv[2]; N=int(sys.argv[3])
pick=[l for l in sel if f'{l[0]}-{l[5]}'==want][:N]
r=30;z=4;tiles=[]
for l in pick:
    T,A,B,jx,jy=l[:5]; box=(max(0,jx-r),max(0,jy-r),min(W,jx+r),min(H,jy+r))
    a=render('a',box,T); b=render('j',box,T)
    t=np.hstack([a,np.full((a.shape[0],3,3),255,np.uint8),b])
    im=Image.fromarray(t).resize((t.shape[1]*z,t.shape[0]*z),Image.NEAREST)
    c=Image.new('RGB',(im.width,im.height+18),'white');c.paste(im,(0,18))
    ImageDraw.Draw(c).text((3,3),f'{A}/{B} under {T} x{jx} y{jy}  now | fixed',fill='black'); tiles.append(c)
cols=3; w=tiles[0].width; h=tiles[0].height
S=Image.new('RGB',(cols*(w+10),((len(tiles)+cols-1)//cols)*(h+10)),'white')
for i,t in enumerate(tiles): S.paste(t,((i%cols)*(w+10),(i//cols)*(h+10)))
S.save(out)
