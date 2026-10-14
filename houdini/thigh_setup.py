"""Shared native control/node installation. Fullness zero preserves the FBX."""
import hou
PARAMETERS=[
 ('thigh_fullness','Thigh fullness',0.,0.,1.),
 ('thigh_outer','Outer sweep',1.,0.,2.),
 ('thigh_front','Front projection',1.,0.,2.),
 ('thigh_inner','Inner fullness',.45,0.,1.5),
 ('thigh_back','Back fullness',.25,0.,1.5),
 ('thigh_taper','Knee taper',.6,0.,1.),
 ('thigh_peak','Fullness peak: knee to hip',.64,.2,.8),
]
def install(geo,root):
 ctrl=geo.node('CONTROLS');ptg=ctrl.parmTemplateGroup()
 if ptg.find('thigh_fullness') is None:
  folder=hou.FolderParmTemplate('independent_thighs','Independent thighs')
  for name,label,default,lo,hi in PARAMETERS:
   folder.addParmTemplate(hou.FloatParmTemplate(name,label,1,default_value=(default,),min=lo,max=hi,min_is_strict=True,max_is_strict=True))
  ptg.append(folder);ctrl.setParmTemplateGroup(ptg)
 sculpt=geo.node('INDEPENDENT_THIGHS') or geo.createNode('attribwrangle','INDEPENDENT_THIGHS')
 sculpt.setInput(0,geo.node('DIRECT_OR_SIMULATED'));sculpt.setInput(1,geo.node('FBX_DERIVED_BODY'))
 sculpt.parm('snippet').set((root/'thigh_shape.vfl').read_text())
 sculpt.setComment('Separate thigh design. Canonical source coordinates define the mask and displacement. Fullness zero is identity. Transverse sculpt only: fixed leg length and knee position. Rear seat and front pelvis are protected; no thigh dynamics or anatomical volume measurement.')
 sculpt.setGenericFlag(hou.nodeFlag.DisplayComment,True)
 geo.node('SURFACE_NORMALS').setInput(0,sculpt)
 geo.layoutChildren()
 return sculpt
