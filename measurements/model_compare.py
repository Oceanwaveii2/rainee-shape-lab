"""CPU-only reference-model inventory and explicitly calibrated shape comparison.

No model generator, diffusion dependency, anatomical inference or topology match.
Python 3 + numpy + Pillow. Original files are read only.
"""
from __future__ import annotations
import argparse, hashlib, json
from array import array
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def bounds(points):
    low, high = points.min(0), points.max(0)
    return {"min": low.tolist(), "max": high.tolist(), "extent": (high-low).tolist()}

def read_obj(path):
    vertices, triangles, face_tags = array("d"), array("I"), array("I")
    tags, tag_ids = [], {}
    objects, groups, materials = Counter(), Counter(), Counter()
    obj, group, material = "", "", ""
    mtllib, poly_sizes = [], Counter()
    with path.open("r", encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if line.startswith("v "):
                values = line.split()
                vertices.extend(map(float, values[1:4]))
            elif line.startswith("f "):
                nv = len(vertices)//3
                indices = [int(v.split("/")[0]) for v in line.split()[1:]]
                indices = [i-1 if i>0 else nv+i for i in indices]
                if min(indices)<0 or max(indices)>=nv:
                    raise ValueError("Invalid OBJ index")
                key = (obj, group, material)
                if key not in tag_ids:
                    tag_ids[key] = len(tags)
                    tags.append({"object":obj, "group":group, "material":material})
                tag = tag_ids[key]
                for i in range(1, len(indices)-1):
                    triangles.extend((indices[0], indices[i], indices[i+1]))
                    face_tags.append(tag)
                objects[obj]+=1; groups[group]+=1; materials[material]+=1
                poly_sizes[len(indices)]+=1
            elif line.startswith("o "): obj=line[2:].strip()
            elif line.startswith("g "): group=line[2:].strip()
            elif line.startswith("usemtl "): material=line[7:].strip()
            elif line.startswith("mtllib "): mtllib.append(line[7:].strip())
    return (np.asarray(vertices).reshape(-1,3), np.asarray(triangles).reshape(-1,3),
            np.asarray(face_tags), {"face_tags":tags,"objects_polygon_counts":dict(objects),
                "groups_polygon_counts":dict(groups),"materials_polygon_counts":dict(materials),
                "mtllib":mtllib,"polygon_size_counts":dict(poly_sizes)})

def components(points, faces):
    # Connectivity is indexed topology, not positional welding: disconnected generated
    # patches and props remain visible even if they share the same object/material tag.
    parent=np.arange(len(points),dtype=np.int32)
    size=np.ones(len(points),dtype=np.int32)
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]; a=int(parent[a])
        return a
    for a,b,c in faces:
        ra=find(int(a))
        for t in (b,c):
            rb=find(int(t))
            if ra!=rb:
                if size[ra]<size[rb]: ra,rb=rb,ra
                parent[rb]=ra; size[ra]+=size[rb]
    labels=np.fromiter((find(i) for i in range(len(points))),dtype=np.int32,count=len(points))
    roots,counts=np.unique(labels,return_counts=True)
    order=np.argsort(-counts)
    root_to_rank={int(roots[i]):rank for rank,i in enumerate(order)}
    ids=np.fromiter((root_to_rank[int(r)] for r in labels),dtype=np.int32,count=len(points))
    face_counts=np.bincount(ids[faces[:,0]],minlength=len(roots))
    summaries=[]
    for cid,i in enumerate(order):
        subset=points[ids==cid]
        summaries.append({"id":cid,"vertices":int(counts[i]),"triangles":int(face_counts[cid]),
                          "bounds":bounds(subset),"interpretation":"unclassified surface component"})
    return ids,summaries

def basis(config):
    axes={"x":np.array([1.,0,0]),"y":np.array([0.,1,0]),"z":np.array([0.,0,1])}
    def parse(value):
        value=value.lower()
        return axes[value[-1]]*(-1 if value.startswith("-") else 1)
    result=np.array([parse(config["right_axis"]),parse(config["up_axis"]),parse(config["front_axis"])])
    if not np.allclose(result@result.T,np.eye(3)):
        raise ValueError("right/up/front must select three distinct orthogonal source axes")
    return result

def calibrated(points, config):
    transformed=points@basis(config).T
    landmarks=config.get("landmarks",{})
    head,feet=landmarks.get("head_top"),landmarks.get("feet_bottom")
    if head is None or feet is None:
        return transformed, {"status":"needs_calibration", "units":"source units",
            "reason":"Explicit body head/feet landmarks are missing. Full asset bounds may include props, hair, shoes or a base.",
            "basis_semantics":"Axis labels are supplied settings, not verified anatomical orientation."}
    b=basis(config)
    h=float((np.asarray(head)-np.asarray(feet))@b[1])
    if not h>0: raise ValueError("Head must be above feet on configured up axis")
    center=config.get("midline_origin")
    if center is None: raise ValueError("Provide an explicit midline_origin; bounding-box midpoint is not anatomical center")
    origin=np.asarray(center)@b.T
    origin[1]=np.asarray(feet)@b[1]
    transformed=(transformed-origin)/h
    return transformed,{"status":"landmark_normalized", "height_source_units":h,
        "units":"fractions of explicit landmark stature", "landmark_confidence":landmarks.get("confidence","artist-supplied"),
        "source_has_real_world_scale":False,"basis":b.tolist(),"origin_in_basis":origin.tolist()}

def select_faces(points,faces,tags,ids,config):
    spec=config.get("selection",{})
    keep=np.ones(len(faces),dtype=bool)
    if spec.get("component_ids") is not None: keep&=np.isin(ids[faces[:,0]],spec["component_ids"])
    if spec.get("face_tag_ids") is not None: keep&=np.isin(tags,spec["face_tag_ids"])
    crop=spec.get("source_bounds")
    if crop:
        # Require all vertices inside, so triangles crossing a crop do not mix props.
        mask=np.all((points>=np.asarray(crop["min"]))&(points<=np.asarray(crop["max"])),axis=1)
        keep&=np.all(mask[faces],axis=1)
    if not keep.any(): raise ValueError("Selection contains no faces")
    return faces[keep]

def cross_sections(points, faces, ys, roi=None):
    # Exact triangle-plane intersections; results do not depend on vertex density
    # or compatible topology. Width/depth use all intersections in the selection,
    # so body-only selection and the region labels must be reviewed by the artist.
    tri=points[faces]
    output=[]
    for y in ys:
        candidates=tri[(tri[:,:,1].min(1)<=y)&(tri[:,:,1].max(1)>=y)]
        intersections=[]
        segments=np.zeros((len(candidates),2,3)) if roi else None
        hits=np.zeros(len(candidates),dtype=np.int32) if roi else None
        for a,b in ((0,1),(1,2),(2,0)):
            va,vb=candidates[:,a],candidates[:,b]
            den=vb[:,1]-va[:,1]
            crosses=((va[:,1]<=y)&(vb[:,1]>y))|((vb[:,1]<=y)&(va[:,1]>y))
            if crosses.any():
                alpha=(y-va[crosses,1])/den[crosses]
                q=va[crosses]+alpha[:,None]*(vb[crosses]-va[crosses])
                intersections.append(q)
                if roi:
                    hitids=np.flatnonzero(crosses)
                    segments[hitids,hits[hitids]]=q
                    hits[hitids]+=1
        if not intersections:
            output.append({"height":float(y),"valid":False}); continue
        p=np.concatenate(intersections)
        if roi:
            # Clip actual section segments, including segments whose endpoints
            # both lie outside a narrow ROI but which pass through it.
            a=segments[:,0];d=segments[:,1]-a
            enter=np.zeros(len(a));leave=np.ones(len(a));valid=hits==2
            for axis,key in ((0,"lateral_range"),(2,"depth_range")):
                if roi.get(key) is None:continue
                low,high=roi[key];parallel=np.abs(d[:,axis])<1e-12
                valid&=~(parallel&((a[:,axis]<low)|(a[:,axis]>high)))
                den=np.where(parallel,1,d[:,axis])
                t1=(low-a[:,axis])/den;t2=(high-a[:,axis])/den
                enter=np.maximum(enter,np.where(parallel,-np.inf,np.minimum(t1,t2)))
                leave=np.minimum(leave,np.where(parallel,np.inf,np.maximum(t1,t2)))
            valid&=leave>=enter
            p=np.concatenate([a[valid]+enter[valid,None]*d[valid],a[valid]+leave[valid,None]*d[valid]])
        if not len(p):
            output.append({"height":float(y),"valid":False});continue
        low,high=p.min(0),p.max(0)
        # Fractions distinguish lobe width from pelvis width only after region
        # definitions are supplied. These are surface extents, not circumferences.
        output.append({"height":float(y),"valid":True,"intersection_samples":len(p),
            "width":float(high[0]-low[0]),"depth":float(high[2]-low[2]),
            "left":float(low[0]),"right":float(high[0]),
            "rear":float(low[2]),"front":float(high[2]),
            "center_x":float((high[0]+low[0])/2),"center_depth":float((high[2]+low[2])/2)})
    return output

def preview(points, ids, output, caption="Full asset; component colors; source axes only"):
    # Orthographic geometry point rendering; no inferred hidden anatomy. Full asset
    # shown, with connected components colored consistently across all views.
    pixels=720; margin=42
    low,high=points.min(0),points.max(0)
    palette=np.array([[197,139,244],[74,200,196],[246,160,97],[115,171,245],[242,129,170],[183,209,100]])
    canvas=Image.new("RGB",(pixels*3,pixels+88),(21,23,31));draw=ImageDraw.Draw(canvas)
    views=[(0,1,2,"Source X / Y"),(2,1,0,"Source Z / Y"),(0,2,1,"Source X / Z")]
    # All original vertices, binned through a nearest-visible point Z buffer.
    for panel,(a,b,depth,label) in enumerate(views):
        scale=(pixels-margin*2)/max(high[a]-low[a],high[b]-low[b])
        x=np.rint((points[:,a]-(low[a]+high[a])/2)*scale+pixels/2).astype(int)
        y=np.rint(-(points[:,b]-(low[b]+high[b])/2)*scale+pixels/2).astype(int)
        key=y*pixels+x
        order=np.lexsort((points[:,depth],key))
        sortedkeys=key[order]; unique=np.r_[sortedkeys[:-1]!=sortedkeys[1:],True]
        visible=order[unique]
        pic=np.empty((pixels,pixels,3),dtype=np.uint8)
        pic[:]=[30,33,44]
        color=palette[ids[visible]%len(palette)].astype(float)
        shade=.6+.4*(points[visible,depth]-low[depth])/max(high[depth]-low[depth],1e-12)
        pic[y[visible],x[visible]]=(color*shade[:,None]).astype(np.uint8)
        canvas.paste(Image.fromarray(pic), (panel*pixels,44))
        draw.text((panel*pixels+20,14),label,fill="white")
        draw.text((panel*pixels+20,pixels+58),caption,fill=(197,202,216))
    canvas.save(output)

def clustered_proxy(points,faces,out_dir,grid=180):
    low=points.min(0);extent=np.ptp(points,axis=0);cell=max(extent)/grid
    cells=np.floor((points-low)/cell).astype(np.int32)
    _,inverse=np.unique(cells,axis=0,return_inverse=True)
    n=int(inverse.max())+1
    count=np.bincount(inverse,minlength=n)
    verts=np.stack([np.bincount(inverse,weights=points[:,i],minlength=n)/count for i in range(3)],axis=1)
    tris=inverse[faces]
    tris=tris[(tris[:,0]!=tris[:,1])&(tris[:,1]!=tris[:,2])&(tris[:,2]!=tris[:,0])]
    sortedtri=np.sort(tris,axis=1);_,u=np.unique(sortedtri,axis=0,return_index=True)
    tris=tris[u]
    verts.astype("<f4").tofile(out_dir/"preview-positions.bin")
    tris.astype("<u4").tofile(out_dir/"preview-triangles.bin")
    return {"method":"vertex clustering for inspection only", "vertices":len(verts),"triangles":len(tris),
            "source_coordinate_system":True,"cell_size":cell,"not_production_retopology":True}

def inventory(args):
    source=Path(args.obj);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    p,f,t,meta=read_obj(source)
    if not np.isfinite(p).all(): raise ValueError("Nonfinite source positions")
    ids,c=components(p,f)
    p.astype("<f4").tofile(out/"source-positions.bin")
    f.astype("<u4").tofile(out/"source-triangles.bin")
    t.astype("<u4").tofile(out/"source-face-tags.bin")
    ids.astype("<i4").tofile(out/"source-components.bin")
    preview(p,ids,out/"orthographic-inventory.png")
    report={"source":str(source.resolve()),"source_bytes":source.stat().st_size,
        "source_sha256":hashlib.file_digest(source.open("rb"),"sha256").hexdigest(),
        "vertices":len(p),"triangles":len(f),"bounds":bounds(p),"tags":meta,
        "component_count":len(c),"components":c,"calibration_status":"needs_calibration",
        "anatomical_warning":"Whole asset may include a stand, hair, garments and carried props. No anatomical or stature labels inferred.",
        "preview":clustered_proxy(p,f,out),"coordinate_units":"not declared by OBJ"}
    dump(out/"inventory.json",report)
    default={"right_axis":"x","up_axis":"y","front_axis":"z","selection":{"artist_reviewed_body_only":False},
        "midline_origin":None,"landmarks":{"head_top":None,"feet_bottom":None,"confidence":"not supplied"},
        "pose_reviewed":False,"regions":[],"status":"needs artist-reviewed axes, body selection and landmarks"}
    if not (out/"calibration.json").exists():dump(out/"calibration.json",default)
    # Raw slices deliberately use source coordinates and nonanatomical labels.
    dump(out/"raw-source-y-profile.json",{"status":"uncalibrated", "units":"source units",
        "selection":"entire asset, includes any props/base", "sections":cross_sections(p,f,np.linspace(p[:,1].min(),p[:,1].max(),61))})
    print(json.dumps({"inventory":str(out/"inventory.json"),"vertices":len(p),"triangles":len(f),"components":len(c),"bounds":bounds(p)}))

def cached(folder):
    return (np.fromfile(folder/"source-positions.bin",dtype="<f4").reshape(-1,3),
        np.fromfile(folder/"source-triangles.bin",dtype="<u4").reshape(-1,3),
        np.fromfile(folder/"source-face-tags.bin",dtype="<u4"),
        np.fromfile(folder/"source-components.bin",dtype="<i4"))

def profile(args):
    folder=Path(args.inventory);config=json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
    p,f,t,ids=cached(folder);f=select_faces(p,f,t,ids,config)
    p,cal=calibrated(p,config)
    if cal["status"]!="landmark_normalized":
        dump(Path(args.out),{"calibration":cal,"comparison_ready":False,"sections":[],
            "message":"No normalized profile emitted until reliable head/feet and body midline are supplied."})
        print("Uncalibrated: comparison-ready false");return
    ys=np.linspace(0,1,101)
    sections=cross_sections(p,f,ys)
    regions=[]
    for spec in config.get("regions",[]):
        a,b=spec["height_range"]
        regionsections=cross_sections(p,f,[y for y in ys if a<=y<=b],spec)
        selected=[s for s in regionsections if s["valid"]]
        regions.append({**spec,"metrics": {"max_width":max([s["width"] for s in selected],default=None),
            "max_depth":max([s["depth"] for s in selected],default=None)},
            "sections":regionsections,"scope":"selected surface extents; no enclosed tissue volume"})
    reviewed=config.get("selection",{}).get("artist_reviewed_body_only",False) and config.get("pose_reviewed",False)
    overhang=None
    anchor=config.get("rear_overhang_anchor")
    if anchor:
        rr={r["name"]:r for r in regions}
        rear=rr.get(anchor["rear_region"]);reference=rr.get(anchor["anchor_region"])
        if rear and reference:
            rsections=[s for s in rear["sections"] if s["valid"]]
            asections=[s for s in reference["sections"] if s["valid"]]
            if rsections and asections:
                anchorcenter=float(np.mean([s["center_depth"] for s in asections]))
                rearextent=min(s["rear"] for s in rsections)
                overhang={**anchor,"anchor_mean_surface_center":anchorcenter,"rear_surface_extremum":rearextent,
                    "rear_overhang":max(0,anchorcenter-rearextent),
                    "scope":"Selected rear extremum relative to mean selected anchor surface midpoint, not skeletal or anatomical measurement.",
                    "confidence":"exploratory" if not reviewed else "artist-reviewed geometric ROI"}
    dump(Path(args.out),{"calibration":cal,"comparison_ready":reviewed,"selection":config.get("selection",{}),
        "selected_triangles":len(f),"sections":sections,"regions":regions,"rear_overhang_descriptor":overhang,
        "limitations":["Pose and camera-independent source geometry are required for shape-only interpretation.",
            "Clothes and merged props can bias extents; body selection is artist reviewed.",
            "Cross sections are surface widths/depths, not anatomical circumference or volume."]})
    print("Wrote landmark profile; comparison ready: "+str(reviewed))

def compare(args):
    a=json.loads(Path(args.base).read_text());b=json.loads(Path(args.target).read_text())
    if not a.get("comparison_ready") or not b.get("comparison_ready"):
        dump(Path(args.out),{"status":"needs_calibration", "differences":[],"reason":"Both profiles need explicit landmarks, artist-reviewed body-only selection and pose review."})
        print("Comparison withheld: uncalibrated profiles");return
    lookup={round(s["height"],8):s for s in a["sections"] if s["valid"]}
    rows=[]
    for t in b["sections"]:
        s=lookup.get(round(t["height"],8))
        if not t["valid"] or s is None:continue
        row={"height":t["height"]}
        for k in ("width","depth","rear","front","center_x","center_depth"):
            row[k+"_delta"]=t[k]-s[k]
        for k in ("width","depth"):
            row[k+"_ratio"]=t[k]/s[k] if s[k]>1e-8 else None
        rows.append(row)
    region_deltas=[]
    regions_a={r["name"]:r for r in a.get("regions",[])}
    for region in b.get("regions",[]):
        base=regions_a.get(region["name"])
        if not base:continue
        reference={round(s["height"],8):s for s in base["sections"] if s["valid"]}
        differences=[]
        for target in region["sections"]:
            source=reference.get(round(target["height"],8))
            if not target["valid"] or source is None:continue
            differences.append({"height":target["height"],
                "mass_width_delta":target["width"]-source["width"],
                "mass_depth_delta":target["depth"]-source["depth"],
                "surface_center_depth_delta":target["center_depth"]-source["center_depth"],
                "surface_center_lateral_delta":target["center_x"]-source["center_x"],
                "rear_extent_delta":target["rear"]-source["rear"]})
        region_deltas.append({"name":region["name"],"role":region.get("role","unspecified"),"differences":differences})
    dump(Path(args.out),{"status":"geometric_difference", "differences":rows,"region_differences":region_deltas,
        "equations":{"additive":"q(y,t) = q_baseline(y) + t * (q_target(y) - q_baseline(y)), 0 <= t <= 1",
            "ratio":"r_width(y) = width_target(y) / width_baseline(y)",
            "usage":"Sampled width, depth and centers are fitting constraints. They do not define a deformation map or prove matched anatomy.",
            "registration":"Align consistent pose and semantic landmarks before interpreting deltas as shape."},
        "posture_separation":{"mass_descriptors":["width(y)","depth(y)"],
            "pose_descriptors":["surface_center_depth(y)","surface_center_x(y)"],
            "definition":"Center is the midpoint of selected surface extrema. It is NOT the anatomical spine or pelvis rotation.",
            "transfer_rule":"Do not apply donor posture/height differences as butt or thigh inflation. Preserve target landmark stature and separately review centerline displacement."},
        "confidence":"Depends on artist-reviewed landmarks, selection, orientation and pose consistency.",
        "topology_requirement":"none; comparison uses triangle-plane intersections"})
    print(f"Compared {len(rows)} corresponding height samples")

def rainee(args):
    p=np.fromfile(ROOT/"assets/positions.bin",dtype="<f4").reshape(-1,3)
    f=np.fromfile(ROOT/"assets/triangles.bin",dtype="<u4").reshape(-1,3)
    info=json.loads((ROOT/"assets/mesh-info.json").read_text())
    # Existing proxy is normalized by the supplied FBX full source height, whose
    # floor/head are not independently artist-validated anatomical landmarks.
    dump(Path(args.out),{"comparison_ready":False,"calibration":{"status":"FBX working-coordinate reference",
        "units":"fractions of FBX full source height","height_source_units":info["normalization_height_source_units"],
        "anatomical_landmarks_validated":False},"sections":cross_sections(p,f,np.linspace(0,1,101)),
        "reason":"Working source-height profile available. For strict anatomical comparison, supply explicit body landmarks to both models.",
        "source":info["source"],"bounds":bounds(p)})
    print("Wrote Rainee working-coordinate profile; anatomical comparison remains uncalibrated")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest="action",required=True)
    q=sub.add_parser("inventory");q.add_argument("obj");q.add_argument("--out",required=True);q.set_defaults(fn=inventory)
    q=sub.add_parser("profile");q.add_argument("--inventory",required=True);q.add_argument("--config",required=True);q.add_argument("--out",required=True);q.set_defaults(fn=profile)
    q=sub.add_parser("compare");q.add_argument("--base",required=True);q.add_argument("--target",required=True);q.add_argument("--out",required=True);q.set_defaults(fn=compare)
    q=sub.add_parser("rainee-profile");q.add_argument("--out",required=True);q.set_defaults(fn=rainee)
    args=parser.parse_args();args.fn(args)
if __name__=="__main__":main()
