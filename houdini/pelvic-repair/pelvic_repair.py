"""A localized, sewn structural skin bridge for the flawed Rainee proxy.

No anatomical interior or genital detail is constructed. Original positions
are retained verbatim. Four source triangles with locally manifold edges are
carved; one connected saddle-shaped surface is sewn to their exact indices.
This is a repair candidate, not a watertight retopology of the whole body.
"""
from pathlib import Path
import json, math
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT=Path(__file__).resolve().parent
APP=ROOT.parents[1]
DEFAULTS={'center':[0.,.574,0.],'radius':[.036,.023,.055],
          'saddle_drop':.030,'rings':40,'segments':64,
          'source_targets':[[0.,.590,.054],[0.,.577,-.050],[-.028,.553,.02],[.028,.553,.02]]}

def edge_counts(f):
    ed=np.sort(np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]])),axis=1)
    return np.unique(ed,axis=0,return_counts=True)

def _shape(c):
    center=np.asarray(c['center']);rad=np.asarray(c['radius']);nr=c['rings'];ns=c['segments']
    # Latitudes about Y; drop lateral sides smoothly to create a groin saddle.
    points=[[0.,-1.,0.]];faces=[]
    for j in range(1,nr):
        phi=-math.pi/2+math.pi*j/nr
        for k in range(ns):
            a=2*math.pi*k/ns
            points.append([math.cos(phi)*math.cos(a),math.sin(phi),math.cos(phi)*math.sin(a)])
    points.append([0.,1.,0.]);top=len(points)-1
    for k in range(ns):faces.append([0,1+k,1+(k+1)%ns])
    for j in range(nr-2):
        for k in range(ns):
            a=1+j*ns+k;b=1+j*ns+(k+1)%ns;c2=a+ns;d=b+ns
            faces.extend([[a,c2,b],[b,c2,d]])
    for k in range(ns):faces.append([top,1+(nr-2)*ns+(k+1)%ns,1+(nr-2)*ns+k])
    unit=np.array(points);v=unit*rad+center
    v[:,1]-=c['saddle_drop']*unit[:,0]**2
    # The flawed source's anterior flap tapers sharply toward its lower edge.
    # Keep this structural bridge behind its visible pubic contour rather than
    # adding an anterior bulb; the connecting underside remains smooth.
    anterior=v[:,2]>0
    cap=np.clip(.020+1.5*(v[:,1]-.561),.018,.055)
    v[anterior,2]=cap[anterior]*np.tanh(v[anterior,2]/cap[anterior])
    f=np.asarray(faces,dtype=np.uint32)
    if np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()<0:f=f[:,::-1]
    return v,f

def build(source_positions,source_faces,config=None):
    """Return repaired positions, triangles, a deformation recipe, and report.

    A future existing source deformation can be propagated using transfer().
    The resulting bridge uses the source vertices at its four seams; there
    are no coincident duplicate seam points or disconnected hiding objects.
    """
    c={**DEFAULTS,**(config or {})};v=np.asarray(source_positions,dtype=np.float64)
    f=np.asarray(source_faces,dtype=np.uint32)
    ed,counts=edge_counts(f);countmap={tuple(q):int(n) for q,n in zip(ed,counts)}
    manifold=np.array([all(countmap[tuple(sorted(e))]==2 for e in [(a,b),(b,c2),(c2,a)]) for a,b,c2 in f])
    centroid=v[f].mean(1)
    local=(np.abs(centroid[:,0])<.062)&(centroid[:,1]>.525)&(centroid[:,1]<.603)&manifold
    ids=np.flatnonzero(local);tree=cKDTree(centroid[ids]);anchors=[];chosen_vertices=set()
    for target in c['source_targets']:
        dd,ii=tree.query(target,k=min(64,len(ids)))
        for distance,index in zip(np.atleast_1d(dd),np.atleast_1d(ii)):
            fi=int(ids[index])
            if not chosen_vertices.intersection(f[fi].tolist()):break
        else:raise ValueError('Cannot find distinct locally manifold source seams')
        anchors.append(fi);chosen_vertices.update(f[fi].tolist())
    patch,pf=_shape(c);pc=patch[pf].mean(1);pt=cKDTree(pc);panchors=[];pch=set()
    for ai in anchors:
        _,ii=pt.query(centroid[ai],k=100)
        for fi in np.atleast_1d(ii):
            fi=int(fi)
            if not pch.intersection(pf[fi].tolist()):break
        else:raise ValueError('Patch seam selection failed')
        panchors.append(fi);pch.update(pf[fi].tolist())
    nv=len(v);sewn=[];source_seams=[];patch_seams=[]
    for ai,bi in zip(anchors,panchors):
        aa=f[ai].tolist();bb=(pf[bi][::-1]+nv).tolist()
        # Match cyclic corners to minimize annulus twisting, preserving winding.
        rotations=[bb[j:]+bb[:j] for j in range(3)]
        bb=min(rotations,key=lambda q:sum(np.linalg.norm(v[a]-patch[b-nv]) for a,b in zip(aa,q)))
        source_seams.extend([[aa[i],aa[(i+1)%3]] for i in range(3)])
        patch_seams.extend([[bb[i],bb[(i+1)%3]] for i in range(3)])
        for i in range(3):
            a=aa[i];an=aa[(i+1)%3];b=bb[i];bn=bb[(i+1)%3]
            sewn.extend([[a,an,bn],[a,bn,b]])
    sourcekeep=np.ones(len(f),bool);sourcekeep[anchors]=False
    patchkeep=np.ones(len(pf),bool);patchkeep[panchors]=False
    outv=np.vstack((v,patch)).astype('<f4')
    outf=np.vstack((f[sourcekeep],pf[patchkeep]+nv,np.array(sewn,dtype=np.uint32))).astype('<u4')
    # Small deterministic skin-space interpolation table for subsequent body states.
    # Uses at most eight nearby original points; requires only NumPy at runtime.
    distance,near=cKDTree(v).query(patch,k=8)
    weight=1/np.maximum(distance,.0001)**2;weight/=weight.sum(1)[:,None]
    recipe={'source_count':nv,'source_faces':f,'removed_source_faces':np.array(anchors),
            'baseline_source':v.astype('<f4'),'new_baseline':patch.astype('<f4'),
            'nearest_source':near.astype('<u4'),'weights':weight.astype('<f4'),
            'triangles':outf,'source_seam_edges':np.array(source_seams,dtype='<u4')}
    e2,c2=edge_counts(outf);cm2={tuple(q):int(n) for q,n in zip(e2,c2)}
    newedges=(e2[:,1]>=nv)
    seam_incidence=[cm2[tuple(sorted(e))] for e in source_seams]
    n,label=connected_components(coo_matrix((np.ones(len(e2)),(e2[:,0],e2[:,1])),shape=(len(outv),len(outv))),directed=False)
    patchlabels=np.unique(label[nv:]);anchorl=np.unique(label[np.array(source_seams).ravel()])
    area=np.linalg.norm(np.cross(outv[outf[:,1]]-outv[outf[:,0]],outv[outf[:,2]]-outv[outf[:,0]]),axis=1)/2
    report={'method':'Sewn saddle bridge through four carved manifold triangle seams',
            'source_points':len(v),'source_triangles':len(f),'output_points':len(outv),'output_triangles':len(outf),
            'new_patch_points':len(patch),'new_bridge_triangles':int(patchkeep.sum()+len(sewn)),
            'carved_source_triangles':anchors,'source_anchor_centroids':centroid[anchors].tolist(),
            'source_unchanged_max_displacement':float(np.max(np.abs(outv[:nv]-source_positions))),
            'source_height':float(np.ptp(source_positions[:,1])),'output_height':float(np.ptp(outv[:,1])),
            'source_boundary_edges':int((counts==1).sum()),'source_nonmanifold_edges':int((counts>2).sum()),
            'output_boundary_edges':int((c2==1).sum()),'output_nonmanifold_edges':int((c2>2).sum()),
            'new_edge_count':int(newedges.sum()),'new_edges_all_two_faces':bool(np.all(c2[newedges]==2)),
            'source_seam_edge_face_counts':seam_incidence,'seam_edges_all_two_faces':all(n==2 for n in seam_incidence),
            'bridge_one_connected_component':len(patchlabels)==1 and np.array_equal(patchlabels,anchorl),
            'zero_area_faces':int((area<1e-12).sum()),'finite':bool(np.isfinite(outv).all()),
            'added_bounds':{'min':patch.min(0).tolist(),'max':patch.max(0).tolist()},
            'config':c,'status':'Connected local structural repair candidate; whole source remains nonmanifold',
            'limits':['Source/patch overlap is not boolean-unioned; local visual and collision review is required.',
                      'Four small annulus seams are a graft, not production anatomical retopology.',
                      'Whole-body preexisting boundary and nonmanifold defects remain; do not pressure-simulate this render surface.',
                      'Only normal external structural continuity is addressed; no genital detail or internal anatomy.']}
    return outv,outf,recipe,report

def transfer(source_state,recipe):
    """Move the repair with a deformed original topology without a detached seam."""
    state=np.asarray(source_state,dtype='<f4')
    if len(state)!=int(recipe['source_count']):raise ValueError('Source topology point count differs')
    d=state-recipe['baseline_source']
    offset=(d[recipe['nearest_source']]*recipe['weights'][:,:,None]).sum(1)
    return np.vstack((state,recipe['new_baseline']+offset)).astype('<f4')

def write_obj(path,v,f):
    with Path(path).open('w',encoding='utf-8') as o:
        o.write('# Rainee localized sewn external pelvic repair candidate\n')
        for p in v:o.write('v %.9g %.9g %.9g\n'%tuple(p))
        for t in f:o.write('f %d %d %d\n'%tuple(t+1))

if __name__=='__main__':
    base=np.fromfile(APP/'assets/positions.bin','<f4').reshape(-1,3)
    faces=np.fromfile(APP/'assets/triangles.bin','<u4').reshape(-1,3)
    v,f,recipe,report=build(base,faces)
    v.tofile(ROOT/'repaired-positions.bin');f.tofile(ROOT/'repaired-triangles.bin')
    np.savez_compressed(ROOT/'repair-recipe.npz',**recipe)
    (ROOT/'repair-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    write_obj(ROOT/'Rainee-pelvic-repair.obj',v,f)
    from inspect_proxy import render
    render(v,f,ROOT/'repaired-front.png');render(v,f,ROOT/'repaired-back.png',camera='back')
    print(json.dumps(report,indent=2))
