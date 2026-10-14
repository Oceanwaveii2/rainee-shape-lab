"""Read-only, guided image-contour measurement. Writes only beside this file.

Guides are reviewable annotations, not ground-truth anatomical landmarks. The
image gradients refine them; ellipse fits use only the visible outside arc.
"""
from pathlib import Path
import json, hashlib, math, shutil, argparse
import numpy as np
import cv2
from PIL import Image
from scipy.interpolate import PchipInterpolator
from scipy.optimize import least_squares
from scipy.ndimage import map_coordinates, median_filter

OUT = Path(__file__).resolve().parent
SOURCE = Path(r"C:/Users/User/Downloads/Qwen-21-Regenerated-Enhanced-Five-Frames02/qwen_intermediate_1024")
STAGE_ROOT = OUT.parent
FRAMES = [0, 10, 18, 26]

# Outside arcs start near the top/inner side, travel around the exterior, and
# finish near the bottom/inner side. Interior closure follows clothing/cleft.
# All coordinates are annotations in the ORIGINAL 1024 px image frame.
GUIDES = {
  0: {
    "left": {"arc": [[436,660],[404,650],[368,653],[330,667],[292,692],[260,726],[240,765],[233,805],[234,847],[243,886],[262,923],[287,948],[321,954],[359,947],[401,936],[435,923]], "closure": [[442,886],[448,834],[450,775],[447,718],[436,660]]},
    "right": {"arc": [[595,649],[634,660],[675,688],[709,728],[737,773],[755,823],[762,873],[759,919],[747,958],[719,968],[675,973],[631,972],[589,965],[550,953],[516,935],[487,911]], "closure": [[466,875],[457,825],[463,777],[478,729],[508,686],[551,660],[595,649]]},
    "torso": [[502,620],[646,620]],
  },
  10: {
    "left": {"arc": [[433,647],[395,633],[355,631],[313,639],[272,656],[235,684],[205,720],[185,760],[178,801],[179,844],[190,888],[208,926],[238,958],[272,978],[311,980],[352,971],[391,956],[424,941]], "closure": [[432,899],[435,850],[441,796],[444,744],[439,689],[433,647]]},
    "right": {"arc": [[580,644],[625,652],[670,674],[711,709],[745,752],[772,800],[788,849],[793,899],[784,947],[766,986],[724,1000],[678,1005],[628,1002],[582,990],[541,972],[504,947],[474,917]], "closure": [[446,870],[434,824],[440,775],[466,725],[498,684],[537,658],[580,644]]},
    "torso": [[489,620],[651,620]],
  },
  18: {
    "left": {"arc": [[433,651],[397,634],[357,625],[315,627],[271,638],[229,659],[191,690],[162,730],[145,773],[141,818],[146,865],[160,909],[186,950],[217,982],[254,1001],[296,1000],[337,991],[378,976],[414,955]], "closure": [[421,909],[423,861],[431,808],[436,755],[436,703],[433,651]]},
    "right": {"arc": [[579,642],[624,650],[670,672],[713,707],[750,750],[779,799],[798,850],[807,901],[803,950],[790,994],[766,1011],[724,1022],[679,1023],[635,1017],[591,1004],[550,982],[513,955],[482,922]], "closure": [[454,880],[436,832],[433,783],[453,734],[486,692],[528,661],[579,642]]},
    "torso": [[487,620],[657,620]],
  },
  26: {
    "left": {"arc": [[402,650],[371,640],[334,636],[293,640],[252,653],[214,676],[181,708],[154,750],[137,794],[128,839],[132,883],[146,924],[167,957],[193,982],[226,1004],[263,1015],[304,1011],[345,1001],[384,985],[409,961]], "closure": [[415,916],[417,865],[422,815],[425,763],[419,709],[402,650]]},
    "right": {"arc": [[581,645],[625,653],[671,676],[713,711],[749,754],[775,804],[792,855],[798,906],[793,956],[776,999]], "closure": [[757,1023],[665,1023],[605,1012],[565,997],[526,976],[491,946],[458,905],[430,853],[418,802],[436,752],[470,709],[511,676],[549,655],[581,645]]},
    "torso": [[481,620],[640,620]],
  },
}

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def resample(points, spacing=3.):
    p=np.asarray(points,dtype=float)
    t=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    q=np.linspace(0,t[-1],max(2,int(t[-1]/spacing)+1))
    curve=PchipInterpolator(t,p)(q)
    tangent=PchipInterpolator(t,p).derivative()(q)
    tangent/=np.maximum(np.linalg.norm(tangent,axis=1,keepdims=True),1e-8)
    return curve,np.column_stack([-tangent[:,1],tangent[:,0]])

def snap_arc(rgb, guide, window=8):
    curve,normals=resample(guide)
    # A blurred Lab color derivative reduces skin texture/highlight noise.
    lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(float)
    lab=cv2.GaussianBlur(lab,(0,0),1.15)
    gx=cv2.Sobel(lab,cv2.CV_64F,1,0,ksize=3)/8
    gy=cv2.Sobel(lab,cv2.CV_64F,0,1,ksize=3)/8
    offsets=np.arange(-window,window+.01,.5)
    positions=curve[:,None,:]+normals[:,None,:]*offsets[None,:,None]
    coords=np.array([positions[:,:,1],positions[:,:,0]])
    dx=np.stack([map_coordinates(gx[:,:,c],coords,order=1,mode="nearest") for c in range(3)],axis=2)
    dy=np.stack([map_coordinates(gy[:,:,c],coords,order=1,mode="nearest") for c in range(3)],axis=2)
    strength=np.linalg.norm(dx*normals[:,None,0,None]+dy*normals[:,None,1,None],axis=2)
    # Soft locality preference prevents jumping to a nearby fold or seam.
    score=strength-.18*np.abs(offsets)[None,:]
    best=np.argmax(score,axis=1)
    shifts=median_filter(offsets[best],size=5,mode="nearest")
    snapped=curve+normals*shifts[:,None]
    edge=np.array([np.interp(s,offsets,st) for s,st in zip(shifts,strength)])
    # Remove gradients too weak to carry even a provisional silhouette cue.
    threshold=max(.65,float(np.quantile(edge,.04)))
    valid=(edge>=threshold)&(snapped[:,1]<1022)&(snapped[:,1]>0)&(snapped[:,0]>0)&(snapped[:,0]<1023)
    return snapped,normals,valid,shifts,edge

def ellipse_residual(par,pts):
    cx,cy,la,lb,theta=par
    a,b=np.exp([la,lb]);c,s=np.cos(theta),np.sin(theta)
    d=pts-[cx,cy]
    u=d[:,0]*c+d[:,1]*s;v=-d[:,0]*s+d[:,1]*c
    f=(u/a)**2+(v/b)**2-1
    grad=2*np.sqrt((u/a**2)**2+(v/b**2)**2)
    return f/np.maximum(grad,1e-9)

def fit_ellipse(pts):
    (cx,cy),(da,db),deg=cv2.fitEllipse(pts.astype(np.float32))
    p0=[cx,cy,np.log(da/2),np.log(db/2),np.deg2rad(deg)]
    opt=least_squares(ellipse_residual,p0,args=(pts,),loss="soft_l1",f_scale=3,
      bounds=([50,450,np.log(60),np.log(60),-20],[950,1200,np.log(500),np.log(500),20]),max_nfev=180)
    p=opt.x;a,b=np.exp(p[2:4]);t=p[4]
    if b>a:a,b=b,a;t+=np.pi/2
    t=(t+np.pi/2)%np.pi-np.pi/2
    out={"center_px":p[:2].tolist(),"semimajor_px":float(a),"semiminor_px":float(b),"major_rotation_degrees":float(np.rad2deg(t))}
    return out,opt

def ellipse_geometry(e):
    x,y=e["center_px"];a=e["semimajor_px"];b=e["semiminor_px"];t=np.deg2rad(e["major_rotation_degrees"])
    c,s=np.cos(t),np.sin(t);cov=np.array([[a*a*c*c+b*b*s*s,(a*a-b*b)*c*s],[(a*a-b*b)*c*s,a*a*s*s+b*b*c*c]])
    sx,sy=np.sqrt(np.diag(cov))
    return {"upper_pole_px":[float(x-cov[0,1]/sy),float(y-sy)],"lower_pole_px":[float(x+cov[0,1]/sy),float(y+sy)],"left_pole_px":[float(x-sx),float(y-cov[0,1]/sx)],"right_pole_px":[float(x+sx),float(y+cov[0,1]/sx)],"projected_width_px":float(2*sx),"projected_height_px":float(2*sy),"ellipse_area_px2":float(np.pi*a*b)}

def ellipse_par(e):
    return np.r_[e["center_px"],np.log([e["semimajor_px"],e["semiminor_px"]]),np.deg2rad(e["major_rotation_degrees"])]

def fit_circle(pts):
    center=np.mean(pts,axis=0);r=np.median(np.linalg.norm(pts-center,axis=1))
    opt=least_squares(lambda p:np.linalg.norm(pts-p[:2],axis=1)-p[2],np.r_[center,r],loss="soft_l1",f_scale=3)
    res=np.linalg.norm(pts-opt.x[:2],axis=1)-opt.x[2]
    return {"center_px":opt.x[:2].tolist(),"radius_px":float(opt.x[2]),"curve_rms_px":float(np.sqrt(np.mean(res**2)))}

def area_polygon(p):
    p=np.asarray(p);return float(abs(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))/2)

def equivalent_ellipse(p):
    """Exact planar polygon area moments, followed by area-preserving ellipse.

    The ellipse is a descriptor of the VISIBLE region. It does not claim to
    reconstruct the occluded side of a lobe. Its center cannot run away as a
    partial-arc ellipse fit can.
    """
    p=np.asarray(p,float);q=np.roll(p,-1,axis=0)
    cr=p[:,0]*q[:,1]-q[:,0]*p[:,1]
    signed=cr.sum()/2
    if signed<0:return equivalent_ellipse(p[::-1])
    cx=((p[:,0]+q[:,0])*cr).sum()/(6*signed)
    cy=((p[:,1]+q[:,1])*cr).sum()/(6*signed)
    xx=((p[:,0]**2+p[:,0]*q[:,0]+q[:,0]**2)*cr).sum()/(12*signed)
    yy=((p[:,1]**2+p[:,1]*q[:,1]+q[:,1]**2)*cr).sum()/(12*signed)
    xy=((2*p[:,0]*p[:,1]+p[:,0]*q[:,1]+q[:,0]*p[:,1]+2*q[:,0]*q[:,1])*cr).sum()/(24*signed)
    cov=np.array([[xx-cx*cx,xy-cx*cy],[xy-cx*cy,yy-cy*cy]])
    values,vectors=np.linalg.eigh(cov)
    axes=2*np.sqrt(values[::-1]);major=vectors[:,1]
    axes*=np.sqrt(signed/(np.pi*np.prod(axes)))
    t=(np.arctan2(major[1],major[0])+np.pi/2)%np.pi-np.pi/2
    return {"center_px":[float(cx),float(cy)],"semimajor_px":float(axes[0]),"semiminor_px":float(axes[1]),"major_rotation_degrees":float(np.rad2deg(t)),"definition":"Area-equivalent ellipse oriented by exact visible-polygon second moments; center is visible-region area centroid. NOT full anatomical lobe ellipse."}

def region_sensitivity(pts,normals,closure,seed,count=64):
    rng=np.random.default_rng(seed);values=[]
    closure=np.asarray(closure,float)
    for _ in range(count):
      jitter=np.interp(np.linspace(0,1,len(pts)),np.linspace(0,1,12),rng.uniform(-3,3,12))
      close_jitter=rng.uniform(-5,5,closure.shape)
      poly=np.vstack([pts+normals*jitter[:,None],closure+close_jitter])
      e=equivalent_ellipse(poly);g=ellipse_geometry(e)
      arc=pts+normals*jitter[:,None]
      values.append([*e["center_px"],e["semimajor_px"],e["semiminor_px"],area_polygon(poly),g["upper_pole_px"][1],g["lower_pole_px"][1],arc[:,0].min(),arc[:,0].max(),arc[:,1].min(),arc[:,1].max()])
    cols=["center_x","center_y","semimajor","semiminor","visible_region_area_px2","upper_y","lower_y","outside_min_x","outside_max_x","outside_min_y","outside_max_y"]
    q=np.quantile(values,[.05,.95],axis=0)
    return {"method":"64 correlated +/-3 px outside-arc jitters and +/-5 px clothing/cleft closure jitters; 5–95 percentiles. Algorithm sensitivity only; excludes pose, semantic boundary and generative uncertainty.","successful_fits":count,"ranges":{n:[float(q[0,i]),float(q[1,i])] for i,n in enumerate(cols)}}

def sensitivity(pts,normals,seed, count=64):
    rng=np.random.default_rng(seed);values=[]
    # Correlated +/-3 px annotation jitter plus block resampling; percentile
    # range measures this specific extraction's sensitivity, not truth CI.
    blocks=np.array_split(np.arange(len(pts)),12)
    for _ in range(count):
      ids=np.concatenate([blocks[i] for i in rng.integers(0,len(blocks),len(blocks))])
      jitter=np.interp(np.linspace(0,1,len(pts)),np.linspace(0,1,12),rng.uniform(-3,3,12))
      try:
        e,_=fit_ellipse((pts+normals*jitter[:,None])[ids])
        g=ellipse_geometry(e)
        values.append([*e["center_px"],e["semimajor_px"],e["semiminor_px"],g["projected_width_px"],g["projected_height_px"],g["upper_pole_px"][1],g["lower_pole_px"][1]])
      except Exception:pass
    cols=["center_x","center_y","semimajor","semiminor","projected_width","projected_height","upper_y","lower_y"]
    q=np.quantile(values,[.05,.95],axis=0)
    return {"method":"64 correlated +/-3 px contour-jitter and 12-block resampling fits; 5–95 percentiles, NOT anatomical confidence intervals", "successful_fits":len(values),"ranges_px":{n:[float(q[0,i]),float(q[1,i])] for i,n in enumerate(cols)}}

def torso_measure(rgb,guide):
    # Explicit manual landmarks remain primary: boundaries can be occluded,
    # and strongest derivative can be a decorative gold strand. Do not snap
    # an ambiguous torso span automatically and claim precise anatomy.
    a,b=np.asarray(guide,float);w=float(b[0]-a[0]);err=8.
    return {"definition":"Visible exposed lower-back skin horizontal span at image row y=620: left skin/background or bodice termination to right skin/sleeve boundary. Excludes sleeves; garment and pose dependent, NOT skeletal waist width.","endpoints_px":[a.tolist(),b.tolist()],"width_px":w,"endpoint_review_tolerance_px":err,"width_range_px":[w-2*err,w+2*err],"method":"Explicit manually reviewed provisional boundary annotations; editable in review. No automatic anatomical landmark claim.","confidence":"low_to_moderate; seams and silhouette occlusion differ across frames"}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guides",type=Path,help="Optional editable guide-annotations JSON. Only read; all outputs remain beside this script.")
    args=parser.parse_args()
    global GUIDES
    if args.guides:
      loaded=json.loads(args.guides.read_text(encoding="utf-8"))
      GUIDES={int(k):v for k,v in loaded["guides"].items()}
      if list(sorted(GUIDES))!=FRAMES:raise ValueError("Exactly accepted0000/0010/0018/0026 guide entries required.")
    manifest={"schema":"rainee.provisional-paired-lobe-profile.v1","status":"provisional_editable_image_profile_candidate; not accepted 3D fit","accepted_frame_numbers":FRAMES,"endpoint_frame_number":26,"excluded_frame_numbers":[49],"stage_semantics":"Ordinal 1–4 only; NO physical volume multipliers","units":"Original full-frame pixels, x right/y down; image-normalized values divide x,y by1024","anatomical_identity":"image-left/image-right exposed posterior lobe profiles; not established anatomical left/right","method":{"contour":"Manual outside-arc guides, PCHIP resampling every ~3 px, blurred-Lab normal gradient search within +/-8 px, locality penalty, 5-sample median shifts, weak-edge filtering. Guide points and selected points retained for review.","ellipse":"Five-parameter rotated ellipse least-squares fit to the VISIBLE OUTSIDE ARC only, first-order orthogonal residual, soft-L1 3 px loss. Clothing/cleft closure excluded from ellipse fitting.","visible_area":"Shoelace area of gradient-snapped outside arc plus annotated clothing/cleft closure. Visible-skin silhouette estimate; NOT complete lobe surface area.","limitations":["Enhanced frames contain generated pixels; profiles describe this reference appearance.","Contours are guided and provisional, not fully automatic segmentation or precise anatomical landmarks.","Torso span is a visible skin/garment cue, not skeletal waist or a fixed scale landmark.","Pose, camera, overlap, perspective and enhancement can change apparent width and area.","Ellipse poles may be extrapolated beyond visible contour, especially lower frame0026.","No image pixel area or ellipse area is 3D tissue volume."]},"frames":[]}
    for ordinal,num in enumerate(FRAMES,1):
      src=SOURCE/f"frame_{num:04}.png";dest=OUT/src.name
      shutil.copyfile(src,dest)
      rgb=np.asarray(Image.open(src).convert("RGB"));height,width=rgb.shape[:2]
      frame={"frame_number":num,"stage_ordinal":ordinal,"image":{"original_path":str(src),"review_path":dest.name,"sha256":sha(src),"copy_sha256":sha(dest),"width":width,"height":height,"unchanged_uncropped":True},"lobes":{},"torso_span":torso_measure(rgb,GUIDES[num]["torso"])}
      for side in ["left","right"]:
        guide=GUIDES[num][side]
        pts,normals,valid,shifts,edge=snap_arc(rgb,guide["arc"])
        used=pts[valid];used_normals=normals[valid]
        e,opt=fit_ellipse(used);g=ellipse_geometry(e);res=ellipse_residual(ellipse_par(e),used)
        alt,_,av,_,_=snap_arc(rgb,guide["arc"],12)
        alt_e,_=fit_ellipse(alt[av]);alt_g=ellipse_geometry(alt_e)
        local=(used-e["center_px"])@np.array([[np.cos(np.deg2rad(e["major_rotation_degrees"])), -np.sin(np.deg2rad(e["major_rotation_degrees"]))],[np.sin(np.deg2rad(e["major_rotation_degrees"])),np.cos(np.deg2rad(e["major_rotation_degrees"]))]])
        ang=np.sort(np.arctan2(local[:,1]/e["semiminor_px"],local[:,0]/e["semimajor_px"])%(2*np.pi))
        maxgap=float(np.max(np.diff(np.r_[ang,ang[0]+2*np.pi])))
        closed=np.vstack([pts,guide["closure"]])
        primary=equivalent_ellipse(closed);primary_geometry=ellipse_geometry(primary)
        clipping=(num==26 and side=="right") or max(closed[:,1])>=1023
        observed_supports={"outside_top_px":used[np.argmin(used[:,1])].tolist(),"outside_bottom_px":used[np.argmax(used[:,1])].tolist(),"outside_left_px":used[np.argmin(used[:,0])].tolist(),"outside_right_px":used[np.argmax(used[:,0])].tolist()}
        sensitivity_fit=sensitivity(used,used_normals,num+(side=="right")*100)
        unstable=sensitivity_fit["ranges_px"]["center_x"][1]-sensitivity_fit["ranges_px"]["center_x"][0]>80
        frame["lobes"][side]={"guide_outside_arc_px":guide["arc"],"annotated_clothing_cleft_closure_px":guide["closure"],"selected_outside_curve_px":np.round(used,2).tolist(),"selected_curve_soft_fit_weights":[.25 if p[1]<700 else .6 if p[1]>940 else 1. for p in used],"curve_weight_definition":"Review heuristic: upper y<700 soft lobe/torso or garment transition=.25; lower y>940 garment/crease boundary=.6; middle outside skin/background edge=1. NOT calibrated probability.","visible_region_polygon_px":np.round(closed,2).tolist(),"selected_curve_points":len(used),"gradient_window_px":8,"median_abs_normal_shift_px":float(np.median(abs(shifts))),"ellipse":primary,"ellipse_derived":primary_geometry,"primary_descriptor_method":"Exact review-guided exposed-region area centroid and area-equivalent ellipse from polygon second moments. Describes selected skin patch including garment occlusion and soft lobe/waist transition; NOT anatomical center/radii.","outside_curve_ellipse_fit":{"ellipse":e,"derived":g,"curve_rms_px":float(np.sqrt(np.mean(res**2))),"median_abs_residual_px":float(np.median(abs(res))),"outside_arc_coverage_degrees":float(360-np.rad2deg(maxgap)),"identifiability":"ill_conditioned_partial_arc; do not use hidden center/radii/poles as hard constraints" if unstable else "provisional_partial_arc_fit; hidden side still not observed","sensitivity":sensitivity_fit},"circle_alternative":fit_circle(used),"observed_contour_supports":observed_supports,"visible_skin_region_area_px2":area_polygon(closed),"normalized_center":(np.asarray(primary["center_px"])/1024).tolist(),"normalized_semiaxes":[primary["semimajor_px"]/1024,primary["semiminor_px"]/1024],"uncertainty":region_sensitivity(pts,normals,guide["closure"],num+(side=="right")*100),"alternate_12px_gradient_window_delta":{"center_px":(np.asarray(alt_e["center_px"])-e["center_px"]).tolist(),"projected_width_px":alt_g["projected_width_px"]-g["projected_width_px"],"projected_height_px":alt_g["projected_height_px"]-g["projected_height_px"]},"lower_pole_status":"region truncated at image edge; equivalent-ellipse pole is descriptive, true lower extent unknown" if clipping else "equivalent-ellipse extremum; observed boundary is separately retained","contour_status":"review-guided outside arc; upper soft lobe/waist transition can be inferred, not a background silhouette. Interior clothing/cleft closure excluded from outside-arc ellipse fit."}
      left,right=[frame["lobes"][s] for s in ["left","right"]]
      allpts=np.vstack([left["selected_outside_curve_px"],right["selected_outside_curve_px"]]);visible_width=float(np.ptp(allpts[:,0]))
      torso=frame["torso_span"]["width_px"]
      frame["paired_profile"]={"visible_outside_width_px":visible_width,"center_distance_px":float(np.linalg.norm(np.array(left["ellipse"]["center_px"])-right["ellipse"]["center_px"])),"left_right_center_dx_px":float(right["ellipse"]["center_px"][0]-left["ellipse"]["center_px"][0]),"rear_width_over_visible_torso_span":visible_width/torso,"sum_visible_skin_region_area_px2":left["visible_skin_region_area_px2"]+right["visible_skin_region_area_px2"],"rear_width_over_torso_sensitivity_range":[visible_width/(torso+16),visible_width/(torso-16)],"ratio_limit":"Width uses observed outside arcs; denominator is reviewed visible back-skin span, pose/garment dependent. Ratio is a screen-space fitting cue only."}
      lr=left["uncertainty"]["ranges"];rr=right["uncertainty"]["ranges"]
      pair=frame["paired_profile"]
      pair["outside_width_sensitivity_range_px"]=[rr["outside_max_x"][0]-lr["outside_min_x"][1],rr["outside_max_x"][1]-lr["outside_min_x"][0]]
      pair["visible_area_sensitivity_range_px2"]=[lr["visible_region_area_px2"][0]+rr["visible_region_area_px2"][0],lr["visible_region_area_px2"][1]+rr["visible_region_area_px2"][1]]
      pair["sensitivity_range_definition"]="Conservative envelope formed from the two lobes' 5–95% correlated-jitter ranges. Extraction sensitivity only; semantic region choice, unknown camera/pose, generation and off-frame extent are NOT covered."
      desc_path=STAGE_ROOT/f"frame_{num:04}"/"shape-descriptors.json"
      descriptor=json.loads(desc_path.read_text())
      rear=descriptor["regions"]["rear"];waist=descriptor["regions"]["waist"]
      frame["generated_3d_context"]={"source_path":descriptor["geometry_source"],"read_only_descriptor_path":str(desc_path),"descriptor_sha256":sha(desc_path),"pose_registered":False,"axis_acceptance":False,"roi_acceptance":False,"rear_to_waist_width":rear["weighted_spans"]["lateral"]/waist["weighted_spans"]["lateral"],"rear_depth_over_width":rear["depth_over_width"],"rear_pca_minor_over_major":rear["pca_minor_over_major"],"comparison_status":"Unregistered generated geometry ROI descriptors; NOT corresponding camera projection or anatomical lobes. Endpoint image0026 remains target irrespective of these metrics."}
      manifest["frames"].append(frame)
    base=manifest["frames"][0]["paired_profile"]
    for frame in manifest["frames"]:
      p=frame["paired_profile"]
      p["apparent_width_ratio_to_baseline"]=p["visible_outside_width_px"]/base["visible_outside_width_px"]
      p["visible_area_ratio_to_baseline"]=p["sum_visible_skin_region_area_px2"]/base["sum_visible_skin_region_area_px2"]
    manifest["shared_camera_fit_use"]={"usable_now":["Screen-space outside contour residuals, paired centers/separation, top/bottom supports and left/right apparent shape asymmetry.","Compare one projected Rainee surface with the same coordinate-frame contours after camera and pose registration.","Keep four ordinal targets; hold0026 endpoint after the accepted inflation interval."],"requires_registration":["Estimate a shared or per-frame camera from stable environment/torso landmarks and independently constrained body pose.","Use robust contour objective; downweight interior seams, clipped lower poles and uncertain torso landmarks.","Keep source-authoritative height; do not rescale body to explain image framing.","3D generated ROI descriptors may provide soft regularization only after axes/regions/camera correspondence review."],"prohibited_inferences":["2D area or stage ordinal → physical tissue volume multiplier","Unregistered generated stage0026 ROI decrease → intended deflation","Image-left lobe → confirmed anatomical left"]}
    manifest["method"]["primary_ellipse"]="Exact visible-polygon centroid and second moments, rescaled to preserve polygon area. Area-equivalent descriptive ellipse; includes exposed-region occlusion and DOES NOT reconstruct hidden lobe anatomy. Free outside-arc ellipse/circle fits retained separately, with sensitivity gating."
    manifest["method"]["limitations"].append("Upper lobe/waist transitions can be soft skin-on-skin boundaries rather than silhouettes; they are review-guided and downweighted. The region is a selected exposed lobe patch, not all exposed body skin.")
    (OUT/"profile-fit-candidate.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    (OUT/"guide-annotations.json").write_text(json.dumps({"status":"editable provisional annotations","guides":GUIDES},indent=2),encoding="utf-8")
    summary=[{"frame":f["frame_number"],"width":round(f["paired_profile"]["visible_outside_width_px"],2),"visible_area":round(f["paired_profile"]["sum_visible_skin_region_area_px2"],1),"torso":f["torso_span"]["width_px"],"ratio":round(f["paired_profile"]["rear_width_over_visible_torso_span"],3),"lobes":{s:{"center":np.round(f["lobes"][s]["ellipse"]["center_px"],1).tolist(),"a":round(f["lobes"][s]["ellipse"]["semimajor_px"],1),"b":round(f["lobes"][s]["ellipse"]["semiminor_px"],1),"curve_fit_rms":round(f["lobes"][s]["outside_curve_ellipse_fit"]["curve_rms_px"],2)} for s in ["left","right"]}} for f in manifest["frames"]]
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
