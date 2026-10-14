# Rainee shape engineering — review handoff

Rainee is a tall, hyper-stylized adult character with a very large paired rear, an exaggerated spinal arch, and independently designed thighs. This repository contains the working local app, anatomy references, geometry and measurement telemetry for review by Argon / Gemini 4. **The intended anatomy and inflation likeness are still unfinished.** Passing numerical checks does not establish artistic accuracy.

For Argon’s entire-body processing pass, start with [START_HERE_ARGON.md](START_HERE_ARGON.md) and [the extensive full-body handoff](documentation/ARGON_FULL_BODY_HANDOFF.md). Complete geometry for both newest donors is now included with a verified Python decoder and OBJ exporter; the old inspection LOD remains a display derivative.

Start with [the design goals](documentation/GOALS.md), [current implementation and open problems](documentation/REVIEW_HANDOFF.md), and [the data guide](documentation/DATA_GUIDE.md). This branch consolidates **Argon curvilinear v5 as the user-selected design authority and default for new shape projects**. The original studio UI and measurement lab share the exact Argon field, four stage presets, recipes and canonical export path; older saved recipes retain their selected engine. Read [the evaluation and corrected claims](documentation/ARGON_V6_EVALUATION.md) before interpreting their results. Anatomy fitting remains unfinished.

## Run the review app

Python 3 is sufficient for the packaged app; no package installation, cloud service or diffusion model is required.

```powershell
python serve.py --port 5197 --open
```

Use another port if 5197 is already serving the full local project. Open these pages:

- [Argon v5 consolidated shape studio](houdini/argon-v5-studio.html)
- [New donor, full-source telemetry and lean inspection geometry](measurements/new-donor-20261014/review.html)
- [New anatomy references, full geometry and eight videos](measurements/canonical-20261014/review.html)
- [Anatomy and measurement lab](houdini/lab/index.html)
- [Working character and accepted growth sequence](houdini/authoring.html)
- [Donor registration workspace](houdini/lab/donor-workspace.html)
- [Accepted growth and face references](measurements/growth-review.html)
- [Editable image contour review](measurements/five-frame-20261013/profile-fit-candidate/review.html)

These are relative page paths to open through the Python server. Static file hosting alone cannot restore the compressed virtual geometry routes. GitHub hosts the review source/data; this project has not been deployed as a public website.

## What is retained in the lean version

The four new primary GLBs contribute **1,836,182 vertices and 3,407,608 triangles**. Every world-space float32 position and triangle index extracted from those primary files is retained. There is no decimation of these four builds. Textures, UVs, original normals and duplicate OBJ/STL exports are omitted; the viewer computes neutral surface normals.

The core reference images, accepted frames and face closeups retain their original dimensions and decoded RGBA pixels through lossless WebP containers; original PNG files stay local. Three older supplementary images and the new fox donor image use full-size uncropped JPEG derivatives. The newly supplied fox donor has a clearly labeled lossy inspection mesh (5,070 vertices / 11,040 triangles); complete decoded OBJ/FBX geometry is now included separately under `models/full-body-bridge/`, while original file containers and textures remain local. The four earlier primary GLBs remain losslessly retained. The eight new videos have full-duration, uncropped proportional review copies at 12 fps, with audio omitted, plus timed inspection sheets. Exact originals remain local.

Binary coordinates and indices are stored with lossless gzip, reversible byte shuffling, index deltas and sparse native-frame updates. `serve.py` restores the original binary bytes at the existing app URLs and checks SHA-256. See [the codec and measurements](documentation/DATA_GUIDE.md) and [package verification](documentation/package-verification.json).

## Access actual geometry files

```powershell
python tools/materialize_review_assets.py --out ..\Rainee-expanded-review --geometry-glb
```

This expands the earlier retained assets and writes four neutral geometry-only GLBs outside the repository. Export the complete newest models with `python tools/argon_model_bridge.py export --id R05-new-obj --out expanded/R05.obj` (or `R06-new-fbx`). It does not restore omitted textures or invent missing surfaces. The expanded folder exceeds the lean transfer budget and stays local.

For Sol on the original computer, [LOCAL_DATA.md](documentation/LOCAL_DATA.md) and [local-data-map.json](documentation/local-data-map.json) locate the complete working data, original reference archive, FBX and videos.

## Main limitations

The FBX stature is **2.3951061964035034 source units**, with physical centimetres/metres unknown. Donor scene bounds include hair, clothing, shoes, bases and props. They are not body height or anatomical circumference. Cameras, poses, anatomical regions and correspondence between generated meshes still require review.

Accepted inflation order is **0000 → 0010 → 0018 → 0026, then hold 0026**. Later shrinkage and stature drift are rejected. Stage numbers are ordinal; current native cage ratios 1 / 1.5 / 2 / 2.5 are initial sculpt controls, not image-measured tissue volumes.

The regional implicit template is a connected, closed artist proposal. It is not a fitted whole body, a seamless FBX replacement, a native analytic Houdini SOP, or validated contact physics. The Gaussian experiment is source code and CPU evidence here; full Gaussian scenes remain local and GPU behavior was not certified.

Third-party runtime licenses are retained under `vendor/package/LICENSE` and `vendor/spark/LICENSE`. Reference imagery and generated assets remain separately identified by provenance; dependency licenses do not confer ownership of those assets.
