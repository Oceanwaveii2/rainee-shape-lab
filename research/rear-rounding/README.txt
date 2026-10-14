Rainee rear-rounding research candidates

Latest verified optional static study:
  native-study/Rainee-Optional-Radial-Rounding.hip
  native-study/preview-manifest.json
  native-study/verification-native-flow.json
  native-study/verification-source-stature.json

The radial-relaxation VFL has now been compiled and cooked in Houdini 22.0.368.
Four static states 1,1.5,2,2.5 passed native/NumPy parity, measured cage volume,
neutral identity and fixed-region/height checks on the locally repaired body:
121,901 points, 252,337 triangles. A native finite-difference field audit covered
all 39,273 repaired rear ROI points; no negative sampled Jacobians. The native
source-stature export branch removes unused points and uniformly restores the
113,383-point referenced surface to the original FBX coordinate height/origin.
Baseline and 2.5 source-stature checks passed within float32 precision. Static
native evidence does not certify dynamics, contact or exact artistic match.

Earlier NumPy morphology candidate (98,078-point un-repaired proxy):
  body-2.5x-round-flow-0.65-volume-fit.bin
  rear_rounding_flow.py
  round_lobes_flow.vfl
  flow-case.json
  comparison-flow-three-views.jpg

The exact-volume radial-relaxation candidate visibly rounds the actual upper
corners and lower silhouette more than the direct v3 deformation. It still has
attachment/cleft bands and is not an established Grok match. All outputs retain
98,078 source point indices; triangles/material correspondence is unchanged.

Matched default cage amplitude: 0.450446808245033
Measured closed-cage ratio: 2.499999999824623
Minimum sampled body-field Jacobian: 0.045904286310723415
Sampled negative body-field Jacobians: 0
Neutral identity, finite geometry, overall height, fixed-region positions passed.
Full NumPy body cook: approximately 2.45 seconds, 20 RK4 steps.
Fixed regions: source Y<=.48, Y>=.77, Z>=.015, or abs(X)>=.22.
These coordinate regions protect the head/feet, upper waist, front pelvis and
outer arms in this source mesh. Other local rear attachment points can move.

The NumPy kernel calibrates the SAME corrected cage it uses to deform the body.
Do not feed this VFL an amplitude from the old direct-only cage solver. The VFL
has a compiled/verified counterpart with a roundness parameter in native-study.
The recorded four native static states are the current evidence; original
NumPy-only numbers above are retained as prototype history.
Only the recorded default controls/ratio were audited; other controls need an
audit. Positive sampled Jacobians do not establish collision-free triangles,
watertight anatomy or physical tissue behavior.

Prior direct-ray candidates:
  body-2.5x-round-0.65-volume-fit.bin
  Matched amplitude .4723725569138031, cage ratio 2.499999999313888.
  Minimum sampled Jacobian .0990562, no sampled negative Jacobians.
  comparison-three-views.jpg shows only a modest rounding improvement.
  rear_rounding.py and round_lobes.vfl are this direct projection candidate.

Rejected research:
  Direct ray strength .90 has 154 sampled negative body Jacobians.
  Broad-support direct projection .65 has 67 sampled negative Jacobians.
  These binaries are diagnostics and must not be exposed as approved presets.

All image comparisons use the same orthographic front/back/rear-three-quarter
cameras, same triangle indices and lighting. They show a body region with
X in [-.265,.265], Y in [.435,.765]. They are mesh renders, not cropped reference
images or generative images. The original FBX and reference media are untouched.

Source authority: FBX stature/general identity; selected consistent figurines
and drawings refine anatomy; early Grok close frames guide growth. The flawed
FBX surface is not an anatomical ground truth. Closed cage volume is a control
quantity, not a measured tissue volume.
