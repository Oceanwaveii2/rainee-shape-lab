import hou,numpy as np
node=hou.pwd();g=node.geometry();ctrl=node.parent().node('CONTROLS')
v=np.array(g.pointFloatAttribValues('P')).reshape(-1,3);faces=np.array([[p.number() for p in f.points()] for f in g.prims()])
def smooth(a,b,t):
 s=np.clip((t-a)/(b-a),0,1);return s*s*(3-2*s)
mask=smooth(.49,.555,v[:,1])*(1-smooth(.667,.73,v[:,1]))*(1-smooth(-.045,.015,v[:,2]))*(1-smooth(.18,.22,np.abs(v[:,0])))
delta=np.column_stack([v[:,0]*ctrl.evalParm('lateral'),(v[:,1]-.61)*ctrl.evalParm('vertical'),-(.025-v[:,2])*ctrl.evalParm('projection')])*mask[:,None]
def volume(p):return abs(np.einsum('ij,ij->i',p[faces[:,0]],np.cross(p[faces[:,1]],p[faces[:,2]])).sum()/6)
original=volume(v);desired=ctrl.evalParm('volume');low=-.65;high=5.
for _ in range(32):
 mid=(low+high)/2
 if volume(v+delta*mid)<original*desired:low=mid
 else:high=mid
amp=(low+high)/2
if abs(desired-1)<1e-9:amp=0
out=v+delta*amp
if abs(volume(out)/original-desired)>1e-5:raise hou.NodeError('Volume target outside calibrated range')
g.setPointFloatAttribValues('P',out.flatten().tolist())
for name,value in [('inflation_amplitude',amp),('cage_volume',volume(out)),('baseline_cage_volume',original),('volume_ratio',volume(out)/original)]:
 if g.findGlobalAttrib(name) is None:g.addAttrib(hou.attribType.Global,name,0.)
 g.setGlobalAttribValue(name,float(value))
grp=g.createPointGroup('attachment')
for i,pt in enumerate(g.points()):
 if mask[i]<.001:grp.add(pt)
