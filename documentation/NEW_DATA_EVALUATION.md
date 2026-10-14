# New reference data evaluation — 2026-10-14

Argon's curvilinear v5 design now has the user's design authority. These observations support evaluating that design; they do not certify likeness, physical dynamics, or camera calibration. Preserve the original stature FBX anchor at **2.3951061964 source units**. Physical unit scale remains unknown. Keep complete local originals; use the lean package as a review derivative.

## New mesh audit

The new streamed OBJ audit reports **749,820 vertices**, **1,499,800 triangles**, **one indexed component**, and **zero indexed boundary edges**. Source bounds are min `[-0.29716, 0, -0.297678]`, max `[0.34235, 1.13697, 0.270847]`. The supplied ZIP is **57,964,555 bytes** and FBX is **121,170,476 bytes**.

These are uncalibrated donor bounds, not Rainee's stature or approved anatomical dimensions. One indexed component and zero indexed boundary edges do not establish correct winding, absence of self-intersections, anatomical continuity, or reliable enclosed volume. Register this donor using reviewed landmarks and regional correspondences before comparing its shape to the retained stature anchor.

The independently parsed FBX has **749,122 vertices and 1,498,428 triangular polygons**. Raw local extents are `[0.6509140134, 1.1872719526, 0.2666729987]`; its model lists scale `[100,100,100]` and a tiny X rotation. The inventory records these transforms without applying them. OBJ and FBX counts and raw bounds differ, so exact equivalence is not established.

The new inspection page retains a full-resolution uncropped JPEG reference, source hashes and numerical inventories. Its **5,070-vertex / 11,040-triangle** mesh uses averaged 32-cell vertex clustering and is explicitly a lossy visual derivative. All original donor assets remain local. Unlike the four previous primary GLBs, this extra mesh is not retained losslessly in the 100 MB review package.

## Eight videos: four candidate export families

All eight retained contact sheets were inspected. They depict a red-haired figurine wearing a green cap, striped top and denim. Their five sampled views strongly suggest four sequence families:

| Candidate family | Video IDs | Matching sampled sequence |
|---|---|---|
| A | V01 / V04 | Profile → rear → profile → front |
| B | V02 / V07 | Close rear → rear → profile → front |
| C | V03 / V08 | Rear close views → torso and face close views |
| D | V05 / V06 | Front → profile → rear → three-quarter → front |

The recorded source hashes are all different. Every video stream reports **193 frames, 24 fps, 8.041667 seconds**; audio can make the container duration slightly longer. The family assignments are visual findings from five samples, **not decoded pixel equality or verified full frame alignment**. Avoid weighting these as eight independent sequences until export provenance or frame comparisons establish their relationship.

Camera calibration and model associations remain unassigned in the retained metadata. Close framing, changing orientation and cropped views prevent treating apparent pixel-size changes as calibrated shape growth. The video character does not automatically become Rainee's face authority, nor does it establish a mapping to R01–R04.

## Regional reference cues

| Reference | Useful observable cues | Important limits |
|---|---|---|
| R01, BlondeFlowerFigurine | Broad rounded upper rear contour and waist-to-lobe transition in a rear three-quarter view | Lower body cropped; no stature constraint |
| R02, GoldCatFigurine | Front pelvic continuity, lateral hip/thigh envelope and taper toward knees | Front view does not determine posterior projection |
| R03, CatEaredFigurine | Expanded lateral hips/thighs and narrow waist with connected front structure | Cropped legs and absent profile restrict stature/depth inference |
| R04, FoxCupFigurine | Extreme paired rear lobes, central seam and compressed underfold against thighs | Seated/kneeling pose and base; no upright stature constraint |

The four older complete GLB bounds have Y extents near **1.90 source units**, despite different poses, crops and props. This is consistent with generator normalization. Full-asset bounds include hair, costume, bases and props and must not stand in for anatomical measurements. R03/R04 remain candidates for the previously mentioned larger builds; the exact pair was not explicitly assigned.

## Next measurement pass

1. Group candidate duplicate exports before setting fitting weights; verify corresponding source frames when feasible.
2. Mark waist, fold, pelvic midline, thigh stations and rigid base landmarks with confidence and visibility labels.
3. Fit camera and framing separately from shape. Do not infer growth from a zoom or renormalize kneeling bounds into upright stature.
4. Segment the pelvic region before extracting measurements. Compare paired-lobe width, posterior projection, upper-pole height, fold station and cleft depth using a reviewed pelvic landmark scale.
5. Keep thigh sections independent from rear growth, and preserve the stature anchor throughout deformation.

Pending work: donor association, camera/extrinsic calibration, anatomical ROI labels, landmark registration, mesh self-intersection/winding checks, and reference-fit validation. This pass made no new claim of measured tissue-volume ratios or physical inflation correctness.

Evidence: retained `measurements/canonical-20261014/videos.json`, all eight local contact sheets, `models.json`, and the four original reference images; original published snapshot `73fd9073c49bc9bb742bac8a919dd19c9572a3e5`. The new OBJ numbers above come from the separate streamed audit. No supplied scripts were executed for this visual evaluation.
