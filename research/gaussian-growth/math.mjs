// Compact deformation in source coordinates. No whole-scene scale is used.
export const MAX_GROWTH=2.25;
export function validateControls(center,radii,growth){
 if(!center||!radii||center.length!==3||radii.length!==3||!center.every(Number.isFinite)||!radii.every(r=>Number.isFinite(r)&&r>=1e-4))throw Error('Finite centre and radii ≥0.0001 source units are required.');
 if(!Number.isFinite(growth)||growth<1||growth>MAX_GROWTH)throw Error('Growth must stay between1 and2.25; this preserves the analytic determinant bound.');
}
export function determinantBound(growth){
 if(!Number.isFinite(growth)||growth<1||growth>MAX_GROWTH)throw Error('Growth outside the guarded range.');
 return 1-(growth-1)*32/49;
}
function evaluatedField(point,center,radii,growth){
 const d=point.map((v,i)=>v-center[i]),q=d.reduce((s,v,i)=>s+(v/radii[i])**2,0),k=growth-1;
 const J=[[1,0,0],[0,1,0],[0,0,1]];
 if(q>=1||k===0)return {point:[...point],J,q,weight:0,determinant:1};
 const u=1-q,w=u*u*u,gradient=d.map((v,i)=>-6*u*u*v/(radii[i]*radii[i]));
 for(let i=0;i<3;i++)for(let j=0;j<3;j++)J[i][j]+=k*((i===j?w:0)+d[i]*gradient[j]);
 const tangential=1+k*w,radial=1+k*u*u*(1-7*q);
 return {point:point.map((v,i)=>v+k*w*d[i]),J,q,weight:w,determinant:tangential*tangential*radial};
}
// Public scalar calls enforce the same control range as the shader. A fixed
// region can be validated once before a bulk read-only centre inspection.
export function createField(center,radii,growth){
 validateControls(center,radii,growth);const c=Array.from(center),r=Array.from(radii);
 return point=>{if(!point||point.length!==3||!point.every(Number.isFinite))throw Error('Finite source centre required.');return evaluatedField(Array.from(point),c,r,growth)};
}
export function field(point,center,radii,growth){return createField(center,radii,growth)(point)}
export function transportCovariance(cov,J){
 const result=Array.from({length:3},()=>[0,0,0]);
 for(let i=0;i<3;i++)for(let j=0;j<3;j++)for(let a=0;a<3;a++)for(let b=0;b<3;b++)result[i][j]+=J[i][a]*cov[a][b]*J[j][b];
 return result;
}
export function determinant3(m){return m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])-m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])+m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]);}
