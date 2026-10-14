import hou,json,pathlib
r=pathlib.Path(__file__).resolve().parent/'houdini'
g=hou.node('/obj').createNode('geo');s=g.createNode('vellumsolver');s.allowEditingOfContents();d=s.node('dopnet1/forces');n=d.createNode('vellumrestblend')
result={'restblend':[{'name':p.name(),'value':str(p.eval()),'menu':list(zip(p.parmTemplate().menuItems(),p.parmTemplate().menuLabels())) if hasattr(p.parmTemplate(),'menuItems') else []} for p in n.parms()], 'forces':[{'name':c.name(),'inputs':[i.path() if i else None for i in c.inputs()],'connections':[(x.inputIndex(),x.inputNode().path(),x.outputIndex()) for x in c.inputConnections()]} for c in d.children()]}
(r/'dop-api.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
