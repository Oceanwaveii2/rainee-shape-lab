"""Package the local implicit union with source-index-compatible deformation data."""
from pathlib import Path
import numpy as np,json
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pelvic_repair import edge_counts,write_obj
from inspect_proxy import render
R=Path(__file__).resolve().parent;A=R.parents[1]/'assets'
base=np.fromfile(A/'positions.bin','<f4').reshape(-1,3);bf=np.fromfile(A/'triangles.bin','<u4').reshape(-1,3)
rv=np.fromfile(R/'local-vdb-positions.bin','<f4').reshape(-1,3);rf=np.fromfile(R/'local-vdb-triangles.bin','<u4').reshape(-1,3)
tree=cKDTree(base);dist,idx=tree.query(rv)
exact=dist<1e-7
new=rv[~exact];remap=np.zeros(len(rv),dtype='<u4');remap[exact]=idx[exact];remap[~exact]=len(base)+np.arange(len(new))
v=np.vstack((base,new)).astype('<f4');f=remap[rf]
# Boolean performs incidental cleanup of damaged source triangles even away
# from an intersection. Use its triangles only inside a padded repair box;
# outside that box, restore the original triangle records verbatim.
lo=np.array([-.077,.495,-.123]);hi=np.array([.077,.665,.113])
def touches_box(points,tri):
 q=points[tri];inside=((q>=lo)&(q<=hi)).all(2)
 center=q.mean(1);return inside.any(1)|((center>=lo)&(center<=hi)).all(1)
source_local=touches_box(base,bf);native_local=touches_box(v,f)
f=np.vstack((bf[~source_local],f[native_local]))
# Repeated remapped corners are discarded; they were already below float epsilon.
valid=(f[:,0]!=f[:,1])&(f[:,1]!=f[:,2])&(f[:,2]!=f[:,0]);f=f[valid]
usednew=np.unique(f[f>=len(base)])-len(base)
nr=np.zeros(len(new),dtype='<u4');nr[usednew]=np.arange(len(usednew))+len(base)
newmask=f>=len(base);f[newmask]=nr[f[newmask]-len(base)];new=new[usednew];v=np.vstack((base,new)).astype('<f4')
distance,near=tree.query(new,k=8);weights=1/np.maximum(distance,.0001)**2;weights/=weights.sum(1)[:,None]
np.savez_compressed(R/'implicit-repair-recipe.npz',source_count=len(base),baseline_source=base,new_baseline=new,
 nearest_source=near.astype('<u4'),weights=weights.astype('<f4'),triangles=f)
v.tofile(R/'implicit-repaired-positions.bin');f.tofile(R/'implicit-repaired-triangles.bin');write_obj(R/'Rainee-local-implicit-repair.obj',v,f)
e,c=edge_counts(f);mid=v[e].mean(1)
center=np.array([0.,.579,-.005]);radius=np.array([.07,.077,.111]);r=((mid-center)/radius)**2;r=r.sum(1)
core=(np.abs(mid[:,0])<.030)&(mid[:,1]>.539)&(mid[:,1]<.613)&(mid[:,2]>-.063)&(mid[:,2]<.070)
newbounds={'min':new.min(0).tolist(),'max':new.max(0).tolist()}
n,label=connected_components(coo_matrix((np.ones(len(e)),(e[:,0],e[:,1])),shape=(len(v),len(v))),directed=False)
active=np.unique(f);la,lc=np.unique(label[active],return_counts=True);main=la[np.argmax(lc)]
targetpoints=np.array([[0.,.6,.06],[0.,.571,-.05],[-.028,.553,.02],[.028,.553,.02]])
_,ti=cKDTree(v[active]).query(targetpoints);tl=label[active[ti]]
outside_new=np.sum((((new-center)/radius)**2).sum(1)>1.002)
origused=np.unique(bf);nowused=np.unique(f);before_height=float(np.ptp(base[origused,1]));after_height=float(np.ptp(v[nowused,1]))
native=json.loads((R/'local-vdb-native-report.json').read_text())
report={'method':'Local implicit skin replacement with overlapping cut volumes and native polygon union',
 'output_points':len(v),'output_triangles':len(f),'new_points':len(new),'source_points_retained_for_binding':len(base),
 'new_point_bounds':newbounds,'new_points_outside_repair_ellipsoid':int(outside_new),
 'distant_source_coordinates_max_shift':0.,'distant_source_triangles_restored_verbatim':int((~source_local).sum()),
 'strict_local_composition_box':{'min':lo.tolist(),'max':hi.tolist()},
 'height_all_points_drift':float(np.ptp(v[:,1])-np.ptp(base[:,1])),
 'height_rendered_surface_before':before_height,'height_rendered_surface_after':after_height,'height_rendered_surface_drift':after_height-before_height,
 'whole_mesh_boundary_edges':int((c==1).sum()),'whole_mesh_nonmanifold_edges':int((c>2).sum()),
 'core_edges':int(core.sum()),'core_boundary_edges':int(((c==1)&core).sum()),'core_nonmanifold_edges':int(((c>2)&core).sum()),
 'joined_core_attachment_points_same_component':bool(np.all(tl==main)),'attachments_labels':tl.tolist(),
 'rendered_connected_components':int(len(la)),'largest_component_referenced_points':int(lc.max()),
 'finite':bool(np.isfinite(v).all()),'native_errors':{k:x['errors'] for k,x in native['nodes'].items()},
 'native_warning_summary':'Original solid A has crossed unshared boundary edges in both carve and union. Incidental distant Boolean edits were replaced with original source triangles; boundary defects at the overlap collar remain.',
 'voxel_size_normalized_height':.0015,'limits':['Outer overlap collar shows a small visible transition; future retopology/detail transfer needed.',
 'Original whole-body boundary/nonmanifold defects outside the replacement persist.',
 'This is a coarse external structural repair candidate, not genital/internal anatomical sculpture.',
 'Deformation binding uses nearby source-point offsets; extreme motion requires renewed seam/collision checks.']}
(R/'implicit-repair-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
render(v,f,R/'implicit-repaired-front.png');render(v,f,R/'implicit-repaired-back.png',camera='back')
