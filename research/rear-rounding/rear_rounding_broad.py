"""Reusable research ray-rounding kernel; not an installed production model."""
from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'houdini'))
from rear_model import DEFAULTS,region,smooth,deform,volume

def rounding_region(v):
    # Wider pole support; original front pelvis limit and lateral support retained.
    return smooth(.49,.540,v[:,1])*(1-smooth(.710,.750,v[:,1]))*(1-smooth(-.015,.015,v[:,2]))*(1-smooth(.18,.22,np.abs(v[:,0])))

def round_lobes(v,amp,roundness=.65,controls=None):
    c={**DEFAULTS,**(controls or {})};out=deform(v,amp,c)
    if amp==0 or roundness==0:return out
    side=np.where(v[:,0]<0,-1.,1.)
    centers=np.column_stack((side*.073,np.full(len(v),.61),np.full(len(v),-.043)))
    radii=np.array([.088,.078,.089])
    ray=(v-centers)/radii
    rho=np.linalg.norm(ray,axis=1)
    ray=ray/np.maximum(rho[:,None],1e-8)
    target_centers=centers.copy()
    target_centers[:,0]*=1+amp*c['separation']
    target_centers[:,2]-=amp*(.025+.043)*c['projection']
    target=target_centers.copy()
    target[:,0]+=.088*(1+amp*c['lateral'])*ray[:,0]
    pole=c['lower_pole']+(c['upper_pole']-c['lower_pole'])*smooth(-.15,.15,ray[:,1])
    target[:,1]+=.078*(1+amp*c['vertical']*pole)*ray[:,1]
    target[:,2]+=.089*(1+amp*c['projection'])*ray[:,2]
    # A smooth inward-limit analogue instead of clipping a lobe through X=0.
    ax=np.abs(v[:,0]);target_ax=side*target[:,0]
    room=np.maximum(ax-.006,0)
    inward=target_ax<ax
    safe=room>0
    candidate=np.where(safe,ax-room*(1-np.exp(np.minimum((target_ax-ax)/np.maximum(room,1e-8),0))),ax)
    target[:,0]=side*np.where(inward,candidate,target_ax)
    strength=roundness*(1-np.exp(-6*amp))
    weight=strength*rounding_region(v)*smooth(.025,.060,ax)*smooth(.30,.65,rho)
    out+=weight[:,None]*(target-out)
    fixed=(region(v)==0)&(rounding_region(v)==0)
    out[fixed]=v[fixed]
    return out

def calibrate_rounding(v,faces,ratio,roundness=.65,controls=None):
    """Measure the same corrected cage; approved study interval only."""
    if not 1<=ratio<=2.5 or not 0<=roundness<=.65:
        raise ValueError('Research study interval: ratio 1..2.5, roundness 0..0.65')
    if ratio==1:return 0.,v.copy()
    target=volume(v,faces)*ratio;lo,hi=0.,4.
    if volume(round_lobes(v,hi,roundness,controls),faces)<target:
        raise ValueError('Volume target not bracketed')
    for _ in range(32):
        mid=(lo+hi)/2
        if volume(round_lobes(v,mid,roundness,controls),faces)<target:lo=mid
        else:hi=mid
    amp=(lo+hi)/2
    return amp,round_lobes(v,amp,roundness,controls)
