Rainee regional model-reference fitter
======================================

Integration manifest: reference-fit-manifest.json.
The candidate can be inspected in the editor as a provisional shape trial.
Automatic adoption is disabled. No accepted winner is claimed while source
and reference pelvis axes/pose and region correspondence remain unregistered.

Input geometry
--------------
Source: original FBX-derived 98,078-point Rainee proxy, followed by the baked
local pelvic repair. Reference: actual full-resolution archived OBJ geometry
and the separately reported color-role/3D ROI selections from reference-01a13749.
No donor face, body topology, height, or global proportions are transferred.

Source axes are X lateral, Y up, Z front/depth. Reference source axes are
Z lateral, Y up, X front/depth, based on provisional surface review. Explicit
source rear and waist boxes and perineal exclusion are in reference-fit.json.
Selected source triangle membership is locked before deformation.

Measurements and equations
--------------------------
Each selected triangle contributes its true surface area as weight.
Local spans use area-weighted 5th-to-95th percentiles of triangle centroids.
These are approximate outside-shape descriptors, not crop-box heights.
Principal shape ratios use exact area-integrated surface covariance. For a
uniform triangle with vertices p0,p1,p2 and s=p0+p1+p2:

    E[p] = s/3
    E[pp^T] = (sum_i p_i p_i^T + ss^T)/12

The covariance is area weighted across the selected triangles. Its square-root
eigenvalue ratios are invariant under rigid rotation, translation, uniform
scale, and subdivision of the same planar surface. The selected region itself
can still change with pose/segmentation, so that mathematical invariance does
not establish anatomical correspondence.

The existing production rear_model.py deformer is used unchanged. Its closed
control cage calibrates the authored volume multiplier by bisection:

    V_cage(deformed) / V_cage(rest) = volume

That is control-cage volume, not an inferred tissue volume from the open body.
The bounded objective is:

    E(theta) = sum_k w_k log(m_k(theta)/target_k)^2
               + 0.015 ||(theta-prior)/parameter_range||^2

theta = [volume, lateral, vertical, projection]. Bounds are volume [1,2.5]
and each directional control [0.4,1.6]. Separation, pole and cleft controls
stay at the existing production defaults, recorded in the report.

Results and limits
------------------
The diagnostic search uses 17 coarse evaluations plus at most 60 bounded
Powell objective calls. It stopped at the declared resource cap, so the result
is a best tested candidate rather than a converged optimum.

The local posterior reference asks for a higher depth/width ratio, while its
waist-normalized rear width/depth cues ask for contraction. Those cues conflict
because the reference waist is turned and its color/ROI segmentation is still
provisional. The current inflation controls start at volume 1 and do not offer
contraction. The candidate therefore remains a soft geometric trial; these
numbers do not imply that the donor body should replace Rainee's proportions.

Candidate fit, deltas, objective score and parameter values are machine readable.
The score is an internal weighted descriptor error, not anatomical or visual
accuracy percent. Editor inspection is allowed despite the correspondence gate;
the gate blocks presenting the trial as an accepted match or automatic adoption.

Performance and verification
----------------------------
The objective evaluates 24,040 regional points, requiring only 20,130 original
source points and their repair binds. Full body deformation is generated only
for the chosen candidate. The 77-call diagnostic run took approximately eight
seconds on this host. This is a measured run, not a sustained-performance claim.

The chosen candidate has finite points, unchanged source height and unchanged
protected source points. The production finite-difference Jacobian screen has
no nonpositive samples. This checks field orientation, not self-collision,
whole-body topology, artistic identity, or agreement with the inflation video.

Commands
--------
System Python with NumPy, SciPy and Pillow:
    python fit_regional_rear.py --diagnostic
    python verify_fitter.py
    python package_fit.py

Without --diagnostic, the script emits source/reference descriptors and the
needs-registration report without proposing a shape candidate.

Reusable API
------------
    target, regions, masks = target_descriptors(target_directory)
    fitter = RearFitter(features(regions), maximum_evaluations=95)
    candidate, search_report = fitter.search()
    full_positions, full_triangles = fitter.full_candidate(candidate)

The calling workflow must retain the ROI/pose acceptance status. A numeric
candidate does not replace that information. No main .hip, editor or existing
model files were changed by this fitter.
