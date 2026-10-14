import hou,pathlib,json
r=pathlib.Path(__file__).resolve().parent
hou.hipFile.load(str(r/'Rainee-Volume-Lab-v2.hip'),suppress_save_prompt=True)
g=hou.node('/obj/RAINEE');c=g.node('CONTROLS');ptg=c.parmTemplateGroup()
for name,label,default,lo,hi in [('volume','Rear cage volume / baseline',1,1,4),('lateral','Lobe radial width',1,.4,1.6),('vertical','Lobe radial height',1,.4,1.6),('projection','Rear projection',1,.4,1.6)]:
 template=ptg.find(name);template.setLabel(label);template.setDefaultValue((default,));template.setMinValue(lo);template.setMaxValue(hi);ptg.replace(name,template)
folder=hou.FolderParmTemplate('rear_shape','Lobe shape / attachment')
for name,label,default,lo,hi in [('separation','Center separation share',.15,0,.6),('upper_pole','Upper dome',1.15,.5,1.6),('lower_pole','Lower pole fullness',1.,.5,1.6),('cleft_hold','Cleft hold',.75,0,1)]:
 folder.addParmTemplate(hou.FloatParmTemplate(name,label,1,default_value=(default,),min=lo,max=hi,min_is_strict=True,max_is_strict=True))
ptg.append(folder);c.setParmTemplateGroup(ptg)
for name,value in [('lateral',1),('vertical',1),('projection',1)]:c.parm(name).set(value)
g.node('VOLUME_CALIBRATED_TARGET').parm('python').set((r/'target_rear_v3.py').read_text())
g.node('AUTHORED_INFLATION').parm('snippet').set((r/'rear_shape_v3.vfl').read_text())
c.setComment('v3 authored lobe growth: radius expands around each lobe center; center separation is a separate share. Upper dome, lower pole and cleft are explicit shape controls. 1x preserves canonical proxy. Grok early close views guide the silhouette; no imported stature shortening. Separate thighs remain neutral by default. This is a work-in-progress study, not a certified video match.')
hou.setFrame(1);g.node('OUT_NORMALIZED').cook(force=True)
assert not g.node('AUTHORED_INFLATION').errors(),g.node('AUTHORED_INFLATION').errors()
hou.hipFile.save(str(r/'Rainee-Volume-Lab-v3.hip'))
print(json.dumps({'scene':str(r/'Rainee-Volume-Lab-v3.hip'),'source':'v2','rear_shape':'per-lobe growth','baseline_ratio':c.evalParm('volume')}),flush=True)
