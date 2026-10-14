from pathlib import Path
import hou,numpy as np,json
R=Path(__file__).resolve().parent
v=np.fromfile(R/'repaired-positions.bin','<f4').reshape(-1,3);f=np.fromfile(R/'repaired-triangles.bin','<u4').reshape(-1,3)
g=hou.Geometry();pts=g.createPoints(v.tolist());sid=g.addAttrib(hou.attribType.Point,'source_id',-1)
group=g.createPointGroup('structural_repair')
for i,p in enumerate(pts):
 if i<98078:p.setAttribValue(sid,i)
 else:group.add(p)
for tri in f:
 p=g.createPolygon()
 for i in tri:p.addVertex(pts[int(i)])
g.saveToFile(str(R/'body-pelvic-repair.bgeo.sc'))
obj=hou.node('/obj').createNode('geo','RAINEE_REPAIR_STUDY')
file=obj.createNode('file','EXACT_SOURCE_WITH_SEWN_BRIDGE');file.parm('file').set('$HIP/body-pelvic-repair.bgeo.sc')
normal=obj.createNode('normal','NORMALS');normal.setInput(0,file);normal.setDisplayFlag(True);normal.setRenderFlag(True)
hou.hipFile.save(str(R/'Rainee-Pelvic-Repair-Study.hip'))
card={}
for typ in ['vdbfrompolygons','convertvdb']:
 n=obj.createNode(typ,'PROBE_'+typ)
 card[typ]=[{'name':p.name(),'label':p.parmTemplate().label(),'value':p.eval(),'tokens':p.menuItems() if p.parmTemplate().type()==hou.parmTemplateType.Menu else None} for p in n.parms()]
(R/'vdb-node-cards.json').write_text(json.dumps(card,indent=2))
print('Saved native repaired mesh and standalone study; '+str(len(pts))+' points',flush=True)
