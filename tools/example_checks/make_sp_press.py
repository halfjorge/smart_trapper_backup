# Build press-ready layered TIFF for Smashing Pumpkins Jacksonville.
import struct, zlib, numpy as np, cv2, sys, tifffile
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
SRC=sys.argv[1]; OUT=sys.argv[2]
im=Image.open(SRC); tags=im.tag_v2
W,H=im.size
psd=bytes(tags[37724]); res34377=bytes(tags[34377])
p=36; ln=struct.unpack('<I',psd[p+8:p+12])[0]; body=psd[p+12:p+12+ln]; tail=psd[p+12+ln+((4-ln%4)%4):]
# --- parse records keeping raw extra data
q=0; cnt=abs(struct.unpack('<h',body[:2])[0]); q=2; recs=[]
for i in range(cnt):
    t,l,b,r=struct.unpack('<4i',body[q:q+16]); q+=16
    nch=struct.unpack('<H',body[q:q+2])[0]; q+=2
    chans=[struct.unpack('<hI',body[q+6*c:q+6*c+6]) for c in range(nch)]; q+=6*nch
    blend=body[q:q+8]; q+=8
    opacity,clip,flags,filler=body[q:q+4]; q+=4
    el=struct.unpack('<I',body[q:q+4])[0]; q+=4; ex=body[q:q+el]; q+=el
    recs.append(dict(box=(t,l,b,r),chans=chans,blend=blend,opacity=opacity,clip=clip,flags=flags,filler=filler,ex=ex))
comps=[]
for rc in recs:
    for cid,cl in rc['chans']:
        comps.append(struct.unpack('<H',body[q:q+2])[0]); q+=cl
print('source channel compressions',set(comps))
def rename(ex,name):
    e=0; ml=struct.unpack('<I',ex[:4])[0]; e=4+ml; bl=struct.unpack('<I',ex[e:e+4])[0]; e+=4+bl
    head=ex[:e]; nl=ex[e]; e+=((1+nl+3)//4)*4; blocks=ex[e:]
    nb=name.encode('latin1'); pas=bytes([len(nb)])+nb; pas+=b'\0'*((4-len(pas)%4)%4)
    out=b''; f=0
    while f+12<=len(blocks):
        k=blocks[f+4:f+8]; L=struct.unpack('<I',blocks[f+8:f+12])[0]; blk=blocks[f:f+12+L]
        if k==b'inul':
            u=name.encode('utf-16-le'); data=struct.pack('<I',len(name))+u
            if len(data)%4: data+=b'\0'*(4-len(data)%4)
            blk=blocks[f:f+8]+struct.pack('<I',len(data))+data
        out+=blk; f+=12+L
    return head+pas+out
# --- masks
def A(i): return np.load(f'SP/{i}.npy',mmap_mode='r')[...,3]>127
green,tb,black,white=A(1),A(2),A(3),A(4)
k=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11))
inner=cv2.erode((green|black).astype(np.uint8),k).astype(bool)   # outside canvas counts as covered
gold=~inner & ~white
layers=[  # bottom -> top: (source record index, name, rgb, mask, opacity)
 (4,'paper',(255,255,255),np.ones((H,W),bool),255),
 (0,'GOLD',(223,189,56),gold,255),
 (1,'Green',(81,164,131),green&~white,255),
 (2,'trapped trans black',(0,0,0),tb&~white,recs[2]['opacity']),
 (3,'black',(0,0,0),black&~white,255),
]
del green,tb,black,white,inner
for _,n,_,m,_ in layers: print(n,'coverage %.1f%%'%(m.mean()*100))
# --- write layer info
recbytes=b''; chdata=b''
for src,name,rgb,mask,op in layers:
    rc=recs[src]; planes=[np.full((H,W),c,np.uint8) for c in rgb]+[mask.astype(np.uint8)*255]
    enc=[struct.pack('<H',3)+zlib.compress(np.diff(pl,axis=1,prepend=np.zeros((H,1),np.uint8)).astype(np.uint8).tobytes(),6) for pl in planes]
    ex=rename(rc['ex'],name)
    r=struct.pack('<4i',0,0,H,W)+struct.pack('<H',4)
    for cid,e in zip((0,1,2,-1),enc): r+=struct.pack('<hI',cid,len(e))
    r+=rc['blend']+bytes([op,rc['clip'],rc['flags']&~2,rc['filler']])+struct.pack('<I',len(ex))+ex
    recbytes+=r; chdata+=b''.join(enc)
lay=struct.pack('<h',len(layers))+recbytes+chdata
if len(lay)%4: lay+=b'\0'*(4-len(lay)%4)
newpsd=psd[:36]+b'MIB8ryaL'+struct.pack('<I',len(lay))+lay+tail
# --- composite
comp=np.zeros((H,W,3),np.float32)
for _,_,rgb,mask,op in layers:
    a=op/255.0
    comp[mask]=comp[mask]*(1-a)+np.array(rgb,np.float32)*a
comp=comp.round().astype(np.uint8)
Image.fromarray(comp[::5,::5]).save(OUT.replace('.tif','_preview.png'))
tifffile.imwrite(OUT,comp,photometric='rgb',resolution=(300,300),resolutionunit='INCH',
    software='Adobe Photoshop 27.10 (Windows)',compression='zlib',
    extratags=[(34377,7,len(res34377),res34377,True),(37724,7,len(newpsd),newpsd,True)])
print('written')
