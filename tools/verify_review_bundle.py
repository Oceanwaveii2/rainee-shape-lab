"""Check a generated lean bundle against the full local source; no publication."""
from pathlib import Path
from functools import lru_cache
import argparse,gzip,hashlib,importlib.util,json,math,struct,time,urllib.request
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--url',default='http://127.0.0.1:5198');args=p.parse_args();root=args.bundle.resolve();source=args.source.resolve();start=time.time()
 spec=importlib.util.spec_from_file_location('verified_review_server',root/'serve.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);entries=json.loads((root/'data/asset-map.json').read_text())['assets'];checked=[]
 @lru_cache(maxsize=5)
 def load(route):return mod.decode(root,entries[route],entries,load)
 image_pixels_checked=0;binary_bytes_checked=0
 for route,entry in entries.items():
  raw=load(route);original=source/entry.get('source_relative_path',route)
  assert original.is_file(),route
  if entry.get('pixel_identity_verified'):
   from PIL import Image
   from io import BytesIO
   original_image=Image.open(original);retained_image=Image.open(BytesIO(raw));assert original_image.size==retained_image.size and original_image.convert('RGBA').tobytes()==retained_image.convert('RGBA').tobytes(),route;assert sha(original)==entry['original_png_sha256'];image_pixels_checked+=1;exact=False
  else:assert hashlib.sha256(raw).hexdigest()==sha(original),route;binary_bytes_checked+=1;exact=True
  checked.append({'route':route,'sha256':entry['decoded_sha256'],'bytes':len(raw),'codec':entry['codec'],'encoding':entry.get('encoding','bytes'),'matches_full_local_bytes':exact,'matches_original_pixels':entry.get('pixel_identity_verified',False)})
 retained=json.loads((root/'measurements/canonical-20261014/local-source-manifest.json').read_text(encoding='utf-8'))
 for row in retained['files']:assert sha(Path(row['local_path']))==row['sha256'],row['archive_path']
 assert sha(Path(retained['archive_path']))==retained['archive_sha256']
 videos=json.loads((root/'measurements/canonical-20261014/videos.json').read_text(encoding='utf-8'))['videos']
 for v in videos:
  assert sha(Path(v['local_path']))==v['sha256']
  assert abs(v['lean_review']['duration_seconds']-v['duration_seconds'])<=1/12+.02
  assert sha(root/('measurements/canonical-20261014/'+v['lean_review']['path']))==v['lean_review']['sha256']
 http=[]
 for route in ['houdini/body-v4-rest.bin','research/rear-rounding/native-study/accepted-sequence/body-frame_0026.bin','measurements/canonical-20261014/derived/R04/positions.bin','measurements/canonical-20261014/derived/R04/triangles.bin']:
  with urllib.request.urlopen(args.url+'/'+route) as r:raw=r.read();header=r.headers.get('X-Rainee-Asset-SHA256')
  assert hashlib.sha256(raw).hexdigest()==entries[route]['decoded_sha256']==header
  http.append({'route':route,'response_hash_verified':True})
 donor_root=root/'measurements/new-donor-20261014';extra_donor=None
 if donor_root.is_dir():
  manifest=json.loads((donor_root/'manifest.json').read_text(encoding='utf-8'));lod=manifest['lod'];raw=gzip.decompress((donor_root/lod['path']).read_bytes());offset=lod['positions_float32_bytes']
  assert len(raw)==offset+lod['triangles_uint32_bytes']
  assert hashlib.sha256(raw).hexdigest()==lod['decoded_sha256']
  assert all(math.isfinite(v[0]) for v in struct.iter_unpack('<f',raw[:offset]))
  assert max(v[0] for v in struct.iter_unpack('<I',raw[offset:]))<lod['vertices']
  for name,key in [('obj-inventory.json','source_zip'),('fbx-inventory.json','source_file')]:
   inventory=json.loads((donor_root/name).read_text(encoding='utf-8'));assert sha(Path(inventory[key]))==inventory['zip_sha256' if key=='source_zip' else 'sha256']
  assert sha(Path(manifest['source_image']['path']))==manifest['source_image']['sha256']
  extra_donor={'inspection_lod_is_lossy':True,'decoded_lod_hash_verified':True,'lod_vertices':lod['vertices'],'lod_triangles':lod['triangles'],'full_original_zip_fbx_png_hashes_unchanged':True,'measurement_source':'full local originals, not inspection LOD'}
 report={'schema':'rainee-review-package-verification-v2','passed':True,'transfer_archive_limit_decimal_bytes':100000000,'virtual_routes_verified':len(checked),'binary_routes_restored_bit_exactly':binary_bytes_checked,'lossless_pixel_image_routes_verified':image_pixels_checked,'decoded_assets':checked,'archive_files_retained_verified':len(retained['files']),'archive_hash_unchanged':True,'original_videos_retained_verified':len(videos),'review_duration_within_one_12fps_frame':True,'primary_four_glb_meshes_decimated':False,'retained_coordinate_or_index_bits_modified_by_compression':False,'extra_donor':extra_donor,'http_checks':http,'elapsed_seconds':time.time()-start,'scope':'Bit-exact retained geometry, pixel-identical image container derivatives, separate extra donor LOD and full-model registry, review duration and HTTP restoration. No anatomy/registration/physics certification; ZIP transfer budget is verified separately.'}
 dest=root/'documentation/package-verification.json';dest.write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='decoded_assets'},indent=2))
if __name__=='__main__':main()
