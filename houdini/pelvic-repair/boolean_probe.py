import hou,json
from pathlib import Path
R=Path(__file__).resolve().parent
g=hou.node('/obj').createNode('geo','PROBE')
card={}
for t in ['boolean','smooth','groupcreate']:
 n=g.createNode(t,t)
 card[t]=[{'name':p.name(),'label':p.parmTemplate().label(),'value':p.eval(),'tokens':list(p.menuItems()) if p.parmTemplate().type()==hou.parmTemplateType.Menu else None} for p in n.parms()]
(R/'boolean-cards.json').write_text(json.dumps(card,indent=2))
