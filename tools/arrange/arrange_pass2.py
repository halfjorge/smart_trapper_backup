import json, sys, numpy as np, cv2
S=sys.argv[1]
m=json.load(open(f'{S}/wilco_meta.json')); names=m['names']; H,W=m['H'],m['W']
cover=np.load(f'{S}/wilco_cover.npy', mmap_mode='r'); vis=np.load(f'{S}/wilco_vis.npy'); comp=np.load(f'{S}/wilco_comp.npy', mmap_mode='r');  touch=None; platearr=np.load(f'{S}/wilco_plate.npy', mmap_mode='r')
def hexrgb(h): return np.array([int(h[i:i+2],16) for i in (0,2,4)], np.float32)
def Lstar(rgb):
    c=rgb/255; c=np.where(c<=0.04045,c/12.92,((c+0.055)/1.055)**2.4); Y=0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
    return 116*(Y**(1/3) if Y>0.008856 else 7.787*Y+16/116)-16
inks=[n for n in names if n!='paper']; P=names.index('paper')
L={n: Lstar(hexrgb(m['inks'][n])) for n in inks}
order=sorted(inks, key=lambda n: L[n])            # darkest first (= top)
print('order top->bottom:', [(n, m['inks'][n], round(L[n],1)) for n in order])
rank={n:r for r,n in enumerate(order)}            # 0 = top
plates={}; removed={}
for n in order:
    i=names.index(n)
    pl=np.array(platearr[i]); removed[n]=int(((np.asarray(cover[i])>0)&(pl==0)).sum())
    plates[n]=pl
    print(f'{n:7s} coverage {int((cover[i]>0).sum()):>11,}  kept {int((pl>0).sum()):>11,}  removed (lighter colour / paper showed on top there) {removed[n]:>10,}')
# new composite in ink colours, bottom->top
new=np.empty((H,W,3),np.uint8); soft=np.zeros((H,W),np.uint8)
for y0 in range(0,H,512):
    y1=min(H,y0+512); o=np.broadcast_to(hexrgb(m['inks']['paper']),(y1-y0,W,3)).copy()
    for n in reversed(order):
        A=(plates[n][y0:y1].astype(np.float32)/255)[...,None]; o=o*(1-A)+hexrgb(m['inks'][n])*A
        soft[y0:y1]|=((plates[n][y0:y1]>0)&(plates[n][y0:y1]<255)).astype(np.uint8)
    new[y0:y1]=np.clip(o+.5,0,255).astype(np.uint8)
soft=cv2.dilate(soft,np.ones((5,5),np.uint8)).astype(bool)
ch=np.zeros((H,W),bool)
for y0 in range(0,H,512):
    y1=min(H,y0+512); ch[y0:y1]=np.abs(new[y0:y1].astype(np.int16)-np.asarray(comp[y0:y1]).astype(np.int16)).max(2)>12
print(f'look vs original: changed {int(ch.sum()):,} px ({ch.mean()*100:.3f}%), soft edges {int((ch&soft).sum()):,}, solid areas {int((ch&~soft).sum()):,}')
np.save(f'{S}/wilco_new.npy', new); np.save(f'{S}/wilco_chsolid.npy', ch&~soft)
np.savez_compressed(f'{S}/wilco_plates.npz', **{n: plates[n] for n in order})
json.dump(dict(order=order, removed=removed), open(f'{S}/wilco_order.json','w'))
