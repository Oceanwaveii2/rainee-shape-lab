/** Selected engine, saved view and exact rendered/audited geometry consistency. */
import assert from 'node:assert/strict';
import {ANATOMY_DEFAULTS,createAnatomyTemplate,extractAnatomy,extractAnatomyImplicitSkinning,measureAnatomyMesh} from './anatomy-model.mjs';
import {ACCEPTED_FRAMES,THIGH_KEYS,CAMERA_DEFAULTS,POSE_DEFAULTS,createProject,validateProject,viewAt,templateAt,setSolverEngine,extractProjectAnatomy,auditTemplateSequence,storeTemplateStage,previewPositions} from './lab-state.mjs';
import {auditProjectMessage} from './lab-audit-worker.mjs';

const source={bodySha256:'a'.repeat(64),trianglesSha256:'b'.repeat(64),heightSourceUnits:2.3951061964035034,physicalUnits:null};
let count=0;
function check(name,fn){fn();count++;console.log('PASS '+name)}
const original=createProject(source);
check('New recipes select Argon v5; older recipes retain legacy and absent display boost',()=>{
 assert.equal(original.solverEngine,'argon-v5');assert.equal(original.mode,'implicit');
 const older=structuredClone(original);delete older.solverEngine;
 older.referenceViews[26]={camera:{...CAMERA_DEFAULTS},pose:{...POSE_DEFAULTS}};
 const restored=validateProject(JSON.parse(JSON.stringify(older)),source);
 assert.equal(restored.solverEngine,'legacy');assert.equal(viewAt(restored,49).viewCheat,0);
});
const selected=setSolverEngine({...original,mode:'implicit',sequenceAudit:{passed:true}},'v5-contact');
selected.referenceViews[26]={camera:{...CAMERA_DEFAULTS,yaw:140},pose:{...POSE_DEFAULTS},viewCheat:.8};
const restored=validateProject(JSON.parse(JSON.stringify(selected)),source);
check('Engine and endpoint view correction survive project JSON round trip',()=>{
 assert.equal(restored.solverEngine,'v5-contact');assert.deepEqual(viewAt(restored,26),viewAt(restored,49));
 assert.equal(viewAt(restored,49).viewCheat,.8);assert.equal(selected.sequenceAudit,undefined);
});
check('Imported engine and display corrections are range checked; stale audits discarded',()=>{
 for(const solverEngine of ['unknown',null])assert.throws(()=>validateProject({...original,solverEngine},source),/solver engine/i);
 for(const viewCheat of [-.1,1.6,null]){const bad=structuredClone(selected);bad.referenceViews[26].viewCheat=viewCheat;assert.throws(()=>validateProject(bad,source),/silhouette boost/i)}
 const stale=validateProject({...selected,sequenceAudit:{passed:true,solverEngine:'legacy'}},source);assert.equal(stale.sequenceAudit,undefined);
});
check('Both engine choices dispatch to exactly the corresponding rendered extractor',()=>{
 for(const [engine,extractor]of [['legacy',extractAnatomy],['v5-contact',extractAnatomyImplicitSkinning]]){
  const project=setSolverEngine(original,engine),parameters=templateAt(project,26),actual=extractProjectAnatomy(project,parameters,{resolution:12}),expected=extractor(createAnatomyTemplate(parameters),{resolution:12});
  assert.deepEqual(actual.positions,expected.positions);assert.deepEqual(actual.triangles,expected.triangles);
 }
});
check('Each engine holds actual endpoint geometry and shares thighs across accepted stages',()=>{
 for(const engine of ['legacy','v5-contact']){
  const project=setSolverEngine(original,engine),changed=storeTemplateStage(project,26,{...templateAt(project,26),thighFullness:1.08},{audit:false});
  assert.equal(changed.sequenceAudit,undefined);
  for(const f of [...ACCEPTED_FRAMES,49])for(const k of THIGH_KEYS)assert.equal(templateAt(changed,f)[k],changed.thighParams[k]);
  const a=extractProjectAnatomy(changed,templateAt(changed,26),{resolution:12}),b=extractProjectAnatomy(changed,templateAt(changed,49),{resolution:12});
  assert.deepEqual(a.positions,b.positions);assert.deepEqual(a.triangles,b.triangles);
 }
});
check('27 sampled audits identify the selected engine and report that engine geometry',()=>{
 for(const engine of ['legacy','v5-contact']){
  const project=setSolverEngine(original,engine),audit=auditTemplateSequence(project,{resolution:12}),endpoint=measureAnatomyMesh(extractProjectAnatomy(project,templateAt(project,26),{resolution:12}));
  assert.equal(audit.solverEngine,engine);assert.equal(audit.states.length,27);assert.equal(audit.states.at(-1).volumeH3,endpoint.volume);assert.equal(audit.endpointHold,true);
 }
});
check('Background worker audits the selected experimental extractor rather than legacy',()=>{
 const reply=auditProjectMessage({id:7,project:restored});assert.equal(reply.id,7);assert.equal(reply.error,undefined);
 assert.equal(reply.audit.solverEngine,'v5-contact');
 const experimental=measureAnatomyMesh(extractProjectAnatomy(restored,templateAt(restored,26),{resolution:24}));
 const legacy=measureAnatomyMesh(extractAnatomy(createAnatomyTemplate(templateAt(restored,26)),{resolution:24}));
 assert.equal(reply.audit.states.at(-1).volumeH3,experimental.volume);assert.notEqual(experimental.volume,legacy.volume);
});
check('Display boost changes a preview copy while canonical measurement/export positions stay exact',()=>{
 const canonical=new Float32Array([-.08,.61,-.12,.08,.61,-.12,.015,.62,-.1]),snapshot=canonical.slice(),view=viewAt(restored,49);
 const preview=previewPositions(canonical,view);assert.notStrictEqual(preview,canonical);assert.notDeepEqual(preview,canonical);assert.deepEqual(canonical,snapshot);
 const neutral=previewPositions(canonical,{...view,viewCheat:0});assert.deepEqual(neutral,canonical);
 const wrapped=previewPositions(canonical,{...view,camera:{...view.camera,yaw:-140}});assert.notDeepEqual(wrapped,canonical);assert.deepEqual(canonical,snapshot);
});
console.log(JSON.stringify({passed:true,testCount:count,scope:'Actual selected regional extraction and 27 discrete audit states, recipe round trip and independent preview buffers; no continuous topology or anatomical accuracy claim.'}));
