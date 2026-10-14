import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {createHash} from 'node:crypto';import {gunzipSync} from 'node:zlib';import assert from 'node:assert/strict';
import {field,createField,determinant3,determinantBound,transportCovariance,validateControls} from './math.mjs';
import {makeCovarianceGrowth} from './covariance-modifier.mjs';
import {dyno,SplatMesh} from '@sparkjsdev/spark';
const here=path.dirname(fileURLToPath(import.meta.url)),assets=path.resolve(here,'../../measurements/worldgen-20261013'),hash=b=>createHash('sha256').update(b).digest('hex'),start=performance.now();
let seed=77219;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
const I=[[1,0,0],[0,1,0],[0,0,1]];let maxJacobianError=0,maxDeterminantError=0,maxSymmetryError=0,minCovarianceDeterminant=Infinity,numericCases=0;
for(const growth of [1,1.01,1.5,2,2.25])for(const radii of [[1,1,1],[.03,.17,.51],[1.2,.08,.13]])for(let n=0;n<160;n++){
 const center=[.15,-.2,-1.1],p=radii.map((r,i)=>center[i]+(random()*2.6-1.3)*r),f=field(p,center,radii,growth);validateControls(center,radii,growth);
 assert(f.determinant>=determinantBound(growth)-1e-10);
 const det=determinant3(f.J);maxDeterminantError=Math.max(maxDeterminantError,Math.abs(det-f.determinant));assert(Math.abs(det-f.determinant)<1e-10);
 if(growth===1||f.q>=1){assert.deepEqual(f.point,p);assert.deepEqual(f.J,I)}
 for(let axis=0;axis<3;axis++){
  const eps=radii[axis]*1e-5,a=[...p],b=[...p];a[axis]+=eps;b[axis]-=eps;
  const pa=field(a,center,radii,growth).point,pb=field(b,center,radii,growth).point;
  for(let i=0;i<3;i++)maxJacobianError=Math.max(maxJacobianError,Math.abs((pa[i]-pb[i])/(2*eps)-f.J[i][axis]));
 }
 // Independent nonspherical positive-definite covariance A A^T.
 const A=[[.012,.007,.003],[.002,.004,-.006],[.001,.003,.016]],cov=A.map(a=>A.map(b=>a.reduce((s,v,i)=>s+v*b[i],0))),transformed=transportCovariance(cov,f.J);
 for(let i=0;i<3;i++)for(let j=0;j<3;j++)maxSymmetryError=Math.max(maxSymmetryError,Math.abs(transformed[i][j]-transformed[j][i]));
 const determinant=determinant3(transformed);minCovarianceDeterminant=Math.min(minCovarianceDeterminant,determinant);assert(transformed[0][0]>0&&transformed[0][0]*transformed[1][1]-transformed[0][1]**2>0&&determinant>0);
 assert(Math.abs(determinant/(determinant3(cov)*det*det)-1)<1e-8);numericCases++;
}
assert(maxJacobianError<2e-7);assert(maxSymmetryError<1e-14);
assert.throws(()=>validateControls([0,0,0],[1,1,1],2.6));assert.throws(()=>validateControls([0,0,0],[1,0,1],1));assert.throws(()=>validateControls([NaN,0,0],[1,1,1],1));
assert.throws(()=>field([0,0,0],[0,0,0],[1,1,1],2.6));assert.throws(()=>field([NaN,0,0],[0,0,0],[1,1,1],1));
const frozenCenter=[0,0,0],frozenRadii=[1,1,1],fixedField=createField(frozenCenter,frozenRadii,1.5),fixedPoint=[.1,.2,.3],expectedFixed=fixedField(fixedPoint);
frozenCenter[0]=100;frozenRadii[1]=.0001;assert.deepEqual(fixedField(fixedPoint),expectedFixed);assert.deepEqual(fixedPoint,[.1,.2,.3]);
// No additional discontinuity at the support: displacement and derivative
// both approach identity from within. Identity is exact outside.
const boundary=[];for(const e of [1e-2,1e-3,1e-4,1e-5]){const p=[1-e,0,0],f=field(p,[0,0,0],[1,1,1],2.25);boundary.push({epsilon:e,displacement:Math.abs(f.point[0]-p[0]),J_error:Math.abs(f.J[0][0]-1)})}
assert(boundary.every((r,i)=>i===0||r.displacement<boundary[i-1].displacement));assert(boundary.at(-1).J_error<1e-7);
// Whole SPZ payload remains read-only. Inspect every stored centre under a
// deliberately artificial test region; this is NOT an anatomical selection.
const inventory=JSON.parse(fs.readFileSync(path.join(assets,'inventory.json'))),asset=inventory.unique_spz.find(a=>a.id.startsWith('spz-04-')),source=path.join(assets,asset.path),bytes=fs.readFileSync(source),before=hash(bytes),raw=gunzipSync(bytes);
assert.equal(before,asset.sha256);assert.equal(hash(raw),asset.header.raw_payload_sha256);assert.equal(raw.readUInt32LE(0),0x5053474e);assert.equal(raw.readUInt32LE(4),3);const count=raw.readUInt32LE(8),bits=raw[13],lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity],factor=2**-bits;
assert.equal(count,asset.header.num_points);assert(raw.length>=16+count*9);
function position(i){return [0,1,2].map(k=>{const o=16+i*9+k*3;let v=raw[o]|raw[o+1]<<8|raw[o+2]<<16;if(v&0x800000)v-=0x1000000;return v*factor})}
for(let i=0;i<count;i++){const p=position(i);for(let k=0;k<3;k++){lo[k]=Math.min(lo[k],p[k]);hi[k]=Math.max(hi[k],p[k])}}
const testCenter=lo.map((v,i)=>(v+hi[i])/2),testRadii=lo.map((v,i)=>(hi[i]-v)*.32),testField=createField(testCenter,testRadii,2.25);let selected=0,outside=0,minimumSampledDeterminant=Infinity,maxOutputSupportQ=0;
for(let i=0;i<count;i++){const p=position(i),f=testField(p);assert(f.point.every(Number.isFinite));assert(Number.isFinite(f.determinant)&&f.determinant>0);minimumSampledDeterminant=Math.min(minimumSampledDeterminant,f.determinant);if(f.q<1){selected++;const outputQ=f.point.reduce((s,v,k)=>s+((v-testCenter[k])/testRadii[k])**2,0);maxOutputSupportQ=Math.max(maxOutputSupportQ,outputQ);assert(outputQ<=1+1e-12)}else{outside++;assert.deepEqual(f.point,p)}}
assert.equal(hash(fs.readFileSync(source)),before);
// Compile the actual vendored Spark covariance generator graph to GLSL.
// This checks API/typed graph integration; a GPU shader compile is separate.
const pipeline=makeCovarianceGrowth(),mesh=new SplatMesh({extSplats:true,covSplats:true,lod:false});await mesh.initialized;mesh.covObjectModifiers=[pipeline.modifier];mesh.context.splats=mesh.extSplats;mesh.constructCovGenerator(mesh.context);assert(mesh.covGenerator&&!mesh.generator);
const template=new dyno.DynoProgramTemplate('precision highp float;\nprecision highp int;\n{{ GLOBALS }}\nout vec4 color;\nvoid main(){\n CovSplat result;\n {{ STATEMENTS }}\n color=result.rgba;\n}');
const program=new dyno.DynoProgram({graph:mesh.covGenerator,inputs:{index:'0'},outputs:{covsplat:'result'},template});assert(program.shader.includes('raineeCompactGrowth'));assert(program.shader.includes('J * covariance * transpose(J)'));assert(program.shader.includes('growth == 1.0'));assert(Object.values(program.uniforms).some(u=>u===pipeline.growth.uniform));fs.writeFileSync(path.join(here,'shader-audit.glsl'),program.shader);mesh.dispose();
const sparkPackage=path.resolve(here,'../../vendor/spark/package.json'),sparkModule=path.resolve(here,'../../vendor/spark/spark.module.js');
const report={passed:true,created_utc:new Date().toISOString(),elapsed_ms:performance.now()-start,numeric_cases:numericCases,analytic_finite_difference_J_max_error:maxJacobianError,analytic_explicit_det_max_error:maxDeterminantError,anisotropic_covariance_symmetry_max_error:maxSymmetryError,anisotropic_covariance_minimum_determinant:minCovarianceDeterminant,neutral_identity:true,outside_identity:true,public_controls_guarded:true,fixed_field_copies_controls:true,boundary_checks:boundary,maximum_growth:2.25,analytic_determinant_lower_bound:determinantBound(2.25),source_asset:asset.id,source_sha256:before,source_raw_payload_sha256:hash(raw),source_point_count:count,source_payload_unchanged:true,artificial_region:{center:testCenter,radii:testRadii,selected_centres:selected,outside_centres:outside,minimum_sampled_determinant:minimumSampledDeterminant,maximum_output_normalized_support_q:maxOutputSupportQ,support_boundary_fixed:true,anatomical_selection:false},spark_version:JSON.parse(fs.readFileSync(sparkPackage,'utf8')).version,spark_module_sha256:hash(fs.readFileSync(sparkModule)),actual_vendored_covariance_generator_to_GLSL:true,shader_audit_scope:'Generated Dyno graph fragment; renderer common definitions and GPU compilation are separate',gpu_shader_compile:false,browser_render_verified:false,limits:'Numeric and actual Spark graph generation checks. GPU compilation/render requires browser verification. Fixed-boundary compact appearance redistribution, not support enlargement. Nonlinear covariance transport is first-order, exact for local affine linearization; no anatomical volume, semantic segmentation, or source-frame provenance claim.'};
fs.writeFileSync(path.join(here,'verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
