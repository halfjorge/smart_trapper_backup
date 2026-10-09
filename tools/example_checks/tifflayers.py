# Read Photoshop layers stored inside a layered TIFF (little-endian ImageSourceData).
import struct, zlib, numpy as np, sys, os, json
def packbits(src, n):
    out=bytearray(); i=0
    while len(out)<n and i<len(src):
        c=src[i]; i+=1
        if c<128: out+=src[i:i+c+1]; i+=c+1
        elif c>128: out+=bytes([src[i]])*(257-c); i+=1
    return bytes(out[:n])
def read_layers(d, out, H, W):
    p=d.index(b'Adobe Photoshop Document Data Block\0')+36
    while p<len(d):
        sig,key=d[p:p+4],d[p+4:p+8]; ln=struct.unpack('<I',d[p+8:p+12])[0]; body=d[p+12:p+12+ln]
        if key==b'ryaL': break
        p+=12+ln+((4-ln%4)%4)
    q=0; cnt=struct.unpack('<h',body[q:q+2])[0]; q+=2; cnt=abs(cnt)
    recs=[]
    for li in range(cnt):
        t,l,b,r=struct.unpack('<4i',body[q:q+16]); q+=16
        nch=struct.unpack('<H',body[q:q+2])[0]; q+=2
        chans=[]
        for c in range(nch):
            cid,cl=struct.unpack('<hI',body[q:q+6]); q+=6; chans.append((cid,cl))
        bsig=body[q:q+4]; bkey=body[q+4:q+8][::-1].decode(); q+=8
        opacity,clip,flags,_=body[q:q+4]; q+=4
        el=struct.unpack('<I',body[q:q+4])[0]; q+=4; ex=body[q:q+el]; q+=el
        e=0; ml=struct.unpack('<I',ex[e:e+4])[0]; e+=4+ml
        bl=struct.unpack('<I',ex[e:e+4])[0]; e+=4+bl
        nl=ex[e]; name=ex[e+1:e+1+nl].decode('latin1'); e+=((1+nl+3)//4)*4
        # unicode name
        while e+12<=len(ex):
            k=ex[e+4:e+8]; L=struct.unpack('<I',ex[e+8:e+12])[0]; blk=ex[e+12:e+12+L]
            if k==b'inul':
                n=struct.unpack('<I',blk[:4])[0]; name=blk[4:4+2*n].decode('utf-16-le').rstrip('\0')
            if k==b'tcsl':  # section divider (groups)
                pass
            e+=12+L+((4-L%4)%4) if False else 12+L
        recs.append(dict(name=name,box=(t,l,b,r),chans=chans,blend=bkey,opacity=opacity,flags=flags,hidden=bool(flags&2)))
    os.makedirs(out,exist_ok=True); meta=[]
    for i,rc in enumerate(recs):
        t,l,b,r=rc['box']; h,w=b-t,r-l
        planes={}
        for cid,cl in rc['chans']:
            comp=struct.unpack('<H',body[q:q+2])[0]; data=body[q+2:q+cl]; q+=cl
            if cid<-1 or h<=0 or w<=0: continue
            if comp==0: arr=np.frombuffer(data[:h*w],np.uint8).reshape(h,w)
            elif comp==1:
                counts=struct.unpack(f'<{h}H',data[:2*h]); o=2*h; rows=[]
                for c in counts: rows.append(packbits(data[o:o+c],w)); o+=c
                arr=np.frombuffer(b''.join(rows),np.uint8).reshape(h,w)
            elif comp in (2,3):
                raw=np.frombuffer(zlib.decompress(data),np.uint8).reshape(h,w)
                arr=np.cumsum(raw,axis=1,dtype=np.uint8) if comp==3 else raw
            planes[cid]=arr
        full=np.zeros((H,W,4),np.uint8)
        if h>0 and w>0:
            y0,x0=max(t,0),max(l,0); y1,x1=min(b,H),min(r,W)
            for ci,cid in enumerate((0,1,2,-1)):
                if cid in planes: full[y0:y1,x0:x1,ci]=planes[cid][y0-t:y1-t,x0-l:x1-l]
                elif cid==-1: full[y0:y1,x0:x1,3]=255
        np.save(f'{out}/{i}.npy',full)
        meta.append((i,rc['name'],'BlendMode.'+{'norm':'NORMAL','mul ':'MULTIPLY','dark':'DARKEN'}.get(rc['blend'],rc['blend']),int((full[...,3]>127).sum()),rc['opacity'],rc['hidden']))
        print(i,repr(rc['name']),rc['blend'],'opacity',rc['opacity'],'hidden' if rc['hidden'] else '','box',rc['box'],'ink',meta[-1][3])
    json.dump(dict(W=W,H=H,layers=[m[:4] for m in meta]),open(f'{out}/meta.json','w'))
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
d=bytes(Image.open(sys.argv[1]).tag_v2[37724]); read_layers(d, sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
