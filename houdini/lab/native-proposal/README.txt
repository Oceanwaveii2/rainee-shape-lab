RAINEE IMPLICIT ANATOMY LAB — STATIC NATIVE PROPOSAL

Open Rainee-Implicit-Anatomy-Lab.hip in Houdini 22.0.368. Keep this directory
beside the HIP: its File SOPs use $HIP/default.obj, $HIP/expanded.obj and
$HIP/source-height-guide.obj. No FBX import or source asset mutation is needed.

At /obj/REGIONAL_PROPOSAL_static_states, the Static mesh state dropdown
selects Default proposal or Expanded proposal. The named SOURCE_HEIGHT_GUIDE_FIXED
object shows the original FBX stature independently of regional mesh bounds.

These are imported draft-resolution-24 extracts from anatomy-model.mjs:
connected pelvic core, paired lobes, and independently authored upper-thigh
transitions. They are editable geometric proposals, not accepted anatomy,
image-fitted dimensions, a full body, or a seamless attachment to the FBX.
No native analytic/SDF SOP template, skeleton, physical/contact simulation,
or tissue-volume certification is supplied. No accepted-stage mapping is claimed.
The two extracts have different topology, so they are selectable static
states, not a directly interpolatable blend-shape pair.

Editable recipe JSON is on the main object's parameter interface. It records
the source API controls. Editing those fields DOES NOT regenerate geometry.
To change shape, edit the state recipe in export-proposal.mjs or extract from
the documented anatomy-model API, regenerate the OBJ, and reload its File SOP.
Regenerate the HIP to synchronize its recipe provenance with a new extract.

Source-coordinate conversion:
 P_source = P_canonical * 2.3951061964035034
            + [0,-1.220656394958496,0.028106868267059326]
Canonical H=1, +Y up, posterior -Z. Source units have no physical calibration;
the package does not assert centimetres. Guide height is not local-mesh height.

Verified results (native-verification.json):
 - Actual saved HIP reloaded and cooked in detached hython.
 - Default: 3,478 points, 6,952 triangles, volume 0.1062067629336846 source units^3.
 - Expanded: 3,710 points, 7,416 triangles, volume 0.219833061523257 source units^3.
 - Both states: one connected closed component; zero boundary, nonmanifold,
   inconsistent-winding or degenerate edges/triangles; finite unit normals.
 - Each state has identical geometry hashes at frames 1,12,144; no animation.
 - Source-height guide: exactly 2.3951061964035034 native units.
 - All SOPs cook with no errors/warnings.
 - Original FBX, source body/tris and anatomy-model source hashes unchanged.
 - All 13 existing HIP hashes unchanged. The live Houdini scene was not loaded,
   saved or controlled. No native viewport/render appearance claim is made.

Volume is the integral of the final connected union surface; overlapping
component volumes are not added. OBJ uses right-handed face winding; Houdini's
native OBJ importer reverses it for Houdini's left-handed polygon normals.
The report records both signed conventions and checks imported normals against
native primitive normals. Official convention documentation:
 https://www.sidefx.com/docs/houdini/model/primitive_spaces.html
OBJ format support:
 https://www.sidefx.com/docs/houdini/io/formats/geometry_formats.html

Reproduction from this directory (writes only this owned study directory):
 node export-proposal.mjs
 & "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" probe-native.py
 & "C:/Program Files/Side Effects Software/Houdini 22.0.368/bin/hython.exe" build-native.py
The Python scripts refuse an interactive Houdini process before clearing a scene.

manifest.json carries source hashes, model metadata, recipes and source-space
measurements; native-verification.json carries actual HIP/cook/topology checks.
The .bin files are source-space float32 positions/normals and uint32 triangles.
