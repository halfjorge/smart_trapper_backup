# Rebuild the trapper's own Obey file record-for-record (low-level, low memory), swapping in the joint-fixed
# CLEAN__/TRAP__ pixels, dropping Sara's white "Layer 1", writing a normal .psd at 600 ppi.
import sys, gc, numpy as np
sys.path.insert(0,'/home/claude/psdsrc/src')
from psd_tools import PSDImage
from psd_tools.constants import Tag, Resource, Compression
from psd_tools.psd.image_resources import ImageResource, ResoulutionInfo
src,D,outp=sys.argv[1:4]; DPI=600; W,H=9600,12000
col={'Yellow':(234,180,73),'Cream':(239,226,194),'Red':(195,33,36),'Light Blue':(57,180,198),'Blue':(76,137,166),'Dark blue':(14,63,93),'Key':(7,26,41)}
def m(pre,n): return np.unpackbits(np.load(f'{D}/{pre}_{n}.npy'))[:W*H].reshape(H,W)
p=PSDImage.open(src); rec=p._record
li=rec.layer_and_mask_information.layer_info
recs=li.layer_records; cdat=li.channel_image_data
def lname(r):
    try: return r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME)
    except Exception: return r.name
keep_r=[];keep_c=[]
for r,chs in zip(recs,cdat):
    n=lname(r)
    if n=='Layer 1': print('drop',n); continue
    fixed=False
    if n.startswith('CLEAN__') or n.startswith('TRAP__'):
        j=m('j',n)
        if (j!=m('a',n)).any():
            fixed=True; X=n.split('__')[1].split('_under_')[0]
            ys=np.where(j.any(1))[0]; xs=np.where(j.any(0))[0]
            r.top,r.bottom,r.left,r.right=int(ys[0]),int(ys[-1]+1),int(xs[0]),int(xs[-1]+1)
            sub=j[r.top:r.bottom,r.left:r.right]; w,h=r.right-r.left,r.bottom-r.top
            for ci,ch in zip(r.channel_info,chs):
                if ci.id==-1: data=(sub*255).astype(np.uint8).tobytes()
                elif ci.id in (0,1,2): data=bytes([col[X][ci.id]])*(w*h)
                else: raise SystemExit('unexpected channel %d in %s'%(ci.id,n))
                ch.compression=Compression.RLE; ch.set_data(data,w,h,8,version=1)
        del j
    if not fixed:
        w,h=r.right-r.left,r.bottom-r.top
        for ci,ch in zip(r.channel_info,chs):
            if ci.id<-1: raise SystemExit('layer mask present in %s - not handled'%n)
            if ch.compression==Compression.RLE and w>0 and h>0:
                d=ch.get_data(w,h,8,version=2); ch.set_data(d,w,h,8,version=1); del d
    print(' ',n,'(fixed)' if fixed else '',flush=True); gc.collect()
    keep_r.append(r); keep_c.append(chs)
recs[:]=keep_r; cdat[:]=keep_c
li.layer_count=len(keep_r) if li.layer_count>0 else -len(keep_r)
# flattened preview = what the layers show (paper, colours, key at its own opacity)
comp=np.zeros((H,W,3),np.float32); comp[:]=(248,239,229)
order=[lname(r) for r in keep_r]
vis={lname(r):(r.flags.visible if hasattr(r.flags,'visible') else True, r.opacity) for r in keep_r}
for n in order:
    if n.startswith('CLEAN__') or n.startswith('TRAP__'):
        X=n.split('__')[1].split('_under_')[0]; mm=m('j',n).astype(bool); comp[mm]=col[X]
    elif n=='Key':
        mm=m('j','Key').astype(bool); a=vis['Key'][1]/255; comp[mm]=comp[mm]*(1-a)+np.array(col['Key'])*a
comp=np.clip(comp+0.5,0,255).astype(np.uint8)
rec.header.version=1
rec.image_data.compression=Compression.RLE
rec.image_data.set_data([np.ascontiguousarray(comp[...,c]).tobytes() for c in range(3)],rec.header)
del comp; gc.collect()
from psd_tools.psd.image_resources import ImageResources
if rec.image_resources is None or not hasattr(rec.image_resources,"__setitem__"): rec.image_resources=ImageResources.new()
rec.image_resources[Resource.RESOLUTION_INFO]=ImageResource(key=Resource.RESOLUTION_INFO,data=ResoulutionInfo(DPI<<16,1,1,DPI<<16,1,1))
with open(outp,'wb') as f: rec.write(f)
print('saved',outp)
