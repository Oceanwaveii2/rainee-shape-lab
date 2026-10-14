"""Research: smoothly relax the authored body toward an ellipsoid shell.

This stronger corrective evaluates its mask at current coordinates and uses
RK4. It retains point correspondence; sampled Jacobians are not contact tests.
"""
from pathlib import Path
import sys,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'houdini'))
from rear_model import DEFAULTS,region,smooth,deform,volume

def ellipsoid(amp,controls=None):
    c={**DEFAULTS,**(controls or {})}
    center=np.array([.073*(1+amp*c['separation']),.61,-.043-amp*.068*c['projection']])
    radii=np.array([.088*(1+amp*c['lateral']),.078*(1+amp*c['vertical']*(c['upper_pole']+c['lower_pole'])/2),.089*(1+amp*c['projection'])])
    return center,radii

def velocity(v,amp,controls=None):
    center,radii=ellipsoid(amp,controls);side=np.where(v[:,0]<0,-1.,1.)
    centers=np.broadcast_to(center,(len(v),3)).copy();centers[:,0]*=side
    q=(v-centers)/radii;rho=np.linalg.norm(q,axis=1)
    target=centers+radii*q/np.maximum(rho[:,None],1e-8)
    ax=np.abs(v[:,0])
    gate=smooth(.48,.535,v[:,1])*(1-smooth(.725,.770,v[:,1]))*(1-smooth(-.045,.015,v[:,2]))
    gate*=smooth(.025,.060,ax)*(1-smooth(.195,.22,ax))*smooth(.25,.60,rho)*(1-smooth(1.25,1.65,rho))
    return (target-v)*gate[:,None]

def round_lobes(v,amp,roundness=.65,controls=None,steps=20):
    out=deform(v,amp,controls)
    if amp==0 or roundness==0:return out
    duration=roundness*4*(1-np.exp(-6*amp));dt=duration/steps
    for _ in range(steps):
        k1=velocity(out,amp,controls)
        k2=velocity(out+dt*k1/2,amp,controls)
        k3=velocity(out+dt*k2/2,amp,controls)
        k4=velocity(out+dt*k3,amp,controls)
        out+=dt*(k1+2*k2+2*k3+k4)/6
    return out

def calibrate_rounding(v,faces,ratio,roundness=.65,controls=None):
    if not 1<=ratio<=2.5 or not 0<=roundness<=.65:raise ValueError('Research interval only')
    if ratio==1:return 0.,v.copy()
    target=volume(v,faces)*ratio;lo,hi=0.,1.
    if volume(round_lobes(v,hi,roundness,controls),faces)<target:raise ValueError('Target not bracketed')
    for _ in range(30):
        mid=(lo+hi)/2
        if volume(round_lobes(v,mid,roundness,controls),faces)<target:lo=mid
        else:hi=mid
    amp=(lo+hi)/2;return amp,round_lobes(v,amp,roundness,controls)
