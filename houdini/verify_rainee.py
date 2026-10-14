import hou,numpy as np,pathlib,json,time
r=pathlib.Path(__file__).resolve().parent
hou.hipFile.load(str(r/'Rainee-Volume-Lab.hip'),suppress_save_prompt=True)
g=hou.node('/obj/RAINEE');ctrl=g.node('CONTROLS');shape=g.node('AUTHORED_INFLATION');target=g.node('VOLUME_CALIBRATED_TARGET');solver=g.node('SOFT_MOTION')
def positions(node):return np.array(node.geometry().pointFloatAttribValues('P')).reshape(-1,3)
def volume(geo):
 p=np.array(geo.pointFloatAttribValues('P')).reshape(-1,3);t=np.array([[x.number() for x in f.points()] for f in geo.prims()]);return abs(np.einsum('ij,ij->i',p[t[:,0]],np.cross(p[t[:,1]],p[t[:,2]])).sum()/6)
base=positions(g.node('FBX_DERIVED_BODY'));report={'static':[],'dynamic':[]};hou.setFrame(1)
c=target.geometry();t=np.array([[p.number() for p in f.points()] for f in c.prims()]);edges=np.sort(np.concatenate((t[:,[0,1]],t[:,[1,2]],t[:,[2,0]])),axis=1);_,counts=np.unique(edges,axis=0,return_counts=True)
assert (counts==2).all();report['cage_closed_manifold_edge_test']=True
ctrl.parm('volume').deleteAllKeyframes()
for ratio in [.65,1,1.5,2,3]:
 ctrl.parm('volume').set(ratio);p=positions(shape);assert np.isfinite(p).all();actual=target.geometry().attribValue('volume_ratio');assert abs(actual-ratio)<1e-5
 protected=(base[:,1]>.73)|(base[:,1]<.49)|(base[:,2]>=.015)|(np.abs(base[:,0])>=.22)
 assert np.max(np.abs(p[protected]-base[protected]))<1e-7
 assert abs(np.ptp(p[:,1])-np.ptp(base[:,1]))<1e-7
 if ratio==1:assert np.max(np.abs(p-base))<1e-7
 native=positions(g.node('OUT_FBX_COORDINATES'))
 report['static'].append({'target_ratio':ratio,'actual_cage_ratio':actual,'height_normalized':float(np.ptp(p[:,1])),'height_source_units':float(np.ptp(native[:,1])),'protected_points':int(protected.sum()),'max_protected_displacement':float(np.max(np.abs(p[protected]-base[protected]))),'cage_volume':target.geometry().attribValue('cage_volume')})
 if ratio in [1,1.5,2]:
  p.astype('<f4').tofile(r/f'body-{ratio:g}x.bin');shape.geometry().saveToFile(str(r/f'Rainee-{ratio:g}x.obj'))
print('STATIC CHECKS PASSED',flush=True)
(r/'verification-native.json').write_text(json.dumps(report,indent=2))
hou.hipFile.load(str(r/'Rainee-Volume-Lab.hip'),suppress_save_prompt=True)
g=hou.node('/obj/RAINEE');solver=g.node('SOFT_MOTION');target=g.node('VOLUME_CALIBRATED_TARGET');g.node('CONTROLS').parm('simulation').set(True)
start=time.monotonic()
for frame in range(1,73):
 hou.setFrame(frame);sg=solver.geometry();p=np.array(sg.pointFloatAttribValues('P')).reshape(-1,3)
 if not np.isfinite(p).all():raise RuntimeError('Non-finite simulation')
 if frame in [1,12,24,36,48,60,72]:
  tg=target.geometry();tv=tg.attribValue('cage_volume');sv=volume(sg)
  row={'frame':frame,'target_ratio':tg.attribValue('volume_ratio'),'target_volume':tv,'simulated_volume':sv,'relative_volume_error':abs(sv-tv)/tv,'elapsed_seconds':time.monotonic()-start,'solver_errors':list(solver.errors()),'solver_warnings':list(solver.warnings())}
  report['dynamic'].append(row);print(json.dumps(row),flush=True);(r/'verification-native.json').write_text(json.dumps(report,indent=2))
  if frame in [24,48,72]:
   out=g.node('OUT_NORMALIZED');out.geometry().saveToFile(str(r/f'Rainee-sim-frame-{frame}.obj'));positions(out).astype('<f4').tofile(r/f'body-sim-{frame}.bin');sg.saveToFile(str(r/f'cage-sim-{frame}.bgeo.sc'))
report['dynamic_smoke_passed']=all(not x['solver_errors'] for x in report['dynamic']);report['note']='Dynamics smoke test only. Volume residuals are recorded; this is not a production collision or rig certification.'
(r/'verification-native.json').write_text(json.dumps(report,indent=2));print('VERIFICATION COMPLETE',flush=True)
