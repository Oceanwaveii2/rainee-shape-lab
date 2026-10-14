"""Expand retained review assets outside the lean repository; optionally emit GLBs."""
from pathlib import Path,PurePosixPath
from functools import lru_cache
import argparse,importlib.util,json,struct

def write_glb(path,positions,triangles,report):
 if len(positions)%12 or len(triangles)%12:raise ValueError('XYZ/triangle alignment failure')
 doc={'asset':{'version':'2.0','generator':'Rainee geometry-only review exporter'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0}],'meshes':[{'name':report['id']+' full geometry only','primitives':[{'attributes':{'POSITION':0},'indices':1,'mode':4}]}],'buffers':[{'byteLength':len(positions)+len(triangles)}],'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':len(positions),'target':34962},{'buffer':0,'byteOffset':len(positions),'byteLength':len(triangles),'target':34963}],'accessors':[{'bufferView':0,'componentType':5126,'count':len(positions)//12,'type':'VEC3','min':report['bounds']['min'],'max':report['bounds']['max']},{'bufferView':1,'componentType':5125,'count':len(triangles)//4,'type':'SCALAR'}],'extras':{'original_primary_glb_sha256':report['source_sha256'],'positions_sha256':report['position_sha256'],'triangles_sha256':report['triangle_sha256'],'source_world_coordinates':True,'textures_and_uvs_omitted':True,'canonical_registered':False,'anatomical_volume':None}}
 data=json.dumps(doc,separators=(',',':')).encode();data+=b' '*(-len(data)%4);binary=positions+triangles;binary+=b'\x00'*(-len(binary)%4)
 path.write_bytes(struct.pack('<4sII',b'glTF',2,12+8+len(data)+8+len(binary))+struct.pack('<II',len(data),0x4e4f534a)+data+struct.pack('<II',len(binary),0x004e4942)+binary)
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry-glb',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[1];out=args.out.resolve()
 if out.is_relative_to(root.resolve()):raise ValueError('Expand outside the review repository to preserve its transfer budget')
 server=root/'serve.py';spec=importlib.util.spec_from_file_location('rainee_asset_server',server);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 entries=json.loads((root/'data/asset-map.json').read_text(encoding='utf-8'))['assets']
 @lru_cache(maxsize=5)
 def load(route):return mod.decode(root,entries[route],entries,load)
 for route in entries:
  rel=PurePosixPath(route)
  if rel.is_absolute() or '..' in rel.parts:raise ValueError('Invalid route')
  target=out.joinpath(*rel.parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(load(route))
 if args.geometry_glb:
  for rid in ['R01','R02','R03','R04']:
   base='measurements/canonical-20261014/derived/'+rid+'/';report=json.loads((root/(base+'measurements.json')).read_text(encoding='utf-8'));target=out/(rid+'-geometry-only.glb');write_glb(target,load(base+'positions.bin'),load(base+'triangles.bin'),report);print(target)
 print(f'{len(entries)} retained assets expanded to {out}; omitted full local assets not reconstructed.')
if __name__=='__main__':main()
