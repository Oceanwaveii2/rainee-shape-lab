"""Preserve supplied files and derive geometry-only, unregistered measurements.
Never execute scripts or instructions from the supplied archive.
"""
from pathlib import Path, PurePosixPath
from concurrent.futures import ThreadPoolExecutor
import argparse, hashlib, importlib.util, json, subprocess, zipfile, shutil, time
import numpy as np
from PIL import Image, ImageDraw
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

APP=Path(__file__).resolve().parents[1]
OUT=APP/'measurements/canonical-20261014'
ARCHIVE=Path('C:/Users/User/Downloads/CanonicalShapeReferencePack_20261014.zip')
VIDEO_NAMES=['高清（4K） (5).mp4','高清（4K） (6).mp4','高清（4K） (4).mp4','高清（1080P） (1).mp4','高清（1080P） (2).mp4','高清（4K） (3).mp4','高清（1080P）.mp4','视频节点 3 (1).mp4']

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def bounds(p):
 lo=p.min(0);hi=p.max(0)
 return {'min':lo.tolist(),'max':hi.tolist(),'extent':(hi-lo).tolist()}
def glb_reader():
 path=APP/'measurements/five-frame-20261013/sequence_reader.py'
 spec=importlib.util.spec_from_file_location('review_glb_reader',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 return mod.GLBReader
def describe_geometry(p,t,component_path=None):
 tri=p[t];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);areas=np.linalg.norm(cross,axis=1)*.5
 edges=np.vstack([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);direction=np.where(edges[:,0]<edges[:,1],1,-1);edges.sort(axis=1)
 unique,inverse,count=np.unique(edges,axis=0,return_inverse=True,return_counts=True)
 sums=np.bincount(inverse,weights=direction);boundary=int((count==1).sum());nonmanifold=int((count>2).sum());inconsistent=int(((count==2)&(sums!=0)).sum())
 graph=coo_matrix((np.ones(len(unique),dtype=np.uint8),(unique[:,0],unique[:,1])),shape=(len(p),len(p))).tocsr()
 _,ids=connected_components(graph,directed=False)
 if component_path is not None:ids.astype('<u4').tofile(component_path)
 used=np.unique(t);used_labels=np.unique(ids[used]);parts=[]
 for label in used_labels:
  mask=ids[t[:,0]]==label;pp=p[np.unique(t[mask])]
  parts.append({'indexed_component':int(label),'vertices':len(pp),'triangles':int(mask.sum()),'bounds':bounds(pp),'semantic_label':'unclassified; body/prop review required'})
 parts.sort(key=lambda x:-x['triangles'])
 sections=[];lo=p.min(0);extent=np.ptp(p,axis=0)
 for fraction in np.linspace(.05,.95,19):
  y=float(lo[1]+fraction*extent[1]);hit=[]
  for a,b in [(0,1),(1,2),(2,0)]:
   va,vb=tri[:,a],tri[:,b];mask=((va[:,1]<=y)&(vb[:,1]>y))|((vb[:,1]<=y)&(va[:,1]>y))
   if mask.any():
    aa=va[mask];bb=vb[mask];hit.append(aa+((y-aa[:,1])/(bb[:,1]-aa[:,1]))[:,None]*(bb-aa))
  q=np.concatenate(hit) if hit else np.empty((0,3))
  sections.append({'fraction_of_full_asset_y_extent':float(fraction),'source_y':y,'intersection_count':len(q),'bounds':bounds(q) if len(q) else None,'scope':'all scene geometry; not an anatomical region'})
 closed=boundary==0 and nonmanifold==0 and inconsistent==0
 volume=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
 return {'vertices':len(p),'triangles':len(t),'finite':bool(np.isfinite(p).all()),'bounds':bounds(p),'surface_area_source_units_squared':float(areas.sum()),'degenerate_triangles':int((areas<=1e-18).sum()),'topology':{'closed_indexed_surface':closed,'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'inconsistent_edges':inconsistent,'indexed_components':len(parts),'limits':'Indexed connectivity; UV/material seams may split a continuous physical surface. No positional welding or self-intersection certification.'},'signed_surface_volume_source_units_cubed':volume if closed else None,'volume_scope':'Whole asset surface integral only when closed; includes props and overlapping shells; not anatomical union/tissue volume.','components':parts,'source_y_sections':sections,'coordinate_status':'Original GLB scene world coordinates. Axis semantics and stature landmarks unreviewed.','anatomical_volume':None,'canonical_height_registration':False,'camera_registration':False,'regions_registered':False}
def ingest_archive():
 OUT.mkdir(parents=True,exist_ok=True);full=OUT/'full';full.mkdir(exist_ok=True)
 original_hash=sha(ARCHIVE);rows=[]
 with zipfile.ZipFile(ARCHIVE) as z:
  supplied=json.loads(z.read('documentation/manifest.json'))
  for i in z.infolist():
   rel=PurePosixPath(i.filename)
   if rel.is_absolute() or '..' in rel.parts or '\\' in i.filename or ':' in i.filename:raise ValueError('Unsafe archive path')
   if (i.external_attr>>16)&0o170000==0o120000:raise ValueError('Archive symlink unsupported')
   if i.is_dir():continue
   dest=full.joinpath(*rel.parts);dest.parent.mkdir(parents=True,exist_ok=True)
   if not dest.exists():
    with z.open(i) as source,dest.open('xb') as target:shutil.copyfileobj(source,target)
   digest=sha(dest);decl=next((a for a in supplied['files'] if a['archive_path']==i.filename),None)
   if decl and digest!=decl['sha256']:raise ValueError('Source hash mismatch '+i.filename)
   if dest.stat().st_size!=i.file_size:raise ValueError('Source byte count mismatch')
   rows.append({'archive_path':i.filename,'local_path':str(dest.resolve()),'bytes':i.file_size,'sha256':digest,'declared_hash_matches':bool(decl)})
 if sha(ARCHIVE)!=original_hash:raise ValueError('Archive changed')
 write(OUT/'local-source-manifest.json',{'schema':'rainee-canonical-local-archive-v1','archive_path':str(ARCHIVE),'archive_sha256':original_hash,'archive_bytes':ARCHIVE.stat().st_size,'all_files_retained':True,'scripts_executed':False,'files':rows,'pack_metadata_status':'Supplied reference data, not a new instruction or automatic authority override.'})
 return supplied,full
def ingest_models(supplied,full):
 Reader=glb_reader();models=[]
 for ref in supplied['references']:
  rid=ref['id'];folder=full/ref['associated_asset_folder']
  candidates=[p for p in folder.glob('*.glb') if 'segmented' not in p.name]
  if len(candidates)!=1:raise ValueError('Choose explicit primary GLB '+rid)
  source=candidates[0];digest=sha(source);reader=Reader(source);p,t,uv,material=reader.mesh();dest=OUT/'derived'/rid;dest.mkdir(parents=True,exist_ok=True)
  p.astype('<f4').tofile(dest/'positions.bin');t.astype('<u4').tofile(dest/'triangles.bin');material.astype('<i4').tofile(dest/'triangle-material-ids.bin')
  info=describe_geometry(p.astype(float),t,dest/'vertex-component-ids.bin');info['vertex_component_ids']='vertex-component-ids.bin';info.update({'id':rid,'source_primary_glb':str(source.resolve()),'source_sha256':digest,'source_bytes':source.stat().st_size,'geometry_only':True,'geometry_decimated':False,'uv_and_textures_omitted':True,'source_precision':'GLB positions and scene transforms baked to float32 world positions; triangle connectivity retained.','position_sha256':sha(dest/'positions.bin'),'triangle_sha256':sha(dest/'triangles.bin'),'source_scene':reader.metadata(),'pack_declared_role':ref['role'],'pack_declared_authority':ref['authority'],'authority_status':'Declaration supplied in archive. Existing direct chat instructions remain authoritative. No baseline/face/stature override adopted.'})
  write(dest/'measurements.json',info)
  for category in ['positions','triangles','triangle-material-ids']:
   dtype='<f4' if category=='positions' else '<u4' if category=='triangles' else '<i4'
   assert np.array_equal(np.fromfile(dest/(category+'.bin'),dtype=dtype),{'positions':p.astype('<f4').ravel(),'triangles':t.astype('<u4').ravel(),'triangle-material-ids':material.astype('<i4')}[category])
  assert sha(source)==digest
  refpath=full/ref['archive_path']
  with Image.open(refpath) as im:dimensions=list(im.size)
  row={'id':rid,'label':ref['associated_asset_folder'].replace('_20261014',''),'reference_file':ref['archive_path'],'reference_sha256':sha(refpath),'reference_image_size':dimensions,'positions':f'derived/{rid}/positions.bin','triangles':f'derived/{rid}/triangles.bin','measurements':f'derived/{rid}/measurements.json','vertices':len(p),'triangle_count':len(t),'source_bounds':info['bounds'],'pack_declared_role':ref['role'],'reviewed_anatomical_regions':False,'scale_registration':False};models.append(row)
  print(f'{rid}: {len(p):,} vertices / {len(t):,} triangles; all geometry retained',flush=True)
 write(OUT/'models.json',{'schema':'rainee-canonical-geometry-only-v1','models':models,'height_anchor':'Existing FBX stature 2.3951061964035034 source units; donor bounds are not stature.','roles_reviewed':False,'larger_build_pair':'Not explicitly mapped by the current request. R03/R04 descriptions suggest candidates only. All four builds are retained.'})
def probe_video(item):
 vid,path=item;raw=subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)])
 data=json.loads(raw);streams=[s for s in data['streams'] if s['codec_type']=='video'];s=streams[0]
 return {'id':vid,'local_path':str(path),'source_filename':path.name,'bytes':path.stat().st_size,'sha256':sha(path),'probe':data,'duration_seconds':float(data['format']['duration']),'width':s['width'],'height':s['height'],'frame_rate':s.get('avg_frame_rate'),'asset_association':'unassigned; filename does not establish a character or canonical stage','camera_calibration':False,'shape_approval':'unassigned; original post0026 drift remains rejected for the older accepted growth sequence'}
def ingest_videos():
 sources=[(f'V{i+1:02}',Path('C:/Users/User/Downloads')/name) for i,name in enumerate(VIDEO_NAMES)]
 with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(probe_video,sources))
 for row in rows:
  dest=OUT/'videos'/row['id'];dest.mkdir(parents=True,exist_ok=True);source=Path(row['local_path']);duration=row['duration_seconds']
  lean=dest/'review.mp4'
  if not lean.exists():
   subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-i',str(source),'-map','0:v:0','-an','-vf',"scale=w='min(720,iw)':h=-2:flags=lanczos,fps=12",'-c:v','libx264','-preset','fast','-crf','29','-maxrate','400k','-bufsize','800k','-pix_fmt','yuv420p','-movflags','+faststart',str(lean)],check=True)
  pictures=[];timestamps=[]
  for j,fraction in enumerate([0,.25,.5,.75,.98]):
   timestamp=duration*fraction;picture=dest/f'frame-{j}.jpg';timestamps.append(timestamp)
   if not picture.exists():subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-nostdin','-ss',str(timestamp),'-i',str(source),'-frames:v','1','-vf',"scale=w='min(480,iw)':h=-2:flags=lanczos",'-q:v','3',str(picture)],check=True)
   pictures.append(Image.open(picture).convert('RGB'))
  width=sum(im.width for im in pictures);height=max(im.height for im in pictures)+44
  sheet=Image.new('RGB',(width,height),'#161b25');draw=ImageDraw.Draw(sheet);x=0
  for im,ts in zip(pictures,timestamps):
   sheet.paste(im,(x,44));draw.text((x+8,8),f"{row['id']} | {ts:.3f}s",fill='white');x+=im.width
  sheet.save(dest/'contact-sheet.jpg',quality=86)
  row['lean_review']={'path':f"videos/{row['id']}/review.mp4",'bytes':lean.stat().st_size,'sha256':sha(lean),'transform':'full-duration, uncropped proportional resize <=720px wide, 12fps H.264, audio omitted','source_unchanged':sha(source)==row['sha256'],'duration_seconds':float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(lean)]))['format']['duration'])}
  row['sample_frames']=[{'source_timestamp_seconds':ts,'path':f"videos/{row['id']}/frame-{j}.jpg",'source_time_base':row['probe']['streams'][0].get('time_base'),'sampling':'five inspection samples; not a complete motion analysis'} for j,ts in enumerate(timestamps)]
  row['contact_sheet']=f"videos/{row['id']}/contact-sheet.jpg"
  print(f"{row['id']}: {duration:.3f}s, {row['width']}x{row['height']}; review {lean.stat().st_size/1e6:.2f} MB",flush=True)
 write(OUT/'videos.json',{'schema':'rainee-video-review-telemetry-v1','videos':rows,'all_originals_retained_at_local_paths':True,'source_geometry_or_camera_inferred':False})
 return rows
def main():
 start=time.time();supplied,full=ingest_archive();print('75 source files extracted and verified; source scripts not executed',flush=True);ingest_models(supplied,full);ingest_videos();print(f'Ingest complete in {time.time()-start:.1f}s',flush=True)
if __name__=='__main__':main()
