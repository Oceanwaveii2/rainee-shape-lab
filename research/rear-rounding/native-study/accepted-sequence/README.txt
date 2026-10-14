Rainee accepted-growth sequence — static native timing initialization

Open the sibling Rainee-Accepted-Growth-Sequence.hip in Houdini22.0.368.
All dependencies remain in the same native-study folder as the original
Rainee-Optional-Radial-Rounding.hip. The original HIP was not overwritten.
The current live scene is this separate accepted-growth sequence.

The user's accepted progression is source frame0000 (baseline),0010,
0018,0026 (endpoint), at24fps. Stage1,2,3,4 are ordinal stages, not
physical volume multipliers. Geometry from later video frames, including
0049, is explicitly rejected as a shape target because it deflates.

This initial native study uses closed-cage controls1.0,1.5,2.0,2.5 at
Houdini frames1,11,19,27 respectively. Those ratios are authored
initialization settings, NOT measurements recovered from reference images.
They preserve the existing radial-rounding strength0.65 and shape controls.

The volume channel expression is:
1 + 0.5*clamp(($F-1)/10,0,1) + 0.5*clamp(($F-11)/8,0,1) + 0.5*clamp(($F-19)/8,0,1)

This is three native piecewise linear ramps with no interpolation overshoot.
It holds the frame0026 endpoint through the end of the144-frame study and
continues to hold if sampled later. There is no walking animation in this
study: it establishes shape retention independently of future pose work.

verification.json documents27 static native frames (source0..26) and late
hold samples27,49,120. All30 states passed finite geometry, fixed protected
regions, fixed source-stature height, monotone measured closed-cage volume,
and native finite-difference Jacobian screening at all39,273 repaired-source
rear ROI points. Minimum tested Jacobian0.0462884968; zero nonpositive
samples. Late hold body and cage arrays exactly equal frame0026.

Source-stature output height2.3951060772 source units versus original
FBX height2.3951061964 (float32 difference-1.19e-7). Real-world centimeters
are not established by the FBX metadata. Normalized modeling coordinates
are retained internally. No entire-body shortening is used for inflation.

preview-manifest.json indexes exact native body-frame_XXXX.bin and
cage-frame_XXXX.bin little-endian float32 XYZ arrays.27 body+cage pairs total
39,983,868 bytes. All body caches have121,901 points and252,337 triangles;
cage caches have1,506 points and3,008 triangles. Sibling body-triangles.bin
and cage-triangles.bin are shared unchanged. Later frames reuse0026.
The browser should load frames on demand and retain at most3 pairs.

verify_export.py opens the saved HIP read-only, samples static native SOP
outputs, and writes browser buffers/reports. It does not build or modify
nodes, parameters, wiring, or layouts. HIP mutation was done using dedicated
Houdini MCP expression/frame-range/save tools. Measured native geometry
audit/export duration45.667seconds; process startup/load is additional.

Limits: this is not an image-fitted volume calibration, camera/pose solve,
Vellum simulation, production topology repair, continuous-domain Jacobian
proof, or contact/self-intersection certification. The timing/hold behavior
is implemented; matching reference silhouettes still requires fitting.

A pre-sequence snapshot of the previous live Figurine-Projection-Trial
scene is kept here. It had no unsaved changes. That snapshot's $HIP-relative
dependencies belong to the original rainee/houdini folder, so use the
unchanged original Rainee-Figurine-Projection-Trial.hip to reopen it normally.
