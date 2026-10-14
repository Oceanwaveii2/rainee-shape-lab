"""Make a lightweight inspection proxy; preserve the source FBX unchanged."""
import json, pathlib, zlib, numpy as np, hashlib
from scan_fbx import scan, SOURCE
root=pathlib.Path(__file__).resolve().parent
data=scan(); nodes=data['nodes']
def array(name, dtype):
    p=next(n['props'][0] for n in nodes if n['path']=='/Objects/Geometry/'+name)
    with SOURCE.open('rb') as f:
        f.seek(p['offset']); raw=f.read(p['length'])
    if p['encoding']:raw=zlib.decompress(raw)
    return np.frombuffer(raw,dtype=dtype)
v=array('Vertices','<f8').reshape(-1,3)
lo=v.min(0);hi=v.max(0);print('Bounds',lo,hi,flush=True)
cell=(hi-lo).max()/260
q=np.floor((v-lo)/cell).astype(np.int32); shape=q.max(0).astype(np.int64)+1
ids=q[:,0].astype(np.int64)+shape[0]*(q[:,1].astype(np.int64)+shape[1]*q[:,2]); del q
unique,inv=np.unique(ids,return_inverse=True);del ids
counts=np.bincount(inv); proxy=np.column_stack([np.bincount(inv,weights=v[:,i])/counts for i in range(3)])
source_count=len(v);del v
p=array('PolygonVertexIndex','<i4'); ends=np.flatnonzero(p<0); lengths=np.diff(np.r_[-1,ends]);print('Polygon sizes',np.unique(lengths,return_counts=True),flush=True)
mapped=inv[np.where(p<0,-p-1,p)];del p,inv
starts=ends-lengths+1;faces=[]
for size in np.unique(lengths):
    if size<3:continue
    st=starts[lengths==size]
    for k in range(1,int(size)-1):
        a=mapped[st];b=mapped[st+k];c=mapped[st+k+1]
        keep=(a!=b)&(b!=c)&(a!=c)
        faces.append(np.column_stack([a[keep],b[keep],c[keep]]).astype(np.uint32))
t=np.concatenate(faces);del faces,mapped
_,ix=np.unique(np.sort(t,axis=1),axis=0,return_index=True);t=t[np.sort(ix)]
# Store Y-up native FBX coordinates, normalized to unit height. UI applies artist-selected scale.
height=hi[1]-lo[1];center=(lo+hi)/2
proxy[:,0]-=center[0];proxy[:,1]-=lo[1];proxy[:,2]-=center[2];proxy/=height
(root/'assets').mkdir(exist_ok=True)
proxy.astype('<f4').tofile(root/'assets/positions.bin');t.astype('<u4').tofile(root/'assets/triangles.bin')
report={'source':str(SOURCE),'source_vertices':source_count,'source_polygons':len(ends),'proxy_vertices':len(proxy),'proxy_triangles':len(t),'source_bounds':{'min':lo.tolist(),'max':hi.tolist()},'source_dimensions_cm':(hi-lo).tolist(),'normalization_height_source_units':float(height),'proxy_method':'Vertex clustering, 260 cells along longest dimension; inspection proxy, not production retopology','rigged':any(n['path']=='/Objects/Deformer' for n in nodes),'reference_status':'Artist estimates; images do not determine hidden depth or absolute stature'}
(root/'assets/mesh-info.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
