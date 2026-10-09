import numpy as np, json, cv2
off=150; H,W=7200,5400
mb=json.load(open('BTS2/before/meta.json'))['layers']; ma=json.load(open('BTS2/after/meta.json'))['layers']
nb=[x[1] for x in mb]; na=[x[1] for x in ma]
fl=json.load(open('BTS/flat/meta.json'))['layers']; nf=[x[1] for x in fl]
san=lambda s: ''.join('_' if c in '/\\:*?"<>|' else c for c in s)
cols=nb[1:-1]; key=nb[-1]; allc=cols+[key]
B={n:np.asarray(np.load(f'BTS2/before/{nb.index(n)}.npy',mmap_mode='r')[...,3])>127 for n in allc}
A={n:np.ascontiguousarray(np.asarray(np.load(f'BTS2/after/{na.index(n)}.npy',mmap_mode='r')[off:off+H,off:off+W,3])>127) for n in allc}
F={n:np.asarray(np.load(f'BTS/flat/{nf.index("COLOR__"+san(n)) if n!=key else nf.index(key)}.npy',mmap_mode='r')[...,3])>127 for n in allc}
short=lambda n:n.split(' - ')[0]
client_order=allc; manual_order=[na[i] for i in range(1,len(na))]
print('client order:',[short(x) for x in client_order]); print('manual order:',[short(x) for x in manual_order])
rows=[]
for x in allc:
    for y in allc:
        if x==y: continue
        # pixels where client shows y (visible) and x was extended into it, within 10px of x's client edge
        d=cv2.distanceTransform((~B[x]).astype(np.uint8),cv2.DIST_L2,5)
        zone=B[y]&~B[x]&(d<=10)
        m=(A[x]&zone).sum(); f=(F[x]&zone).sum()
        if m>20000 or f>20000:
            rows.append((x,y,m,f))
print(f'\n{"spreads":16s} {"into":16s} {"you (px)":>10s} {"trapper":>10s}   x below y? client / yours')
for x,y,m,f in sorted(rows,key=lambda r:-(r[2]-r[3])):
    cb=client_order.index(x)<client_order.index(y); mbelow=manual_order.index(x)<manual_order.index(y)
    print(f'{short(x):16s} {short(y):16s} {m:>10,} {f:>10,}   {"below" if cb else "ABOVE"} / {"below" if mbelow else "ABOVE"}')
