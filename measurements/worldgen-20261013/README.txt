WorldGen reference archive inspection — 2026-10-13

Original nine ZIPs in C:/Users/User/Downloads were read only. No .blend files
were opened, executed or extracted. Data asset extraction validated archive
paths, rejected symlinks/traversal, bounded entry size and validated ZIP CRC.
inventory.json records original archive hashes and extracted payload hashes.

Run:
python import_worldgen.py scan
python import_worldgen.py analyze
python test_importer.py
For an explicitly selected future ZIP, pass --archive filename.zip (repeatable)
and optionally --downloads C:/path. Default scan reads exactly the nine supplied
archives. It does not enumerate unrelated ZIPs or execute scripts/documents.

Actual inventory
9 archives total 368,126,219 bytes. Eight WorldGen packs contain SPZ Gaussian
appearance fields, environment collider GLBs and tiny camera.json transforms.
There are seven compressed SPZ file variants but SIX distinct raw datasets:
 - 6098… and its (1) copy contain byte-identical SPZ and collider assets, with
   different cameras / Blender scene files.
 - 0bf4… and 905f… have different gzip file hashes but identical decompressed
   SPZ attribute bytes and identical colliders; cameras differ.
canonical_raw_geometry_groups selects one representative per actual dataset.
Each record retains all source ZIP memberships and compressed variants.
Five datasets contain 1,179,648 splats; 83db5… contains 1,920,000 splats.
All observed files are SPZ version3, gzip, SHdegree0, fractionalbits12, flags0.
Six collider meshes have about57k–64k vertices; the last has137,592 vertices.
These are environment collider surfaces, not verified anatomical body meshes.

Renderer paths
Use canonical_raw_geometry_groups[*].canonical_path in inventory.json, relative
to this folder. Paths are URL-ready forward slashes. All original full_res.spz
attributes are preserved for the separate proper Gaussian renderer. Load one
canonical dataset at a time to conserve resources. Do not display the duplicate
0bf4/905 geometry as two growth states.

Camera/provenance limits
camera.json is only an orthonormal4x4 transform. Its c2w/w2c direction, lens,
image dimensions/intrinsics and target frame IDs are not declared. No ZIP path
or inspected JSON identifies0000/0010/0018/0026/0049, an input-image hash, elapsed
time or anatomical growth order. Do not infer sequence order from ZIP listing,
download suffix, GUID or apparent point count. Match independent provenance or
artist-confirmed views before relating these assets to the accepted frames.

Stats versus anatomy and render quality
splat-stats.json records decoded point-center bounds, opacity/log-scale
quantiles and opacity-threshold center bounds. A deterministic160k-point limit
produces derived center-preview buffers for cheap geometric inspection only.
This is not Gaussian covariance/opacity compositing and does not prove visual
fidelity. Opacity is appearance density, not tissue occupancy or body volume.
Neither splat-center extrema nor a sum of Gaussian scales yields an anatomical
measurement. The broad83db5 scene spans roughly22–26 sourceunits; scene bounds
cannot be treated as body stature. No unit conversion is invented.

The f9f63233… ZIP is separate OBJ geometry:249,768vertices,500,000triangles,
20connectedcomponents. Orthographic inspection shows a cropped cat-eared
upper-body bust with hair and torso; there are no thighs, butt or full legs.
derived/obj-f9f63233/inventory.json and orthographic-inventory.png make this
reviewable. shaded_00.png is a UVtexture atlas, not a scene render. This asset
can refine head/upper-body design but cannot measure lower-body growth.

SPZ parser references checked against primary sources:
https://github.com/nianticlabs/spz
https://github.com/nianticlabs/spz/blob/main/src/cc/load-spz.cc
https://github.com/nianticlabs/spz/blob/main/src/cc/splat-utils.h
This local importer decodes legacy1–3 position/color/opacity/scale attributes
for statistics; complete rotation-aware Gaussian rendering is separate. It
recognizes v4 headers but delegates its ZSTD streams to a compatible renderer.
