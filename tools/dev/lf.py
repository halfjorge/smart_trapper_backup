# Convert CRLF -> LF in place (repo stores LF). Usage: lf.py <files...>
import sys
for p in sys.argv[1:]:
    b=open(p,'rb').read()
    if b'\0' in b: continue
    open(p,'wb').write(b.replace(b'\r\n',b'\n'))
