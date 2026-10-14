"""Build a native Houdini study from the existing FBX-derived proxy.
Run with Houdini 22 hython. Original FBX is never modified or imported in full.
"""
import hou, numpy as np, pathlib, json, math
from thigh_setup import install as install_thighs
ROOT=pathlib.Path(__file__).resolve().parent
APP=ROOT.parent
hou.hipFile.clear(suppress_save_prompt=True)
hou.setFps(24);hou.playbar.setFrameRange(1,96);hou.playbar.setPlaybackRange(1,96)
def mesh_file(path,verts,faces):
 g=hou.Geometry();pts=g.createPoints(verts.tolist())
 for f in faces:
  poly=g.createPolygon()
  for i in f:poly.addVertex(pts[int(i)])
 g.saveToFile(str(path))
 return g
base=np.fromfile(APP/'assets/positions.bin',dtype='<f4').reshape(-1,3)
faces=np.fromfile(APP/'assets/triangles.bin',dtype='<u4').reshape(-1,3)
mesh_file(ROOT/'body_proxy.bgeo.sc',base,faces)
# A single closed two-lobed control surface, not two disconnected balloons.
verts=[[-.161,.61,-.043]];tri=[];nr=48;ns=32
for j in range(1,nr):
 x=-.161+.322*j/nr
 radius=math.sqrt(max(0,1-((abs(x)-.073)/.088)**2))
 for k in range(ns):
  a=2*math.pi*k/ns;verts.append([x,.61+.078*radius*math.sin(a),-.043+.089*radius*math.cos(a)])
verts.append([.161,.61,-.043]);last=len(verts)-1
for k in range(ns):tri.append([0,1+(k+1)%ns,1+k])
for j in range(nr-2):
 for k in range(ns):
  a=1+j*ns+k;b=1+j*ns+(k+1)%ns;c=a+ns;d=b+ns
  tri.extend([[a,b,c],[b,d,c]])
for k in range(ns):tri.append([last,1+(nr-2)*ns+k,1+(nr-2)*ns+(k+1)%ns])
cv=np.array(verts);ct=np.array(tri)
signed=np.einsum('ij,ij->i',cv[ct[:,0]],np.cross(cv[ct[:,1]],cv[ct[:,2]])).sum()/6
if signed<0:ct=ct[:,::-1]
mesh_file(ROOT/'closed_volume_cage.bgeo.sc',cv,ct)
geo=hou.node('/obj').createNode('geo','RAINEE');geo.setColor(hou.Color((.56,.36,.66)))
ctrl=geo.createNode('null','CONTROLS')
ptg=ctrl.parmTemplateGroup()
for name,label,default,lo,hi in [('volume','Rear volume / baseline',1.,.65,3.),('lateral','Lateral expansion share',.45,0,1),('vertical','Vertical expansion share',.30,0,1),('projection','Rear projection share',1.,.1,2),('motion','Secondary motion strength',1.,0,1)]:
 ptg.append(hou.FloatParmTemplate(name,label,1,default_value=(default,),min=lo,max=hi,min_is_strict=True,max_is_strict=True))
ptg.append(hou.ToggleParmTemplate('simulation','Use Vellum secondary motion',default_value=False))
ctrl.setParmTemplateGroup(ptg)
ctrl.setComment('FBX height and front pelvis remain fixed. Volume is measured on a separate closed cage, not on the open render proxy. Disable simulation for direct shape editing. Frame 1 = canonical template; frames 25-72 = inflation study.');ctrl.setGenericFlag(hou.nodeFlag.DisplayComment,True)
for frame,value in [(1,1),(24,1),(72,2),(96,2)]:
 key=hou.Keyframe();key.setFrame(frame);key.setValue(value);key.setExpression('linear()',hou.exprLanguage.Hscript);ctrl.parm('volume').setKeyframe(key)
body=geo.createNode('file','FBX_DERIVED_BODY');body.parm('file').set('$HIP/body_proxy.bgeo.sc')
cage=geo.createNode('file','CLOSED_REAR_CAGE');cage.parm('file').set('$HIP/closed_volume_cage.bgeo.sc')
target=geo.createNode('python','VOLUME_CALIBRATED_TARGET');target.setInput(0,cage)
target.parm('python').set((ROOT/'target_cage.py').read_text())
rest=geo.createNode('timeshift','REST_CAGE_FRAME_1');rest.setInput(0,target);rest.parm('frame').deleteAllKeyframes();rest.parm('frame').set(1)
shape=geo.createNode('attribwrangle','AUTHORED_INFLATION');shape.setInput(0,body);shape.setInput(1,target)
shape.parm('snippet').set((ROOT/'inflate.vfl').read_text())
cloth=geo.createNode('vellumconstraints','SKIN_STRETCH_AND_BEND');cloth.setInput(0,rest)
cloth.parm('constrainttype').set('cloth');cloth.parm('stretchstiffness').set(1);cloth.parm('stretchstiffnessexp').set(4);cloth.parm('bendstiffness').set(1);cloth.parm('bendstiffnessexp').set(-2);cloth.parm('pingroup').set('attachment');cloth.parm('pintype').set('hard');cloth.parm('stretchdampingratio').set(.03)
pressure=geo.createNode('vellumconstraints','ONE_SHARED_VOLUME');pressure.setInput(0,cloth,0);pressure.setInput(1,cloth,1);pressure.parm('constrainttype').set('pressure');pressure.parm('stretchstiffnessexp').set(6)
solver=geo.createNode('vellumsolver','SOFT_MOTION');solver.setInput(0,pressure,0);solver.setInput(1,pressure,1);solver.parm('substeps').set(3);solver.parm('niter').set(40);solver.parmTuple('gravity').set((0,0,0));solver.parm('targetmethod').set('soppath');solver.parm('targetpath').set(target.path());solver.parm('veldamping').set(.12)
solver.allowEditingOfContents()
forces=solver.node('dopnet1/forces');restblend=forces.createNode('vellumrestblend','FOLLOW_AUTHORED_REST_SHAPE');restblend.parm('updatemode').set('persubstep');restblend.parm('restsource').set('sop');restblend.parm('restsop').set(target.path());restblend.parm('blend').set(1);restblend.parm('usetimestep').set(1);forces.node('FORCE').setInput(0,restblend);forces.layoutChildren()
deform=geo.createNode('pointdeform','CAGE_SECONDARY_MOTION');deform.setInput(0,shape);deform.setInput(1,target);deform.setInput(2,solver);deform.parm('radius').set(.055)
blend=geo.createNode('attribwrangle','PROTECT_CANONICAL_BODY');blend.setInput(0,deform);blend.setInput(1,shape)
blend.parm('snippet').set('vector authored=point(1,"P",@ptnum); float mask=point(1,"rainee_mask",@ptnum); @P=lerp(authored,@P,mask*ch("../CONTROLS/motion"));')
switch=geo.createNode('switch','DIRECT_OR_SIMULATED');switch.setInput(0,shape);switch.setInput(1,blend);switch.parm('input').setExpression('ch("../CONTROLS/simulation")')
normal=geo.createNode('normal','SURFACE_NORMALS');normal.setInput(0,switch)
out=geo.createNode('null','OUT_NORMALIZED');out.setInput(0,normal);out.setDisplayFlag(True);out.setRenderFlag(True)
info=json.loads((APP/'assets/mesh-info.json').read_text());lo=np.array(info['source_bounds']['min']);hi=np.array(info['source_bounds']['max']);h=hi[1]-lo[1];center=(hi+lo)/2
native=geo.createNode('xform','OUT_FBX_COORDINATES');native.setInput(0,out);native.parm('scale').set(float(h));native.parmTuple('t').set((float(center[0]),float(lo[1]),float(center[2])))
native.setComment('Restores the FBX original coordinate bounds. No invented cm height. Normalized branch is only an internal solver coordinate system.');native.setGenericFlag(hou.nodeFlag.DisplayComment,True)
install_thighs(geo,ROOT)
geo.layoutChildren();hou.setFrame(1)
hou.hipFile.save(str(ROOT/'Rainee-Volume-Lab-v2.hip'))
g=out.geometry();g.saveToFile(str(ROOT/'baseline.obj'))
report={'houdini':hou.applicationVersionString(),'hip':str(ROOT/'Rainee-Volume-Lab-v2.hip'),'body_points':len(g.points()),'body_primitives':len(g.prims()),'cage_points':len(cv),'cage_triangles':len(ct),'source_height_native_units':float(h),'simulation_default':False,'thigh_default':0,'status':'Built; run native volume verification and verify_thighs.py for this rebuild'}
(ROOT/'build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)

