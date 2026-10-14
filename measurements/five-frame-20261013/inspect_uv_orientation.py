"""Inspect embedded base color with two V conventions; no source edits."""
import numpy as np
from PIL import Image,ImageDraw
from sequence_reader import ROOT,HANDOFF,GLBReader
from measure_stages import texture
r=GLBReader(HANDOFF/'frame_0000/model.glb');p,f,uv,_=r.mesh();rgb,_=texture(r)
# Bound point-render work while retaining full-frame mesh extents.
i=np.linspace(0,len(p)-1,250000).astype(int);p=p[i];uv=uv[i]
h,w=rgb.shape[:2];pixels=760;canvas=Image.new('RGB',(pixels*2,pixels*2+80),(21,23,31));draw=ImageDraw.Draw(canvas)
lo=p.min(0);hi=p.max(0)
for row,flip in enumerate([False,True]):
 u=np.mod(uv[:,0],1);v=np.mod(1-uv[:,1] if flip else uv[:,1],1)
 color=rgb[np.minimum((v*h).astype(int),h-1),np.minimum((u*w).astype(int),w-1)]
 for col,(a,b,depth,label) in enumerate([(0,1,2,'X/Y'),(2,1,0,'Z/Y')]):
  scale=(pixels-70)/max(hi[a]-lo[a],hi[b]-lo[b]);x=np.rint((p[:,a]-(lo[a]+hi[a])/2)*scale+pixels/2).astype(int);y=np.rint(-(p[:,b]-(lo[b]+hi[b])/2)*scale+pixels/2).astype(int)
  key=y*pixels+x;order=np.lexsort((p[:,depth],key));k=key[order];visible=order[np.r_[k[:-1]!=k[1:],True]]
  pic=np.empty((pixels,pixels,3),dtype='u1');pic[:]=[30,33,44];pic[y[visible],x[visible]]=color[visible]
  canvas.paste(Image.fromarray(pic),(col*pixels,row*(pixels+40)+32));draw.text((col*pixels+14,row*(pixels+40)+10),f'{label} / V={"1-v" if flip else "v"}',fill='white')
canvas.save(ROOT/'texture-v-orientation-review.png')
