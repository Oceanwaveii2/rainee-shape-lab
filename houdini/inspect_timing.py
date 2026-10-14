import hou,pathlib,json
r=pathlib.Path(__file__).resolve().parent;hou.hipFile.load(str(r/'Rainee-Volume-Lab.hip'),suppress_save_prompt=True)
n=hou.node('/obj/RAINEE/SOFT_MOTION/dopnet1/forces/FOLLOW_AUTHORED_REST_SHAPE');rows=[]
for x in [n]+list(n.allSubChildren()):
 for p in x.parms():
  if any(k in p.name().lower() for k in ['time','frame','sop','rest']):
   try: raw=p.unexpandedString()
   except: raw=str(p.eval())
   rows.append([x.path(),p.name(),raw])
print(json.dumps(rows,indent=2));(r/'timing-inspection.json').write_text(json.dumps(rows,indent=2))
