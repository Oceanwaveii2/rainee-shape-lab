Rainee localized external pelvic repair
======================================

Default integration artifact: final-repair-manifest.json.
All paths in that manifest are relative to this directory. Raw sewn, Boolean,
and local-vdb-union studies are preserved for inspection. They are NOT the
default integration buffers; native Boolean did incidental cleanup outside
the local repair, so the final package restores distant source faces exactly.

Scope
-----
The source proxy has an incomplete rectangular anterior/perineal flap and
missing structural skin between the front pelvis, posterior/perineal region,
and upper inner thighs. The repair creates a continuous, gently rounded
external groin junction. It does not construct genital details, interior
anatomy, or a clinical anatomical model. The reference images guide shape;
the original mesh provides stature and distant identity, not authority for
its defects.

Construction
------------
1. A small saddle-shaped skin donor is sewn through four locally manifold
   source triangle seams to provide an actual connected structural seed.
2. Houdini VDB From Polygons rebuilds that seed at voxel size 0.0015 H.
3. VDB Smooth SDF applies five passes with a radius of five voxels. Half a
   voxel dilation provides an overlap collar.
4. A smaller ellipsoid cuts the defective source core away. A larger one
   clips the replacement skin. Native Boolean unions their overlap.
5. The final Python package retains native local triangles within a padded
   box and restores original oriented source triangles outside that box.
   Source vertex IDs are retained first; added skin receives a reusable bind.

Coordinates are Y-up, normalized by the original FBX coordinate height.
0.0015 H means 0.15% of height, not a real-world mm/cm calibration.
Padded composition box: X [-0.077, 0.077], Y [0.495, 0.665],
Z [-0.123, 0.113]. New rendered skin stays inside that box. The original
FBX, source positions.bin, source triangles.bin, and main .hip files were
not modified.

Verified final package
----------------------
121,901 points and 252,337 triangles; 98,078 original source points first.
180,520 original oriented triangles outside the composition box are retained
verbatim. Their coordinates do not move. Rendered surface height drift is
exactly zero relative to the source proxy.

The evaluated structural core contains 22,290 edges, all incident to exactly
two faces. The front, rear/perineal, and both inner-thigh attachment samples
belong to the body's main connected component. Baseline application is exact.
Four authored body states (baseline, 1.5x rear, 2x rear, and 2x rear plus thigh
adjustment) retain source coordinates/height and produce finite repair points,
with no zero-area triangles in the evaluated core.

Important limits
----------------
Whole-body topology remains flawed: 4,913 boundary edges and 26,797 edges
with more than two incident faces. These counts are NOT a watertight claim.
The source has many inherited failures and the overlap collar still needs
topology cleanup/detail transfer. The native carve and union warn about crossed
unshared source boundary edges. The evaluated inner structural core passes
manifold incidence tests; that does not establish a pressure-simulation-ready
whole character, collision robustness, or final artistic fidelity.

The original proxy had 61 isolated/unreferenced points. Point-bound height and
rendered-face height are therefore distinct. Both are preserved by the final
package, and the report records rendered height separately. Restoring source
points in the buffer is for binding/provenance, not a substitute for height
verification of the rendered faces.

Runtime use
-----------
apply_repair.py uses NumPy only, so it can be imported by Houdini hython.

    from apply_repair import apply
    repaired_positions, repaired_triangles = apply(source_positions)

Input must contain the original 98,078 points in original order. The result
retains those points verbatim and transfers their displacement to added skin
using an eight-neighbor bind. Source triangles are replaced by the manifest's
triangle topology. Extreme motion still needs renewed seam/collision tests.

Reproduction (all outputs stay in this directory)
------------------------------------------------
System Python with NumPy and SciPy:
    python pelvic_repair.py
Houdini 22 hython:
    hython native_export.py
    hython local_vdb_union.py
System Python:
    python package_local_repair.py
    python verify_final.py
Houdini 22 hython:
    hython bake_final.py

Source documentation used
-------------------------
https://www.sidefx.com/docs/houdini/nodes/sop/convertvdb.html
https://www.sidefx.com/docs/houdini/nodes/sop/vdbsmoothsdf.html
https://www.sidefx.com/docs/houdini/nodes/sop/boolean.html

Machine-readable evidence
-------------------------
implicit-repair-report.json: geometry/topology and native warning scope.
final-repair-verification.json: strict distant records, height, deformation,
and source/final buffer SHA-256 hashes.
local-vdb-native-report.json: actual native cooks and diagnostic messages.
