RAINEE VOLUME LAB — current v4 and optional native rounded-pole study

OPEN
Double-click Start-Rainee-Houdini.cmd to open Rainee-Volume-Lab-v4.hip in
Houdini 22. Select /obj/RAINEE/CONTROLS. Rear volume and thigh fullness are
independent; thigh fullness 0 preserves the neutral thigh design.

For the browser, run "python serve.py" from the parent rainee folder and open:
http://127.0.0.1:5197/houdini/authoring.html
The current default shows the accepted native growth sequence, using source
frames 0000, 0010, 0018, 0026 and holding the endpoint after 0026. Closed-cage
ratios 1, 1.5, 2, 2.5 are initialization controls, not measured image volumes.
Choose direct controls for continuous authored rear/thigh adjustments.
Cached native states and direct authored controls are separate modes.

SOURCE AND STATURE
C:/Users/User/Downloads/Core Body (Template Only).fbx remains unchanged.
Its height, 2.3951061964 source units, anchors Rainee. Her face follows the accepted frames and clearer torso images.
The incomplete ZBrush anatomy is refined using selected figurines/drawings;
the source groin gap is a defect, not a feature to preserve. Early Grok frames
guide inflation; the later shortened stature is excluded.

v4 uses the locally repaired surface: 121,901 points / 252,337 triangles.
OUT_NORMALIZED retains internal working coordinates. OUT_FBX_SOURCE_STATURE
removes orphan vertices, then uniformly restores the referenced surface to the
FBX height and origin. It has 113,383 referenced points; checked height is
2.3951060772 source units, within float32 precision of the original.
This source-coordinate height is not a verified real-world centimeter scale.

VOLUME AND VERIFICATION
Rear ratio measures one closed two-lobed control cage: 1,506 points / 3,008
triangles. It is a geometric control quantity, not anatomical tissue volume.
v4 passed eight static combinations: rear 1 / 1.5 / 2 / 2.5, each with thigh
fullness 0 / 0.65. See verification-v4.json for finite geometry, fixed stature,
protected regions and sampled deformation-field checks.

The optional rounded-pole study is separate:
../research/rear-rounding/native-study/Rainee-Optional-Radial-Rounding.hip
Its CONTROLS exposes rear ratio 1..2.5 and radial relaxation 0..0.65. It opens
at 1x. Native VFL compiled and passed four static states at relaxation 0.65:
1 / 1.5 / 2 / 2.5, using the repaired body. See that folder's
verification-native-flow.json, verification-source-stature.json and
preview-manifest.json. Its source-stature export branch uses the same visible
height correction. The saved study and kernels are self-contained locally.

Neither v4 nor the optional study has new dynamics or certified contact.
The earlier v1 Vellum frames 1..72 are separate historical evidence in
verification-native.json; they do not validate the revised anatomy or poles.
Collar/inherited topology still need cleanup. Artistic resemblance is a
separate review from static geometry checks.

MEASUREMENT WORKFLOW
Open ../measurements/inspection.html, or:
http://127.0.0.1:5197/measurements/inspection.html
The latest donor is ../measurements/reference-01a13749/.
Its local-shape-constraints.json contains provisional regional ROIs. Compare
selected rear/waist surface patches rather than transferring donor height.
The donor needs pose/landmark alignment before fitting or accepting a winner;
../measurements/reference-fit/reference-fit.json records that status.
Measurements guide editable anatomy; they do not reveal hidden physical tissue.

REBUILD v4
From this houdini folder, run in PowerShell:
& "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" upgrade_pelvis_v4.py
& "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" verify_v4.py
The optional study has its own README and build/export scripts. Historical HIPs
and original media are retained. No diffusion or cloud generation is involved.


FIGURINE PROJECTION TRIAL
Rainee-Figurine-Projection-Trial.hip is a separate reversible native v4
parameter trial driven by the new generated figurine local descriptors.
Volume 1.170726, lateral .939946, vertical .757714, projection 1.201770;
other rear controls retain defaults, thighs 0, secondary motion off.
Native network: 19 nodes, healthy, no errors, stature 2.395106 source units,
closed-cage ratio1.170725584 and sampled minimum determinant .8532665.
See verification-figurine-trial.json. The browser third method shows actual
native body-figurine-native.bin; Try provisional figurine fit selects it.
The fitting study and native body agree at original source points within
5.96e-8 normalized coordinates. Added repair points use different transfer
policies; their max difference.003824 is recorded. Frozen fit output remains
separate from the actual native cache.

This trial improves the internal descriptor objective by about 8 percent;
that is not an accuracy rating or accepted anatomical match. Turned waist,
bentleg and differing ROI definitions remain unresolved correspondence.
The trial does not replace Rainee baseline or determine her inflation curve.

Browser OBJ export now defaults to FBX source stature and origin. Optional
normalized H=1 export remains available. Both compact unused vertices.

ACCEPTED GROWTH AND FACE REFERENCES, OCTOBER 13 UPDATE
../research/rear-rounding/native-study/Rainee-Accepted-Growth-Sequence.hip
contains a monotone native HScript ramp at source 0/10/18/26, then a constant
endpoint hold. All 27 growth frames and hold samples 27/49/120 passed native
finite geometry, fixed stature, measured cage growth and 39,273-point field
audits. This is static shape timing, not an image-fitted curve or new dynamics.
The browser lazily loads native frame buffers and retains at most three frames.
Frame 0049 remains an error reference, never an inflation target.

../measurements/growth-review.html shows accepted images, generated 3D proxies
and face closeups. ../measurements/splats.html displays actual local anisotropic
Gaussians, one geometry at a time, with on-demand rendering and review box
selection. Gaussian centre statistics are not anatomical volume.
Face authority is recorded in ../measurements/face-identity-20261013/manifest.json.
The new reference hierarchy has not yet replaced the production head mesh.
