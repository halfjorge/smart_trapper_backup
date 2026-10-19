import numpy as np,sys
from PIL import Image,ImageDraw
from scipy import ndimage
sys.path.insert(0,'/home/claude/ex')
from obey_proto import order,col,cn
W,H=9600,12000;RB=1200
def get(pre,n,box):
    x0,y0,x1,y1=box; P=np.load(f'{pre}_{n}.npy',mmap_mode='r')
    return np.unpackbits(np.asarray(P[y0*RB:y1*RB])).reshape(y1-y0,W)[:,x0:x1].astype(bool)
def render(pre,box,only,ants=True):
    x0,y0,x1,y1=box; img=np.zeros((y1-y0,x1-x0,3),np.uint8); img[:]=(248,239,229)
    for n in order:
        if cn(n) not in only or n=='Key': continue
        img[get(pre,n,box)]=col[cn(n)]
    if ants:
        k=get(pre,'Key',box); edge=k&~ndimage.binary_erosion(k); img[edge]=(0,0,0)
    return img
def sheet(spots,out,pres=('a','j'),labels=('trapper original','fixed now')):
    tiles=[]
    for lab,box,only,z in spots:
        ims=[render(p,box,only) for p in pres]
        t=np.hstack([ims[0],np.full((ims[0].shape[0],6,3),255,np.uint8),ims[1]])
        im=Image.fromarray(t).resize((t.shape[1]*z,t.shape[0]*z),Image.NEAREST)
        c=Image.new('RGB',(im.width,im.height+22),'white');c.paste(im,(0,22))
        ImageDraw.Draw(c).text((4,5),f'{lab}   LEFT = {labels[0]}   RIGHT = {labels[1]}   (key off, black line = key edge)',fill='black'); tiles.append(c)
    w=max(t.width for t in tiles); S=Image.new('RGB',(w,sum(t.height+10 for t in tiles)),'white'); y=0
    for t in tiles: S.paste(t,(0,y)); y+=t.height+10
    S.save(out)
