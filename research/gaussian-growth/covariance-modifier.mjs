import * as THREE from 'three';
import {dyno} from '@sparkjsdev/spark';

// First-order transport for a nonlinear map: exact for the local J affine
// linearization, not the exact transformed distribution of a finite Gaussian.
export const GLSL_FIELD=`
void raineeCompactGrowth(inout CovSplat splat, vec3 centre, vec3 radii, float growth) {
  if (!isCovSplatActive(splat.flags) || growth == 1.0) return;
  if (growth < 1.0 || growth > 2.25 || isnan(growth) || isinf(growth)
      || any(lessThan(radii, vec3(0.0001))) || any(isnan(radii)) || any(isinf(radii))) return;
  vec3 d = splat.center - centre;
  vec3 normalized = d / radii;
  float q = dot(normalized, normalized);
  if (q >= 1.0 || isnan(q) || isinf(q)) return;
  float k = growth - 1.0;
  float u = 1.0 - q;
  float w = u*u*u;
  vec3 gradient = -6.0*u*u*d/(radii*radii);
  mat3 J = mat3(1.0);
  for (int column=0; column<3; ++column)
    for (int row=0; row<3; ++row)
      J[column][row] += k * ((column == row ? w : 0.0) + d[row]*gradient[column]);
  float detJ = determinant(J);
  if (detJ <= 0.05 || isnan(detJ) || isinf(detJ)) return;
  mat3 covariance = mat3(
    splat.xxyyzz.x, splat.xyxzyz.x, splat.xyxzyz.y,
    splat.xyxzyz.x, splat.xxyyzz.y, splat.xyxzyz.z,
    splat.xyxzyz.y, splat.xyxzyz.z, splat.xxyyzz.z);
  covariance = J * covariance * transpose(J);
  if (any(isnan(covariance[0])) || any(isnan(covariance[1])) || any(isnan(covariance[2]))
      || any(isinf(covariance[0])) || any(isinf(covariance[1])) || any(isinf(covariance[2]))) return;
  splat.center += k*w*d;
  splat.xxyyzz = vec3(covariance[0][0], covariance[1][1], covariance[2][2]);
  splat.xyxzyz = vec3(covariance[0][1], covariance[0][2], covariance[1][2]);
}
`;

export function makeCovarianceGrowth(){
 const center=new dyno.DynoVec3({value:new THREE.Vector3(),key:'raineeGrowthCenter'});
 const radii=new dyno.DynoVec3({value:new THREE.Vector3(1,1,1),key:'raineeGrowthRadii'});
 const growth=new dyno.DynoFloat({value:1,key:'raineeGrowthFactor'});
 const modifier=new dyno.Dyno({
  inTypes:{covsplat:dyno.CovSplat,center:'vec3',radii:'vec3',growth:'float'},
  outTypes:{covsplat:dyno.CovSplat},inputs:{center,radii,growth},
  globals:()=>[dyno.defineGsplat,dyno.defineCovSplat,GLSL_FIELD],
  statements:({inputs,outputs})=>[`${outputs.covsplat} = ${inputs.covsplat};`,`raineeCompactGrowth(${outputs.covsplat}, ${inputs.center}, ${inputs.radii}, ${inputs.growth});`]
 });
 return {modifier,center,radii,growth};
}


// Experimental boundary-moving radial map remains opt-in and unwired.
export {GLSL_SURFACE_FROSTING_FIELD} from './frosting-field.mjs';
