import numpy as np, json, os, sys
from PIL import Image
out=sys.argv[1]; zero=len(sys.argv)>2
os.makedirs(out+'/masks',exist_ok=True); os.makedirs(out+'/traps',exist_ok=True)
H=W=300; yy,xx=np.mgrid[:H,:W]
red=np.zeros((H,W),np.uint8); red[40:200,40:200]=255
blue=(((yy-170)**2+(xx-170)**2)<80**2).astype(np.uint8)*255
ring=((yy-170)**2+(xx-170)**2); key=((ring<84**2)&(ring>78**2)).astype(np.uint8)*255
if zero:  # colours far apart, no key contact -> 0 traps
    red=np.zeros((H,W),np.uint8); red[10:40,10:40]=255; blue=np.zeros((H,W),np.uint8); blue[250:290,250:290]=255; key=np.zeros((H,W),np.uint8); key[120:125,120:125]=255
# progressive knockout (key cuts colours, blue cuts red)
blue[key>0]=0; red[(key>0)|(blue>0)]=0
def save(a,p,c):
    x=np.zeros((H,W,4),np.uint8); x[...,:3]=c; x[...,3]=a; Image.fromarray(x).save(out+'/'+p)
save(key,'masks/KEY.png',(0,0,0)); save(red,'masks/1.png',(220,30,30)); save(blue,'masks/2.png',(30,60,220))
cols=[dict(name='red',blendMode='normal',opacity=100,fillOpacity=100),dict(name='blue',blendMode='normal',opacity=100,fillOpacity=100)]
files=[dict(kind='KEY',name='key',blendMode='normal',opacity=100,fillOpacity=100,png='masks/KEY.png'),
       dict(kind='COLOR',name='red',blendMode='normal',opacity=100,fillOpacity=100,png='masks/1.png'),
       dict(kind='COLOR',name='blue',blendMode='normal',opacity=100,fillOpacity=100,png='masks/2.png')]
json.dump(dict(docName='test',widthPx=W,heightPx=H,resolution=300,preflightCleanup=True,alphaThreshold=90,edgeBiasPx=1,
  keyTrapPullbackPx=1,colorTrapPullbackPx=0,trapShape='round',closeKeyHaloPx=0,keyLayerName='key',paperLayerName='paper',
  colors=cols,files=files),open(out+'/job.json','w'))
