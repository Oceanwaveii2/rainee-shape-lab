from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
APP=ROOT.parents[1]
v=np.fromfile(APP/'assets/positions.bin',dtype='<f4').reshape(-1,3)
f=np.fromfile(APP/'assets/triangles.bin',dtype='<u4').reshape(-1,3)
def render(v,f,path,x=(-.22,.22),y=(.34,.65),camera='front'):
    p=v.copy()
    if camera=='back':p[:,0]*=-1;p[:,2]*=-1
    if camera=='side':p=p[:,[2,1,0]]
    keep=np.all((p[f][:,:,0]>x[0]-.025)&(p[f][:,:,0]<x[1]+.025)&(p[f][:,:,1]>y[0]-.025)&(p[f][:,:,1]<y[1]+.025),axis=1)
    ff=f[keep];tri=p[ff];c=tri.mean(1)
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    w=1100;h=int(w*(y[1]-y[0])/(x[1]-x[0]));im=Image.new('RGB',(w,h),(29,29,35));d=ImageDraw.Draw(im)
    for i in np.argsort(c[:,2]):
        xy=[((q[0]-x[0])/(x[1]-x[0])*w,(y[1]-q[1])/(y[1]-y[0])*h) for q in tri[i]]
        s=.3+.7*abs(float(normals[i]@np.array([.25,.35,.9])))
        d.polygon(xy,fill=tuple(int(c*s) for c in (196,154,203)))
    # Axis grid assists locating repair.
    for a in np.arange(np.ceil(x[0]/.05)*.05,x[1],.05):
        xx=(a-x[0])/(x[1]-x[0])*w;d.line((xx,0,xx,h),fill=(50,60,63));d.text((xx+3,5),f'x {a:.2f}',fill=(235,235,240))
    for a in np.arange(np.ceil(y[0]/.05)*.05,y[1],.05):
        yy=(y[1]-a)/(y[1]-y[0])*h;d.line((0,yy,w,yy),fill=(50,60,63));d.text((4,yy+3),f'y {a:.2f}',fill=(235,235,240))
    im.save(path)
if __name__=='__main__':
    edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
    e,counts=np.unique(edges,axis=0,return_counts=True)
    boundary=e[counts==1]
    central=(np.max(np.abs(v[boundary][:,:,0]),axis=1)<.1)&(np.min(v[boundary][:,:,1],axis=1)>.38)&(np.max(v[boundary][:,:,1],axis=1)<.59)
    np.savez(ROOT/'diagnostic-data.npz',boundary=boundary,central_boundary=boundary[central])
    report={'points':len(v),'triangles':len(f),'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum()),'central_boundary_edges':int(central.sum())}
    (ROOT/'inspection.json').write_text(json.dumps(report,indent=2))
    render(v,f,ROOT/'proxy-front.png');render(v,f,ROOT/'proxy-back.png',camera='back')
    print(json.dumps(report,indent=2))
