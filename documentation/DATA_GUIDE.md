# Geometry, image and telemetry guide

## Coordinate roles

Canonical working geometry is normalized to the referenced FBX stature, H=1, +Y up and posterior −Z. The source height is 2.3951061964035034 units and source origin is `[0, -1.220656394958496, 0.028106868267059326]`. Orphan vertices do not define stature. No physical metre/centimetre calibration has been supplied.

New R01–R04 geometry is in each GLB's original scene-world coordinates after node transforms are baked to float32. Do not equate its full scene Y range with body stature. Do not rescale the canonical character using donor hair, props or bases.

| ID | Primary build | Vertices | Triangles | Supplied role declaration |
| --- | --- | ---: | ---: | --- |
| R01 | BlondeFlowerFigurine | 405,713 | 751,140 | Rear three-quarter body flow and transition |
| R02 | GoldCatFigurine | 343,386 | 640,530 | Full-length front pelvic/leg structure |
| R03 | CatEaredFigurine | 452,290 | 840,980 | Face, bust, large hips and tall/leggy proportion cues |
| R04 | FoxCupFigurine | 634,793 | 1,174,958 | Extreme enlarged-rear variant |

These roles came from the supplied archive. They remain reference data, not automatic authority over direct user decisions. New source images are at `references/canonical/R01.png` through `R04.png` in the lean repository; their dimensions, original archive paths and hashes are recorded in `measurements/canonical-20261014/models.json` and `local-source-manifest.json`.

## What measurements mean

Each `derived/R*/measurements.json` records full-asset bounds, surface area, indexed topology, unclassified component bounds and 19 actual horizontal-plane intersections. These are source-coordinate geometric quantities. Hair, shoes, base, cup and clothing remain in the source scene. Semantic anatomical ROIs, true body stature, circumferences, camera correspondence and anatomical volume are unresolved.

Many indexed components are created by UV/material seams. Their presence is not by itself proof of a physical anatomical hole. No positional welding, manifold repair or self-intersection certification was applied to the new geometry. Enclosed anatomical volume is withheld.

The native cage ratio, regional template volume, projected image area, full-asset surface integral and Gaussian covariance describe different quantities. None can be silently substituted for tissue volume.

## Lossless storage

`data/asset-map.json` maps existing virtual URL paths to content-addressed `data/blobs/*.gz` files. It records compressed/decoded byte counts, SHA-256 hashes, codec, byte encoding and any sparse baseline.

- `gzip`: preserves the original binary payload.
- `shuffle32`: groups each of four byte positions for improved compression; the inverse restores every bit.
- `delta-zigzag-shuffle32`: encodes integer index differences reversibly before shuffling; no index order or connectivity is changed.
- `sparse-point-f32` / `RSP1`: stores changed vertex IDs and their complete XYZ bit patterns against a named baseline. Header `<4sII>` is magic `RSP1`, total vertices, changed vertices; followed by little-endian uint32 IDs, then 12 bytes per changed XYZ point.

`serve.py` restores these routes, validates both stored and decoded hashes and caches at most five decoded assets. All 27 native body cache frames are retained exactly. No approximate interpolation between four samples replaces them.

`tools/materialize_review_assets.py` expands assets or emits neutral geometry-only GLBs for DCC inspection. Original node metadata, primary GLB hashes, material IDs and component IDs remain in the telemetry even though texture/UV/normal payloads are omitted.

## Images and video

The new four source PNGs, accepted frames and identity closeups retain original dimensions and decoded pixels in lossless WebP viewing containers; original PNG containers remain local. Full-size JPEG derivatives of three older supplementary PNGs are identified under `references/secondary/`; original pixels and files remain in the local project.

V01–V08 are the new videos in the order supplied by the user. Their original names, SHA-256, sizes, ffprobe stream metadata, duration and source sampling times are in `videos.json`. The review clips retain full duration at 12fps and proportional width ≤480px, omit audio, and use H.264. This is a viewing derivative, not a calibrated turntable or motion reconstruction. Individual sample stills remain local; their five-sample inspection sheets are included here.

The exact two larger-build targets and video-to-model mapping remain unassigned. Filenames, similar appearance, predicted geometry and archive roles do not prove camera or anatomical correspondence.

## Complete new donor bridge

See `models/full-body-bridge/registry.json` and `tools/argon_model_bridge.py`. R05/R06 preserve decoded float64 positions and uint32 triangle indices exactly, including signed zeros and vertex/face ordering. The original 719 MB dense FBX remains local; its source proxy is explicitly lossy. Transfer budget applies to the ZIP, not expanded geometry. Source PNG hashes and lossless-pixel derivative hashes are distinct.
