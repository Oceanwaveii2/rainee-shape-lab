"""Build an isolated <=100,000,000-byte source/geometry review repository.
Full local sources stay unchanged. No GitHub writes or source deletion here.
"""
from pathlib import Path
import gzip,hashlib,json,shutil,struct,sys,time
import numpy as np
from PIL import Image
APP=Path(__file__).resolve().parents[1]
DEST=Path('C:/Users/User/Downloads/Rainee-GitHub-Review-20261014')
SOURCE=APP/'measurements/canonical-20261014'
LIMIT=100_000_000
TEXT={'.py','.js','.mjs','.html','.css','.json','.md','.txt','.vfl','.glsl','.cmd'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def put(relative,raw):
 p=DEST/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
def dump(relative,value):put(relative,json.dumps(value,indent=2,ensure_ascii=False).encode('utf-8'))
def build():
 DEST.mkdir(parents=True,exist_ok=True);entries={};images={};inventory=[]
 def compress(payload,indices=False):
  variants=[('bytes',gzip.compress(payload,compresslevel=6,mtime=0))]
  if len(payload)%4==0:
   shuffled=np.frombuffer(payload,dtype=np.uint8).reshape(-1,4).T.copy().tobytes();variants.append(('shuffle32',gzip.compress(shuffled,compresslevel=6,mtime=0)))
   if indices:
    values=np.frombuffer(payload,dtype='<u4').astype(np.int64);delta=np.diff(values,prepend=0)
    if np.max(np.abs(delta))<0x7fffffff:
     zz=((delta<<1)^(delta>>31)).astype('<u4');shuffled=zz.view(np.uint8).reshape(-1,4).T.copy().tobytes();variants.append(('delta-zigzag-shuffle32',gzip.compress(shuffled,compresslevel=6,mtime=0)))
  return min(variants,key=lambda x:len(x[1]))
 def encode(path,base=None):
  rel=path.relative_to(APP).as_posix();raw=path.read_bytes();payload=raw;codec='gzip';meta={};encoding,packed=compress(raw,'triangles' in path.name)
  if base is not None:
   braw=base.read_bytes()
   if len(raw)==len(braw) and len(raw)%12==0:
    bits=np.frombuffer(raw,dtype='<u4').reshape(-1,3);bbits=np.frombuffer(braw,dtype='<u4').reshape(-1,3);ids=np.flatnonzero(np.any(bits!=bbits,axis=1)).astype('<u4')
    sparse=struct.pack('<4sII',b'RSP1',len(bits),len(ids))+ids.tobytes()+bits[ids].tobytes()
    se,sp=compress(sparse)
    if len(sp)<len(packed):encoding,packed=se,sp;codec='sparse-point-f32';meta={'base':base.relative_to(APP).as_posix(),'changed_vertices':len(ids)}
  storage=f'data/blobs/{sha(packed)}.gz';put(storage,packed)
  entries[rel]={'codec':codec,'encoding':encoding,'storage':storage,'decoded_bytes':len(raw),'decoded_sha256':sha(raw),'stored_bytes':len(packed),'stored_sha256':sha(packed),**meta}
 def copy_image(path,relative=None):
  raw=path.read_bytes();digest=sha(raw);route=path.relative_to(APP).as_posix();target=relative or route
  if digest in images:
   entries[route]={'codec':'file','storage':images[digest],'decoded_bytes':len(raw),'decoded_sha256':digest,'stored_bytes':len(raw),'stored_sha256':digest}
  else:put(target,raw);images[digest]=target
  if target!=route:entries[route]={'codec':'file','storage':images[digest],'decoded_bytes':len(raw),'decoded_sha256':digest,'stored_bytes':len(raw),'stored_sha256':digest}
 def remove_old_source_copy(path):
  rel=path.relative_to(APP);target=(DEST/rel).resolve()
  if not target.is_relative_to(DEST.resolve()):raise ValueError('Export deletion outside owned root')
  if target.is_file():
   if sha(target.read_bytes())!=sha(path.read_bytes()):raise ValueError('Unexpected export file content before prune '+str(rel))
   target.unlink()
 # Source, numerical telemetry and evidence. Supplied full archive is data only.
 for p in APP.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(APP);s=rel.as_posix()
  if any(part in {'__pycache__','.git','node_modules'} for part in rel.parts):continue
  if s.startswith('measurements/canonical-20261014/full/'):continue
  if p.suffix.lower() in TEXT:put(s,p.read_bytes())
 # Preserve original face/anatomy references, including explicit rejected-frame evidence.
 secondary={'front-detail.png','front-scene.png','rear-style.png'}
 for folder in ['references','measurements/face-identity-20261013','research/thigh-reference-review']:
  for p in (APP/folder).rglob('*'):
   if p.is_file() and p.suffix.lower() in {'.png','.jpg','.webp'}:
    if p.name in secondary and p.parent==APP/'references':
     target=f'references/secondary/{p.stem}.jpg';(DEST/target).parent.mkdir(parents=True,exist_ok=True)
     with Image.open(p) as im:im.convert('RGB').save(DEST/target,quality=91,subsampling=0)
     remove_old_source_copy(p)
    else:copy_image(p)
 # One older growth inspection frame is shown by the working editor. The full
 # chronology remains local; the four user-accepted original references are above.
 rear=APP/'research/rear-growth-review'
 for p in rear.glob('*.png'):
  if p.name=='grok-01-0.500s.png':copy_image(p)
  else:remove_old_source_copy(p)
 for rid in ['R01','R02','R03','R04']:
  p=next((SOURCE/'full/references'/rid).glob('*.png'));copy_image(p,f'references/canonical/{rid}.png')
 # Dependencies: the locally vendored Three.js/Spark files plus their licenses.
 for p in (APP/'vendor').rglob('*'):
  if p.is_file() and (p.suffix.lower() in {'.js','.json','.txt','.md'} or p.name=='LICENSE'):put(p.relative_to(APP).as_posix(),p.read_bytes())
 # All 27 exact native cache frames and four original rounded states. Sparse payloads
 # encode actual float32 bits; no interpolation/quantization changes are introduced.
 baseline=APP/'houdini/body-v4-rest.bin'
 required=['houdini/body-v4-rest.bin','houdini/pelvic-repair/implicit-repaired-triangles.bin','houdini/cage-rest.bin','houdini/cage-triangles.bin','houdini/body-figurine-native.bin','research/rear-rounding/native-study/body-triangles.bin','research/rear-rounding/native-study/cage-triangles.bin']
 for rel in required:
  p=APP/rel
  if p.exists():encode(p,baseline if 'body-' in p.name and p!=baseline else None)
 for p in (APP/'research/rear-rounding/native-study').glob('*.bin'):
  if p.name.startswith(('body-native-flow-','cage-native-flow-')):encode(p,baseline if p.name.startswith('body-') else None)
 for p in (APP/'research/rear-rounding/native-study/accepted-sequence').glob('*.bin'):encode(p,baseline if p.name.startswith('body-') else None)
 # Existing donor inspection proxies retain their original source coordinates.
 for folder in ['measurements/five-frame-20261013','measurements/reference-01a13749']:
  for p in (APP/folder).rglob('preview-*.bin'):encode(p)
 for p in (SOURCE/'derived').rglob('*.bin'):encode(p)
 for p in (SOURCE/'videos').rglob('*'):
  if p.is_file() and p.suffix in {'.mp4','.jpg'}:
   if p.name.startswith('frame-'):
    remove_old_source_copy(p)
   else:put(p.relative_to(APP).as_posix(),p.read_bytes())
 # Native regional HIP is self contained beside its small OBJ imports.
 native=APP/'houdini/lab/native-proposal'
 for p in native.iterdir():
  if p.is_file() and p.suffix in {'.hip','.obj'}:put(p.relative_to(APP).as_posix(),p.read_bytes())
 # Other HIPs depend on heavy local caches. Source scripts and verification stay
 # in the review; the complete HIPs stay available in the full local project.
 for p in APP.rglob('*.hip'):
  if 'full' not in p.relative_to(APP).parts and native not in p.parents:remove_old_source_copy(p)
 # Compact visual evidence of paused implementation.
 for p in (APP/'houdini/lab').glob('*.png'):copy_image(p)
 put('serve.py',(APP/'tools/lean_server.py').read_bytes())
 dump('data/asset-map.json',{'schema':'rainee-lossless-asset-map-v1','assets':entries,'description':'Virtual source URLs restored byte-exactly by serve.py; data/blobs are ordinary gzip or RSP1 sparse-point float32 payloads.'})
 # Prune only obsolete generated blobs in this explicit export directory. Sources
 # and unrelated checkout files are never targets of a delete or a Git add.
 if DEST.resolve()!=Path('C:/Users/User/Downloads/Rainee-GitHub-Review-20261014').resolve():raise ValueError('Export root mismatch')
 retained={v['storage'] for v in entries.values()}
 for old in (DEST/'data/blobs').glob('*.gz'):
  if old.relative_to(DEST).as_posix() not in retained and len(old.stem)==64 and all(c in '0123456789abcdef' for c in old.stem):old.unlink()
 dump('documentation/local-data-map.json',{'schema':'rainee-full-local-lookup-v1','full_project_root':str(APP),'new_full_archive_root':str(SOURCE/'full'),'original_archive':'C:/Users/User/Downloads/CanonicalShapeReferencePack_20261014.zip','original_fbx':'C:/Users/User/Downloads/Core Body (Template Only).fbx','local_manifest':'measurements/canonical-20261014/local-source-manifest.json','video_manifest':'measurements/canonical-20261014/videos.json','rule':'Read full local data via these mappings; no original sources are deleted or replaced. Large archive, textures, original videos, OBJ duplicates, native caches and full Gaussian scenes remain local.','new_archive_integrity':json.loads((SOURCE/'local-source-manifest.json').read_text(encoding='utf-8'))['archive_sha256']})
 # Public nav points to included resources. No anatomy/solver algorithm is changed.
 p=DEST/'houdini/lab/index.html';s=p.read_text(encoding='utf-8').replace('../../research/gaussian-growth/index.html','../../documentation/LOCAL_DATA.md').replace('Gaussian deformation</a>','Local Gaussian data</a>');p.write_text(s,encoding='utf-8')
 for p in DEST.rglob('*'):
  if p.is_file() and p.suffix in {'.html','.js','.mjs'}:
   s=p.read_text(encoding='utf-8')
   for name in secondary:s=s.replace(name,'secondary/'+Path(name).stem+'.jpg')
   p.write_text(s,encoding='utf-8')
 p=DEST/'houdini/authoring.js';s=p.read_text(encoding='utf-8');start=s.index("$('#hip-link').href=");end=s.index(";if(mode==='sequence')",start);s=s[:start]+"$('#hip-link').href='../documentation/LOCAL_DATA.md';$('#hip-link').textContent='Native scenes and local data ↗'"+s[end:];p.write_text(s,encoding='utf-8')
 # Remove accidental interpreter artifacts from deterministic file budget.
 total=sum(p.stat().st_size for p in DEST.rglob('*') if p.is_file() and '.git' not in p.relative_to(DEST).parts)
 if total>=LIMIT:raise ValueError(f'Review bundle exceeds strict 100 MB budget: {total:,}')
 stats={'schema':'rainee-lean-budget-v1','limit_decimal_bytes':LIMIT,'working_tree_bytes_before_docs':total,'virtual_asset_routes':len(entries),'stored_blobs':len(list((DEST/'data/blobs').glob('*.gz'))),'lossless_float32_cache_and_geometry':True,'original_images_uncropped':True,'full_local_data_kept':True,'source_project_root':str(APP),'review_root':str(DEST),'new_3d_meshes_decimated':False}
 dump('documentation/build-budget.json',stats);print(json.dumps(stats,indent=2),flush=True)
if __name__=='__main__':build()
