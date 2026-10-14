"""Independent numerical regressions for experimental v6 helpers; no donor likeness claims."""
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import numpy as np
from scipy.interpolate import BSpline
import butt_data_supercomputer_v6 as b
import model_compare as m


def raises(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError('Invalid input was not rejected')


def fixture_glb(path):
    p=np.array([[0,0,0],[1,0,0],[0,1,0]],dtype='<f4')
    n=np.tile([0,0,1],(3,1)).astype('<f4')
    indices=np.array([0,1,2],dtype='<u4')
    binary=p.tobytes()+n.tobytes()+indices.tobytes()
    doc={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0,2]}],
        'nodes':[{'translation':[2,3,4],'children':[1]}, {'mesh':0,'scale':[-2,3,4]}, {'mesh':0,'translation':[0,0,10]}],
        'meshes':[{'primitives':[{'attributes':{'POSITION':0,'NORMAL':1},'indices':2}]}],
        'buffers':[{'byteLength':len(binary)}],
        'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36},{'buffer':0,'byteOffset':36,'byteLength':36},{'buffer':0,'byteOffset':72,'byteLength':12}],
        'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'},
            {'bufferView':1,'componentType':5126,'count':3,'type':'VEC3'}, {'bufferView':2,'componentType':5125,'count':3,'type':'SCALAR'}]}
    def write():
        js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
        path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary)
    write()
    return doc,write


def main():
    checks=[]
    y=np.linspace(0,1,25);theta=np.linspace(-math.pi,math.pi,96,endpoint=False)
    r=np.full((len(y),len(theta)),2.0)
    mean,gauss,shape=b.radial_chart_curvature(r,y,theta)
    assert np.allclose(mean,-.25,atol=1e-12) and np.allclose(gauss,0,atol=1e-12)
    assert np.allclose(shape,-.5,atol=1e-12)
    checks.append('radius-two cylinder has outward mean curvature -1/4, Gaussian 0, shape index -1/2')
    theta2=np.linspace(-math.pi,math.pi,240,endpoint=False)
    points=np.array([[np.cos(t),yy,np.sin(t)] for yy in np.linspace(0,1,112) for t in theta2])
    dem=b.extract_intrinsic_butt_dem(points,0,1,0,0)
    assert np.allclose(dem['mean_curvature'],-.5,atol=1e-10)
    assert dem['observed_mask'].any() and (~dem['observed_mask']).any()
    assert np.isnan(dem['sampled_elevation'][~dem['observed_mask']]).all()
    assert np.isfinite(dem['elevation']).all() and not dem['anatomical_calibration']
    checks.append('DEM curvature survives extraction and completed bins remain explicitly unobserved')
    raises(lambda:b.extract_intrinsic_butt_dem(np.empty((0,3))))
    raises(lambda:b.extract_intrinsic_butt_dem(np.zeros((12,3))))
    raises(lambda:b.extract_intrinsic_butt_dem(points,y_fold_norm=.6,y_waist_norm=.5))
    raises(lambda:b.extract_intrinsic_butt_dem(points,n_y=2))
    raises(lambda:b._fill_empty_bins(np.full((3,4),np.nan)))
    checks.append('empty, degenerate, reversed-landmark, low-resolution and entirely unobserved charts reject')
    _,cal=m.calibrated_intrinsic_pelvic(points,{'y_fold_norm':0,'y_waist_norm':1,'cleft_yaw_offset_deg':0,'spinal_torsion_deg':0})
    assert cal['status']=='provisional_manual_pelvic_chart' and not cal['comparison_ready']
    checks.append('manual bbox assumptions do not grant anatomical calibration')
    with tempfile.TemporaryDirectory(prefix='rainee-v6-test-') as folder:
        path=Path(folder)/'scene.glb';doc,write=fixture_glb(path)
        p,n,t=b.load_glb_vertices_and_normals(path)
        assert np.allclose(p[:3],[[2,3,4],[0,3,4],[2,6,4]]) and np.allclose(p[3:],[[0,0,10],[1,0,10],[0,1,10]])
        assert np.array_equal(t,[[0,2,1],[3,4,5]]) and np.allclose(n[:,2],1)
        doc['animations']=[{}];write();raises(lambda:b.load_glb_vertices_and_normals(path))
    checks.append('GLB active-scene instances, parent transform and reflected winding preserved; unevaluated animation rejected')
    u=np.linspace(0,1,9);v=np.linspace(0,1,7);z=3*u[:,None]+2*v[None,:]
    fit=b.fit_bicubic_nurbs_patch(z,5,4,1,0)
    assert fit['rms_error']<1e-12 and np.allclose([fit['reconstructed'][0,0],fit['reconstructed'][-1,-1]],[0,5],atol=1e-12)
    assert not fit['class_a_certified']
    raises(lambda:b.fit_bicubic_nurbs_patch(z,n_ctrl_u=3))
    raises(lambda:b.fit_bicubic_nurbs_patch(z,w_ridge=0))
    raises(lambda:b.fit_bicubic_nurbs_patch(z,knots_u=np.zeros(9)))
    checks.append('clamped spline reproduces a plane including endpoints; malformed knots/control grids reject')
    rng=np.random.default_rng(12)
    ctrl=rng.normal(size=(6,5));weights=1+rng.random((6,5))
    ku=np.array([2,2,2,2,3,6,8,8,8,8],dtype=float)
    kv=np.array([0,0,0,0,.35,1,1,1,1],dtype=float)
    samples=[(0,0),(.1,.9),(.43,.57),(1,1)]
    expected=[]
    for su,sv in samples:
        bu=BSpline(ku,np.eye(6),3)(2+6*su);bv=BSpline(kv,np.eye(5),3)(sv)
        phi=bu[:,None]*bv[None,:]*weights
        expected.append(float(np.sum(phi*ctrl)/np.sum(phi)))
    payload={'control':ctrl.tolist(),'weights':weights.tolist(),'knotsU':ku.tolist(),'knotsV':kv.tolist(),'samples':samples}
    js=Path(__file__).with_name('butt-data-supercomputer-v6.mjs').as_uri()
    program=f"import {{evaluateRationalBicubicNurbs as e}} from {json.dumps(js)};let raw='';for await(const c of process.stdin)raw+=c;const p=JSON.parse(raw);console.log(JSON.stringify(p.samples.map(([u,v])=>e(p.control,p.weights,u,v,p))));"
    node=shutil.which('node')
    if not node:raise RuntimeError('Node.js required for cross-language regression')
    result=subprocess.run([node,'--input-type=module','-e',program],input=json.dumps(payload),text=True,capture_output=True,check=True)
    assert np.allclose(json.loads(result.stdout),expected,atol=1e-12)
    checks.append('Python SciPy and JavaScript rational cubic evaluation agree on nonuniform explicit knots and endpoints')
    pca=b.ButtMorphableModel(2);pca.add_donor('single',np.ones((3,4)))
    assert np.allclose(pca.variance_ratio,0)
    pca.add_donor('second',np.full((3,4),2.0))
    projection=pca.project(np.full((3,4),1.5));assert projection['rms_error']<1e-12
    raises(lambda:pca.project(np.full((3,4),np.nan)))
    raises(lambda:pca.project(np.ones((4,3))))
    raises(lambda:b.ButtMorphableModel(0))
    checks.append('batch PCA records absent single-donor variance and rejects partial/nonfinite or mismatched charts')
    print(json.dumps({'passed':True,'checks':checks,'scope':'Synthetic numerical correctness; no calibrated donor alignment, likeness, Class-A or hidden anatomy validation'},indent=2))


if __name__=='__main__':main()
