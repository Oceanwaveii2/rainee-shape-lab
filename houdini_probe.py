import hou,json,pathlib
r=pathlib.Path(__file__).resolve().parent/'houdini';r.mkdir(exist_ok=True)
obj=hou.node('/obj').createNode('geo','probe')
result={}
for typ in ['vellumconstraints','vellumsolver','pointdeform','vellumrestblend','attribwrangle']:
 try:
  n=obj.createNode(typ)
  result[typ]={'type':n.type().name(),'parameters':[{'name':p.name(),'label':p.parmTemplate().label(),'value':str(p.eval()),'menu':list(zip(p.parmTemplate().menuItems(),p.parmTemplate().menuLabels())) if hasattr(p.parmTemplate(),'menuItems') else []} for p in n.parms()]}
  if typ=='vellumsolver': result[typ]['children']=[{'path':c.path(),'type':c.type().name()} for c in n.allSubChildren()]
 except Exception as e:result[typ]={'error':str(e)}
(r/'node-api.json').write_text(json.dumps(result,indent=2));print('PROBE COMPLETE',flush=True)
