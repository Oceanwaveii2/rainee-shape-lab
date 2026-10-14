from pathlib import Path
import numpy as np,json,hashlib
from apply_repair import apply,load_recipe
from pelvic_repair import edge_counts
R=Path(__file__).resolve().parent;A=R.parents[1]/'assets'
base=np.fromfile(A/'positions.bin','<f4').reshape(-1,3);bf=np.fromfile(A/'triangles.bin','<u4').reshape(-1,3)
v=np.fromfile(R/'implicit-repaired-positions.bin','<f4').reshape(-1,3);f=np.fromfile(R/'implicit-repaired-triangles.bin','<u4').reshape(-1,3)
report=json.loads((R/'implicit-repair-report.json').read_text())
lo=np.array(report['strict_local_composition_box']['min']);hi=np.array(report['strict_local_composition_box']['max'])
def touches(v,f):
 q=v[f];c=q.mean(1);return ((q>=lo)&(q<=hi)).all(2).any(1)|((c>=lo)&(c<=hi)).all(1)
outside_source=bf[~touches(base,bf)];outside_output=f[~touches(v,f)]
# Preserve literal oriented triangle records, not merely nearest positions.
key=lambda arr:set(map(tuple,arr.tolist()))
outside_identical=key(outside_source)==key(outside_output)
assert outside_identical
e,c=edge_counts(f);mid=v[e].mean(1)
core=(abs(mid[:,0])<.030)&(mid[:,1]>.539)&(mid[:,1]<.613)&(mid[:,2]>-.063)&(mid[:,2]<.07)
assert not ((c!=2)&core).any()
assert np.array_equal(v[:len(base)],base)
assert np.ptp(v[:,1])==np.ptp(base[:,1])
r=load_recipe();bv,ff=apply(base,r);assert np.array_equal(v,bv);assert np.array_equal(f,ff)
states=[]
for name in ['body-v3-1x.bin','body-v3-1.5x.bin','body-v3-2x.bin','body-rear-2-thigh-065.bin']:
 p=R.parent/name
 if not p.exists():continue
 s=np.fromfile(p,'<f4').reshape(-1,3);ov,_=apply(s,r)
 area=np.linalg.norm(np.cross(ov[f[:,1]]-ov[f[:,0]],ov[f[:,2]]-ov[f[:,0]]),axis=1)/2
 corefaces=np.all((abs(v[f][:,:,0])<.03)&(v[f][:,:,1]>.539)&(v[f][:,:,1]<.613)&(v[f][:,:,2]>-.063)&(v[f][:,:,2]<.07),axis=1)
 entry={'state':name,'finite':bool(np.isfinite(ov).all()),'height_drift_from_state':float(np.ptp(ov[:,1])-np.ptp(s[:,1])),
 'all_original_state_points_retained_exactly':bool(np.array_equal(ov[:len(s)],s)),
 'core_zero_area_faces':int((area[corefaces]<1e-12).sum())}
 assert entry['finite'] and entry['height_drift_from_state']==0 and entry['all_original_state_points_retained_exactly']
 states.append(entry)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={'outside_source_triangles_verbatim':outside_identical,'outside_source_triangle_count':len(outside_source),
 'baseline_application_identity':True,'rendered_height_drift':report['height_rendered_surface_drift'],
 'core_edges':int(core.sum()),'core_edges_all_two_faces':True,'deformed_states':states,
 'source_hashes':{'positions.bin':sha(A/'positions.bin'),'triangles.bin':sha(A/'triangles.bin')},
 'final_hashes':{'positions':sha(R/'implicit-repaired-positions.bin'),'triangles':sha(R/'implicit-repaired-triangles.bin')},
 'pass':True,'limits':'Verifies structural core and protected distant records; does not prove self-contact, production watertight topology, or final artistic fidelity.'}
(R/'final-repair-verification.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
