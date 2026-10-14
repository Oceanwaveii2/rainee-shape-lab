"""Verify independent thigh sculpt in actual Houdini cooks, including cached motion."""
import hou,numpy as np,pathlib,json
from thigh_setup import PARAMETERS
r=pathlib.Path(__file__).resolve().parent
hou.hipFile.load(str(r/'Rainee-Volume-Lab-v2.hip'),suppress_save_prompt=True)
g=hou.node('/obj/RAINEE');c=g.node('CONTROLS');s=g.node('INDEPENDENT_THIGHS');shape=g.node('AUTHORED_INFLATION');target=g.node('VOLUME_CALIBRATED_TARGET')
c.parm('simulation').set(False);c.parm('volume').deleteAllKeyframes();hou.setFrame(1)
def positions(n):
 geo=n.geometry()
 if geo is None:raise RuntimeError(n.path()+': '+str(n.errors()))
 return np.array(geo.pointFloatAttribValues('P'),dtype=np.float32).reshape(-1,3)
base=positions(g.node('FBX_DERIVED_BODY'))
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
seat=smooth(.49,.555,base[:,1])*(1-smooth(.667,.73,base[:,1]))*(1-smooth(-.045,.015,base[:,2]))*(1-smooth(.18,.22,np.abs(base[:,0])))
protected=(base[:,1]<=.34)|(base[:,1]>=.535)|(np.abs(base[:,0])>=.205)|(seat>=.025)
defaults={name:default for name,label,default,lo,hi in PARAMETERS}
profiles=[{}, {'thigh_fullness':.35}, {'thigh_fullness':.65},
 {'thigh_fullness':1,'thigh_outer':2,'thigh_front':2,'thigh_inner':1.5,'thigh_back':1.5,'thigh_taper':0,'thigh_peak':.2},
 {'thigh_fullness':1,'thigh_outer':2,'thigh_front':2,'thigh_inner':1.5,'thigh_back':1.5,'thigh_taper':1,'thigh_peak':.8}]
report={'scene':'Rainee-Volume-Lab-v2.hip','native_static_cases':[],'exports':[],'cached_dynamic_transfer':None,'limits':'Transverse artistic sculpt; no measured thigh tissue volume, pose rig, thigh dynamics, or collision certification.'}
deltas=[]
for ratio in [1,2,3]:
 c.parm('volume').set(ratio);authored=positions(shape)
 for j,profile in enumerate(profiles):
  opts={**defaults,**profile}
  for name,value in opts.items():c.parm(name).set(value)
  p=positions(s);assert not s.errors(),s.errors();assert np.isfinite(p).all()
  assert np.array_equal(p[:,1],authored[:,1]),'Thigh sculpt changed a vertex height'
  assert np.ptp(p[:,1])==np.ptp(base[:,1]),'Overall body height changed'
  assert np.array_equal(p[protected],authored[protected]),'Protected anatomy moved'
  assert np.all(p[base[:,0]>0,0]>0) and np.all(p[base[:,0]<0,0]<0),'Thigh crossed the medial plane'
  if j==0:assert np.array_equal(p,authored),'Neutral control is not identity'
  actual=target.geometry().attribValue('volume_ratio');assert abs(actual-ratio)<1e-5
  displacement=p-authored
  report['native_static_cases'].append({'rear_ratio':ratio,'thigh_controls':opts,'max_height_change_from_authored':float(abs(p[:,1]-authored[:,1]).max()),'overall_height_drift':float(np.ptp(p[:,1])-np.ptp(base[:,1])),'max_protected_change':float(abs(displacement[protected]).max()),'max_thigh_displacement':float(np.linalg.norm(displacement,axis=1).max()),'changed_points':int(np.any(displacement!=0,axis=1).sum()),'rear_cage_ratio':actual})
  if j==2:
   deltas.append(displacement)
   if ratio in [1,2]:
    file=f'body-rear-{ratio:g}-thigh-065.bin';p.astype('<f4').tofile(r/file);s.geometry().saveToFile(str(r/f'Rainee-rear-{ratio:g}-thigh-065.obj'))
    report['exports'].append({'file':file,'authored_file':f'body-{ratio:g}x.bin','controls':{k.removeprefix('thigh_'):v for k,v in opts.items()}})
assert max(float(abs(d-deltas[0]).max()) for d in deltas)<2e-7,'Rear ratio altered thigh delta'
report['independent_rear_controls']=True
# Cook the same native sculpt on the previously verified Vellum frame-72 export.
cached=g.createNode('python','VERIFY_CACHED_SIMULATION')
cached.parm('python').set('import hou,numpy as np\ng=hou.pwd().geometry();g.merge(hou.pwd().parent().node("FBX_DERIVED_BODY").geometry())\np=np.fromfile('+repr((r/'body-sim-72.bin').as_posix())+',dtype="<f4")\ng.setPointFloatAttribValues("P",p.tolist())')
s.setInput(0,cached)
for name,value in {**defaults,'thigh_fullness':.65}.items():c.parm(name).set(value)
authored=positions(cached);p=positions(s)
assert np.array_equal(p[:,1],authored[:,1]);assert np.array_equal(p[protected],authored[protected]);assert np.isfinite(p).all()
file='body-sim-72-thigh-065.bin';p.astype('<f4').tofile(r/file);s.geometry().saveToFile(str(r/'Rainee-sim-frame-72-thigh-065.obj'))
report['cached_dynamic_transfer']={'frame':72,'max_height_change':0,'max_protected_change':0,'note':'Native sculpt applied to the existing verified Vellum cache; upstream simulation was not rerun.'}
report['exports'].append({'file':file,'authored_file':'body-sim-72.bin','controls':{k.removeprefix('thigh_'):v for k,v in {**defaults,'thigh_fullness':.65}.items()}})
s.setInput(0,g.node('DIRECT_OR_SIMULATED'));cached.destroy()
report['protected_points']=int(protected.sum());report['native_passed']=True
(r/'verification-thighs.json').write_text(json.dumps(report,indent=2));print(json.dumps({'native_cases':len(report['native_static_cases']),'protected_points':report['protected_points'],'independent_rear_controls':True,'native_passed':True}),flush=True)
