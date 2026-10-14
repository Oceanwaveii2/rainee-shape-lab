Rainee reference-model measurements (CPU, no generation)

Purpose
Read separately generated 3D reference assets even when they have different
topology. Separate their geometric width/depth descriptors from posture/center
descriptors. Original OBJ and FBX are read-only. Never transfer donor stature,
pose, clothes or props into Rainee simply because a bounding box differs.

Requirements: Python 3, numpy, Pillow. Installed locally and tested.
Run from the rainee/measurements folder, or use absolute paths.

1. Inventory a new model:
python model_compare.py inventory "C:/path/reference.obj" --out "reference-name"

This writes source buffers, SHA256, bounds/axis extents, object/group/material
tags, connected component sizes/bounds, raw SOURCE Y cross sections and a full
asset orthographic preview. Component IDs are sorted by vertex count. Those
are surface patches, not inferred body parts. Preview buffers are clustered
inspection geometry; they are not a repaired or production mesh.

2. Review calibration.json. Supply:
 - right/up/front source axes (x, y, z or negative versions),
 - head_top and feet_bottom 3D source coordinates,
 - explicit midline_origin in source coordinates,
 - source bounds/component/tag selection as useful,
 - artist_reviewed_body_only=true only after props/base/clothes are addressed,
 - pose_reviewed=true only after noting compatible or registered poses,
 - named region height_range and optional normalized lateral_range/depth_range.

3. Extract profile:
python model_compare.py profile --inventory "reference-name" --config "reference-name/calibration.json" --out "reference-name/profile.json"

If landmarks are absent, needs_calibration is emitted. If landmarks exist but
body-only selection or pose review is absent, exploratory profiles are emitted
with comparison_ready=false. The supplied Dexter model example has provisional
estimates solely for inspection; it remains unaccepted and comparison-gated.

4. Compare accepted model profiles:
python model_compare.py compare --base "baseline/profile.json" --target "inflated/profile.json" --out "difference.json"

Both inputs must be comparison_ready. Exact triangle-plane intersections compare
surface extents at corresponding landmark-normalized heights: compatible vertex
topology is unnecessary. Ratios are geometric constraints, not a fitted 3D
deformation. Rear extent is an extremum; tissue volume/circumference is not
claimed. Region metrics isolate candidate thigh, rear, torso etc only according
to the artist's explicit ROI definitions. Their accuracy depends on selection.

Sampled fitting equations
W(y,t)=W0(y)+t*(W1(y)-W0(y)); D(y,t)=D0(y)+t*(D1(y)-D0(y)).
C(y,t)=C0(y)+t*(C1(y)-C0(y)) describes surface-center displacement separately.
The midpoint of selected surface extrema is NOT the spine, skeletal pelvis
rotation or anatomical center. Do not interpret apparent arch as body tissue
growth, and do not shorten target stature while transferring a rear mass.
Corresponding region names are compared separately. Mixed or rotated poses
need registration before differences can be treated as mass changes.

Supplied files / actual findings
Dexter mom model.obj: 418,195 vertices, 836,562 triangles, source units unknown.
Source extents X=1.428404, Y=1.901719, Z=0.900411. Source Y is up in reviewed
geometry. X/Y shows the side silhouette; Z/Y is front/rear. Source X is candidate
front/depth and Z lateral, pending artist-confirmed signs/landmarks.
One object, one material, no useful body/prop tags. Main component has 402,452
vertices and contains the body, circular stand, teapots and dish sets. The
15,743-vertex secondary component is a detached top cup in the rear dish set.
Global bounds and component zero bounds are therefore NOT reliable body height.

dexter-mom/provisional-calibration.json uses unaccepted outer hair top and
approximate shoe/base contact Y. Rainee FBX includes ears in full source height;
hair/ear top differs from skull crown, and heels differ from barefoot stature.
No accepted cross-character anatomical ratio has been generated.

rainee-working-profile.json is a geometric profile of the existing Rainee proxy,
normalized by FBX full source height. The provided FBX metadata unit label does
not prove real-world centimeters. Strict body-landmark comparison still needs
the corresponding accepted landmark definition for Rainee.

Verification
python test_model_compare.py
Checks triangle-plane extents agree across different topology, source-axis
calibration, missing-landmark gating and disconnected prop components.

No shape generation, hidden-surface inference, training, medical anatomy
estimation, source overwrite or exact tissue-volume claims occur in this tool.

New purple-swimsuit reference archive 01a13749
Source ZIP: D:/0/Noir Fiction Engine/meshy_output/20261013_150229_image-to-3d_01a13749/20261013_150229_image-to-3d_01a13749.zip
Extracted asset-only into reference-01a13749. archive-inventory.json records
archive and extracted-file hashes, byte sizes and safe extraction checks.
model.obj is 291,120 vertices / 582,268 triangles; one fused component includes
the figure, red twin-tail hair, metallic held prop and circular base. Source Y
is up, X depth/front candidate, Z lateral. Bent leg and turned torso mean raw
global-height and pose comparisons are gated.

Inspect http://127.0.0.1:5197/measurements/inspection.html and select either model.
New figure includes candidate material-role colors and local-ROI overlays;
they are inspection colors derived from provisional UV/texture classification,
not the full appearance textures. Original supplied preview.png is beside it.

Provisional local geometric constraints
python local_shape_constraints.py --inventory reference-01a13749 --config reference-01a13749/local-roi-config.json

This uses full OBJ triangles (not clustered preview) and source texture UVs.
Triangle-centroid color rules distinguish candidate skin, purple garment,
red hair and unknown surfaces; source-space ROIs then define local patches.
local-shape-constraints.json records the exact ROI coordinates and confidence.
local-roi-preview.png and texture-role-candidates.png make selection reviewable.

Actual selected target geometry: rear/waist lateral width ratio 2.30808 and
rear depth/lateral width 0.626238. These are soft outside-shape cues, not
accepted anatomy, tissue volume or a command to transfer foreign stature.
The ROI height is an arbitrary source-space cut window, not an anatomical
rear height. Area-weighted local ellipsoid fits report their residual,
orientation, center and partial directional coverage. Two rear patch axis
ratios are about 1.567 and 1.619; some waist/thigh fits are poor or rejected.
Pose and selection limitations must remain attached to any downstream fit.

python test_local_shape_constraints.py
Checks known rotated ellipsoid recovery, translation/scale invariance and
degenerate-sample rejection. scipy is used only for nearest-point color transfer
to the small inspection proxy; no dependency installation was required locally.
