"""Bake the final source-compatible buffers, with no edits to the main scene."""
from pathlib import Path
import hou,numpy as np,json
R=Path(__file__).resolve().parent
v=np.fromfile(R/'implicit-repaired-positions.bin','<f4').reshape(-1,3);f=np.fromfile(R/'implicit-repaired-triangles.bin','<u4').reshape(-1,3)
g=hou.Geometry();pts=g.createPoints(v.tolist());sid=g.addAttrib(hou.attribType.Point,'source_id',-1)
group=g.createPointGroup('structural_repair')
for i,p in enumerate(pts):
 if i<98078:p.setAttribValue(sid,i)
 else:group.add(p)
for tri in f:
 p=g.createPolygon()
 for i in tri:p.addVertex(pts[int(i)])
g.saveToFile(str(R/'body-local-implicit-repair.bgeo.sc'))
o=hou.node('/obj').createNode('geo','RAINEE_FINAL_LOCAL_REPAIR')
src=o.createNode('file','LOCAL_IMPLICIT_REPAIR');src.parm('file').set('$HIP/body-local-implicit-repair.bgeo.sc')
normal=o.createNode('normal','NORMALS');normal.setInput(0,src);normal.setDisplayFlag(True);normal.setRenderFlag(True)
hou.hipFile.save(str(R/'Rainee-Final-Local-Repair.hip'))
manifest={'positions':'implicit-repaired-positions.bin','triangles':'implicit-repaired-triangles.bin',
 'bgeo':'body-local-implicit-repair.bgeo.sc','report':'implicit-repair-report.json','verification':'final-repair-verification.json',
 'recipe':'implicit-repair-recipe.npz','application':'apply_repair.py','source_point_count':98078,
 'native_study':'Rainee-Local-VDB-Repair.hip','baked_study':'Rainee-Final-Local-Repair.hip',
 'obj':'Rainee-local-implicit-repair.obj','preview_front':'implicit-repaired-front.png','preview_back':'implicit-repaired-back.png',
 'status':'Local core structurally repaired; collar and inherited source topology require further cleanup'}
(R/'final-repair-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2),flush=True)
