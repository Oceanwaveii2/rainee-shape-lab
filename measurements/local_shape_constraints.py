"""Provisional local shape descriptors from manually specified 3D surface ROIs.

Texture classifications are candidate filters, not accepted anatomical labels.
All measurements use source geometry; no global body height transfer occurs.
"""
import argparse,hashlib,json
from array import array
from pathlib import Path
import numpy as np
from PIL import Image
import model_compare as m

def obj_uvs(source):
    uv=array('f');faceuv=array('i')
    with source.open('r',encoding='utf-8',errors='replace') as stream:
        for line in stream:
            if line.startswith('vt '):uv.extend(map(float,line.split()[1:3]))
            elif line.startswith('f '):
                n=len(uv)//2;indices=[]
                for token in line.split()[1:]:
                    chunks=token.split('/');i=int(chunks[1]) if len(chunks)>1 and chunks[1] else 0
                    indices.append(i-1 if i>0 else n+i if i<0 else -1)
                for k in range(1,len(indices)-1):faceuv.extend((indices[0],indices[k],indices[k+1]))
    return np.asarray(uv).reshape(-1,2),np.asarray(faceuv).reshape(-1,3)

def candidate_roles(source,texture,faces):
    uv,uvfaces=obj_uvs(source)
    if len(uvfaces)!=len(faces) or (uvfaces<0).any():raise ValueError('UV triangles missing or do not correspond to source geometry')
    tex=Image.open(texture).convert('RGB');tex.thumbnail((2048,2048));rgb=np.asarray(tex)
    coords=uv[uvfaces].mean(1);w,h=tex.size
    px=np.clip(np.floor(coords[:,0]*w).astype(int),0,w-1);py=np.clip(np.floor((1-coords[:,1])*h).astype(int),0,h-1)
    colors=rgb[py,px]/255.;r,g,b=colors.T
    roles=np.zeros(len(faces),dtype=np.uint8)
    skin=(r>.45)&(g>.25)&(r>g*1.04)&(g>b*1.025)&((r-g)<.39)
    purple=(b>g*1.35)&(r>g*1.25)&(b>r*.95)&(b>.18)
    hair=(r>g*1.6)&(r>b*1.35)&(g<.45)&(r>.25)
    roles[skin]=1;roles[purple]=2;roles[hair]=3
    return roles,{'method':'Triangle-centroid UV nearest color, base color downsampled to max2048px; explicit RGB candidate rules',
        'labels':{'0':'other / unknown','1':'skin-colored candidate','2':'purple garment candidate','3':'red hair candidate'},
        'counts':{str(i):int((roles==i).sum()) for i in range(4)},
        'confidence':'Provisional color segmentation; highlights, seams and generated material errors may misclassify geometry.'}

def fit_ellipsoid(points,weights):
    # Geometric fit to sampled visible surface patch. It is not an internal tissue
    # volume or proof of anatomical correctness. Missing coverage is explicit.
    valid=np.isfinite(points).all(1)&np.isfinite(weights)&(weights>0)
    points,weights=points[valid],weights[valid]
    if len(points)<10:return {'status':'insufficient_nondegenerate_samples'}
    origin=points.mean(0);scale=np.sqrt(np.mean(np.sum((points-origin)**2,axis=1)))
    if scale<1e-9:return {'status':'degenerate'}
    p=(points-origin)/scale;x,y,z=p.T
    A=np.column_stack([x*x,y*y,z*z,2*x*y,2*x*z,2*y*z,x,y,z,np.ones(len(x))])
    A*=np.sqrt(weights/weights.mean())[:,None]
    _,_,vh=np.linalg.svd(A,full_matrices=False);c=vh[-1]
    Q=np.array([[c[0],c[3],c[4]],[c[3],c[1],c[5]],[c[4],c[5],c[2]]])
    if np.linalg.eigvalsh(Q).max()<0:Q=-Q;c=-c
    eig,vec=np.linalg.eigh(Q)
    if eig.min()<=1e-8:return {'status':'no_positive_definite_ellipsoid','reason':'Selected patch does not support a bounded ellipsoid fit'}
    center=-.5*np.linalg.solve(Q,c[6:9]);k=center@Q@center-c[9]
    if k<=0:return {'status':'no_positive_radius'}
    radii=np.sqrt(k/eig)*scale
    ellvalue=np.einsum('ni,ij,nj->n',p-center,Q,p-center)/k
    residual=float(np.sqrt(np.average((ellvalue-1)**2,weights=weights)))
    displacement=points-(center*scale+origin)
    directions=displacement/np.maximum(np.linalg.norm(displacement,axis=1)[:,None],1e-12)
    return {'status':'surface_patch_fit','center_source':(center*scale+origin).tolist(),
        'principal_radii_source':radii.tolist(),'principal_axes_source_columns':vec.tolist(),
        'axis_ratio_largest_to_smallest':float(radii.max()/radii.min()),'implicit_residual_rms':residual,
        'directional_coverage_bounds':m.bounds(directions),
        'limitation':'Open selected surface patch; inferred back of ellipsoid is unconstrained by ROI. This is a shape cue, not enclosed anatomical volume.'}

def describe(p,f,selection,config,lateral_midline):
    tri=p[f];centroid=tri.mean(1)
    area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
    low=np.asarray(config['min']);high=np.asarray(config['max'])
    keep=selection & np.all((centroid>=low)&(centroid<=high),axis=1)
    selected=f[keep];points=p[np.unique(selected)]
    if not len(selected):return {'status':'empty_roi'}
    result={'status':'provisional_geometric_roi','source_bounds':m.bounds(points),'selected_triangles':len(selected),
        'selected_surface_area_source_units_squared':float(area[keep].sum()),'explicit_roi':config,
        'selection_rule':'Texture candidate roles + source-space triangle centroid inside ROI; boundary triangles may extend slightly beyond ROI.',
        'stature_transfer':False,'anatomical_acceptance':False}
    oriented=p@m.basis({'right_axis':'z','up_axis':'y','front_axis':'x'}).T
    ys=np.linspace(low[1],high[1],31);sections=m.cross_sections(oriented,selected,ys)
    valid=[s for s in sections if s['valid']]
    result['source_y_sections']=sections
    if valid:
        width=max(s['width'] for s in valid);depth=max(s['depth'] for s in valid);height=high[1]-low[1]
        result['local_extent_constraints']={'max_lateral_width':width,'max_depth':depth,'roi_height':height,
            'depth_over_lateral_width':depth/width if width else None,'width_over_roi_height':width/height,
            'depth_over_roi_height':depth/height,'ratio_fields_source_unit_independent':True}
    for name,lateral in [('negative_z_lobe',(-np.inf,lateral_midline)),('positive_z_lobe',(lateral_midline,np.inf))]:
        lobemask=keep&(centroid[:,2]>=lateral[0])&(centroid[:,2]<lateral[1])
        samples=centroid[lobemask];weights=area[lobemask]
        if len(samples)>30000:
            indices=np.linspace(0,len(samples)-1,30000).astype(int);samples=samples[indices];weights=weights[indices]
        result[name]=fit_ellipsoid(samples,weights) if len(samples)>20 else {'status':'insufficient_patch'}
    return result,keep

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inventory',required=True);parser.add_argument('--config',required=True);args=parser.parse_args()
    folder=Path(args.inventory);config=json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
    p,f,t,ids=m.cached(folder);source=folder/'model.obj';texture=folder/'textures/base_color.png'
    roles,method=candidate_roles(source,texture,f)
    selection=np.isin(roles,config.get('candidate_role_ids',[1,2]));selection.astype('u1').tofile(folder/'candidate-body-face-mask.bin')
    roles.tofile(folder/'candidate-face-roles.bin')
    # Associate each source vertex with the majority class of its incident faces.
    counts=np.zeros((len(p),4),dtype=np.int32)
    for i in range(4):
        for corner in range(3):np.add.at(counts[:,i],f[roles==i,corner],1)
    vroles=counts.argmax(1);m.preview(p,vroles,folder/'texture-role-candidates.png',"Full asset; skin / purple garment / red hair candidates")
    reports={};masks={}
    for name,roi in config['regions'].items():
        reports[name],masks[name]=describe(p,f,selection,roi,config.get('source_lateral_midline',0))
    # A separate geometry preview shows candidate rear/waist/upper thigh ROI cuts.
    roiids=np.zeros(len(p),dtype=np.int32)
    for i,name in enumerate(config['regions'],1):roiids[np.unique(f[masks[name]])]=i
    m.preview(p,roiids,folder/'local-roi-preview.png',"Full asset; cyan rear / orange waist / blue upper thigh ROI")
    from scipy.spatial import cKDTree
    proxy=np.fromfile(folder/'preview-positions.bin',dtype='<f4').reshape(-1,3)
    _,nearest=cKDTree(p).query(proxy)
    palette=np.array([[.64,.65,.7],[.96,.71,.59],[.44,.15,.68],[.64,.08,.06]],dtype='<f4')
    palette[vroles[nearest]].tofile(folder/'preview-colors.bin')
    roipalette=np.array([[.28,.3,.36],[.18,.83,.8],[1,.58,.2],[.24,.5,1]],dtype='<f4')
    roipalette[roiids[nearest]].tofile(folder/'preview-roi-colors.bin')
    rear=reports.get('rear');waist=reports.get('waist')
    ratios={}
    if rear and waist and rear.get('local_extent_constraints') and waist.get('local_extent_constraints'):
        a=rear['local_extent_constraints'];b=waist['local_extent_constraints']
        ratios={'rear_to_waist_width':a['max_lateral_width']/b['max_lateral_width'],
            'rear_to_waist_depth':a['max_depth']/b['max_depth'],
            'scope':'Real selected surface extents, dimensionless; provisional ROIs and segmentation, no foreign stature/pose transfer.'}
    source_inventory=json.loads((folder/'inventory.json').read_text(encoding='utf-8'))
    report={'source':str(source.resolve()),'source_sha256':source_inventory['source_sha256'],
        'roi_config_sha256':hashlib.sha256(Path(args.config).read_bytes()).hexdigest(),
        'status':'provisional_local_surface_constraints','global_comparison_ready':False,
        'geometry_source':'actual supplied OBJ, not image-inferred mesh or proxy',
        'axis_semantics':{'source_y':'up','source_x':'front/depth candidate','source_z':'lateral candidate','lobe_partition_source_z':config.get('source_lateral_midline',0)},
        'selection':method,'regions':reports,'local_ratios':ratios,
        'configuration':config,'limitations':['Hair, props, garments and stand fused with body; color filtering is imperfect.',
            'Bent leg and turned torso make full body comparison unsuitable without registration.',
            'Surface fit describes selected outside shape; inferred interior anatomy and tissue volume are not measured.']}
    m.dump(folder/'local-shape-constraints.json',report)
    print(json.dumps({'role_counts':method['counts'],'local_ratios':ratios,'region_triangles':{k:v['selected_triangles'] for k,v in reports.items()}}))
if __name__=='__main__':main()
