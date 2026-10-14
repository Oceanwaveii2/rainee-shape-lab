import hou,numpy as np,importlib.util,pathlib
node=hou.pwd();g=node.geometry();root=pathlib.Path(hou.expandString('$HIP'))
spec=importlib.util.spec_from_file_location('rainee_rear_model',root/'rear_model.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
ctrl=node.parent().node('CONTROLS');v=np.array(g.pointFloatAttribValues('P')).reshape(-1,3);faces=np.array([[p.number() for p in f.points()] for f in g.prims()])
controls={k:ctrl.evalParm(k) for k in model.DEFAULTS};ratio=ctrl.evalParm('volume')
try:amp,out=model.calibrate(v,faces,ratio,controls)
except ValueError as e:raise hou.NodeError(str(e))
body_node=node.parent().node('REPAIRED_BODY') or node.parent().node('FBX_DERIVED_BODY')
body=np.array(body_node.geometry().pointFloatAttribValues('P')).reshape(-1,3)
screen=model.jacobian_screen(body,amp,controls)
if screen['nonpositive'] or screen['min_determinant']<.025:
 raise hou.NodeError('Rear shape folds or nearly collapses the body deformation field. Reduce volume or redistribute radial height/width. This candidate is not accepted.')
g.setPointFloatAttribValues('P',out.flatten().tolist());original=model.volume(v,faces);actual=model.volume(out,faces)
for name,value in [('inflation_amplitude',amp),('cage_volume',actual),('baseline_cage_volume',original),('volume_ratio',actual/original),('minimum_sampled_jacobian',screen['min_determinant'])]:
 if g.findGlobalAttrib(name) is None:g.addAttrib(hou.attribType.Global,name,0.)
 g.setGlobalAttribValue(name,float(value))
grp=g.createPointGroup('attachment')
mask=model.region(v)
for i,p in enumerate(g.points()):
 if mask[i]<.001:grp.add(p)
