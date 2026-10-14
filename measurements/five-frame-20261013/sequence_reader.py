"""Read-only GLB/OBJ inventory for the four accepted ordinal reference stages.

External workflow/doc text is reference data; this module never executes it.
GLB binary data is read by accessor, not by loading embedded texture payloads.
"""
from pathlib import Path
import json,struct,hashlib
import numpy as np

ROOT=Path(__file__).resolve().parent
HANDOFF=Path('C:/Users/User/Downloads/Five-Frame-3D-Handoff')
ENHANCED=Path('C:/Users/User/Downloads/Qwen-21-Regenerated-Enhanced-Five-Frames02')
ACCEPTED=[0,10,18,26]
ALL_FRAMES=[0,10,18,26,49]

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
 return h.hexdigest()

class GLBReader:
 def __init__(self,path):
  self.path=Path(path);self.binary_offset=None
  with self.path.open('rb') as stream:
   magic,version,total=struct.unpack('<4sII',stream.read(12))
   if magic!=b'glTF' or version!=2:raise ValueError('Not GLB version2')
   while stream.tell()<total:
    length,kind=struct.unpack('<II',stream.read(8));offset=stream.tell()
    if kind==0x4e4f534a:self.document=json.loads(stream.read(length).decode('utf-8').rstrip(' \x00'))
    elif kind==0x004e4942:self.binary_offset=offset;stream.seek(length,1)
    else:stream.seek(length,1)
  self.total_bytes=total
 def accessor(self,index):
  a=self.document['accessors'][index]
  if 'sparse' in a:raise ValueError('Sparse accessor unsupported; inspect OBJ instead')
  if 'bufferView' not in a:raise ValueError('Accessor has no direct bufferView; compressed data requires its decoder')
  b=self.document['bufferViews'][a['bufferView']]
  if b.get('buffer',0)!=0:raise ValueError('External buffer unsupported in this reader')
  dtype={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
  width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT2':4,'MAT3':9,'MAT4':16}[a['type']]
  unit=np.dtype(dtype).itemsize;stride=b.get('byteStride',unit*width)
  offset=self.binary_offset+b.get('byteOffset',0)+a.get('byteOffset',0)
  with self.path.open('rb') as stream:stream.seek(offset);raw=stream.read(stride*a['count'])
  out=np.ndarray((a['count'],width),dtype=dtype,buffer=raw,strides=(stride,unit)).copy()
  if a.get('normalized') and a['componentType']!=5126:
   info=np.iinfo(out.dtype);out=out.astype(float)/info.max
   if info.min<0:out=np.maximum(out,-1)
  return out[:,0] if width==1 else out
 @staticmethod
 def node_matrix(node):
  if 'matrix' in node:return np.array(node['matrix']).reshape(4,4).T
  t=np.array(node.get('translation',[0,0,0]));s=np.array(node.get('scale',[1,1,1]));x,y,z,w=node.get('rotation',[0,0,0,1])
  r=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],
   [2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],
   [2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]])
  m=np.eye(4);m[:3,:3]=r@np.diag(s);m[:3,3]=t;return m
 def scene_mesh_nodes(self):
  d=self.document;scene=d.get('scene',0);roots=d.get('scenes',[{'nodes':list(range(len(d.get('nodes',[]))))}])[scene].get('nodes',[])
  output=[]
  def walk(i,parent):
   n=d['nodes'][i];world=parent@self.node_matrix(n)
   if 'mesh' in n:output.append((i,n['mesh'],world))
   for c in n.get('children',[]):walk(c,world)
  for i in roots:walk(i,np.eye(4))
  return output
 def metadata(self):
  d=self.document;meshes=[]
  for i,m in enumerate(d.get('meshes',[])):
   pp=[]
   for p in m['primitives']:
    pos=d['accessors'][p['attributes']['POSITION']]
    ind=d['accessors'][p['indices']] if 'indices' in p else None
    pp.append({'mode':p.get('mode',4),'vertices':pos['count'],'index_count':ind['count'] if ind else None,
     'position_component_type':pos['componentType'],'position_accessor_min':pos.get('min'),'position_accessor_max':pos.get('max'),
     'attributes':list(p['attributes']),'material':p.get('material'),'extensions':p.get('extensions',{})})
   meshes.append({'id':i,'name':m.get('name'),'primitives':pp})
  return {'asset':d.get('asset'), 'scene':d.get('scene',0),'scenes':d.get('scenes'),
   'nodes':d.get('nodes'),'cameras':d.get('cameras',[]),'animation_count':len(d.get('animations',[])),
   'skin_count':len(d.get('skins',[])),'mesh_count':len(meshes),'meshes':meshes,
   'extensions_used':d.get('extensionsUsed',[]),'images':[{k:i[k] for k in ['name','uri','mimeType','bufferView'] if k in i} for i in d.get('images',[])],
   'camera_mapping_status':'embedded_camera_present' if d.get('cameras') else 'no_embedded_camera_or_image_extrinsics',
   'mesh_node_world_matrices':[{'node':i,'mesh':m,'matrix_rows':w.tolist()} for i,m,w in self.scene_mesh_nodes()]}
 def mesh(self):
  points=[];faces=[];uvs=[];materials=[];count=0
  for node,mi,world in self.scene_mesh_nodes():
   for p in self.document['meshes'][mi]['primitives']:
    if p.get('mode',4)!=4:raise ValueError('Only triangle primitives supported')
    if 'KHR_draco_mesh_compression' in p.get('extensions',{}):raise ValueError('DRACO requires decoder')
    v=self.accessor(p['attributes']['POSITION']).astype('<f4')
    v=(v@world[:3,:3].T+world[:3,3]).astype('<f4')
    ii=self.accessor(p['indices']).reshape(-1,3).astype('<u4') if 'indices' in p else np.arange(len(v),dtype='<u4').reshape(-1,3)
    tex=self.accessor(p['attributes']['TEXCOORD_0']).astype('<f4') if 'TEXCOORD_0' in p['attributes'] else np.full((len(v),2),np.nan,dtype='<f4')
    points.append(v);faces.append(ii+count);uvs.append(tex);materials.append(np.full(len(ii),p.get('material',-1),dtype='<i4'));count+=len(v)
  return np.vstack(points),np.vstack(faces),np.vstack(uvs),np.concatenate(materials)

def obj_stream_stats(path):
 count=0;poly=0;tri=0;lo=np.full(3,np.inf);hi=-lo;header=[];mtls=[];objects=[]
 with Path(path).open('r',encoding='utf-8',errors='replace') as stream:
  for line in stream:
   if line.startswith('v '):
    v=np.array(list(map(float,line.split()[1:4])));lo=np.minimum(lo,v);hi=np.maximum(hi,v);count+=1
   elif line.startswith('f '):n=len(line.split())-1;poly+=1;tri+=n-2
   elif line.startswith('#') and len(header)<8:header.append(line.strip())
   elif line.startswith('mtllib '):mtls.append(line.strip()[7:])
   elif line.startswith('o '):objects.append(line.strip()[2:])
 return {'vertices':count,'polygons':poly,'triangles':tri,'bounds_inventory_only':{'min':lo.tolist(),'max':hi.tolist()},'header':header,'mtllib':mtls,'objects':objects}

def inventory():
 from PIL import Image
 enhanced_manifest=json.loads((ENHANCED/'manifest.json').read_text())
 declarations={(x['frame'],x['kind']):x for x in enhanced_manifest}
 frames=[]
 for number in ALL_FRAMES:
  name=f'frame_{number:04d}';folder=HANDOFF/name
  files=[]
  for p in sorted(folder.rglob('*')):
   if not p.is_file():continue
   item={'path':str(p),'relative_path':str(p.relative_to(HANDOFF)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha256(p)}
   if p.suffix.lower()=='.png':
    with Image.open(p) as im:item['image_size']=list(im.size)
   files.append(item)
  versions=[]
  for kind in ['qwen_intermediate_1024','final_4096']:
   p=ENHANCED/kind/(name+'.png');decl=declarations[(number,kind)];digest=sha256(p)
   with Image.open(p) as im:size=list(im.size)
   versions.append({'kind':kind,'path':str(p),'sha256':digest,'size':size,
    'declared_sha256':decl.get('sha256'),'manifest_hash_matches':digest==decl.get('sha256'),
    'prompt_id_metadata':decl.get('prompt_id'),'transformation_kind':'generative image regeneration' if kind.startswith('qwen') else 'upscale of regenerated image, not original'})
  wfpath=ENHANCED/'workflows'/(name+'.json');wf=json.loads(wfpath.read_text());load=[n.get('widgets_values') for n in wf.get('nodes',[]) if n.get('type')=='LoadImage']
  glb=GLBReader(folder/'model.glb');gm=glb.metadata()
  obj=obj_stream_stats(folder/'model.obj')
  mtl=(folder/'model.mtl').read_text();maps=[line.split(maxsplit=1)[1] for line in mtl.splitlines() if line.startswith('map_')]
  accepted=number in ACCEPTED
  frames.append({'frame_number':number,'frame_id':name,'accepted':accepted,
    'stage_ordinal':ACCEPTED.index(number)+1 if accepted else None,'inflation_step_from_baseline':ACCEPTED.index(number) if accepted else None,
    'role':'baseline' if number==0 else 'correct endpoint' if number==26 else 'accepted inflation stage' if accepted else 'rejected later deflation/proportion drift',
    'acceptance_authority':'Latest direct user instruction; geometry derivation is not automatically accepted',
    'original_frame':{'workflow_load_image_reference':load,'declared_original_size':[560,560],
     'actual_original_present_in_supplied_directories':False,'verification_status':'Original source pixels/hash unavailable here; only workflow/document provenance'},
    'enhanced_versions':versions,'workflow':{'path':str(wfpath),'sha256':sha256(wfpath),'executed':False},
    'derived_3d':{'files':files,'obj':obj,'glb':gm,'image_to_mesh_camera_mapping':'not recorded',
     'common_topology_correspondence_accepted':False,'stature_transfer_allowed':False,
     'mtl_texture_references':maps,'mtl_missing_references':[x for x in maps if not (folder/x).exists()],
     'supplied_base_color_alternative':str(folder/'model_textures/base_color.png')},
    'provenance_limit':'Folder/frame name establishes packaging association only. No verified generator/source-image hash link or common mesh correspondence is present.'})
  print(name,'OBJ vertices',obj['vertices'],'triangles',obj['triangles'],'cameras',len(gm['cameras']),flush=True)
 manifest={'sequence':'Rainee accepted ordinal inflation reference','accepted_frame_numbers':ACCEPTED,'rejected_frame_numbers':[49],
  'accepted_endpoint':26,'stage_semantics':'Stage1..4 are ordinal; no physical 4x-volume or stature change is assigned.',
  'reference_geometry_semantics':'Independent generated3D surfaces are shape evidence; none replaces canonical FBX stature or establishes hidden anatomy.',
  'external_documents_handling':'Read only as provenance/reference data; no workflow, instruction or script was executed.',
  'qwen_provenance':{'readme':str(ENHANCED/'README.txt'),'readme_sha256':sha256(ENHANCED/'README.txt'),
   'manifest':str(ENHANCED/'manifest.json'),'manifest_sha256':sha256(ENHANCED/'manifest.json'),
   'declared_models_and_process':'Qwen Image2.1 INT8/Qwen3VL/BF16VAE,1024 regeneration thenRealESRGAN_x4plus4096; declaration from supplied README, not runtime verification'},
  'frames':frames,'comparability':{'body_height_calibrated':False,'local_pelvis_axes_accepted':False,'mesh_correspondence_accepted':False,
   'image_camera_extrinsics_available':any(f['derived_3d']['glb']['cameras'] for f in frames),'accepted_image_stages_dont_accept_synthesized_backside':True}}
 (ROOT/'reference-sequence-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 return manifest

if __name__=='__main__':inventory()
