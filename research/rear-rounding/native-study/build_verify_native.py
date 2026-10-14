"""Bounded native Houdini22 optional static study; no production mutations.

Node search: SOP deform lists lattice/pointdeform/posespacedeform/surfacedeform
etc. Those native transfer nodes do not express this custom analytic per-point
ellipsoid flow or its exact measured cage calibration. Attribute Wrangle is
used only for the already-authored attribute math; no geometry is made in VEX.
"""
from pathlib import Path
import hou,numpy as np,json,time,shutil,hashlib,sys

ROOT=Path(__file__).resolve().parent
RESEARCH=ROOT.parent
APP=ROOT.parents[2]
REPAIR=APP/'houdini/pelvic-repair'
manifest=json.loads((REPAIR/'final-repair-manifest.json').read_text())
for src,name in [(APP/'houdini/rear_model.py','rear_model.py'),(RESEARCH/'rear_rounding_flow.py','rear_rounding_flow.py')]:
    text=src.read_text()
    if name=='rear_rounding_flow.py':
        text=text.replace("sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'houdini'))","sys.path.insert(0,str(Path(__file__).resolve().parent))")
    (ROOT/name).write_text(text)
sys.path.insert(0,str(ROOT))
from rear_model import DEFAULTS,volume
from rear_rounding_flow import round_lobes,calibrate_rounding

body=np.fromfile(REPAIR/manifest['positions'],dtype='<f4').reshape(-1,3)
body_faces=np.fromfile(REPAIR/manifest['triangles'],dtype='<u4').reshape(-1,3)
cage=np.fromfile(APP/'houdini/cage-rest.bin',dtype='<f4').reshape(-1,3)
cage_faces=np.fromfile(APP/'houdini/cage-triangles.bin',dtype='<u4').reshape(-1,3)
sourcegeo=hou.Geometry();sourcegeo.loadFromFile(str(REPAIR/manifest['bgeo']))
assert np.array_equal(np.array(sourcegeo.pointFloatAttribValues('P'),dtype=np.float32).reshape(-1,3),body)
assert len(sourcegeo.prims())==len(body_faces)
sourcegeo.saveToFile(str(ROOT/'repaired-neutral.bgeo.sc'))

def point_file(path,positions,faces=None):
    g=hou.Geometry();points=g.createPoints(positions.tolist())
    if faces is not None:
        for face in faces:
            poly=g.createPolygon()
            for i in face:poly.addVertex(points[int(i)])
    g.saveToFile(str(path))
point_file(ROOT/'cage-rest.bgeo.sc',cage,cage_faces)
# Audit the actual repaired rear ROI at every point, including new repair points.
roi=(body[:,1]>.48)&(body[:,1]<.77)&(body[:,2]<.015)&(np.abs(body[:,0])<.22)
samples=body[roi].astype(float);epsilon=1e-4;perturbed=[]
for axis in range(3):
    offset=np.zeros_like(samples);offset[:,axis]=epsilon
    perturbed.extend([samples+offset,samples-offset])
point_file(ROOT/'audit-samples.bgeo.sc',np.concatenate(perturbed))

hou.hipFile.clear(suppress_save_prompt=True)
geo=hou.node('/obj').createNode('geo','RAINEE_OPTIONAL_ROUNDING')
for old in geo.children():old.destroy()
ctrl=geo.createNode('null','CONTROLS');ptg=ctrl.parmTemplateGroup()
for name,label,value,lo,hi in [('volume','Closed rear cage ratio',1.,1.,2.5),('roundness','Radial relaxation strength',.65,0.,.65)]:
    ptg.append(hou.FloatParmTemplate(name,label,1,default_value=(value,),min=lo,max=hi,min_is_strict=True,max_is_strict=True))
for name,value in DEFAULTS.items():
    t=hou.FloatParmTemplate(name,name.replace('_',' ').title(),1,default_value=(value,));t.hide(True);ptg.append(t)
ctrl.setParmTemplateGroup(ptg)
ctrl.setComment('Optional native static study. Fixed approved shape controls; volume1..2.5, radialrelaxation0..0.65. No dynamics/contact certification. Baseline is the locally repaired body, not flawed FBX anatomy.')

def file_node(name,path):
    n=geo.createNode('file',name);n.parm('file').set('$HIP/'+path);return n
body_source=file_node('REPAIRED_NEUTRAL','repaired-neutral.bgeo.sc')
cage_source=file_node('CAGE_REST','cage-rest.bgeo.sc')
audit_source=file_node('AUDIT_POINTS','audit-samples.bgeo.sc')
target=geo.createNode('python','MATCHED_CAGE_TARGET');target.setInput(0,cage_source)
target_code='''import hou,numpy as np,sys
sys.path.insert(0,hou.expandString('$HIP'))
from rear_rounding_flow import calibrate_rounding
from rear_model import DEFAULTS,volume
node=hou.pwd();g=node.geometry();c=node.parent().node('CONTROLS')
v=np.array(g.pointFloatAttribValues('P')).reshape(-1,3)
f=np.array([[p.number() for p in poly.points()] for poly in g.prims()])
controls={name:c.evalParm(name) for name in DEFAULTS}
amp,p=calibrate_rounding(v,f,c.evalParm('volume'),c.evalParm('roundness'),controls)
g.setPointFloatAttribValues('P',p.flatten().tolist())
for name,value in [('inflation_amplitude',amp),('volume_ratio',volume(p,f)/volume(v,f))]:
 if g.findGlobalAttrib(name) is None:g.addAttrib(hou.attribType.Global,name,0.)
 g.setGlobalAttribValue(name,float(value))
'''
target.parm('python').set(target_code)
vfl=(RESEARCH/'round_lobes_flow.vfl').read_text().replace('amp=detail(1,"inflation_amplitude",0),roundness=.65','amp=detail(1,"inflation_amplitude",0),roundness=ch("../CONTROLS/roundness")')
(ROOT/'round_lobes_flow.vfl').write_text(vfl)
def wrangle(name,source):
    n=geo.createNode('attribwrangle',name);n.setInput(0,source);n.setInput(1,target);n.parm('snippet').set(vfl);return n
body_flow=wrangle('BODY_RADIAL_RELAXATION',body_source)
cage_flow=wrangle('CAGE_RADIAL_RELAXATION',cage_source)
audit_flow=wrangle('NATIVE_FIELD_AUDIT',audit_source)
normals=geo.createNode('normal','NORMALS');normals.setInput(0,body_flow)
out=geo.createNode('null','OUT_BODY');out.setInput(0,normals);out.setDisplayFlag(True);out.setRenderFlag(True)
for n in [ctrl,body_source,cage_source,audit_source,target,body_flow,cage_flow,audit_flow,normals]:
    n.setDisplayFlag(False)
# Position only newly-created nodes; existing production scenes are not touched.
for n,pos in [(ctrl,(0,4)),(body_source,(-3,3)),(cage_source,(0,3)),(audit_source,(3,3)),(target,(0,1)),(body_flow,(-3,0)),(cage_flow,(0,0)),(audit_flow,(3,0)),(normals,(-3,-1)),(out,(-3,-2))]:
    n.setPosition(hou.Vector2(pos))
hip=ROOT/'Rainee-Optional-Radial-Rounding.hip'
hou.hipFile.save(str(hip))

def positions(n):
    n.cook(force=True)
    assert not n.errors(),(n.path(),n.errors())
    return np.array(n.geometry().pointFloatAttribValues('P'),dtype=np.float32).reshape(-1,3)

fixed=(body[:,1]>=.77)|(body[:,1]<=.48)|(body[:,2]>=.015)|(np.abs(body[:,0])>=.22)
report={'houdini':hou.applicationVersionString(),'hip':str(hip),'source_manifest':str(REPAIR/'final-repair-manifest.json'),
        'source_bgeo_sha256':hashlib.sha256((REPAIR/manifest['bgeo']).read_bytes()).hexdigest(),
        'body_points':len(body),'body_triangles':len(body_faces),'cage_points':len(cage),'cage_triangles':len(cage_faces),
        'roundness':.65,'shape_controls':DEFAULTS,'audit_repaired_roi_points':len(samples),'audit_epsilon':epsilon,
        'source_height_normalized':float(np.ptp(body[:,1])),
        'limits':'Four static native cooks. No dynamics, measured tissuevolume, or trianglecontact/selfintersection certification. Finite-differenceJacobian screen covers all repaired-source points in rearROI, not the continuous domain.',
        'states':[]}
for ratio in [1.,1.5,2.,2.5]:
    c=ctrl.parm('volume');c.set(ratio)
    started=time.perf_counter();p=positions(out);body_seconds=time.perf_counter()-started
    cp=positions(cage_flow);ap=positions(audit_flow).astype(float)
    assert np.isfinite(p).all() and np.isfinite(cp).all() and np.isfinite(ap).all()
    amp=target.geometry().attribValue('inflation_amplitude')
    expected=round_lobes(body.astype(float),amp,.65)
    expected_cage=round_lobes(cage.astype(float),amp,.65)
    body_error=float(abs(p.astype(float)-expected).max());cage_error=float(abs(cp.astype(float)-expected_cage).max())
    assert body_error<2e-6,(ratio,body_error)
    assert cage_error<2e-6,(ratio,cage_error)
    assert np.array_equal(p[fixed],body[fixed])
    assert np.ptp(p[:,1])==np.ptp(body[:,1])
    if ratio==1:assert np.array_equal(p,body)
    values=ap.reshape(6,len(samples),3)
    jac=np.empty((len(samples),3,3))
    for axis in range(3):jac[:,:,axis]=(values[axis*2]-values[axis*2+1])/(2*epsilon)
    det=np.linalg.det(jac);assert np.all(det>0),(ratio,float(det.min()),int((det<=0).sum()))
    actual=float(volume(cp,cage_faces)/volume(cage,cage_faces));assert abs(actual-ratio)<2e-5,(ratio,actual)
    assert np.all(p[body[:,0]>0,0]>0) and np.all(p[body[:,0]<0,0]<0)
    body_file=f'body-native-flow-{ratio:g}x.bin';cage_file=f'cage-native-flow-{ratio:g}x.bin'
    p.astype('<f4').tofile(ROOT/body_file);cp.astype('<f4').tofile(ROOT/cage_file)
    out.geometry().saveToFile(str(ROOT/f'body-native-flow-{ratio:g}x.bgeo.sc'))
    cage_flow.geometry().saveToFile(str(ROOT/f'cage-native-flow-{ratio:g}x.bgeo.sc'))
    state={'ratio':ratio,'amplitude':amp,'body':body_file,'cage':cage_file,'actual_native_cage_ratio':actual,
           'max_native_numpy_body_error':body_error,'max_native_numpy_cage_error':cage_error,
           'native_roi_minimum_jacobian':float(det.min()),'native_roi_negative_jacobians':int((det<=0).sum()),
           'height_drift':0.,'fixed_region_displacement':0.,'finite':True,'native_body_cook_seconds':body_seconds,
           'warnings':{n.name():list(n.warnings()) for n in [target,body_flow,cage_flow,audit_flow,normals] if n.warnings()}}
    report['states'].append(state);print(json.dumps(state),flush=True)
ctrl.parm('volume').set(1.);positions(out);hou.hipFile.save(str(hip))
report['native_passed']=True
(ROOT/'verification-native-flow.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'native_passed':True,'states':len(report['states']),'roi_points':len(samples),'hip':str(hip)}),flush=True)
