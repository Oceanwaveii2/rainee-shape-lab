"""Read/export retained full-body model geometry in an Argon sandbox.

List/export require Python standard library. Inspect/verify also require NumPy.
XZ geometry preserves decoded float64 position and uint32 triangle bits; no LOD
is substituted for the complete R01-R06 source geometry. All originals are read-only.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,lzma,struct,sys
from array import array

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/'models/full-body-bridge/registry.json'
def digest(b):return hashlib.sha256(b).hexdigest()
def catalog():
 data=json.loads(REGISTRY.read_text(encoding='utf-8'))
 if data['schema']!='rainee-full-body-model-bridge-v1':raise ValueError('Unsupported model registry')
 return data
def entry(mid):
 matches=[m for m in catalog()['models']if m['id']==mid]
 if len(matches)!=1:raise ValueError('Choose one registered model id')
 return matches[0]
def unshuffle(raw,width):
 if len(raw)%width:raise ValueError('Unaligned shuffled buffer')
 count=len(raw)//width;out=bytearray(len(raw))
 for i in range(width):out[i::width]=raw[i*count:(i+1)*count]
 return bytes(out)
def read_geometry_buffer(desc):
 if 'route'in desc:
  spec=importlib.util.spec_from_file_location('rainee_legacy',ROOT/'tools/retained_asset.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);raw=mod.read_retained_asset(ROOT/desc['route'])
 else:
  path=(ROOT/desc['path']).resolve()
  if not path.is_relative_to(ROOT.resolve()):raise ValueError('Model buffer outside package')
  packed=path.read_bytes()
  if digest(packed)!=desc['stored_sha256']:raise ValueError('Stored geometry checksum mismatch')
  raw=lzma.decompress(packed);encoding=desc['encoding']
  if encoding=='delta-zigzag-shuffle32':
   raw=unshuffle(raw,4);values=array('I');values.frombytes(raw)
   if sys.byteorder!='little':values.byteswap()
   accumulator=0
   for i,value in enumerate(values):
    accumulator+=(value>>1)^-(value&1)
    if not 0<=accumulator<=0xffffffff:raise ValueError('Index delta outside uint32')
    values[i]=accumulator
   if sys.byteorder!='little':values.byteswap()
   raw=values.tobytes()
  else:
   raw=unshuffle(raw,desc['shuffle_word']);out=array('d')
   if encoding=='decimal-i32-f64-exact':
    values=array('i');values.frombytes(raw)
    if sys.byteorder!='little':values.byteswap()
    scale=desc['scale']
    if not isinstance(scale,int)or scale<=0:raise ValueError('Invalid exact lattice scale')
    out.extend(value/scale for value in values)
    for i in desc['negative_zero_indices']:
     if not 0<=i<len(out)or out[i]!=0:raise ValueError('Invalid negative-zero record')
     out[i]=-0.0
   elif encoding=='f32-to-f64-exact':
    values=array('f');values.frombytes(raw)
    if sys.byteorder!='little':values.byteswap()
    out.extend(float(value)for value in values)
   elif encoding=='f64-exact':out.frombytes(raw)
   else:raise ValueError('Unsupported full model position encoding')
   if sys.byteorder!='little':out.byteswap()
   raw=out.tobytes()
 if len(raw)!=desc['decoded_bytes']or digest(raw)!=desc['decoded_sha256']:raise ValueError('Decoded model checksum mismatch')
 return raw
def read_model(mid):
 m=entry(mid);g=m['geometry']
 if g['positions']['dtype']not in ['float32-le','float64-le']or g['triangles']['dtype']!='uint32-le':raise ValueError('Unsupported decoded mesh types')
 p,t=read_geometry_buffer(g['positions']),read_geometry_buffer(g['triangles']);stride=24 if g['positions']['dtype']=='float64-le'else 12
 if len(p)%stride or len(t)%12:raise ValueError('Invalid position/triangle alignment')
 return m,p,t
def export_obj(mid,path):
 m,p,t=read_model(mid);dtype=m['geometry']['positions']['dtype'];fmt='<ddd'if dtype=='float64-le'else'<fff'
 count=len(p)//struct.calcsize(fmt)
 if len(t)%12:raise ValueError('Triangle buffer alignment failure')
 path=Path(path).resolve()
 if path.is_relative_to((ROOT/'models').resolve())or path.is_relative_to((ROOT/'data').resolve()):raise ValueError('Export outside immutable model/storage directories')
 if path.exists():raise ValueError('Export destination already exists; choose a new file')
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',encoding='utf-8',newline='\n')as stream:
  stream.write('# Model '+mid+'\n# Coordinates: '+m['coordinates']+'\n# '+m['role']+'\n# Physical units and anatomical acceptance uncalibrated.\n')
  for xyz in struct.iter_unpack(fmt,p):stream.write('v '+' '.join(repr(v)for v in xyz)+'\n')
  for a,b,c in struct.iter_unpack('<III',t):
   if max(a,b,c)>=count:raise ValueError('Triangle index outside model')
   stream.write(f'f {a+1} {b+1} {c+1}\n')
 return {'model':mid,'path':str(path),'vertices':count,'triangles':len(t)//12,'export':'complete decoded geometry for this registered representation; no textures or rig'}
def inspect(mid,sections=0):
 import numpy as np
 m,raw_p,raw_t=read_model(mid);dtype='<f8'if m['geometry']['positions']['dtype']=='float64-le'else'<f4'
 p=np.frombuffer(raw_p,dtype=dtype).reshape(-1,3);t=np.frombuffer(raw_t,dtype='<u4').reshape(-1,3)
 if not len(p)or not len(t)or not np.isfinite(p).all()or t.max()>=len(p):raise ValueError('Nonfinite/empty/out-of-range model geometry')
 ids=np.unique(t);used=p[ids].astype(np.float64);lo,hi=used.min(0),used.max(0);area=0.;zero_area=0
 for start in range(0,len(t),100000):
  q=p[t[start:start+100000]].astype(np.float64);a=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)*.5;area+=float(a.sum());zero_area+=int((a==0).sum())
 result={'model':mid,'vertices':len(p),'triangles':len(t),'referenced_vertices':len(ids),'finite':True,'referenced_bounds':{'min':lo.tolist(),'max':hi.tolist(),'span':(hi-lo).tolist()},'whole_asset_surface_area_coordinate_units_squared':area,'coordinate_unit_kind':m.get('decoded_coordinate_unit_kind','unregistered_asset_units'),'zero_area_triangles':zero_area,'coordinates':m['coordinates'],'role':m['role'],'registration':m['registration'],'anatomical_metrics':None,'anatomical_volume':None,'physical_unit_calibration':None,'source_position_sha256':digest(raw_p),'source_triangle_sha256':digest(raw_t),'scope':'Full retained representation in declared coordinates; includes unsegmented accessories. No anatomical height/width/circumference or tissue volume is inferred.'}
 if m.get('source_to_canonical_rest'):
  matrix=np.asarray(m['source_to_canonical_rest']['matrix_row_major']).reshape(4,4);canonical=used@matrix[:3,:3].T+matrix[:3,3];clo,chi=canonical.min(0),canonical.max(0);result['canonical_rest_referenced_bounds']={'min':clo.tolist(),'max':chi.tolist(),'span':(chi-clo).tolist()};result['canonical_stature_adapter_applied_to_report_only']=True
 if sections:
  if not 2<=sections<=25:raise ValueError('Section count must be 2…25')
  records=[]
  for y in np.linspace(lo[1],hi[1],sections):
   samples=[]
   for start in range(0,len(t),100000):
    tri=p[t[start:start+100000]].astype(np.float64);mask=(tri[:,:,1].min(1)<=y)&(tri[:,:,1].max(1)>=y);tri=tri[mask]
    for a,b in [(0,1),(1,2),(2,0)]:
     v,w=tri[:,a],tri[:,b];dy=w[:,1]-v[:,1];cross=((v[:,1]-y)*(w[:,1]-y)<=0)&(dy!=0);v,w,dy=v[cross],w[cross],dy[cross]
     if len(v):samples.append(v+(w-v)*((y-v[:,1])/dy)[:,None])
   q=np.concatenate(samples)if samples else np.zeros((0,3));records.append({'source_y':float(y),'intersection_samples':len(q),'axis_x_span':float(np.ptp(q[:,0]))if len(q)else None,'axis_z_span':float(np.ptp(q[:,2]))if len(q)else None,'circumference':None,'scope':'Actual triangle-plane intersections; contour loops and anatomy labels unreviewed'})
  result['source_y_sections']=records
 return result
def main():
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
 sub.add_parser('list');verify=sub.add_parser('verify');verify.add_argument('--out',type=Path)
 one=sub.add_parser('inspect');one.add_argument('--id',required=True);one.add_argument('--sections',type=int,default=0);one.add_argument('--out',type=Path)
 export=sub.add_parser('export');export.add_argument('--id',required=True);export.add_argument('--out',type=Path,required=True)
 args=parser.parse_args()
 if args.command=='list':result={'models':[{'id':m['id'],'label':m['label'],'role':m['role'],'coordinates':m['coordinates']}for m in catalog()['models']]}
 elif args.command=='export':result=export_obj(args.id,args.out)
 elif args.command=='inspect':result=inspect(args.id,args.sections)
 else:result={'passed':True,'models':[inspect(m['id'])for m in catalog()['models']],'scope':'Decoded hashes, finite positions, valid indices, full representation bounds and geometric area; no registration/anatomical accuracy claim'}
 if getattr(args,'out',None)and args.command!='export':
  target=args.out.resolve()
  if target.is_relative_to((ROOT/'models').resolve())or target.is_relative_to((ROOT/'data').resolve()):raise ValueError('Report destination must not overwrite immutable model/storage data')
  target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result if args.command!='verify'else{'passed':True,'models':len(result['models']),'out':str(args.out)},indent=2))
if __name__=='__main__':main()
