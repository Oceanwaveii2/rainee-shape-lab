# Argon v5 consolidation and reviewed v6 tools

The upgrade adds useful authoring and measurement experiments. It does **not** yet solve Rainee's reference likeness, establish a nine-donor anatomical model, or implement the complete reconstruction methods named in the supplied handoff. This assessment compares actual code and test outputs with the proposals; the original proposal documents remain available with that distinction.

## Design authority and consolidation

The user explicitly selected **Argon curvilinear v5** as the main shape direction. The exact supplied field and marching-tetrahedra extractor now live in `houdini/lab/argon-curvilinear-v5.mjs`. All four original presets, including shelf/overhang/contact terms, reproduce the supplied source's canonical positions, normals and indices byte for byte at resolution 24; 320 field samples also match exactly. `argon-source-fixtures.json` records the original source fingerprint and independent outputs.

The consolidated Argon studio retains its original layout and diagnostic shading while sharing geometry, project state, stage interpolation, thigh controls, canonical exports and background growth audit with the measurement lab. New projects default to Argon v5. Older recipes preserve their prior engine; an explicit stage-preset action converts them while preserving stature, thigh settings and reference views. The native full-body growth editor remains available as a comparison.

The v6 numerical tools support investigation alongside that direction. Distinguishing experimental research from implemented behavior does not reduce Argon's design authority. The remaining engineering target is a reference-fitted whole character with approved attachments and motion.

## What the code demonstrates

| Area | Implemented and checked | What remains unresolved |
| --- | --- | --- |
| Curvilinear growth | Adjustable lobe offset, Hermite lateral mapping, shelf/tuck terms and RK4 relaxation. The default 2.5x cage case has sampled minimum determinant approximately 0.2202. | Cage volume is not tissue volume. Sampled positive determinants do not certify global injectivity, self-contact, or visual accuracy. The offset is an editable hypothesis. |
| Regional implicit proposal | A second localized blending/bulge field and closed extracted meshes. Each selected engine uses its own shared extractor consistently for rendering, export and 27-frame audits. Argon v5 is now the new-project default. | The field does not compute the gradient-angle contact mechanism of the complete Implicit Skinning method. It is an artist proposal, not a rigged contact solver. |
| Pelvic radial chart | Manually specified bounding-box fractions, yaw and torsion produce a radial grid. Observed and completed cells are distinguished. Curvature uses the completed chart's fundamental forms. | Props, clothing, pose and hidden surfaces require reviewed segmentation and landmarks. Curvature of a completed/recentered chart is not directly measured anatomical curvature. |
| Rational splines | Clamped cubic rational scalar-grid fitting and Python/JavaScript evaluator agreement, including explicit knot vectors. | Two independent rear charts do not impose shared seam positions/tangents. No Class-A, G2/G3, closed-volume or six-patch surface certificate is established. |
| Morphable model | A batch SVD/PCA helper stores input grids and recomputes a basis when a donor is added. | No aligned nine-model dataset or browser-trained basis is delivered. The browser's hand-authored beta coefficients are not learned principal components. Training-set projection error is not held-out accuracy. |
| Gaussian tools | An opacity-crossing helper and first-order covariance transport. A corrected optional noncompact radial map has positive analytic Jacobian eigenvalues over its supported growth interval; 804 CPU cases check derivatives. | Input splats must already be evaluated along one ray. This is not GOF reconstruction, 2DGS training, SuGaR optimization or a mesh-bound Frosting layer. The new shader remains unwired and GPU-unverified. |
| Display tools | Normal-stripe and three-band toon shaders, approximate section-envelope curvature combs, and an optional view-dependent silhouette adjustment. | These are visual diagnostics. Display boosts stay separate from canonical coordinates and measurements; no Pixar/ArcSys pipeline replication is claimed. |

## Defects corrected during integration

The supplied lab used an undefined `settings.distance` during camera setup. Its new engine selection was absent from saved project state, while the audit worker still checked the older extractor. Both are corrected, including backwards-compatible imports and rollback after a failed engine switch. Display boosts now persist per reference view.

The authoring startup requested a render before its scheduling variable was initialized. This is fixed. Both apps preserve the original triangle indices: orienting each face relative to one chosen centre is a heuristic that can misclassify concave surfaces, rather than a verified winding repair.

The supplied curvature computation returned zero curvature for a circular cylinder. The corrected chart implementation recovers the cylinder's nonzero principal curvature. Missing bins remain explicitly marked unobserved. GLB loading now respects scene instances and world transforms, transforms normals correctly and handles reflected winding.

The supplied JavaScript spline basis did not match Python's clamped knots. It now agrees on endpoints and nonuniform knots. Opacity accumulation now returns `null` when the requested crossing is never reached, rather than inventing a surface at the last splat.

The original proposed Gaussian expansion has a negative radial derivative near `q = 1.5 / 0.85` at growth 3.5, and a hard discontinuity at `q = 2.25`. The optional replacement uses `w(q) = 1/sqrt(1+q)`, with eigenvalues `1+(g-1)/sqrt(1+q)` and `1+(g-1)/(1+q)^1.5`. It is noncompact and is not automatically applied to a scene. The existing guarded compact experiment retains its 2.25 limit.

## Which approach is most useful next

The strongest next step is a **hybrid of reviewed profile curves, local surface patches and implicit attachment geometry**. Use several local charts to preserve shelves, clefts and underside folds; a single maximum-radius cylindrical chart cannot represent every overhang or multiple intersections along a ray. Keep the FBX stature anchor and separate pose, rest shape, camera and display adjustment.

First annotate a small number of consistent front, side and rear profiles and anatomical landmarks on the accepted stages. Register each donor's selected body region without props, and record uncertain correspondences. Compare legacy and experimental candidates at the same camera, pose and target constraints using rendered silhouettes and landmark/section residuals. Inspect held-out views before choosing a representation. Retain several depth hypotheses where the pictures are ambiguous.

Next fit a curve-controlled patch atlas with explicit seam constraints, using implicit unions for connected pelvic and thigh attachments. Test seam position/tangent residuals, selected-region coverage, self-intersection and resolution convergence separately. Train any PCA prior only after matching anatomical coordinates; report held-out donors, missing-data masks and sensitivity to landmark choices. Secondary motion and contact come after approved rest geometry.

Gaussian reconstruction is valuable as an appearance and surface-evidence experiment when capture cameras and images are consistent. Generated turntables with changing anatomy should not be treated as a rigid scan. Trial an official GOF/SuGaR/Frosting pipeline on one consistent sequence before committing resources to the whole collection. No such training job was launched by this integration.

## Primary research checked

Pixar's [Character Articulation through Profile Curves](https://research.pixar.com/docs/2022.SiggraphPapers.GSF.pdf) describes a profile-curve articulation system. Our small angle-dependent display offset is only a local experiment inspired by the idea.

[Implicit Skinning](https://rodolphe-vaillant.fr/images/projects/implicit_skinning/implicit_skinning.pdf) combines implicit surfaces to correct skinned mesh vertices and model contact. A localized smooth union and bulge term is not that full method.

[GOF's official implementation](https://github.com/autonomousvision/gaussian-opacity-fields) reconstructs an opacity level set with geometry regularization and adaptive tetrahedral extraction. [SuGaR](https://github.com/Anttwo/SuGaR) optimizes surface alignment and mesh extraction. [Gaussian Frosting](https://github.com/Anttwo/Frosting) optimizes an adaptive layer around a base mesh. A centre statistic or `J covariance J^T` update alone does not implement these pipelines.

[NeuSOGA3D](https://arxiv.org/abs/2609.20323) is a September 2026 preprint; the supplied SIGGRAPH Asia 2024 attribution is incorrect. Its symbolic reconstruction/lofting proposal is relevant research, but the complete neural-symbolic system is not installed here.

## Verification and handoff

Run `python verify_v6_supercomputer.py --node <node-executable>` with NumPy, SciPy and Pillow installed. The runner decodes retained geometry in memory and records exact suite outcomes in [verification-v6-supercomputer.json](../verification-v6-supercomputer.json). These are targeted CPU checks, including 28 saved-state checks, 8 selected-engine checks, 8 Argon consolidation checks, exact source-parity fixtures, known-shape/camera tests and new numerical regressions. Historical full-scene Gaussian tests require the local originals and their runtime; the old root prototype also requires its omitted source proxy assets.

The actual browser smoke test is recorded separately. Passing these tests does not establish anatomical likeness or physical contact. The original accepted order remains **0000 -> 0010 -> 0018 -> 0026, then hold**, with independent shared thigh controls and fixed source stature.

The separate Antigravity handoff at `RedNote-Scraper-Engine` commit `8c10667` adds a 38,321-byte DOCX and a saved patch record; the parent introduces a research/prose graph. The inspected [provider router](https://github.com/Oceanwaveii2/RedNote-Scraper-Engine/blob/8c10667/engines/headless_research/scatter_pipeline_ext.py#L821) generates local template prose despite its provider labels; it does not demonstrate actual Grok/Gemini inference. Its spatial module indexes 2D graph cards, not anatomical geometry. DOCX generation does not establish routing, rendering or 3D accuracy. This is useful workflow context and a separate project. Future exchanges use files on disk or Git branches; no raw patch relay through chat is needed.
