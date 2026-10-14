Four accepted ordinal inflation references
========================================

Use integration-manifest.json to find reports, reader and lightweight geometry.
Accepted order is frame0000 baseline ->0010 ->0018 ->0026 correct endpoint.
Frame0049 is rejected later deflation/proportion drift. Hold0026 as the endpoint.
Stage1,2,3,4 are ordinal labels; this package assigns no physical volume4x.

Source inventory and provenance
-------------------------------
Five-Frame-3D-Handoff contains a separate OBJ/GLB and textures for every frame.
All GLBs declare pygltflib1.16.5/glTF2.0, one mesh, identity node transform,
no embedded camera, no animation and no skin. OBJ headers declare Blender4.4.0.
Those are serialization/export versions, not verified image-to-3D generator
identities. OBJ/GLB vertex and triangle counts differ; both are inventoried.
Actual GLB and OBJ coordinate bounds agree within1e-6, but that does not prove
vertex correspondence or anatomical fidelity.

The MTL files reference texture_0.png, which is absent. Supplied textures are
in model_textures, while GLBs contain embedded JPEG material images. Measurement
color candidates are sampled from the GLB's actual embedded base-color image.

The enhanced archive declares Qwen Image2.1 image regeneration at1024 followed
by RealESRGAN4x enhancement to4096. All ten supplied enhanced-image hashes match
its manifest. These are generative references, not unchanged original pixels.
The original560x560frames are named in LoadImage workflow metadata but are not
present in the supplied folders, so their pixels/hash and video timing are not
verified. Workflow JSON and README instructions were treated as data; none was
executed. The folder/frame names provide packaging association, not a verified
input-image hash link for the generated3D models.

Measurement scope
-----------------
Actual full GLB geometry is read one stage at a time. Node world transforms are
applied by the reusable reader. Raw-source axis hypotheses are X lateral,
Y up, Z front/depth. Local rear and waist windows are explicit in every report.
Warm skin and white garment color rules are only candidate filters; shadows,
arms, gold props and generated textures can contaminate them.

Descriptors use actual selected triangle areas, weighted centroid quantile
spans and exact surface covariance/PCA shape ratios. No full-asset bounding-box
height is used to normalize measurements. No foreign stature, anatomy, global
body proportions or tissue volume is transferred to Rainee. Inventory bounds
and preview cell size are technical data, not accepted height calibration.

Registration limit
------------------
The four accepted image stages do not automatically accept the models' hidden
surfaces or poses. There is no shared rig, morph mesh correspondence, camera
extrinsics, projection calibration or accepted pelvis registration. A default
front/back preview orientation alone proves neither a correct nor an incorrect
backside. Color/box ROI previews must be reviewed before fitting those shapes.

The current provisional regional measurements are nonmonotonic across stages,
including a decrease at0026. This demonstrates selector/pose/reconstruction
uncertainty; it is not an instruction to deflate the accepted endpoint or shrink
the canonical character. Accepted order comes from the user and remains fixed.

Reproduction
------------
Own Python3 code, with NumPy, SciPy and Pillow:
    python sequence_reader.py
    python measure_stages.py
    python finalize_sequence.py
    python verify_sequence.py

sequence_reader.py streams hashes and OBJ statistics and reads GLB accessors
without loading entire embedded image payloads. Measurement processes one
accepted stage at a time; embedded JPEG draft sampling limits texture RAM.
The clustered meshes are inspection proxies in original source coordinates,
not production retopology. The original source files and main HIP/UI are untouched.
