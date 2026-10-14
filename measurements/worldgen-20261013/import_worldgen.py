"""Bounded, data-only WorldGen archive inspection, payload deduplication and SPZ stats.

No .blend files are opened, executed or extracted. Original ZIPs remain read-only.
"""
from __future__ import annotations
import argparse,gzip,hashlib,io,json,stat,struct,zipfile
from pathlib import Path,PurePosixPath,PureWindowsPath
import numpy as np

HERE=Path(__file__).resolve().parent
NAMES=[
 'WorldGen-37454f46-f13b-40bf-aa5f-d6b4abda437d.zip',
 'WorldGen-76a46eb1-e415-49a2-bb91-3be79caa7dcd.zip',
 'WorldGen-6098cc79-65f3-4635-834a-82a324881aa1 (1).zip',
 'WorldGen-6098cc79-65f3-4635-834a-82a324881aa1.zip',
 'f9f63233-cc50-4a28-8c61-7c45affbdbbb.zip',
 'WorldGen-0bf4b058-d866-4995-a256-d64fe3cb01dc.zip',
 'WorldGen-6dfde300-424f-4eb0-89de-c1925ca67615.zip',
 'WorldGen-905f90ce-a0b6-420e-8cf9-a330b76035aa.zip',
 'WorldGen-83db5ca5-c31e-46ab-b886-67935fc362ac.zip']
SPEC='https://github.com/nianticlabs/spz'
MAX_ENTRY=256*1024*1024

def dump(name,data):
    target=HERE/name;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(data,indent=2),encoding='utf-8')
def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def safe_name(name):
    name=name.replace('\\','/');p=PurePosixPath(name);w=PureWindowsPath(name)
    if p.is_absolute() or w.is_absolute() or w.drive or '..' in p.parts or ':' in name or '\x00' in name:
        raise ValueError('Unsafe archive path')
    return str(p)
def bounded_read(archive,entry):
    if entry.file_size>MAX_ENTRY:raise ValueError('Entry exceeds bounded size')
    return archive.read(entry) # ZIP CRC validation occurs while reading.
def save_unique(path,data):
    path=path.resolve()
    if not path.is_relative_to(HERE):raise ValueError('Output outside importer subtree')
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if digest(path)!=hashlib.sha256(data).hexdigest():raise ValueError('Existing derived asset differs')
    else:path.write_bytes(data)

def legacy_raw(data):
    # Read at most 128 MB; a forged gzip expansion cannot consume unbounded RAM.
    with gzip.GzipFile(fileobj=io.BytesIO(data)) as stream:
        raw=stream.read(128*1024*1024+1)
        if len(raw)>128*1024*1024:raise ValueError('SPZ expansion exceeds bounded size')
    return raw
def spz_header(data):
    if data[:2]==b'\x1f\x8b':
        raw=legacy_raw(data)
        if len(raw)<16:raise ValueError('Truncated SPZ header')
        magic,version,n,degree,bits,flags,reserved=struct.unpack('<III4B',raw[:16])
        if magic!=0x5053474e or version not in (1,2,3) or degree>4 or bits>24 or reserved:
            raise ValueError('Unsupported or invalid legacy SPZ header')
        sh=(degree+1)**2-1;stride=(6 if version==1 else 9)+1+3+3+(4 if version>=3 else 3)+sh*3
        expected=16+n*stride
        if n>5_000_000 or len(raw)<expected:raise ValueError('SPZ point count/length invalid or above bounded inspection ceiling')
        return {'format':'legacy-gzip-SPZ','version':version,'num_points':n,'sh_degree':degree,
            'fractional_bits':bits,'flags':flags,'uncompressed_bytes':len(raw),
            'attribute_bytes_expected':expected,'trailing_bytes':len(raw)-expected,
            'raw_payload_sha256':hashlib.sha256(raw).hexdigest(),'storage_coordinate_convention':'RUB per Niantic default; producer semantics still reviewable'},raw
    if data[:4]==b'NGSP':
        if len(data)<32:raise ValueError('Truncated v4 SPZ header')
        _,version,n,degree,bits,flags,streams,toc=struct.unpack('<III4BI',data[:20])
        if version!=4 or n>5_000_000 or degree>4 or bits>24 or streams<1 or toc<32 or toc>len(data):
            raise ValueError('Unsupported or invalid SPZ v4 header')
        return {'format':'NGSP-ZSTD-SPZ','version':version,'num_points':n,'sh_degree':degree,
            'fractional_bits':bits,'flags':flags,'streams':streams,'toc_offset':toc,
            'stats_status':'Header only; v4 attribute decoding is delegated to renderer'},None
    raise ValueError('Unrecognized SPZ format')

def glb_summary(data):
    if len(data)<20:raise ValueError('Truncated GLB')
    magic,version,length=struct.unpack('<III',data[:12])
    if magic!=0x46546c67 or version!=2 or length!=len(data):raise ValueError('Invalid GLB header')
    n,kind=struct.unpack('<II',data[12:20])
    if kind!=0x4e4f534a or n>4*1024*1024:raise ValueError('Missing or oversized GLB JSON')
    document=json.loads(data[20:20+n].decode('utf-8').rstrip('\x00 '))
    primitives=[]
    for mesh in document.get('meshes',[]):
        for primitive in mesh.get('primitives',[]):
            pos=primitive.get('attributes',{}).get('POSITION');acc=document.get('accessors',[])[pos] if pos is not None else {}
            index=primitive.get('indices');indices=document.get('accessors',[])[index] if index is not None else {}
            primitives.append({'mesh_name':mesh.get('name'),'mode':primitive.get('mode',4),'position_count':acc.get('count'),
                'position_min':acc.get('min'),'position_max':acc.get('max'),'index_count':indices.get('count'),
                'extensions':list(primitive.get('extensions',{}))})
    return {'asset':document.get('asset'), 'nodes':[{'name':x.get('name'),'mesh':x.get('mesh'),'camera':x.get('camera'),
        'translation':x.get('translation'),'rotation':x.get('rotation'),'scale':x.get('scale')} for x in document.get('nodes',[])],
        'primitives':primitives,'cameras':document.get('cameras',[]),'extensions_used':document.get('extensionsUsed',[]),
        'scope':'Environment collider geometry metadata, not a validated body or closed anatomical volume'}

def scan(downloads,names=None):
    records=[];payloads={};spz_ids={};collider_ids={}
    for name in names or NAMES:
        source=downloads/name;record={'archive':str(source.resolve()),'archive_name':name,'archive_bytes':source.stat().st_size,
            'archive_sha256':digest(source),'entries':[],'frame_mapping_status':'unmapped: no explicit input-frame provenance found'}
        with zipfile.ZipFile(source) as archive:
            seen=set();total=0
            for entry in archive.infolist():
                normal=safe_name(entry.filename);resolved=(HERE/'assets'/normal).resolve()
                if not resolved.is_relative_to(HERE/'assets'):raise ValueError('Archive traversal')
                if normal.casefold() in seen:raise ValueError('Archive duplicate target')
                seen.add(normal.casefold());total+=entry.file_size
                if stat.S_ISLNK(entry.external_attr>>16):raise ValueError('Archive symlink')
                if entry.file_size>MAX_ENTRY or total>512*1024*1024:raise ValueError('Archive exceeds bounded data limit')
                row={'name':normal,'bytes':entry.file_size,'compressed_bytes':entry.compress_size,'zip_crc32':f'{entry.CRC:08x}',
                    'extension':Path(normal).suffix.lower(),'extracted':False}
                if entry.is_dir():record['entries'].append(row);continue
                # Inspect only documented data assets. .blend metadata is inventoried
                # but Blender scene contents are neither opened nor extracted.
                if row['extension'] in ('.spz','.glb','.json','.obj','.png'):
                    data=bounded_read(archive,entry);sha=hashlib.sha256(data).hexdigest();row['sha256']=sha
                    payloads.setdefault(sha,[]).append({'archive':name,'entry':normal})
                    if row['extension']=='.json':
                        if len(data)>1024*1024:raise ValueError('Metadata JSON exceeds inspection bound')
                        row['metadata_as_data']=json.loads(data.decode('utf-8-sig'))
                        target=HERE/'cameras'/f'{source.stem}.json';save_unique(target,data);row['extracted_path']=target.relative_to(HERE).as_posix();row['extracted']=True
                        matrix=np.asarray(row['metadata_as_data'],dtype=float) if isinstance(row['metadata_as_data'],list) else np.zeros((0,))
                        if matrix.shape==(4,4):
                            row['camera_matrix_check']={'shape':[4,4],'finite':bool(np.isfinite(matrix).all()),
                                'rotation_determinant':float(np.linalg.det(matrix[:3,:3])),
                                'orthogonality_max_error':float(np.abs(matrix[:3,:3]@matrix[:3,:3].T-np.eye(3)).max()),
                                'interpretation':'4x4 transform only; c2w/w2c direction and intrinsics are not declared. No exact reference-camera claim.'}
                    elif row['extension']=='.spz':
                        if sha not in spz_ids:
                            spz_id=f'spz-{len(spz_ids):02d}-{sha[:10]}';header,_=spz_header(data)
                            target=HERE/'assets'/spz_id/'full_res.spz';save_unique(target,data)
                            spz_ids[sha]={'id':spz_id,'sha256':sha,'header':header,'path':target.relative_to(HERE).as_posix(),'sources':[]}
                        spz_ids[sha]['sources'].append({'archive':name,'entry':normal});row['geometry_id']=spz_ids[sha]['id'];row['extracted_path']=spz_ids[sha]['path'];row['extracted']=True
                    elif row['extension']=='.glb':
                        if sha not in collider_ids:
                            cid=f'collider-{len(collider_ids):02d}-{sha[:10]}';target=HERE/'assets'/cid/'environment_collider.glb';save_unique(target,data)
                            collider_ids[sha]={'id':cid,'sha256':sha,'path':target.relative_to(HERE).as_posix(),'summary':glb_summary(data),'sources':[]}
                        collider_ids[sha]['sources'].append({'archive':name,'entry':normal});row['collider_id']=collider_ids[sha]['id'];row['extracted_path']=collider_ids[sha]['path'];row['extracted']=True
                    elif name.startswith('f9f63233') and normal in ('base.obj','texture_diffuse_00.png','shaded_00.png'):
                        target=HERE/'assets'/'obj-f9f63233'/normal;save_unique(target,data);row['extracted_path']=target.relative_to(HERE).as_posix();row['extracted']=True
                record['entries'].append(row)
        record['total_uncompressed_bytes']=total;records.append(record)
        dump('inventory-progress.json',{'records':records,'complete':False})
    groups=[{'sha256':sha,'members':members} for sha,members in payloads.items() if len(members)>1]
    report={'archives':records,'archive_count':len(records),'total_archive_bytes':sum(r['archive_bytes'] for r in records),
        'unique_spz':list(spz_ids.values()),'unique_colliders':list(collider_ids.values()),'duplicate_payload_groups':groups,
        'duplicate_archive_groups':[], 'provenance':'Source original ZIPs read-only. Reviewed data assets only. No .blend execution or extraction.',
        'frame_mapping':'No frame IDs, input image hashes, timing, intrinsics or growth-order metadata found in ZIP paths/camera transforms.',
        'decoder_reference':SPEC,'complete':True}
    archivegroups={}
    for r in records:archivegroups.setdefault(r['archive_sha256'],[]).append(r['archive_name'])
    report['duplicate_archive_groups']=[{'sha256':h,'archives':x} for h,x in archivegroups.items() if len(x)>1]
    rawgroups={}
    for a in spz_ids.values():
        rawsha=a['header'].get('raw_payload_sha256',a['sha256'])
        group=rawgroups.setdefault(rawsha,{'geometry_id':f'geometry-{len(rawgroups):02d}',
            'raw_payload_sha256':rawsha,'canonical_asset_id':a['id'],'canonical_path':a['path'],
            'num_points':a['header'].get('num_points'),'compressed_variants':[],'sources':[]})
        group['compressed_variants'].append({'id':a['id'],'sha256':a['sha256'],'path':a['path']})
        group['sources'].extend(a['sources'])
    report['canonical_raw_geometry_groups']=list(rawgroups.values())
    report['unique_raw_geometry_count']=len(rawgroups)
    dump('inventory.json',report)
    print(json.dumps({'archives':len(records),'unique_spz':len(spz_ids),'unique_colliders':len(collider_ids),
        'point_counts':[(x['id'],x['header'].get('num_points'),len(x['sources'])) for x in spz_ids.values()],
        'unique_raw_geometry_count':len(rawgroups),'duplicate_payload_groups':len(groups),'total_archive_bytes':report['total_archive_bytes']}))

def decode_positions(raw,header):
    n=header['num_points'];version=header['version'];size=n*(6 if version==1 else 9);offset=16
    if version==1:p=np.frombuffer(raw,dtype='<f2',count=n*3,offset=offset).astype(np.float32).reshape(n,3)
    else:
        q=np.frombuffer(raw,dtype=np.uint8,count=n*9,offset=offset).reshape(n*3,3).astype(np.int32)
        fixed=q[:,0]|(q[:,1]<<8)|(q[:,2]<<16);fixed=np.where(fixed&0x800000,fixed-0x1000000,fixed)
        p=(fixed.astype(np.float32)/(1<<header['fractional_bits'])).reshape(n,3)
    offset+=size;opacity=np.frombuffer(raw,dtype=np.uint8,count=n,offset=offset);offset+=n
    colors=np.frombuffer(raw,dtype=np.uint8,count=n*3,offset=offset).reshape(n,3);offset+=n*3
    scales=np.frombuffer(raw,dtype=np.uint8,count=n*3,offset=offset).reshape(n,3)
    return p,opacity,colors,scales

def analyze():
    inventory=json.loads((HERE/'inventory.json').read_text());reports=[]
    canonical={g['canonical_asset_id'] for g in inventory['canonical_raw_geometry_groups']}
    for asset in [a for a in inventory['unique_spz'] if a['id'] in canonical]:
        file=HERE/asset['path'];header,raw=spz_header(file.read_bytes())
        if raw is None:reports.append({'id':asset['id'],'status':'header_only'});continue
        p,alpha,colors,scales=decode_positions(raw,header)
        def bounds(v):return {'min':v.min(0).tolist(),'max':v.max(0).tolist(),'extent':np.ptp(v,axis=0).tolist()}
        report={'id':asset['id'],'source_sha256':asset['sha256'],'header':header,'finite_positions':bool(np.isfinite(p).all()),
            'center_bounds_all':bounds(p),'opacity_quantiles':np.percentile(alpha/255.,[0,1,10,50,90,99,100]).tolist(),
            'log_scale_quantiles':np.percentile(scales.astype(np.float32)/16.-10.,[0,1,50,99,100],axis=0).tolist(),
            'body_constraints_status':'unsegmented appearance field: splat centers/opacity/scale do not define anatomical volume or closed body surface',
            'sources':asset['sources'],'frame_mapping_status':'unmapped','coordinate_frame':'SPZ stored coordinates, no anatomy alignment applied'}
        for threshold in (0.05,0.2,0.5,0.8):
            selected=p[alpha>=round(threshold*255)]
            report[f'opacity_ge_{threshold}']={'count':len(selected),'center_bounds':bounds(selected) if len(selected) else None,
                'center_quantile_1_99':np.percentile(selected,[1,99],axis=0).tolist() if len(selected) else None}
        # A small deterministic center/color sample supports geometry inspection.
        # It is explicitly NOT a full anisotropic Gaussian render.
        keep=np.flatnonzero(alpha>=51)
        if len(keep)>160000:keep=keep[np.linspace(0,len(keep)-1,160000).astype(int)]
        folder=HERE/'derived'/asset['id'];folder.mkdir(parents=True,exist_ok=True)
        p[keep].astype('<f4').tofile(folder/'center-preview-positions.bin')
        rgb=np.clip(.5+0.28209479177387814*((colors[keep]/255.-.5)/.15),0,1)
        rgb.astype('<f4').tofile(folder/'center-preview-colors.bin');(alpha[keep]/255.).astype('<f4').tofile(folder/'center-preview-opacity.bin')
        report['center_preview']={'count':len(keep),'positions':(folder/'center-preview-positions.bin').relative_to(HERE).as_posix(),
            'colors':(folder/'center-preview-colors.bin').relative_to(HERE).as_posix(),'scope':'Deterministic opacity-filtered center sample, no rotation/anisotropic covariance compositing'}
        dump(Path('derived')/asset['id']/'stats.json',report);reports.append(report)
        del raw,p,alpha,colors,scales
    dump('splat-stats.json',{'assets':reports,'geometry_claim':'Gaussian appearance statistics only. No body measurements, frame order or closed tissue volume inferred.'})
    print(json.dumps({'analyzed_unique_splats':len(reports),'preview_point_limit':160000,'scope':'center/statistics inspection, not Gaussian renderer fidelity'}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['scan','analyze']);parser.add_argument('--downloads',default='C:/Users/User/Downloads');parser.add_argument('--archive',action='append',help='Explicit archive filename; repeat for additional ZIPs. Defaults to the nine user-supplied archives.');args=parser.parse_args()
    if args.action=='scan':scan(Path(args.downloads),args.archive)
    else:analyze()
