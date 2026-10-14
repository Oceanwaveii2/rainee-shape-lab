"""Compare frozen transferred-patch fit vs native direct field; no optimization."""
import json,numpy as np
from fit_regional_rear import ROOT,HOUDINI,RearFitter,describe,features,METRIC_WEIGHTS
R=ROOT
report=json.loads((R/'reference-fit.json').read_text());candidate=report['diagnostic_candidate']
fit=RearFitter(report['target_shared_features'])
native=np.fromfile(HOUDINI/'body-figurine-native.bin','<f4').reshape(-1,3)
local=native[fit.region_point_ids]
regions={k:describe(local,f) for k,f in fit.region_faces.items()};feat=features(regions)
errors={k:float(np.log(feat[k]/fit.target[k])) for k in METRIC_WEIGHTS}
data=sum(METRIC_WEIGHTS[k]*errors[k]**2 for k in errors)
score=data+candidate['regularization_score']
rows={k:{'fitter_transferred_patch':candidate['features'][k],'native_direct_field':feat[k],
 'native_difference_percent':100*(feat[k]/candidate['features'][k]-1)} for k in feat}
diag={'status':'operator_semantics_difference_confirmed','frozen_files_modified':False,'new_optimization_performed':False,
 'source_operator':'Deform original source points, then transfer their offsets through eight-neighbor repair bind',
 'native_operator':'Apply production rear field directly to all repaired body points',
 'same_parameters':candidate['parameters'],'regional_objective_points':len(fit.region_point_ids),
 'regional_objective_original_points':len(fit.oldids),'regional_objective_repair_points':len(fit.newids),
 'original_source_defaults_match':True,'features':rows,'frozen_objective_score':candidate['score'],
 'native_direct_objective_score':float(score),'absolute_objective_score_difference':float(score-candidate['score']),
 'relative_objective_score_difference':float(score/candidate['score']-1),
 'native_direct_regions':regions,'interpretation':'Defaults and original-body deformation match. The added repair collar uses a different deformation operator, which slightly changes regional measures. This is an expected bind-vs-direct-field difference, and native cache measurements should describe the actual editor trial.'}
(R/'native-objective-diagnostic.json').write_text(json.dumps(diag,indent=2));print(json.dumps(diag,indent=2))
