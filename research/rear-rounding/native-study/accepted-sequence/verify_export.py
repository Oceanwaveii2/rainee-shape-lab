"""Read-only native geometry audit/export of the separately authored sequence.

Scene graph and parameters are never modified here. The sole time-context
change reads static native SOP outputs at requested frames. Raw float32
browser buffers have no equivalent in Houdini's geometry export_file tool.
"""
from pathlib import Path
import sys, json, time, hashlib
import hou
import numpy as np

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parent
HIP = STUDY / 'Rainee-Accepted-Growth-Sequence.hip'
BASE = STUDY / 'Rainee-Optional-Radial-Rounding.hip'
SOURCE_HEIGHT = 2.3951061964035034
EXPRESSION = '1 + 0.5*clamp(($F-1)/10,0,1) + 0.5*clamp(($F-11)/8,0,1) + 0.5*clamp(($F-19)/8,0,1)'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

baseline_hash = sha(BASE)
hou.hipFile.load(str(HIP), suppress_save_prompt=True)
geo = hou.node('/obj/RAINEE_OPTIONAL_ROUNDING')
ctrl = geo.node('CONTROLS')
assert ctrl.parm('volume').expression() == EXPRESSION
assert ctrl.evalParm('roundness') == .65
assert hou.fps() == 24
assert tuple(hou.playbar.frameRange()) == (1., 144.)
out = geo.node('OUT_BODY')
cageout = geo.node('CAGE_RADIAL_RELAXATION')
audit = geo.node('NATIVE_FIELD_AUDIT')
heightout = geo.node('OUT_FBX_SOURCE_STATURE')
target = geo.node('MATCHED_CAGE_TARGET')
neutral = np.array(geo.node('REPAIRED_NEUTRAL').geometry().pointFloatAttribValues('P'), dtype=np.float32).reshape(-1,3)
cagerest = np.array(geo.node('CAGE_REST').geometry().pointFloatAttribValues('P'), dtype=np.float32).reshape(-1,3)
bodyfaces = np.fromfile(STUDY/'body-triangles.bin', dtype='<u4').reshape(-1,3)
cagefaces = np.fromfile(STUDY/'cage-triangles.bin', dtype='<u4').reshape(-1,3)
assert len(neutral) == 121901 and len(bodyfaces) == 252337
assert len(cagerest) == 1506 and len(cagefaces) == 3008
roi = (neutral[:,1]>.48)&(neutral[:,1]<.77)&(neutral[:,2]<.015)&(np.abs(neutral[:,0])<.22)
sample_count = int(roi.sum())
assert sample_count == 39273
fixed = ~roi
epsilon = 1e-4

def read(n):
    n.cook(force=True)
    assert not n.errors(), (n.path(), n.errors())
    g = n.geometry()
    return np.array(g.pointFloatAttribValues('P'),dtype=np.float32).reshape(-1,3)

def volume(p):
    p = p.astype(np.float64)
    return abs(float(np.einsum('ij,ij->i',p[cagefaces[:,0]],np.cross(p[cagefaces[:,1]],p[cagefaces[:,2]])).sum()/6))

rest_volume = volume(cagerest)
rows = []
last_ratio = -float('inf')
final_body = final_cage = None
start = time.perf_counter()
for frame in list(range(27)) + [27,49,120]:
    hou.setFrame(frame + 1)
    begin = time.perf_counter()
    authored = float(ctrl.evalParm('volume'))
    p = read(out)
    cp = read(cageout)
    ap = read(audit).astype(np.float64)
    hp = read(heightout)
    assert len(p) == len(neutral) and len(cp) == len(cagerest)
    assert all(np.isfinite(a).all() for a in [p,cp,ap,hp])
    assert np.array_equal(p[fixed],neutral[fixed])
    assert np.ptp(p[:,1]) == np.ptp(neutral[:,1])
    source_height = float(np.ptp(hp[:,1]))
    assert abs(source_height - SOURCE_HEIGHT) < 2e-6
    values = ap.reshape(6,sample_count,3)
    jac = np.empty((sample_count,3,3))
    for axis in range(3):
        jac[:,:,axis] = (values[axis*2]-values[axis*2+1])/(2*epsilon)
    det = np.linalg.det(jac)
    assert np.all(det>0), (frame,float(det.min()),int((det<=0).sum()))
    actual = volume(cp)/rest_volume
    assert abs(actual-authored) < 2e-5, (frame,actual,authored)
    assert actual >= last_ratio-2e-6, (frame,actual,last_ratio)
    last_ratio = actual
    warnings = {n.name():list(n.warnings()) for n in geo.children() if n.warnings()}
    errors = {n.name():list(n.errors()) for n in geo.children() if n.errors()}
    assert not errors
    body_name = f'body-frame_{min(frame,26):04d}.bin'
    cage_name = f'cage-frame_{min(frame,26):04d}.bin'
    if frame <= 26:
        p.astype('<f4').tofile(ROOT/body_name)
        cp.astype('<f4').tofile(ROOT/cage_name)
    if frame == 0:
        assert np.array_equal(p,neutral)
        topology = np.array([[q.number() for q in prim.points()] for prim in out.geometry().prims()],dtype=np.uint32)
        assert np.array_equal(topology,bodyfaces)
    if frame == 26:
        final_body = p.copy(); final_cage = cp.copy()
    if frame > 26:
        assert np.array_equal(p,final_body) and np.array_equal(cp,final_cage)
        assert authored == 2.5
    row = {'source_frame':frame,'houdini_frame':frame+1,'time_seconds':frame/24,
        'authored_cage_ratio':authored,'actual_native_cage_ratio':actual,
        'body':body_name,'cage':cage_name,'finite':True,
        'native_roi_minimum_jacobian':float(det.min()),'native_roi_nonpositive_jacobians':int((det<=0).sum()),
        'source_stature_height':source_height,'height_error':source_height-SOURCE_HEIGHT,
        'normalized_height_drift':0.,'protected_region_displacement':0.,
        'native_geometry_seconds':time.perf_counter()-begin,'errors':errors,'warnings':warnings}
    rows.append(row)
    print(json.dumps({'source_frame':frame,'actual_cage_ratio':actual,'minJ':row['native_roi_minimum_jacobian'],'height_error':row['height_error']}),flush=True)

assert baseline_hash == sha(BASE)
report = {'native_passed':True,'houdini':hou.applicationVersionString(),'hip':str(HIP),'fps':24,
    'interpolation':'piecewise linear sum of clamped native HScript ramps; constant final hold',
    'expression':EXPRESSION,
    'authored_schedule':[{'stage':i+1,'source_frame':f,'houdini_frame':f+1,'initial_cage_ratio':v} for i,(f,v) in enumerate([(0,1.),(10,1.5),(18,2.),(26,2.5)])],
    'correct_source_frame_range':[0,26],'endpoint_source_frame':26,'rejected_geometry_source_frame_range':[27,None],
    'initialization_only':True,'image_measured_volumes':False,
    'source_height_units':SOURCE_HEIGHT,'body_points':len(neutral),'body_triangle_count':len(bodyfaces),
    'cage_points':len(cagerest),'cage_triangle_count':len(cagefaces),
    'native_roi_audit_points':sample_count,'audit_epsilon':epsilon,'roundness':.65,
    'sequence_file_rule':'source frame0..26 maps to exact same-topology native float32 buffers; later frames reuse frame0026',
    'hold_rule':{'source_frame_min':26,'source_frame_max':143,'cache_source_frame':26,'initial_cage_ratio':2.5},
    'body_triangles':'../body-triangles.bin','cage_triangles':'../cage-triangles.bin','dtype':'little-endian float32 xyz',
    'original_base_sha256':baseline_hash,'new_hip_sha256':sha(HIP),
    'elapsed_seconds':time.perf_counter()-start,'states':rows,
    'limits':'Native static SOP geometry; no Vellum resimulation, measured image-volume calibration, camera/pose fitting, continuous-domain Jacobian guarantee, or contact/self-intersection certification. Stage1..4 are ordinal. Numeric ratios1/1.5/2/2.5 are explicit initial authoring controls, not four-times inflation.'}
(ROOT/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(ROOT/'preview-manifest.json').write_text(json.dumps({k:v for k,v in report.items() if k not in ['elapsed_seconds']},indent=2),encoding='utf-8')
print(json.dumps({'native_passed':True,'checked_states':len(rows),'exported_frames':27,'minJ':min(r['native_roi_minimum_jacobian'] for r in rows),'elapsed_seconds':report['elapsed_seconds']}),flush=True)
