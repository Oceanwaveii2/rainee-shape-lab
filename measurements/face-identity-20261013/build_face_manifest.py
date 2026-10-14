"""Preserve accepted face-reference assets and record artist authority/provenance.

Copies source bytes unchanged. No image editing, generation, facial measurements,
averaging, camera inference or production head replacement occurs here.
"""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent
RAINEE=HERE.parent.parent
DOWNLOADS=Path('C:/Users/User/Downloads')

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def preserve(source,friendly):
    source=Path(source);target=HERE/'references'/friendly;target.parent.mkdir(parents=True,exist_ok=True)
    original=sha(source)
    if target.exists() and sha(target)!=original:raise ValueError('Existing reference differs; refusing silent overwrite')
    if not target.exists():shutil.copyfile(source,target)
    copied=sha(target)
    if copied!=original:raise ValueError('Copied bytes do not match source')
    with Image.open(source) as image:dimensions=list(image.size);fmt=image.format;mode=image.mode
    return {'source_path':str(source.resolve()),'source_filename':source.name,
        'reference_path':target.relative_to(HERE).as_posix(),'source_sha256':original,
        'copy_sha256':copied,'bytes':source.stat().st_size,'image_size':dimensions,'image_format':fmt,'image_mode':mode,
        'preservation':{'byte_identical':True,'uncropped':True,'resampled':False,'retouched':False,'generated_here':False}}

def main():
    references=[]
    closeups=[
        ('closeup-blue-bust', '2026042111255844_427f7f7c365c0b938c2eca69bb6ff61a.png','blue-bust.png',
         'Front-facing blue-costume bust',
         {'hair':'Red center-parted wavy bob','ears':'Large glossy blue ear shapes with sculpted blue inner tufts',
          'eyes':'Large blue irises inside wide almond-shaped eyes','makeup':'Pink eye shadow and black upper lash fans',
          'lips':'Full glossy pink lips with visible cupid bow','face':'Tapering oval/heart-like outline and small rounded nose'},
         'A stylized sculpt/render appearance variant; blue ear finish is retained separately from natural fur references.'),
        ('closeup-red-portrait','0000.webp','red-portrait.webp',
         'Red-haired portrait with natural ear finish',
         {'hair':'Red center-parted waves with long twin tails and light fluffy ties','ears':'Brown/orange outer fur and white inner tufts',
          'eyes':'Large blue irises and almond eye openings','makeup':'Pink/plum eye shadow and long dense upper lashes',
          'lips':'Full pink/plum lips','face':'Small rounded nose, curved cheeks and tapered oval/heart-like chin outline'},
         'The original filename0000.webp is a separate closeup and does not prove it is the accepted growth frame0000.'),
        ('closeup-blonde-illustration','image (3) (1).png','blonde-portrait.png',
         'Blonde illustrated portrait',
         {'hair':'Blonde center-parted curls with long twin tails and light fluffy ties','ears':'Orange/brown fur with pale pink interiors and white inner tufts',
          'eyes':'Large round blue irises within stylized almond eye openings','makeup':'Pink eye shadow, black eyeliner and pronounced long upper lashes',
          'lips':'Full saturated pink/red lips','face':'Small rounded nose and tapered cheek-to-chin oval/heart-like outline'},
         'Drawn shading and blonde hair are preserved as a separate appearance variant, not averaged into the red variants.')]
    for identity,filename,friendly,label,cues,note in closeups:
        record=preserve(DOWNLOADS/filename,friendly)
        record.update({'id':identity,'group':'face_closeups','label':label,
            'authority_role':'Accepted artist face/appearance reference above flawed FBX facial sculpt',
            'authority_basis':'Latest direct user clarification relayed by root; file contents are reference data, not instructions',
            'observed_artist_cues':cues,'variant_note':note,
            'geometry_status':'2D observational face cues only; no exact3D dimensions or hidden facial surfaces inferred'})
        references.append(record)
    sequence_path=RAINEE/'measurements/five-frame-20261013/reference-sequence-manifest.json'
    sequence=json.loads(sequence_path.read_text(encoding='utf-8'))
    observations={
        0:{'face_visibility':'Three-quarter face visible looking back','eyes':'Visible iris reads gold/green under this lighting, not the blue of the closeups',
            'cues':['Large almond eye opening','Long upper lashes','Small rounded nose','Full lips','Soft tapered face outline'],
            'hair_and_ears':'Long red/auburn waves; brown ears with white inner tufts'},
        10:{'face_visibility':'Three-quarter face visible looking back','eyes':'Visible iris reads gold/green under this lighting; do not automatically recolor or average',
            'cues':['Large almond eye opening','Long upper lashes','Small rounded nose','Full lips','Soft tapered face outline'],
            'hair_and_ears':'Long red/auburn waves; brown ears with white inner tufts'},
        18:{'face_visibility':'Mostly profile with eye closed or nearly closed','eyes':'Iris color and full eye opening cannot be established from this frame',
            'cues':['Upper lash silhouette','Small rounded nose profile','Full lip profile','Tapered cheek/chin profile'],
            'hair_and_ears':'Long red/auburn waves; brown ears with white inner tufts'},
        26:{'face_visibility':'Turned away; face largely hidden by hair','eyes':'Unseen facial features and iris color are unconstrained by this view',
            'cues':['Hair and ear appearance context; no frontal facial shape measurements supported'],
            'hair_and_ears':'Long red/auburn waves; brown ears with white inner tufts'}}
    for number in (0,10,18,26):
        frame=next(f for f in sequence['frames'] if f['frame_number']==number)
        primary=next(v for v in frame['enhanced_versions'] if v['kind']=='qwen_intermediate_1024')
        record=preserve(primary['path'],f'frame-{number:04d}.png')
        if record['source_sha256']!=primary['sha256']:raise ValueError('Frame hash differs from source provenance manifest')
        versions=[]
        for version in frame['enhanced_versions']:
            source=Path(version['path']);current=sha(source)
            versions.append({'kind':version['kind'],'source_path':str(source),'source_sha256':current,
                'matches_existing_provenance_hash':current==version['sha256'],'image_size':version['size'],
                'transformation_kind':version['transformation_kind'],
                'copied_for_board':version['kind']=='qwen_intermediate_1024'})
        record.update({'id':f'accepted-frame-{number:04d}','group':'accepted_growth_frames',
            'frame_number':number,'stage_ordinal':frame['stage_ordinal'],'stage_role':frame['role'],
            'label':f'Accepted frame{number:04d} · {frame["role"]}',
            'authority_role':'Accepted face/appearance evidence where visible, plus accepted ordinal growth stage',
            'authority_basis':'Latest direct user face clarification and accepted stage order; no inferred acceptance of generated3D anatomy',
            'observed_artist_cues':observations[number],
            'source_processing_provenance':{'board_version':'Existing Qwen1024 regeneration copied without alteration',
                'final4096_status':'Existing upscale of regeneration; source/hash linked but not copied for lightweight board',
                'versions':versions,'original_frame':frame['original_frame']},
            'geometry_status':'Appearance/frame authority does not establish calibrated 3D facial dimensions or shared mesh topology'})
        references.append(record)
    worldgen_path=RAINEE/'measurements/worldgen-20261013/inventory.json'
    worldgen=json.loads(worldgen_path.read_text(encoding='utf-8'))
    supporting=[]
    for prefix,ref,label in [('WorldGen-37454f46','closeup-blonde-illustration','Blonde portrait appearance field'),
        ('WorldGen-83db5ca5','closeup-blue-bust','Blue-costume bust appearance field')]:
        group=next(g for g in worldgen['canonical_raw_geometry_groups'] if any(s['archive'].startswith(prefix) for s in g['sources']))
        supporting.append({'kind':'Gaussian appearance field','reference_id':ref,'label':label,
            'geometry_id':group['geometry_id'],'raw_payload_sha256':group['raw_payload_sha256'],
            'asset_path_relative_to_rainee':'measurements/worldgen-20261013/'+group['canonical_path'],
            'association_basis':'Root visually inspected actual Gaussian rendering against supplied reference; input-image hash/camera equivalence not established',
            'authority_role':'Supporting appearance evidence for user-approved face family; not canonical facial geometry',
            'limitations':['Gaussian appearance field is not a closed facial surface','No exact 3D facial dimensions inferred','No production-head replacement performed']})
    head_inventory_path=RAINEE/'measurements/worldgen-20261013/derived/obj-f9f63233/inventory.json'
    head=json.loads(head_inventory_path.read_text(encoding='utf-8'))
    supporting.append({'kind':'Cropped upper-body OBJ','source_path':head['source'],'source_sha256':head['source_sha256'],
        'vertices':head['vertices'],'triangles':head['triangles'],
        'authority_role':'Candidate head/upper-body reconstruction for inspection only',
        'association_basis':'Geometry inventory confirms head/ears/hair/upper torso; no exact accepted-reference camera or generator-image hash mapping',
        'limitations':['No calibrated camera correspondence','No canonical acceptance of exact face geometry','No butt/thigh/full stature evidence','No production head replacement performed']})
    fbx_info=json.loads((RAINEE/'assets/mesh-info.json').read_text(encoding='utf-8'))
    manifest={'schema':'rainee-face-authority-v1','date':'2026-10-13',
        'authority_decision':{'basis':'Latest direct user clarification: three closeups and accepted frames are more correct for her face than the flawed FBX sculpt',
            'face_authority':'The seven listed accepted image references supersede FBX facial shape/appearance as artist intent',
            'fbx_role':'Height anchor only; face is not immutable or canonical',
            'fbx_source_path':fbx_info['source'],'height_anchor_source_units':fbx_info['normalization_height_source_units'],
            'real_world_stature_calibrated':False,'production_head_geometry_replaced':False,
            '3d_dimension_acceptance':'No automatic face measurements, mesh replacements or unseen facial geometry are accepted by this manifest'},
        'shared_visible_artist_cues':[
            {'cue':'Large stylized almond eye openings and prominent irises','evidence_reference_ids':['closeup-blue-bust','closeup-red-portrait','closeup-blonde-illustration','accepted-frame-0000','accepted-frame-0010']},
            {'cue':'Blue iris family in the three closeups; gold/green appearance in visible accepted frames remains a separate variant','evidence_reference_ids':['closeup-blue-bust','closeup-red-portrait','closeup-blonde-illustration','accepted-frame-0000','accepted-frame-0010']},
            {'cue':'Long, prominent upper lashes; pink/plum eye shadow most clearly visible in closeups','evidence_reference_ids':['closeup-blue-bust','closeup-red-portrait','closeup-blonde-illustration','accepted-frame-0000','accepted-frame-0010','accepted-frame-0018']},
            {'cue':'Small rounded nose, full lips, tapering oval/heart-like facial outline','evidence_reference_ids':['closeup-blue-bust','closeup-red-portrait','closeup-blonde-illustration','accepted-frame-0000','accepted-frame-0010','accepted-frame-0018']}],
        'variant_policy':'Keep red versus blonde hair, bob versus twin-tail/long-wave styling, blue sculpted versus natural furry ears, and eye-color/lighting variants separate. Do not average or silently reconcile them.',
        'reference_groups':[{'id':'face_closeups','label':'Accepted face closeups','reference_ids':[r['id'] for r in references if r['group']=='face_closeups']},
            {'id':'accepted_growth_frames','label':'Accepted frame sequence with visibility limits','reference_ids':[r['id'] for r in references if r['group']=='accepted_growth_frames']}],
        'display_order':[r['id'] for r in references],'references':references,'supporting_3d':supporting,
        'sequence_policy':{'accepted_frames':[0,10,18,26],'endpoint':26,'stage_scale':'ordinal, no absolute time/volume inferred',
            'excluded_frame':49,'reason':'User rejected later deflation/wrong proportions; not copied or promoted here'},
        'provenance_inputs':[{'path':str(sequence_path),'sha256':sha(sequence_path)}, {'path':str(worldgen_path),'sha256':sha(worldgen_path)},
            {'path':str(head_inventory_path),'sha256':sha(head_inventory_path)}],
        'preservation_policy':'All seven copied source images are byte-identical and fully uncropped; no resampling, compositing, retouching or generation occurred.',
        'implementation_scope':'Reference authority/provenance only. Main UI, original assets, inventories and production head geometry unchanged.'}
    additional_path=HERE/'new-bust-archive.json'
    if additional_path.exists():
        additional=json.loads(additional_path.read_text(encoding='utf-8'))
        manifest['additional_bust_attachment']={'report':'new-bust-archive.json','status':additional['status'],
            'source_path':additional['new']['source_path'],'archive_sha256':additional['new']['archive_sha256'],
            'member_payloads_identical_to_earlier':additional['member_payloads_identical'],
            'geometry_replaced':False,'new_extraction_performed':False}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    verification={'passed':True,'reference_count':len(references),'all_byte_identical':all(r['source_sha256']==r['copy_sha256'] for r in references),
        'all_uncropped':True,'copied_bytes':sum(r['bytes'] for r in references),'accepted_frame_numbers':[0,10,18,26],
        'rejected_frame49_not_copied':not (HERE/'references/frame-0049.png').exists(),
        'production_head_replacement':False,'scope':'File preservation and authority manifest, not facial geometry accuracy'}
    (HERE/'verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
    print(json.dumps(verification))

if __name__=='__main__':main()
