"""Read-only scene comparison; writes a diagnostic report, never changes the trial."""
from pathlib import Path
import hou,numpy as np,json,importlib.util,hashlib
R=Path(__file__).resolve().parent;H=R.parents[1]/'houdini'
hou.hipFile.load(str(H/'Rainee-Figurine-Projection-Trial.hip'),suppress_save_prompt=True,ignore_load_warnings=True)
ctrl=hou.node('/obj/RAINEE/CONTROLS');obj=ctrl.parent()
spec=importlib.util.spec_from_file_location('native_rear_model',H/'rear_model.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
params={k:ctrl.evalParm(k) for k in ['volume',*model.DEFAULTS.keys()]}
body=obj.node('REPAIRED_BODY') or obj.node('FBX_DERIVED_BODY')
baseline=np.array(body.geometry().pointFloatAttribValues('P')).reshape(-1,3)
shape=obj.node('AUTHORED_INFLATION')
native=np.array(shape.geometry().pointFloatAttribValues('P')).reshape(-1,3)
frozen=np.fromfile(R/'diagnostic-candidate-positions.bin','<f4').reshape(-1,3)
delta=np.linalg.norm(native-frozen,axis=1);n=98078
e=np.abs(native-frozen);i=int(delta.argmax())
cage=obj.node('CLOSED_REAR_CAGE').geometry()
cv=np.array(cage.pointFloatAttribValues('P')).reshape(-1,3);cf=np.array([[p.number() for p in f.points()] for f in cage.prims()])
amp,_=model.calibrate(cv,cf,params['volume'],params)
direct=model.deform(baseline,amp,params)
dd=np.linalg.norm(native-direct,axis=1)
report={'native_parameters':params,'model_defaults':model.DEFAULTS,'native_cage_amplitude':float(amp),
 'native_count':len(native),'frozen_count':len(frozen),'max_euclidean_delta':float(delta.max()),'max_coordinate_delta':float(e.max()),
 'original_source_max_euclidean_delta':float(delta[:n].max()),'added_repair_max_euclidean_delta':float(delta[n:].max()),
 'original_source_points_over_1e_6':int((delta[:n]>1e-6).sum()),'repair_points_over_1e_6':int((delta[n:]>1e-6).sum()),
 'maximum_point':{'id':i,'baseline':baseline[i].tolist(),'native':native[i].tolist(),'frozen':frozen[i].tolist()},
 'native_vs_direct_production_python_max_delta':float(dd.max()),
 'native_field_guard_full_repaired_body':model.jacobian_screen(baseline,amp,params),
 'frozen_positions_sha256':hashlib.sha256((R/'diagnostic-candidate-positions.bin').read_bytes()).hexdigest()}
(R/'native-trial-diagnostic.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
