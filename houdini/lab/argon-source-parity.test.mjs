import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {ARGON_V5_SOURCE,evaluateArgonV5Field,extractArgonV5Surface} from './argon-curvilinear-v5.mjs';
const fixture=JSON.parse(fs.readFileSync(new URL('./argon-source-fixtures.json',import.meta.url)));
const sha=a=>crypto.createHash('sha256').update(Buffer.from(a.buffer,a.byteOffset,a.byteLength)).digest('hex');
assert.equal(fixture.sourceSha256,ARGON_V5_SOURCE.sha256);
for(const row of fixture.fixtures){for(const {point,expected}of row.samples)assert.equal(evaluateArgonV5Field(point,row.params),expected);const mesh=extractArgonV5Surface(row.params,{resolution:fixture.resolution});assert.equal(sha(mesh.positions),row.positionSha256);assert.equal(sha(mesh.normals),row.normalSha256);assert.equal(sha(mesh.triangles),row.triangleSha256)}
console.log(JSON.stringify({passed:true,presets:4,fieldSamples:320,sourceSha256:fixture.sourceSha256,scope:'Exact field values and extracted canonical positions/normals/triangles against the supplied standalone source; no anatomy or physics certificate.'}));
