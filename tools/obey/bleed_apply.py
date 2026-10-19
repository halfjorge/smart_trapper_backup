import numpy as np
def load_map(path):
    z=np.load(path); return {k:z[k] for k in z.files}
def apply(A,mp):
    """A: (H,W[,c]) full original canvas -> canvas grown by B on every side, bleed filled from the map."""
    B=int(mp['B']); y0,y1,x0,x1=[int(v) for v in mp['box']]; Bt,Bb,Bl,Br=[int(v) for v in mp['Bs']]
    I=A[y0:y1,x0:x1]; h,w=I.shape[:2]
    out=np.empty((h+Bt+Bb,w+Bl+Br)+A.shape[2:],A.dtype)
    out[Bt:Bt+h,Bl:Bl+w]=I
    for d in range(1,Bl+1): out[Bt:Bt+h,Bl-d]=I[mp['Ml'][d-1],mp['Dl'][d-1]]
    for d in range(1,Br+1): out[Bt:Bt+h,Bl+w-1+d]=I[mp['Mr'][d-1],w-1-mp['Dr'][d-1]]
    for d in range(1,Bt+1): out[Bt-d]=out[Bt+mp['Dt'][d-1],mp['Mt'][d-1]]
    for d in range(1,Bb+1): out[Bt+h-1+d]=out[Bt+h-1-mp['Db'][d-1],mp['Mb'][d-1]]
    return out
