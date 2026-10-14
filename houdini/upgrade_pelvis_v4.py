"""Integrate the localized implicit skin repair into native shape authoring."""
import hou,pathlib,json,numpy as np
r=pathlib.Path(__file__).resolve().parent;patch=r/'pelvic-repair'
manifest=json.loads((patch/'final-repair-manifest.json').read_text())
hou.hipFile.load(str(r/'Rainee-Volume-Lab-v3.hip'),suppress_save_prompt=True)
g=hou.node('/obj/RAINEE');c=g.node('CONTROLS')
repair=g.createNode('file','REPAIRED_BODY');repair.parm('file').set('$HIP/pelvic-repair/'+manifest['bgeo'])
repair.setComment('Localized implicit pelvic skin repair: preserves stature and distant source polygons. The original ZBrush gap is a defect. Core attachments are connected; collar and inherited whole-body defects still need cleanup. See pelvic-repair/implicit-repair-report.json.')
repair.setGenericFlag(hou.nodeFlag.DisplayComment,True)
g.node('AUTHORED_INFLATION').setInput(0,repair);g.node('INDEPENDENT_THIGHS').setInput(1,repair)
base=np.array(repair.geometry().pointFloatAttribValues('P'),dtype='<f4').reshape(-1,3)
faces=np.fromfile(patch/manifest['triangles'],'<u4').reshape(-1,3);used=np.unique(faces)
info=json.loads((r.parent/'assets/mesh-info.json').read_text());lo=np.array(info['source_bounds']['min']);hi=np.array(info['source_bounds']['max']);center=(lo+hi)/2
visible_min=float(base[used,1].min());visible_height=float(np.ptp(base[used,1]));source_height=float(hi[1]-lo[1])
referenced=g.createNode('attribwrangle','REMOVE_UNUSED_EXPORT_POINTS');referenced.setInput(0,g.node('OUT_NORMALIZED'));referenced.parm('snippet').set('if (len(pointprims(0,@ptnum))==0) removepoint(0,@ptnum);')
exact=g.createNode('xform','OUT_FBX_SOURCE_STATURE');exact.setInput(0,referenced);exact.parm('scale').set(source_height/visible_height);exact.parmTuple('t').set((float(center[0]),float(lo[1]-visible_min*source_height/visible_height),float(center[2])))
exact.setComment('Uniformly restores the referenced working surface to the FBX full bounding height. This accounts for proxy clustering and unused extreme points. Internal solver coordinates and deformation are unchanged.');exact.setGenericFlag(hou.nodeFlag.DisplayComment,True)
exact.setDisplayFlag(True);exact.setRenderFlag(True)
c.setComment('FBX stature and general identity anchor the model. Selected figurines/drawings refine anatomy; the incomplete groin has been repaired with a local SDF construction. Rear per-lobe growth and thigh sculpt are independent. Direct growth uses a sampled field-fold guard; no claim of exact video match or certified contact.')
hou.setFrame(1);g.node('OUT_NORMALIZED').cook(force=True)
assert not g.node('OUT_NORMALIZED').errors(),g.node('OUT_NORMALIZED').errors()
g.layoutChildren();hou.hipFile.save(str(r/'Rainee-Volume-Lab-v4.hip'))
base.tofile(r/'body-v4-rest.bin')
report={'scene':str(r/'Rainee-Volume-Lab-v4.hip'),'repair_manifest':'pelvic-repair/final-repair-manifest.json','body_points':len(base),'body_primitives':len(repair.geometry().prims()),'source_height':source_height,'proxy_rendered_height_normalized':visible_height,'source_stature_output':'OUT_FBX_SOURCE_STATURE','source_authority':'FBX stature/general identity; reference-refined anatomy; flawed source topology is not protected.','status':'Built; native integration checks pending'}
(r/'build-report-v4.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
