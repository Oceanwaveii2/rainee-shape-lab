"""Verify local ellipsoid shape fits independently on known rotated geometry."""
import json
from pathlib import Path
import numpy as np
from local_shape_constraints import fit_ellipsoid, fit_ferrari_nurbs_patch

def main():
    lat=np.linspace(.03,np.pi-.03,30);lon=np.linspace(0,2*np.pi,60,endpoint=False)
    lat,lon=np.meshgrid(lat,lon,indexing='ij')
    sphere=np.column_stack([np.sin(lat.ravel())*np.cos(lon.ravel()),np.sin(lat.ravel())*np.sin(lon.ravel()),np.cos(lat.ravel())])
    a=.4;b=.7;Rz=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    Ry=np.array([[np.cos(b),0,np.sin(b)],[0,1,0],[-np.sin(b),0,np.cos(b)]])
    center=np.array([.3,-.1,.25]);radii=np.array([.2,.16,.13]);points=(sphere*radii)@(Rz@Ry).T+center
    weights=np.sin(lat.ravel());fit=fit_ellipsoid(points,weights)
    assert fit['status']=='surface_patch_fit'
    assert np.allclose(fit['center_source'],center,atol=1e-8)
    assert np.allclose(sorted(fit['principal_radii_source']),sorted(radii),atol=1e-8)
    translated=fit_ellipsoid(points*7+np.array([-3,6,2]),weights)
    assert abs(fit['axis_ratio_largest_to_smallest']-translated['axis_ratio_largest_to_smallest'])<1e-8
    assert fit['implicit_residual_rms']<1e-8
    nurbs_fit=fit_ferrari_nurbs_patch(points,weights)
    assert nurbs_fit['status']=='experimental_radial_nurbs_fit' and nurbs_fit['radial_residual_rms']<0.05
    assert not nurbs_fit['class_a_certified'] and not nurbs_fit['anatomical_acceptance']
    degenerate=fit_ellipsoid(np.zeros((20,3)),np.zeros(20));assert degenerate['status']=='insufficient_nondegenerate_samples'
    result={'passed':True,'checks':['known rotated ellipsoid center and principal radii recovered',
        'dimensionless axis ratio preserved under translation and scale','degenerate surface samples rejected'],
        'scope':'geometric fitter correctness; does not validate target anatomical ROI acceptance or correspondence'}
    Path(__file__).with_name('verification-local-shapes.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__':main()
