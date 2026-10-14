Optional native radial-relaxation study — Houdini 22.0.368

Open Rainee-Optional-Radial-Rounding.hip. CONTROLS has a volume control (1..2.5)
and roundness (0..0.65). Shape controls are fixed approved defaults, hidden to
avoid implying arbitrary combinations were audited. The scene opens at 1x.

This standalone folder contains frozen repaired-neutral geometry, rest cage,
the native VFL, calibration Python, kernel snapshots, and native geometry
caches. It does not modify the original FBX, repaired-source files or main HIP.
The build script reads the current repair manifest if explicitly rerun; the
saved HIP uses the frozen local source and kernels. Cached states are static.

verification-native-flow.json records the actual native results. Four states
(1,1.5,2,2.5) passed VFL compilation/cooks, finite positions, identity at 1x,
unchanged height and fixed regions, measured cage ratios, NumPy/native parity,
and native finite-difference field-Jacobian screens over every repaired-source
point in the rear ROI (39,273 points; epsilon 0.0001). 121,901 body points and
252,337 triangles retain the repaired body's point/material correspondence.

At 2.5x, minimum sampled native field Jacobian is 0.0462885, no sampled negative
Jacobians. Actual native cage ratio is 2.500000954. Worst body NumPy/native
position difference is under 0.000000615 normalized units. Body cooks measured
about 0.81..0.90 seconds with calibration; these are four static cook timings,
not a sustained interactive performance claim. No dynamics were run.

preview-manifest.json maps local binary body/cage states and triangle buffers.
Binary positions are little-endian float32 XYZ in normalized source units.
Triangle indices are little-endian uint32. The body is the locally repaired
source, so the vertex count differs from the older 98,078-point preview.

Limits: closed-cage ratio is not measured tissue volume. Sampled positive
Jacobians do not certify continuous-domain orientation, watertight character
topology, contact/self-intersection safety or physical anatomy. Source collar
and inherited topology still need cleanup. Visual resemblance to the Grok
reference is a separate artistic review. Roundness0..0.65 and intermediate
ratios are editable but only the four recorded states at default 0.65 were
fully audited. Keep the optional study label when exposing preview presets.

Source-stature export branch (verified separately):
  /obj/RAINEE_OPTIONAL_ROUNDING/OUT_FBX_SOURCE_STATURE
  verification-source-stature.json
  body-source-stature-1x.bgeo.sc / Rainee-source-stature-1x.obj
  body-source-stature-2.5x.bgeo.sc / Rainee-source-stature-2.5x.obj

The branch uses Clean SOP with only Remove Unused Points enabled, then a
uniform transform. It retains 252,337 triangles on 113,383 referenced points.
Scale 2.3979114179253354 corrects referenced normalized height 0.9988301396 to
original FBX coordinate height 2.3951061964. Actual native export height is
2.3951060772 at both tested states (float32 error −1.19e−7). The original source
origin is restored. This does not establish real-world centimeters.

Existing normalized flow outputs exactly matched the previously verified
binary caches in both export checks. Original cache hashes, VFL, input wiring,
roundness and baseline state were preserved. Export branch display is off;
OUT_BODY remains the normalized authoring output. Raw source-stature exports
have compacted point order: use source-stature-triangles.bin, not the normalized
body-triangles.bin. preview-manifest.json identifies both schemas.

To rebuild the complete standalone study, run build_verify_native.py first,
then add_source_stature_export.py with Houdini 22 hython. No production files
are changed by either script. Only baseline and 2.5 source-stature exports were
checked; normalized static states remain 1,1.5,2,2.5.
