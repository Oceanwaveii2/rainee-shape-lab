import bpy, json, pathlib
from mathutils import Vector
root = pathlib.Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r'C:\Users\User\Downloads\Core Body (Template Only).fbx')
rows=[]
for o in bpy.context.scene.objects:
    row={'name':o.name,'type':o.type,'dimensions':list(o.dimensions),'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale)}
    if o.type=='MESH':
        row.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),shape_keys=list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else [],groups=list(o.vertex_groups.keys()),modifiers=[m.type for m in o.modifiers])
    rows.append(row)
(root/'fbx-inventory.json').write_text(json.dumps({'unit_scale':bpy.context.scene.unit_settings.scale_length,'objects':rows},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(root/'source-import.blend'))
print('RAINEE_INSPECTION_COMPLETE')
