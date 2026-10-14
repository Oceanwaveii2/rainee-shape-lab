# Canonical measurements and reference-fit groundwork

These modules measure explicitly selected geometry, project declared shapes through independent camera/pose hypotheses, and expose depth ambiguity. They do not recover unique anatomy from a drawing or automatically accept a generated mesh as Rainee.

Both modules are dependency-free ES modules usable in a browser or Node. Their functions perform no I/O. The verification scripts write only reports in this folder, preserving all input assets.

Run from the workspace root:

```powershell
node rainee/houdini/lab/measurements/verify-measurement-model.mjs
node rainee/houdini/lab/measurements/verify-current-body.mjs
```

`verification.json` contains 11 synthetic cases: known ellipsoid and paired-lobe dimensions/volumes, exact triangle-plane intersections, ROI clipping, withheld open/unverified volume, reviewed rotated ellipse fitting, framing invariance, perspective depth, pose isolation, and single-view ambiguity. Mesh volume differs from the analytic ellipsoid by about 0.1784% at the tested tessellation. `current-body-verification.json` reports the actual bounded native-source inspection separately. Synthetic success does not certify likeness or anatomical correctness.

## Coordinates, height and units

The public geometry contract is `{positions, triangles}`: flat XYZ floats and indexed triangles. Coordinates must already be **canonical, unposed, ground-normalized H=1**. X is lateral, Y is up, and posterior is −Z in the current Rainee convention. No mesh bounding box automatically becomes a body measurement.

For the reviewed native body snapshot, the parent supplied foot Y `0.00020352914` and top Y `0.99903368950`; their difference is `0.99883016036`. All three axes are divided by that difference and Y is shifted to ground zero. This corrects the slight working-coordinate stature mismatch without changing proportions.

```js
import {
  canonicalizeBodyCoordinates, createUnitContext, convertQuantity,
  DEFAULT_REAR_ROI, measureRearGeometry, crossSectionSegments,
} from '../measurement-model.mjs';

const canonical = canonicalizeBodyCoordinates(rawPositions, {
  footY: 0.00020352914, topY: 0.99903368950,
  heightSourceUnits: 2.3951061964035034,
  reviewedBodyBounds: true,
});
const geometry = {positions: canonical.positions, triangles};
const units = createUnitContext({heightSourceUnits: 2.3951061964035034});
const selected = measureRearGeometry(geometry, {
  roi: DEFAULT_REAR_ROI,
  sectionHeights: [.54, .58, .62, .66],
  unitContext: units,
});
const section = crossSectionSegments(geometry, {axis: 'y', value: .62}, {
  roi: DEFAULT_REAR_ROI,
});
```

`convertQuantity(value, units, {power, target})` converts H, H² or H³ with powers 1, 2 or 3. `target: 'source'` uses the fixed FBX stature anchor. Physical conversion is withheld until a physical stature and unit are explicitly reviewed. The current `2.3951061964035034` is in source units, not meters or centimeters. The native full-stature definition includes its original top/ear finish; donor hair, ears, heel geometry, pose and bases must not silently replace that definition.

## Selection and cross-sections

`DEFAULT_REAR_ROI` is an editable, provisional rectangular window: X ±0.22 H, Y 0.49…0.73 H, Z ≤0.015 H. Null limits are unbounded. Pass a different ROI explicitly when the selection changes. For a reviewed semantic face selection, pass only its triangles in the geometry object; spatial bounds alone cannot distinguish rear surface from an arm, clothing or unrelated fragment in the same window.

`measureRearGeometry` clips triangles to this window and returns `bounds`, `dimensions`, `sourceDimensions`, `selectedTriangles`, `clippedTriangles`, `boundaryContacts`, `boundaryLimited`, `sections` and `enclosedVolume`. `selectedHeight` is the selected window extent, never an automatically identified anatomical lobe height. Boundary contacts warn when a cut limits reported extents.

The current native snapshot yields selected width 0.406805 H, window height 0.24 H and depth span 0.153918 H, with cuts at the Y and Z boundaries. Central posterior sections are approximately 0.296…0.298 H wide. A sparse upper section at Y=0.70 spans approximately 0.397 H while lying near the Z front limit; this is a region-contamination cue for artist review, not evidence that the full rear lobe is that wide.

`crossSectionSegments` intersects triangle edges with a specified plane, interpolates actual intersection points, clips each segment to the ROI, removes duplicate segments, and cancels shared coplanar diagonals. It returns line segments and their extents. `closedLoopCandidate` is only an endpoint-degree diagnostic; it does not prove simplicity, enclosed area or anatomical circumference. The current source's clipped sections are open. No closing cap is invented.

## Volume gates and provenance

`inspectMeshTopology(geometry)` diagnoses indexed boundary edges, nonmanifold edges, triangle winding, degenerate triangles and connected face components. It does not weld coincident vertices automatically or check self-intersection.

`measureEnclosedVolume(geometry, {topology, provenance})` returns a quantity only when:

- Indexed topology is closed, nondegenerate, manifold and consistently oriented.
- `provenance.selfIntersectionStatus` is explicitly `reviewed-clear` or `known-analytic-simple`.
- `provenance.componentRelationship` is explicitly `single` or `disjoint`; `single` must agree with the indexed component count.

This provenance is a caller declaration, not a geometric certification produced by the function. Recompute topology whenever geometry changes; a cached diagnostic belongs only to its unchanged source. For disjoint components, absolute component volumes are summed to avoid cancellation from opposite global winding. Overlapping/contained components require a reviewed union or another appropriate volume model first.

An open ROI has no volume without a separately declared closing surface. `measureRearGeometry` withholds it when clipping occurs. Even a valid closed quantity is **authored enclosed geometry volume**, not tissue mass, anatomy ground truth, or volume inferred from Gaussian opacity. The authored growth control `2.5` remains a control value and is never converted to body volume here.

## Camera, pose and appearance separation

```js
import {
  createCamera, projectPoint, projectPoints, applyRigidPose,
  fitReviewedEllipseSilhouette, orthographicEllipsoidProfile,
  evaluateDepthCandidates, rankNextViews, observationParameterBlocks,
} from '../reference-fit-model.mjs';

const camera = createCamera({
  id: 'reviewed-side', type: 'orthographic',
  position: [1, .61, 0], target: [0, .61, 0],
  width: 1024, height: 1024, verticalSpan: .55,
  calibrated: false, // Manual camera hypothesis; not source-image calibration.
});
const projected = projectPoints(geometry.positions, camera, {
  pose: {rotationEuler: [0, .1, 0], pivot: [0, .61, 0]},
});
```

`createCamera` uses a right/up/forward basis and pixel origin at the top left. Perspective projection uses depth and FOV or explicit `{fx, fy, cx, cy}` intrinsics. Orthographic scale is pixels per canonical H. `projectPoint` distinguishes near-plane visibility from viewport inclusion. `applyRigidPose` supports XYZ Euler angles in radians (`Rz * Ry * Rx`) or a rigid row-major 3×3 rotation, plus pivot/translation. Nonrigid scale/reflection is rejected. Projection never mutates canonical coordinates.

`observationParameterBlocks` keeps identity, shape, pose, camera and appearance records separate. A torso arch is a nonrigid display deformation and must be labeled separately from the rigid candidate model. Lighting, glossy highlights and texture are not geometry measurements. Unknown imported cameras remain hypotheses; merely selecting a camera type does not calibrate them.

## Reviewed 2D profiles and depth alternatives

`fitReviewedEllipseSilhouette(points, {reviewed, coverage, camera, weights})` fits one explicitly selected, possibly rotated 2D ellipse. A profile is accepted as a reviewed 2D approximation only with `reviewed: true` and `coverage: 'full-contour'`. Partial or occluded outside curves remain diagnostic. Residuals describe the ellipse approximation; they are not probabilities.

A reviewed full profile and calibrated orthographic camera permit camera-plane spans (`rightSpan`, `upSpan`) in H. Assign them to anatomical axes only after orientation/pose review. Perspective pixel spans remain depth-dependent. No depth, circumference or volume is inferred from this fit alone.

`orthographicEllipsoidProfile(candidate, camera)` analytically projects an explicitly proposed ellipsoid's silhouette. Candidates declare `radii`, optional `center`, shape orientation, and optional rigid `pose`. This family is an artist assumption and can be replaced by a custom predictor; it is not a realistic-body prior or an automatically fitted character.

```js
const candidates = [.04, .08, .16].map(depth => ({
  id: `depth-${depth}`, center: [0, .61, 0], radii: [.08, .06, depth],
}));
const compatibility = evaluateDepthCandidates(candidates, reviewedObservations, {
  tolerancePixels: 2,
});
const suggestions = rankNextViews(candidates, proposedCameras);
```

`evaluateDepthCandidates` compares sampled contours using symmetric nearest-neighbor RMS pixel disagreement. Every observation must pass the declared tolerance; unreviewed contours or uncalibrated cameras cannot accept a candidate. One front view can support several depth choices with identical projected contours. Even a unique match in this finite family is not a unique unrestricted 3D reconstruction.

`rankNextViews` ranks camera hypotheses by candidate silhouette disagreement divided by viewport diagonal, requiring fully framed candidate contours. It returns no recommendation when no view separates candidates. Its suggestion requires a consistent growth state, useful framing and pose/occlusion review. It is a heuristic for selecting the next reference view, not guaranteed information gain.

## Resource and evidence limits

Measure bounded geometry on state changes; cache unchanged source topology rather than inspecting it each animation frame. Per-section triangle intersections are linear in the triangle count. The actual source inspection (121,901 vertices and 252,337 triangles, five sections) took about 425 ms in an isolated Node run and 1.16 s while other verification scripts ran concurrently; these are CPU inspection results, not browser frame-rate claims. Topology inspection uses an edge map and should be requested intentionally for large meshes.

The current-source verification script binds its reviewed height settings to exact buffer SHA-256 hashes and stops if that source changes. It does not calibrate future donor files. Generated models need explicit orientation, registration, body/prop separation, source-height definitions and face-region review before their descriptors become shape constraints.
