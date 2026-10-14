"""Checks reader transforms, actual source buffers, and acceptance semantics."""
import json,struct,numpy as np
from sequence_reader import ROOT,HANDOFF,ACCEPTED,GLBReader

# A tiny self-authored GLB checks accessor offsets and parent-child transforms.
p=np.array([[0,0,0],[1,0,0],[0,1,0]],dtype='<f4');ii=np.array([0,1,2],dtype='<u2')
binary=p.tobytes()+ii.tobytes();binary+=b'\x00'*((-len(binary))%4)
doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(binary)}],
 'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36},{'buffer':0,'byteOffset':36,'byteLength':6}],
 'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'},
 {'bufferView':1,'componentType':5123,'count':3,'type':'SCALAR'}],
 'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1}]}],
 'nodes':[{'translation':[2,3,4],'scale':[2,2,2],'children':[1]},{'translation':[1,0,0],'mesh':0}],
 'scenes':[{'nodes':[0]}],'scene':0}
j=json.dumps(doc).encode();j+=b' '*((-len(j))%4)
fixture=ROOT/'reader-transform-fixture.glb'
fixture.write_bytes(struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)
v,f,_,_=GLBReader(fixture).mesh()
assert np.array_equal(v,np.array([[4,3,4],[6,3,4],[4,5,4]],dtype='<f4')) and np.array_equal(f,[[0,1,2]])

manifest=json.loads((ROOT/'reference-sequence-manifest.json').read_text());descriptors=json.loads((ROOT/'stage-shape-descriptors.json').read_text())
assert manifest['accepted_frame_numbers']==ACCEPTED and manifest['accepted_endpoint']==26
assert manifest['rejected_frame_numbers']==[49]
assert [f['stage_ordinal'] for f in manifest['frames'] if f['accepted']]==[1,2,3,4]
assert [f['frame_number'] for f in descriptors['frames']]==ACCEPTED
assert not (ROOT/'frame_0049/shape-descriptors.json').exists()
assert all(v['manifest_hash_matches'] for f in manifest['frames'] for v in f['enhanced_versions'])
checks=[]
for info in descriptors['frames']:
 num=info['frame_number'];name=f'frame_{num:04d}';reader=GLBReader(HANDOFF/name/'model.glb');p,f,_,_=reader.mesh()
 assert np.isfinite(p).all() and int(f.max())<len(p)
 mi=next(x for x in manifest['frames'] if x['frame_number']==num)
 ob=mi['derived_3d']['obj']['bounds_inventory_only']
 bounds_delta=max(float(abs(p.min(0)-np.array(ob['min'])).max()),float(abs(p.max(0)-np.array(ob['max'])).max()))
 assert bounds_delta<1e-6
 for region in ['rear','waist']:
  mask=np.fromfile(ROOT/name/(region+'-face-mask.bin'),'u1')
  assert len(mask)==len(f) and int(mask.sum())==info['regions'][region]['selected_triangle_count']
 assert info['uses_global_bbox_height'] is False and info['ordinal_stage_not_volume_multiplier'] is True
 checks.append({'frame_number':num,'finite_positions':True,'valid_triangle_indices':True,
  'GLB_OBJ_bound_difference_inventory_only':bounds_delta,'ROI_mask_lengths_and_counts_match':True,
  'global_bbox_height_used_for_measurement':False,'embedded_camera_count':len(reader.document.get('cameras',[]))})
 del p,f
verification={'pass':True,'reader_parent_child_transform_fixture_pass':True,'accepted_stages_match_direct_user_order':True,
 'frame0049_excluded_from_target_measurements':True,'enhancement_hashes_match':True,'frames':checks,
 'camera_or_pose_registration_proved':False,'soft_surface_descriptors_only':True,
 'limitations':'Verifies accepted stage bookkeeping, actual mesh data/ROI masks and buffer transforms, not anatomical labels or cross-stage mesh correspondence.'}
(ROOT/'verification.json').write_text(json.dumps(verification,indent=2));print(json.dumps(verification,indent=2))
