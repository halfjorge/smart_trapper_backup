# Grow a layered PSD by the bleed map (bleed.py) - every layer, hidden ones included, goes through the same map.
import sys, gc, numpy as np
sys.path.insert(0,'/home/claude/psdsrc/src'); sys.path.insert(0,'/home/claude/smart_trapper_backup/tools/obey')
from psd_tools import PSDImage
from psd_tools.constants import Tag, Compression
from bleed_apply import load_map, apply
src,mapf,outp=sys.argv[1:4]
mp=load_map(mapf); y0i,y1i,x0i,x1i=[int(v) for v in mp['box']]; Bt,Bb,Bl,Br=[int(v) for v in mp['Bs']]
p=PSDImage.open(src); rec=p._record; V=rec.header.version
W,H=rec.header.width,rec.header.height; H2,W2=(y1i-y0i)+Bt+Bb,(x1i-x0i)+Bl+Br
li=rec.layer_and_mask_information.layer_info
def lname(r):
    try: return r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME)
    except Exception: return r.name
dy,dx=Bt-y0i,Bl-x0i
for r,chs in zip(li.layer_records,li.channel_image_data):
    n=lname(r); w,h=r.right-r.left,r.bottom-r.top
    if w<=0 or h<=0: continue
    touches = r.top<=y0i or r.left<=x0i or r.bottom>=y1i or r.right>=x1i
    if not touches:
        r.top+=dy; r.bottom+=dy; r.left+=dx; r.right+=dx; print(' shift',n,flush=True); continue
    planes={}
    for ci,ch in zip(r.channel_info,chs):
        if ci.id<-1: raise SystemExit('mask channel in '+n)
        a=np.frombuffer(ch.get_data(w,h,8,version=V),np.uint8).reshape(h,w)
        full=np.zeros((H,W),np.uint8); full[r.top:r.bottom,r.left:r.right]=a; del a
        planes[ci.id]=apply(full,mp); del full; gc.collect()
    al=planes.get(-1)
    if al is not None:
        ys=np.where(al.any(1))[0]; xs=np.where(al.any(0))[0]
        t,b,l,rr=int(ys[0]),int(ys[-1]+1),int(xs[0]),int(xs[-1]+1)
    else: t,b,l,rr=0,H2,0,W2
    r.top,r.bottom,r.left,r.right=t,b,l,rr
    for ci,ch in zip(r.channel_info,chs):
        d=np.ascontiguousarray(planes[ci.id][t:b,l:rr]).tobytes()
        ch.compression=Compression.RLE; ch.set_data(d,rr-l,b-t,8,version=V)
    del planes,al; gc.collect(); print(' bleed',n,flush=True)
# flattened preview
comp=[]
raw=rec.image_data.get_data(rec.header)
nch=rec.header.channels
for c in range(nch):
    a=np.frombuffer(raw[c*W*H:(c+1)*W*H] if isinstance(raw,(bytes,bytearray)) else raw[c],np.uint8).reshape(H,W)
    comp.append(np.ascontiguousarray(apply(a,mp)).tobytes()); gc.collect()
del raw
rec.header.width,rec.header.height=W2,H2
rec.image_data.compression=Compression.RLE
rec.image_data.set_data(comp,rec.header)
with open(outp,'wb') as f: rec.write(f)
print('saved',outp,W2,H2)
