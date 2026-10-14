from pathlib import Path
import json,math
R=Path(__file__).resolve().parent
d=json.loads((R/'reference-fit.json').read_text());c=d['diagnostic_candidate'];b=d['source_baseline'];t=d['target_shared_features']
rows={k:{'baseline':b['features'][k],'reference':t[k],'candidate':c['features'][k],
 'reference_change_from_baseline_percent':100*(t[k]/b['features'][k]-1),
 'candidate_difference_from_reference_percent':100*(c['features'][k]/t[k]-1)} for k in t}
delta={'status':'provisional_local_measurement_deltas','descriptors':rows,
 'contraction_constraints':{
  'rear_to_waist_width_target_lower_than_source':t['rear_to_waist_width']<b['features']['rear_to_waist_width'],
  'rear_to_waist_depth_target_lower_than_source':t['rear_to_waist_depth']<b['features']['rear_to_waist_depth'],
  'volume_lower_bound':1.,'current_controls_allow_contraction':False,
  'interpretation':'Two waist-normalized cues ask for a smaller rear relative to the selected waist, while rear depth/width asks for more projection. Target waist shape/pose and corresponding patches are provisional. This is a correspondence conflict, not a validated instruction to contract Rainee.'},
 'observed_feature_ranges':d['diagnostic_search'].get('observed_feature_ranges'),
 'objective':{'baseline':b['score'],'candidate':c['score'],'direction':'smaller is better',
  'relative_objective_reduction':1-c['score']/b['score'],
  'candidate_weighted_log_rmse':math.sqrt(c['data_score']/sum(d['metric_weights'].values())),
  'interpretation':'Internal weighted descriptor error, not percent anatomical or visual accuracy.'},
 'candidate_constraints':d['candidate_checks'],'parameters':c['parameters'],'jacobian_guard':c['jacobian_guard'],
 'comparison_ready':False,'accepted_winner':None}
(R/'descriptor-deltas.json').write_text(json.dumps(delta,indent=2))
preset=json.loads((R/'parameter-preset-candidate.json').read_text())
preset.update({'inspection_allowed':True,'automatic_adoption':False,'objective_score':c['score'],
 'objective_label':'weighted regional descriptor objective; smaller is better',
 'match_accuracy_percent':None,'source_height_drift':0.,'jacobian_min_determinant':c['jacobian_guard']['min_determinant']})
(R/'parameter-preset-candidate.json').write_text(json.dumps(preset,indent=2))
manifest={'fit_report':'reference-fit.json','descriptor_deltas':'descriptor-deltas.json','preset':'parameter-preset-candidate.json',
 'candidate_positions':'diagnostic-candidate-positions.bin','candidate_triangles':'diagnostic-candidate-triangles.bin',
 'source_roi_preview':'source-regional-roi-preview.png','candidate_roi_preview':'diagnostic-candidate-roi-preview.png',
 'verification':'verification.json','fitter':'fit_regional_rear.py','evaluated_candidates':'evaluated-candidates.json','source_point_count':98078,'candidate_point_count':121901,
 'comparison_ready':False,'candidate_inspection_allowed':True,'automatic_adoption':False,
 'status':'Provisional diagnostic regional fit; local axes/ROI correspondence still need registration'}
(R/'reference-fit-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'manifest':str(R/'reference-fit-manifest.json'),'deltas':rows,'objective':delta['objective']},indent=2))
