# Add bleed. Straight/clean edges are carried outward along their own direction; busy curvy pattern areas
# (like the flower texture) are mirrored instead, so the pattern keeps going. Thin paper slivers right at a
# trim edge (art not quite reaching the edge) are replaced too.
# One position map is built from all visible ink layers together and applied identically to every layer.
import numpy as np, json, sys
D=sys.argv[1]; B=int(sys.argv[2]) if len(sys.argv)>2 else 150
W,H=9600,12000; RB=W//8; K=30
vis=json.load(open(f'{D}/vis_layers.json'))
def rows(n,y0,y1):
    P=np.load(f'{D}/j_{n}.npy',mmap_mode='r'); return np.unpackbits(np.asarray(P[y0*RB:y1*RB])).reshape(y1-y0,W).astype(bool)
_sig={}
def sig_rows(y0,y1):
    s=np.zeros((y1-y0,W),np.uint32)
    for i,n in enumerate(vis): s|=rows(n,y0,y1).astype(np.uint32)<<i
    return s
# --- inset: edge lines where paper shows through much more than just inside are rebuilt as bleed
def paper_frac(line): return float((line==0).mean())
top=sig_rows(0,12); bot=sig_rows(H-12,H)
lef=np.concatenate([sig_rows(y,min(H,y+2000))[:,:12] for y in range(0,H,2000)]); rig=np.concatenate([sig_rows(y,min(H,y+2000))[:,-12:] for y in range(0,H,2000)])
def inset(lines):   # lines[k] = k-th line from the edge
    ref=paper_frac(lines[10]); k=0
    while k<8 and paper_frac(lines[k])>ref+0.01: k+=1
    return k
ins={'t':inset(top),'b':inset(bot[::-1]),'l':inset(lef.T),'r':inset(rig.T[::-1])}
print('insets',ins,flush=True)
def side_map(S,Bn):
    """S[k,t]: signature k lines in from the edge line. Returns (M,Dp): bleed line d -> source (depth Dp, pos M)."""
    n=S.shape[1]; e=S[0]
    cross=np.nonzero(e[1:]!=e[:-1])[0]+1
    p=cross.astype(float); s=np.zeros(len(p)); good=np.zeros(len(p),bool)
    top=np.zeros(S.shape,np.int8)               # top-most visible ink per pixel (for tracing printed edges)
    for i in range(len(vis)):
        on=((S>>np.uint32(i))&np.uint32(1)).astype(bool); top[on]=i+1
    def trace(L,c):
        a,b=L[0][c-1],L[0][c]; pos=[(0,float(c))]; cur=float(c)
        for k in range(1,K):
            row=L[k]; lo,hi=int(max(1,cur-3)),int(min(n-1,cur+4))
            cand=[t for t in range(lo,hi) if row[t-1]==a and row[t]==b]
            if not cand: break
            cur=float(min(cand,key=lambda t:abs(t-cur))); pos.append((k,cur))
        return pos
    traced=np.zeros(len(p),bool)
    for i,c in enumerate(cross):
        pos=trace(S,c)
        if len(pos)<8 and top[0][c-1]!=top[0][c]: pos=trace(top,c)
        if len(pos)>=8:
            ks=np.array([q[0] for q in pos]); ts=np.array([q[1] for q in pos])
            f=np.polyfit(ks,ts,1); s[i]=float(np.clip(f[0],-3,3)); traced[i]=True
            res=np.abs(np.polyval(f,ks)-ts).max()
            good[i]= len(pos)>=K-2 and res<=1.5
    # an edge we could not follow borrows the direction of the nearest followed edge (within 20 px)
    for i in np.nonzero(~traced)[0]:
        j=np.nonzero(traced)[0]
        if len(j):
            k=j[np.argmin(np.abs(p[j]-p[i]))]
            if abs(p[k]-p[i])<=20: s[i]=s[k]; good[i]=good[k]
    # busy pattern spans: runs of consecutive edges that are not clean straight lines get mirrored.
    # Spans start and end exactly on a colour edge, so the seam with the straight-carried art is invisible.
    pattern=np.zeros(n,bool); i=0
    while i<len(cross):
        if good[i]: i+=1; continue
        j=i
        while j+1<len(cross) and not good[j+1] and cross[j+1]-cross[j]<200: j+=1
        if j-i+1>=4: pattern[cross[i]:cross[j]]=True
        i=j+1
    allowed=np.unique(e[pattern]) if pattern.any() else np.array([],np.uint32)
    M=np.zeros((Bn,n),np.float32); Dp=np.zeros((Bn,n),np.int32); t=np.arange(n,dtype=float)
    for d in range(1,Bn+1):
        if len(p):
            q=np.maximum.accumulate(p-s*d)
            xs=np.concatenate([[q[0]-1e6],q,[q[-1]+1e6]]); ys=np.concatenate([[p[0]-1e6],p,[p[-1]+1e6]])
            M[d-1]=np.interp(t+0.5,xs,ys)-0.5
        else: M[d-1]=t
        # mirror only where the mirrored pixel is still part of the pattern (never mirror a neighbouring line)
        ok=pattern.copy()
        if d-1<S.shape[0]: ok&=np.isin(S[d-1],allowed)
        else: ok[:]=False
        M[d-1][ok]=t[ok]; Dp[d-1][ok]=d-1
    return np.clip(np.rint(M),0,n-1).astype(np.int32),Dp,pattern
# inner rectangle (original coords) that is kept as-is
y0i,y1i,x0i,x1i=ins['t'],H-ins['b'],ins['l'],W-ins['r']
Bl,Br,Bt,Bb=B+ins['l'],B+ins['r'],B+ins['t'],B+ins['b']
# left/right strips from the inner rectangle
L=[];R=[]
for y in range(y0i,y1i,2000):
    sg=sig_rows(y,min(y1i,y+2000)); L.append(sg[:,x0i:x0i+B+8]); R.append(sg[:,x1i-B-8:x1i][:,::-1])
L=np.concatenate(L).T; R=np.concatenate(R).T
Ml,Dl,pl=side_map(L,Bl); Mr,Dr,pr=side_map(R,Br)
print('left/right pattern px',int(pl.sum()),int(pr.sum()),flush=True)
# extended rows (inner rows, full extended width) -> original coords, for top/bottom tracing
W2=(x1i-x0i)+Bl+Br
def ext_row(yi):   # yi index within inner rows
    sy=np.full(W2,y0i+yi,np.int32); sx=np.zeros(W2,np.int32); sx[Bl:Bl+(x1i-x0i)]=np.arange(x0i,x1i)
    for d in range(1,Bl+1): sy[Bl-d]=y0i+Ml[d-1][yi]; sx[Bl-d]=x0i+Dl[d-1][yi]
    for d in range(1,Br+1): sy[Bl+(x1i-x0i)-1+d]=y0i+Mr[d-1][yi]; sx[Bl+(x1i-x0i)-1+d]=x1i-1-Dr[d-1][yi]
    return sy,sx
def sig_line(sy,sx):
    a,b=int(sy.min()),int(sy.max())+1; sg=sig_rows(a,b); return sg[sy-a,sx]
Hn=y1i-y0i
T=np.array([sig_line(*ext_row(k)) for k in range(B+8)]); Bo=np.array([sig_line(*ext_row(Hn-1-k)) for k in range(B+8)])
Mt,Dt,pt=side_map(T,Bt); Mb,Db,pb=side_map(Bo,Bb)
print('top/bottom pattern px',int(pt.sum()),int(pb.sum()),flush=True)
np.savez(f'{D}/bleed_map.npz',Ml=Ml,Dl=Dl,Mr=Mr,Dr=Dr,Mt=Mt,Dt=Dt,Mb=Mb,Db=Db,B=B,
         box=np.array([y0i,y1i,x0i,x1i]),Bs=np.array([Bt,Bb,Bl,Br]))
print('saved')
