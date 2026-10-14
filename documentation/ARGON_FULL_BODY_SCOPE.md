# Argon full-body bridge: scope, contracts and evidence gates

This handoff is a plan for advancing the existing Rainee app into a coherent full-body authoring and measurement system. It distinguishes current retained evidence from proposed implementation. The shared model registry delivered with the package must identify the actual included meshes, their coordinate frames, hashes and local-original lookup paths. This document does not assert that the full-body reconstruction, registration, rig, camera calibration or reference fit is already complete.

## Design authority and invariants

- **Argon's curvilinear v5 design has the user's design authority.** Evaluate and extend it without silently substituting a generic human-body template or normalizing away the intended exaggeration.
- **Stature anchor:** the original FBX height is **2.3951061964 source units**. Physical metres/centimetres are unknown. Preserve that anchored stature in the rest body and report any drift explicitly. Hair, ears, heels, a display base or a kneeling pose must not redefine stature.
- **Shape authority:** approved art, accepted growth frames and clearer torso/face references refine the anatomy. The source FBX is a flawed sculpt and is not authoritative for the pelvic gap, hidden anatomy or facial likeness merely because it supplies height.
- **Growth:** accepted stages are **0000 → 0010 → 0018 → 0026**, followed by **holding 0026**. Later deflation and shortened proportions in generated video are rejected. Stage IDs are ordinal observations, not measured volume multipliers. Keep pose and camera changes separate from growth.
- **Thighs:** design and measure them independently from rear growth, using the strong-thigh references. Do not inflate every lower-body region by one global scale.
- **Face:** accepted frames and the clearer torso/face images supply identity cues. Hair colour, ears, costume and donor identity remain attribute-specific evidence rather than a licence to replace the whole character.
- **Structure:** the pelvis must support connected external skin and continuous attachments to the abdomen, rear lobes and inner thighs. Repair the source gap as a structural error. Detailed internal genital anatomy is outside this bridge's scope.
- **Pose:** distinguish the exaggerated lumbar arch and pelvic orientation from bending at the hips. Large posterior projection should remain visible without requiring an unintended forward bend or shortening the legs.
- Preserve full local originals, reversible controls and provenance. Never overwrite donor geometry to make it appear registered or accepted.

## Retained geometry and what it means

The four earlier R01–R04 primary models retain **1,836,182 vertices / 3,407,608 triangles** in total, with exact extracted coordinates. Their geometry includes costume, hair, shoes, bases and props. They have independently generated topology and unreviewed semantic regions. Their complete-asset bounds are not anatomical dimensions or evidence of a common physical scale.

The new raw OBJ has **749,820 vertices / 1,499,800 triangles**; the new FBX has **749,122 vertices / 1,498,428 triangles**. Treat them as separately identified inputs until registration and mesh comparison establish whether they represent the same surface. Count differences alone do not prove a shape difference. The preceding OBJ audit found one indexed component and zero indexed boundary edges; it did not certify winding, lack of self-intersections, anatomical acceptance or a usable enclosed tissue volume.

Keep three classes of geometry explicit:

1. **Original asset:** the unmodified full mesh, its authored transforms and all attachments.
2. **Derived regional evidence:** labelled triangles, sampled surfaces, landmarks, cross-sections and charts, each linked to the original mesh and extraction parameters.
3. **Authored Rainee body:** a registered, connected external surface with its own topology, controls, growth states and rig. Its acceptance is separate from a donor's existence.

Anatomical extents must be calculated on the anatomical region. Complete-asset bounds can assist loading and inspection, but must never be relabelled as body height, hip width, pelvic depth, thigh circumference or volume.

## Semantic body map

Build a reviewed region map before aggregating body measurements. At minimum identify:

| Region | Needed landmarks/attachments | Principal authoring purpose |
|---|---|---|
| Head and face | Crown of skull, chin, eye centres, mouth corners, nose and ear roots | Identity, facial proportions and expression |
| Neck and shoulder girdle | Neck base, clavicle/shoulder points, upper-arm roots | Head support, shoulder width and arm attachment |
| Thorax and bust | Ribcage envelope, sternum centre, bust attachment boundaries | Torso shape with bust controls separated from ribcage |
| Abdomen and waist | Waist station, navel cue, lower ribcage and iliac transition | Narrow-waist continuity and torso length |
| Pelvic core | Pelvic midline, sacral region, lateral hip landmarks, external crotch bridge | Stable connected support and pelvis-relative frame |
| Left/right rear lobes | Upper pole, lateral pole, posterior pole, cleft and underfold boundaries | Exaggerated paired form and staged growth |
| Left/right thighs | Hip attachment, anterior/lateral/medial sections, knee centres | Independent thigh mass, taper and mobility |
| Lower legs and feet | Knee/ankle centres, heel and sole contacts | Stature, stance and leg proportions |
| Arms and hands | Elbow/wrist centres, hand roots and fingertips | Full-body silhouette and gesture |
| Excluded attachments | Hair, costume, ears, jewellery, heels, props, display bases | Separate geometry, appearance and collision layers |

Labels may overlap at blended attachment bands. Store whether a label is artist-reviewed, algorithmic, provisional or unknown. An indexed component is not a semantic region: UV seams may split physical surfaces, and connected costume may share a component with skin. Record occluded and ambiguous landmarks explicitly instead of inventing them.

## Registration, cameras and correspondence

### Registration

Use reviewed stable landmarks to solve translation, orientation and uniform scale for each donor. Maintain the original-to-inspection-to-canonical transforms independently. Record residuals and unit semantics. Prohibit nonuniform scaling as a hidden registration shortcut; if used as a deliberate shape operation, expose and label it.

A cropped or kneeling donor needs a local pelvic frame. A proposed pelvic-height scale, `Hp = y_waist - y_fold`, is useful only when the waist and fold landmarks are visible, defined consistently and reviewed. It cannot reconstruct missing legs or establish physical height. Pose unbending requires correspondence or a rig; renormalizing the complete Y bounds is not pose recovery.

### Camera fitting

For every image/view retain crop, image size, perspective/orthographic choice, camera orientation, focal/FOV parameters, framing and uncertainty. Estimate camera using stable visible anatomy or rigid base features before interpreting silhouette changes as growth. Keep camera parameters out of the anatomical shape state.

The eight retained videos have four visually supported candidate export families: V01/V04, V02/V07, V03/V08 and V05/V06. Five sampled views suggest paired sequences, but decoded-frame equality and complete alignment have not been certified. Do not count them as eight independent sequences or assume a calibrated rigid turntable. Model associations remain unassigned.

### Surface correspondence

Independent donor vertex indices cannot be subtracted or fed directly into PCA. Establish a common labelled template, surface chart or sampled semantic correspondence first. Use a rigid/similarity initialization, landmark alignment, then bounded nonrigid registration with attachment constraints. Retain masks and residuals for clothing, occlusion, incomplete body regions and generated ambiguities.

Choose a correspondence that supports the actual form. A single radial chart or rear depth map cannot represent every fold, undercut, medial contact or seated overhang. Use multiple charts or a surface representation with explicit front/back intersections where needed. Validate chart Jacobians and orientation; do not force every donor into a global fixed cleft azimuth.

## Full-body representation and attachments

Use the v5 rear construction as a regional authoring component, connected to a broader body scaffold. Proposed components include a spine/torso curve, pelvic frame, bilateral rear patches, independent thigh profiles and continuous transition bands. Preserve bilateral correspondence while allowing reviewed asymmetry.

Compare representation choices through small controlled experiments rather than declaring one universally superior:

- **Profile curves and curvilinear charts:** compact controls for upper shelf, posterior projection, side contour and fold position. Validate their behaviour across the whole azimuth and attachment bands; a correct rear view alone is insufficient.
- **Rational bicubic patches/NURBS:** useful editable surface control where the chart is regular. Four-by-four rational control points alone do not demonstrate a general NURBS implementation or automotive Class-A quality. Specify degree, knots, weights, domain and evaluation rules. Inspect positional, tangent and curvature continuity at joins; zebra shading is diagnostic, not certification.
- **Implicit unions/R-functions:** useful for connecting pelvic core, rear lobes and thighs while preserving a closed envelope. A distance-like field is not automatically an exact signed distance function. Smoothing can erase the cleft or underfold, so retain those as explicit controlled features and quantify the effect on attachment shape.
- **Corresponded shape bases/PCA:** useful after consistent registration and semantic correspondence. Do not interpret modes dominated by pose, hair, bases or inconsistent point order as anatomical variation. For `n` centred examples there are at most `n-1` independent sample modes; nine assets do not constitute a broad trained body model. Report reconstruction and held-out errors, not only training projection error.
- **Gaussian/GOF/2DGS evidence:** useful for visual reconstruction and surface hypotheses. Gaussian opacity thresholds depend on ray/view, opacity and sampling; a median-transmittance radius is not certified tissue thickness, circumference or volume. Surfel planarity is not watertightness. A local covariance transport `J Σ Jᵀ` is first-order and does not prove a global deformation without foldover or self-contact errors.
- **View-dependent profile corrections:** may preserve stylized silhouettes for selected cameras, but store them as view-conditioned appearance/shape corrections. Measurements and canonical exports must use the uncorrected canonical body unless a correction is explicitly included and named.

Surface fairing and curvature estimation need appropriate units, resolution studies and boundary conditions. Curvature noise from triangulation, UV seams or generated texture detail must not become anatomy. Fixed fairing constants should be tested under scale and resolution changes. Research names and citations describe inspiration; they do not establish that a paper's complete method has been implemented.

## Measurement and objective contracts

Offer a whole-body ledger with measurement definition, region, pose, units, confidence and provenance. Candidate quantities include skeletal landmark lengths, shoulder/ribcage/waist/pelvic widths, torso length, paired-lobe posterior projection and upper-pole height, thigh/knee/calf/ankle sections, stance width and limb proportions. Define whether each is a surface envelope, landmark distance, projected image quantity or closed-region volume.

Keep image and geometric objectives distinct. A proposed fitting objective is:

`L = Σ_view w_view L_projected_silhouette + Σ_landmark w_landmark L_landmark + Σ_region w_region L_surface + λ_attachment L_attachment + λ_fair L_fairness + λ_invariant L_invariants`.

Each term requires an explicit domain and normalization. Use projected contours only in the associated fitted camera. Landmark weights must incorporate visibility/confidence. Surface distances apply only to registered, labelled comparable regions. Attachment/fairness terms regularize the authored body rather than declaring the donor physically correct. Height and protected-region terms enforce actual invariants; they must not be merely tiny penalties that a silhouette fit can ignore. Publish term values and residual overlays, not just a single score.

Closed anatomical volume is available only for an explicitly selected, consistently oriented, closed and sufficiently self-intersection-checked anatomical surface. Open sections, cropped donors, splat-centre bounds and ellipse pixel areas must remain their correctly named quantities. A growth-stage control value or cage scale must not be reported as a measured tissue-volume ratio.

## Proposed JSON interfaces

These are contracts to implement and version, not assertions that every field already exists.

```json
{
  "schema": "rainee-full-body-bridge-v1",
  "asset": {
    "id": "registry-id",
    "source_sha256": "recorded-source-hash",
    "representation": "mesh",
    "coordinate_frame": "source",
    "unit_semantics": "unknown physical scale",
    "original_to_canonical": null
  },
  "region": {
    "id": "pelvic-core",
    "selection_ref": "versioned-region-selection",
    "label_status": "provisional",
    "excluded_regions": ["hair", "costume", "base", "props"]
  },
  "landmarks": [],
  "camera": {
    "image_ref": "registry-image-id",
    "model": "unassigned",
    "parameters": null,
    "calibration_status": "unreviewed"
  },
  "state": {
    "pose_ref": "canonical-rest",
    "growth_stage": "0026",
    "thigh_controls_ref": "independent-thigh-state",
    "view_correction": null
  },
  "measurement": {
    "definition": "explicit quantity and region",
    "value": null,
    "units": "source units",
    "confidence": "unassigned",
    "method_version": "versioned-method",
    "validity_gates": []
  }
}
```

Use `null` for missing/unassigned values, never zero. A landmark record needs position, coordinate frame, semantic definition, visibility, uncertainty/confidence, author/reviewer and source reference. A result needs input hashes, parameter hash, code version, extraction region, pose/camera state and checks performed. Save registrations, body authoring parameters, cameras and review decisions as separate versioned objects. Import must reject mismatched source hashes or incompatible schemas rather than silently adapting them.

## Rigging, deformation and continuity

Construct the accepted rest surface before adding dynamics. Preserve skeleton/landmark lengths independently from skin volume changes. Use pelvis-relative growth and local attachment controls; the spine arch, hip rotation and forward bend must remain independent controls. Keep face, hands, feet, stature and other protected regions fixed unless the selected operation explicitly targets them.

Test neutral stance, intended arch, hip flexion, walking, seated/kneeling states and asymmetric leg movement. The pelvic bridge and rear-to-thigh/abdomen transitions must remain connected without unstable pinching or unintended gaps. Check triangle/field orientation, local deformation Jacobians, surface self-intersections, left/right contact, clothing clearance and ground/base contact. Positive sampled Jacobians alone do not prove collision-free geometry; discrete checks do not certify unsampled intermediate states.

Growth must progress through the accepted stages and hold the endpoint during subsequent action. Rest growth, pose deformation and contact/dynamics should be separate evaluation stages with separately inspectable outputs. Clothing and hair need their own attachments and collision treatment. Do not treat changing costume geometry as tissue growth.

## Implementation phases and acceptance gates

| Phase | Deliverable | Gate before advancing |
|---|---|---|
| 1. Evidence inventory | Shared registry, original/derived hashes, explicit roles and duplicate families | Every retained asset resolves; omissions and local-only originals are documented |
| 2. Semantic annotation | Reviewed regions, landmarks, visibility and exclusion masks | Anatomy separated from full asset; ambiguous landmarks remain labelled unknown |
| 3. Registration/cameras | Separate donor transforms, pose information and per-view cameras | Residuals shown; no hidden stature normalization or pose-as-growth substitution |
| 4. Full-body scaffold | Connected torso/pelvis/limbs and v5 regional rear controls | Height invariant, continuous attachment bands, independent thighs and recognizable face cues |
| 5. Reference fit | Confidence-weighted objectives and residual overlays across accepted views | Regional fit improves without shortening, topology damage or uncontrolled protected-region motion |
| 6. Growth and rig | Accepted staged growth plus endpoint hold in representative poses | Full-body invariants, orientation and contact checks pass at relevant states and intermediates |
| 7. Export and review | Reproducible app state, geometry, reports and native bridge | Reimport reproduces the accepted state; package budget and original-data retention verified |

Tests must challenge the boundaries: cropped/seated donors, different camera framing, unknown region labels, reversed/ambiguous axes, independent topology, missing landmarks and rejected post0026 frames. Include regression checks for source preservation, height, thigh independence and endpoint hold. Synthetic convergence tests supplement, but cannot replace, real-reference residuals and artist review.

## Deliverables for Argon and artist decisions

Deliver the app and reproducible launch instructions; shared model registry; retained old/new geometry in the documented packaging format; uncropped identity/anatomy references; video metadata and duplicate-family assessment; this scope; regional/camera/registration contracts; existing verification receipts with their actual limits; and a local-original map for the heavy assets.

For each proposed improvement, Argon should return changes directly on disk or in a Git branch, exact input/code hashes, a runnable verification command, meaningful before/after views, measurement definitions, failure cases and a clear implemented-versus-proposed statement. Keep the published package below the user's 100 MB budget while preserving complete local originals. A lower-resolution preview may accompany exact retained geometry, but must not silently replace it or inherit its quantitative claims.

Artist review remains necessary for donor-to-Rainee associations, face/torso likeness, intended rear upper shelf and projection, cleft/fold character, thigh mass/taper, lumbar arch, asymmetry and allowed view corrections. Unassigned evidence is not a request to discard it; retain it with uncertainty until those design choices are resolved. Numerical tests can establish reproducibility and structural validity, while the artist establishes whether the resulting character is Rainee.
