import json,re
from sequence_reader import ROOT,ACCEPTED
manifest=json.loads((ROOT/'reference-sequence-manifest.json').read_text());shape=json.loads((ROOT/'stage-shape-descriptors.json').read_text())
for frame in manifest['frames']:
 frame['physical_volume_multiplier']=None
 refs=frame['original_frame']['workflow_load_image_reference']
 matches=[re.search(r'_([0-9]+\.[0-9]+)s\.',str(x)) for x in refs]
 frame['original_frame']['declared_time_seconds_from_filename']=[float(m.group(1)) for m in matches if m]
 frame['original_frame']['declared_time_is_video_verified']=False
manifest['cross_dataset_payload_mapping']={'worldgen_obj_f9f63233_sha256':'299c5c92cf71000e437509bbbc50e95f9b281df8de32e4ec01e5a3ff949bd599',
 'exact_OBJ_payload_match_to_any_stage':any(x['sha256']=='299c5c92cf71000e437509bbbc50e95f9b281df8de32e4ec01e5a3ff949bd599' for f in manifest['frames'] for x in f['derived_3d']['files'] if x['relative_path'].endswith('.obj')),
 'SPZ_or_worldgen_frame_association':'Not established; no original frame IDs/hashes or camera calibration link these mesh sets to scene splats.'}
(ROOT/'reference-sequence-manifest.json').write_text(json.dumps(manifest,indent=2))
features={x['frame_number']:x['dimensionless_features'] for x in shape['frames']}
ratios={k:[features[n][k] for n in ACCEPTED] for k in features[0]}
notes={'accepted_frame_numbers':ACCEPTED,'correct_endpoint':26,'reject_after_endpoint_including':[49],
 'stage_semantics':'Ordinal1..4; not 1x/2x/3x/4x volume labels',
 'actual_meshes':[{k:x[k] for k in ['frame_number','source_vertices','source_triangles']} for x in shape['frames']],
 'dimensionless_feature_sequences':ratios,
 'descriptor_monotonicity_is_target_authority':False,
 'correspondence_findings':['Four independent generated GLB meshes have identity scene transforms and no cameras, animations, or skins.',
 'They are cropped characters with different poses/view evidence and vertex counts. Common source coordinates do not establish local pelvis axes or matching anatomy.',
 'The provisional posterior ROI includes possible pelvis/upper-thigh/arm/garment overlap; color selection is imperfect.',
 'Raw rear-to-waist descriptors do not follow the accepted monotonic inflation order. Their decrease at0026 must not be treated as intended deflation or used to shrink Rainee.',
 'Default model preview viewpoint does not prove the unseen posterior surface is correct or incorrect; actual camera correspondence is unavailable.',
 'Qwen1024 images are generative regenerations;4096 versions are upscales of those outputs. Original560²source pixels/hash are unavailable in supplied folders.'],
 'safe_integration':'Use0000→0010→0018→0026 as approved image-stage timeline, hold0026 endpoint, exclude0049. Keep generated mesh descriptors as separately labeled soft evidence until local ROIs/axes and camera correspondences are reviewed.',
 'global_height_transfer':False,'anatomical_volume_inferred':False,'workflow_or_external_script_executed':False}
(ROOT/'sequence-assessment.json').write_text(json.dumps(notes,indent=2))
out={'reference_manifest':'reference-sequence-manifest.json','assessment':'sequence-assessment.json','descriptors':'stage-shape-descriptors.json',
 'reader':'sequence_reader.py','measurements':'measure_stages.py','verification':'verification.json','accepted_frame_numbers':ACCEPTED,
 'endpoint':26,'rejected_frame_numbers':[49],'comparison_ready':False,
 'stage_geometry_previews':{f'frame_{n:04d}':{'positions':f'frame_{n:04d}/preview-positions.bin','triangles':f'frame_{n:04d}/preview-triangles.bin',
  'ROI_preview':f'frame_{n:04d}/local-roi-preview.png','role_preview':f'frame_{n:04d}/texture-role-preview.png','report':f'frame_{n:04d}/shape-descriptors.json'} for n in ACCEPTED}}
(ROOT/'integration-manifest.json').write_text(json.dumps(out,indent=2))
print(json.dumps(notes,indent=2))
