/** Exact Argon v5 preset authority, migration and actual selected-surface audits. */
import assert from 'node:assert/strict';
import {ARGON_V5_STAGES,evaluateArgonV5Field,extractArgonV5Surface} from './argon-curvilinear-v5.mjs';
import {measureAnatomyMesh} from './anatomy-model.mjs';
import {ACCEPTED_FRAMES,SOLVER_ENGINES,THIGH_KEYS,CAMERA_DEFAULTS,POSE_DEFAULTS,createProject,validateProject,templateAt,viewAt,useArgonV5Stages,extractProjectAnatomy,auditTemplateSequence,previewPositions} from './lab-state.mjs';

const source={bodySha256:'a'.repeat(64),trianglesSha256:'b'.repeat(64),heightSourceUnits:2.3951061964035034,physicalUnits:null};
const expected={
 0:{rearProjection:1,lobeWidth:1,upperPole:1.08,lowerPole:1,cleft:.75,contactBulge:.5,lobeHeight:1.12},
 10:{rearProjection:1.22,lobeWidth:1.14,upperPole:1.18,lowerPole:1.12,cleft:.85,contactBulge:.75,lobeHeight:1.12},
 18:{rearProjection:1.38,lobeWidth:1.25,upperPole:1.26,lowerPole:1.20,cleft:.92,contactBulge:.9,lobeHeight:1.12},
 26:{rearProjection:1.55,lobeWidth:1.36,upperPole:1.34,lowerPole:1.28,cleft:.96,contactBulge:1,lobeHeight:1.12}
};
let count=0;
function check(name,fn){const start=performance.now();fn();count++;console.log('PASS '+name+' ('+Math.round(performance.now()-start)+'ms)')}
const project=createProject(source),originalSnapshot=JSON.stringify(project);

check('New consolidated projects default to the exact Argon v5 stage schedule',()=>{
 assert.equal(project.mode,'implicit');assert.equal(project.solverEngine,'argon-v5');
 assert.deepEqual(ACCEPTED_FRAMES,[0,10,18,26]);
 for(const engine of ['legacy','v5-contact','argon-v5'])assert.ok(SOLVER_ENGINES.includes(engine));
 for(const f of ACCEPTED_FRAMES)for(const [key,value]of Object.entries(expected[f])){
  assert.equal(ARGON_V5_STAGES[f][key],value,'Standalone authority '+f+': '+key);
  assert.equal(templateAt(project,f)[key],value,'Initial recipe '+f+': '+key);
 }
 assert.deepEqual(project.source,source);assert.equal(project.physicalUnits,null);
});

check('Older recipes retain their chosen engine and receive only the missing contact default',()=>{
 const old=structuredClone(project);delete old.solverEngine;
 for(const f of ACCEPTED_FRAMES)delete old.templateStages[f].contactBulge;
 const migrated=validateProject(JSON.parse(JSON.stringify(old)),source);
 assert.equal(migrated.solverEngine,'legacy');
 for(const f of ACCEPTED_FRAMES){
  assert.equal(migrated.templateStages[f].contactBulge,.5);
  for(const [key,value]of Object.entries(old.templateStages[f]))assert.equal(migrated.templateStages[f][key],value);
 }
 for(const solverEngine of ['legacy','v5-contact']){
  const saved={...structuredClone(old),solverEngine};
  assert.equal(validateProject(saved,source).solverEngine,solverEngine);
 }
 const broken=structuredClone(old);delete broken.templateStages[18].upperPole;
 assert.throws(()=>validateProject(broken,source),/Complete finite|stage|upperPole/i);
});

check('Contact bulge is interpolated between the accepted stages and held after 0026',()=>{
 for(const [frame,value]of [[5,.625],[14,.825],[22,.95]])assert.ok(Math.abs(templateAt(project,frame).contactBulge-value)<1e-12);
 assert.equal(templateAt(project,49).contactBulge,1);
 const restored=validateProject(JSON.parse(JSON.stringify(project)),source);
 assert.deepEqual(restored.templateStages,project.templateStages);
 assert.equal(restored.solverEngine,'argon-v5');
});

check('Resetting the Argon schedule preserves source, shared thighs and saved views',()=>{
 const prior=structuredClone(project);prior.solverEngine='legacy';
 prior.templateStages[26].rearProjection=.6;
 prior.thighParams={thighFullness:1.18,thighOuter:1.12,thighFront:1.06,kneeTaper:.72};
 prior.referenceViews[26]={camera:{...CAMERA_DEFAULTS,yaw:140},pose:{...POSE_DEFAULTS,arch:4},viewCheat:.7,status:'artist view hypothesis'};
 prior.sequenceAudit={passed:true,solverEngine:'legacy',stale:true};
 const sourceBefore=structuredClone(prior.source),thighsBefore=structuredClone(prior.thighParams),viewsBefore=structuredClone(prior.referenceViews);
 const reset=useArgonV5Stages(prior);
 assert.equal(reset.solverEngine,'argon-v5');assert.equal(reset.sequenceAudit,undefined);
 assert.deepEqual(reset.source,sourceBefore);assert.deepEqual(reset.thighParams,thighsBefore);assert.deepEqual(reset.referenceViews,viewsBefore);
 for(const f of [...ACCEPTED_FRAMES,49]){
  for(const k of THIGH_KEYS)assert.equal(templateAt(reset,f)[k],thighsBefore[k]);
  for(const [key,value]of Object.entries(expected[Math.min(f,26)]))assert.equal(templateAt(reset,f)[key],value);
 }
 assert.deepEqual(viewAt(reset,26),viewAt(reset,49));
});

check('Selected renderer extraction matches the exact standalone Argon field module',()=>{
 const params=templateAt(project,26),before=JSON.stringify(params);
 const selected=extractProjectAnatomy(project,params,{resolution:24}),direct=extractArgonV5Surface(params,{resolution:24});
 assert.deepEqual(selected.positions,direct.positions);assert.deepEqual(selected.triangles,direct.triangles);
 for(const point of [[0,.61,-.12],[-.09,.58,-.18],[.09,.65,-.14],[0,.516,.005]])assert.ok(Number.isFinite(evaluateArgonV5Field(point,params)));
 assert.equal(JSON.stringify(params),before);assert.equal(JSON.stringify(project),originalSnapshot);
});

let audit;
check('All 27 actual Argon surfaces at resolution24 are closed, connected and ordered',()=>{
 audit=auditTemplateSequence(project,{resolution:24});
 assert.equal(audit.solverEngine,'argon-v5');assert.equal(audit.resolution,24);assert.equal(audit.states.length,27);assert.equal(audit.passed,true);
 assert.deepEqual(audit.states.map(s=>s.sourceFrame),Array.from({length:27},(_,i)=>i));
 let previous=-Infinity;
 for(const state of audit.states){
  assert.equal(state.closed,true);assert.equal(state.connectedComponents,1);
  assert.ok(Number.isFinite(state.volumeH3)&&state.volumeH3>0);
  assert.ok(state.volumeH3+1e-10>=previous,'Nondecreasing actual volume at frame '+state.sourceFrame);
  previous=state.volumeH3;
 }
 const actual=measureAnatomyMesh(extractProjectAnatomy(project,templateAt(project,26),{resolution:24}));
 assert.equal(actual.degenerateTriangles,0);assert.equal(actual.volume,audit.states.at(-1).volumeH3);
 assert.equal(audit.endpointHold,true);
});

check('Actual canonical endpoint geometry and normals remain identical at 0026 and 0049',()=>{
 const a=extractProjectAnatomy(project,templateAt(project,26),{resolution:24}),b=extractProjectAnatomy(project,templateAt(project,49),{resolution:24});
 assert.deepEqual(a.positions,b.positions);assert.deepEqual(a.triangles,b.triangles);assert.deepEqual(a.normals,b.normals);
 assert.equal(project.source.heightSourceUnits,source.heightSourceUnits);assert.equal(JSON.stringify(project),originalSnapshot);
});

check('Pose and view boost modify only copied preview positions used for display',()=>{
 const canonical=extractProjectAnatomy(project,templateAt(project,26),{resolution:24}),snapshot=canonical.positions.slice();
 const view={camera:{...CAMERA_DEFAULTS,yaw:140},pose:{...POSE_DEFAULTS,arch:4},viewCheat:.8};
 const preview=previewPositions(canonical.positions,view);
 assert.notStrictEqual(preview,canonical.positions);assert.notDeepEqual(preview,canonical.positions);
 assert.deepEqual(canonical.positions,snapshot);
 const neutral=previewPositions(canonical.positions,{camera:{...CAMERA_DEFAULTS},pose:{...POSE_DEFAULTS},viewCheat:0});
 assert.deepEqual(neutral,canonical.positions);assert.deepEqual(canonical.positions,snapshot);
 const canonicalVolume=measureAnatomyMesh(canonical).volume;
 assert.equal(canonicalVolume,audit.states.at(-1).volumeH3);
});

console.log(JSON.stringify({passed:true,testCount:count,solverEngine:'argon-v5',resolution:24,scope:'Exact supplied stage presets, backward recipe compatibility, real selected surfaces at 27 integer frames and separate display buffers. No continuous topology, physical dynamics or anatomical acceptance claim.'}));
