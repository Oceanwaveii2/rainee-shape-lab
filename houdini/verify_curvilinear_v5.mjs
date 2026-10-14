import assert from 'node:assert/strict';
import fs from 'node:fs';
import {readRetainedAsset} from '../tools/retained-asset.mjs';
import {V5_REAR_DEFAULTS, calibrateRearV5, deformRearV5, screenRearV5, fixVdbTriangleWinding, applyViewDependentSilhouetteBuffer} from './curvilinear-rear-v5.mjs';
import {activeRearSamples} from './rear-model.mjs';
import {createAnatomyTemplate, softMin2, pspsTransition, pspsBasis, evaluateAnatomyImplicitSkinning, extractAnatomyImplicitSkinning, measureAnatomyMesh} from './lab/anatomy-model.mjs';
import {unwarpPerspectiveRearToWaistRatio, applyViewDependentSilhouetteOffset, computeCurvatureComb2D} from './lab/reference-fit-model.mjs';

const bBuf = readRetainedAsset('houdini/body-v4-rest.bin');
const tBuf = readRetainedAsset('houdini/pelvic-repair/implicit-repaired-triangles.bin');
const cBuf = readRetainedAsset('houdini/cage-rest.bin');
const ctBuf = readRetainedAsset('houdini/cage-triangles.bin');

const body = new Float32Array(bBuf.buffer, bBuf.byteOffset, bBuf.byteLength / 4);
const tri = new Uint32Array(tBuf.buffer, tBuf.byteOffset, tBuf.byteLength / 4);
const cage = new Float32Array(cBuf.buffer, cBuf.byteOffset, cBuf.byteLength / 4);
const cageTri = new Uint32Array(ctBuf.buffer, ctBuf.byteOffset, ctBuf.byteLength / 4);

// 1. Test D-04 VDB Triangle Winding Fix
const fixed = fixVdbTriangleWinding(body, tri, 98078);
assert(fixed.triangles.length===tri.length);
assert(fixed.flippedCount>0); // Radial heuristic smoke test, not an outward-winding proof.

// 2. Test Curvilinear v5 Calibration, Deformation, and Jacobian Audit at 2.50x
const solve = calibrateRearV5(cage, cageTri, 2.5, V5_REAR_DEFAULTS, {steps: 12});
assert(Math.abs(solve.ratio - 2.5) < 1e-5, 'Expected exact 2.5x cage volume calibration');
const samples = activeRearSamples(body);
const screen = screenRearV5(samples, solve.amplitude, V5_REAR_DEFAULTS, {steps: 12});
assert(screen.nonpositive === 0 && screen.minimum > 0.18, `Expected min det(J) > 0.18, got ${screen.minimum}`);
const deformed = deformRearV5(body, solve.amplitude, V5_REAR_DEFAULTS, {steps: 12, isCage: false});
assert(deformed.length === body.length);
assert.throws(()=>deformRearV5(body,NaN));
assert.throws(()=>deformRearV5(body,.3,{lateral:Infinity}));
assert.throws(()=>deformRearV5(body,.3,V5_REAR_DEFAULTS,{steps:1.5}));
assert.throws(()=>screenRearV5(new Float32Array(),.3));

// 3. Test View-Dependent 3/4 Silhouette Modifier
const vd = applyViewDependentSilhouetteBuffer(deformed, (38 * Math.PI) / 180, 1.0);
assert(vd.length === deformed.length);
const ptVd = applyViewDependentSilhouetteOffset([0.09, 0.61, -0.15], (38 * Math.PI) / 180);
const ptCleft = applyViewDependentSilhouetteOffset([0.015, 0.61, -0.11], (38 * Math.PI) / 180);
assert(ptVd[0] > 0.09 && ptCleft[2] < -0.11);

// 4. Test NeuSOGA3D softMin2, PSPS Basis Partition of Unity, & Implicit Skinning Contact Bulge
assert(Math.abs(softMin2(0.1, 0.1, 0.05) - (0.1 - 0.05 / 6)) < 1e-9);
const basis = pspsBasis(0.61, [0.50, 0.56, 0.62, 0.68], 3);
const sumBasis = basis.reduce((a, b) => a + b, 0);
assert(Math.abs(sumBasis - 1.0) < 1e-12 && basis.every(v => v >= 0));

const tpl = createAnatomyTemplate({lobeWidth: 1.35, rearProjection: 1.55, cleft: 0.9});
const impMesh = extractAnatomyImplicitSkinning(tpl, {resolution: 24});
const impStats = measureAnatomyMesh(impMesh);
assert(impStats.closed && impStats.connectedComponents === 1 && impStats.volume > 0);

// 5. Test 2D-to-3D Perspective Ratio Unwarping & Class-A Curvature Comb
const unwarp = unwarpPerspectiveRearToWaistRatio(2.45, {fovYDegrees: 40});
assert(unwarp.true3DRatio > 1.95 && unwarp.true3DRatio < 2.15);
const dummySegs = Array.from({length: 40}, (_, i) => {
  const x0 = -0.18 + i * 0.009, x1 = x0 + 0.009;
  const z0 = -0.12 - 0.08 * Math.sin(Math.PI * ((x0 + 0.18) / 0.36));
  const z1 = -0.12 - 0.08 * Math.sin(Math.PI * ((x1 + 0.18) / 0.36));
  return [[x0, 0.61, z0], [x1, 0.61, z1]];
});
const comb = computeCurvatureComb2D(dummySegs);
assert(comb.left.length > 0 && comb.right.length > 0);

const verificationReport = {
  passed: true,
  flipped_vdb_triangles: fixed.flippedCount,
  v5_25x_amplitude: solve.amplitude,
  v5_25x_cage_ratio: solve.ratio,
  v5_25x_min_jacobian_det: screen.minimum,
  v5_25x_nonpositive_jacobians: screen.nonpositive,
  implicit_skinning_closed: impStats.closed,
  implicit_skinning_volume_H3: impStats.volume,
  psps_partition_of_unity_error: Math.abs(sumBasis - 1),
  perspective_40deg_unwarped_ratio: unwarp.true3DRatio
};
fs.writeFileSync('houdini/verification-curvilinear-v5.json', JSON.stringify(verificationReport, null, 2));
console.log('VERIFIED CURVILINEAR V5 & 2D-TO-3D SUITE:', JSON.stringify(verificationReport));
