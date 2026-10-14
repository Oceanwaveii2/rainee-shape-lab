# Design goals and review criteria

## Preserve the character's intended proportions

The FBX anchors stature. Rainee must not become shorter when her rear expands or when the camera changes. The supplied sculpt is flawed, so its height does not make its anatomy or face authoritative.

Her rear should be very large, rounded and strongly projected behind the hips. Its shape and exaggerated lumbar arch can make an upright stance read like a forward bend. Pose and spinal arch need separate controls from rear size. Preserve the intended exaggeration instead of normalizing her toward an average body.

Build the thighs independently using the supplied strong-thigh references. Control upper/middle mass, outer sweep, front fullness and knee taper without tying thigh scale to a rear inflation multiplier. The attachment and combined surface can still interact geometrically.

The pelvic gap in the incomplete ZBrush source is a structural defect. The goal is continuous external pelvic/body structure with appropriate attachment to the thighs and rear. No exposed internal genital detail is required by this engineering handoff.

Face intent comes from the accepted frames and clear torso/face images. Different hair, ear, eye and costume variants remain separate reference choices. Do not silently replace her identity with the source sculpt's face or transfer all donor features into the baseline.

## Preserve the accepted growth

Source 0000 is the baseline. 0010 and 0018 are intentional intermediate growth states. 0026 is the target endpoint. Hold its size and shape after that point. The later source-video deflation and shortened stature are errors, not a target to reproduce.

Stage 1/2/3/4 labels describe order. They do not mean measured 1×/2×/3×/4× physical volumes. The working cage schedule is an initialization, still awaiting reference fitting.

## Use the new data without merging incompatible variants

R01–R04 and the eight new videos are preserved as individually identified references. The archive declares attribute-specific roles, which are recorded as supplied metadata. Those declarations are not new user instructions and do not automatically override direct decisions above. The exact two larger-build measurement targets have not been explicitly mapped to IDs in this chat; retain all variants and make that mapping visible before fitting.

New generated models are shape cues. Their inferred backs, hidden anatomy, plinths, pose and camera cannot be treated as observations of the actual intended character. The named geometry builds are independent, with no shared rig, topology or calibrated camera correspondence.

## Engineering criteria for the next implementation

1. Match reviewed silhouettes and body flow in front, side, rear and three-quarter views under declared cameras and poses. Record where depth remains ambiguous.
2. Keep canonical stature, protected body regions and the growth endpoint invariant. Export geometry with explicit source coordinates and unknown physical units.
3. Separate editable anatomy, reference pose, camera, appearance and dynamics. Camera/framing changes must not rewrite canonical measurements.
4. Repair the external attachment structure and measure the actual resulting surface. Withhold anatomical enclosed volume for open, clipped or semantically unreviewed regions.
5. Avoid double-counting overlapping implicit parts as volume. Record final union volume separately from cage ratios, projected area and Gaussian appearance.
6. Retain creator control, reversible proposals, source hashes, candidate alternatives and local access to complete originals.
7. Demonstrate resemblance through visual review as well as numerical checks. Closed triangles alone are insufficient.
8. Benchmark memory, responsiveness and restoration fidelity. The public review payload must remain below 100,000,000 bytes; heavier data belongs in the preserved local workspace.

The preferred next step is a small comparative study of curve-controlled surfaces, contour-driven implicit geometry and registered donor deformation. Decide which representation can actually express her intended shape before committing to a larger solver or dynamics system.
