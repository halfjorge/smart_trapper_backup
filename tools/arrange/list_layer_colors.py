import sys, warnings, numpy as np; warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/claude/psdsrc/src')
from psd_tools import PSDImage
from collections import Counter
p=PSDImage.open(sys.argv[1])
tot=Counter()
def path(l):
    s=[]; x=l
    while x is not None and x is not p: s.append(x.name); x=x.parent
    return '/'.join(reversed(s))
for l in p.descendants():
    if l.is_group(): continue
    if l.kind=='solidcolorfill':
        print('FILL', path(l), l.tagged_blocks.get_data(b'SoCo') if hasattr(l,'tagged_blocks') else '', 'mask bbox', l.mask.bbox if l.has_mask() else None); continue
    im=l.topil()
    if im is None: print('EMPTY', path(l)); continue
    a=np.asarray(im.convert('RGBA'))
    al=a[...,3]; sol=al>=250
    if not sol.any(): print(f'{path(l):45s} no solid px'); continue
    q=(a[...,:3][sol]//1).astype(np.int32); key=q[:,0]*65536+q[:,1]*256+q[:,2]
    u,c=np.unique(key,return_counts=True); o=np.argsort(-c)
    top=[(f'#{u[i]:06x}',int(c[i])) for i in o[:4]]
    share=c[o[0]]/c.sum()
    print(f'{path(l):45s} vis={l.visible} solid={sol.sum():>9,} ncol={len(u):>6} top={top} main={share*100:.0f}%')
    for i in o[:50]: tot[f'#{u[i]:06x}']+=int(c[i])
print('\nOVERALL top colours:')
for k,v in tot.most_common(30): print(k,f'{v:,}')
