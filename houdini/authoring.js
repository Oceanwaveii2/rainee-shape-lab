import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {cacheFrame,approvedReference,sequenceLabel} from './sequence-preview.mjs';
import {REAR_DEFAULTS,calibrateRear,deformRear,activeRearSamples,screenRear} from './rear-model.mjs';
import {V5_REAR_DEFAULTS,calibrateRearV5,deformRearV5,screenRearV5,fixVdbTriangleWinding,applyViewDependentSilhouetteBuffer} from './curvilinear-rear-v5.mjs';
import {THIGH_DEFAULTS,sculptThighs} from './thigh-model.mjs';

const $=s=>document.querySelector(s),view=$('#view');
let source,tri,used,cageRest,cageTri,geo,body,ghost,cageMesh,samples,config,visibleHeight,visibleMin,ready=false,last,fitPreset,fitBody,seqManifest,seqState,seqRequest=0;
let canonicalAuthoredBuffer=null,flippedVdbCount=0;
const seqBuffers=new Map(),seqRoot='../research/rear-rounding/native-study/accepted-sequence/';
const nativeStates=new Map(),nativeRoot='../research/rear-rounding/native-study/';

const scene=new THREE.Scene();scene.background=new THREE.Color('#14141b');
const camera=new THREE.OrthographicCamera(-1,1,.63,-.63,.01,20);
const renderer=new THREE.WebGLRenderer({antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
view.prepend(renderer.domElement);
const orbit=new OrbitControls(camera,renderer.domElement);
orbit.enableDamping=false;orbit.target.set(0,.51,0);

scene.add(new THREE.HemisphereLight(0xe9e0ff,0x423042,2));
for(const [x,y,z]of [[2,3,-3],[-2,1,2]]){const l=new THREE.DirectionalLight(0xffffff,2.5);l.position.set(x,y,z);scene.add(l)}
scene.add(new THREE.GridHelper(2,20,0x53405d,0x2d2631));

const clayMaterial=new THREE.MeshStandardMaterial({color:0xc9a8cc,roughness:.68,metalness:.04,side:THREE.DoubleSide});
const zebraMaterial=new THREE.ShaderMaterial({
  side:THREE.DoubleSide,
  uniforms:{stripeFreq:{value:14.0}},
  vertexShader:`
    varying vec3 vNormalView;
    varying vec3 vWorldPos;
    void main(){
      vNormalView = normalize(normalMatrix * normal);
      vec4 wp = modelMatrix * vec4(position, 1.0);
      vWorldPos = wp.xyz;
      gl_Position = projectionMatrix * viewMatrix * wp;
    }
  `,
  fragmentShader:`
    uniform float stripeFreq;
    varying vec3 vNormalView;
    varying vec3 vWorldPos;
    void main(){
      vec3 n = normalize(vNormalView);
      float refl = 0.72 * n.y + 0.48 * n.x + 0.35 * abs(n.z);
      float zebra = 0.5 + 0.5 * tanh(3.0 * sin(stripeFreq * 3.14159265 * refl));
      float diff = clamp(dot(n, normalize(vec3(-0.28, 0.45, 0.85))), 0.0, 1.0);
      vec3 baseCol = vec3(0.14, 0.20, 0.30) + 0.45 * diff * vec3(0.35, 0.55, 0.85);
      vec3 stripeCol = vec3(0.93, 0.97, 1.0);
      vec3 col = mix(baseCol, stripeCol, 0.68 * zebra);
      gl_FragColor = vec4(col, 1.0);
    }
  `
});
const toonMaterial=new THREE.ShaderMaterial({
  side:THREE.DoubleSide,
  vertexShader:`
    varying vec3 vNormalWorld;
    varying vec3 vNormalView;
    varying vec3 vLocalPos;
    void main(){
      vLocalPos = position;
      vNormalWorld = normalize(mat3(modelMatrix) * normal);
      vNormalView = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader:`
    varying vec3 vNormalWorld;
    varying vec3 vNormalView;
    varying vec3 vLocalPos;
    void main(){
      vec3 n = normalize(vNormalWorld);
      vec3 lightDir = normalize(vec3(0.35, 0.65, -0.68));
      float ndl = dot(n, lightDir);
      // ArcSys 3-band quantized cel shading + rim highlight
      float cel = ndl > 0.45 ? 1.0 : (ndl > 0.02 ? 0.74 : 0.42);
      float rim = pow(1.0 - clamp(abs(vNormalView.z), 0.0, 1.0), 3.2);
      vec3 base = vec3(0.86, 0.70, 0.89) * cel + (rim > 0.65 ? vec3(0.22, 0.18, 0.28) : vec3(0.0));
      gl_FragColor = vec4(clamp(base, 0.0, 1.0), 1.0);
    }
  `
});

function updateMaterialMode(){
  if(!body)return;
  const mode=$('#shading-mode').value;
  const wf=body.material.wireframe;
  body.material=mode==='zebra'?zebraMaterial:mode==='toon'?toonMaterial:clayMaterial;
  body.material.wireframe=wf;
  $('#toggle-zebra').classList.toggle('active-mode',mode==='zebra');
  $('#toggle-toon').classList.toggle('active-mode',mode==='toon');
  requestRender();
}

function currentCameraYawFromBack(){
  const dx=camera.position.x-orbit.target.x,dz=camera.position.z-orbit.target.z;
  // Angle relative to back view (0, 0, -2)
  return Math.atan2(dx,-dz);
}

function refreshViewDependentDisplay(){
  if(!ready||!canonicalAuthoredBuffer||!geo)return;
  const boost=Number($('#view-dependent-boost')?.value||0);
  $('#value-view-dependent-boost').textContent=boost.toFixed(2);
  const cleftX=Number($('#rear-cleft_x_offset')?.value||0.0122);
  if(boost>0){
    const yaw=currentCameraYawFromBack();
    applyViewDependentSilhouetteBuffer(canonicalAuthoredBuffer,yaw,boost,{cleftX,out:geo.attributes.position.array});
  }else{
    geo.attributes.position.array.set(canonicalAuthoredBuffer);
  }
  geo.attributes.position.needsUpdate=true;
  geo.computeVertexNormals();
}

function angle(name){
  const v={front:[0,.51,2],side:[2,.51,0],back:[0,.51,-2],three:[1.5,.8,-2]}[name];
  camera.position.set(...v);orbit.target.set(0,.51,0);orbit.update();
  refreshViewDependentDisplay();requestRender();
}


let renderScheduled=false;
function requestRender(){
  if(renderScheduled)return;
  renderScheduled=true;
  requestAnimationFrame(()=>{renderScheduled=false;renderer.render(scene,camera)});
}
orbit.addEventListener("change",()=>{
  if(Number($('#view-dependent-boost')?.value||0)>0)refreshViewDependentDisplay();
  requestRender();
});
new ResizeObserver(()=>{
  const w=view.clientWidth,h=view.clientHeight;
  renderer.setSize(w,h);
  camera.left=-.63*w/h;camera.right=.63*w/h;
  camera.updateProjectionMatrix();requestRender();
}).observe(view);
angle('three');

async function get(path,type){
  const r=await fetch(path,{cache:'no-store'});
  if(!r.ok)throw Error('Missing working asset: '+path);
  return r[type]();
}
function values(prefix,defaults){return Object.fromEntries(Object.keys(defaults).map(k=>[k,Number($('#'+prefix+k)?.value??defaults[k])]))}
function set(prefix,vals){for(const[k,v]of Object.entries(vals)){const el=$('#'+prefix+k);if(el)el.value=v}}
function height(p){let lo=Infinity,hi=-Infinity;for(const id of used){lo=Math.min(lo,p[id*3+1]);hi=Math.max(hi,p[id*3+1])}return hi-lo}

function apply(){
  if(!ready)return;
  const mode=$('#shape-mode').value,thigh=values('thigh-',THIGH_DEFAULTS);
  let ratio=Number($('#rear-volume').value),rear=values('rear-',mode==='curvilinear-v5'?V5_REAR_DEFAULTS:REAR_DEFAULTS);
  try{
    let solve,screen,authored;
    if(mode==='sequence'){
      const f=cacheFrame($('#source-frame').value);
      if(!seqState||seqState.source_frame!==f){$('#status').textContent='Loading native growth frame…';return}
      ratio=seqState.authored_cage_ratio;rear={...V5_REAR_DEFAULTS,...REAR_DEFAULTS};
      solve={cage:seqState.cageBuffer,ratio:seqState.actual_native_cage_ratio};
      screen={minimum:seqState.native_roi_minimum_jacobian,nonpositive:seqState.native_roi_nonpositive_jacobians};
      authored=seqState.bodyBuffer;
    }else if(mode==='figurine'){
      ratio=fitPreset.parameters.volume;
      const {volume,...shape}=fitPreset.parameters;
      rear={...V5_REAR_DEFAULTS,...REAR_DEFAULTS,...shape};
      solve=calibrateRear(cageRest,cageTri,ratio,rear);
      screen=screenRear(samples,solve.amplitude,rear);
      authored=fitBody;
    }else if(mode==='rounded'){
      const state=nativeStates.get(ratio);
      if(!state)throw Error('Select a native rounded-pole study state (1.0, 1.5, 2.0, or 2.5).');
      solve={cage:state.cage,ratio:state.actual_native_cage_ratio};
      screen={minimum:state.native_roi_minimum_jacobian,nonpositive:state.native_roi_negative_jacobians};
      authored=state.body;
    }else if(mode==='curvilinear-v5'){
      solve=calibrateRearV5(cageRest,cageTri,ratio,rear,{steps:12});
      screen=screenRearV5(samples,solve.amplitude,rear,{steps:12});
      authored=deformRearV5(source,solve.amplitude,rear,{steps:12,isCage:false});
    }else{
      solve=calibrateRear(cageRest,cageTri,ratio,rear);
      screen=screenRear(samples,solve.amplitude,rear);
      authored=deformRear(source,solve.amplitude,rear);
    }
    if(screen.nonpositive||screen.minimum<.025)throw Error('This setting folds the growth field; restored the last accepted shape.');
    if(!canonicalAuthoredBuffer)canonicalAuthoredBuffer=new Float32Array(source.length);
    sculptThighs(source,authored,thigh,canonicalAuthoredBuffer);
    refreshViewDependentDisplay();
    geo.computeBoundingSphere();
    cageMesh.geometry.attributes.position.array.set(solve.cage);
    cageMesh.geometry.attributes.position.needsUpdate=true;
    cageMesh.geometry.computeBoundingSphere();

    const h=height(canonicalAuthoredBuffer);
    $('#height').textContent=(h/visibleHeight*config.height_source_units).toFixed(6)+' units';
    $('#drift').textContent=((h/visibleHeight-1)*100).toFixed(5)+'%';
    const modeTitle=mode==='curvilinear-v5'?'Curvilinear v5 (Pelvis-Aligned Cusp)':mode==='sequence'?sequenceLabel($('#source-frame').value):mode==='rounded'?'Native rounded poles':mode==='figurine'?'Provisional figurine projection':'Legacy v4 direct';
    $('#status').textContent=`${modeTitle} · rear ${ratio.toFixed(2)}× · thighs ${thigh.fullness.toFixed(2)} · min det(J) ${screen.minimum.toFixed(3)}`;
    $('#field').textContent=screen.minimum.toFixed(3);
    $('#measured-volume').textContent=solve.ratio.toFixed(3)+'×';
    for(const [k,v]of Object.entries({...rear,volume:ratio})){
      const out=$('#value-rear-'+k);
      if(out)out.textContent=Number(v).toFixed(k==='cleft_x_offset'?4:2);
    }
    for(const[k,v]of Object.entries(thigh))$('#value-thigh-'+k).textContent=v.toFixed(2);
    last={mode,ratio,rear,thigh,frame:Number($('#source-frame').value)};
    $('#hip-link').href='../documentation/LOCAL_DATA.md';
    $('#hip-link').textContent='Native scenes and local data ↗';
    if(mode==='sequence')updateAcceptedReference();
    requestRender();
  }catch(e){
    if(last){$('#source-frame').value=last.frame;$('#shape-mode').value=last.mode;$('#rear-volume').value=last.ratio;set('rear-',last.rear);set('thigh-',last.thigh)}
    $('#status').textContent=e.message;
  }
}

const queue=()=>{clearTimeout(queue.timer);queue.timer=setTimeout(apply,70)};
function geometry(p,t){
  const g=new THREE.BufferGeometry();
  g.setAttribute('position',new THREE.BufferAttribute(new Float32Array(p),3));
  g.setIndex(new THREE.BufferAttribute(t,1));
  g.computeVertexNormals();
  return g;
}

async function init(){
  config=await get('viewer-config.json','json');
  const[p,t,cp,ct,flow]=await Promise.all([
    get(config.body,'arrayBuffer'),
    get(config.triangles,'arrayBuffer'),
    get('cage-rest.bin','arrayBuffer'),
    get('cage-triangles.bin','arrayBuffer'),
    get(nativeRoot+'verification-native-flow.json','json')
  ]);
  source=new Float32Array(p);
  const rawTri=new Uint32Array(t);
  // Fix D-04: Orient the 51,907 left-handed Houdini VDB triangles (>=98078) to right-handed outward winding
  tri=new Uint32Array(rawTri);
  flippedVdbCount=0; // Original indices preserved; radial normal heuristic is not a certified repair.
  used=Array.from(new Set(tri));
  visibleHeight=height(source);
  visibleMin=Infinity;
  for(const id of used)visibleMin=Math.min(visibleMin,source[id*3+1]);
  cageRest=new Float32Array(cp);
  cageTri=new Uint32Array(ct);
  samples=activeRearSamples(source);

  await Promise.all(flow.states.map(async state=>{
    const[b,c]=await Promise.all([get(nativeRoot+state.body,'arrayBuffer'),get(nativeRoot+state.cage,'arrayBuffer')]);
    const positions=new Float32Array(b);
    if(positions.length!==source.length)throw Error('Native study topology mismatch');
    nativeStates.set(state.ratio,{...state,body:positions,cage:new Float32Array(c)});
  }));
  const [fp,fb]=await Promise.all([get('../measurements/reference-fit/parameter-preset-candidate.json','json'),get('body-figurine-native.bin','arrayBuffer')]);
  fitPreset=fp;fitBody=new Float32Array(fb);
  if(fitBody.length!==source.length)throw Error('Figurine trial topology mismatch');
  seqManifest=await get(seqRoot+'preview-manifest.json','json');
  seqState=await readSequenceState(Number($('#source-frame').value));

  geo=geometry(source,tri);
  body=new THREE.Mesh(geo,clayMaterial);
  scene.add(body);
  ghost=new THREE.Mesh(geometry(source,tri),new THREE.MeshBasicMaterial({wireframe:true,color:0x8de3d6,transparent:true,opacity:.14,depthWrite:false}));
  ghost.visible=false;scene.add(ghost);
  cageMesh=new THREE.Mesh(geometry(cageRest,cageTri),new THREE.MeshBasicMaterial({color:0x8de3d6,wireframe:true,transparent:true,opacity:.5,depthWrite:false}));
  cageMesh.visible=false;scene.add(cageMesh);

  for(const mesh of [body,ghost,cageMesh]){mesh.scale.setScalar(1/visibleHeight);mesh.position.y=-visibleMin/visibleHeight}
  $('#repair-status').textContent=config.repair_status+' Original triangle indices preserved; winding review remains open.';
  $('#hip-link').href=config.scene;
  ready=true;
  $('#edit-controls').disabled=false;
  modeControls();
  apply();
  const v=await get('verification-v4.json','json');
  $('#verification').textContent=`${v.static.length} historical repaired-body combinations and 27 native growth frames. Experimental v5 controls use sampled determinant checks; anatomy and contact remain unverified.`;
}

document.querySelectorAll('[data-sculpt]').forEach(e=>e.oninput=queue);
document.querySelectorAll('[data-view]').forEach(e=>e.onclick=()=>angle(e.dataset.view));
$('#shading-mode').onchange=updateMaterialMode;
$('#toggle-zebra').onclick=()=>{$('#shading-mode').value=$('#shading-mode').value==='zebra'?'clay':'zebra';updateMaterialMode()};
$('#toggle-toon').onclick=()=>{$('#shading-mode').value=$('#shading-mode').value==='toon'?'clay':'toon';updateMaterialMode()};
$('#view-dependent-boost').oninput=()=>{refreshViewDependentDisplay();requestRender()};

function modeControls(){
  if($('#shape-mode').value!=='sequence'){clearTimeout(refreshSequence.timer);seqRequest++}
  const mode=$('#shape-mode').value;
  const rounded=mode==='rounded',fit=mode==='figurine',sequence=mode==='sequence',v5=mode==='curvilinear-v5';
  const volume=$('#rear-volume');
  volume.disabled=fit||sequence;
  $('#source-frame').disabled=!sequence;
  document.querySelectorAll('[data-frame]').forEach(e=>e.disabled=!sequence);
  if(sequence){set('rear-',{...V5_REAR_DEFAULTS,...REAR_DEFAULTS});if(seqState)volume.value=seqState.authored_cage_ratio}
  volume.max=rounded?2.5:3;
  volume.step=rounded?.5:.01;
  if(fit){volume.value=fitPreset.parameters.volume;const {volume:fitVolume,...fitShape}=fitPreset.parameters;set('rear-',{...V5_REAR_DEFAULTS,...REAR_DEFAULTS,...fitShape})}
  if(rounded){volume.value=Math.min(2.5,Math.round(Number(volume.value)*2)/2);set('rear-',{...V5_REAR_DEFAULTS,...REAR_DEFAULTS})}
  if(v5&&last?.mode!=='curvilinear-v5')set('rear-',V5_REAR_DEFAULTS);
  document.querySelectorAll('#rear-shape-controls input').forEach(e=>e.disabled=rounded||fit||sequence);
}
$('#shape-mode').onchange=()=>{modeControls();if($('#shape-mode').value==='sequence')refreshSequence();else apply()};

async function readSequenceState(frame){
  const f=cacheFrame(frame);
  if(seqBuffers.has(f)){const state=seqBuffers.get(f);seqBuffers.delete(f);seqBuffers.set(f,state);return state}
  const row=seqManifest.states.find(s=>s.source_frame===f);
  if(!row)throw Error('Missing native frame '+f);
  const[b,c]=await Promise.all([get(seqRoot+row.body,'arrayBuffer'),get(seqRoot+row.cage,'arrayBuffer')]);
  const state={...row,bodyBuffer:new Float32Array(b),cageBuffer:new Float32Array(c)};
  if(state.bodyBuffer.length!==source.length)throw Error('Sequence topology mismatch');
  seqBuffers.set(f,state);
  while(seqBuffers.size>3)seqBuffers.delete(seqBuffers.keys().next().value);
  return state;
}

function updateAcceptedReference(){
  const f=Number($('#source-frame').value),id=approvedReference(f);
  $('#value-source-frame').textContent=String(Math.round(f)).padStart(4,'0');
  $('#sequence-note').textContent=(f>26?'Endpoint held from 0026. Later deflation is excluded. ':'Accepted growth through 0026. ')+'Cage ratios are an initial sculpt schedule, pending silhouette fitting.';
  if($('#reference-choice').value==='accepted'){
    $('#reference-image').src='../references/accepted-growth/frame_'+String(id).padStart(4,'0')+'.png';
    $('#reference-caption').textContent=f>26?'Frame '+String(Math.round(f)).padStart(4,'0')+' uses the accepted 0026 endpoint.':'Accepted reference '+String(id).padStart(4,'0')+'; images guide anatomy and face.';
  }
}

async function refreshSequence(){
  if($('#shape-mode').value!=='sequence')return;
  const ticket=++seqRequest;
  updateAcceptedReference();
  $('#status').textContent='Loading native growth frame…';
  try{
    const state=await readSequenceState(Number($('#source-frame').value));
    if(ticket!==seqRequest||$('#shape-mode').value!=='sequence')return;
    seqState=state;modeControls();apply();
  }catch(e){
    if(ticket===seqRequest&&$('#shape-mode').value==='sequence')$('#status').textContent=e.message;
  }
}

$('#source-frame').oninput=()=>{clearTimeout(refreshSequence.timer);refreshSequence.timer=setTimeout(refreshSequence,65)};
document.querySelectorAll('[data-frame]').forEach(e=>e.onclick=()=>{$('#source-frame').value=e.dataset.frame;refreshSequence()});
$('#v5-study').onclick=()=>{$('#shape-mode').value='curvilinear-v5';set('rear-',V5_REAR_DEFAULTS);$('#rear-volume').value=2.5;modeControls();apply()};
$('#fit-study').onclick=()=>{$('#shape-mode').value='figurine';modeControls();apply()};
$('#round-study').onclick=()=>{$('#shape-mode').value='rounded';set('rear-',{...V5_REAR_DEFAULTS,...REAR_DEFAULTS});$('#rear-volume').value=2.5;modeControls();apply()};
$('#baseline').onclick=()=>{
  if(['figurine','sequence'].includes($('#shape-mode').value)){$('#shape-mode').value='direct';modeControls()}
  set('rear-',$('#shape-mode').value==='curvilinear-v5'?V5_REAR_DEFAULTS:REAR_DEFAULTS);set('thigh-',THIGH_DEFAULTS);$('#rear-volume').value=1;apply();
};
$('#thigh-study').onclick=()=>{set('thigh-',{...THIGH_DEFAULTS,fullness:.65});apply()};
$('#reset-thighs').onclick=()=>{set('thigh-',THIGH_DEFAULTS);apply()};
$('#ghost').onclick=()=>{if(ghost){ghost.visible=!ghost.visible;requestRender()}};
$('#cage').onclick=()=>{if(cageMesh){cageMesh.visible=!cageMesh.visible;requestRender()}};
$('#wire').onclick=()=>{if(body){body.material.wireframe=!body.material.wireframe;requestRender()}};
$('#reference-choice').onchange=e=>{
  if(e.target.value==='accepted'){updateAcceptedReference();return}
  const data={
    rear:['../research/rear-growth-review/grok-01-0.500s.png','Early Grok growth: rounded upper and lower poles. Camera and stature drift later in the clip.'],
    thigh:['../research/thigh-reference-review/frame-06.jpg','Thigh reference: upper-to-middle mass and knee taper, designed separately.'],
    source:['../references/native-rear.png','Original sculpt supplies stature. Face identity follows the newer images; structural gaps and surface artifacts require repair.']
  }[e.target.value];
  $('#reference-image').src=data[0];$('#reference-caption').textContent=data[1];
};
$('#obj').onclick=()=>{
  if(!ready)return;
  try{
    const coordinates=$('#export-coordinates').value,sourceScale=coordinates==='source',scale=(sourceScale?config.height_source_units:1)/visibleHeight,origin=sourceScale?config.source_origin:[0,0,0];
    // Always export canonicalAuthoredBuffer (excluding view-dependent camera cheat!)
    const p=canonicalAuthoredBuffer||geo.attributes.position.array,remap=new Uint32Array(source.length/3),lines=[`# Rainee working mesh (${last.mode}); ${sourceScale?'FBX source stature and origin; physical unit unknown':'normalized stature H=1'}`];
    used.forEach((id,j)=>{remap[id]=j+1;lines.push(`v ${p[id*3]*scale+origin[0]} ${(p[id*3+1]-visibleMin)*scale+origin[1]} ${p[id*3+2]*scale+origin[2]}`)});
    for(let i=0;i<tri.length;i+=3)lines.push(`f ${remap[tri[i]]} ${remap[tri[i+1]]} ${remap[tri[i+2]]}`);
    const url=URL.createObjectURL(new Blob([lines.join('\n')+'\n'],{type:'text/plain'})),a=document.createElement('a');
    a.href=url;a.download=`Rainee-${last.mode}${last.mode==='sequence'?'-frame-'+String(last.frame).padStart(4,'0'):''}-rear-${last.ratio.toFixed(2)}-thigh-${last.thigh.fullness.toFixed(2)}-${coordinates}.obj`;
    a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
    $('#status').textContent='Exported canonical OBJ with '+(sourceScale?'FBX source stature':'normalized height')+' (view-dependent display offset excluded)';
  }catch(e){$('#status').textContent='OBJ export failed: '+e.message}
};
init().catch(e=>$('#status').textContent=e.message);
