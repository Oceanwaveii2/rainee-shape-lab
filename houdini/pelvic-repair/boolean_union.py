"""Test a native exact polygon union; does not change the main scene."""
import hou,numpy as np,json,time
from pathlib import Path
R=Path(__file__).resolve().parent
o=hou.node('/obj').createNode('geo','EXTERNAL_PELVIC_UNION')
a=o.createNode('file','SOURCE');a.parm('file').set(str(R.parent/'body_proxy.bgeo.sc'))
b=o.createNode('file','BRIDGE');b.parm('file').set(str(R/'saddle-donor.obj'))
union=o.createNode('boolean','LOCAL_UNION');union.setInput(0,a);union.setInput(1,b)
union.parm('resolvea').set(0);union.parm('resolveb').set(0);union.parm('detriangulate').set('none')
union.parm('useabseamedges').set(1)
start=time.time();g=union.geometry();print('Boolean cook '+str(time.time()-start)+' s',flush=True)
g.saveToFile(str(R/'boolean-union.bgeo.sc'));g.saveToFile(str(R/'boolean-union.obj'))
vv=np.array([p.position() for p in g.points()],dtype='<f4');ff=[]
for p in g.prims():
 ids=[q.point().number() for q in p.vertices()]
 for j in range(1,len(ids)-1):ff.append([ids[0],ids[j],ids[j+1]])
ff=np.array(ff,dtype='<u4');vv.tofile(R/'boolean-positions.bin');ff.tofile(R/'boolean-triangles.bin')
union.setDisplayFlag(True);union.setRenderFlag(True);hou.hipFile.save(str(R/'Rainee-Boolean-Repair-Study.hip'))
report={'points':len(vv),'triangles':len(ff),'errors':list(union.errors()),'warnings':list(union.warnings()),'cook_seconds':time.time()-start}
(R/'boolean-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
