Rainee Gaussian region growth experiment
========================================

Status: CPU numerical and vendored Spark graph-generation checks pass.
GPU compilation, browser rendering, visual fidelity, sustained performance,
anatomical segmentation and source-frame association remain unverified.
No source SPZ, archive, mesh or production character asset is modified.

Run from the Local Stuff workspace root:
  node --loader ./rainee/research/gaussian-growth/node-loader.mjs ./rainee/research/gaussian-growth/verify.mjs

The loader resolves only existing local Three.js and Spark modules; it does
not install packages. Node may print its experimental-loader warning. The
script writes verification.json and shader-audit.glsl in this folder only.

Equations
---------
Let d = p - c and q = sum_i (d_i / r_i)^2 for an artist-assigned ellipsoid.
For q < 1, let k = g - 1, u = 1 - q, w = u^3:
  F(p) = p + k w d
  gradient(w)_i = -6 u^2 d_i / r_i^2
  J_ij = delta_ij + k [delta_ij w + d_i gradient(w)_j]
For q >= 1, F(p) = p and J = I exactly. Neutral g = 1 is also exact identity.
The displacement and its first derivative approach identity at the boundary.

The two tangential eigenvalues are 1 + k(1-q)^3, and the radial eigenvalue is
1 + k(1-q)^2(1-7q). For 1 <= g <= 2.25:
  det(J) >= 1 - (g-1) * 32/49 >= 9/49, approximately 0.183673.
The CPU API and GLSL reject controls outside this range. Finite positive
radii of at least 0.0001 source units are required. Direct field() calls are
guarded; createField() validates and copies fixed controls once for bulk use.

This is a fixed-boundary compact map: centres inside the support stay inside
it. It stretches the interior and compresses an outer transition, rather
than increasing the ellipsoid's support extent. A larger desired exterior
silhouette requires a reviewed larger support or another boundary-moving
shape model. The g control describes local linear stretching at the centre,
not overall body volume, a physical inflation parameter or a growth stage.

Gaussian covariance is transported as Sigma' = J Sigma J^T. This is exact
for the local affine linearization of F, and only a first-order approximation
to the nonlinear transformation of a finite Gaussian. Means outside the
support remain fixed; Gaussian tails themselves are not clipped by the ROI.
The modifier preserves input colour and opacity. Their values and sums do
not measure tissue volume, density, mass or brightness conservation.

API and rendering path
----------------------
makeCovarianceGrowth() injects a CovSplat modifier through the instance
covObjectModifiers field, before Spark's object-to-world covariance transform.
The supplied Spark 2.3.1 constructor does not consume a covObjectModifiers
constructor option. Both SplatMesh extSplats/covSplats and SparkRenderer
accumExtSplats/covSplats must be true; existing extended storage is used.

The program operates in each source scene's coordinates. It does not scale
the whole scene, normalize a donor to Rainee's stature, or imply that these
appearance coordinates are body coordinates. Region assignment is manual.
Hair, clothing, props, nearby scenery and overlapping splat tails require
artist review. A moving guide is not accepted semantic segmentation.

Rest picking reads Spark's undeformed stored centres/covariances, not the
shader-modified result. Growth is reset to neutral before picking. Switching
assets cancels picking and pending growth timers; failed loads dispose the
partial scene and clear its loaded/assignment state. Only one scene is kept.
Rendering is requested on interaction or Spark dirty callbacks, not through
an idle requestAnimationFrame loop.

Camera assumptions
------------------
Initialization retains the same origin view as measurements/splats.js:
position (0,0,0), identity quaternion, looking along -Z, FOV 50 degrees.
This is an inspection hypothesis, not a calibrated reference camera.

Read-only inspection of the main viewer confirms its stored-camera trial
uses Matrix4.set(...cameraJSON.flat()), optionally inverts that matrix, then
decomposes position/quaternion and aims along the rotated -Z axis. The export
contains a rigid 4x4 matrix but does not declare camera-to-world versus
world-to-camera direction or intrinsics. Neither direction is accepted here.
If the origin view is ineffective during GPU review, use a stored/inverse
trial under that same explicitly uncalibrated convention; source geometry
must remain unchanged. No source frame number is inferred from that matrix.

Evidence and remaining checks
-----------------------------
verify.mjs checks 2,400 controlled numerical cases, finite-difference J,
positive determinants, nonspherical positive-definite covariance transport,
boundary continuity, exact neutral/outside identity, public input guards,
and copied fixed controls. It also inspects all 1,179,648 centres of the local
spz-04-d62ca9b1b3 payload under an artificial region, confirms stored header,
compressed and raw payload hashes, and rehashes the unchanged SPZ afterward.
The artificial region has no anatomical or frame association.

The actual locally vendored Spark CovSplat graph is generated to GLSL. The
audit file is a Dyno graph fragment, not a standalone complete GPU shader;
Spark renderer common functions still supply its packing/math definitions.
Successful graph generation does not establish GPU compilation or rendering.

Before claiming a working Gaussian deformation view, GPU review must show:
the neutral source actually renders; an explicitly assigned appearance region
changes; outside centres are untouched; reset returns to neutral; rest picking
and asset switching behave correctly; and shader/console failures are absent.
Visual anatomical likeness and accepted growth-sequence fitting remain
separate work. This isolated prototype is not a production character rig.
