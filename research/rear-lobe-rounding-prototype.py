"""Actual-body lobe rounding candidates; research only, not a production edit.

Same point/material correspondence as the proxy. Each fitted source ellipsoid
ray is normalized and mapped to an inflated ellipsoid, then blended into the
authored body. The corrective is zero at neutral inflation, attachment edges,
and a narrow medial band. This is art geometry, not an anatomical inference.
"""
from pathlib import Path
import sys,json,time
import numpy as np
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'rear-rounding';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT.parent/'houdini'))
from rear_model import DEFAULTS,region,smooth,deform,calibrate,volume

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
    weight=strength*region(v)*smooth(.025,.060,ax)*smooth(.30,.65,rho)
    out+=weight[:,None]*(target-out)
    out[region(v)==0]=v[region(v)==0]
    return out

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
    authored=np.fromfile(ROOT.parent/'houdini/body-v3-2.5x.bin',dtype='<f4').reshape(-1,3).astype(float)
    cage=np.fromfile(ROOT.parent/'houdini/cage-v3-1x.bin',dtype='<f4').reshape(-1,3).astype(float)
    faces=cage_faces();amp,_=calibrate(cage,faces,2.5);mask=region(body);active=mask>0;epsilon=1e-5
    assert np.array_equal(round_lobes(body,0),body)
    report={'source_body':'assets/positions.bin','comparison':'houdini/body-v3-2.5x.bin',
            'source_points':len(body),'neutral_identity':True,'authored_ratio':2.5,'amplitude':amp,
            'source_lobe_fit':{'centers_x':[-.073,.073],'center_y':.61,'center_z':-.043,'radii':[.088,.078,.089]},
            'limits':'Actual-body artistic ray normalization; no established visual match, anatomical volume or triangle-contact certification. Corrective changes the measured cage ratio, reported separately.',
            'cases':[]}
    for strength in [.35,.65,.90]:
        start=time.perf_counter();p=round_lobes(body,amp,strength);cook_seconds=time.perf_counter()-start
        jac=np.empty((len(body),3,3))
        for k in range(3):
            off=np.zeros_like(body);off[:,k]=epsilon
            jac[:,:,k]=(round_lobes(body+off,amp,strength)-round_lobes(body-off,amp,strength))/(2*epsilon)
        det=np.linalg.det(jac);cp=round_lobes(cage,amp,strength)
        filename=f'body-2.5x-round-{strength:.2f}.bin';p.astype('<f4').tofile(OUT/filename)
        correction=p-authored
        info={'file':filename,'roundness':strength,'point_count':len(p),'body_cook_seconds':cook_seconds,
              'measured_corrected_cage_ratio':volume(cp,faces)/volume(cage,faces),
              'height_drift':float(np.ptp(p[:,1])-np.ptp(body[:,1])),
              'protected_displacement':float(abs(correction[~active]).max()),
              'minimum_sampled_body_jacobian':float(det[active].min()),
              'negative_sampled_body_jacobians':int((det[active]<=0).sum()),
              'maximum_corrective_displacement':float(np.linalg.norm(correction,axis=1).max()),
              'changed_points':int(np.sum(np.linalg.norm(correction,axis=1)>1e-7)),
              'finite':bool(np.isfinite(p).all()),
              'medial_crossings':int(np.sum(active&(body[:,0]*p[:,0]<0)))}
        report['cases'].append(info);print(json.dumps(info),flush=True)
    # A second comparison maintains the measured closed-cage ratio exactly.
    lo,hi=0.,amp;target_volume=volume(cage,faces)*2.5;strength=.65
    for _ in range(30):
        mid=(lo+hi)/2
        if volume(round_lobes(cage,mid,strength),faces)<target_volume:lo=mid
        else:hi=mid
    fitted_amp=(lo+hi)/2;p=round_lobes(body,fitted_amp,strength)
    jac=np.empty((len(body),3,3))
    for k in range(3):
        off=np.zeros_like(body);off[:,k]=epsilon
        jac[:,:,k]=(round_lobes(body+off,fitted_amp,strength)-round_lobes(body-off,fitted_amp,strength))/(2*epsilon)
    det=np.linalg.det(jac);cp=round_lobes(cage,fitted_amp,strength)
    filename='body-2.5x-round-0.65-volume-fit.bin';p.astype('<f4').tofile(OUT/filename)
    matched={'file':filename,'roundness':strength,'amplitude':fitted_amp,'point_count':len(p),
             'measured_corrected_cage_ratio':volume(cp,faces)/volume(cage,faces),
             'minimum_sampled_body_jacobian':float(det[active].min()),
             'negative_sampled_body_jacobians':int((det[active]<=0).sum()),
             'height_drift':float(np.ptp(p[:,1])-np.ptp(body[:,1])),
             'protected_displacement':float(abs(p[~active]-body[~active]).max()),
             'finite':bool(np.isfinite(p).all()),
             'medial_crossings':int(np.sum(active&(body[:,0]*p[:,0]<0)))}
    report['volume_matched_candidate']=matched;print(json.dumps(matched),flush=True)
    (OUT/'cases.json').write_text(json.dumps(report,indent=2))
