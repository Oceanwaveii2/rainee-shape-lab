import assert from 'node:assert/strict';
import {evaluateBoundaryMovingField as field} from './frosting-field.mjs';
const center=[.1,-.2,.3],radii=[.3,.4,.7];
let cases=0,min=Infinity;
for(const g of [.5,1,2.5,3.5])for(let i=0;i<=200;i++){
  const p=[center[0]+radii[0]*i/40,center[1]+radii[1]*.2,center[2]-radii[2]*.1];
  const a=field(p,center,radii,g),eps=1e-6;
  assert(a.determinant>0);min=Math.min(min,a.determinant);
  for(let col=0;col<3;col++){const plus=[...p],minus=[...p];plus[col]+=eps;minus[col]-=eps;const x=field(plus,center,radii,g).position,y=field(minus,center,radii,g).position;for(let row=0;row<3;row++)assert(Math.abs((x[row]-y[row])/(2*eps)-a.jacobian[row][col])<1e-7);}
  cases++;
}
// Old implementation jumped at q=2.25 and folded near q=1.765 at g=3.5.
for(const q of [1.5/.85,2.25]){const p=[center[0]+radii[0]*Math.sqrt(q),center[1],center[2]],a=[...p],b=[...p];a[0]-=1e-8;b[0]+=1e-8;assert(Math.abs(field(a,center,radii,3.5).position[0]-field(b,center,radii,3.5).position[0])<1e-7);assert(field(p,center,radii,3.5).determinant>0);}
assert.throws(()=>field([0,0,0],center,[0,1,1],3.5));
console.log(JSON.stringify({passed:true,cases,minimumDeterminant:min,scope:'CPU analytic Jacobian and continuity; noncompact map, no surface binding or GPU certification'}));
