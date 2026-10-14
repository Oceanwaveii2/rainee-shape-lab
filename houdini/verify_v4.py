"""Actual native cooks of repaired anatomy plus separate rear/thigh controls."""
import hou,numpy as np,pathlib,json
from rear_model import region
r=pathlib.Path(__file__).resolve().parent;patch=r/'pelvic-repair'
manifest=json.loads((patch/'final-repair-manifest.json').read_text());faces=np.fromfile(patch/manifest['triangles'],'<u4').reshape(-1,3);used=np.unique(faces)
hou.hipFile.load(str(r/'Rainee-Volume-Lab-v4.hip'),suppress_save_prompt=True)
g=hou.node('/obj/RAINEE');c=g.node('CONTROLS');c.parm('volume').deleteAllKeyframes();c.parm('simulation').set(False);hou.setFrame(1)
def positions(n):
 geo=n.geometry()
 if geo is None:raise RuntimeError(n.path()+': '+str(n.errors()))
 return np.array(geo.pointFloatAttribValues('P'),dtype='<f4').reshape(-1,3)
base=positions(g.node('REPAIRED_BODY'));bins=np.fromfile(patch/manifest['positions'],'<f4').reshape(-1,3);assert np.array_equal(base,bins)
assert len(used)>0 and int(faces.max())<len(base)
report={'scene':'Rainee-Volume-Lab-v4.hip','static':[],'point_height_normalized':float(np.ptp(base[:,1])),'rendered_height_normalized':float(np.ptp(base[used,1])),'rendered_vertex_count':len(used),'limits':'Local repaired core; inherited body/collar topology defects remain. Field check is sampled, not a contact certification. Original v1 dynamics are separate evidence.'}
fixed=region(base)==0
for ratio in [1,1.5,2,2.5]:
 c.parm('volume').set(ratio);c.parm('thigh_fullness').set(0);authored=positions(g.node('AUTHORED_INFLATION'));target=g.node('VOLUME_CALIBRATED_TARGET').geometry()
 assert np.array_equal(authored[fixed],base[fixed]);assert abs(target.attribValue('volume_ratio')-ratio)<1e-5
 for full in [0,.65]:
  c.parm('thigh_fullness').set(full);p=positions(g.node('OUT_NORMALIZED'));assert np.isfinite(p).all();assert len(p)==len(base)
  assert np.ptp(p[:,1])==np.ptp(base[:,1]);assert np.ptp(p[used,1])==np.ptp(base[used,1])
  assert np.array_equal(p[:,1],authored[:,1])
  exact=positions(g.node('OUT_FBX_SOURCE_STATURE'));target_height=json.loads((r.parent/'assets/mesh-info.json').read_text())['normalization_height_source_units']
  assert len(exact)==len(used),'Unused export points remain'
  assert abs(float(np.ptp(exact[:,1]))-target_height)<1e-6,'Source stature output differs from FBX height'
  thighfixed=(base[:,1]<=.34)|(base[:,1]>=.535)|(np.abs(base[:,0])>=.205)|(region(base)>=.025)
  assert np.array_equal(p[thighfixed],authored[thighfixed])
  if ratio==1 and full==0:assert np.array_equal(p,base)
  report['static'].append({'rear_ratio':ratio,'thigh_fullness':full,'finite':True,'point_height_drift':0,'rendered_height_drift':0,'source_stature_height':float(np.ptp(exact[:,1])),'source_stature_points':len(exact),'protected_thigh_displacement':0,'minimum_sampled_rear_jacobian':target.attribValue('minimum_sampled_jacobian')})
  if ratio in [1,2.5]:
   name=f'body-v4-{ratio:g}x-thigh-{full:g}';p.tofile(r/(name+'.bin'));g.node('OUT_NORMALIZED').geometry().saveToFile(str(r/(name+'.obj')))
c.parm('volume').set(4);target=g.node('VOLUME_CALIBRATED_TARGET');assert target.geometry() is None and any('folds' in x for x in target.errors())
report['unsafe_four_x_rejected']=True;report['native_integration_passed']=True
(r/'verification-v4.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
build=json.loads((r/'build-report-v4.json').read_text());build['status']='Native static integration verified; see verification-v4.json';(r/'build-report-v4.json').write_text(json.dumps(build,indent=2))
