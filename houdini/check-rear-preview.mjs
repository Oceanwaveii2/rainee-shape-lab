import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';import {deformRear,calibrateRear,activeRearSamples,screenRear} from './rear-model.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
function read(f,Type=Float32Array){const b=fs.readFileSync(path.join(root,f));return new Type(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength))}
const base=read('body-1x.bin'),cage=read('cage-rest.bin'),tri=read('cage-triangles.bin',Uint32Array),report=JSON.parse(fs.readFileSync(path.join(root,'verification-rear-v3.json')));
report.browser_formula_checks=[];
for(const row of report.static){const solve=calibrateRear(cage,tri,row.ratio),p=deformRear(base,solve.amplitude),expected=read(`body-v3-${row.ratio}x.bin`);let diff=0;for(let i=0;i<p.length;i++)diff=Math.max(diff,Math.abs(p[i]-expected[i]));if(diff>2e-7)throw Error('Native mismatch: '+diff);report.browser_formula_checks.push({ratio:row.ratio,max_position_difference:diff,cage_ratio:solve.ratio})}
const samples=activeRearSamples(base),unsafe=screenRear(samples,calibrateRear(cage,tri,4).amplitude);if(!unsafe.nonpositive)throw Error('Browser failed to detect unsafe 4x field');report.browser_rejection_check={ratio:4,...unsafe};
report.browser_formula_passed=true;fs.writeFileSync(path.join(root,'verification-rear-v3.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({checks:report.browser_formula_checks,rejection:report.browser_rejection_check},null,2));
