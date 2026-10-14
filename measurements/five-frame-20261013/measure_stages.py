"""Provisional local-surface descriptors of actual four accepted GLB meshes.

Single-stage memory use; no full-model height normalization or anatomy transfer.
Texture color rules and raw-source ROI boxes are explicitly reviewable filters.
"""
from pathlib import Path
import sys,json,io,gc
import numpy as np
from PIL import Image,ImageDraw
from sequence_reader import ROOT,HANDOFF,ACCEPTED,GLBReader
sys.path.insert(0,str(ROOT.parent));import model_compare
sys.path.insert(0,str(ROOT.parent/'reference-fit'));from fit_regional_rear import describe,features

REGIONS={
 'rear':{'min':[-.80,-.91,-.80],'max':[.80,-.10,.18],
  'confidence':'Provisional posterior lower-torso/lobe patch in GLB source coordinates; cropped thigh/pelvis overlap possible.'},
 'waist':{'min':[-.31,-.14,-.27],'max':[.31,.12,.31],
  'confidence':'Provisional central torso waist window in source coordinates; turn/arm/garment contamination possible.'}}

def texture(reader):
 doc=reader.document
 material=doc.get('materials',[{}])[0]
 index=material.get('pbrMetallicRoughness',{}).get('baseColorTexture',{}).get('index',0)
 imageindex=doc.get('textures',[{'source':0}])[index]['source'];data=doc['images'][imageindex]
 bv=doc['bufferViews'][data['bufferView']]
 with reader.path.open('rb') as stream:
  stream.seek(reader.binary_offset+bv.get('byteOffset',0));raw=stream.read(bv['byteLength'])
 im=Image.open(io.BytesIO(raw));original=im.size
 # Embedded images are JPEGs; decoder draft avoids decoding full8k textures.
 im.draft('RGB',(1024,1024));im.thumbnail((1024,1024));rgb=np.asarray(im.convert('RGB'))
 return rgb,{'image_index':imageindex,'embedded_mime':data.get('mimeType'),'original_size':list(original),'sampled_size':[rgb.shape[1],rgb.shape[0]],
  'sampling':'GLB TEXCOORD_0 triangle-centroid nearest embedded base-color image; JPEG draft/thumbnail max1024.'}

def roles_for_uv(uv,rgb):
 h,w=rgb.shape[:2];u=np.mod(uv[:,0],1);v=np.mod(uv[:,1],1)
 px=np.minimum((u*w).astype(int),w-1);py=np.minimum((v*h).astype(int),h-1)
 color=rgb[py,px].astype(float)/255.;r,g,b=color.T
 skin=(r>.40)&(g>.20)&(b>.12)&(r>g*1.025)&(g>b*.93)&((r-g)<.45)
 white=(np.min(color,1)>.35)&((np.max(color,1)-np.min(color,1))<.23)&(r<g*1.04)
 hair=(r>g*1.5)&(r>b*1.4)&(r>.25)&(g<.40)
 roles=np.zeros(len(uv),dtype=np.uint8);roles[skin]=1;roles[white]=2;roles[hair]=3
 return roles

def exact_selection(p,f,face_roles,roi):
 c=(p[f[:,0]]+p[f[:,1]]+p[f[:,2]])/3
 keep=((c>=np.array(roi['min']))&(c<=np.array(roi['max']))).all(1)&np.isin(face_roles,[1,2])
 return f[keep],keep

def main():
 reports=[]
 for number in ACCEPTED:
  name=f'frame_{number:04d}';out=ROOT/name;out.mkdir(exist_ok=True)
  reader=GLBReader(HANDOFF/name/'model.glb');p,f,uv,materials=reader.mesh()
  rgb,texture_info=texture(reader)
  fuv=(uv[f[:,0]]+uv[f[:,1]]+uv[f[:,2]])/3;roles=roles_for_uv(fuv,rgb)
  # Vertex candidate color roles support source-space inspection, not labeling anatomy.
  vertex_roles=roles_for_uv(uv,rgb)
  if not (out/'texture-role-preview.png').exists():model_compare.preview(p,vertex_roles,out/'texture-role-preview.png',caption='Source axes; turquoise skin candidate, orange white garment, blue red-hair candidate')
  regions={};roi_ids=np.zeros(len(p),dtype=np.int32)
  for i,(region,config) in enumerate(REGIONS.items(),1):
   selected,mask=exact_selection(p,f,roles,config)
   regions[region]=describe(p,selected)
   regions[region]['raw_source_roi']=config
   regions[region]['selected_triangle_count']=len(selected)
   mask.astype('u1').tofile(out/f'{region}-face-mask.bin')
   roi_ids[np.unique(selected)]=i
  if not (out/'local-roi-preview.png').exists():model_compare.preview(p,roi_ids,out/'local-roi-preview.png',caption='Provisional geometric ROIs: turquoise posterior/rear, orange waist; no height normalization')
  # Lightweight inspection proxy retains original source coordinates only.
  if (out/'preview-positions.bin').exists() and (out/'preview-triangles.bin').exists():
   proxy_info={'method':'vertex clustering for inspection only','vertices':(out/'preview-positions.bin').stat().st_size//12,
    'triangles':(out/'preview-triangles.bin').stat().st_size//12,'cell_size':float(np.ptp(p,axis=0).max()/180),
    'source_coordinate_system':True,'not_production_retopology':True}
  else:proxy_info=model_compare.clustered_proxy(p,f,out,grid=180)
  summary={'frame_number':number,'stage_ordinal':ACCEPTED.index(number)+1,'accepted_by_user':True,
   'geometry_source':str(reader.path),'geometry_representation':'Actual GLB scene mesh, node world transform applied; triangle mode',
   'source_vertices':len(p),'source_triangles':len(f),'source_axis_hypothesis':{'x':'lateral candidate','y':'up candidate','z':'front/depth candidate'},
   'axis_acceptance':False,'roi_acceptance':False,'pose_registered':False,
   'source_mesh_role_counts':{str(k):int((roles==k).sum()) for k in range(4)},'texture_sampling':texture_info,
   'regions':regions,'dimensionless_features':features(regions),'preview_proxy':proxy_info,
   'camera_mapping':'No GLB camera/extrinsic or source-image projection calibration. Default preview viewpoint is not evidence of a wrong unseen surface.',
   'ordinal_stage_not_volume_multiplier':True,'uses_global_bbox_height':False,
   'limits':['Independent generated cropped3D models; anatomy/pose and hidden surfaces can differ across stages.',
    'Color and source-space boxes are provisional selectors, not accepted body-part labels.',
    'Dimensionless area/PCA descriptors describe selected outside surfaces; no enclosed anatomical volume or stature is measured.',
    'No vertex correspondence, common rig, morph targets, or image-to-mesh camera registration is established.']}
  (out/'shape-descriptors.json').write_text(json.dumps(summary,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else None));reports.append(summary)
  print(name,'selected', {k:v['selected_triangle_count'] for k,v in regions.items()},'features',summary['dimensionless_features'],flush=True)
  del p,f,uv,fuv,roles,vertex_roles,rgb,roi_ids;gc.collect()
 combined={'status':'provisional_accepted_stage_surface_descriptors','accepted_frame_numbers':ACCEPTED,'endpoint':26,
  'rejected_frame0049_measured_as_target':False,'frames':reports,
  'comparison_ready':False,'scale_method':'Only within-region or rear-to-waist ratios; no full asset bounding-box height normalization.',
  'alignment_support':'Identity GLB node matrices and similar source axes support provisional common coordinate hypotheses. Independent geometry, pose/ROI correspondence and cameras remain unaccepted.',
  'stage_ordinals_are_not_volume_multipliers':True}
 (ROOT/'stage-shape-descriptors.json').write_text(json.dumps(combined,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else None))

if __name__=='__main__':main()
