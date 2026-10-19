import sys,struct
raw=open(sys.argv[1],'rb').read()
L=struct.unpack('>Q',raw[8:16])[0]
content=raw[16:16+L]
W,H=int(sys.argv[3]),int(sys.argv[4])
hdr=b'8BPS'+struct.pack('>H',2)+b'\0'*6+struct.pack('>HIIHH',3,H,W,8,3)
li=struct.pack('>Q',len(content))+content
if len(li)%2: li+=b'\0'
lm=li+struct.pack('>I',0)
body=hdr+struct.pack('>I',0)+struct.pack('>I',0)+struct.pack('>Q',len(lm))+lm
# image data: RLE, each row 2 bytes (0xFF? use literal run of 0 repeat): use compression 1 with PackBits for constant rows
import math
row=b''
n=W
while n>0:
    k=min(128,n); row+=bytes([257-k if k>1 else 0, 255]) if k>1 else bytes([0,255]); n-=k
counts=struct.pack('>I',len(row))*(H*3)
body+=struct.pack('>H',1)+counts+row*(H*3)
open(sys.argv[2],'wb').write(body)
print(len(body))
