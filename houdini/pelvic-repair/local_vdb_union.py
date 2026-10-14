"""Native local implicit replacement; remote body geometry remains source polygons.

The VDB is a construction intermediate. Its smoothed/dilated skin is clipped
to a small ellipsoid, then polygon-unioned to the original proxy. This trims
overlap rather than leaving the saddle graft inside the old flap surface.
"""
import hou,numpy as np,json,time
from pathlib import Path
R=Path(__file__).resolve().parent
obj=hou.node('/obj').createNode('geo','RAINEE_LOCAL_IMPLICIT_REPAIR')
source=obj.createNode('file','ORIGINAL_PROXY');source.parm('file').set(str(R.parent/'body_proxy.bgeo.sc'))
seed=obj.createNode('file','JOINED_STRUCTURAL_SEED');seed.parm('file').set(str(R/'body-pelvic-repair.bgeo.sc'))
sdf=obj.createNode('vdbfrompolygons','REBUILD_SKIN_FIELD');sdf.setInput(0,seed);sdf.parm('voxelsize').set(.0015)
sm=obj.createNode('vdbsmoothsdf','ROUND_DEFECTIVE_FLAP');sm.setInput(0,sdf);sm.parm('radius').set(5);sm.parm('iterations').set(5)
expand=obj.createNode('vdbreshapesdf','COVER_DEFECTIVE_SOURCE');expand.setInput(0,sm);expand.parm('operation').set('dilate');expand.parm('voxeloffset').set(.5)
convert=obj.createNode('convertvdb','LOCAL_SKIN_MESH');convert.setInput(0,expand);convert.parm('conversion').set('poly');convert.parm('adaptivity').set(0.)
roi=obj.createNode('sphere','REPAIR_SCOPE');roi.parm('type').set('poly');roi.parmTuple('rad').set((.070,.077,.111));roi.parmTuple('t').set((0.,.579,-.005));roi.parm('freq').set(6)
cut=obj.createNode('boolean','TRIM_TO_REPAIR_SCOPE');cut.setInput(0,convert);cut.setInput(1,roi);cut.parm('booleanop').set('intersect');cut.parm('resolvea').set(0);cut.parm('resolveb').set(0);cut.parm('detriangulate').set('none')
core=obj.createNode('sphere','REMOVE_DEFECTIVE_CORE');core.parm('type').set('poly');core.parmTuple('rad').set((.058,.065,.099));core.parmTuple('t').set((0.,.579,-.005));core.parm('freq').set(6)
outside=obj.createNode('boolean','CARVE_DEFECTIVE_FLAP_AND_OVERLAP');outside.setInput(0,source);outside.setInput(1,core);outside.parm('booleanop').set('subtract');outside.parm('resolvea').set(0);outside.parm('resolveb').set(0);outside.parm('detriangulate').set('none')
join=obj.createNode('boolean','EXACT_SOURCE_PLUS_LOCAL_SKIN');join.setInput(0,outside);join.setInput(1,cut);join.parm('resolvea').set(0);join.parm('resolveb').set(0);join.parm('detriangulate').set('none');join.parm('useabseamedges').set(1)
join.setDisplayFlag(True);join.setRenderFlag(True)
hou.hipFile.save(str(R/'Rainee-Local-VDB-Repair.hip'))
start=time.time();g=join.geometry();print('Local VDB/Boolean cook '+str(time.time()-start)+' s',flush=True)
g.saveToFile(str(R/'local-vdb-union.bgeo.sc'));g.saveToFile(str(R/'local-vdb-union.obj'))
v=np.array([p.position() for p in g.points()],dtype='<f4');f=[]
for p in g.prims():
 ids=[q.point().number() for q in p.vertices()]
 for j in range(1,len(ids)-1):f.append([ids[0],ids[j],ids[j+1]])
v.tofile(R/'local-vdb-positions.bin');np.array(f,dtype='<u4').tofile(R/'local-vdb-triangles.bin')
report={'houdini':hou.applicationVersionString(),'points':len(v),'triangles':len(f),'cook_seconds':time.time()-start,
 'nodes':{n.name():{'errors':list(n.errors()),'warnings':list(n.warnings())} for n in [sdf,sm,expand,convert,cut,outside,join]},
 'voxel_size':.0015,'repair_scope_center':[0.,.579,-.005],'repair_scope_radius':[.07,.077,.111]}
(R/'local-vdb-native-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
