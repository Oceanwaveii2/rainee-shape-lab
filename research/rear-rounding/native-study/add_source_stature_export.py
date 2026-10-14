"""Add export-only source-stature branch; two bounded native checks only."""
from pathlib import Path
import hou,numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parent
APP=ROOT.parents[2]
hip=ROOT/'Rainee-Optional-Radial-Rounding.hip'
cache_paths=sorted(ROOT.glob('body-native-flow-*.bin'))+sorted(ROOT.glob('cage-native-flow-*.bin'))
cache_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in cache_paths}
hou.hipFile.load(str(hip),suppress_save_prompt=True)
g=hou.node('/obj/RAINEE_OPTIONAL_ROUNDING');ctrl=g.node('CONTROLS');original_ratio=ctrl.evalParm('volume')
old_display=[n for n in g.children() if n.isDisplayFlagSet()]
old_render=[n for n in g.children() if n.isRenderFlagSet()]
before_input=g.node('BODY_RADIAL_RELAXATION').input(0).path()
before_vfl=g.node('BODY_RADIAL_RELAXATION').evalParm('snippet')
source=np.fromfile(ROOT/'body-native-flow-1x.bin',dtype='<f4').reshape(-1,3)
faces=np.fromfile(ROOT/'body-triangles.bin',dtype='<u4').reshape(-1,3);used=np.unique(faces)
info=json.loads((APP/'assets/mesh-info.json').read_text())
lo=np.array(info['source_bounds']['min']);hi=np.array(info['source_bounds']['max']);center=(lo+hi)/2
visible_min=float(source[used,1].min());visible_height=float(np.ptp(source[used,1]));height=float(hi[1]-lo[1]);scale=height/visible_height
remap=np.full(len(source),-1,dtype=np.int64);remap[used]=np.arange(len(used))
remap[faces].astype('<u4').tofile(ROOT/'source-stature-triangles.bin')
clean=g.node('REMOVE_UNUSED_EXPORT_POINTS') or g.createNode('clean','REMOVE_UNUSED_EXPORT_POINTS')
clean.setInput(0,g.node('OUT_BODY'))
# Dedicated Clean SOP: ONLY remove unreferenced points. Preserve polygons/attrs.
for parm in ['fusepts','deldegengeo','removeunusedgrp','orientpoly','reversewinding','fixoverlap','deleteoverlap','dodelattribs','dodelgroups','delnans','make_manifold','delete_small']:
    clean.parm(parm).set(0)
clean.parm('delunusedpts').set(1)
clean.setComment('Export branch only: remove unreferenced points before measuring/restoring visible source stature. Internal normalized flow and caches are unchanged.')
exact=g.node('OUT_FBX_SOURCE_STATURE') or g.createNode('xform','OUT_FBX_SOURCE_STATURE')
exact.setInput(0,clean);exact.parm('scale').set(scale)
translation=(float(center[0]),float(lo[1]-visible_min*scale),float(center[2]));exact.parmTuple('t').set(translation)
exact.setComment('Uniformly restores the referenced repaired/rounded surface to the original FBX coordinate height and origin. The stored FBX unit metadata does not establish credible real-world centimeters. Export only; solver coordinates remain normalized.')
for n in [clean,exact]:n.setDisplayFlag(False);n.setRenderFlag(False)
for n in old_display:n.setDisplayFlag(True)
for n in old_render:n.setRenderFlag(True)
clean.setPosition(hou.Vector2(-1,-3));exact.setPosition(hou.Vector2(-1,-4))
report={'hip':str(hip),'branch':exact.path(),'upstream_normalized':g.node('OUT_BODY').path(),
        'source_height_native_units':height,'proxy_referenced_height_normalized':visible_height,'proxy_referenced_y_min':visible_min,
        'uniform_export_scale':scale,'export_translation':translation,'source_points':len(source),'referenced_points':len(used),
        'compacted_triangle_buffer':'source-stature-triangles.bin',
        'limits':'Uniform export correction, not anatomical changes or physical unit calibration. Existing flow/cage calibration and normalized caches are preserved. Two export states only.',
        'states':[]}
for ratio in [1.,2.5]:
    ctrl.parm('volume').set(ratio)
    internal=g.node('OUT_BODY');internal.cook(force=True);assert not internal.errors(),internal.errors()
    internal_p=np.array(internal.geometry().pointFloatAttribValues('P'),dtype=np.float32).reshape(-1,3)
    cached=np.fromfile(ROOT/f'body-native-flow-{ratio:g}x.bin',dtype='<f4').reshape(-1,3)
    # Exact equality proves the new branch did not alter the verified flow.
    assert np.array_equal(internal_p,cached),(ratio,float(abs(internal_p-cached).max()))
    exact.cook(force=True);assert not exact.errors(),exact.errors()
    eg=exact.geometry();p=np.array(eg.pointFloatAttribValues('P'),dtype=np.float32).reshape(-1,3)
    assert np.isfinite(p).all();assert len(eg.prims())==len(faces);assert len(p)==len(used)
    expected=internal_p[used].astype(float)*scale+np.array(translation)
    assert np.max(abs(p-expected))<1e-6,'Compacted export point order changed'
    actual_height=float(np.ptp(p[:,1]));error=actual_height-height
    assert abs(error)<1e-6,(ratio,actual_height,height)
    assert abs(float(p[:,1].min())-lo[1])<1e-6
    assert abs(float(p[:,1].max())-hi[1])<1e-6
    bgeo=f'body-source-stature-{ratio:g}x.bgeo.sc';obj=f'Rainee-source-stature-{ratio:g}x.obj';binary=f'body-source-stature-{ratio:g}x.bin'
    eg.saveToFile(str(ROOT/bgeo));eg.saveToFile(str(ROOT/obj));p.astype('<f4').tofile(ROOT/binary)
    state={'ratio':ratio,'points':len(p),'primitives':len(eg.prims()),'referenced_export_height':actual_height,
           'height_error':error,'y_min':float(p[:,1].min()),'y_max':float(p[:,1].max()),
           'internal_positions_exactly_match_verified_cache':True,'bgeo':bgeo,'obj':obj,'positions':binary}
    report['states'].append(state);print(json.dumps(state),flush=True)
ctrl.parm('volume').set(original_ratio)
assert g.node('BODY_RADIAL_RELAXATION').input(0).path()==before_input
assert g.node('BODY_RADIAL_RELAXATION').evalParm('snippet')==before_vfl
assert {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in cache_paths}==cache_hashes
report['flow_inputs_vfl_settings_caches_preserved']=True;report['native_export_passed']=True
hou.hipFile.save(str(hip))
(ROOT/'verification-source-stature.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'native_export_passed':True,'source_height':height,'scale':scale,'export_branch':exact.path()}),flush=True)
