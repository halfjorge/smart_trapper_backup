# Remove pixels the joint fix ADDED to a TRAP__X layer when that pixel is already inked by another layer of the
# same colour X (CLEAN__X or another TRAP__X). Separations are unchanged (same union per colour); only the
# double-stacked pixels that show darker in a multiply preview go away. The trapper's own overlaps are left alone.
import numpy as np, json, sys
D=sys.argv[1]; W,H=9600,12000
vis=json.load(open(f'{D}/vis_layers.json'))
for X in ['Yellow','Cream','Red','Light Blue','Blue','Dark blue']:
    ls=[n for n in vis if n!='Key' and n.split('__')[1].split('_under_')[0]==X]
    J={n:np.unpackbits(np.load(f'{D}/j_{n}.npy'))[:W*H].astype(bool) for n in ls}
    A={n:np.unpackbits(np.load(f'{D}/a_{n}.npy'))[:W*H].astype(bool) for n in ls}
    for n in ls:
        if not n.startswith('TRAP__'): continue
        others=np.zeros(W*H,bool)
        for o in ls:
            if o!=n: others|=J[o]
        drop=J[n]&~A[n]&others
        if drop.any():
            J[n]=J[n]&~drop; print(n,'removed doubled px',int(drop.sum()))
            np.save(f'{D}/j_{n}.npy',np.packbits(J[n]))
    del J,A
