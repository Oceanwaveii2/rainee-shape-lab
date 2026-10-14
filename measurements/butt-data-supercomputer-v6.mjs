/**
 * Experimental scalar spline evaluation, analytic radial style controls,
 * discrete opacity accumulation, and first-order covariance transport.
 * API names are retained for compatibility. These helpers do not implement or
 * certify Class-A automotive surfaces, a trained PCA basis, GOF, SuGaR, or Frosting.
 */

export function cubicBSplineBasis(t) {
  const u = Math.max(0, Math.min(1, Number(t) || 0));
  const u2 = u * u;
  const u3 = u2 * u;
  const om = 1 - u;
  return [
    (om * om * om) / 6,
    (3 * u3 - 6 * u2 + 4) / 6,
    (-3 * u3 + 3 * u2 + 3 * u + 1) / 6,
    u3 / 6
  ];
}

function clampedBasis(normalized, n, explicitKnots) {
  if (!Number.isFinite(normalized)) throw new RangeError('Spline parameter must be finite');
  const knots = explicitKnots == null ? [0, 0, 0, 0,
    ...Array.from({length: n - 4}, (_, i) => (i + 1) / (n - 3)), 1, 1, 1, 1] : Array.from(explicitKnots);
  if (knots.length !== n + 4 || knots.some((k, i) => !Number.isFinite(k) || (i && k < knots[i - 1])) ||
      !(knots[n] > knots[3]) || knots.slice(0, 4).some(k => k !== knots[3]) ||
      knots.slice(-4).some(k => k !== knots[n])) throw new RangeError('Expected a clamped cubic knot vector');
  const t = knots[3] + Math.max(0, Math.min(1, normalized)) * (knots[n] - knots[3]);
  if (t === knots[n]) return Array.from({length: n}, (_, i) => i === n - 1 ? 1 : 0);
  let basis = Array.from({length: knots.length - 1}, (_, i) => knots[i] <= t && t < knots[i + 1] ? 1 : 0);
  for (let degree = 1; degree <= 3; degree++) {
    basis = Array.from({length: knots.length - degree - 1}, (_, i) => {
      const left = knots[i + degree] - knots[i];
      const right = knots[i + degree + 1] - knots[i + 1];
      return (left > 0 ? (t - knots[i]) / left * basis[i] : 0) +
        (right > 0 ? (knots[i + degree + 1] - t) / right * basis[i + 1] : 0);
    });
  }
  return basis.slice(0, n);
}

/** Scalar clamped rational cubic patch, matching the Python fitter's knot domain. */
export function evaluateRationalBicubicNurbs(controlGrid, weightGrid, u, v, options = {}) {
  if (!Array.isArray(controlGrid) || controlGrid.length < 4 || !Array.isArray(controlGrid[0]) || controlGrid[0].length < 4)
    throw new RangeError('Cubic control grid needs at least 4 by 4 entries');
  const M = controlGrid.length, N = controlGrid[0].length;
  if (controlGrid.some(row => !Array.isArray(row) || row.length !== N || row.some(q => !Number.isFinite(q))))
    throw new RangeError('Control grid must be rectangular and finite');
  if (weightGrid != null && (!Array.isArray(weightGrid) || weightGrid.length !== M ||
      weightGrid.some(row => !Array.isArray(row) || row.length !== N || row.some(w => !Number.isFinite(w) || w <= 0))))
    throw new RangeError('Rational weights must be rectangular, finite and positive');
  const bu = clampedBasis(u, M, options.knotsU ?? options.knots_u);
  const bv = clampedBasis(v, N, options.knotsV ?? options.knots_v);
  let num = 0, den = 0;
  for (let a = 0; a < M; a++) for (let b = 0; b < N; b++) {
    const w = (weightGrid?.[a]?.[b] ?? 1) * bu[a] * bv[b];
    num += w * controlGrid[a][b]; den += w;
  }
  if (!(den > 0) || !Number.isFinite(num)) throw new RangeError('Invalid rational spline denominator');
  return num / den;
}

export function evaluateFerrariNurbsGlutealField(thetaRad, yStar, params = {}) {
  // Historical name: this is an analytic radial heuristic, not a fitted spline
  // or a learned PCA synthesis. pcaBeta* are ordinary analytic style controls.
  const {
    hipFlare = 0.78,
    rearProjection = 0.88,
    ridgeWeight = 1.55,
    cleftDepth = 0.32,
    cleftDihedralSharpness = 0.13,
    shelfLaunchSlope = 1.45,
    subGlutealTuck = 0.24,
    pcaBeta1 = 0.0,
    pcaBeta2 = 0.0,
    pcaBeta3 = 0.0
  } = params;

  const y = Math.max(-0.25, Math.min(1.15, Number(yStar) || 0));
  const waistPinch = 1.0 - 0.54 * Math.exp(-Math.pow((y - 1.0) / 0.21, 2));
  const baseRadius = 0.44 * waistPinch;

  const effRear = rearProjection * (1.0 + 0.18 * pcaBeta1 - 0.08 * pcaBeta2);
  const effFlare = hipFlare * (1.0 + 0.10 * pcaBeta1 + 0.22 * pcaBeta2);
  const effCleft = cleftDepth * (1.0 + 0.25 * pcaBeta3);

  const uDome = Math.max(0, Math.min(1, 1.0 - Math.abs(y - 0.34) / 0.44));
  const rationalDomeEnv = (uDome * uDome * (3 - 2 * uDome) * ridgeWeight) /
    (1.0 + (ridgeWeight - 1.0) * uDome * uDome);

  const dThetaL = Math.atan2(Math.sin(thetaRad - (-1.08)), Math.cos(thetaRad - (-1.08)));
  const dThetaR = Math.atan2(Math.sin(thetaRad - (-2.06)), Math.cos(thetaRad - (-2.06)));
  const dThetaCleft = Math.atan2(Math.sin(thetaRad - (-Math.PI / 2)), Math.cos(thetaRad - (-Math.PI / 2)));

  const lobeL = effRear * rationalDomeEnv * Math.exp(-Math.pow(dThetaL / 0.56, 2));
  const lobeR = effRear * rationalDomeEnv * Math.exp(-Math.pow(dThetaR / 0.56, 2));

  const cleftAbs = Math.abs(dThetaCleft);
  const cleftSeam = effCleft * Math.exp(-cleftAbs / Math.max(cleftDihedralSharpness, 0.03)) * rationalDomeEnv;

  const tuckNotch = subGlutealTuck * Math.exp(-Math.pow((y - 0.04) / 0.065, 2)) *
    Math.exp(-Math.pow(dThetaCleft / 0.75, 2));

  const dLat0 = Math.atan2(Math.sin(thetaRad), Math.cos(thetaRad));
  const dLatPi = Math.atan2(Math.sin(thetaRad - Math.PI), Math.cos(thetaRad - Math.PI));
  const fenderEnv = Math.exp(-Math.pow((y - 0.40) / (0.38 / shelfLaunchSlope), 2));
  const fenderFlare = 0.55 * effFlare * fenderEnv * (
    Math.exp(-Math.pow(dLat0 / 0.62, 2)) + Math.exp(-Math.pow(dLatPi / 0.62, 2))
  );

  return Math.max(0.08, baseRadius + Math.max(lobeL, lobeR) + fenderFlare - cleftSeam - tuckNotch);
}

export function computeGofRaySurfaceCrossing(raySplats, targetOpacity = 0.5) {
  // Discrete front-to-back alpha heuristic. This does not integrate a GOF density.
  if (!Number.isFinite(targetOpacity) || targetOpacity <= 0 || targetOpacity > 1)
    throw new RangeError('Target opacity must be in (0,1]');
  if (!Array.isArray(raySplats) || raySplats.length === 0) return null;
  const sorted = [...raySplats]
    .filter(s => Number.isFinite(s?.t) && Number.isFinite(s?.alpha) && s.alpha > 0)
    .sort((a, b) => a.t - b.t);
  if (sorted.length === 0) return null;

  let transmittance = 1.0;
  for (let i = 0; i < sorted.length; i++) {
    const a = Math.min(1, Math.max(0, sorted[i].alpha));
    const prevT = transmittance;
    transmittance *= (1.0 - a);
    const accumulatedOpacity = 1.0 - transmittance;
    if (accumulatedOpacity >= targetOpacity) {
      const prevAcc = 1.0 - prevT;
      const frac = (targetOpacity - prevAcc) / Math.max(accumulatedOpacity - prevAcc, 1e-8);
      const tPrev = i > 0 ? sorted[i - 1].t : sorted[i].t;
      return tPrev + frac * (sorted[i].t - tPrev);
    }
  }
  return null;
}

export function transportSurfaceBoundGaussianSplat(splatCenter, splatCov3x3, surfaceDeformFn, eps = 1e-4) {
  const [x, y, z] = splatCenter;
  const pNew = surfaceDeformFn(x, y, z);
  const px = surfaceDeformFn(x + eps, y, z);
  const py = surfaceDeformFn(x, y + eps, z);
  const pz = surfaceDeformFn(x, y, z + eps);

  const J = [
    [(px[0] - pNew[0]) / eps, (py[0] - pNew[0]) / eps, (pz[0] - pNew[0]) / eps],
    [(px[1] - pNew[1]) / eps, (py[1] - pNew[1]) / eps, (pz[1] - pNew[1]) / eps],
    [(px[2] - pNew[2]) / eps, (py[2] - pNew[2]) / eps, (pz[2] - pNew[2]) / eps]
  ];

  const detJ =
    J[0][0] * (J[1][1] * J[2][2] - J[1][2] * J[2][1]) -
    J[0][1] * (J[1][0] * J[2][2] - J[1][2] * J[2][0]) +
    J[0][2] * (J[1][0] * J[2][1] - J[1][1] * J[2][0]);

  const JS = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      JS[i][j] = J[i][0] * splatCov3x3[0][j] + J[i][1] * splatCov3x3[1][j] + J[i][2] * splatCov3x3[2][j];
    }
  }
  const covNew = [[0, 0, 0], [0, 0, 0], [0, 0, 0]];
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 3; j++) {
      covNew[i][j] = JS[i][0] * J[j][0] + JS[i][1] * J[j][1] + JS[i][2] * J[j][2];
    }
  }

  return {
    center: pNew,
    covariance: covNew,
    jacobianDeterminant: detJ
  };
}
