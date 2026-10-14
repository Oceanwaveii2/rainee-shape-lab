/** Experimental noncompact radial map. No reconstructed surface or binding.
 * For q = |d/r|^2, F = c + (1 + (g-1)/sqrt(1+q)) d.
 * Tangential/radial eigenvalues are 1+k/sqrt(1+q), 1+k/(1+q)^1.5.
 * Both stay positive for 0.5 <= g <= 3.5. GPU execution remains unverified.
 */
export function evaluateBoundaryMovingField(point,center,radii,growth){
  if(![...point,...center,...radii,growth].every(Number.isFinite)||radii.some(r=>r<1e-4)||growth<.5||growth>3.5)throw Error('Invalid radial map parameters');
  const d=point.map((v,i)=>v-center[i]),q=d.reduce((s,v,i)=>s+(v/radii[i])**2,0),k=growth-1,w=1/Math.sqrt(1+q),scale=1+k*w;
  const gradient=d.map((v,i)=>-v/(radii[i]**2*(1+q)**1.5));
  const jacobian=d.map((v,row)=>gradient.map((a,col)=>(row===col?scale:0)+k*v*a));
  return {position:d.map((v,i)=>center[i]+scale*v),jacobian,determinant:scale*scale*(1+k/(1+q)**1.5)};
}
// Compatibility export name retained from Argon's bundle; not Gaussian Frosting.
export const GLSL_SURFACE_FROSTING_FIELD=`
void raineeSurfaceBoundFrosting(inout CovSplat splat, vec3 centre, vec3 radii, float growth) {
  if (!isCovSplatActive(splat.flags) || growth == 1.0) return;
  if (growth < 0.5 || growth > 3.5 || isnan(growth) || isinf(growth)
      || any(lessThan(radii, vec3(0.0001))) || any(isnan(radii)) || any(isinf(radii))) return;
  vec3 d = splat.center - centre;
  float q = dot(d/radii, d/radii);
  if (isnan(q) || isinf(q)) return;
  float w = inversesqrt(1.0 + q);
  float scale = 1.0 + (growth - 1.0) * w;
  vec3 gradient = -d / (radii*radii) * w*w*w;
  mat3 J = mat3(scale);
  for (int col=0; col<3; ++col)
    for (int row=0; row<3; ++row) J[col][row] += (growth-1.0)*d[row]*gradient[col];
  mat3 covariance = mat3(splat.xxyyzz.x,splat.xyxzyz.x,splat.xyxzyz.y,
    splat.xyxzyz.x,splat.xxyyzz.y,splat.xyxzyz.z,
    splat.xyxzyz.y,splat.xyxzyz.z,splat.xxyyzz.z);
  covariance = J * covariance * transpose(J);
  if (any(isnan(covariance[0])) || any(isnan(covariance[1])) || any(isnan(covariance[2]))
      || any(isinf(covariance[0])) || any(isinf(covariance[1])) || any(isinf(covariance[2]))) return;
  splat.center = centre + scale*d;
  splat.xxyyzz = vec3(covariance[0][0],covariance[1][1],covariance[2][2]);
  splat.xyxzyz = vec3(covariance[0][1],covariance[0][2],covariance[1][2]);
}
`;
