import numpy as np, json, sys
from PIL import Image, ImageDraw
mb=json.load(open('Ocean/before/meta.json'))['layers']; ma=json.load(open('Ocean/after/meta.json'))['layers']
nb={l[1]:l[0] for l in mb}; na={l[1].replace(' *OVERLAY*',''):l[0] for l in ma}
R=np.load('Ocean_gray/result.npz'); tg=json.load(open('Ocean_gray/result_targets.json'))
order=['L BLUE','BLUE D','OCHRE','coral','blue 3','DATE BLK']
raw={n:np.load(f"Ocean/before/{nb[n]}.npy",mmap_mode='r') for n in order}
rgb={n:np.median(np.asarray(raw[n][::8,::8,:3])[np.asarray(raw[n][::8,::8,3])>240],axis=0) for n in order}
paper=np.median(np.asarray(np.load(f"Ocean/before/{nb['manilla paer']}.npy",mmap_mode='r')[::16,::16,:3]).reshape(-1,3),axis=0)
def comp(get,sl,shape):
    o=np.broadcast_to(paper.astype(np.float32),shape+(3,)).copy()
    for n in order:
        A=get(n,sl)[...,None]; o=o*(1-A)+((o*rgb[n]/255) if n=='OCHRE' else rgb[n])*A
    return np.clip(o,0,255).astype(np.uint8)
cl=lambda n,sl: raw[n][sl][...,3]/255.
hd=lambda n,sl: np.load(f"Ocean/after/{na[n]}.npy",mmap_mode='r')[sl][...,3]/255.
def te(n,sl):
    if n=='DATE BLK': return cl(n,sl)
    i=nb[n]; a=R[f'clean_{i}'][sl].astype(np.float32)
    for k in range(len(tg[str(i)])): a=np.maximum(a,R[f'trap_{i}_{k}'][sl])
    return a/255
if sys.argv[1]=='overview':
    sl=(slice(None,None,8),slice(None,None,8)); sh=raw['DATE BLK'][sl].shape[:2]
    Image.fromarray(np.concatenate([comp(cl,sl,sh),comp(te,sl,sh)],1)).save(sys.argv[2])
else:
    spots=[tuple(map(int,s.split(','))) for s in sys.argv[3:]]; r=300; rows=[]
    for cx,cy in spots:
        sl=(slice(cy-r,cy+r),slice(cx-r,cx+r)); sh=(2*r,2*r)
        p=[comp(cl,sl,sh),comp(hd,sl,sh),comp(te,sl,sh)]
        rows.append(np.pad(np.concatenate([np.pad(x,((0,0),(0,8),(0,0)),constant_values=255) for x in p],1),((16,4),(0,0),(0,0)),constant_values=255))
    im=Image.fromarray(np.concatenate(rows,0)); d=ImageDraw.Draw(im)
    for k,t in enumerate(['client','your hand after','test (current logic)']): d.text((k*608+4,2),t,fill=(0,0,0))
    im.save(sys.argv[2])
