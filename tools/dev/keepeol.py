# usage: keepeol.py <original> <edited_lf> <out>  - rebuild edited file keeping original line endings
import sys, difflib
orig=open(sys.argv[1],'rb').read(); raw=orig.split(b'\n'); norm=[l.rstrip(b'\r') for l in raw]
new=open(sys.argv[2],'rb').read().split(b'\n')
out=[]
for op,i1,i2,j1,j2 in difflib.SequenceMatcher(None,norm,new,autojunk=False).get_opcodes():
    out+= raw[i1:i2] if op=='equal' else [l+b'\r' for l in new[j1:j2]]
open(sys.argv[3],'wb').write(b'\n'.join(out))
