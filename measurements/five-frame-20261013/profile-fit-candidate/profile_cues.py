"""Reusable provisional 2D targets. No camera guessing or geometry mutation.

Caller supplies projected, visible posterior outside curves in the ORIGINAL
1024x1024 coordinate frame (x right / y down), with anatomical occlusion handled
by the caller. An unregistered camera produces a diagnostic score, not a match.
"""
from pathlib import Path
import json
import numpy as np
from scipy.spatial import cKDTree

ACCEPTED=(0,10,18,26)

def load_candidate(path=None):
    path=Path(path) if path else Path(__file__).with_name("profile-fit-candidate.json")
    data=json.loads(path.read_text(encoding="utf-8"))
    if tuple(data["accepted_frame_numbers"])!=ACCEPTED or data["endpoint_frame_number"]!=26:
        raise ValueError("Expected accepted0000/0010/0018/0026 and held endpoint0026")
    return data

def stage_target(frame_number,data=None):
    if frame_number not in ACCEPTED:
        raise ValueError("Only four accepted stages may be fitting targets;0049 is excluded")
    data=load_candidate() if data is None else data
    return next(frame for frame in data["frames"] if frame["frame_number"]==frame_number)

def _huber(dist,delta):
    return np.where(dist<=delta,.5*dist**2,delta*(dist-.5*delta))

def projected_profile_loss(projected_visible_curves,frame_number,data=None,camera_registered=False,huber_delta_px=4.):
    """Weighted target→projection robust contour objective, normalized by H=1024.

    Single direction is intentional: unobserved garment/cleft/lower boundaries
    must not be invented as targets. This cannot penalize extra model silhouette
    segments; caller may add reverse residuals ONLY for accepted corresponding
    visible arc segments. Do not optimize camera scale by shrinking the body.
    """
    target=stage_target(frame_number,data);result={}
    losses=[]
    for side in ("left","right"):
        prediction=np.asarray(projected_visible_curves[side],float)
        if prediction.ndim!=2 or prediction.shape[1]!=2 or len(prediction)<3 or not np.isfinite(prediction).all():
            raise ValueError("Finite Nx2 projected outside curve required for each image-side lobe")
        lobe=target["lobes"][side]
        observed=np.asarray(lobe["selected_outside_curve_px"],float)
        weights=np.asarray(lobe["selected_curve_soft_fit_weights"],float)
        distances=cKDTree(prediction).query(observed)[0]
        mean=float(np.average(_huber(distances,huber_delta_px),weights=weights))
        losses.append(mean/(1024**2))
        result[side]={"weighted_huber_px2":mean,"median_nearest_curve_distance_px":float(np.median(distances)),"p90_nearest_curve_distance_px":float(np.quantile(distances,.9)),"observed_points":len(observed),"predicted_points":len(prediction)}
    return {"frame_number":frame_number,"stage_ordinal":target["stage_ordinal"],"normalized_contour_objective":float(np.mean(losses)),"camera_registered":bool(camera_registered),"status":"provisional_registered_screen_space_score" if camera_registered else "diagnostic_only_requires_camera_and_pose_registration","side_residuals":result,"objective_limits":["target→prediction only; extra model segments not penalized","semantic upper/lower arcs downweighted by review heuristic","no physical volume or stature inference","visible-region ellipse/centroid descriptors are supplementary and occlusion dependent"]}
