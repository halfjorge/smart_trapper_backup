import sys,re,zlib,struct
src,out=sys.argv[1],sys.argv[2]
d=open(src,'rb').read()
best=None
for m in re.finditer(rb'stream\r?\n',d):
    s=m.end(); e=d.find(b'endstream',s)
    if e-s<100000: continue
    try: raw=zlib.decompressobj().decompress(d[s:e])
    except Exception: continue
    i=raw.find(b'8BIMLayr')
    if i>=0:
        best=(raw,i);break
raw,i=best
print('found Layr at',i,'in stream of',len(raw))
# dump info for header
hdr=raw[:200]
print(hdr[:120])
open(out+'.bin','wb').write(raw)
