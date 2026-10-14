import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {sculptThighs} from './thigh-model.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
function read(file){const b=fs.readFileSync(path.join(root,file));return new Float32Array(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength))}
const source=read('body-1x.bin'),report=JSON.parse(fs.readFileSync(path.join(root,'verification-thighs.json')));
report.browser_formula_checks=[];
for(const e of report.exports){const actual=read(e.file),a=sculptThighs(source,read(e.authored_file),e.controls);let max=0;for(let i=0;i<a.length;i++)max=Math.max(max,Math.abs(a[i]-actual[i]));if(max>2e-7)throw Error(`Preview differs from native VEX: ${e.file}: ${max}`);report.browser_formula_checks.push({file:e.file,max_position_difference:max})}
report.browser_formula_passed=true;fs.writeFileSync(path.join(root,'verification-thighs.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report.browser_formula_checks,null,2));
