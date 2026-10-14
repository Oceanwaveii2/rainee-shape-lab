import assert from 'node:assert/strict';import fs from 'node:fs';import path from 'node:path';import {fileURLToPath} from 'node:url';
import {ANATOMY_DEFAULTS,createAnatomyTemplate,evaluateAnatomy,evaluateAnatomyComponents,extractAnatomy,measureAnatomyMesh,measureAnatomyVoxels,anatomyCrossSection} from './anatomy-model.mjs';
const here=path.dirname(fileURLToPath(import.meta.url)),start=performance.now(),rows=[];
const cases=[
 ['default',{}],['wider',{lobeWidth:1.3}],['taller',{lobeHeight:1.35}],['posterior',{rearProjection:1.5}],
 ['upper-pole',{upperPole:1.35}],['lower-pole',{lowerPole:1.3}],['separated',{separation:1.4,cleft:1}],
 ['thighs',{thighFullness:1.4,thighFront:1.3}],['asymmetric',{asymmetry:.18}],
 ['compact',{lobeWidth:.55,lobeHeight:.65,rearProjection:.55,separation:1.5,attachment:.003}],
 ['thin-thigh-attachment',{thighFullness:.65,thighOuter:.5,thighFront:.5,pelvisWidth:.8,pelvisDepth:.8,attachment:.003}],
 ['expanded',{lobeWidth:1.6,lobeHeight:1.55,rearProjection:2.1,upperPole:1.4,lowerPole:1.4,attachment:.03}]
];
let defaultMesh,refinedMesh,defaultMeasures;
for(const [name,params] of cases){
 const template=createAnatomyTemplate(params),begin=performance.now(),mesh=extractAnatomy(template,{resolution:24}),m=measureAnatomyMesh(mesh);
 assert(mesh.positions.every(Number.isFinite)&&mesh.normals.every(Number.isFinite));assert(m.closed,JSON.stringify({name,...m}));assert(m.connectedComponents===1,JSON.stringify({name,...m}));assert(m.degenerateTriangles===0,JSON.stringify({name,...m}));assert(m.volume>0&&m.signedVolume>0);
 let normalError=0;for(let i=0;i<mesh.normals.length;i+=3)normalError=Math.max(normalError,Math.abs(Math.hypot(mesh.normals[i],mesh.normals[i+1],mesh.normals[i+2])-1));assert(normalError<1e-6);
 assert(mesh.metadata.height_reference_normalized===1&&mesh.metadata.source_height_units===2.3951061964035034);assert(mesh.metadata.anatomical_acceptance===false&&!mesh.metadata.reference_fitted);
 const slice=anatomyCrossSection(mesh,{axis:'y',value:.61});assert(slice.positions.every(Number.isFinite)&&slice.segments.length>0);
 const row={name,parameters:template.params,resolution:24,...m,normal_unit_length_error:normalError,milliseconds:performance.now()-begin,stature_metadata_fixed:true,slice_y_061_bounds:slice.bounds};rows.push(row);console.log(JSON.stringify({name,closed:m.closed,components:m.connectedComponents,volume:m.volume,ms:row.milliseconds}));
 if(name==='default'){defaultMesh=mesh;defaultMeasures=m}
}
const base=createAnatomyTemplate(),wide=createAnatomyTemplate({lobeWidth:1.5,lobeHeight:1.5,rearProjection:2}),thick=createAnatomyTemplate({thighFullness:1.5,thighOuter:1.4,thighFront:1.4});
let independenceCases=0;
for(const point of [[-.09,.405,.028],[.11,.45,.018],[.08,.49,.025],[-.12,.38,.0],[0,.61,-.095],[.08,.63,-.1]]){
 const a=evaluateAnatomyComponents(point,base),b=evaluateAnatomyComponents(point,wide),c=evaluateAnatomyComponents(point,thick);
 assert(a.leftThigh===b.leftThigh&&a.rightThigh===b.rightThigh);assert(a.leftLobe===c.leftLobe&&a.rightLobe===c.rightLobe);assert(a.core===b.core&&a.core===c.core);independenceCases++;
}
for(const point of [[-.09,.405,.028],[.11,.4,.018],[-.12,.38,0]])assert(evaluateAnatomy(point,base)===evaluateAnatomy(point,wide));
for(const point of [[-.08,.63,-.1],[.08,.63,-.1]])assert(evaluateAnatomy(point,base)===evaluateAnatomy(point,thick));
let mirrorError=0;const left=createAnatomyTemplate({asymmetry:-.18}),right=createAnatomyTemplate({asymmetry:.18});
for(let n=0;n<400;n++){const p=[Math.sin(n*.31)*.21,.32+(n%97)/97*.4,-.19+(n%73)/73*.28],mirror=[-p[0],p[1],p[2]];mirrorError=Math.max(mirrorError,Math.abs(evaluateAnatomy(p,base)-evaluateAnatomy(mirror,base)),Math.abs(evaluateAnatomy(p,left)-evaluateAnatomy(mirror,right)))}assert(mirrorError<1e-13);
assert(evaluateAnatomy([0,.61,-.098],createAnatomyTemplate({cleft:0}))!==evaluateAnatomy([0,.61,-.098],createAnatomyTemplate({cleft:1})));
// Both joins penetrate the central core and their own lobe for all tested
// controls. There is no separate detached sphere pretending to be anatomy.
for(const [,params]of cases){const template=createAnatomyTemplate(params);for(const side of [-1,1])assert(evaluateAnatomy([side*.052,.582,-.020],template)<0)}
assert.throws(()=>createAnatomyTemplate({lobeWidth:NaN}));assert.throws(()=>createAnatomyTemplate({height:2}));assert.throws(()=>extractAnatomy(base,{resolution:100}));
refinedMesh=extractAnatomy(base,{resolution:40});const refined=measureAnatomyMesh(refinedMesh),voxels=measureAnatomyVoxels(base,{resolution:48});assert(refined.closed&&refined.connectedComponents===1&&refined.degenerateTriangles===0);
const coarseRefinedRelativeDifference=Math.abs(defaultMeasures.volume/refined.volume-1),voxelMeshRelativeDifference=Math.abs(voxels.volume/refined.volume-1);assert(coarseRefinedRelativeDifference<.12);assert(voxelMeshRelativeDifference<.08);
assert(rows.find(r=>r.name==='wider').volume>defaultMeasures.volume);assert(rows.find(r=>r.name==='posterior').volume>defaultMeasures.volume);assert(rows.find(r=>r.name==='thighs').volume>defaultMeasures.volume);
const report={passed:true,model_status:'editable deterministic regional proposal; not accepted or image fitted',source_assets_modified:false,native_hips_modified:false,source_stature_metadata:base.metadata,states:rows,parameter_independence_cases:independenceCases,independent_components_exact:true,protected_mid_thigh_field_exact:true,protected_deep_lobe_field_exact:true,mirror_symmetry_and_opposite_asymmetry_max_error:mirrorError,cleft_control_changes_field:true,refined:{resolution:40,...refined},voxel_measurement:voxels,coarse_refined_volume_relative_difference:coarseRefinedRelativeDifference,voxel_mesh_volume_relative_difference:voxelMeshRelativeDifference,volume_overlap_policy:'final union mesh integral or one negative-field voxel classification; component volumes are never summed',elapsed_seconds:(performance.now()-start)/1000,limits:'Closed regional template only. Not attached seamlessly to original full body; no anatomy acceptance, surface detail, clothing, skeleton, contact simulation, actual tissue-volume calibration, or full implementation of an academic paper.'};
fs.writeFileSync(path.join(here,'anatomy-model.verification.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({passed:true,elapsed_seconds:report.elapsed_seconds,coarseRefinedRelativeDifference,voxelMeshRelativeDifference,refined_points:refined.points,refined_triangles:refined.triangles}));
