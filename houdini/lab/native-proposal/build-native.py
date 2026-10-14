"""Build/verify only the separate static proposal HIP in detached hython.

User-authorized sidecar delivery keeps the live Houdini scene untouched.
Imports JS-extracted geometry; never builds an analytic anatomy SOP.
"""
import hou,json,pathlib,hashlib,math,struct,time
if hou.isUIAvailable():
    raise RuntimeError('Refusing interactive Houdini: use detached hython only.')
ROOT=pathlib.Path(__file__).resolve().parent
APP=ROOT.parents[2]
HIP=ROOT/'Rainee-Implicit-Anatomy-Lab.hip'
begin=time.perf_counter()
manifest=json.loads((ROOT/'manifest.json').read_text())
discovery=json.loads((ROOT/'native-node-discovery.json').read_text())
assert discovery['detached'] and discovery['version']==hou.applicationVersionString()
assert 'file' in discovery['types']['file']['parameters']
assert 'input' in discovery['types']['switch']['parameters']

def sha(path):
    digest=hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()

old_hips={str(p):sha(p) for p in APP.rglob('*.hip') if ROOT not in p.parents}
source_before={row['path']:row['sha256'] for row in manifest['source_files_before']}
assert all(sha(p)==h for p,h in source_before.items()),'Protected source changed before native build.'
hou.hipFile.clear(suppress_save_prompt=True)
hou.setFps(24)
hou.playbar.setFrameRange(1,144)
hou.playbar.setPlaybackRange(1,144)
obj=hou.node('/obj')
main=obj.createNode('geo','REGIONAL_PROPOSAL_static_states',run_init_scripts=False)
main.setComment('Closed regional artist proposal only. Two static JS-extracted states, not accepted anatomy or whole-body FBX attachment. No native analytic field or physics.')
ptg=main.parmTemplateGroup()
ptg.append(hou.MenuParmTemplate('proposal_state','Static mesh state',['default','expanded'],['Default proposal','Expanded proposal'],default_value=0))
ptg.append(hou.StringParmTemplate('proposal_scope','Scope and status',1,default_value=(manifest['status']+'; regional surface only; no native analytic SOP; no physics',)))
ptg.append(hou.FloatParmTemplate('source_height_units','Fixed source-FBX height (uncalibrated units)',1,default_value=(manifest['source_height_units'],)))
ptg.append(hou.FloatParmTemplate('source_origin','Fixed source foot origin',3,default_value=tuple(manifest['source_origin'])))
recipes=hou.FolderParmTemplate('recipe_provenance','Editable recipe provenance — static geometry')
recipes.addParmTemplate(hou.StringParmTemplate('recipe_instructions','Recipe behavior',1,default_value=('Editing these recipe fields does NOT regenerate the imported mesh. Re-extract through anatomy-model.mjs/export-proposal.mjs, then reload the File SOP. The state selector chooses existing extracts only.',)))
for row in manifest['states']:
    recipes.addParmTemplate(hou.StringParmTemplate('recipe_'+row['name']+'_json',row['name'].title()+' parameters JSON — requires re-extraction',1,default_value=(json.dumps(row['parameters'],indent=2),),tags={'editor':'1','editorlines':'18'}))
ptg.append(recipes)
main.setParmTemplateGroup(ptg)
for name in ('source_height_units','source_origin','proposal_scope','recipe_instructions'):
    for parm in main.parmTuple(name):parm.lock(True)
files=[]
for index,row in enumerate(manifest['states']):
    node=main.createNode('file','IMPORT_'+row['name'].upper()+'_STATIC_EXTRACT',run_init_scripts=False)
    node.parm('file').set('$HIP/'+row['obj'])
    node.setPosition(hou.Vector2(index*4,2))
    node.setComment('Read-only JS extraction. Recipe: '+row['recipe']+'. Source assets are not linked for mutation.')
    files.append(node)
switch=main.createNode('switch','SELECT_STATIC_PROPOSAL',run_init_scripts=False)
for index,node in enumerate(files):switch.setInput(index,node)
switch.parm('input').setExpression('ch("../proposal_state")',hou.exprLanguage.Hscript)
switch.setPosition(hou.Vector2(2,0))
out=main.createNode('null','OUT_REGIONAL_PROPOSAL_STATIC',run_init_scripts=False)
out.setInput(0,switch);out.setPosition(hou.Vector2(2,-2));out.setDisplayFlag(True);out.setRenderFlag(True)
main.setPosition(hou.Vector2(0,0))
guide=obj.createNode('geo','SOURCE_HEIGHT_GUIDE_FIXED',run_init_scripts=False)
guide.setPosition(hou.Vector2(6,0))
guide.setComment('Wire guide measures original FBX stature, independent of local proposal bounds. Physical units are uncalibrated.')
guide_file=guide.createNode('file','IMPORT_SOURCE_HEIGHT_GUIDE',run_init_scripts=False)
guide_file.parm('file').set('$HIP/'+manifest['guide'])
guide_out=guide.createNode('null','OUT_SOURCE_HEIGHT_GUIDE',run_init_scripts=False)
guide_out.setInput(0,guide_file);guide_out.setPosition(hou.Vector2(0,-2));guide_out.setDisplayFlag(True);guide_out.setRenderFlag(False)
guide.setDisplayFlag(True);main.setDisplayFlag(True)
hou.hipFile.save(str(HIP))
assert pathlib.Path(hou.hipFile.path()).resolve()==HIP
main_path,out_path,guide_path=main.path(),out.path(),guide_out.path()
# Reload exactly the saved study in this sidecar, never in the user's app.
hou.hipFile.load(str(HIP),suppress_save_prompt=True,ignore_load_warnings=True)
main=hou.node(main_path);out=hou.node(out_path);guide_out=hou.node(guide_path)

def geometry_audit(geo):
    points=[tuple(p.position()) for p in geo.points()]
    faces=[tuple(v.point().number() for v in prim.vertices()) for prim in geo.prims()]
    assert all(len(f)==3 for f in faces),'Native regional extract must be triangulated.'
    assert all(all(math.isfinite(v) for v in p) for p in points),'Non-finite position.'
    edge_counts={};edge_directions={};neighbors=[set() for p in points]
    signed=0.;minimum_area=math.inf;degenerate=0
    for a,b,c in faces:
        pa,pb,pc=points[a],points[b],points[c]
        u=[pb[i]-pa[i] for i in range(3)];v=[pc[i]-pa[i] for i in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        area=math.sqrt(sum(x*x for x in cross))*.5;minimum_area=min(minimum_area,area)
        if area<1e-15:degenerate+=1
        bc=(pb[1]*pc[2]-pb[2]*pc[1],pb[2]*pc[0]-pb[0]*pc[2],pb[0]*pc[1]-pb[1]*pc[0])
        signed+=sum(pa[i]*bc[i] for i in range(3))/6
        for i,j in ((a,b),(b,c),(c,a)):
            key=(min(i,j),max(i,j));edge_counts[key]=edge_counts.get(key,0)+1
            edge_directions[key]=edge_directions.get(key,0)+(1 if i<j else -1)
            neighbors[i].add(j);neighbors[j].add(i)
    used=set(i for f in faces for i in f);unseen=set(used);components=0
    while unseen:
        components+=1;stack=[unseen.pop()]
        while stack:
            current=stack.pop();next_points=neighbors[current]&unseen;unseen-=next_points;stack.extend(next_points)
    boundary=sum(n==1 for n in edge_counts.values());nonmanifold=sum(n>2 for n in edge_counts.values());inconsistent=sum(n!=0 for n in edge_directions.values())
    normal_values=[]
    if geo.findPointAttrib('N'):normal_values=[p.attribValue('N') for p in geo.points()]
    elif geo.findVertexAttrib('N'):normal_values=[v.attribValue('N') for p in geo.prims() for v in p.vertices()]
    normals_finite=bool(normal_values) and all(all(math.isfinite(x) for x in n) for n in normal_values)
    normal_error=max((abs(math.sqrt(sum(x*x for x in n))-1) for n in normal_values),default=None)
    payload=b''.join(struct.pack('<3f',*p) for p in points)+b''.join(struct.pack('<3I',*f) for f in faces)
    # Houdini uses left-handed polygon normals; gwavefront reverses OBJ's
    # right-handed winding at import. Keep both integrals explicitly labeled.
    # SideFX: /docs/houdini/model/primitive_spaces.html
    alignments=[]
    for prim in geo.prims():
        normal=tuple(prim.normal())
        provided=[v.point().attribValue('N') if geo.findPointAttrib('N') else v.attribValue('N') for v in prim.vertices()]
        avg=[sum(n[i] for n in provided)/3 for i in range(3)]
        alignments.append(sum(normal[i]*avg[i] for i in range(3)))
    normal_alignment_mean=sum(alignments)/len(alignments)
    result={'points':len(points),'triangles':len(faces),'finite':True,'closed':boundary==0 and nonmanifold==0 and inconsistent==0,'boundary_edges':boundary,'nonmanifold_edges':nonmanifold,'inconsistent_winding_edges':inconsistent,'connected_components':components,'degenerate_triangles':degenerate,'minimum_triangle_area':minimum_area,'right_hand_signed_volume_source_units_cubed':signed,'houdini_left_hand_signed_volume_source_units_cubed':-signed,'volume_source_units_cubed':abs(signed),'winding_convention':'Houdini left-handed; OBJ right-handed order reversed by native importer','winding_reference':'https://www.sidefx.com/docs/houdini/model/primitive_spaces.html','normal_values_present_and_finite':normals_finite,'normal_unit_length_max_error':normal_error,'native_primitive_vs_imported_normal_alignment_mean':normal_alignment_mean,'geometry_sha256':hashlib.sha256(payload).hexdigest(),'bounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}}
    assert result['closed'] and components==1 and degenerate==0 and -signed>0,result
    assert normal_alignment_mean>.9,result
    assert normals_finite and normal_error<1e-5,result
    return result

checks=[]
for index,row in enumerate(manifest['states']):
    main.parm('proposal_state').set(index)
    expected=row['source_coordinate_measurement']
    hashes=[]
    for frame in (1,12,144):
        hou.setFrame(frame);started=time.perf_counter();out.cook(force=True);geo=out.geometry();audit=geometry_audit(geo)
        assert not out.errors() and not out.warnings(),(out.errors(),out.warnings())
        assert audit['points']==expected['points'] and audit['triangles']==expected['triangles']
        error=abs(audit['volume_source_units_cubed']/expected['volume']-1);assert error<2e-6,error
        audit.update({'state':row['name'],'frame':frame,'cook_and_audit_seconds':time.perf_counter()-started,'errors':out.errors(),'warnings':out.warnings(),'volume_vs_js_relative_error':error})
        checks.append(audit);hashes.append(audit['geometry_sha256'])
    assert len(set(hashes))==1,'Static state changed across frames.'
guide_out.cook(force=True);guide_geo=guide_out.geometry();bb=guide_geo.boundingBox()
height=bb.maxvec()[1]-bb.minvec()[1]
assert abs(height-manifest['source_height_units'])<2e-7
assert not guide_out.errors() and not guide_out.warnings()
all_errors=[]
for node in hou.node('/obj').allSubChildren():
    if node.type().category()==hou.sopNodeTypeCategory():
        node.cook(force=True)
        if node.errors() or node.warnings():all_errors.append({'node':node.path(),'errors':node.errors(),'warnings':node.warnings()})
assert not all_errors,all_errors
source_after={p:sha(p) for p in source_before}
hips_after={p:sha(p) for p in old_hips}
assert source_after==source_before and hips_after==old_hips,'Protected source or existing HIP changed.'
main.parm('proposal_state').set(0);hou.setFrame(1)
hou.hipFile.save(str(HIP))
report={'passed':True,'hip':str(HIP),'hip_sha256':sha(HIP),'houdini_version':hou.applicationVersionString(),'execution':'detached hython; live app not contacted or loaded','native_analytic_SOP_template':False,'static_not_physics':True,'template_scope':'regional closed proposal; not accepted/image-fitted anatomy or seamless full FBX attachment','native_checks':checks,'static_geometry_across_frames':[1,12,144],'source_height_guide':{'height_source_units':height,'expected_height':manifest['source_height_units'],'height_error':height-manifest['source_height_units'],'points':len(guide_geo.points()),'primitives':len(guide_geo.prims()),'source_origin':manifest['source_origin']},'all_sop_errors_or_warnings':all_errors,'protected_source_files_after':source_after,'protected_source_hashes_unchanged':True,'existing_hip_hashes_unchanged':True,'existing_hip_count':len(old_hips),'existing_hip_hashes':old_hips,'elapsed_seconds':time.perf_counter()-begin,'limits':manifest['limits']}
(ROOT/'native-verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'passed':True,'hip':str(HIP),'states':len(manifest['states']),'checks':len(checks),'guide_height':height,'source_hashes_unchanged':True,'existing_hips_unchanged':len(old_hips),'elapsed_seconds':report['elapsed_seconds']}))
