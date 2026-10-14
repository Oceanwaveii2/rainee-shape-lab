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
| `canonical-rest` | Rainee rest coordinates, H = 1, +Y up, posterior −Z | Chosen stature source and accepted alignment |
| `posed-preview` | Pose applied for inspection or reprojection | Pose recipe; excluded from rest measurements |
| `observation-camera` | Projection into one image | Image hash, camera hypothesis/calibration, framing |

The known source stature anchor remains `2.3951061964035034` source units. Its physical unit is unknown. Keep `physicalUnitCalibration: null` until a reviewed calibration exists. Do not renormalize every donor by its entire asset bounds, crop height, hair, ears, footwear, plinth or props.

For a uniform source-to-canonical scale `s`, lengths scale by `s`, areas by `s²`, and volumes by `s³`. Nonuniform scale is a shape proposal, not a unit conversion. Reflection and negative determinant transforms need an explicit derived winding policy and provenance; do not overwrite source indices.

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

Keep the order `0000 → 0010 → 0018 → 0026`. Frames after 0026 use the endpoint shape unless the user explicitly authors another action. Interpolate rear controls between accepted stages; use shared independent thigh controls across the sequence. Contact and attachment controls are explicit parameters rather than accidental consequences of a whole-body scale.

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
