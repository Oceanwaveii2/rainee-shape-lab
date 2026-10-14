"""Optional stationary-velocity rear deformation research, not a shipping model.

RK4 integrates a localized velocity at the current coordinates. The attachment
mask has finite X/Y support and no far-posterior Z cutoff. Smooth
continuous flows preserve orientation analytically; finite RK4 steps require
sampling checks. Positive sampled Jacobians do not certify contact or triangles.
Run with Python + NumPy. Outputs only this research folder's JSON report.
"""
from pathlib import Path
import sys, time, json
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'houdini'))
from rear_model import DEFAULTS, region, smooth, volume

def velocity(v,controls):
    c={**DEFAULTS,**controls};ax=np.abs(v[:,0]);side=np.where(v[:,0]<0,-1.,1.)
    weight=region(v)*(1-c['cleft_hold']*.7*(1-smooth(.004,.035,ax)))
    cx=.073
    # Infinitesimal version of the authored inner-lobe mapping, regularized at X=0.
    inner=ax*(c['separation']+(c['lateral']-c['separation'])*np.log(np.maximum(ax/cx,1e-4)))
    outer=cx*c['separation']+(ax-cx)*c['lateral']
    pole=c['lower_pole']+(c['upper_pole']-c['lower_pole'])*smooth(.595,.625,v[:,1])
    out=np.column_stack((side*np.where(ax<=cx,inner,outer),
                         (v[:,1]-.61)*c['vertical']*pole,
                         -( .025-v[:,2])*c['projection']))
    return out*weight[:,None]

def flow(v,duration,controls=None,steps=24):
    controls=controls or {};out=np.array(v,dtype=np.float64,copy=True)
    if duration==0:return out
    dt=duration/steps
    for _ in range(steps):
        k1=velocity(out,controls)
        k2=velocity(out+dt*k1/2,controls)
        k3=velocity(out+dt*k2/2,controls)
        k4=velocity(out+dt*k3,controls)
        out+=dt*(k1+2*k2+2*k3+k4)/6
    out[region(v)==0]=v[region(v)==0]
    return out

def calibrate(v,faces,ratio,controls=None,steps=24):
    target=volume(v,faces)*ratio
    if ratio==1:return 0.,v.copy()
    lo,hi=0.,4.
    if volume(flow(v,hi,controls,steps),faces)<target:raise ValueError('Target not bracketed')
    for _ in range(28):
        mid=(lo+hi)/2
        if volume(flow(v,mid,controls,steps),faces)<target:lo=mid
        else:hi=mid
    duration=(lo+hi)/2
    return duration,flow(v,duration,controls,steps)

def cage_faces(nr=48,ns=32):
    tri=[];last=1+(nr-1)*ns
    for k in range(ns):tri.append([0,1+(k+1)%ns,1+k])
    for j in range(nr-2):
        for k in range(ns):
            a=1+j*ns+k;b=1+j*ns+(k+1)%ns;c=a+ns;d=b+ns
            tri.extend([[a,b,c],[b,d,c]])
    for k in range(ns):tri.append([last,1+(nr-2)*ns+k,1+(nr-2)*ns+(k+1)%ns])
    return np.array(tri)

if __name__=='__main__':
    body=np.fromfile(ROOT.parent/'assets/positions.bin',dtype='<f4').reshape(-1,3).astype(float)
    cage=np.fromfile(ROOT.parent/'houdini/cage-v3-1x.bin',dtype='<f4').reshape(-1,3).astype(float)
    faces=cage_faces();active=region(body)>0;steps=24;epsilon=1e-5
    cases=[(2,{}),(3,{}),(4,{}),(2,{'lateral':.4,'vertical':1.6,'projection':.4})]
    report={'method':'Stationary velocity RK4 research prototype','steps':steps,'body_points':len(body),
            'jacobian_epsilon':epsilon,'limits':'Sampled field Jacobians; no contact certification, no native/VEX implementation, no established visual match.', 'cases':[]}
    for ratio,controls in cases:
        start=time.perf_counter();duration,cp=calibrate(cage,faces,ratio,controls,steps)
        solve_seconds=time.perf_counter()-start
        start=time.perf_counter();p=flow(body,duration,controls,steps);cook_seconds=time.perf_counter()-start
        start=time.perf_counter();jac=np.empty((len(body),3,3))
        for k in range(3):
            off=np.zeros_like(body);off[:,k]=epsilon
            jac[:,:,k]=(flow(body+off,duration,controls,steps)-flow(body-off,duration,controls,steps))/(2*epsilon)
        determinants=np.linalg.det(jac)
        case={'ratio':ratio,'controls':controls,'duration':duration,'actual_cage_ratio':volume(cp,faces)/volume(cage,faces),
              'sampled_active_min_jacobian':float(determinants[active].min()),
              'negative_active_jacobians':int((determinants[active]<=0).sum()),
              'height_drift':float(np.ptp(p[:,1])-np.ptp(body[:,1])),
              'protected_displacement':float(abs(p[~active]-body[~active]).max()),
              'finite_positions':bool(np.isfinite(p).all()),
              'cage_calibration_seconds':solve_seconds,'full_body_flow_seconds':cook_seconds,
              'jacobian_audit_seconds':time.perf_counter()-start}
        report['cases'].append(case);print(json.dumps(case),flush=True)
    (ROOT/'rear-flow-prototype-results.json').write_text(json.dumps(report,indent=2))
