# Review handoff for Argon / Gemini 4

Please assess the current work critically. The creator is dissatisfied with the inflation likeness and wants better ways to construct and measure the intended hyper-stylized anatomy. Implementation is paused while the representation and fitting approach are reconsidered.

## Implemented and observed

| Area | Current evidence | Practical limit |
| --- | --- | --- |
| Working source | Repaired working body, 121,901 points / 252,337 triangles; 113,383 referenced points | Inherited surface/collar defects remain; no finished anatomy claim |
| Accepted native sequence | 27 source frames, endpoint reuse; native finite geometry and stature checks | Cage schedule is initialized, not silhouette-fitted |
| Regional anatomy | Editable distance-like implicit union, paired lobes, pelvic core and upper thighs | Regional proposal; not a full-body seamless replacement or exact Euclidean SDF |
| Measurements | Triangle-plane sections, selection bounds, guarded closed-volume calculation, unit adapter | Selected extents depend on ROI and can include unrelated surfaces |
| Camera/pose | Explicit projection controls; pose preview independent of canonical geometry | Manually declared hypotheses, not solved calibration |
| Donors | Manual similarity transform, reviewed-axis/landmark guard and source-space provenance | Similarity placement cannot undo different poses or establish anatomical correspondence |
| New data | Four complete primary geometry extracts, exact new reference PNGs, eight review videos | No new rig, semantic body segmentation, or cross-source camera calibration |
| Native regional sidecar | Saved HIP reloaded/cooked for two static imports at frames 1/12/144 | Recipe fields do not regenerate native geometry; JS re-extraction required |
| Gaussian experiment | Analytic compact field and first-order JΣJᵀ transport; CPU/source graph evidence | Full scenes local; GPU compilation/render not certified; support boundary fixed |

The browser was observed rendering the previous regional proposal and donor surfaces. Save/import and canonical camera/pose invariance were checked before anatomy implementation paused. Packaging verification now separately checks the lean server and new reference viewer. These evidence scopes must not be merged into a claim of accepted likeness or dynamics.

Useful existing reports:

- `houdini/lab/measurements/verification.json`: 11 synthetic measurement/projection checks.
- `houdini/lab/state-verification.json`: 28 state checks, including 27 discrete closed/ordered growth meshes, identical 26/49 regional exports and invalid import rejection.
- `houdini/lab/anatomy-model.verification.json`: geometry template cases and refinement comparisons.
- `houdini/lab/donors/verification.json`: affine transforms, inverse transforms and review guards.
- `houdini/lab/native-proposal/native-verification.json`: actual HIP reload/cook; source-height guide and imported surface checks.
- `research/rear-rounding/native-study/accepted-sequence/preview-manifest.json`: exact native sequence and control-volume provenance.

Reports prove their recorded cases. Integer-frame tests do not prove continuous topology, source correspondence, self-contact or physically stable motion.

## Questions the review should resolve

1. Is the current primitive template too restrictive to reproduce the upper dome, underside and thigh junction? Compare direct 3D curve constraints/lofts, a richer implicit surface and low-dimensional donor deformation.
2. Which reference views can be reconciled after camera and pose registration? Which contradictions are deliberate stylization or generative errors? Keep multiple depth candidates where the observations do not determine a unique shape.
3. How should full donor geometry be segmented into body regions while excluding hair, shoes, bases, cup and clothing? Current indexed components are often UV-seam patches, not anatomical parts.
4. How should we obtain consistent surface correspondence across independent Meshy builds? Do not subtract unrelated vertex arrays as if they shared topology.
5. Should the canonical body remain view-independent, with separate rendering corrections for conflicting stylistic views? If so, keep measurement volume and contact physics tied to the canonical body.
6. How should accepted growth be represented as authored rest shapes with an exact endpoint hold? Only then assess animation, collision, compression and contact.
7. What additional observations would most reduce uncertainty: calibrated side view, fixed-camera orthographic turntable, reviewed stature/body landmarks, body-only masks or cross-section guides?

Provide a concrete recommended representation and fitting objective, expected cost, unresolved assumptions, and one small discriminating experiment. Explain what each experiment can prove. Do not report a paper, proposed architecture, code import or UI screenshot as an implemented native solver.

## Research directions already examined

- [FiberMesh, SIGGRAPH 2007](https://www-ui.is.s.u-tokyo.ac.jp/~takeo/research/fibermesh/index.html): editable 3D curves constrain a smooth surface. Potentially useful for dome, underside, attachment and thigh-profile control.
- [Monster Mash, SIGGRAPH Asia 2020](https://dcgi.fel.cvut.cz/publications/2020/dvoroznak-tog-mm): sketch inflation and layered deformation for rapid organic shape/animation ideation. Single-view convenience does not establish correct hidden depth.
- [View-dependent geometry, SIGGRAPH 1999](https://doi.org/10.1145/311535.311612): shared-topology base with key-view corrections. Relevant when stylized views deliberately disagree; incompatible with interpreting every corrected view as one physical volume.
- [Large Steps in Inverse Rendering, SIGGRAPH Asia 2021](https://rgl.epfl.ch/publications/Nicolet2021Large): better-conditioned geometric optimization from images. It still needs suitable observations, objective and representation.
- [Implicit Skinning, SIGGRAPH 2013](https://rodolphe-vaillant.fr/entry/31/implicit-skinning-real-time-skin-deformation-with-contact-modeli/jumble): geometric contact and bulge handling as a skinning post-process; does not itself discover the character's desired rest shape.

These methods are research candidates. The current deterministic modules are not full implementations of these papers. Additional earlier research, including implicit surfaces, MASH, neural geometry and Gaussian methods, is retained under `research/` with its original status labels.
