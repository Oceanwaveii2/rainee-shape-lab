/** Synthetic numerical regressions; independent of donor imagery or likeness. */
import assert from 'node:assert/strict';
import {evaluateRationalBicubicNurbs as spline, computeGofRaySurfaceCrossing as crossing,
  transportSurfaceBoundGaussianSplat as transport} from './butt-data-supercomputer-v6.mjs';
const close=(a,b,tolerance=1e-10)=>assert.ok(Math.abs(a-b)<tolerance, `${a} differs from ${b}`);
const grid=Array.from({length:4},(_,i)=>Array.from({length:4},(_,j)=>i+2*j));
for(const [u,v] of [[0,0],[.25,.7],[1,1]]) close(spline(grid,null,u,v),3*u+6*v);
close(spline(Array.from({length:5},()=>Array(6).fill(7)),null,.42,.8),7);
assert.throws(()=>spline([[1,2]],null,0,0));
assert.throws(()=>spline(grid,Array.from({length:4},()=>Array(4).fill(-1)),0,0));
assert.throws(()=>spline(grid,null,NaN,0));
assert.throws(()=>spline(grid,null,0,0,{knotsU:Array(8).fill(0)}));
assert.equal(crossing([{t:2,alpha:.1},{t:3,alpha:.1}],.5),null);
assert.equal(crossing([], .5),null);
close(crossing([{t:4,alpha:.3},{t:2,alpha:.3}],.5),2+(.5-.3)/(.51-.3)*2);
close(crossing([{t:8,alpha:1}],1),8);
assert.throws(()=>crossing([{t:1,alpha:.9}],0));
const cov=[[1,0,0],[0,2,0],[0,0,3]];
const moved=transport([1,2,3],cov,(x,y,z)=>[2*x+1,3*y-2,4*z]);
close(moved.jacobianDeterminant,24,1e-8);
close(moved.covariance[0][0],4,1e-8);close(moved.covariance[1][1],18,1e-8);close(moved.covariance[2][2],48,1e-8);
console.log(JSON.stringify({passed:true,checks:['clamped cubic plane and constant reproduction with exact endpoints',
  'invalid spline grids, weights, knots and parameters rejected','opacity threshold never invents a noncrossing surface',
  'sorted compositing and fully opaque splat threshold','affine first-order covariance transport'],
  scope:'Synthetic helpers only; no GOF density, surface attachment, anatomical volume or foldover guarantee'}));
