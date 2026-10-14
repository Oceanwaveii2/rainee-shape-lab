"""Bounded local transition sculpting on the actual boolean union topology."""
import numpy as np,json
from scipy.sparse import coo_matrix
from pathlib import Path
from pelvic_repair import edge_counts,write_obj
from inspect_proxy import render
R=Path(__file__).resolve().parent
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def refine(v,f):
 v=np.asarray(v).copy();base=v.copy()
 w=smooth(.530,.551,v[:,1])*(1-smooth(.605,.632,v[:,1]))*(1-smooth(.039,.065,np.abs(v[:,0])))*smooth(-.075,-.042,v[:,2])*(1-smooth(.073,.095,v[:,2]))
 # Uniform topology averaging is restricted to short local edges, to prevent
 # noisy collapsed source triangles from pulling one anatomical part across another.
 e,_=edge_counts(f);length=np.linalg.norm(v[e[:,0]]-v[e[:,1]],axis=1)
 e=e[(length<.015)&(length>1e-8)]
 e=np.vstack((e,e[:,::-1]));a=coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(v),len(v))).tocsr()
 degree=np.asarray(a.sum(1)).ravel();degree=np.maximum(degree,1)
 for j in range(32):
  for rate in [.46,-.475]:
   avg=a@v/degree[:,None]
   v+=rate*w[:,None]*(avg-v)
 # Lift the rectangular flap's side corners into a continuous groin arch.
 # The anterior contour remains shallow; this is structural skin shaping only.
 local=(np.abs(base[:,0])<.032)&(base[:,1]>.543)&(base[:,1]<.578)&(base[:,2]>-.008)
 arc=.553-.010*(np.minimum(np.abs(base[:,0])/.029,1))**2
 lift=1-smooth(.556,.580,base[:,1])
 v[local,1]=np.maximum(v[local,1],arc[local]*lift[local]+v[local,1]*(1-lift[local]))
 v[w==0]=base[w==0]
 return v.astype('<f4'),w
if __name__=='__main__':
 v=np.fromfile(R/'boolean-positions.bin','<f4').reshape(-1,3);f=np.fromfile(R/'boolean-triangles.bin','<u4').reshape(-1,3)
 o,w=refine(v,f);o.tofile(R/'refined-positions.bin');f.tofile(R/'refined-triangles.bin');write_obj(R/'Rainee-pelvic-refined.obj',o,f)
 render(o,f,R/'refined-front.png');render(o,f,R/'refined-back.png',camera='back')
 e,c=edge_counts(f)
 report={'method':'Houdini polygon union plus bounded Taubin transition smoothing',
 'points':len(o),'triangles':len(f),'modified_points':int((np.linalg.norm(o-v,axis=1)>1e-9).sum()),
 'modified_bounds':{'min':v[np.linalg.norm(o-v,axis=1)>1e-9].min(0).tolist(),'max':v[np.linalg.norm(o-v,axis=1)>1e-9].max(0).tolist()},
 'distant_max_displacement':float(np.max(np.linalg.norm(o[w==0]-v[w==0],axis=1))),
 'height_drift':float(np.ptp(o[:,1])-np.ptp(v[:,1])),'max_local_shift':float(np.max(np.linalg.norm(o-v,axis=1))),
 'boundary_edges':int((c==1).sum()),'nonmanifold_edges':int((c>2).sum()),'finite':bool(np.isfinite(o).all()),
 'status':'Visually improved local union candidate; source topology defects persist'}
 (R/'refined-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
