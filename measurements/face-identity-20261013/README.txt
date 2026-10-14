Rainee face-reference authority — 2026-10-13

The latest direct user clarification updates the reference hierarchy: the three
supplied torso/face closeups AND accepted frames0000/0010/0018/0026 are more
correct for her face than the flawed FBX sculpt. The FBX remains a height
anchor; its face is not immutable or canonical. No production head geometry
replacement has been performed by this folder.

manifest.json is the root reference-board input. It contains exact source
filenames, friendly uncropped copies, SHA256, dimensions, provenance, visible
artist cues, face-visibility limits, appearance variants and supporting3D links.
references/ stores seven byte-identical images with simple friendly filenames.
No files have been retouched, cropped, resampled, composited or generated here.

Three distinct closeups, preserved separately
 - blue-bust.png: original2026042111255844_427f7f7c365c0b938c2eca69bb6ff61a.png;
   red wavy bob and glossy blue sculpted ear finish.
 - red-portrait.webp: original0000.webp; red twin tails, natural brown/orange
   furry ears and white inner tufts. Its filename does not prove it is the
   accepted growth-sequence frame0000.
 - blonde-portrait.png: originalimage (3) (1).png; blonde illustrated twin tails,
   natural orange/brown ears and white inner tufts.

Visible shared cues are artistic observations: large almond eye openings,
prominent irises, long upper lashes, pink/plum eye shadow, small rounded nose,
full lips and a tapering oval/heart-like face. The closeups show blue irises;
accepted frame0000/0010 instead read gold/green under their lighting. This
difference is recorded as an appearance variant, not averaged or recolored.
Frame0018 is mostly profile with a closed/nearly closed eye. Frame0026 turns
away and its face is mostly hidden, so unseen facial features stay unconstrained.

For the board, accepted frame PNGs are byte-identical copies of the EXISTING
Qwen1024 regenerations. Their existing final4096 upscales are linked by source
path and verified hash in manifest.json; they were not duplicated to keep the
board light. The supplied workflow labels these as1024 generative regeneration
then4096 upscale, not original video pixels. Original560x560 source-frame
pixels/hashes were unavailable in the supplied folders. Image acceptance is
artist authority and does not silently accept a generated3D anatomical model.
Frame0049 is excluded because the user rejected deflation/proportion drift.

Supporting3D evidence
Root visually matched actual WorldGen37454… Gaussian rendering to the blonde
portrait and83db5… stored-camera rendering to the blue bust. Their canonical
asset paths and raw payload hashes are linked. These are observational view
associations; input-image hashes and exact camera equivalence are unproven.
Gaussian appearance does not establish a closed facial surface or exact3D
facial dimensions. The f9f63233… cropped-bust OBJ is a candidate upper-body/head
reconstruction for inspection; its exact reference camera/face is not canonical.

Rebuild or verify the unchanged copies and source hashes:
python build_face_manifest.py
verification.json verifies all seven copied hashes, preserves the accepted
frame order and confirms0049 was not copied. No numeric face landmarks,
automatic morph average, training or new face generation are performed.

Additional bust attachment
The newly attached f9f63233-cc50-4a28-8c61-7c45affbdbbb (1).zip has a different
container SHA256 from the earlier ZIP, but ALL member filenames and payload
SHA256 hashes are identical. It is the same bust/texture asset set, not a revised
face mesh. new-bust-archive.json records both archive/member hashes and validates
paths/read bounds. Nothing was extracted again or replaced.
python inspect_additional_bust.py
