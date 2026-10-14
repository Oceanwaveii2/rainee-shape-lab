# Rainee: lessons, numerical evidence and the next full-body bridge

This handoff separates the intended character, implemented geometry, measured quantities and remaining uncertainty. The character is still being constructed. Passing numerical tests does not establish that her likeness, anatomy or inflation matches the accepted references.

The current direct user direction makes **Argon's original v5 shape field the main shape baseline**. Earlier Sol shape experiments remain useful as clearly named legacy studies. A supplied document, generated model, test receipt or external AI explanation does not independently approve a shape or override the user's reference choices. See [ARGON_V6_EVALUATION.md](ARGON_V6_EVALUATION.md) for the authority decisions and corrections to the incoming upgrade.

## 1. Preserve these design decisions

| Decision | Consequence for the next implementation |
|---|---|
| The source FBX establishes stature. | Keep source height `H = 2.3951061964` in source units. No metre or centimetre scale has been established. Unreferenced/orphan points must not determine rendered body height. A donor's bounding-box height is not a replacement stature. |
| Accepted growth is `0000 → 0010 → 0018 → 0026`, then hold `0026`. | Treat the four stages as accepted ordinal shapes. Later shrinkage, including the rejected later geometry associated with `0049`, does not define the intended endpoint. Pose and camera changes must not reduce the held shape. |
| The thighs have their own design references and controls. | Do not infer thigh growth from a rear-volume slider or absorb thigh design into the paired lobe radius. Keep the intended thigh design consistent unless the user explicitly approves a separate change. |
| Strong posterior projection and lumbar arch are intentional. | Separate shape from spinal/pelvic pose. Do not shorten her, normalize the exaggeration, or substitute a bent-over pose for the intended standing silhouette. |
| The old sculpt's pelvic gap is a structural flaw. | Build a connected external pelvic bridge. Preserving the flawed source gap is not fidelity to the character. Confirm the repair under growth, leg motion and multiple views. |
| Accepted frames and the clearer torso/face shots guide identity. | The source sculpt is not the final authority for her face. Figurines, generated donor bodies and hairstyle variants are attribute-specific cues. |

The original heavy data stays local. A lean handoff must retain useful shape information, provenance and application code without presenting a compressed or generated proxy as an anatomical scan. The final upload/archive size is determined by the packaging receipt, not by this document.

## 2. One shared Argon field is now the reference geometry

The exact original field is transcribed in [argon-curvilinear-v5.mjs](../houdini/lab/argon-curvilinear-v5.mjs), exposing `evaluateArgonV5Field`, `extractArgonV5Surface` and `ARGON_V5_STAGES`. The shared implementation is the source of truth for this field; independently rewriting its constants in the editor, exporter or measurement tool would reintroduce drift.

Write the scalar source field as

\[
F_A(p;s,c),\qquad \mathcal S_s=\{p:F_A(p;s,c)=0\},
\]

where `s` selects an accepted source preset and `c` contains the field controls. This notation names the implemented source function; it does not replace its code with an approximation. The editor and mesh export must evaluate the same `F_A` and use the same coordinate convention.

[argon-source-fixtures.json](../houdini/lab/argon-source-fixtures.json) and [argon-source-parity.test.mjs](../houdini/lab/argon-source-parity.test.mjs) compare **four source presets**, extracted meshes at **resolution 24**, and **320 field samples**. This establishes parity with the supplied source at the tested inputs. It does not establish a match to all image references, correctness between every sample, or a physically calibrated growth process.

The latest consolidated [verification-v6-supercomputer.json](../verification-v6-supercomputer.json) records **14 passing CPU suites**. The [browser consolidation receipt](browser-consolidation-verification.json) also records the real canonical OBJ export with the view boost at `0` and `1.5`: its hash remains the same. That is useful evidence that a view/style adjustment did not silently rewrite the canonical exported geometry in that check. It is not a guarantee about every future view control.

The accepted-sequence audit checks **27 sampled closed, ordered states**. Closure and ordering at those samples are stronger evidence than screenshots alone, but remain discrete geometric checks. They are not a continuous-time proof, a self-contact solution, or a biomechanical simulation.

## 3. Quantities that must never be conflated

| Quantity | What it actually measures | What it does not establish |
|---|---|---|
| Source stature `H` | The retained source-coordinate height anchor, with the relevant referenced body geometry used for rendered invariants. | Physical units, donor stature, or correctness of source anatomy. |
| Cage control volume | Enclosed volume of a particular control cage. A ratio can calibrate deformation amplitude for that cage. | Tissue volume, image growth ratio, or a universal proportion scale. |
| Closed regional union volume | Volume enclosed by the generated regional union, including the modeled pelvic/thigh connections within its defined domain. | Isolated butt tissue volume or biological mass. |
| Anatomical/tissue volume | A quantity requiring an explicitly accepted body region and a valid enclosed surface. | It cannot be recovered from an open lobe patch, whole figurine, or a splat bounding box merely by assigning an anatomical name. |
| Projected image area | Pixels occupied by an outline or region at a particular camera/pose. | A 3D volume ratio. Depth, focal length, distance and occlusion can change the area. |
| Section width/depth | Extrema of triangle-plane intersections in a chosen geometric selection. | Circumference, skeletal position, or tissue volume. |
| Radial-chart/spline RMS | Residual in the explicitly defined chart and its normalization, often on the fit's own samples. | Anatomical accuracy, unseen-side correctness or held-out generalization. |
| Gaussian covariance | The size, orientation and local support of a rendering primitive. | A closed surface or anatomical volume. |

For an oriented closed triangular surface, a common geometric volume calculation is

\[
V=\frac16\sum_{(a,b,c)}a\cdot(b\times c).
\]

Its usefulness depends on the domain, winding, closure and absence of invalid overlap. A numerical value alone does not validate those prerequisites. Indexed boundary-edge counts can also be inflated by UV/normal seams, so index connectivity and physical surface continuity must be distinguished.

The earlier cage values `1 / 1.5 / 2 / 2.5` are control initialization. The four accepted stages do not imply four measured physical tissue-volume multiples.

## 4. Failures found in the proposed v6 numerical helpers

### Radial charts need observations and explicit assumptions

The incoming DEM helper used whole-asset Y bounds, fixed fold/waist fractions, row medians and supplied torsion offsets while describing itself as automatic, crop- and pose-invariant calibration. Props, hair, bases, cropping and a bent pose can change those bounds. The revised metadata calls it a **provisional manual pelvic chart**, with anatomical calibration and comparison readiness withheld.

`observed_mask` identifies sampled angular/height bins. `sampled_elevation` preserves missing bins as missing. Nearest-bin completion and smoothing produce a completed estimate for experimentation; they do not turn missing regions into observations. Empty, degenerate, invalid and entirely unobserved inputs are rejected. Vertex-density dependence and the inability of a single radial chart to represent every overhang remain limitations.

The original curvature calculation used the eigenvalues of a radial-grid Hessian as though they were surface principal curvatures. A constant-radius cylinder exposed the error: the radial grid is constant, but the cylinder has nonzero curvature. The corrected helper uses the first and second fundamental forms of

\[
X(\theta,y^*)=(r\cos\theta,y^*,r\sin\theta).
\]

With `E = Xθ·Xθ`, `F = Xθ·Xy`, `G = Xy·Xy`, outward normal `n`, and second-form coefficients `L = n·Xθθ`, `M = n·Xθy`, `N = n·Xyy`,

\[
H_m=\frac{LG-2MF+NE}{2(EG-F^2)},\qquad K=\frac{LN-M^2}{EG-F^2}.
\]

The cylinder regression checks radius `2`: outward signed mean curvature `−1/4`, Gaussian curvature `0`, shape index `−1/2`. These are curvatures of the **completed, recentered and untwisted chart**, not measured curvature of the original donor mesh. See [test_v6_numerics.py](../measurements/test_v6_numerics.py).

### Read scene instances, not just mesh-local accessor arrays

The incoming GLB reader ignored the active scene and node transforms. It could omit instances, include unused meshes, and measure local coordinates as though they were world coordinates. The revised loader uses the existing scene-aware reader, applies parent transforms, transports normals with the inverse transpose, and reverses triangle winding for reflected instances:

\[
p_w=Ap+t,\qquad n_w=\operatorname{normalize}(A^{-T}n),\qquad \det A<0\Rightarrow\text{reverse winding}.
\]

Its regression includes repeated instances, a parent translation, nonuniform reflected scale, and rejection of an unevaluated animated input. Unsupported pose/compression cases must be evaluated or decoded explicitly rather than silently measured.

### Spline fitting is useful; the advertised certification was unsupported

The Python fitter used clamped cubic knots while the original JavaScript evaluator used a different uniform segment basis. The same control net therefore evaluated differently, especially at endpoints. Both now use compatible clamped rational cubic evaluation, with explicit knot-vector support and validation. Python/SciPy and JavaScript are compared on nonuniform knots, rational weights and endpoints.

\[
R(u,v)=\frac{\sum_{ij}B_i(u)B_j(v)w_{ij}c_{ij}}
                 {\sum_{ij}B_i(u)B_j(v)w_{ij}}.
\]

The fairing term is a **discrete control-net second-difference penalty**. It is not a demonstrated continuous thin-plate energy or an automotive Class-A certificate. The two rear charts are fit independently; no G0/G1 seam constraint is implemented. A smooth preview or low training residual cannot certify the seam. Historical API names are retained, while metadata states these limitations.

### PCA projection is not a nine-model trained anatomical learner

The implementation stores the charts and recomputes a batch SVD:

\[
X-\bar X=U\Sigma V^T,\qquad \hat x=\bar x+\sum_k\beta_k\sigma_kv_k.
\]

The exercised study uses **three inputs, including one synthetic scaled chart**. It is not a streamed nine-mesh anatomical training corpus. A small projection RMS for a chart already represented in the fitted data is a training-space reconstruction check, not held-out validation. The analytic browser `pcaBeta*` controls are style coefficients, not a loaded learned basis. Partial/nonfinite charts are not accepted as though they were complete observations.

### An opacity threshold must be allowed to have no crossing

The original ray helper returned the last splat depth even when accumulated opacity never reached the requested threshold. Two splats of alpha `0.1` accumulate only `0.19`; they must not invent an opacity-`0.5` surface. The corrected helper returns `null`/no crossing in that case.

\[
T_i=\prod_{j\le i}(1-\alpha_j),\qquad O_i=1-T_i.
\]

This is discrete sorted alpha compositing with an interpolation heuristic. It is not a full Gaussian Opacity Fields density integration or a certified surface extractor. See [v6-numerics.verify.mjs](../measurements/v6-numerics.verify.mjs).

## 5. Deformation transport and the v5 join correction

First-order Gaussian transport uses

\[
\mu'=\Phi(\mu),\qquad \Sigma'=J\Sigma J^T,\qquad J=D\Phi.
\]

This is a local rendering-support transformation. It does not by itself attach a splat to an anatomical surface, preserve tissue volume or prove global injectivity.

Earlier hard-cut/compact experiments exposed discontinuity or fold risks and boundary pinning. A replacement noncompact radial-weight experiment checks the tangential and radial eigenvalues. For the illustrative radial form `Φ(p) = c + [1 + a w(r)](p − c)`,

\[
\lambda_t=1+aw(r),\qquad
\lambda_r=1+a[w(r)+rw'(r)],\qquad
\det J=\lambda_t^2\lambda_r.
\]

The corrected experiment records positive eigenvalues over multipliers **0.5–3.5** in **804 CPU cases**. These are the tested field/range and sampled inputs, not a general theorem for arbitrary controls or stitched fields. The experiment is **not wired into the GPU rendering pipeline**. Do not describe the visual application as already using a verified surface-bound Gaussian growth method.

The legacy v5 body-map study also had a specific inner/outer join defect: the inner Hermite branch clamped its terminal slope to `min(sx, 2.2cs)`, while the outer branch started at `sx`. High lateral expansion with low separation made those slopes disagree. Removing the clamp would undermine its monotonicity purpose. The correction keeps the clamp and matches the outer branch before smoothly recovering the desired expansion:

\[
m_1=\min(s_x,2.2c_s),\quad
x_{in}=c_x[c_sh_{01}(t)+h_{10}(t)+m_1h_{11}(t)],\quad t=|x|/c_x,
\]

\[
x_{out}=c_xc_s+(|x|-c_x)\left[m_1+(s_x-m_1)S(c_x,c_x+0.020,|x|)\right].
\]

Here `S` is the smooth transition used by the implementation and `h` are cubic Hermite basis functions. At the join, both branches share the terminal slope and matching coefficient derivatives. Python, JavaScript and VEX carry the same correction. The **36-case** one-sided derivative/local monotonicity regression targets this former failure, including high width and zero separation. It does not certify the entire deformed body against global self-intersection. Default cases where the clamp is inactive retain the previous field. See [test_curvilinear_v5_join.py](../houdini/test_curvilinear_v5_join.py).

The winding helper remains a detached **radial-facing proposal**. A concave cleft can legitimately face a chosen center, and a source-specific vertex threshold is not a general VDB classifier. Proposals must not be automatically applied and then presented as certified outward orientation.

## 6. What the latest donor data actually establishes

The new measurements are recorded under [new-donor-20261014](../measurements/new-donor-20261014/manifest.json), with separate [OBJ](../measurements/new-donor-20261014/obj-inventory.json) and [FBX](../measurements/new-donor-20261014/fbx-inventory.json) inventories.

| Asset | Vertices / triangles | Source-coordinate bounds | Scope |
|---|---:|---|---|
| New OBJ | `749,820 / 1,499,800` | Min `[-0.297160, 0, -0.297678]`; max `[0.342350, 1.136970, 0.270847]` | One indexed component; zero indexed boundary/nonmanifold edges and zero zero-area triangles reported. These are whole-asset index/geometric facts, not anatomical acceptance. |
| New FBX | `749,122 / 1,498,428` | Raw geometry min `[-0.3297770023, 0, -0.114812999964]`; max `[0.3211370111, 1.1872719526, 0.1518599987]` | Raw geometry coordinates. Model scale `[100,100,100]` and tiny X rotation about `−4.3257e−6°` are listed, **not applied** to these bounds. |

The files differ in counts and raw bounds. Do not assume vertex correspondence, identical world transforms or compatible physical units. The supplied figure image is a cropped character reference with costume, hair/tail and other shape cues; the dataset does not establish a new full-body stature anchor merely because it is a new model.

For comparison, the retained R01–R04 primary geometry inventories contain `405,713 / 751,140`, `343,386 / 640,530`, `452,290 / 840,980`, and `634,793 / 1,174,958` vertices/triangles respectively. Their stands, hair, garments and carried props belong to whole-asset extents. More triangles or a closed index graph does not make a donor more anatomically correct. Compare artist-approved body regions after pose, axis and scale review.

The video duplicate families are currently recorded as **A: 01/04, B: 02/07, C: 03/08, D: 05/06**. This grouping avoids counting repeated evidence as independent scans. It does not certify that each family is a rigid turntable with fixed camera, unchanged geometry or calibrated intrinsics. A likely normalized donor whole-asset Y span near `1.90` is an inspection observation/hypothesis, not accepted body stature. AI-generated rotation can change geometry between views.

## 7. The next full-body validation dataset

Before claiming a full-body bridge is correct, assemble a small, explicit dataset rather than adding more unregistered images indiscriminately:

1. **A canonical rest body.** Provide the stature anchor, referenced body selection, source units, body axes and named head/feet landmarks. Separate hair, costume, base and props. Mark the pelvic repair and the intended external connection explicitly.
2. **The four accepted shapes in one coordinate frame.** Keep head, torso, leg lengths and the independently designed thighs consistent. Record which controls define each accepted stage. Preserve `0026` at later hold frames.
3. **Approved orthographic or calibrated perspective views.** Supply front, side, rear and rear-three-quarter views with camera type, focal/FOV data, pose and crop limits. Mark which outlines are authoritative and which are stylistic alternatives.
4. **Body-region annotations.** Identify pelvic anchors, paired rear surfaces, fold/waist landmarks and thigh interfaces. Record confidence and acceptance separately from a generated color segmentation or an indexed component number.
5. **A bridge deformation audit.** Check protected-region drift, joint/leg continuity, pelvic connection, triangle orientation, boundary/manifold status, self-intersection and volume of the explicitly selected domain. Audit growth and leg/pelvis motion together without importing donor pose into mass growth.
6. **Held-out tests.** Reserve approved views or donor measurements that are not used in fitting. Report image silhouette residual, section residual and 3D domain validity separately, with units and camera assumptions. Keep failures visible instead of renaming an in-sample reconstruction RMS as accuracy.
7. **A render/geometry separation check.** Export the canonical geometry under alternative view boosts and compare hashes/coordinates. If a deliberate view-dependent correction is needed, name it and retain a canonical geometric representation for measurements.

For camera ambiguity, retain several plausible depth/camera explanations rather than forcing one image to decide hidden anatomy. A body-only mesh/SDF or constrained shared surface can supply canonical measurements; splats can supplement visual evidence, but should not silently replace that measurable domain.

## 8. Research leads and boundaries

These primary references informed possible directions; citations do not mean their full methods are implemented here:

- [Rademacher, *View-Dependent Geometry*, SIGGRAPH 1999](https://doi.org/10.1145/311535.311612): a basis for deliberately separating view-dependent artistic corrections from one canonical surface.
- [Lin et al., *BARF: Bundle-Adjusting Neural Radiance Fields*, ICCV 2021](https://openaccess.thecvf.com/content/ICCV2021/html/Lin_BARF_Bundle-Adjusting_Neural_Radiance_Fields_ICCV_2021_paper.html): camera/scene estimation is relevant when observations form a coherent scene; conflicting generated drawings do not automatically meet that assumption.
- [Rivers, Durand and Igarashi, *3D Modeling with Silhouettes*, SIGGRAPH 2010, author-hosted paper](https://www-ui.is.s.u-tokyo.ac.jp/~takeo/papers/alec_siggraph2010_silhouette.pdf): persistent artist-approved contours can be more informative than radius sliders. The paper targets man-made objects and explicitly says organic models are not well suited; use its persistent silhouette editing idea rather than treating it as a ready character reconstructor.

The imported upgrade's names invoking Class-A NURBS, nine-mesh PCA, GOF, SuGaR, Gaussian Frosting, automatic pelvic calibration and other published methods must be evaluated against actual code and data. A research citation is not evidence that the named method was reproduced, trained, calibrated or validated.

The unrelated Antigravity/Red Note material describes a 2D graph/application context. It is not evidence for this 3D character pipeline and must not be used to infer geometry, calibration or simulation capabilities.

The useful next outcome is a full-body bridge whose source authority, geometry, camera assumptions and failure cases can all be inspected. The open issues are likeness, anatomical region acceptance, pose/camera registration, pelvic/thigh continuity and continuous deformation validity—not the existence of additional scientific-sounding labels.

## Critical coordinate discovery from the delivered buffers

The C00 working body and N-prefixed native caches inherit normalized source-proxy coordinates. Their referenced Y extent is approximately **0.998830**, not 2.395106 source units. The app adapts their referenced foot/top range into exact canonical H=1, then uses the original 2.395106 stature and source origin for export. **Do not divide these already normalized buffers by 2.395 again.** The registry and `body-coordinate-adapters.json` provide explicit row-major source-to-canonical matrices.

R05 uses its raw OBJ coordinates. R06 uses raw FBX node-local coordinates with model scale100 listed but unapplied. R01–R04 use previously extracted GLB scene-world coordinates. D-prefixed older entries span their whole generated assets but are **vertex-cluster inspection proxies**; their original large GLBs/OBJs remain local. These different frames/representations must not be merged by filename or identical Y extents.

The legacy `source_dimensions_cm` metadata label is incorrect: its values are uncalibrated source-unit extents. The original dense FBX has15,853,005 vertices,17,673,962 polygons and31,691,060 fan triangles in a719,296,320-byte file; its T00 transfer proxy is98,078 vertices/220,971 triangles. This is a documented source approximation, distinct from the complete geometry of the two newest donors.

