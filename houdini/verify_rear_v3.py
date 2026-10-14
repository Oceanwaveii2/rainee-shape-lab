"""Native geometry and closed-control-volume verification for authored v3 growth."""
import hou,numpy as np,pathlib,json
from rear_model import DEFAULTS,deform,volume,region
r=pathlib.Path(__file__).resolve().parent
hou.hipFile.load(str(r/'Rainee-Volume-Lab-v3.hip'),suppress_save_prompt=True)
g=hou.node('/obj/RAINEE');c=g.node('CONTROLS');c.parm('volume').deleteAllKeyframes();c.parm('simulation').set(False);c.parm('thigh_fullness').set(0);hou.setFrame(1)
def positions(n):
 geo=n.geometry()
 if geo is None:raise RuntimeError(str(n.errors()))
 return np.array(geo.pointFloatAttribValues('P'),dtype=np.float32).reshape(-1,3)
base=positions(g.node('FBX_DERIVED_BODY'));cagebase=positions(g.node('CLOSED_REAR_CAGE'))
tri=np.array([[p.number() for p in f.points()] for f in g.node('CLOSED_REAR_CAGE').geometry().prims()])
mask=region(base);fixed=mask==0
report={'scene':'Rainee-Volume-Lab-v3.hip','static':[],'shape_control_cases':[],'field':'Per-lobe authored deformation with an enclosed-volume constraint. It is not a measured anatomical tissue volume.','visual_status':'Grok-informed shape study; visual match not established.'}
for ratio in [1,1.25,1.5,2,2.5,3]:
 c.parm('volume').set(ratio);target=g.node('VOLUME_CALIBRATED_TARGET');p=positions(g.node('OUT_NORMALIZED'));cp=positions(target)
 amp=target.geometry().attribValue('inflation_amplitude');expected=deform(base.astype(float),amp)
 assert np.isfinite(p).all() and np.isfinite(cp).all()
 assert np.array_equal(p[fixed],base[fixed]);assert np.ptp(p[:,1])==np.ptp(base[:,1])
 assert np.all(p[base[:,0]>0,0]>0) and np.all(p[base[:,0]<0,0]<0)
 actual_ratio=volume(cp.astype(float),tri)/volume(cagebase.astype(float),tri)
 assert abs(actual_ratio-ratio)<2e-6,(ratio,actual_ratio,target.geometry().attribValue('volume_ratio'))
 max_delta=float(abs(p-expected).max());assert max_delta<2e-7
 if ratio==1:assert np.array_equal(p,base)
 right=cp[cp[:,0]>=0];width=float(np.ptp(right[:,0]));height=float(np.ptp(right[:,1]))
 # Local triangle collapse/inversion screen on the authored cage.
 a=cagebase[tri];b=cp[tri];n0=np.cross(a[:,1]-a[:,0],a[:,2]-a[:,0]);n1=np.cross(b[:,1]-b[:,0],b[:,2]-b[:,0]);assert np.min(np.linalg.norm(n1,axis=1))>1e-10
 assert np.all(np.einsum('ij,ij->i',n0,n1)>0),'Cage triangle changed orientation'
 p.astype('<f4').tofile(r/f'body-v3-{ratio:g}x.bin');cp.astype('<f4').tofile(r/f'cage-v3-{ratio:g}x.bin')
 g.node('OUT_NORMALIZED').geometry().saveToFile(str(r/f'Rainee-v3-{ratio:g}x.obj'))
 report['static'].append({'ratio':ratio,'actual_cage_ratio':actual_ratio,'amplitude':amp,'height_drift':0,'protected_displacement':0,'native_formula_error':max_delta,'minimum_sampled_jacobian':target.geometry().attribValue('minimum_sampled_jacobian'),'cage_right_lobe_width_height':width/height,'cage_width':float(np.ptp(cp[:,0])),'cage_height':height,'cage_depth':float(np.ptp(cp[:,2]))})
print('V3 STATIC BASE PROFILES PASSED',flush=True)
for updates in [{'upper_pole':1.6,'lower_pole':1.6},{'cleft_hold':1.,'separation':0.},{'lateral':1.6,'vertical':.4,'projection':1.6},{'lateral':.4,'vertical':1.6,'projection':.4}]:
 opts={**DEFAULTS,**updates}
 for name,value in opts.items():c.parm(name).set(value)
 c.parm('volume').set(2);target=g.node('VOLUME_CALIBRATED_TARGET');tg=target.geometry()
 if updates=={'lateral':.4,'vertical':1.6,'projection':.4}:
  assert tg is None and any('folds' in x for x in target.errors()),'Unsafe directional field was accepted'
  report['shape_control_cases'].append({'controls':opts,'accepted':False,'rejected_as_expected':True,'reason':'Nonpositive sampled field Jacobian'});continue
 p=positions(g.node('OUT_NORMALIZED'));cp=positions(target)
 assert np.isfinite(p).all();assert np.ptp(p[:,1])==np.ptp(base[:,1]);assert np.array_equal(p[fixed],base[fixed]);assert abs(volume(cp.astype(float),tri)/volume(cagebase.astype(float),tri)-2)<2e-6
 report['shape_control_cases'].append({'controls':opts,'accepted':True,'passed':True})
for name,value in DEFAULTS.items():c.parm(name).set(value)
c.parm('volume').set(4);target=g.node('VOLUME_CALIBRATED_TARGET')
assert target.geometry() is None and any('folds' in x for x in target.errors()),'Unsafe 4x field was accepted'
report['rejected_extreme']={'ratio':4,'rejected_as_expected':True,'reason':'Nonpositive sampled field Jacobian'}
report['jacobian_screen_limit']='Point-sampled field orientation check; no triangle contact or collision certification.'
report['native_static_passed']=True
(r/'verification-rear-v3.json').write_text(json.dumps(report,indent=2))
# Geometry and source field for the lightweight interactive authoring view.
cagebase.astype('<f4').tofile(r/'cage-rest.bin');tri.astype('<u4').tofile(r/'cage-triangles.bin')
print(json.dumps({'cases':len(report['static'])+len(report['shape_control_cases']),'lobe_aspects':[(x['ratio'],round(x['cage_right_lobe_width_height'],3)) for x in report['static']],'native_static_passed':True}),flush=True)
