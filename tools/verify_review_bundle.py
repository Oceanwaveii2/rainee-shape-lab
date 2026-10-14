"""Check a generated lean bundle against the full local source; no publication."""
from pathlib import Path
from functools import lru_cache
import argparse,hashlib,importlib.util,json,time,urllib.request
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
 for route,entry in entries.items():
  raw=load(route);original=source/route
  assert original.is_file(),route
  assert hashlib.sha256(raw).hexdigest()==sha(original),route
  checked.append({'route':route,'sha256':entry['decoded_sha256'],'bytes':len(raw),'codec':entry['codec'],'encoding':entry.get('encoding','bytes'),'matches_full_local_bytes':True})
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
 report={'schema':'rainee-review-package-verification-v1','passed':True,'strict_budget_decimal_bytes':100000000,'virtual_routes_restored_exactly':len(checked),'decoded_assets':checked,'archive_files_retained_verified':len(retained['files']),'archive_hash_unchanged':True,'original_videos_retained_verified':len(videos),'review_duration_within_one_12fps_frame':True,'new_meshes_decimated':False,'source_coordinate_or_index_bits_modified_by_compression':False,'http_checks':http,'elapsed_seconds':time.time()-start,'scope':'Lossless package/source integrity, review duration and actual HTTP restoration. Browser rendering is recorded separately; anatomical likeness/registration/physics are not certified.'}
 dest=root/'documentation/package-verification.json';dest.write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='decoded_assets'},indent=2))
if __name__=='__main__':main()
