/** Pure ES Module: Pelvis-Aligned Curvilinear Class-A / Directional-Crease Lobe Solver (v5)
 * plus D-04 VDB Normal Winding Repair and "Jessica Rabbit / Anime" View-Dependent 3/4 Modifier.
 */
import {enclosedVolume} from './rear-model.mjs';

export const V5_REAR_DEFAULTS = Object.freeze({
  lateral: 1.08,
  vertical: 1.04,
  projection: 1.24,
  separation: 0.26,
  upper_pole: 1.35,
  lower_pole: 1.30,
  cleft_hold: 0.96,
  hip_flare: 1.15,
  roundness: 0.65,
  cleft_x_offset: 0.0122
});

function finitePoints(points){
  if(!points||points.length<3||points.length%3||!points.every(Number.isFinite))throw Error('Finite nonempty XYZ points required');
}
function checkedControls(controls){
  const c={...V5_REAR_DEFAULTS,...controls};
  for(const k of Object.keys(V5_REAR_DEFAULTS))if(!Number.isFinite(c[k]))throw Error('Finite control required: '+k);
  for(const k of ['lateral','vertical','projection','upper_pole','lower_pole','hip_flare'])if(c[k]<=0)throw Error('Positive control required: '+k);
  if(c.separation<0||c.cleft_hold<0||c.cleft_hold>1||c.roundness<0||c.roundness>.85)throw Error('Control outside supported range');
  return c;
}

function smooth(a, b, x) {
  const s = Math.max(0, Math.min(1, (x - a) / (b - a)));
  return s * s * (3 - 2 * s);
}

function relaxVelocityPoint(px, py, pz, amp, c, isCage) {
  const x0Cleft = isCage ? 0 : c.cleft_x_offset * smooth(0.49, 0.56, py) * (1 - smooth(0.67, 0.72, py));
  const dx = px - x0Cleft;
  const side = dx < 0 ? -1 : 1;
  const ax = Math.abs(dx);
  const gateY = smooth(0.492, 0.540, py) * (1 - smooth(0.665, 0.725, py));
  const gateZ = 1 - smooth(-0.045, 0.015, pz);
  const gateX = smooth(0.036, 0.072, ax) * (1 - smooth(0.185, 0.218, Math.abs(px)));
  const preGate = gateY * gateZ * gateX;
  if (preGate <= 0) return [0, 0, 0];

  const zCantilever = -0.010 * amp * smooth(0.59, 0.66, py);
  const cx = x0Cleft + side * (0.076 * (1 + amp * c.separation));
  const cy = 0.602;
  const cz = -0.046 - amp * 0.074 * c.projection + zCantilever;

  const rx = 0.091 * (1 + amp * c.lateral * c.hip_flare * 0.9);
  const ry = 0.080 * (1 + amp * c.vertical * 0.5 * (c.upper_pole + c.lower_pole));
  const rz = 0.095 * (1 + amp * c.projection);

  const qx = (px - cx) / rx, qy = (py - cy) / ry, qz = (pz - cz) / rz;
  const rho = Math.hypot(qx, qy, qz);
  const gateRho = smooth(0.25, 0.60, rho) * (1 - smooth(1.25, 1.65, rho));
  const gate = preGate * gateRho;
  if (gate <= 0) return [0, 0, 0];

  const invRho = 1 / Math.max(rho, 1e-8);
  const tx = cx + rx * qx * invRho;
  const ty = cy + ry * qy * invRho;
  const tz = cz + rz * qz * invRho;
  return [(tx - px) * gate, (ty - py) * gate, (tz - pz) * gate];
}

export function deformRearV5(base, amp, controls = V5_REAR_DEFAULTS, {
  steps = 12, isCage = false, out = new Float64Array(base.length)
} = {}) {
  finitePoints(base);
  if(!Number.isFinite(amp)||amp<0)throw Error('Finite nonnegative amplitude required');
  if(!Number.isInteger(steps)||steps<0||steps>128)throw Error('Integration steps must be 0..128');
  if(out.length!==base.length)throw Error('Output buffer size mismatch');
  const c = checkedControls(controls);
  out.set(base);
  if (amp === 0) return out;
  const roundness = c.roundness ?? 0.65;
  const duration = roundness * 3.8 * (1 - Math.exp(-5.5 * amp));
  const dt = steps > 0 ? duration / steps : 0;

  for (let i = 0; i < base.length; i += 3) {
    const x = base[i], y = base[i + 1], z = base[i + 2], axRaw = Math.abs(x);
    if (y <= 0.49 || y >= 0.73 || z >= 0.015 || axRaw >= 0.22) continue;
    const mask = smooth(0.49, 0.555, y) * (1 - smooth(0.667, 0.73, y))
               * (1 - smooth(-0.045, 0.015, z)) * (1 - smooth(0.18, 0.22, axRaw));
    if (mask <= 0) continue;

    const x0Cleft = isCage ? 0 : c.cleft_x_offset * smooth(0.49, 0.56, y) * (1 - smooth(0.67, 0.72, y));
    const dx = x - x0Cleft;
    const ax = Math.abs(dx);
    const side = dx < 0 ? -1 : 1;

    const epsX = 0.0008;
    const uCleft = Math.max(0, Math.min(1, (Math.hypot(ax, epsX) - epsX) / 0.046));
    const cuspArc = uCleft * (2 - uCleft);
    const cleft = (1 - c.cleft_hold) + c.cleft_hold * cuspArc;

    const shelfBell = smooth(0.590, 0.650, y) * (1 - smooth(0.667, 0.725, y));
    const overhangBell = smooth(0.495, 0.540, y) * (1 - smooth(0.570, 0.620, y));
    const zProfile = 1 + 0.35 * (c.upper_pole - 1) * shelfBell + 0.40 * (c.lower_pole - 1) * overhangBell;

    const a = amp * mask * cleft;
    const latFlare = 1 + 0.28 * (c.hip_flare - 1) * smooth(0.52, 0.63, y) * smooth(0.05, 0.14, ax);
    const sx = 1 + a * c.lateral * latFlare;
    const cs = 1 + a * c.separation;
    const cx = 0.073;

    const tx = Math.min(ax / cx, 1);
    const h01 = tx * tx * (3 - 2 * tx);
    const h10 = tx * (1 - tx) * (1 - tx);
    const h11 = tx * tx * (tx - 1);
  const terminalSlope = Math.min(sx, 2.2 * cs);
  const inner = cx * (cs * h01 + 1.0 * h10 + terminalSlope * h11);
  // Match the clamped inner slope at the join, then recover full expansion.
  const outerSlope = terminalSlope + (sx - terminalSlope) * smooth(cx, cx + 0.020, ax);
  const outer = cx * cs + (ax - cx) * outerSlope;
    const nx = ax <= cx ? inner : outer;

    const pole = c.lower_pole + (c.upper_pole - c.lower_pole) * smooth(0.585, 0.625, y);
    const droop = -0.016 * amp * mask * cuspArc * overhangBell * (c.lower_pole - 0.8);

    let px = x0Cleft + side * nx;
    let py = y + a * (y - 0.605) * c.vertical * pole + droop;
    let pz = z - a * (0.025 - z) * c.projection * zProfile;

    if (dt > 0) {
      for (let s = 0; s < steps; s++) {
        const k1 = relaxVelocityPoint(px, py, pz, amp, c, isCage);
        if (k1[0] === 0 && k1[1] === 0 && k1[2] === 0) break;
        const k2 = relaxVelocityPoint(px + 0.5 * dt * k1[0], py + 0.5 * dt * k1[1], pz + 0.5 * dt * k1[2], amp, c, isCage);
        const k3 = relaxVelocityPoint(px + 0.5 * dt * k2[0], py + 0.5 * dt * k2[1], pz + 0.5 * dt * k2[2], amp, c, isCage);
        const k4 = relaxVelocityPoint(px + dt * k3[0], py + dt * k3[1], pz + dt * k3[2], amp, c, isCage);
        px += (dt / 6) * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]);
        py += (dt / 6) * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]);
        pz += (dt / 6) * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2]);
      }
    }
    out[i] = px;
    out[i + 1] = py;
    out[i + 2] = pz;
  }
  return out;
}

export function calibrateRearV5(cage, triangles, ratio, controls = V5_REAR_DEFAULTS, {steps = 12} = {}) {
  finitePoints(cage);checkedControls(controls);
  if (!Number.isFinite(ratio) || ratio < 1 || ratio > 4) throw Error('Rear volume must be between 1× and 4×');
  const rest = enclosedVolume(cage, triangles);
  if(!(rest>0)||!Number.isFinite(rest))throw Error('Positive finite control-cage volume required');
  if (ratio === 1) return {amplitude: 0, cage: cage.slice(), ratio: 1};
  let low = 0, high = 1.5, work = new Float64Array(cage.length);
  if (enclosedVolume(deformRearV5(cage, high, controls, {steps, isCage: true, out: work}), triangles) < rest * ratio)
    throw Error('Shape cannot reach this volume');
  for (let i = 0; i < 28; i++) {
    const mid = 0.5 * (low + high);
    if (enclosedVolume(deformRearV5(cage, mid, controls, {steps, isCage: true, out: work}), triangles) < rest * ratio)
      low = mid;
    else high = mid;
  }
  const amplitude = 0.5 * (low + high);
  deformRearV5(cage, amplitude, controls, {steps, isCage: true, out: work});
  return {amplitude, cage: work, ratio: enclosedVolume(work, triangles) / rest};
}

export function screenRearV5(samples, amp, controls = V5_REAR_DEFAULTS, {steps = 12} = {}) {
  finitePoints(samples);checkedControls(controls);
  if(!Number.isFinite(amp)||amp<0)throw Error('Finite nonnegative amplitude required');
  if (!amp) return {minimum: 1, nonpositive: 0};
  const e = 2e-5, derivatives = [];
  for (let k = 0; k < 3; k++) {
    const a = samples.slice(), b = samples.slice();
    for (let i = k; i < a.length; i += 3) { a[i] += e; b[i] -= e; }
    const pa = deformRearV5(a, amp, controls, {steps, isCage: false});
    const pb = deformRearV5(b, amp, controls, {steps, isCage: false});
    for (let i = 0; i < pa.length; i++) pa[i] = (pa[i] - pb[i]) / (2 * e);
    derivatives.push(pa);
  }
  let minimum = Infinity, nonpositive = 0;
  const [a, b, d] = derivatives;
  for (let i = 0; i < a.length; i += 3) {
    const det = a[i] * (b[i + 1] * d[i + 2] - b[i + 2] * d[i + 1])
              - b[i] * (a[i + 1] * d[i + 2] - a[i + 2] * d[i + 1])
              + d[i] * (a[i + 1] * b[i + 2] - a[i + 2] * b[i + 1]);
    minimum = Math.min(minimum, det);
    if (det <= 0) nonpositive++;
  }
  return {minimum, nonpositive};
}

/** Fix D-04: Flip inward-pointing left-handed Houdini VDB triangles (vertex ID >= 98078) */
export function fixVdbTriangleWinding(positions, triangles, vdbStartVertex = 98078) {
  const out = new Uint32Array(triangles);
  let flipped = 0;
  for (let i = 0; i < out.length; i += 3) {
    const i0 = out[i], i1 = out[i + 1], i2 = out[i + 2];
    if (i0 < vdbStartVertex && i1 < vdbStartVertex && i2 < vdbStartVertex) continue;
    const x0 = positions[i0 * 3], y0 = positions[i0 * 3 + 1], z0 = positions[i0 * 3 + 2];
    const x1 = positions[i1 * 3], y1 = positions[i1 * 3 + 1], z1 = positions[i1 * 3 + 2];
    const x2 = positions[i2 * 3], y2 = positions[i2 * 3 + 1], z2 = positions[i2 * 3 + 2];
    const ux = x1 - x0, uy = y1 - y0, uz = z1 - z0;
    const wx = x2 - x0, wy = y2 - y0, wz = z2 - z0;
    const nx = uy * wz - uz * wy, ny = uz * wx - ux * wz, nz = ux * wy - uy * wx;
    const cx = (x0 + x1 + x2) / 3, cy = (y0 + y1 + y2) / 3 - 0.58, cz = (z0 + z1 + z2) / 3 + 0.01;
    if (nx * cx + ny * cy + nz * cz < 0) {
      out[i + 1] = i2;
      out[i + 2] = i1;
      flipped++;
    }
  }
  return {triangles: out, flippedCount: flipped};
}

/** 'Jessica Rabbit / Anime' View-Dependent 3/4 Silhouette Modifier (display only; never mutates canonical export) */
export function applyViewDependentSilhouetteBuffer(basePositions, cameraYawRadians, strength = 0, {
  cleftX = 0.0122, out = new Float32Array(basePositions.length)
} = {}) {
  out.set(basePositions);
  if (!(strength > 0) || !Number.isFinite(cameraYawRadians)) return out;
  // cameraYawRadians = 0 at back view (-Z), +/- PI/2 at side view (+/-X)
  const absYaw = Math.min(Math.abs(cameraYawRadians), Math.PI / 2);
  const weight34 = Math.sin(2 * absYaw) * strength;
  if (weight34 < 1e-5) return out;
  const yawSign = cameraYawRadians >= 0 ? 1 : -1;
  const cosYaw = Math.cos(absYaw);
  for (let i = 0; i < out.length; i += 3) {
    const x = out[i], y = out[i + 1], z = out[i + 2];
    if (y <= 0.49 || y >= 0.72 || z >= 0.015 || Math.abs(x) >= 0.22) continue;
    const maskY = smooth(0.49, 0.55, y) * (1 - smooth(0.66, 0.72, y)) * (1 - smooth(-0.04, 0.015, z));
    const dx = x - cleftX;
    const isFarLobe = dx * yawSign > 0;
    const farBoost = isFarLobe ? 0.022 * smooth(0.02, 0.12, Math.abs(dx)) : 0;
    const cleftPull = 0.018 * (1 - smooth(0.0, 0.035, Math.abs(dx)));
    out[i] = x + yawSign * weight34 * maskY * farBoost * cosYaw;
    out[i + 2] = z - weight34 * maskY * cleftPull;
  }
  return out;
}
