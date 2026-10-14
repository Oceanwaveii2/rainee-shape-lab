/** Argon curvilinear v5: user-selected design authority.
 * Field and marching-tetrahedra extractor transcribed without geometric changes
 * from the supplied studio. Coordinates H=1, +Y up, posterior -Z.
 * Closed regional artist proposal; fitting and physical contact remain pending.
 */
import {createAnatomyTemplate} from './anatomy-model.mjs';
export const ARGON_V5_SOURCE=Object.freeze({version:'argon-curvilinear-v5-studio',sha256:'52393af0819e66410b0cea1584e3f7d9ba7a6c47616515c0b90187dedf9b711c'});
export const ARGON_V5_STAGES=Object.freeze({
 0:Object.freeze({rearProjection:1,lobeWidth:1,upperPole:1.08,lowerPole:1,cleft:.75,contactBulge:.5,lobeHeight:1.12,separation:1.05}),
 10:Object.freeze({rearProjection:1.22,lobeWidth:1.14,upperPole:1.18,lowerPole:1.12,cleft:.85,contactBulge:.75,lobeHeight:1.12,separation:1.05}),
 18:Object.freeze({rearProjection:1.38,lobeWidth:1.25,upperPole:1.26,lowerPole:1.20,cleft:.92,contactBulge:.9,lobeHeight:1.12,separation:1.05}),
 26:Object.freeze({rearProjection:1.55,lobeWidth:1.36,upperPole:1.34,lowerPole:1.28,cleft:.96,contactBulge:1,lobeHeight:1.12,separation:1.05})
});
export const ARGON_V5_FIXED_KEYS=Object.freeze(['lobeHeight','attachment','asymmetry','pelvisWidth','pelvisDepth','thighFront','kneeTaper']);
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const smooth = (a, b, v) => { const t = clamp((v - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const mix = (a, b, t) => a + (b - a) * t;

function smoothUnionPoly(a, b, k) {
  const r = Math.max(k, 1e-5);
  const h = Math.max(r - Math.abs(a - b), 0) / r;
  return Math.min(a, b) - r * h * h * 0.25;
}

// NeuSOGA3D C2 Shape-Preserving R-Function (Sept 2026)
function softMin2(fA, fB, a) {
  const r = Math.max(a, 1e-5);
  const d = fA - fB, ad = Math.abs(d);
  const sAbs = ad < r ? (d * d) / r - (ad * ad * ad) / (3 * r * r) + r / 3 : ad;
  return 0.5 * (fA + fB - sAbs);
}

function ellipsoid(p, c, r) {
  const q = Math.hypot((p[0] - c[0]) / r[0], (p[1] - c[1]) / r[1], (p[2] - c[2]) / r[2]);
  return (q - 1) * Math.min(r[0], r[1], r[2]);
}

function capsule(p, a, b, r) {
  const dx = p[0]-a[0], dy = p[1]-a[1], dz = p[2]-a[2];
  const vx = b[0]-a[0], vy = b[1]-a[1], vz = b[2]-a[2];
  const den = vx*vx + vy*vy + vz*vz;
  const t = den ? clamp((dx*vx + dy*vy + dz*vz) / den, 0, 1) : 0;
  return Math.hypot(dx - t*vx, dy - t*vy, dz - t*vz) - r;
}

function evaluateField(p, params, mode) {
  const core = ellipsoid(p, [0, 0.567, 0.003], [0.084, 0.085, 0.060]);
  const perineal = ellipsoid(p, [0, 0.516, 0.005], [0.054, 0.055, 0.047]);

  function lobe(side) {
    const hy = 0.087 * 1.12;
    const t = clamp((p[1] - 0.605) / hy, -1.3, 1.3);
    const pole = mix(params.lowerPole, params.upperPole, smooth(-0.35, 0.35, t));
    // Cantilevered dorsal launch shelf & sub-gluteal overhang drop
    const shelfZ = mode === 'v5-implicit' ? -0.014 * (params.upperPole - 0.9) * smooth(-0.1, 0.65, t) : 0;
    const droopY = mode === 'v5-implicit' ? -0.012 * (params.lowerPole - 0.85) * smooth(-0.85, -0.05, -t) : 0;
    const rx = 0.079 * params.lobeWidth * pole;
    const rz = 0.068 * params.rearProjection * pole;
    return ellipsoid([p[0], p[1] - droopY, p[2] - shelfZ], [side * 0.073 * params.separation, 0.608, -0.015 - rz], [rx, hy, rz]);
  }

  function thigh(side) {
    const t = clamp((p[1] - 0.325) / 0.24, 0, 1);
    const cx = side * mix(0.112, 0.082, smooth(0, 1, t));
    const fullness = smooth(0.10, mix(0.88, 0.63, 0.65), t);
    const radial = mix(0.03, 0.068 * params.thighFullness, fullness);
    const outward = smooth(-0.004, 0.004, side * (p[0] - cx));
    const rx = radial * mix(0.82, params.thighOuter, outward);
    const front = smooth(-0.003, 0.003, p[2] - 0.018);
    const rz = mix(0.027, 0.050 * params.thighFullness, fullness) * mix(0.8, 1.05, front);
    return ellipsoid(p, [cx, 0.445, 0.018], [rx, 0.12, rz]);
  }

  const att = 0.015;
  const attachRadius = 0.038 + att * 0.3;
  const dL = lobe(-1), dR = lobe(1);
  const tL = thigh(-1), tR = thigh(1);
  const aL = capsule(p, [-0.052, 0.582, -0.020], [-0.073 * params.separation, 0.609, -0.052], attachRadius);
  const aR = capsule(p, [0.052, 0.582, -0.020], [0.073 * params.separation, 0.609, -0.052], attachRadius);

  if (mode === 'legacy-smooth') {
    let base = smoothUnionPoly(core, perineal, att);
    base = smoothUnionPoly(base, smoothUnionPoly(tL, tR, att), att);
    base = smoothUnionPoly(base, smoothUnionPoly(aL, aR, att), att);
    const lobes = smoothUnionPoly(dL, dR, att * 1.8);
    return smoothUnionPoly(base, lobes, att * 1.8);
  }

  let base = softMin2(core, perineal, att);
  base = softMin2(base, softMin2(tL, tR, att), att);
  base = softMin2(base, softMin2(aL, aR, att), att);

  const posterior = smooth(0.02, 0.08, -p[2]);
  const central = 1 - smooth(0.005, 0.045, Math.abs(p[0]));
  const cleftRadius = Math.max(2e-4, att * (1 - 0.97 * params.cleft * posterior));
  let lobes = softMin2(dL, dR, cleftRadius);

  // Vaillant Implicit Skinning tangential contact bulge ring outside sagittal septum
  const contactBulge = Math.exp(-18 * (dL * dL + dR * dR)) * posterior
                     * smooth(0.005, 0.035, Math.abs(p[0])) * smooth(0.50, 0.56, p[1]) * (1 - smooth(0.66, 0.71, p[1]));
  lobes -= 0.0048 * params.contactBulge * params.cleft * contactBulge;

  const subGlutealFold = posterior * (1 - smooth(0.50, 0.565, p[1])) * (1 - smooth(0.09, 0.14, Math.abs(p[0])));
  const lateralHipFlare = smooth(0.085, 0.145, Math.abs(p[0]));
  const joinRadius = Math.max(2e-4, att * (1.45 * lateralHipFlare + (1 - lateralHipFlare) * (1 - 0.93 * Math.max(params.cleft * posterior * central, subGlutealFold))));
  return softMin2(base, lobes, joinRadius);
}

function extractSurface(params, mode, resolution = 26) {
  const min = [-0.26, 0.31, -0.34], max = [0.26, 0.74, 0.12];
  const extent = [max[0]-min[0], max[1]-min[1], max[2]-min[2]];
  const h = Math.max(...extent) / resolution;
  const cells = extent.map(e => Math.max(4, Math.ceil(e / h)));
  const dims = cells.map(n => n + 1);
  const step = extent.map((e, i) => e / cells[i]);
  const total = dims[0] * dims[1] * dims[2];
  const grid = new Float32Array(total);
  const idx = (x, y, z) => x + dims[0] * (y + dims[1] * z);
  const coord = id => {
    const x = id % dims[0], yz = Math.floor(id / dims[0]), y = yz % dims[1], z = Math.floor(yz / dims[1]);
    return [min[0] + x * step[0], min[1] + y * step[1], min[2] + z * step[2]];
  };
  const eps = 1e-5;
  for (let z = 0; z < dims[2]; z++) {
    for (let y = 0; y < dims[1]; y++) {
      for (let x = 0; x < dims[0]; x++) {
        let v = evaluateField([min[0]+x*step[0], min[1]+y*step[1], min[2]+z*step[2]], params, mode);
        if ((x===0||y===0||z===0||x===cells[0]||y===cells[1]||z===cells[2]) && v <= 0) v = eps;
        if (Math.abs(v) < eps) v = eps;
        grid[idx(x, y, z)] = v;
      }
    }
  }
  const points = [], normals = [], faces = [], edges = new Map();
  const nEps = Math.min(...step) * 0.04;
  function normalAt(p) {
    const gx = evaluateField([p[0]+nEps, p[1], p[2]], params, mode) - evaluateField([p[0]-nEps, p[1], p[2]], params, mode);
    const gy = evaluateField([p[0], p[1]+nEps, p[2]], params, mode) - evaluateField([p[0], p[1]-nEps, p[2]], params, mode);
    const gz = evaluateField([p[0], p[1], p[2]+nEps], params, mode) - evaluateField([p[0], p[1], p[2]-nEps], params, mode);
    const len = Math.hypot(gx, gy, gz) || 1;
    return [gx/len, gy/len, gz/len];
  }
  function getEdge(a, b) {
    const key = a < b ? a + ',' + b : b + ',' + a;
    if (edges.has(key)) return edges.get(key);
    const pa = coord(a), pb = coord(b), t = grid[a] / (grid[a] - grid[b]);
    const p = [pa[0] + (pb[0]-pa[0])*t, pa[1] + (pb[1]-pa[1])*t, pa[2] + (pb[2]-pa[2])*t];
    const id = points.length / 3;
    points.push(p[0], p[1], p[2]);
    const n = normalAt(p);
    normals.push(n[0], n[1], n[2]);
    edges.set(key, id);
    return id;
  }
  function addTri(a, b, c, dir) {
    const ax = points[a*3], ay = points[a*3+1], az = points[a*3+2];
    const ux = points[b*3]-ax, uy = points[b*3+1]-ay, uz = points[b*3+2]-az;
    const vx = points[c*3]-ax, vy = points[c*3+1]-ay, vz = points[c*3+2]-az;
    const cx = uy*vz - uz*vy, cy = uz*vx - ux*vz, cz = ux*vy - uy*vx;
    if (cx*dir[0] + cy*dir[1] + cz*dir[2] < 0) { const tmp = b; b = c; c = tmp; }
    faces.push(a, b, c);
  }
  const tets = [[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]];
  for (let z = 0; z < cells[2]; z++) {
    for (let y = 0; y < cells[1]; y++) {
      for (let x = 0; x < cells[0]; x++) {
        const cube = [idx(x,y,z), idx(x+1,y,z), idx(x+1,y+1,z), idx(x,y+1,z), idx(x,y,z+1), idx(x+1,y,z+1), idx(x+1,y+1,z+1), idx(x,y+1,z+1)];
        for (const tet of tets) {
          const ins = [], outs = [];
          for (const i of tet) (grid[cube[i]] < 0 ? ins : outs).push(cube[i]);
          if (!ins.length || !outs.length) continue;
          const pIn = coord(ins[0]), pOut = coord(outs[0]);
          const dir = [pOut[0]-pIn[0], pOut[1]-pIn[1], pOut[2]-pIn[2]];
          if (ins.length === 1) addTri(getEdge(ins[0],outs[0]), getEdge(ins[0],outs[1]), getEdge(ins[0],outs[2]), dir);
          else if (ins.length === 3) addTri(getEdge(outs[0],ins[0]), getEdge(outs[0],ins[1]), getEdge(outs[0],ins[2]), dir);
          else {
            const ac = getEdge(ins[0],outs[0]), ad = getEdge(ins[0],outs[1]), bc = getEdge(ins[1],outs[0]), bd = getEdge(ins[1],outs[1]);
            addTri(ac, ad, bd, dir); addTri(ac, bd, bc, dir);
          }
        }
      }
    }
  }
  let vol = 0;
  for (let i = 0; i < faces.length; i += 3) {
    const a = faces[i]*3, b = faces[i+1]*3, c = faces[i+2]*3;
    vol += (points[a]*(points[b+1]*points[c+2]-points[b+2]*points[c+1]) + points[a+1]*(points[b+2]*points[c]-points[b]*points[c+2]) + points[a+2]*(points[b]*points[c+1]-points[b+1]*points[c])) / 6;
  }
  return { positions: new Float32Array(points), normals: new Float32Array(normals), triangles: new Uint32Array(faces), volume: Math.abs(vol) };
}

export function evaluateArgonV5Field(point,parameters,{legacyComparison=false}={}){
 if(!Array.isArray(point)||point.length!==3||!point.every(Number.isFinite))throw Error('Finite 3D point required.');
 return evaluateField(point,createAnatomyTemplate(parameters).params,legacyComparison?'legacy-smooth':'v5-implicit');
}
export function extractArgonV5Surface(parameters,{resolution=24,legacyComparison=false}={}){
 if(!Number.isInteger(resolution)||resolution<8||resolution>80)throw Error('Argon resolution must be an integer in 8…80.');
 const params=createAnatomyTemplate(parameters).params;
 const mesh=extractSurface(params,legacyComparison?'legacy-smooth':'v5-implicit',resolution);
 return {...mesh,engine:'argon-v5',source:ARGON_V5_SOURCE,
  scope:'Complete regional artist proposal; fixed extraction window, no fitted full-body or physical-contact claim'};
}
