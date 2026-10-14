/** Bounded static Houdini delivery; all outputs stay beside this script. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import {createAnatomyTemplate,extractAnatomy,measureAnatomyMesh} from '../anatomy-model.mjs';
const root=path.dirname(fileURLToPath(import.meta.url)),app=path.resolve(root,'../../..');
const sourceHeight=2.3951061964035034,sourceOrigin=[0,-1.220656394958496,.028106868267059326];
async function sha(file){const hash=crypto.createHash('sha256');for await(const part of fs.createReadStream(file))hash.update(part);return hash.digest('hex')}
const protectedFiles=[
 'C:/Users/User/Downloads/Core Body (Template Only).fbx',
 path.join(root,'../anatomy-model.mjs'),
 path.join(app,'houdini/body-v4-rest.bin'),
 path.join(app,'houdini/pelvic-repair/implicit-repaired-triangles.bin')
];
const before=await Promise.all(protectedFiles.map(async file=>({path:file,sha256:await sha(file)})));
const states=[['default',{}],['expanded',{lobeWidth:1.32,lobeHeight:1.25,rearProjection:1.6,upperPole:1.2,lowerPole:1.12,attachment:.018}]],rows=[];
for(const [name,overrides]of states){
 const template=createAnatomyTemplate(overrides),mesh=extractAnatomy(template,{resolution:24}),canonical=measureAnatomyMesh(mesh);
 assert(canonical.closed&&canonical.connectedComponents===1&&canonical.degenerateTriangles===0);
 const positions=new Float32Array(mesh.positions.length);
 for(let i=0;i<positions.length;i++)positions[i]=mesh.positions[i]*sourceHeight+sourceOrigin[i%3];
 const rawNative=measureAnatomyMesh({...mesh,positions});
 // The measurement API assumes canonical coordinates. Correct its unit
 // labels and remove its second H^3 conversion for this source-space mesh.
 const native={...rawNative,volumeUnits:'source native units cubed; physical scale uncalibrated',sourceUnitVolume:rawNative.volume,coordinateSystem:'source native coordinates; canonical H=1 mapped to source',heightReferenceSourceUnits:sourceHeight};assert(native.closed&&native.volume>0);
 assert(Math.abs(native.volume/(canonical.volume*sourceHeight**3)-1)<2e-6);
 const obj=['# Rainee editable regional proposal; static extraction, not accepted/fitted anatomy.','# Source units, +Y up, posterior -Z. No source body attachment or physics.'];
 for(let i=0;i<positions.length;i+=3)obj.push('v '+Array.from(positions.subarray(i,i+3)).join(' '));
 for(let i=0;i<mesh.normals.length;i+=3)obj.push('vn '+Array.from(mesh.normals.subarray(i,i+3)).join(' '));
 for(let i=0;i<mesh.triangles.length;i+=3)obj.push('f '+Array.from(mesh.triangles.subarray(i,i+3),id=>(id+1)+'//'+(id+1)).join(' '));
 fs.writeFileSync(path.join(root,name+'.obj'),obj.join('\n')+'\n');
 fs.writeFileSync(path.join(root,name+'-positions.bin'),Buffer.from(positions.buffer));
 fs.writeFileSync(path.join(root,name+'-triangles.bin'),Buffer.from(mesh.triangles.buffer));
 fs.writeFileSync(path.join(root,name+'-normals.bin'),Buffer.from(mesh.normals.buffer));
 const recipe={schema:'rainee-static-anatomy-recipe-v1',state:name,parameters:template.params,resolution:24,sourceHeight,sourceOrigin,regenerate_with:'node export-proposal.mjs; edit states in that script or call the documented anatomy-model API',geometry_is_static:true,recipe_edits_inside_Houdini_do_not_reextract:true};
 fs.writeFileSync(path.join(root,name+'-recipe.json'),JSON.stringify(recipe,null,2));
 rows.push({name,obj:name+'.obj',recipe:name+'-recipe.json',parameters:template.params,canonical_measurement:canonical,source_coordinate_measurement:native,metadata:mesh.metadata,sha256:await sha(path.join(root,name+'.obj'))});
}
// A wire guide at source X=0, with foot/top crossbars; not geometry stature.
const [ox,oy,oz]=sourceOrigin,top=oy+sourceHeight,w=.06*sourceHeight;
fs.writeFileSync(path.join(root,'source-height-guide.obj'),[
 '# Source-FBX height guide, not regional template bounds.',
 `v ${ox} ${oy} ${oz}`,`v ${ox} ${top} ${oz}`,
 `v ${ox-w} ${oy} ${oz}`,`v ${ox+w} ${oy} ${oz}`,
 `v ${ox-w} ${top} ${oz}`,`v ${ox+w} ${top} ${oz}`,
 'l 1 2','l 3 4','l 5 6',''
].join('\n'));
const manifest={schema:'rainee-static-native-anatomy-proposal-v1',status:'Editable regional proposal; not accepted or image fitted',states:rows,source_height_units:sourceHeight,source_origin:sourceOrigin,transform:'P_source = P_canonical * source_height_units + source_origin',physical_units:null,source_files_before:before,limits:['Closed regional surface only; not the whole body or seamlessly joined to FBX','Two independent static extracted mesh states; topology differs, so no direct blend-shape interpolation','No native analytic/SDF SOP implementation; no physical/contact simulation','No source image fit, tissue-volume certification, or accepted inflation-stage mapping','Recipe fields are editable provenance; changing them in Houdini does not regenerate geometry'],guide:'source-height-guide.obj'};
fs.writeFileSync(path.join(root,'manifest.json'),JSON.stringify(manifest,null,2));
console.log(JSON.stringify({passed:true,states:rows.map(r=>({name:r.name,points:r.source_coordinate_measurement.points,triangles:r.source_coordinate_measurement.triangles,volume:r.source_coordinate_measurement.volume})),sourceHeight,output:root}));
