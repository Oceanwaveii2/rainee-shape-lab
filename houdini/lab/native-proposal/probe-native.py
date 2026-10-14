"""Detached type/parameter discovery; never contacts the live Houdini app."""
import hou,json,pathlib
root=pathlib.Path(__file__).resolve().parent
if hou.isUIAvailable():
    raise RuntimeError('This study script may run only in a detached hython process.')
hou.hipFile.clear(suppress_save_prompt=True)
obj=hou.node('/obj')
geo=obj.createNode('geo','probe',run_init_scripts=False)
rows={}
for node_type in ('file','switch','null'):
    assert node_type in hou.sopNodeTypeCategory().nodeTypes(),node_type
    node=geo.createNode(node_type,'probe_'+node_type,run_init_scripts=False)
    names=['file','input'];
    rows[node_type]={'type':node.type().name(),'parameters':{p.name():{'label':p.label(),'default':p.defaultValue() if hasattr(p,'defaultValue') else None} for p in node.parmTemplateGroup().entriesWithoutFolders() if p.name() in names}}
report={'version':hou.applicationVersionString(),'types':rows,'geo_display_parameter':'display' if geo.parm('display') else None,'detached':not hou.isUIAvailable()}
(root/'native-node-discovery.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
