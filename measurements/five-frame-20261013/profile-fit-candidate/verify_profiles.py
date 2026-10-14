"""Meaningful geometry, target gate, provenance and objective verification."""
from pathlib import Path
import json,hashlib
import numpy as np
from analyze_profiles import equivalent_ellipse,fit_ellipse,ellipse_geometry,ellipse_par,ellipse_residual
from profile_cues import load_candidate,stage_target,projected_profile_loss

OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[]
def check(name,ok,detail):
    checks.append({"name":name,"passed":bool(ok),"detail":detail})
    if not ok:raise AssertionError(name)

data=load_candidate()
theta=np.linspace(0,2*np.pi,4096,endpoint=False);rotation=.43
a,b=137.,91.;center=np.array([525.,788.]);R=np.array([[np.cos(rotation),-np.sin(rotation)],[np.sin(rotation),np.cos(rotation)]])
pts=np.column_stack([a*np.cos(theta),b*np.sin(theta)])@R.T+center
e=equivalent_ellipse(pts)
check("known_rotated_ellipse_polygon_moments",np.linalg.norm(np.array(e["center_px"])-center)<1e-6 and abs(e["semimajor_px"]-a)<.001 and abs(e["semiminor_px"]-b)<.001 and abs(e["major_rotation_degrees"]-np.rad2deg(rotation))<1e-5,e)
circle=equivalent_ellipse(np.column_stack([80*np.cos(theta),80*np.sin(theta)])+center)
check("known_circle_region_area",abs(ellipse_geometry(circle)["ellipse_area_px2"]-np.pi*80**2)<.02,"Moment ellipse preserves full polygon area, with polygon discretization tolerance")
partial=pts[theta<4.2];f,_=fit_ellipse(partial)
check("known_partial_rotated_ellipse_curve_fit",np.max(abs(ellipse_residual(ellipse_par(f),partial)))<1e-4,"Fits known 240-degree rotated ellipse without inventing camera/volume")
for frame in data["frames"]:
    n=frame["frame_number"];im=frame["image"]
    check(f"frame{n:04}_unchanged_uncropped_image",sha(im["original_path"])==im["sha256"]==sha(OUT/im["review_path"]) and im["width"]==im["height"]==1024,"Exact source and copied PNG bytes match; full1024x1024")
    for side,l in frame["lobes"].items():
        e=l["ellipse"];p=np.asarray(l["selected_outside_curve_px"])
        check(f"frame{n:04}_{side}_finite_measured_curve",np.isfinite(p).all() and len(p)>100 and len(l["selected_curve_soft_fit_weights"])==len(p),f"{len(p)} actual gradient-selected points")
        check(f"frame{n:04}_{side}_area_equivalent",abs(ellipse_geometry(e)["ellipse_area_px2"]-l["visible_skin_region_area_px2"])<1e-6,"Ellipse area exactly equals measured exposed-region polygon area; no tissue volume")
    exact={s:frame["lobes"][s]["selected_outside_curve_px"] for s in ["left","right"]}
    zero=projected_profile_loss(exact,n,data)
    shifted={s:(np.asarray(p)+[12,0]).tolist() for s,p in exact.items()}
    other=projected_profile_loss(shifted,n,data)
    check(f"frame{n:04}_contour_objective_sensitive",zero["normalized_contour_objective"]==0 and other["normalized_contour_objective"]>zero["normalized_contour_objective"],{"exact":zero["normalized_contour_objective"],"shifted12px":other["normalized_contour_objective"]})
    check(f"frame{n:04}_unregistered_score_gate",zero["status"]=="diagnostic_only_requires_camera_and_pose_registration","Diagnostic output stays inspectable but is not called an accepted match")
try:stage_target(49,data);rejected=False
except ValueError:rejected=True
check("rejected0049_cannot_be_target",rejected,"Endpoint remains0026")
check("ordinal_stage_labels",[f["stage_ordinal"] for f in data["frames"]]==[1,2,3,4] and "NO physical volume" in data["stage_semantics"],"Ordinal labels have no physical4x assignment")
html=(OUT/"review.html").read_text(encoding="utf-8")
check("full_frame_svg_viewbox",'viewBox="0 0 1024 1024"' in html and 'width="1024" height="1024"' in html,"Review preserves complete source-image coordinate frame")
check("manual_proposals_separate_from_source_descriptors","manual_overlay_proposals_are_not_refitted=true" in html,"Export keeps original measurements and manual overlay proposals separate")
report={"passed":all(c["passed"] for c in checks),"checks":checks,"scope":"2D contour/moment/objective/provenance verification only; no native 3D fit or physical volume verification"}
(OUT/"verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print(json.dumps({"passed":report["passed"],"checks":len(checks)}))
