from pathlib import Path
import numpy as np,json
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parent;A=R.parents[1]/'assets'
v=np.fromfile(A/'positions.bin','<f4').reshape(-1,3);f=np.fromfile(A/'triangles.bin','<u4').reshape(-1,3)
e,c=np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0,return_counts=True)
count={tuple(q):n for q,n in zip(e,c)}
ok=np.array([all(count[tuple(sorted(q))]==2 for q in [(a,b),(b,c),(c,a)]) for a,b,c in f])
cv=v[f].mean(1);ids=np.flatnonzero(ok&(np.abs(cv[:,0])<.06)&(cv[:,1]>.525)&(cv[:,1]<.60))
tree=cKDTree(cv[ids])
targets=[(0,.585,.066),(0,.576,-.052),(-.028,.553,.02),(.028,.553,.02)]
for t in targets:
 d,j=tree.query(t,k=1);i=ids[j]; print('target',t,'actual',cv[i].tolist(),'distance',d,'face',int(i),'verts',f[i].tolist())
