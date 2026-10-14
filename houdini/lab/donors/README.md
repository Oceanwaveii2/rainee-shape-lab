# Regional donor alignment workspace

Open `/houdini/lab/donor-workspace.html` through the existing local Rainee server.
An optional `?frame=26` opens the accepted endpoint. Only0000/0010/0018/0026
are selectable;0049 is rejected in the pure model API as well.

This tool implements reviewed **similarity/affine placement**, not paper-based
nonrigid anatomy transfer. The initial donor scale0.25 and rear-centroid placement
are unreviewed preview seeds. They do not normalize a cropped donor's height or
accept its proportions. The current source body is independently normalized by
its indexed Y stature and stays fixed at H=1; the viewer config retains its FBX
source stature/unknown physical unit and origin.

Use

1. Select an accepted donor and inspect source up/front axes. Mark axis review
   only after checking orientation.
2. Adjust donor-only scale/rotation/translation, or review the three semantic
   pairs. Initial centroid/direction markers are guides, not accepted landmarks.
   Pick corresponding surface points or enter coordinates; review every pair.
3. Align reviewed triad uses pelvis-to-waist distance for uniform scale, a
   right-handed frame for orientation, and pelvis anchor for translation. The
   lateral marker sets direction only; its distance residual remains visible.
   This transform cannot remove independent pose/articulation differences.
4. Compare side-by-side or overlay with linked inspection cameras. These are UI
   cameras, not verified source-image cameras. Focus a region and optionally
   isolate its triangles.
5. Select by an editable canonical box, or by the existing donor source-space
   ROI box. The latter is BOX ONLY: these preview buffers lack the full GLB's
   original triangle IDs and texture/color-role selection. The full-mesh report
   is linked separately. The same canonical box can clip away a donor's wider
   extent; expand it or compare source-ROI membership when appropriate.
6. Export a registration/provenance JSON. No original asset, source body, face,
   stature, production scene or native geometry is changed. Export contains the
   original GLB SHA256 inherited from the verified inventory and SHA256 hashes
   computed from the actually loaded proxy/source buffers.

Metric limits

- Selected true proxy triangle area and area-weighted5–95% centroid spans in
  aligned coordinates; topology/decimation, ROI clipping and pose affect them.
- Open patches are not enclosed tissue volume or waist circumference.
- Frame numbers are ordinal stage identity, not physical volume multipliers.
- Artist axis/landmark review does not confirm camera, nonrigid pose or full
  anatomical correspondence. Export records all three as unconfirmed.
- Face references are linked for artistic intent only, never automatically copied.

API: `../donor-registration-model.mjs`

`canonicalizeBody`, `canonicalROI`, `axisMatrix`, `registrationMatrix`,
`transformPoint`, `inversePoint`, `transformPositions`, `selectRegionFaces`,
`regionMetrics`, `alignReviewedTriad`, `registrationExport`, `frameGuard`.

Matrices are row-major storage applied to column vectors:

`pCanonical = translation + Rz * Ry * Rx * axisMap * scale * (pSource - pivot)`

Rendering uses local Three.js imports. It is on demand: interaction/resize/data
changes schedule a frame; no continuous animation loop runs while idle. Donor
buffers are fetched one stage at a time and prior GPU donor geometry is disposed.
Per-stage transform/landmark edits remain in session when switching donors.

Verification

`node rainee/houdini/lab/donors/tests/donor-registration.test.mjs`

Nineteen meaningful checks include known transform/inverse and signed-axis
fixtures, reviewed triad recovery, singular/nonfinite/invalid-index guards,
source-stature isolation, real four-stage proxy geometry and aligned ROIs,
weighted area/centroid correctness, excluded0049, and uncertainty/provenance
export semantics. Browser rendering/picking/export interaction is a separate
root verification step; no browser control was used by this implementer.
