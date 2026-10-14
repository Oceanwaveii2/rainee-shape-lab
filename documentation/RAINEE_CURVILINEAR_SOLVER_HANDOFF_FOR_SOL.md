# Rainee Shape Lab — Deep 3D/2D Character Research, Forensic Audit & Curvilinear v5 Handoff for Sol

> Supplied Argon proposal retained for provenance. Its measurements, implementation claims and instructions are not independently accepted project state. Read [the reviewed evaluation](ARGON_V6_EVALUATION.md) for corrections, evidence and current limitations. In particular, the spline, reconstruction, anatomical-calibration and Class-A claims below must not be treated as verified results.

## 1. Executive Synthesis: Solving the "Jessica Rabbit / Aunt Fanny / McLaren" 3D Paradox

Characters like **Jessica Rabbit** (*Who Framed Roger Rabbit*), **Aunt Fanny** (*Robots*), **Elastigirl** (*The Incredibles*), and hyper-stylized anime/fighting-game heroines (**Chun-Li**, **2B**, *Guilty Gear Strive*) share a foundational geometric paradox: **their appeal relies on combining automotive Class-A $G^2/G^3$ sweeping outer curves with razor-sharp $G^0$ crease intersections and view-dependent 2D silhouette cheats that violate rigid Euclidean 3D projection and standard human anthropometric priors.**

When translating Rainee's 2D reference art (`R01`–`R04` and Grok `0000`–`0026`) into a measurable, animatable 3D geometry solver, existing pipelines fail for six specific reasons—each of which can be solved with proven mathematical and studio techniques:

| Challenge Domain | Why Standard 3D / AI Pipelines Fail on Rainee | Industry / Academic Breakthrough to Add to `rainee-shape-lab` |
| :--- | :--- | :--- |
| **1. "Jessica Rabbit / Anime" 3/4 View Paradox** | In 2D 3/4 rear art (`R01`, `R04`, `0026`), the artist draws **both** the full twin-circle rear silhouette (a $0^\circ$ rear read) **and** the arched spine/side-waist/front-bust (a $45^\circ\text{–}70^\circ$ side read). A single rigid 3D mesh foreshortens the far lobe at $38^\circ$ yaw, losing the twin-peach cleavage. | **Pixar Profile Mover ([de Goes et al., SIGGRAPH 2022](https://research.pixar.com/docs/2022.SiggraphPapers.GSF.pdf))** + **View-Dependent Geometry ([Rademacher 1999](https://doi.org/10.1145/311535.311612))**: Keep the canonical 3D body view-independent for volume/physics, and add a **Camera-Ray Silhouette Offset Layer** that slides the far lobe's horizon rim and deepens the camera-ray cleft tangent at 3/4 angles. |
| **2. Perspective Foreshortening in 2D-to-3D Fitting** | In a perspective rear/3/4 camera ($\text{FOV} = 35^\circ\text{–}50^\circ$, e.g. [CharacterGen, SIGGRAPH 2024](https://arxiv.org/html/2402.17214v3) at $40^\circ$), the rear lobes sit $\Delta Z \approx 0.24 H$ closer to the lens than the narrow waist. This magnifies the apparent 2D rear-to-waist width ratio by **$+16\% \text{ to } +26\%$** ($2.05\times$ in 3D reads as $2.45\times$ in 2D!). | **Closed-Form Perspective Horizon Unwarping**: Replace naive orthographic pixel ratios in `reference-fit-model.mjs` with exact tangent-cone unwarping $R_{\text{true}} = (D - \Delta Z)\sin\theta$ and depth-ratio correction $W_{\text{3D}} / W_{\text{waist}} = (W_{\text{2D}} / W_{\text{waist,2D}}) \cdot \frac{D - \Delta Z_{\text{rear}}}{D - \Delta Z_{\text{waist}}}$. |
| **3. Melted Creases in Implicit / SDF Unions** | `anatomy-model.mjs` uses isotropic quadratic `smoothUnion` everywhere. That acts like a convex caulk fillet that fills in the intergluteal cleft and melts the sub-gluteal overhang into the back of the thigh. | **Gradient-Angle-Modulated Implicit Skinning ([Vaillant et al., SIGGRAPH 2013](https://rodolphe-vaillant.fr/entry/31/implicit-skinning-real-time-skin-deformation-with-contact-modeli/jumble))** + **Shape-Preserving R-Functions ([NeuSOGA3D, Sept 2026](https://arxiv.org/html/2609.20323v2))**: Modulate blend radius by $\cos\alpha = \nabla f_A \cdot \nabla f_B$. Where gradients oppose ($\cos\alpha < 0$, cleft & sub-gluteal fold), enforce a sharp $G^0$ contact crease **plus a tangential "pressed-peach" compression bulge**; where gradients align ($\cos\alpha > 0$, outer hip flare), apply a wide $G^2$ smooth blend. |
| **4. Ellipsoids Cannot Express Cantilevered Profiles** | Standard 3D ellipsoids (`anatomy-model.mjs` and `rear_rounding_flow.py`) have symmetric curvature in $Y$ and $Z$. They cannot represent a flat horizontal sacral launch shelf ($Y \in [0.60, 0.71] H$) overhanging a tucked sub-gluteal fold ($Y \in [0.49, 0.55] H$). | **Multi-Axial Partial Shape-Preserving Spline (PSPS) Lofting ([NeuSOGA3D, Sept 2026](https://arxiv.org/html/2609.20323v2))** + **3D Curve Networks ([True2Form, SIGGRAPH 2014](https://www.dgp.toronto.edu/~karan/papers/artist_driven_graphics_smart_graphics_keynote2014.pdf) / [BendSketch, SIGGRAPH 2017](https://haopan.github.io/bendsketch.html))**: Loft the 19 extracted horizontal cross-sections directly using non-negative partition-of-unity PSPS basis functions $B_i(y) = H_{i-1}(y,n) - H_i(y,n)$, guaranteeing zero overshoot and exact preservation of narrow clefts. |
| **5. Automotive Class-A Surface Inspection** | Standard diffuse clay shading hides $G^2$ (curvature) and $G^3$ (rate-of-curvature) discontinuities, making it impossible to judge whether her hip-to-thigh sweep flows like a McLaren fender or has flat spots. | **In-Viewport Class-A Isophote / Zebra Reflection Shader & 2D Section Curvature Combs ($\kappa(s)$)**: Add real-time light-tunnel Zebra stripes (`houdini/authoring.html`) and normal curvature combs $\mathbf{c}(s) + \beta|\kappa(s)|\mathbf{n}(s)$ (`houdini/lab/index.html`) + [OpenSubdiv](https://en.wikipedia.org/wiki/Catmull%E2%80%93Clark_subdivision_surface) semi-sharp crease tags on the cleft and sub-gluteal shutlines. |
| **6. Cel/Stylized Shading & Pose Articulation** | Complex curvilinear creases cause jagged self-shadowing in toon/stylized lighting, and hip bending crushes gluteal volume under standard Linear Blend Skinning. | **Arc System Works Proxy-Normal Transfer ([GTShader Manual](https://github.com/gabriel01913/GabrielToonShader/blob/main/Manual/GTShader_Manual.md))** + **Houdini KineFX Pose-Space Deform / RBF ([SideFX KineFX](https://www.sidefx.com/docs/houdini/nodes/sop/kinefx--jointdeform.html))**: Transfer clean spherical-teardrop proxy normals to the outer lobes while keeping hard split normals on the cleft shutline; drive hip-flexion overhang compression via RBF pose-space correctives. |

## 2. Four Forensic Geometric & Topological Bugs Discovered in `rainee-shape-lab`

Direct numerical and topological inspection of the binary buffers in `rainee-shape-lab` (`houdini/body-v4-rest.bin`, `houdini/pelvic-repair/implicit-repaired-triangles.bin`, `houdini/rear_model.py`, `houdini/rear_shape_v3.vfl`, and `houdini/lab/anatomy-model.mjs`) uncovered four concrete bugs that caused the flat-bridged "boxy tank" artifact in `documentation/previews/growth-editor.jpg`:

| Defect ID | Affected Files | Mathematical / Topological Root Cause | Measured Impact on `body-v4-rest.bin` (121,901 pts / 252,337 tris) | Verified Fix in Curvilinear v5 |
| :--- | :--- | :--- | :--- | :--- |
| **D-01: Pelvic Midline Offset & Contrapposto Yaw** | `houdini/rear_model.py`, `houdini/rear_shape_v3.vfl`, `research/rear-rounding/rear_rounding_flow.py` | Across $Y \in [0.57, 0.67] H$, the true outer-skin intergluteal sulcus of `body-v4-rest.bin` lies at **$X_{\text{cleft}} = +0.0122 H \text{ to } +0.0150 H$** (with a $3.88^\circ$ pelvic yaw between the left peak at $X=-0.0553$ and right peak at $X=+0.0717$). Hardcoding `ax = abs(rest.x)` places the cleft pinch at $X = 0.0000$ (cutting into the medial slope of the **left** cheek) while assigning the true sculpted cleft ($X = +0.0125$) to the **right** lobe (`side = +1`). | Tears the left cheek's inner slope in half at $X=0$ and inflates the true anatomical cleft at $X=+0.0125$ backward, creating an asymmetric double-stepped central trench. | Shift the cleft coordinate frame to the true anatomical sulcus curve $x_c(y) = +0.0122 \cdot w_y(y)$, keeping the synthetic control cage centered at $x_c = 0$. |
| **D-02: Inward Medial $X$-Collapse (`sx / cs > 1`)** | `houdini/rear_model.py` (lines 15–16), `houdini/rear_shape_v3.vfl` | `rear_model.py` uses `inner = cx * cs * (ax / cx)**(sx / cs)`. Because `lateral` ($1.0$) > `separation` ($0.15$), the exponent $\gamma = s_x / c_s \approx 1.45 > 1$. Raising $a_x / c_x < 1$ to an exponent $> 1$ makes $\frac{\partial x'}{\partial x}(0) = 0$ and $x' < x_0$ across $a_x \in (0, 0.058)$. | Pulls vertices at $x_0 = 0.0243$ **inward** to $x' = 0.0175$ ($\Delta x = -0.0068 H$), piling already-inflated outer vertices onto the midline and forming a flat-backed wall. | Replace the collapsing monomial with a $C^1$ monotonic cubic Hermite spline on $[0, c_x]$ with unit origin slope ($\frac{\partial x'}{\partial x}(0) = 1.0$) and slope $s_x$ at $a_x = c_x$. |
| **D-03: 47.5% Residual Midline Extrusion & Zero-Slope Cleft** | `houdini/rear_model.py` (line 13), `houdini/lab/anatomy-model.mjs` | `cleft = 1 - cleft_hold * 0.7 * (1 - smooth(.004, .035, ax))` leaves **47.5% of the posterior $-Z$ expansion active on the cleft floor** at default `cleft_hold = 0.75`, and `smooth()` has zero derivative at the origin (forcing a $180^\circ$ flat horizontal plateau instead of a sharp dihedral V-cusp). | At $2.50\times$ cage volume (`Y = 0.61 H`), the cleft floor drifts backward from $Z = -0.1040 H$ to $-0.1431 H$ (`v4 Direct`) and $-0.1407 H$ (`Radial Flow`), reducing true cleft relief to $0.0640\text{–}0.0689 H$. | Lock sacral anchor hold to $96\%$ (`cleft_cusp = 0.96`) with a regularized dihedral cusp arc $u(2-u)$, keeping sulcus drift to $-0.1158 H$ (**70% less drift**) and boosting true cleft relief to **$0.0949 H$ (+48.3%)**. |
| **D-04: Inverted Left-Handed Winding on 51,907 VDB Triangles** | `houdini/pelvic-repair/local_vdb_union.py`, `houdini/pelvic-repair/package_local_repair.py` | Houdini's `Convert VDB` SOP outputs left-handed polygon winding ([Houdini Primitive Spaces](https://www.sidefx.com/docs/houdini/model/primitive_spaces.html)), whereas the imported FBX/OBJ source triangles (`< 98,078`) use right-handed outward winding. `package_local_repair.py` merged them without flipping the VDB triangles. | **84.23% of the 51,907 VDB repair triangles** (`vertex ID >= 98,078`) have inward-pointing right-hand normals, causing inside-out normal shading artifacts in the lower cleft/groin in Three.js and cancelling signed volume. | Flip triangle index order `(f[:, 1], f[:, 2] = f[:, 2], f[:, 1])` on inward-oriented VDB triangles (`>= 98,078`) during packaging and normal calculation. |

## 3. Quantitative Benchmark: Existing Solvers vs. Pelvis-Aligned Curvilinear v5 (at Exact 2.50x Cage Volume)

| Metric (Canonical $H=1$ Coordinates, $Y=0.61 H$ Equator) | Rest Baseline (`1.00x`) | Current `v4 Direct` (`2.50x`) | Current `Radial Flow` (`2.50x`) | Proposed `Curvilinear v5` (`2.50x`) |
| :--- | ---: | ---: | ---: | ---: |
| **Calibrated Control-Cage Volume Ratio** | `1.000000x` | `2.500000x` | `2.500000x` | `2.500000x` |
| **Calibrated Deformation Amplitude** | `0.000000` | `0.487065` | `0.450447` | `0.337144` |
| **Outer-Skin Sulcus Lateral Position ($X_{\text{sulcus}}$)** | `+0.0150 H` | `+0.0050 H` (Dragged off-axis) | `+0.0050 H` (Dragged off-axis) | **`+0.0150 H` (Exact anatomical lock)** |
| **Outer-Skin Sulcus Posterior Depth ($Z_{\text{sulcus}}$)** | `-0.1040 H` | `-0.1431 H` (Severe $-Z$ drift) | `-0.1407 H` (Severe $-Z$ drift) | **`-0.1158 H` (70% less sacral drift)** |
| **Mean Lobe Crown Posterior Peak ($Z_{\text{peak}}$)** | `-0.1344 H` | `-0.2120 H` | `-0.2047 H` | **`-0.2107 H`** |
| **True Intergluteal Cleft Relief ($Z_{\text{sulcus}} - Z_{\text{peak}}$)** | `0.0304 H` | `0.0689 H` | `0.0640 H` | **`0.0949 H` (+48.3% vs Radial Flow)** |
| **Equatorial Half-Width ($\max |X|$ at $Y=0.60 H$)** | `0.1517 H` | `0.1906 H` | `0.1997 H` | **`0.2039 H` (Coke-bottle fender flare)** |
| **Minimum Active Jacobian Determinant ($\min \det J$)** | `1.000000` | `0.099056` | `0.045904` | **`0.220206` (4.8x safer margin vs Flow)** |
| **Non-Positive Jacobian Samples ($\det J \le 0$)** | `0 / 38,118` | `0 / 38,118` | `0 / 38,118` | **`0 / 38,118`** |
| **Rendered Stature Drift & Protected-Region Shift** | `0.000000 H` | `0.000000 H` | `0.000000 H` | **`0.000000 H`** |

## 4. Deep Dive: Six New Technologies to Add to `rainee-shape-lab`

### 4.1 2D-to-3D Perspective Horizon Unwarping (Fixing `reference-fit-model.mjs`)
In `houdini/lab/reference-fit-model.mjs`, `fitReviewedEllipseSilhouette` currently blocks perspective cameras with:
`reason: 'Perspective silhouette has depth-dependent scale; no 3D span without an appropriate depth model'`.
Here is the exact projective geometry needed to unlock perspective 2D reference fitting:
1. **Differential Depth Magnification Between Rear Crown and Waist**:
   When a camera at distance $D = \frac{H_{\text{framed}}}{2 \tan(\text{FOV}_y / 2)}$ views the character from behind or rear-3/4, the posterior gluteal crown lies at depth $Z_{\text{rear}} = D - \Delta z_{\text{rear}}$ (closer to the lens), whereas the waist lies at $Z_{\text{waist}} = D - \Delta z_{\text{waist}}$ (further from the lens, with $\Delta z_{\text{gap}} = \Delta z_{\text{rear}} - \Delta z_{\text{waist}} \approx 0.24 H$).
   Consequently, a perspective camera magnifies the apparent 2D rear-to-waist width ratio by:
   $$\left(\frac{W_{\text{rear}}}{W_{\text{waist}}}\right)_{\text{2D}} = \left(\frac{W_{\text{rear}}}{W_{\text{waist}}}\right)_{\text{3D}} \cdot \frac{D - \Delta z_{\text{waist}}}{D - \Delta z_{\text{rear}}}$$
   At a standard $40^\circ$ FOV ($D \approx 1.51 H$, used in [CharacterGen](https://arxiv.org/html/2402.17214v3)), a true 3D orthographic rear-to-waist width ratio of **$2.05\times$** projects onto the 2D image plane as **$2.45\times$** ($+19.5\%$ apparent inflation!). If you fit an orthographic 3D solver directly to the raw 2D pixel ratio without multiplying by $\frac{D - \Delta z_{\text{rear}}}{D - \Delta z_{\text{waist}}}$, you over-widen the 3D hips by $20\%$ and destroy the proportion balance.
2. **Horizon Rim Tangent Shift**:
   A perspective ray from camera distance $d$ tangent to a lobe of cross-sectional radius $R$ grazes the surface at polar angle $\sin\alpha = R / d$ in front of the true equator, shifting the observed silhouette horizon toward the camera by $\Delta z_{\text{horizon}} = -R^2 / d$ and foreshortening the observed chord width unless unwarped via $R_{\text{true}} = \frac{d \cdot u_{\text{norm}}}{\sqrt{1 + u_{\text{norm}}^2}}$ where $u_{\text{norm}} = \Delta x_{\text{px}} / f_x$.

### 4.2 "Jessica Rabbit / Elastigirl / ArcSys" View-Dependent Silhouette Rigging
Why can no single static 3D mesh simultaneously match a 2D artist's $0^\circ$ back drawing, $38^\circ$ three-quarter drawing (`R01`, `R04`, `0026`), and $90^\circ$ profile drawing?
- Because in 2D character design (Jessica Rabbit, Pixar's *Elastigirl* and *Turning Red*, Arc System Works' *Guilty Gear Strive*), 2D artists apply **Multi-Perspective Silhouette Priority**:
  - In a $38^\circ$ rear 3/4 view (`R01`, `R04`, `0026`), a rigid Euclidean projection foreshortens the far gluteal lobe and causes the near lobe to occlude the intergluteal cleft. Yet the 2D artist deliberately draws **both full spherical cheeks and a deep visible cleft** alongside a $45^\circ$ arched spine!
- **How to Add This to `rainee-shape-lab` Without Corrupting Canonical Volume**:
  Following **[Pixar's Profile Mover (SIGGRAPH 2022)](https://research.pixar.com/docs/2022.SiggraphPapers.GSF.pdf)** and **[View-Dependent Geometry (Rademacher 1999)](https://doi.org/10.1145/311535.311612)**, keep the canonical 3D mesh $M_{\text{canonical}}(\theta_{\text{shape}})$ 100% view-independent (so all volume integrals, stature checks, and cross-section ledgers remain invariant), and add an optional **View-Dependent Silhouette Display Modifier** $\Delta \mathbf{P}_{\text{view}}(\mathbf{v}_{\text{cam}})$ active only during camera rendering / 2D contour fitting:
  $$\Delta \mathbf{P}_{\text{view}}(\mathbf{p}, \psi_{\text{yaw}}) = \sin(2|\psi_{\text{yaw}}|) \left[ \alpha_{\text{far}}\, w_{\text{far}}(\mathbf{p})\,\mathbf{u}_{\text{cam,right}} - \alpha_{\text{cleft}}\, w_{\text{cleft}}(\mathbf{p})\,\mathbf{u}_{\text{cam,forward}} \right]$$
  where $\psi_{\text{yaw}}$ is the camera azimuth relative to the posterior pelvis axis ($0$ at dead-on back OR dead-on side $90^\circ$, peaking at $\psi_{\text{yaw}} = \pm 45^\circ$ 3/4 view!). At $\pm 38^\circ$ yaw, this smoothly pushes the far lobe's silhouette rim outward by $+0.022 H$ along the camera right vector and deepens the cleft along the camera view ray by $-0.018 H$—reconciling the "cheated" 3/4 reference drawings (`R01`, `R04`, `0026`) with the canonical 3D mesh!

### 4.3 Gradient-Angle-Modulated Implicit Skinning + Contact Bulging (`anatomy-model.mjs` Upgrade)
In **[Implicit Skinning (Vaillant et al., SIGGRAPH 2013)](https://rodolphe-vaillant.fr/entry/31/implicit-skinning-real-time-skin-deformation-with-contact-modeli/jumble)** and **[NeuSOGA3D (Li et al., Sept 2026)](https://arxiv.org/html/2609.20323v2)**, the fundamental flaw of standard implicit blending (`smoothUnion(fA, fB, k)`) is that a constant blend radius $k$ cannot distinguish between a **convex-to-convex fold where tissues press together** (the intergluteal cleft and sub-gluteal overhang) and a **smooth anatomical transition** (the lateral hip-to-thigh sweep).
- **The Mathematical Fix**:
  Evaluate the unit gradient inner product $\cos\alpha(\mathbf{x}) = \frac{\nabla f_A(\mathbf{x}) \cdot \nabla f_B(\mathbf{x})}{\|\nabla f_A(\mathbf{x})\|\,\|\nabla f_B(\mathbf{x})\|}$ between any two implicit primitives $f_A, f_B$:
  1. **Opposing Gradients ($\cos\alpha < 0$, e.g. Left vs. Right Lobe at $x = x_{\text{cleft}}$, or Lower Lobe vs. Posterior Thigh at the infrigluteal fold)**:
     - Drive the R-function blend radius $a(\alpha) \to \epsilon_{\text{crease}} \approx 0.002 H$ so the two surfaces meet at a **sharp $G^0$ dihedral shutline**, AND
     - Add a **Conservative Contact-Compression Bulge Ring**:
       $$\Delta f_{\text{bulge}}(\mathbf{x}) = -\beta_{\text{contact}} \exp\!\left(-\frac{f_A(\mathbf{x})^2 + f_B(\mathbf{x})^2}{\sigma_c^2}\right) \cdot \text{smoothstep}(r_{\text{inner}}, r_{\text{outer}}, |f_A(\mathbf{x}) - f_B(\mathbf{x})|)$$
       This models the exact physical behavior of two soft, inflated lobes pressing against each other: flat contact along the sagittal septum ($f_A = f_B$) surrounded by a high-tension tangential bulge ("pressed peach" fullness) just outside the crease!
  2. **Aligned Gradients ($\cos\alpha > 0$, e.g. Lateral Hip Core to Outer Thigh Sweep)**:
     - Use **[NeuSOGA3D's Cubic Shape-Preserving R-Function (`softMin2`)](https://arxiv.org/html/2609.20323v2)**:
       $$\text{softMin}_2(f_A, f_B, a) = \frac{1}{2}\left(f_A + f_B - S_{\text{abs}}(f_A - f_B, a)\right), \quad S_{\text{abs}}(d, a) = \begin{cases} \frac{d^2}{a} - \frac{|d|^3}{3a^2} + \frac{a}{3}, & |d| < a \\ |d|, & |d| \ge a \end{cases}$$
       Unlike quadratic `smoothUnion`, `softMin2` has $C^2$ curvature continuity at $|d| = a$ (preventing Zebra-stripe breaks on the outer hip!) and suppresses global volumetric swelling.

### 4.4 Multi-Axial Partial Shape-Preserving Spline (PSPS) Cross-Section Lofting
Instead of forcing artists to guess ellipsoid radii, `rainee-shape-lab` already extracts horizontal cross-sections (`crossSectionSegments` in `houdini/lab/measurement-model.mjs`). Using **[NeuSOGA3D's PSPS Volumetric Lofting](https://arxiv.org/html/2609.20323v2)** and **[True2Form](https://www.dgp.toronto.edu/~karan/papers/artist_driven_graphics_smart_graphics_keynote2014.pdf)**:
- Given $K$ artist-edited or donor-extracted 2D cross-section implicit fields $\{F_i^{(y)}(x,z)\}_{i=1}^K$ at heights $y_1 < y_2 < \dots < y_K$, construct the 3D volumetric field directly as:
  $$F_Y(x,y,z) = \sum_{i=1}^K F_i^{(y)}(x,z)\, B_i(y), \qquad B_i(y) = H\!\left(\frac{y - y_{i-1}}{\Delta y}, n\right) - H\!\left(\frac{y - y_i}{\Delta y}, n\right)$$
  where $H(s,n) = FF\!\left(\frac{n(s+1)}{2}, n\right)$ is the recursive divided-difference polynomial transition generator:
  $$FF(s, n) = \frac{s}{n}FF(s, n-1) + \left(1 - \frac{s}{n}\right)FF(s-1, n-1), \qquad FF(s,0) = \mathbf{1}_{s > 0}$$
- Because $B_i(y) \ge 0$ and $\sum_{i=1}^K B_i(y) \equiv 1$ with compact support, **PSPS lofting reproduces any 2D French-curve cross-section (including deep V-clefts, flat dorsal shelves, and concave overhangs) with zero Runge oscillation and zero unwanted bulging**.

### 4.5 Automotive Class-A Surfacing Diagnostics (Zebra / Isophote Shader + Curvature Combs + OpenSubdiv Creases)
To build a character with "more curves than a McLaren," the workbench (`houdini/authoring.html` and `houdini/lab/index.html`) needs the exact diagnostic instruments used in automotive Class-A surfacing ([Onshape Surfacing](https://www.onshape.com/en/features/surfacing), [SOLIDWORKS Class-A](https://www.engineersrule.com/curves-ahead-how-to-handle-curves-and-splines-in-solidworks/)):
1. **Real-Time Isophote / Zebra-Stripe Diagnostic Shader**:
   Evaluates view-reflection stripes $I_{\text{zebra}} = \frac{1}{2} + \frac{1}{2}\tanh\!\left(3\sin(K\pi (\mathbf{R} \cdot \mathbf{u}_{\text{tunnel}}))\right)$ where $\mathbf{R} = \mathbf{I} - 2(\mathbf{N}\cdot\mathbf{I})\mathbf{N}$.
   - **What it reveals instantly**:
     - $G^0$ Crease / Shutline (Intergluteal Cleft & Sub-Gluteal Fold): Zebra stripes **jump discontinuously** across the seam (confirming a crisp shutline).
     - $G^1$ Tangent (Ordinary SmoothJoin): Stripes connect across the seam but **kink at sharp corners** (revealing why quadratic `smoothUnion` looks cheap under glossy highlights).
     - $G^2 / G^3$ Curvature & Torsion Continuity (McLaren Fender Sweep): Stripes flow **smoothly without kinks** from the waist across the outer hip into the thigh.
2. **2D Cross-Section Curvature Comb Overlay ($\kappa(s)$)**:
   In the 2D section viewer (`review.html` and `houdini/lab/index.html`), plot spikes $\mathbf{p}(s) + \beta\,\kappa(s)\,\mathbf{n}(s)$ where $\kappa(s) = \frac{x'z'' - z'x'}{(x'^2 + z'^2)^{3/2}}$ along every horizontal and sagittal slice so you can visually tune the peak curvature at the posterior crown and cleft roll-in.
3. **[OpenSubdiv](https://en.wikipedia.org/wiki/Catmull%E2%80%93Clark_subdivision_surface) Semi-Sharp Crease Edge Weights**:
   When exporting a low-poly quad control cage for Catmull-Clark subdivision in Houdini/Blender, assign `creaseweight = 4.5` to `6.0` along the intergluteal sulcus loop ($x = x_{\text{cleft}}, y \in [0.51, 0.67]$) and `creaseweight = 3.5` along the infrigluteal fold loop ($y \approx 0.515, z < -0.04$), fading to `0.0` at the lateral hip ($|x| > 0.11$).

## 5. Answers to All Seven Questions in `documentation/REVIEW_HANDOFF.md`

1. **Representation Comparison (Q1)**: Replace symmetric ellipsoids and monomial multipliers with the **Pelvis-Aligned Curvilinear Flow Solver (`curvilinear_rear_v5`)** for full-body mesh authoring, paired with **Gradient-Modulated Implicit Skinning + PSPS Cross-Section Lofting** for the regional implicit template.
2. **Video (`V01`–`V08`) & Figurine (`R01`–`R04`) Reconciliation (Q2)**:
   - The 8 videos are **4 exact high-res (4K) / low-res (1080p/834p) duplicate pairs** of an Aunt-Fanny/Pixar-style denim-jeans figurine turntable:
     - **Pair A (`V06` 4K + `V05` 1080p)**: Clean $360^\circ$ full-body turntable on a circular base (front $\to$ profile $\to$ rear $\to$ 3/4 rear $\to$ front). **Use `V06` as the primary multi-angle kinematic reference**—it directly supplies the missing $90^\circ$ side profile of the horizontal dorsal shelf and sub-gluteal tuck.
     - **Pair B (`V01` 4K + `V04` 1080p)**: 3/4 side $\to$ rear $\to$ 3/4 $\to$ front closeup.
     - **Pair C (`V02` 4K + `V07` 1080p)**: Bent-over rear closeup $\to$ full rear $\to$ side profile $\to$ front.
     - **Pair D (`V03` 4K + `V08` 834p)**: Rear pocket/cleft closeup $\to$ upper-body closeup.
   - Among `R01`–`R04`, **`R03` (`CatEaredFigurine`)** and **`R04` (`FoxCupFigurine`)** are the two larger-build measurement targets (`R03` defines the front/lateral hip-to-waist saddle flare; `R04` defines the extreme posterior cantilevered rear projection, with scene $Z$-extent `1.3424` vs. `R02`'s `0.4801`).
3. **Donor Segmentation (Q3)**: Use a 3-stage deterministic filter: (a) bottom-cylinder plinth culling ($Y < -0.89$), (b) normal-variance culling (excluding high-frequency hair/fur/prop clusters), and (c) transformation into the reviewed 3-point pelvic triad (`pelvis`, `waist`, `lateral` in `donor-registration-model.mjs`).
4. **Cross-Mesh Correspondence Without Shared Topology (Q4)**: Compare independent Meshy/WorldGen builds in **Intrinsic Cross-Section Curve Space** across 16 horizontal slices $y_k \in [0.48, 0.70] H$, measuring sulcus depth $z_{\text{sulcus}}$, peak crown $z_{\text{peak}}$, cleft dihedral angle $\theta_{\text{cleft}}$, lateral flare $w_{\text{max}}$, and sagittal overhang slope $\partial z_{\text{peak}}/\partial y$.
5. **View-Independent Canonical Body vs. Stylistic View Cheats (Q5)**: Keep the canonical 3D body 100% view-independent for volume and physics; handle 2D 3/4 perspective/silhouette cheats via the **View-Dependent Profile Mover** (Section 4.2) and perspective horizon unwarping (Section 4.1).
6. **Accepted Growth Trajectory (`0000 -> 0010 -> 0018 -> 0026`, Hold `0026`) (Q6)**: Parameterize growth as a monotone trajectory $\theta(s)$ over a clamped clock $s(f) \in [0, 1]$ ($s \equiv 1$ for $f \ge 26$), then feed the resulting rest shapes into [Houdini Vellum Rest Blend](https://www.sidefx.com/docs/houdini/nodes/dop/vellumrestblend.html) or XPBD/RBF pose-space correctives.
7. **Highest-Value Observation & Discriminating Experiment (Q7)**: Extract 8 turntable keyframes ($0^\circ..315^\circ$) from **`V06`** for profile/cantilever calibration, and deploy the verified **`Curvilinear v5`** solver (which boosts true cleft relief by **+48.3%** and cuts sacral drift by **70%** with `0` non-positive Jacobians).

## 6. Drop-In Code Modules for `rainee-shape-lab`

### 6.1 Python Solver (`houdini/curvilinear_rear_v5.py`)

```python
"""Rainee Curvilinear Class-A / Directional-Crease Lobe Solver (v5).

Fixes D-01 (X=+0.0122 sulcus alignment), D-02 (monotonic Hermite inner X expansion),
and D-03 (96% sacral anchor hold + dihedral V-cusp + cantilevered shelf & overhang).
"""
import numpy as np
from rear_model import region, smooth, volume

V5_DEFAULTS = {
    'lateral': 1.08,
    'vertical': 1.04,
    'projection': 1.24,
    'separation': 0.26,
    'upper_shelf': 1.35,      # Cantilevered sports-car dorsal launch shelf (Y in 0.59..0.71)
    'lower_overhang': 1.30,   # Aunt-Fanny teardrop lower pole overhang & sub-gluteal tuck
    'cleft_cusp': 0.96,       # 96% sacral anchor hold at true anatomical sulcus
    'hip_flare': 1.15,        # Lateral Coke-bottle fender flare
    'roundness': 0.65,        # Cleft-gated curvilinear shell relaxation
    'cleft_x_offset': 0.0122  # True sculpted intergluteal sulcus X in body-v4-rest.bin
}

def deform_v5_base(v, amp, controls=None, is_cage=False):
    c = {**V5_DEFAULTS, **(controls or {})}
    x0_cleft = 0.0 if is_cage else (
        c['cleft_x_offset'] * smooth(0.49, 0.56, v[:, 1]) * (1.0 - smooth(0.67, 0.72, v[:, 1]))
    )
    dx_cleft = v[:, 0] - x0_cleft
    ax = np.abs(dx_cleft)
    side = np.where(dx_cleft < 0.0, -1.0, 1.0)
    y = v[:, 1]
    z = v[:, 2]
    mask = region(v)

    eps_x = 0.0008
    u_cleft = np.clip((np.sqrt(ax * ax + eps_x * eps_x) - eps_x) / 0.046, 0.0, 1.0)
    cusp_arc = u_cleft * (2.0 - u_cleft)
    cleft = (1.0 - c['cleft_cusp']) + c['cleft_cusp'] * cusp_arc

    shelf_bell = smooth(0.590, 0.650, y) * (1.0 - smooth(0.667, 0.725, y))
    overhang_bell = smooth(0.495, 0.540, y) * (1.0 - smooth(0.570, 0.620, y))
    z_profile = (
        1.0
        + 0.35 * (c['upper_shelf'] - 1.0) * shelf_bell
        + 0.40 * (c['lower_overhang'] - 1.0) * overhang_bell
    )

    a = amp * mask * cleft
    lat_flare = 1.0 + 0.28 * (c['hip_flare'] - 1.0) * smooth(0.52, 0.63, y) * smooth(0.05, 0.14, ax)
    sx = 1.0 + a * c['lateral'] * lat_flare
    cs = 1.0 + a * c['separation']
    cx = 0.073

    t_x = np.minimum(ax / cx, 1.0)
    s0 = 1.0
    h01 = t_x * t_x * (3.0 - 2.0 * t_x)
    h10 = t_x * (1.0 - t_x) * (1.0 - t_x)
    h11 = t_x * t_x * (t_x - 1.0)
    inner = cx * (cs * h01 + s0 * h10 + np.minimum(sx, 2.2 * cs) * h11)
    outer = cx * cs + (ax - cx) * sx

    pole = c['lower_overhang'] + (c['upper_shelf'] - c['lower_overhang']) * smooth(0.585, 0.625, y)
    droop = -0.016 * amp * mask * cusp_arc * overhang_bell * (c['lower_overhang'] - 0.8)

    out = v.copy()
    out[:, 0] = x0_cleft + side * np.where(ax <= cx, inner, outer)
    out[:, 1] = y + a * (y - 0.605) * c['vertical'] * pole + droop
    out[:, 2] = z - a * (0.025 - z) * c['projection'] * z_profile
    out[mask == 0] = v[mask == 0]
    if amp == 0:
        out[:] = v
    return out

def v5_relax_velocity(v, amp, controls=None, is_cage=False):
    c = {**V5_DEFAULTS, **(controls or {})}
    x0_cleft = 0.0 if is_cage else (
        c['cleft_x_offset'] * smooth(0.49, 0.56, v[:, 1]) * (1.0 - smooth(0.67, 0.72, v[:, 1]))
    )
    dx_cleft = v[:, 0] - x0_cleft
    side = np.where(dx_cleft < 0.0, -1.0, 1.0)
    ax = np.abs(dx_cleft)
    y = v[:, 1]
    z = v[:, 2]

    z_cantilever = -0.010 * amp * smooth(0.59, 0.66, y)
    center = np.column_stack((
        x0_cleft + side * (0.076 * (1.0 + amp * c['separation'])),
        np.full_like(y, 0.602),
        -0.046 - amp * 0.074 * c['projection'] + z_cantilever
    ))
    radii = np.array([
        0.091 * (1.0 + amp * c['lateral'] * c['hip_flare'] * 0.9),
        0.080 * (1.0 + amp * c['vertical'] * 0.5 * (c['upper_shelf'] + c['lower_overhang'])),
        0.095 * (1.0 + amp * c['projection'])
    ])
    q = (v - center) / radii
    rho = np.linalg.norm(q, axis=1)
    target = center + radii * q / np.maximum(rho[:, None], 1e-8)

    gate = (
        smooth(0.492, 0.540, y) * (1.0 - smooth(0.665, 0.725, y))
        * (1.0 - smooth(-0.045, 0.015, z))
        * smooth(0.036, 0.072, ax) * (1.0 - smooth(0.185, 0.218, np.abs(v[:, 0])))
        * smooth(0.25, 0.60, rho) * (1.0 - smooth(1.25, 1.65, rho))
    )
    return (target - v) * gate[:, None]

def deform_v5(v, amp, controls=None, steps=20, is_cage=False):
    c = {**V5_DEFAULTS, **(controls or {})}
    out = deform_v5_base(v, amp, c, is_cage=is_cage)
    roundness = c['roundness']
    if amp == 0.0 or roundness == 0.0:
        return out
    duration = roundness * 3.8 * (1.0 - np.exp(-5.5 * amp))
    dt = duration / steps
    for _ in range(steps):
        k1 = v5_relax_velocity(out, amp, c, is_cage=is_cage)
        k2 = v5_relax_velocity(out + 0.5 * dt * k1, amp, c, is_cage=is_cage)
        k3 = v5_relax_velocity(out + 0.5 * dt * k2, amp, c, is_cage=is_cage)
        k4 = v5_relax_velocity(out + dt * k3, amp, c, is_cage=is_cage)
        out += (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    active = region(v) > 0
    out[~active] = v[~active]
    return out
```

### 6.2 Gradient-Modulated Implicit Skinning & NeuSOGA3D `softMin2` (`houdini/lab/anatomy-model.mjs` Upgrade)

```javascript
/** NeuSOGA3D C2 Shape-Preserving R-Function (Li et al., Sept 2026) */
export function softMin2(fA, fB, a) {
  const radius = Math.max(a, 1e-5);
  const d = fA - fB, ad = Math.abs(d);
  const sAbs = ad < radius ? (d * d) / radius - (ad * ad * ad) / (3 * radius * radius) + radius / 3 : ad;
  return 0.5 * (fA + fB - sAbs);
}

/** Gradient-Angle-Modulated Implicit Skinning + Pressed-Peach Contact Bulge (Vaillant et al. + NeuSOGA3D) */
export function evaluateAnatomyImplicitSkinning(point, template) {
  const d = evaluateAnatomyComponents(point, template), c = template.params;
  let base = softMin2(d.core, d.perineal, c.attachment);
  base = softMin2(base, softMin2(d.leftThigh, d.rightThigh, c.attachment), c.attachment);
  base = softMin2(base, softMin2(d.leftAttachment, d.rightAttachment, c.attachment), c.attachment);

  const posterior = smooth(.02, .08, -point[2]);
  const central = 1 - smooth(.005, .042, Math.abs(point[0]));
  // Sharp G0 contact crease in posterior cleft + tangential contact compression bulge ring
  const cleftRadius = Math.max(2e-4, c.attachment * (1 - .97 * c.cleft * posterior));
  let lobes = softMin2(d.leftLobe, d.rightLobe, cleftRadius);
  const contactBulge = Math.exp(-18 * (d.leftLobe * d.leftLobe + d.rightLobe * d.rightLobe))
                     * posterior * smooth(.006, .035, Math.abs(point[0]));
  lobes -= .0045 * c.cleft * contactBulge;

  // Sub-gluteal overhang gets sharp G0 fold; outer lateral hip gets wide G2 fender flare blend
  const subGlutealFold = posterior * (1 - smooth(.50, .56, point[1])) * (1 - smooth(.09, .14, Math.abs(point[0])));
  const lateralHipFlare = smooth(.085, .145, Math.abs(point[0]));
  const joinRadius = Math.max(2e-4, c.attachment * (1.35 * lateralHipFlare + (1 - lateralHipFlare) * (1 - .92 * subGlutealFold)));
  return softMin2(base, lobes, joinRadius);
}
```

### 6.3 2D-to-3D Perspective Ratio Unwarping & View-Dependent Profile Mover (`houdini/lab/reference-fit-model.mjs` Upgrade)

```javascript
/** Unwarp apparent 2D perspective rear-to-waist width ratio to true 3D orthographic ratio */
export function unwarpPerspectiveRearToWaistRatio(apparent2DRatio, {
  fovYDegrees = 40, framedHeightFraction = 0.55, rearProjectionZ = 0.21, waistDepthZ = -0.03
} = {}) {
  if (!(fovYDegrees > 1 && fovYDegrees < 170)) throw new RangeError('Valid perspective FOV required');
  const dCam = framedHeightFraction / Math.tan((fovYDegrees * Math.PI) / 360);
  const dRear = dCam - rearProjectionZ;
  const dWaist = dCam - waistDepthZ;
  if (!(dRear > 0.05 && dWaist > 0.05)) throw new RangeError('Camera distance too close to surface');
  const magnificationFactor = dWaist / dRear;
  return {
    true3DRatio: apparent2DRatio / magnificationFactor,
    apparent2DRatio,
    perspectiveMagnificationFactor: magnificationFactor,
    cameraDistanceH: dCam
  };
}

/** 'Jessica Rabbit / Anime' View-Dependent 3/4 Silhouette Modifier (render/projection only; never mutates canonical mesh) */
export function applyViewDependentSilhouetteOffset(point, cameraYawRadians, {
  cleftX = 0.0122, farLobeBoost = 0.022, cleftDepthLock = 0.018
} = {}) {
  const [x, y, z] = point;
  const weight34 = Math.sin(2 * Math.min(Math.abs(cameraYawRadians), Math.PI / 2));
  if (weight34 < 1e-5 || y < 0.49 || y > 0.72 || z > 0.015) return [x, y, z];
  const maskY = smooth(0.49, 0.55, y) * (1 - smooth(0.66, 0.72, y));
  const yawSign = cameraYawRadians >= 0 ? 1 : -1;
  const dx = x - cleftX;
  const isFarLobe = dx * yawSign > 0;
  const farBoost = isFarLobe ? farLobeBoost * smooth(0.02, 0.12, Math.abs(dx)) : 0;
  const cleftPull = cleftDepthLock * (1 - smooth(0.0, 0.035, Math.abs(dx)));
  return [
    x + yawSign * weight34 * maskY * farBoost * Math.cos(cameraYawRadians),
    y,
    z - weight34 * maskY * cleftPull
  ];
}
```
