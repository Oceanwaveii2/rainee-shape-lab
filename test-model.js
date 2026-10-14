import assert from 'node:assert/strict';
import fs from 'node:fs';
import {defaults,study,specs,landmarks,deform,section,validatePreset} from './model.js';
const bytes=fs.readFileSync(new URL('./assets/positions.bin',import.meta.url));const base=new Float32Array(bytes.buffer,bytes.byteOffset,bytes.byteLength/4).slice();
const ib=fs.readFileSync(new URL('./assets/triangles.bin',import.meta.url));const indices=new Uint32Array(ib.buffer,ib.byteOffset,ib.byteLength/4).slice();
assert(indices.every(i=>i<base.length/3));assert(base.every(Number.isFinite));
const out=new Float32Array(base.length);deform(base,out,defaults);assert.deepEqual(out,base,'Neutral must reproduce source proxy exactly');
deform(base,out,study);assert(out.every(Number.isFinite));
let protectedVertices=0;for(let i=0;i<base.length;i+=3){if(base[i+1]>.83||base[i+1]<.30||Math.abs(base[i])>=.23){assert.deepEqual(out.slice(i,i+3),base.slice(i,i+3));protectedVertices++;}}
const originalHip=section(base,indices,defaults.hipY,base),newHip=section(out,indices,defaults.hipY,base),originalWaist=section(base,indices,defaults.waistY,base),newWaist=section(out,indices,defaults.waistY,base);
assert(newHip.width>originalHip.width);assert(newHip.depth>originalHip.depth);assert(newWaist.width<originalWaist.width);
deform(base,out,defaults);assert.deepEqual(out,base,'Reset must be lossless');
for(const [key,,lo,hi] of [...specs,...landmarks])for(const value of [lo,hi]){deform(base,out,{...defaults,[key]:value});assert(out.every(Number.isFinite));}
assert.deepEqual(validatePreset(JSON.parse(JSON.stringify(study))),study);assert.throws(()=>validatePreset({...study,hip:NaN}));assert.throws(()=>validatePreset({...study,height:0}));
const report={passed:true,vertices:base.length/3,triangles:indices.length/3,protectedVertices,originalHip,newHip,originalWaist,newWaist,tests:['identity and reset','finite geometry at each control endpoint','head feet and outstretched arm preservation','hip width and depth increase','waist narrowing','preset roundtrip and invalid-value rejection','index bounds']};
fs.writeFileSync(new URL('./verification.json',import.meta.url),JSON.stringify(report,null,2));console.log(report);
