import numpy as np,json
from pathlib import Path
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
R=Path(__file__).resolve().parent;A=R.parents[1]/'assets'
v=np.fromfile(A/'positions.bin','<f4').reshape(-1,3);f=np.fromfile(A/'triangles.bin','<u4').reshape(-1,3)
def boundary(f):
 e,c=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),1),axis=0,return_counts=True);return e[c==1]
e=boundary(f); n,c=connected_components(coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(v),len(v))),directed=False)
used=np.unique(e);regions=[]
for label in np.unique(c[used]):
 ids=used[c[used]==label];vv=v[ids];lo=vv.min(0);hi=vv.max(0)
 if lo[1]>.5 and hi[1]<.7 and min(abs(lo[0]),abs(hi[0]))<.05:
  ed=e[c[e[:,0]]==label];_,degree=np.unique(ed,return_counts=True)
  regions.append({'label':int(label),'points':len(ids),'edges':len(ed),'min':lo.tolist(),'max':hi.tolist(),'degree':dict(zip(*[a.tolist() for a in np.unique(degree,return_counts=True)]))})
print(json.dumps(sorted(regions,key=lambda r:-r['points']),indent=2))
