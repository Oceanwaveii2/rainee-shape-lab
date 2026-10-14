# Rainee â†’ Argon: full-body model processing handoff

This is the consolidated scope, executable data bridge and evidence record for extending Argon curvilinear v5 from a regional shape studio into an entire-body character system. **Argon v5 remains the user-selected design authority.** Preserve the intended exaggeration, source stature and independent thighs.

The package contains the app, previous reference data, complete geometry for the four earlier primary GLBs and both newest donors, original-template inspection geometry, current working-body geometry, exact native growth caches, image/video viewing derivatives, model registry, processing tools and the findings from integration. It does not claim that anatomy registration or the final character is complete.

## Start here in an Argon sandbox

Unzip the packet into one directory. Run these commands from its root:

```sh
python tools/argon_model_bridge.py list
python tools/argon_model_bridge.py verify --out expanded/full-body-verification.json
python tools/argon_model_bridge.py inspect --id R05-new-obj --sections 19 --out expanded/R05-sections.json
python tools/argon_model_bridge.py inspect --id R06-new-fbx --sections 19 --out expanded/R06-sections.json
python tools/argon_model_bridge.py export --id R05-new-obj --out expanded/R05-complete.obj
python tools/argon_model_bridge.py export --id R06-new-fbx --out expanded/R06-complete.obj
python serve.py --port 5199
```

List/export and the server use Python's standard library; numerical inspection/verification require NumPy. The existing v6 master suite also requires SciPy, Pillow and Node. Expanded geometry and OBJ files can exceed 100 MB; the transfer ZIP is the artifact subject to the **100,000,000-byte** limit. Exported files go outside the immutable `models/` and `data/` directories.

Open `http://127.0.0.1:5199/houdini/argon-v5-studio.html`. The measurement lab, native growth study, reference workbench and donor workspace are linked. Existing raw `.bin` routes are restored by the local server. Static hosting alone does not perform that restoration.

**Do not use the small new-donor inspection LOD as the quantitative source.** The complete R05/R06 buffers are now in `models/full-body-bridge/`; the CLI reconstructs all their positions and triangle indices. No remote service or Windows original path is needed to read those delivered models.

## What is actually delivered

| ID | Retained vertices | Retained triangles | Representation / role | Coordinate frame |
| --- | ---: | ---: | --- | --- |
| R05-new-obj | 749,820 | 1,499,800 | whole generated asset; shape donor with unreviewed anatomy | raw OBJ coordinates |
| R06-new-fbx | 749,122 | 1,498,428 | whole generated asset; shape donor with unreviewed anatomy | FBX node-local coordinates; listed model transforms not applied |
| R01 | 405,713 | 751,140 | complete generated scene-world geometry; body/accessories unsegmented | GLB world transforms baked to float32 |
| R02 | 343,386 | 640,530 | complete generated scene-world geometry; body/accessories unsegmented | GLB world transforms baked to float32 |
| R03 | 452,290 | 840,980 | complete generated scene-world geometry; body/accessories unsegmented | GLB world transforms baked to float32 |
| R04 | 634,793 | 1,174,958 | complete generated scene-world geometry; body/accessories unsegmented | GLB world transforms baked to float32 |
| C00-working-body | 121,901 | 252,337 | full working body derived from original dense template; pelvic repair remains a proposal | already normalized source-proxy coordinates; use explicit runtime H=1 adapter |
| T00-inspection-proxy | 98,078 | 220,971 | lossy vertex-cluster proxy of original dense template, not a full-resolution measurement source | normalized H=1, X/Z centred, Y from original source foot; see prepare_mesh.py |
| N0000 | 121,901 | 252,337 | full working-body native cache; cage schedule is artist initialization | normalized inspection/source-proxy frame |
| N0010 | 121,901 | 252,337 | full working-body native cache; cage schedule is artist initialization | normalized inspection/source-proxy frame |
| N0018 | 121,901 | 252,337 | full working-body native cache; cage schedule is artist initialization | normalized inspection/source-proxy frame |
| N0026 | 121,901 | 252,337 | full working-body native cache; cage schedule is artist initialization | normalized inspection/source-proxy frame |
| D0000 | 79,902 | 178,074 | whole-asset vertex-cluster inspection proxy; not full original source resolution | donor source coordinates; registration incomplete |
| D0010 | 86,914 | 193,298 | whole-asset vertex-cluster inspection proxy; not full original source resolution | donor source coordinates; registration incomplete |
| D0018 | 62,497 | 128,784 | whole-asset vertex-cluster inspection proxy; not full original source resolution | donor source coordinates; registration incomplete |
| D0026 | 52,632 | 108,207 | whole-asset vertex-cluster inspection proxy; not full original source resolution | donor source coordinates; registration incomplete |

These are 16 registered representations, not 16 independent anatomical ground-truth bodies. Native states share one working topology; D-prefixed entries are whole-asset inspection proxies; T00 is a lossy source inspection proxy. R01â€“R06 contain complete extracted geometry for their declared assets. R05/R06 preserve decoded **float64 positions and uint32 indices**, including negative-zero position bits; R01â€“R04 retain their prior float32 scene-world extraction. No texture maps, rig weights or original FBX/GLB file containers are reconstructed from these geometry buffers.

### The large original template

The original `Core Body (Template Only).fbx` is **719,296,320 bytes**, with **15,853,005 vertices**, **17,673,962 polygons** and **31,691,060 fan triangles**. A lossless full geometry extract alone compresses above the entire transfer budget. Its complete original stays local. The packet includes its documented **98,078-vertex / 220,971-triangle** inspection proxy, source structure/provenance, exact original bounds and stature, plus the complete current working-body mesh.

The stature anchor is **2.3951061964035034 source units**. The legacy metadata field named `source_dimensions_cm` contains source-unit extents, not calibrated centimetres. That label must not establish physical height. The original mesh's pelvic defect and facial shape do not override the user's art/identity decisions.

### Precision and compression

- The R05 OBJ positions lie on a decimal lattice. Store `q = round(10^6 p)` as int32 and reconstruct `p = q / 10^6` only after verifying that every decoded float64 bit equals the parsed original. Two negative-zero coordinate locations are restored explicitly. This is exact encoding, not approximate quantization.
- Every R06 stored float64 position is exactly recoverable from its float32 value. Widening that value back to float64 reproduces the original decoded geometry bytes. Its model scale `[100,100,100]` is listed separately and **not** silently applied.
- Triangle indices use reversible delta/zigzag/byte-shuffle storage. XZ compression uses the Python standard library. Source vertex ordering and fan-triangle ordering are preserved.
- Native sparse caches can store uint32 XOR against the declared baseline. This preserves sign, exponent and mantissa bits; it does not interpolate or regenerate the 27 original cache frames.
- Core PNG references use full-size, uncropped **lossless WebP** viewing containers after decoded RGBA pixel equality is checked. Original PNG containers remain local; their source hashes are separate from derivative hashes. Existing supplementary JPEGs and small full-duration videos are explicitly viewing derivatives.

See `documentation/image-derivatives.json`, `documentation/native-xor-repack.json`, the model registry and buffer descriptors. The SHA-256 checks fail if decoded geometry or stored blobs differ.

## Authority and correspondence decisions

The source FBX supplies stature; the accepted art/frames and clear torso/face shots supply likeness and intended anatomy; Argon v5 supplies the shape direction. Generated donors supply regional evidence after reviewed registration. Treat the newest OBJ and FBX independently: different counts, raw bounds and scene metadata do not establish equivalence. Do not equate cropped, kneeling, accessorized or normalized full-asset bounds with body height.

Maintain **0000 â†’ 0010 â†’ 0018 â†’ 0026, then hold 0026**. The later deflation/shortening is rejected. Stage IDs and native cage ratios are initialization/control quantities, not measured tissue volumes. Thigh growth and rear growth remain independent; pose, lumbar arch, camera and deliberate view adjustment remain separate.

## The next work Argon should perform

1. Verify and inspect the delivered complete models. Return source/decoded hashes and a role-aware inventory. Establish which models/views correspond before assigning fitting weights.
2. Add reviewable body/accessory masks and landmarks. Head, torso, pelvic core, rear lobes, thighs, lower legs, feet, arms and hands need explicit regions. Hair, costume, ears, props and bases need separate treatment.
3. Solve registration, pose and camera hypotheses separately. Preserve the fixed stature anchor and uncertainty; use reviewed pelvis-relative coordinates for cropped/seated donors.
4. Construct a connected full-body scaffold that carries Argon's rear shape, lumbar arch and independent thighs while preserving head/torso identity and limb length. Replace the flawed pelvic gap with coherent external structure.
5. Fit silhouettes, reviewed sections and landmarks across accepted views. Report reprojection, 3D-domain and continuity errors separately. Hold out views or donors for validation.
6. Test orientation, seam continuity, contact, self-intersection, pose transitions and protected-region drift. Implement rig/dynamics only after rest shape and anatomical domains are approved.
7. Return code on disk or a Git branch, runnable checks, actual before/after views, residual reports, failures and a clear implemented-versus-proposed statement. Do not relay raw diffs through chat.

The detailed scope, contracts, objective functions, research lessons and acceptance cases follow. They are requirements/plans for the unfinished work, not claims of an already calibrated full body.

---

# Argon full-body bridge: scope, contracts and evidence gates

This handoff is a plan for advancing the existing Rainee app into a coherent full-body authoring and measurement system. It distinguishes current retained evidence from proposed implementation. The shared model registry delivered with the package must identify the actual included meshes, their coordinate frames, hashes and local-original lookup paths. This document does not assert that the full-body reconstruction, registration, rig, camera calibration or reference fit is already complete.

## Design authority and invariants

- **Argon's curvilinear v5 design has the user's design authority.** Evaluate and extend it without silently substituting a generic human-body template or normalizing away the intended exaggeration.
- **Stature anchor:** the original FBX height is **2.3951061964 source units**. Physical metres/centimetres are unknown. Preserve that anchored stature in the rest body and report any drift explicitly. Hair, ears, heels, a display base or a kneeling pose must not redefine stature.
- **Shape authority:** approved art, accepted growth frames and clearer torso/face references refine the anatomy. The source FBX is a flawed sculpt and is not authoritative for the pelvic gap, hidden anatomy or facial likeness merely because it supplies height.
- **Growth:** accepted stages are **0000 â†’ 0010 â†’ 0018 â†’ 0026**, followed by **holding 0026**. Later deflation and shortened proportions in generated video are rejected. Stage IDs are ordinal observations, not measured volume multipliers. Keep pose and camera changes separate from growth.
- **Thighs:** design and measure them independently from rear growth, using the strong-thigh references. Do not inflate every lower-body region by one global scale.
- **Face:** accepted frames and the clearer torso/face images supply identity cues. Hair colour, ears, costume and donor identity remain attribute-specific evidence rather than a licence to replace the whole character.
- **Structure:** the pelvis must support connected external skin and continuous attachments to the abdomen, rear lobes and inner thighs. Repair the source gap as a structural error. Detailed internal genital anatomy is outside this bridge's scope.
- **Pose:** distinguish the exaggerated lumbar arch and pelvic orientation from bending at the hips. Large posterior projection should remain visible without requiring an unintended forward bend or shortening the legs.
- Preserve full local originals, reversible controls and provenance. Never overwrite donor geometry to make it appear registered or accepted.

## Retained geometry and what it means

The four earlier R01â€“R04 primary models retain **1,836,182 vertices / 3,407,608 triangles** in total, with exact extracted coordinates. Their geometry includes costume, hair, shoes, bases and props. They have independently generated topology and unreviewed semantic regions. Their complete-asset bounds are not anatomical dimensions or evidence of a common physical scale.

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
- **Gaussian/GOF/2DGS evidence:** useful for visual reconstruction and surface hypotheses. Gaussian opacity thresholds depend on ray/view, opacity and sampling; a median-transmittance radius is not certified tissue thickness, circumference or volume. Surfel planarity is not watertightness. A local covariance transport `J Î£ Jáµ€` is first-order and does not prove a global deformation without foldover or self-contact errors.
- **View-dependent profile corrections:** may preserve stylized silhouettes for selected cameras, but store them as view-conditioned appearance/shape corrections. Measurements and canonical exports must use the uncorrected canonical body unless a correction is explicitly included and named.

Surface fairing and curvature estimation need appropriate units, resolution studies and boundary conditions. Curvature noise from triangulation, UV seams or generated texture detail must not become anatomy. Fixed fairing constants should be tested under scale and resolution changes. Research names and citations describe inspiration; they do not establish that a paper's complete method has been implemented.

## Measurement and objective contracts

Offer a whole-body ledger with measurement definition, region, pose, units, confidence and provenance. Candidate quantities include skeletal landmark lengths, shoulder/ribcage/waist/pelvic widths, torso length, paired-lobe posterior projection and upper-pole height, thigh/knee/calf/ankle sections, stance width and limb proportions. Define whether each is a surface envelope, landmark distance, projected image quantity or closed-region volume.

Keep image and geometric objectives distinct. A proposed fitting objective is:

`L = Î£_view w_view L_projected_silhouette + Î£_landmark w_landmark L_landmark + Î£_region w_region L_surface + Î»_attachment L_attachment + Î»_fair L_fairness + Î»_invariant L_invariants`.

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


---

# Argon processing bridge specification

The bridge must turn imported full-body assets and reviewed image observations into reproducible measurements and reversible shape proposals. It must preserve the original assets, Rainee's stature anchor, the accepted four-stage inflation order, and independently authored thighs. Its primary result is an evidence-backed recipe, rather than a claim that an imported generated model already supplies correct anatomy.

**Status:** the accompanying registry, lossless R05/R06 readers, OBJ exporter and basic full-asset inspection CLI are now delivered and verified. The remaining semantic registration, camera solving, full-body fitting and rig/contact workflow below specifies the next implementation. The current application has a regional pelvis/rear/thigh authoring and measurement workflow, source-body context, reference views and experimental shape functions. It does not establish complete full-body reconstruction, semantic body segmentation, calibrated image recovery, or an accepted anatomical fit. Proposed readers, jobs, commands and adapters below must be marked pending until their outputs have been verified.

## 1. Deliverables and boundaries

The implementation should provide:

1. A model registry that identifies every immutable source and derived geometry artifact by hash.
2. Readers that expose mesh buffers, scene transforms, components and import limitations without executing supplied scripts.
3. Versioned semantic annotations, landmarks, alignment, pose and observation cameras.
4. Deterministic measurement jobs on canonical rest geometry, with explicit coverage and validity gates.
5. A full-body proposal interface that applies the Argon rear field while protecting stature and independently controlling thighs.
6. A review report and export recipe that another local program can reproduce from the same artifacts.

The bridge must not silently replace the original FBX, repair an imported source in place, infer physical metres from an unknown unit, treat asset bounding boxes as body measurements, or turn incomplete image evidence into a claimed unique 3D solution. Reference fitting, topology repair and anatomy acceptance are separate operations.

R05 OBJ and R06 FBX must enter the registry as independent sources. Their file formats and asset identifiers do not prove equal stature, matching topology, common pose, equivalent body regions or shared identity. No numerical equivalence or cross-model correspondence is asserted by this specification.

## 2. Coordinate and quantity contracts

Use column-vector homogeneous points and explicitly documented matrix storage. Store matrices as 16 row-major numbers; evaluate `p_out = M * p_in`. Record each transform's input and output frame. A transform is never inferred from its filename.

| Frame | Meaning | Required evidence |
| --- | --- | --- |
| `source-node` | Reader-local vertex coordinates | Reader version, source hash, node/accessor identity |
| `source-world` | Original scene after declared node transforms | Scene transform chain and axis/unit declaration |
| `aligned-rest` | Aligned asset before the proposed growth deformation | Reviewed landmarks and similarity/pose recipe |
| `canonical-rest` | Rainee rest coordinates, H = 1, +Y up, posterior âˆ’Z | Chosen stature source and accepted alignment |
| `posed-preview` | Pose applied for inspection or reprojection | Pose recipe; excluded from rest measurements |
| `observation-camera` | Projection into one image | Image hash, camera hypothesis/calibration, framing |

The known source stature anchor remains `2.3951061964035034` source units. Its physical unit is unknown. Keep `physicalUnitCalibration: null` until a reviewed calibration exists. Do not renormalize every donor by its entire asset bounds, crop height, hair, ears, footwear, plinth or props.

For a uniform source-to-canonical scale `s`, lengths scale by `s`, areas by `sÂ²`, and volumes by `sÂ³`. Nonuniform scale is a shape proposal, not a unit conversion. Reflection and negative determinant transforms need an explicit derived winding policy and provenance; do not overwrite source indices.

Use **Hp0**, a reviewed baseline pelvic length, when comparing cropped or kneeling donors. For example, Hp0 may be the canonical-rest distance between reviewed waist and lower-fold levels. The exact landmark definitions must be recorded. Hp0 stays fixed across growth stages. It is not a substitute for whole-body height and must remain null if either landmark is unreviewed or missing. Report H-normalized and Hp0-normalized quantities in separate fields.

## 3. Registry and artifact layout

Suggested layout:

```text
bridge/
  schemas/                 JSON schemas and schema migrations
  readers/                 Format adapters; no authoring logic
  jobs/                    Import, alignment, measurement and comparison jobs
  registry/models.json     Model identities and artifact references
  annotations/             Semantic masks, landmarks and their revisions
  recipes/                 Reversible alignment and shape proposals
  observations/            Images, camera records and accepted stage roles
  reports/                 Deterministic job receipts and comparison reports
  assets/                  Content-addressed compressed geometry buffers
```

Public artifacts use stable IDs and relative paths. A separate local resolver maps source IDs to full local files. This preserves complete originals for local work without embedding machine-specific paths in every public recipe.

Every artifact record needs both storage and decoded hashes. A decoder must verify the stored bytes, perform the declared decoding, verify the decoded bytes, validate lengths and index ranges, and reject failure before a measurement job starts. Hashes identify bytes; they do not certify anatomy.

The following are type contracts, followed by pending examples. Nullable hashes are allowed only while registration is pending. Runnable or accepted recipes require verified non-null hashes and supported schema versions.

```ts
type Sha256 = string; // exactly 64 lower-case hexadecimal characters
type Vec3 = [number, number, number]; // finite numbers
type Mat4 = number[]; // exactly 16 finite row-major numbers
type Artifact = {
  id: string;
  path: string;
  encoding: 'raw' | 'gzip' | 'gzip-shuffle32' | 'gzip-shuffle64';
  scalarType: 'float32-le' | 'float64-le' | 'uint32-le';
  tupleWidth: 1 | 3;
  elementCount: number | null;
  storedSha256: Sha256 | null;
  decodedSha256: Sha256 | null;
  decodedByteLength: number | null;
};
type GeometrySource = {
  schema: 'rainee-model-source-v1';
  modelId: string;
  registrationStatus: 'pending' | 'verified' | 'rejected';
  source: {filename: string; format: string; sha256: Sha256 | null};
  reader: {id: string; version: string | null; settingsSha256: Sha256 | null};
  positions: Artifact | null;
  triangles: Artifact | null;
  sourceAxes: string | null;
  sourceUnit: string | null;
  sourceWorldFromNode: Mat4 | null;
  measuredScope: 'full-asset' | 'segmented-body' | 'regional-proposal' | null;
  semanticAnnotationId: string | null;
};
```

```json
{
  "schema": "rainee-model-source-v1",
  "modelId": "R05",
  "registrationStatus": "pending",
  "source": {"filename": "R05-source.obj", "format": "obj", "sha256": null},
  "reader": {"id": "obj-mesh-reader", "version": null, "settingsSha256": null},
  "positions": null,
  "triangles": null,
  "sourceAxes": null,
  "sourceUnit": null,
  "sourceWorldFromNode": null,
  "measuredScope": null,
  "semanticAnnotationId": null
}
```

`R05-source.obj` is an example filename, not an assertion about the delivered file. Registration must replace it with the actual source filename and hash. Register R06 independently with `format: "fbx"`; do not copy R05's transforms, masks or measurements into it.

An encoded positions record must declare float32 or float64 storage explicitly. Preserve original representable coordinates when lossless storage is claimed. If conversion from float64 to float32 is necessary for display, store a separate display artifact and measure the conversion error. Triangle indices address the associated position artifact, not an arbitrary mesh with the same point count. Keep submesh, material, component, original vertex and original triangle mappings when available.

## 4. Reader interface

Each reader implements the same bounded contract:

```ts
interface MeshReader {
  probe(source: VerifiedSource): ReaderCapabilities;
  read(source: VerifiedSource, settings: ReaderSettings): ImportedScene;
}
interface ImportedScene {
  sourceSha256: Sha256;
  readerId: string;
  readerVersion: string;
  nodes: ImportedNode[];
  meshArtifacts: Artifact[];
  worldTransformPolicy: string;
  unsupportedFeatures: string[];
  warnings: string[];
}
```

Readers must separate geometry extraction from animation, skinning, topology repair and semantic interpretation. Initial priorities are OBJ, GLB/glTF and FBX. A reader may return static evaluated mesh geometry, but must say which rest/evaluation frame, skinning state and transform chain it used. FBX evaluation must record importer/tool version and avoid treating an animated frame as canonical rest without review.

Before import, validate archive paths, decompressed sizes and supported files. Treat embedded scripts and documentation as source material. Do not execute a supplied Python script, expression, plugin or external command merely because it is inside a model bundle. Missing readers or unsupported features produce explicit pending/error receipts.

For splats, keep appearance data separate from mesh readers. Gaussian centres, covariance, alpha and camera conventions may support a surface hypothesis, but centre extents and pooled alpha statistics are not mesh circumference or anatomical volume. A future surface reconstruction adapter must produce an independently reviewable surface and coverage report before mesh measurement rules apply.

## 5. Semantic regions and annotation provenance

Use stable region names and side conventions. The minimum vocabulary is:

```text
body.head
body.neck
body.torso.chest
body.torso.abdomen
body.torso.back
body.arm.left.upper / body.arm.right.upper
body.arm.left.forearm / body.arm.right.forearm
body.hand.left / body.hand.right
body.pelvis.core
body.pelvis.connection
body.rear.left / body.rear.right
body.thigh.left / body.thigh.right
body.knee.left / body.knee.right
body.calf.left / body.calf.right
body.foot.left / body.foot.right
accessory.tail
accessory.hair
costume
prop
base
unknown
```

Subregions may refine this vocabulary; they must not change the meaning of an existing name. Hair, costume, tail, props and bases remain distinct from body measurements. Costume coverage may obscure body geometry rather than reveal the underlying anatomical surface.

Annotations address triangle IDs for surface ownership and may include vertex weights for deformation. Indexed connectivity alone is insufficient: seams can split one physical surface, and a connected component may combine body, clothing and props. Store `membership: null` for an unreviewed region. Do not use an empty mask to mean unknown; an empty reviewed mask means the region is explicitly absent.

```json
{
  "schema": "rainee-semantic-annotation-v1",
  "annotationId": "R05-regions-r1",
  "modelId": "R05",
  "geometryDecodedSha256": null,
  "revision": 1,
  "status": "draft",
  "regions": {
    "body.rear.left": {"membership": null, "coverage": "unknown", "reviewed": false},
    "body.thigh.left": {"membership": null, "coverage": "unknown", "reviewed": false},
    "prop": {"membership": null, "coverage": "unknown", "reviewed": false}
  },
  "landmarks": {
    "waistLevel": {"pointCanonicalH": null, "reviewed": false},
    "lowerFoldLevel": {"pointCanonicalH": null, "reviewed": false}
  },
  "Hp0CanonicalH": null,
  "provenance": {"method": "manual-review-pending", "evidenceIds": [], "reviewer": null}
}
```

Masks require an associated geometry hash and index-range validation. A mask becomes stale when topology changes. A transfer operation must create a new annotation with correspondence evidence and residuals; it must not quietly reuse old triangle IDs.

## 6. Alignment, pose and camera are separate recipes

Align using reviewed corresponding landmarks and a declared transform family. Begin with a similarity transform: translation, rotation and one uniform scale. Report landmark residuals and missing correspondences. If nonuniform deformation or unposing is needed, create a separate reversible proposal with its own constraints and validity checks.

```json
{
  "schema": "rainee-alignment-recipe-v1",
  "recipeId": "R05-to-rainee-r1",
  "sourceModelId": "R05",
  "sourceGeometrySha256": null,
  "targetStatureSourceId": "rainee-fbx-stature-anchor",
  "targetHeightSourceUnits": 2.3951061964035034,
  "physicalUnitCalibration": null,
  "sourceWorldFromNode": null,
  "alignedRestFromSourceWorld": null,
  "canonicalRestFromAlignedRest": null,
  "transformFamily": "similarity",
  "landmarkCorrespondences": [],
  "landmarkResidualsCanonicalH": null,
  "poseRecipeId": null,
  "status": "draft",
  "acceptedEvidenceIds": []
}
```

An unposing adapter must distinguish skeletal pose from desired rest-shape arch. Rainee's exaggerated resting lumbar shape belongs to the identity/rest proposal when explicitly selected. Camera tilt, body tilt and transient bending belong to observation pose. Do not reduce posterior projection by shortening the body or undo the designed arch merely to fit an image.

Each image observation needs its own camera record. Camera values may be manual hypotheses; mark them uncalibrated. Store image dimensions, uncropped/cropped status, pixel-to-original transform, image hash, visible profile annotations and occlusion/coverage. If fitting a camera, retain parameter bounds, initialization, loss terms, solver version and residuals. Do not use a hard-coded apparent width ratio as a measured 3D value.

```json
{
  "schema": "rainee-observation-v1",
  "observationId": "accepted-frame-0026",
  "imageSha256": null,
  "imageSizePixels": [1024, 1024],
  "sourceFrame": 26,
  "shapeStage": 26,
  "shapeRole": "accepted-inflation-endpoint",
  "camera": {
    "type": "perspective",
    "calibrated": false,
    "worldFromCamera": null,
    "intrinsicsPixels": null,
    "distortion": null
  },
  "poseRecipeId": null,
  "pixelFromOriginalPixel": null,
  "coverage": {"rear": "partial", "lowerContour": "clipped", "depth": "unobserved"},
  "reviewedProfiles": [],
  "status": "source-registration-pending"
}
```

The example records the known endpoint role while leaving registration and calibration unresolved. Pixel dimensions and coverage must be populated from the actual image record for any job. A moving camera after the endpoint must not imply a smaller rest shape. Later deflation or shortened stature is invalid shape evidence, even when a later image can still help review face, pose, appearance or camera.

## 7. Deterministic measurement jobs

Measurement jobs operate on verified geometry in canonical rest coordinates. A job key is a hash of source/decoded geometry hashes, annotation revision/hash, alignment recipe/hash, algorithm/version, numeric settings and requested quantities. Cache by this key. Do not key a receipt only by model filename.

Minimum jobs:

| Job | Inputs | Output and validity gate |
| --- | --- | --- |
| `asset-summary` | Verified imported scene | Full-asset bounds/counts; clearly includes accessories |
| `body-summary` | Reviewed body masks and alignment | Segmented body extents; missing regions and pose limits |
| `plane-section` | Exact triangles, rest transform, plane, region mask | Intersection segments, assembled loops, open chains, coverage |
| `regional-descriptors` | Reviewed rear/thigh masks | Extents, posterior projection and landmarks; region-specific scope |
| `closed-surface-volume` | Complete segmented surface | Volume only after closure, orientation and intersection gates |
| `compare-models` | Two valid independent measurement receipts | Comparable quantities, exclusions, residuals and unresolved fields |
| `growth-audit` | Baseline source and four-stage proposal | Per-frame actual geometry, constraints and validity results |

Triangle-plane sections must use one documented tolerance, deterministic coplanar-edge handling and stable edge/vertex identity. Sort assembled chains deterministically. Report loop count, endpoint gaps, unmatched nodes, coplanar ambiguity, touched ROI boundaries and excluded triangles. The result must distinguish an actual surface section from an image-profile fit or a synthetic ellipsoid.

**Circumference:** report the sum of segment lengths only for a validated, simple, closed loop with declared region and adequate coverage. Multiple closed loops remain separate quantities unless their meaning and combination are reviewed. A closed clothing loop is a clothing-surface circumference. A clipped ROI chain has no inferred circumference; return null and explain the missing boundary.

**Volume:** require a complete intended surface, no boundary or nonmanifold edges, consistent winding, valid finite triangles and an appropriate self-intersection check. Consistent edge orientation alone does not prove outward winding or a valid anatomical solid. Do not reverse concave triangles using a dot product from one arbitrary centre. If a synthetic cap is introduced, report a capped-proposal volume and cap provenance, rather than measured body volume. Never sum overlapping component volumes as if they were the union.

```json
{
  "schema": "rainee-measurement-receipt-v1",
  "jobId": "R05-rear-section-pending",
  "jobKeySha256": null,
  "modelId": "R05",
  "geometrySha256": null,
  "annotationId": "R05-regions-r1",
  "alignmentRecipeId": "R05-to-rainee-r1",
  "coordinateFrame": "canonical-rest",
  "region": "body.rear.left",
  "scope": "segmented-surface",
  "units": {"length": "H", "area": "H2", "volume": "H3", "Hp0H": null},
  "plane": {"normal": [0, 1, 0], "offsetH": 0.61},
  "coverage": "unreviewed",
  "closedLoops": null,
  "openChains": null,
  "circumferenceH": null,
  "volumeH3": null,
  "validity": {"closed": null, "windingConsistent": null, "outwardOrientation": null, "selfIntersectionFree": null},
  "status": "blocked-by-unreviewed-source-and-mask",
  "limitations": ["No anatomical quantity available before geometry and region review."]
}
```

Unknown results stay null. An estimated quantity must state its estimator, assumptions, residual/error measure and coverage; it must not replace an unavailable measured quantity in the same field.

## 8. Full-body Argon proposal contract

The selected standalone Argon v5 field and its four rear presets supply the current design direction. Record the exact implementation and preset hashes in a proposal. This authority defines the intended authored field; it does not by itself prove reference fit, biomechanics, or accepted anatomy.

Keep the order `0000 â†’ 0010 â†’ 0018 â†’ 0026`. Frames after 0026 use the endpoint shape unless the user explicitly authors another action. Interpolate rear controls between accepted stages; use shared independent thigh controls across the sequence. Contact and attachment controls are explicit parameters rather than accidental consequences of a whole-body scale.

The full-body adapter should expose:

```ts
interface FullBodyProposal {
  baselineGeometrySha256: Sha256;
  semanticAnnotationSha256: Sha256;
  restAlignmentRecipeSha256: Sha256;
  fieldImplementationSha256: Sha256;
  stagePresetSha256: Sha256;
  stageIds: [0, 10, 18, 26];
  sharedThighParameters: Record<string, number>;
  protectedRegions: string[];
  targetCanonicalStatureH: 1;
  endpointHoldFrame: 26;
  correspondenceArtifactId: string | null;
  transitionWeightArtifactId: string | null;
  status: 'draft' | 'reviewed' | 'accepted' | 'rejected';
}
```

A mesh-to-field adapter must specify how the source surface is mapped to the target Argon surface. Distinguish baseline identity correction from growth. Suitable implementation options include a reviewed deformation cage, landmark-constrained warp, or a retopologized surface correspondence. They are alternative implementations to evaluate, not already installed capabilities. An implicit union can construct a connected regional surface, but it cannot automatically establish a seamless correct full-body correspondence.

Protect head, torso, arms, knees, calves and feet from rear-growth scaling unless the user intentionally edits those regions. Track normalized stature from the fixed body anchor, not the changing proposal's largest bounds. Shared thigh edits may change thigh mass, but must not be misreported as rear inflation. Mark hair, tail, clothing and props as separate deformation consumers.

Attachment transitions need reviewed masks and smooth weights. External pelvic connection repair must close the intended structural error without copying source defects or treating an unseen internal shape as known. Store the repair as a derived proposal with source-region, replaced-face, seam and topology evidence.

Each evaluated growth frame must report actual protected-region displacement, canonical height drift, rear descriptors, thigh parameters, closure when applicable, degeneracy and sampled Jacobian validity. Use identical integration/discretization settings for the accepted deformation and its derivative screening. Discrete Jacobian samples do not prove global injectivity, collision-free motion or physical realism. Any failed sample rejects that candidate evaluation and retains the prior valid proposal.

## 9. Cross-model report

Comparisons require separately verified readers, semantic coverage and alignments for both models. A report must say which quantities are comparable and which are unresolved. Examples:

- Whole-asset bounds can be compared as asset bounds, with accessory differences stated.
- Rear width in H is comparable only after stature alignment and equivalent reviewed region definitions.
- Rear width in Hp0 is comparable only after equivalent reviewed baseline landmark definitions.
- A pose-dependent kneeling silhouette cannot be compared directly with standing rest height.
- Vertex-to-vertex deltas require established correspondence; equal array length alone is insufficient.
- Closest-surface residuals require sampling, visibility and semantic restrictions, and do not prove identity.

Use separate R05 and R06 columns, alignment residuals and per-quantity status. Do not publish one averaged body that hides conflicting evidence. Preserve candidate alternatives when depth, attachments or camera remain underconstrained.

## 10. Jobs, performance and numerical precision

Run heavy readers and measurement jobs outside the UI thread. Use a bounded local queue with job IDs, progress stages, cancellation and error receipts. Cancellation must stop or discard the candidate result without modifying the selected project. Commit completed artifacts atomically only after validation.

Load one full-resolution model or needed component set at a time. Cache verified decoded buffers and deterministic job results with a measured memory budget. Cache entries include decoder/reader versions and source hashes. Do not reuse results after annotation, transform, field implementation or numeric settings change.

Use LOD exclusively for display unless the user requests an explicitly approximate analysis. Measurement jobs use the registered full geometry. A display simplification must have a different artifact ID, declared method and error report. A screenshot is not a measurement receipt. Use float64 for transform accumulation, section assembly and numerical reductions when practical; retain source precision in the authoritative buffers.

For the GitHub transfer, enforce the requested **100,000,000-byte ZIP archive limit** and check GitHub's separate per-file limit. The unpacked repository and expanded mesh exports may exceed 100 MB; report those quantities separately. Include the app, readers/recipes, relevant images, registry, telemetry and compact geometry artifacts. Omit duplicate formats and heavy textures before sacrificing essential geometry or authority images. Compression must be reversible for geometry described as lossless. Keep full originals in the local resolver. Report actual ZIP bytes, uncompressed snapshot bytes, largest file and decoded geometry fidelity.

## 11. Program and adapter interfaces

These commands are proposed interfaces, not commands verified to exist:

```text
python tools/model_bridge.py register --model-id R05 --source <local-file>
python tools/model_bridge.py inspect --model-id R05 --scope full-asset
python tools/model_bridge.py annotate --model-id R05 --annotation <reviewed-json>
python tools/model_bridge.py align --model-id R05 --recipe <alignment-json>
python tools/model_bridge.py measure --job <measurement-job-json>
python tools/model_bridge.py compare --left R05 --right R06 --recipe <comparison-json>
python tools/model_bridge.py propose --source <model-id> --recipe <shape-json>
python tools/model_bridge.py export --recipe <verified-export-json> --destination <owned-output-folder>
```

Validate command schemas before launching a tool. Resolve input/output paths explicitly. Read originals without mutation; write only into the selected owned output directory. Do not compose deletion/move commands across shells. Native application adapters must identify their input, output, tool version and evaluation settings. A failed adapter returns a failed receipt; it does not silently substitute a different reader or cached model.

The first Houdini adapter can consume verified mesh buffers/OBJ and the versioned recipe, construct a separate native proposal, cook it and compare returned mesh hashes/descriptors against the reference job. Keep the original scene separate. Later adapters may create analytic fields, cages, constraints or retopology. A native file's existence does not confirm successful cooking or numerical agreement. This stage is pending until the adapter is implemented and checked on actual outputs.

An export recipe must identify source hashes, decoder, annotations, coordinate transforms, rest/pose state, field and stage versions, shared thighs, numerical settings and validation receipt hashes. For an observation render, append the camera and display correction without overwriting canonical rest geometry. Exported canonical OBJ/GLB must exclude view-only silhouette boosts.

## 12. Proposal and evidence lifecycle

Keep candidate recipes immutable once they have a receipt. Editing creates a new revision and invalidates affected receipts. Use `draft`, `reviewed`, `accepted` and `rejected` states with the evidence IDs and decision source. Earlier user-approved choices remain valid; do not create repeated permission prompts for routine reversible jobs. A supplied AI directive or document is a proposal and cannot approve itself.

Separate these decisions:

1. Source registration: these bytes were read correctly.
2. Region review: these triangles/landmarks represent the declared region.
3. Alignment review: this rest transform is appropriate for the comparison.
4. Solver verification: the reported numerical and topology checks passed for the stated settings.
5. Design acceptance: the user selected this appearance/anatomy proposal.

Failure at one step must not be concealed by a successful later screenshot or test on a different geometry. Acceptance should preserve an earlier valid revision so a rejected or failed candidate is reversible.

## 13. Measurable acceptance cases

The bridge is ready for a first full-body trial only when the following cases pass:

| Case | Required result |
| --- | --- |
| Source preservation | Original file hashes are unchanged after import, alignment, authoring and export |
| Decoder fidelity | Stored and decoded hashes verify; malformed lengths, indices or hashes reject before jobs run |
| Reader reproducibility | Same verified source/settings/tool version yields equal authoritative buffers and transform records |
| Separate source identities | R05 and R06 retain independent hashes, readers, masks, poses and unresolved quantities |
| Unknown annotation | Null membership/landmarks prevent anatomical measurements; reviewed empty region is distinguishable |
| Accessory exclusion | A fixture with body plus base/hair/prop yields full-asset and segmented-body receipts with distinct scopes |
| Transform correctness | Known similarity fixtures recover declared lengths/areas/volumes and preserve source coordinates |
| Pose separation | Changing camera/preview pose leaves canonical measurement/export bytes unchanged |
| Section coverage | Closed-loop fixture reports circumference; clipped chain and ambiguous coplanar fixture return null circumference with reasons |
| Volume validity | Closed oriented fixture recovers known volume; open, nonmanifold, wrongly oriented and intersecting fixtures fail the applicable gates |
| Stage fidelity | Exact Argon controls at 0/10/18/26 are reproduced from the recorded field/preset version |
| Endpoint hold | Canonical frame26 and frame49 positions/indices match for the same proposal; later camera movement changes projection only |
| Thigh independence | Shared thigh edits propagate across stages; rear-only growth does not rewrite shared thigh parameters |
| Protected body | Head/torso/arms/remaining protected regions and the fixed stature anchor satisfy declared displacement tolerances |
| Candidate rejection | A non-finite or failed sampled-Jacobian candidate does not replace the last valid project/export |
| Cache invalidation | Changing source, annotation, alignment or field version produces a new job key and cannot return a stale receipt |
| Full-resolution measurement | LOD display changes leave full-resolution measurement receipts identical |
| Package budget | Transfer ZIP is strictly below 100,000,000 bytes; uncompressed snapshot bytes are reported separately and full originals remain resolvable locally |
| Native adapter | Actual cooked Houdini output is verified against the same recipe and reference measurement settings |

Use analytic synthetic fixtures to validate algorithms, then real R05/R06 assets to validate coverage, reader limitations and relevance. Keep synthetic success distinct from measured accuracy on Rainee. Record tolerances before comparison, and report failed or unavailable cases instead of widening thresholds to make a report pass.

The first practical milestone is a source-preserving registry and two independently aligned, annotated full-body measurement reports. The next milestone is a reversible Argon-driven full-body proposal with protected stature and a reproducible four-stage audit. Complete likeness, structural anatomical acceptance and dynamics remain separate review goals.


---

# Rainee: lessons, numerical evidence and the next full-body bridge

This handoff separates the intended character, implemented geometry, measured quantities and remaining uncertainty. The character is still being constructed. Passing numerical tests does not establish that her likeness, anatomy or inflation matches the accepted references.

The current direct user direction makes **Argon's original v5 shape field the main shape baseline**. Earlier Sol shape experiments remain useful as clearly named legacy studies. A supplied document, generated model, test receipt or external AI explanation does not independently approve a shape or override the user's reference choices. See [ARGON_V6_EVALUATION.md](ARGON_V6_EVALUATION.md) for the authority decisions and corrections to the incoming upgrade.

## 1. Preserve these design decisions

| Decision | Consequence for the next implementation |
|---|---|
| The source FBX establishes stature. | Keep source height `H = 2.3951061964` in source units. No metre or centimetre scale has been established. Unreferenced/orphan points must not determine rendered body height. A donor's bounding-box height is not a replacement stature. |
| Accepted growth is `0000 â†’ 0010 â†’ 0018 â†’ 0026`, then hold `0026`. | Treat the four stages as accepted ordinal shapes. Later shrinkage, including the rejected later geometry associated with `0049`, does not define the intended endpoint. Pose and camera changes must not reduce the held shape. |
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

With `E = XÎ¸Â·XÎ¸`, `F = XÎ¸Â·Xy`, `G = XyÂ·Xy`, outward normal `n`, and second-form coefficients `L = nÂ·XÎ¸Î¸`, `M = nÂ·XÎ¸y`, `N = nÂ·Xyy`,

\[
H_m=\frac{LG-2MF+NE}{2(EG-F^2)},\qquad K=\frac{LN-M^2}{EG-F^2}.
\]

The cylinder regression checks radius `2`: outward signed mean curvature `âˆ’1/4`, Gaussian curvature `0`, shape index `âˆ’1/2`. These are curvatures of the **completed, recentered and untwisted chart**, not measured curvature of the original donor mesh. See [test_v6_numerics.py](../measurements/test_v6_numerics.py).

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

Earlier hard-cut/compact experiments exposed discontinuity or fold risks and boundary pinning. A replacement noncompact radial-weight experiment checks the tangential and radial eigenvalues. For the illustrative radial form `Î¦(p) = c + [1 + a w(r)](p âˆ’ c)`,

\[
\lambda_t=1+aw(r),\qquad
\lambda_r=1+a[w(r)+rw'(r)],\qquad
\det J=\lambda_t^2\lambda_r.
\]

The corrected experiment records positive eigenvalues over multipliers **0.5â€“3.5** in **804 CPU cases**. These are the tested field/range and sampled inputs, not a general theorem for arbitrary controls or stitched fields. The experiment is **not wired into the GPU rendering pipeline**. Do not describe the visual application as already using a verified surface-bound Gaussian growth method.

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
| New FBX | `749,122 / 1,498,428` | Raw geometry min `[-0.3297770023, 0, -0.114812999964]`; max `[0.3211370111, 1.1872719526, 0.1518599987]` | Raw geometry coordinates. Model scale `[100,100,100]` and tiny X rotation about `âˆ’4.3257eâˆ’6Â°` are listed, **not applied** to these bounds. |

The files differ in counts and raw bounds. Do not assume vertex correspondence, identical world transforms or compatible physical units. The supplied figure image is a cropped character reference with costume, hair/tail and other shape cues; the dataset does not establish a new full-body stature anchor merely because it is a new model.

For comparison, the retained R01â€“R04 primary geometry inventories contain `405,713 / 751,140`, `343,386 / 640,530`, `452,290 / 840,980`, and `634,793 / 1,174,958` vertices/triangles respectively. Their stands, hair, garments and carried props belong to whole-asset extents. More triangles or a closed index graph does not make a donor more anatomically correct. Compare artist-approved body regions after pose, axis and scale review.

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

The useful next outcome is a full-body bridge whose source authority, geometry, camera assumptions and failure cases can all be inspected. The open issues are likeness, anatomical region acceptance, pose/camera registration, pelvic/thigh continuity and continuous deformation validityâ€”not the existence of additional scientific-sounding labels.

## Critical coordinate discovery from the delivered buffers

The C00 working body and N-prefixed native caches inherit normalized source-proxy coordinates. Their referenced Y extent is approximately **0.998830**, not 2.395106 source units. The app adapts their referenced foot/top range into exact canonical H=1, then uses the original 2.395106 stature and source origin for export. **Do not divide these already normalized buffers by 2.395 again.** The registry and `body-coordinate-adapters.json` provide explicit row-major source-to-canonical matrices.

R05 uses its raw OBJ coordinates. R06 uses raw FBX node-local coordinates with model scale100 listed but unapplied. R01â€“R04 use previously extracted GLB scene-world coordinates. D-prefixed older entries span their whole generated assets but are **vertex-cluster inspection proxies**; their original large GLBs/OBJs remain local. These different frames/representations must not be merged by filename or identical Y extents.

The legacy `source_dimensions_cm` metadata label is incorrect: its values are uncalibrated source-unit extents. The original dense FBX has 15,853,005 vertices, 17,673,962 polygons and 31,691,060 fan triangles in a 719,296,320-byte file; its T00 transfer proxy is 98,078 vertices / 220,971 triangles. This is a documented source approximation, distinct from the complete geometry of the two newest donors.

