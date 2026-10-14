"""Rainee's authored lobe growth. Shared by native target and offline fitting.
Art-directed geometry, not an implementation of BBW, PSD, or implicit skinning.
"""
import numpy as np
DEFAULTS={'lateral':1.,'vertical':1.,'projection':1.,'separation':.15,'upper_pole':1.15,'lower_pole':1.,'cleft_hold':.75}
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
def region(v):
 ax=np.abs(v[:,0]);return smooth(.49,.555,v[:,1])*(1-smooth(.667,.73,v[:,1]))*(1-smooth(-.045,.015,v[:,2]))*(1-smooth(.18,.22,ax))
def deform(v,amp,controls=None):
 c={**DEFAULTS,**(controls or {})};ax=np.abs(v[:,0]);side=np.where(v[:,0]<0,-1.,1.)
 mask=region(v);cleft=1-c['cleft_hold']*.7*(1-smooth(.004,.035,ax));a=amp*mask*cleft
 sx=1+a*c['lateral'];center_scale=1+a*c['separation'];cx=.073
 exponent=sx/center_scale
 inner=cx*center_scale*np.power(np.minimum(ax/cx,1),exponent)
 outer=cx*center_scale+(ax-cx)*sx
 out=v.copy();out[:,0]=side*np.where(ax<=cx,inner,outer)
 pole=c['lower_pole']+(c['upper_pole']-c['lower_pole'])*smooth(.595,.625,v[:,1])
 out[:,1]=v[:,1]+a*(v[:,1]-.61)*c['vertical']*pole
 out[:,2]=v[:,2]-a*(.025-v[:,2])*c['projection']
 # Exact identity outside the region, rather than arithmetic cancellation.
 out[mask==0]=v[mask==0]
 if amp==0:out[:]=v
 return out
def volume(v,faces):
 return abs(np.einsum('ij,ij->i',v[faces[:,0]],np.cross(v[faces[:,1]],v[faces[:,2]])).sum()/6)
def calibrate(v,faces,ratio,controls=None):
 if ratio<1 or ratio>4:raise ValueError('Rear ratio must be between 1 and 4')
 original=volume(v,faces)
 if ratio==1:return 0.,v.copy()
 lo,hi=0.,4.
 if volume(deform(v,hi,controls),faces)<original*ratio:raise ValueError('Shape controls cannot reach volume target')
 for _ in range(32):
  mid=(lo+hi)/2
  if volume(deform(v,mid,controls),faces)<original*ratio:lo=mid
  else:hi=mid
 amp=(lo+hi)/2;return amp,deform(v,amp,controls)
def jacobian_screen(body,amp,controls=None,epsilon=2e-5):
 """Sample field orientation on active source points; not triangle contact."""
 v=np.asarray(body,dtype=float);v=v[region(v)>0]
 if len(v)==0:return {'samples':0,'min_determinant':1.,'nonpositive':0}
 j=np.empty((len(v),3,3))
 for k in range(3):
  offset=np.zeros(3);offset[k]=epsilon
  j[:,:,k]=(deform(v+offset,amp,controls)-deform(v-offset,amp,controls))/(2*epsilon)
 det=np.linalg.det(j)
 return {'samples':len(v),'min_determinant':float(det.min()),'nonpositive':int(np.sum(det<=0))}
