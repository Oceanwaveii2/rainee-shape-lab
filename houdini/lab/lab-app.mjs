import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {ANATOMY_DEFAULTS,ANATOMY_RANGES,measureAnatomyMesh} from './anatomy-model.mjs';
import {DEFAULT_REAR_ROI,measureRearGeometry,crossSectionSegments,createUnitContext} from './measurement-model.mjs';
import {createCamera,projectPoint,rankNextViews,computeCurvatureComb2D} from './reference-fit-model.mjs';
import {ACCEPTED_FRAMES,THIGH_KEYS,CAMERA_DEFAULTS,POSE_DEFAULTS,cacheFrame,precedingStage,posePoint,posePositions,previewPositions,createProject,templateAt,viewAt,validateProject,validateCamera,validatePose,storeTemplateStage,setSolverEngine,useArgonV5Stages,extractProjectAnatomy} from './lab-state.mjs';
import {V5_REAR_DEFAULTS,calibrateRearV5,deformRearV5,screenRearV5} from '../curvilinear-rear-v5.mjs';
import {ARGON_V5_FIXED_KEYS} from './argon-curvilinear-v5.mjs';
import {activeRearSamples} from '../rear-model.mjs';

const $=s=>document.querySelector(s),host=$('#viewport'),HROOT='../',SEQ='../../research/rear-rounding/native-study/accepted-sequence/';
let sourceConfig,sourceInfo,rawSource,triangles,canonicalSource,cageRest,cageTri,nativeSamples,used,adapter,unitContext,project,activeGeometry,activeFrame,anatomyAudit,dimensions,profiles,manifest,mesh,contextMesh,sectionLines,alternativeMeshes=[],ready=false,requestId=0,resolution=24,lastNativeState;

const auditWorker=new Worker(new URL('./lab-audit-worker.mjs',import.meta.url),{type:'module'}),auditJobs=new Map();let auditId=0;
auditWorker.onmessage=({data})=>{const job=auditJobs.get(data.id);if(job){auditJobs.delete(data.id);data.error?job.reject(Error(data.error)):job.resolve(data.audit)}};
auditWorker.onerror=e=>{for(const job of auditJobs.values())job.reject(Error(e.message));auditJobs.clear()};
function auditProject(project){return new Promise((resolve,reject)=>{const id=++auditId;auditJobs.set(id,{resolve,reject});auditWorker.postMessage({id,project})})}

const nativeCache=new Map(),roi=structuredClone(DEFAULT_REAR_ROI),roiDefaults=structuredClone(DEFAULT_REAR_ROI);
let cameraSettings={...CAMERA_DEFAULTS},pose={...POSE_DEFAULTS},renderScheduled=false,renderCount=0,settingCamera=false;
const renderer=new T.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.localClippingEnabled=true;host.prepend(renderer.domElement);
const scene=new T.Scene();scene.background=new T.Color('#101722');
const ortho=new T.OrthographicCamera(-1,1,.5,-.5,.01,50),perspective=new T.PerspectiveCamera(40,1,.01,50);let camera=ortho;
const orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=false;orbit.enableZoom=false;orbit.enablePan=false;orbit.minPolarAngle=Math.PI/12;orbit.maxPolarAngle=11*Math.PI/12;orbit.target.set(0,.5,0);
scene.add(new T.HemisphereLight(0xe7eaff,0x253540,2));for(const [x,y,z]of [[2,3,-3],[-3,2,2]]){const l=new T.DirectionalLight(0xffffff,2.5);l.position.set(x,y,z);scene.add(l)}
scene.add(new T.GridHelper(1.6,16,0x3a5560,0x243039));

const sourceMaterial=new T.MeshStandardMaterial({color:0xc4adc9,roughness:1,metalness:0,side:T.DoubleSide});
const zebraMaterial=new T.ShaderMaterial({
  side:T.DoubleSide,
  uniforms:{stripeFreq:{value:14.0}},
  vertexShader:`
    varying vec3 vNormalView;
    void main(){
      vNormalView = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader:`
    uniform float stripeFreq;
    varying vec3 vNormalView;
    void main(){
      vec3 n = normalize(vNormalView);
      float refl = 0.72 * n.y + 0.48 * n.x + 0.35 * abs(n.z);
      float zebra = 0.5 + 0.5 * tanh(3.0 * sin(stripeFreq * 3.14159265 * refl));
      float diff = clamp(dot(n, normalize(vec3(-0.28, 0.45, 0.85))), 0.0, 1.0);
      vec3 baseCol = vec3(0.14, 0.20, 0.30) + 0.45 * diff * vec3(0.35, 0.55, 0.85);
      vec3 stripeCol = vec3(0.93, 0.97, 1.0);
      gl_FragColor = vec4(mix(baseCol, stripeCol, 0.68 * zebra), 1.0);
    }
  `
});
const toonMaterial=new T.ShaderMaterial({
  side:T.DoubleSide,
  vertexShader:`
    varying vec3 vNormalWorld;
    varying vec3 vNormalView;
    void main(){
      vNormalWorld = normalize(mat3(modelMatrix) * normal);
      vNormalView = normalize(normalMatrix * normal);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader:`
    varying vec3 vNormalWorld;
    varying vec3 vNormalView;
    void main(){
      vec3 n = normalize(vNormalWorld);
      float ndl = dot(n, normalize(vec3(0.35, 0.65, -0.68)));
      float cel = ndl > 0.45 ? 1.0 : (ndl > 0.02 ? 0.74 : 0.42);
      float rim = pow(1.0 - clamp(abs(vNormalView.z), 0.0, 1.0), 3.2);
      vec3 base = vec3(0.84, 0.70, 0.88) * cel + (rim > 0.65 ? vec3(0.22, 0.18, 0.28) : vec3(0.0));
      gl_FragColor = vec4(clamp(base, 0.0, 1.0), 1.0);
    }
  `
});
let activeMaterial=sourceMaterial;

function status(s,error=false){$('#status').textContent=s;$('#status').style.color=error?'#f3a4aa':''}
function requestRender(){if(renderScheduled)return;renderScheduled=true;requestAnimationFrame(()=>{renderScheduled=false;renderer.render(scene,camera);host.dataset.renderedFrames=String(++renderCount);drawProjection()})}
new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);updateCamera(false);drawSection()}).observe(host);
orbit.addEventListener('change',()=>{if(!settingCamera){const d=camera.position.clone().sub(orbit.target),r=d.length();cameraSettings.yaw=Math.atan2(d.x,d.z)*180/Math.PI;cameraSettings.pitch=Math.asin(d.y/r)*180/Math.PI;cameraSettings.distance=r;cameraSettings.targetX=orbit.target.x;cameraSettings.targetY=orbit.target.y;syncCameraInputs();if(Number($('#view-cheat')?.value||0)>0)applyPose()}requestRender()});
async function get(path,type='json'){const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error('Missing lab asset: '+path);return r[type]()}
async function sha(buffer){return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer)),v=>v.toString(16).padStart(2,'0')).join('')}
function normalize(raw){const out=new Float32Array(raw.length),h=adapter.inputWorkingStature;for(let i=0;i<raw.length;i+=3){out[i]=raw[i]/h;out[i+1]=(raw[i+1]-adapter.footY)/h;out[i+2]=raw[i+2]/h}return out}
function makeGeometry(data){const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(new Float32Array(data.positions),3));g.setIndex(new T.BufferAttribute(new Uint32Array(data.triangles),1));if(data.normals)g.setAttribute('normal',new T.BufferAttribute(new Float32Array(data.normals),3));else g.computeVertexNormals();g.computeBoundingSphere();return g}
function sliders(target,prefix,defs,labels,ranges,oninput){for(const [key,value]of Object.entries(defs)){const [lo,hi,step]=ranges[key],label=document.createElement('label');label.htmlFor=prefix+key;label.append(document.createTextNode(labels[key]||key));const out=document.createElement('output');out.id='value-'+prefix+key;out.textContent=Number(value).toFixed(step<.01?3:2);label.append(out);const input=document.createElement('input');input.type='range';input.min=lo;input.max=hi;input.step=step;input.value=value;input.id=prefix+key;input.oninput=oninput;$(target).append(label,input)}}
function read(prefix,defs){return Object.fromEntries(Object.keys(defs).map(k=>[k,Number($('#'+prefix+k).value)]))}
function write(prefix,values){for(const [k,v]of Object.entries(values)){const el=$('#'+prefix+k);if(el)el.value=v;const out=$('#value-'+prefix+k);if(out)out.textContent=Number(v).toFixed(k==='attachment'?3:2)}}

const anatomyLabels={lobeWidth:'Lobe width',lobeHeight:'Lobe height',rearProjection:'Posterior projection',upperPole:'Upper dorsal shelf',lowerPole:'Underside overhang',separation:'Lobe spacing',attachment:'Attachment blend / H',cleft:'Cleft cusp hold',contactBulge:'Pressed contact bulge',asymmetry:'Right / left asymmetry',pelvisWidth:'Pelvic core width',pelvisDepth:'Pelvic core depth',thighFullness:'Independent thigh mass',thighOuter:'Thigh outer sweep',thighFront:'Thigh front fullness',kneeTaper:'Knee taper'};
sliders('#anatomy-inputs','anatomy-',ANATOMY_DEFAULTS,anatomyLabels,Object.fromEntries(Object.entries(ANATOMY_RANGES).map(([k,r])=>[k,[...r,k==='attachment'?.001:.01]])),()=>{write('anatomy-',read('anatomy-',ANATOMY_DEFAULTS));clearTimeout(rebuild.timer);rebuild.timer=setTimeout(()=>rebuild(true),130)});
sliders('#camera-inputs','camera-',Object.fromEntries(Object.entries(CAMERA_DEFAULTS).filter(([k])=>k!=='type')),{yaw:'Camera yaw',pitch:'Camera pitch',span:'Vertical frame span / H',fov:'Vertical field of view',distance:'Camera distance / H',targetX:'Frame centre X / H',targetY:'Frame centre height / H'}, {yaw:[-180,180,1],pitch:[-75,75,1],span:[.22,2.4,.005],fov:[15,100,1],distance:[.35,8,.01],targetX:[-.7,.7,.005],targetY:[.15,1.2,.005]},()=>{try{cameraSettings=validateCamera({type:$('#camera-type').value,...read('camera-',CAMERA_DEFAULTS)});updateCamera();rememberView(false)}catch(e){status(e.message,true)}});
sliders('#pose-inputs','pose-',POSE_DEFAULTS,{yaw:'Body yaw',tilt:'Body tilt',arch:'Torso arch preview'}, {yaw:[-90,90,1],tilt:[-25,25,1],arch:[-15,15,1]},()=>{try{pose=validatePose(read('pose-',POSE_DEFAULTS));write('pose-',pose);applyPose();rememberView(false)}catch(e){status(e.message,true)}});

function readCamera(){return {type:$('#camera-type').value,...Object.fromEntries(Object.keys(CAMERA_DEFAULTS).filter(k=>k!=='type').map(k=>[k,Number($('#camera-'+k).value)]))}}
for(const el of document.querySelectorAll('#camera-inputs input'))el.oninput=()=>{try{cameraSettings=validateCamera(readCamera());updateCamera();rememberView(false)}catch(e){status(e.message,true)}};
for(const [key,label,value]of [['halfWidth','Half width / H',.22],['low','Region bottom / H',.49],['high','Region top / H',.73],['front','Front limit Z / H',.015]]){const l=document.createElement('label');l.textContent=label;const n=document.createElement('input');n.type='number';n.id='roi-'+key;n.value=value;n.step=.005;l.append(n);$('#roi-inputs').append(l);n.onchange=()=>{try{const half=Number($('#roi-halfWidth').value),lo=Number($('#roi-low').value),hi=Number($('#roi-high').value),front=Number($('#roi-front').value);if(!(half>0&&half<=.5&&lo>=0&&hi<=1&&lo<hi&&Number.isFinite(front)))throw Error('Region requires valid positive width and ordered heights.');roi.x=[-half,half];roi.y=[lo,hi];roi.z=[null,front];measure();updateSection();updateAlternatives();requestRender()}catch(e){status(e.message,true)}}}

function syncCameraInputs(){write('camera-',cameraSettings);$('#camera-type').value=cameraSettings.type;$('#camera-span').disabled=cameraSettings.type==='perspective';$('#camera-fov').disabled=cameraSettings.type==='orthographic';$('#camera-distance').disabled=cameraSettings.type==='orthographic'}
function updateCamera(render=true){if(!host.clientWidth||!host.clientHeight)return;settingCamera=true;const aspect=host.clientWidth/host.clientHeight,s=cameraSettings;camera=s.type==='orthographic'?ortho:perspective;if(camera===ortho){const half=s.span/2;camera.left=-half*aspect;camera.right=half*aspect;camera.top=half;camera.bottom=-half}else{camera.aspect=aspect;camera.fov=s.fov}camera.zoom=1;camera.updateProjectionMatrix();const yaw=s.yaw*Math.PI/180,pitch=s.pitch*Math.PI/180;orbit.object=camera;orbit.target.set(s.targetX,s.targetY,0);camera.position.set(s.targetX+Math.sin(yaw)*Math.cos(pitch)*s.distance,s.targetY+Math.sin(pitch)*s.distance,Math.cos(yaw)*Math.cos(pitch)*s.distance);camera.lookAt(orbit.target);orbit.update();settingCamera=false;syncCameraInputs();if(render)requestRender()}
function referenceCamera(settings=cameraSettings,id='current'){const yaw=settings.yaw*Math.PI/180,pitch=settings.pitch*Math.PI/180;return createCamera({id,type:settings.type,position:[settings.targetX+Math.sin(yaw)*Math.cos(pitch)*settings.distance,settings.targetY+Math.sin(pitch)*settings.distance,Math.cos(yaw)*Math.cos(pitch)*settings.distance],target:[settings.targetX,settings.targetY,0],verticalSpan:settings.span,fovYDegrees:settings.fov,width:1024,height:1024,calibrated:false})}
function rememberView(announce){if(!project)return;project.referenceViews[precedingStage(project.frame)]={camera:{...cameraSettings},pose:{...pose},viewCheat:Number($('#view-cheat').value),status:'artist camera/pose hypothesis; uncalibrated'};persist();if(announce)status('Remembered camera, pose and display boost for reference '+String(precedingStage(project.frame)).padStart(4,'0'))}
function restoreView(view){cameraSettings={...view.camera};pose={...view.pose};write('pose-',pose);$('#view-cheat').value=view.viewCheat??0;$('#value-view-cheat').textContent=Number($('#view-cheat').value).toFixed(2)}
function persist(){try{localStorage.setItem('rainee-shape-lab-project-v1',JSON.stringify(project))}catch{}}

async function loadNative(frame){
  const f=cacheFrame(frame);
  const useV5=$('#solver-engine')?.value==='v5-contact';
  const cacheKey=(useV5?'v5-':'v4-')+f;
  if(nativeCache.has(cacheKey)){const s=nativeCache.get(cacheKey);nativeCache.delete(cacheKey);nativeCache.set(cacheKey,s);return s}
  const row=manifest.states.find(s=>s.source_frame===f);if(!row)throw Error('Native frame missing: '+f);
  let positions;
  if(useV5&&cageRest&&cageTri){
    const ratio=row.authored_cage_ratio;
    const solve=calibrateRearV5(cageRest,cageTri,ratio,V5_REAR_DEFAULTS,{steps:12});
    const screen=screenRearV5(nativeSamples,solve.amplitude,V5_REAR_DEFAULTS,{steps:12});
    if(!Number.isFinite(screen.minimum)||screen.nonpositive||screen.minimum<.025)throw Error('Experimental native field failed sampled Jacobian screening; select Legacy engine.');
    const rawDeformed=deformRearV5(rawSource,solve.amplitude,V5_REAR_DEFAULTS,{steps:12,isCage:false});
    if(!rawDeformed.every(Number.isFinite))throw Error('Experimental native field produced non-finite positions.');
    positions=normalize(rawDeformed);
  }else{
    const buffer=await get(SEQ+row.body,'arrayBuffer');
    positions=normalize(new Float32Array(buffer));
  }
  const state={row,positions,triangles};
  if(state.positions.length!==canonicalSource.length)throw Error('Native topology mismatch');
  nativeCache.set(cacheKey,state);
  while(nativeCache.size>4)nativeCache.delete(nativeCache.keys().next().value);
  return state;
}

function releaseMesh(object){if(object){scene.remove(object);object.geometry.dispose();if(object.material!==sourceMaterial&&object.material!==zebraMaterial&&object.material!==toonMaterial)object.material.dispose()}}

function computeDisplayPositions(positions){return previewPositions(positions,{camera:cameraSettings,pose,viewCheat:Number($('#view-cheat').value)})}

async function rebuild(fromControls=false){
  if(!ready)return;
  const ticket=++requestId;
  const mode=$('#geometry-mode').value;
  const useV5=$('#solver-engine')?.value==='v5-contact',useArgon=$('#solver-engine')?.value==='argon-v5';
  project.mode=mode;project.frame=Number($('#source-frame').value);
  if(fromControls)delete project.sequenceAudit;
  status('Preparing '+(mode==='implicit'?'regional surface':'working character')+'…');
  try{
    let data;
    if(mode==='native'){
      const native=await loadNative(project.frame);
      if(ticket!==requestId)return;
      lastNativeState=native.row;
      data={positions:native.positions,triangles:native.triangles};
      anatomyAudit=null;
    }else{
      const params=fromControls?read('anatomy-',ANATOMY_DEFAULTS):templateAt(project,project.frame);
      write('anatomy-',params);
      const start=performance.now();
      data=extractProjectAnatomy(project,params,{resolution});
      anatomyAudit=measureAnatomyMesh(data);
      anatomyAudit.extractionMilliseconds=performance.now()-start;
      if(!anatomyAudit.closed||anatomyAudit.connectedComponents!==1)throw Error('Regional proposal is not one closed component.');
      lastNativeState=null;
    }
    activeGeometry=data;
    contextMesh.geometry.attributes.position.array.set(posePositions(canonicalSource,pose));
    contextMesh.geometry.attributes.position.needsUpdate=true;
    contextMesh.geometry.computeBoundingSphere();
    releaseMesh(mesh);
    mesh=new T.Mesh(makeGeometry({positions:computeDisplayPositions(data.positions),triangles:data.triangles}),activeMaterial);
    scene.add(mesh);
    contextMesh.visible=mode==='implicit'&&$('#context').checked;
    mesh.material.wireframe=$('#wire').checked;
    $('#anatomy-controls').open=mode==='implicit';
    const editableStage=ACCEPTED_FRAMES.includes(project.frame)||project.frame>26;
    $('#anatomy-inputs').querySelectorAll('input').forEach(el=>{el.disabled=mode!=='implicit'||!editableStage||(useArgon?ARGON_V5_FIXED_KEYS.includes(el.id.replace('anatomy-','')):el.id==='anatomy-contactBulge');el.title=useArgon&&ARGON_V5_FIXED_KEYS.includes(el.id.replace('anatomy-',''))?'Fixed in the supplied Argon v5 field':''});
    for(const id of ['store-stage','refine','reset-shape'])$('#'+id).disabled=mode!=='implicit'||!editableStage;
    host.dataset.proposalVolume=anatomyAudit?String(anatomyAudit.volume):'';
    $('#geometry-note').textContent=mode==='implicit'?(useArgon?'Argon curvilinear v5 · upper shelf, lower overhang and contact bulge.':useV5?'Experimental localized implicit blend and bulge; reference fit pending.':'Legacy smooth-union regional proposal; reference fit pending.'):(useV5?'Experimental curvilinear field with sampled Jacobian checks; reference fit pending.':'Native working character cache (v4); growth schedule is an initialization.');
    $('#growth-note').textContent=(project.frame>26?'0026 endpoint held. ':'Accepted order 0000 → 0010 → 0018 → 0026. ')+(mode==='implicit'?'Regional stages are authored initializations.':'Camera and pose never rewrite canonical stature.');
    host.dataset.geometryMode=mode;
    host.dataset.solverEngine=project.solverEngine;
    host.dataset.viewCheat=String(Number($('#view-cheat').value));
    host.dataset.sourceFrame=String(project.frame);
    host.dataset.cachedFrame=String(cacheFrame(project.frame));
    measure();updateSection();updateAlternatives();updateReference();persist();requestRender();
    status((mode==='implicit'?(useArgon?'Argon v5 regional shape':useV5?'Experimental regional proposal':'Regional proposal'):(useV5?'Experimental curvilinear character':'Working character'))+' · frame '+String(project.frame).padStart(4,'0')+(project.frame>26?' · held from 0026':'')+' · fixed stature '+sourceConfig.height_source_units.toFixed(6)+' source units');
    return true;
  }catch(e){status(e.message,true);return false}
}

function applyPose(){
  if(!activeGeometry||!mesh)return;
  const cheat=Number($('#view-cheat')?.value||0);
  if($('#value-view-cheat'))$('#value-view-cheat').textContent=cheat.toFixed(2);
  mesh.geometry.attributes.position.array.set(computeDisplayPositions(activeGeometry.positions));
  mesh.geometry.attributes.position.needsUpdate=true;
  mesh.geometry.computeVertexNormals();
  mesh.geometry.computeBoundingSphere();
  contextMesh.geometry.attributes.position.array.set(posePositions(canonicalSource,pose));
  contextMesh.geometry.attributes.position.needsUpdate=true;
  contextMesh.geometry.computeBoundingSphere();
  updateSection();updateAlternatives();requestRender();
  host.dataset.poseApplied=JSON.stringify(pose);
  host.dataset.viewCheat=String(cheat);
  status('Pose / silhouette preview updated · canonical anatomy measurements unchanged');
}

function format(v,digits=3){return Number.isFinite(v)?v.toFixed(digits):'—'}
function ledgerRow(label,value){const box=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;box.append(dt,dd);$('#ledger').append(box)}

function measure(){
  if(!activeGeometry)return;
  dimensions=measureRearGeometry(activeGeometry,{roi,sectionHeights:[],unitContext});
  $('#ledger').replaceChildren();
  ledgerRow('Canonical stature',sourceConfig.height_source_units.toFixed(6)+' source units');
  ledgerRow('Height anchor','H = 1 · physical unit uncalibrated');
  const d=dimensions.dimensions;
  ledgerRow('Selected surface width',d?format(d.lateralWidth)+' H':'No region');
  ledgerRow('Selected depth span',d?format(d.posteriorDepthSpan)+' H':'No region');
  ledgerRow('Selected height window',d?format(d.selectedHeight)+' H':'No region');
  ledgerRow('Width in source units',d?format(d.lateralWidth*sourceConfig.height_source_units):'—');
  if(anatomyAudit){
    ledgerRow('Closed proposal volume',format(anatomyAudit.volume,5)+' H³');
    ledgerRow('Proposal topology',anatomyAudit.connectedComponents+' closed component');
    ledgerRow('Surface detail',anatomyAudit.triangles.toLocaleString()+' triangles');
  }else{
    ledgerRow('Anatomical enclosed volume','Unresolved / region is open');
    ledgerRow('Native control volume',format(lastNativeState?.actual_native_cage_ratio)+'× · control only');
  }
  $('#volume-note').textContent=anatomyAudit?'Volume covers the complete regional template, including its pelvic core and thigh transitions.':'The selected body region is clipped/open. No anatomical volume is inferred from the cage ratio or image area.';
  $('#confidence').replaceChildren();
  for(const [title,message]of [['Stature','FBX anchor retained; canonical H=1.'],['Cleft placement','Artist field parameter; anatomical alignment has not been reviewed.'],['Camera / pose','Manually controlled hypotheses; view-dependent boost changes display only. No camera calibration or 3D ratio recovery is claimed.'],['Attachments',anatomyAudit?'Regional implicit proposal; attachment anatomy remains unaccepted.':'Source triangle indices retained; outward orientation is not certified.'],['Region boundaries',dimensions.boundaryLimited?'This window cuts the surface and may include other body surfaces.':'No selected contour touches this window boundary.']]){
    const div=document.createElement('div');div.className='evidence-row';const strong=document.createElement('strong');strong.textContent=title;div.append(strong,document.createTextNode(message));$('#confidence').append(div);
  }
  host.dataset.canonicalStature=String(sourceConfig.height_source_units);
  host.dataset.regionWidth=String(d?.lateralWidth??'');
  host.dataset.regionDepth=String(d?.posteriorDepthSpan??'');
}

let section;
function updateSection(){
  if(!activeGeometry)return;
  const value=Number($('#section-height').value);
  $('#section-value').textContent=value.toFixed(3);
  section=crossSectionSegments(activeGeometry,{axis:'y',value},{roi});
  releaseMesh(sectionLines);
  if(section.segments.length){
    const points=[];
    for(const seg of section.segments)for(const p of seg)points.push(...posePoint(p,pose));
    const g=new T.BufferGeometry();
    g.setAttribute('position',new T.BufferAttribute(new Float32Array(points),3));
    sectionLines=new T.LineSegments(g,new T.LineBasicMaterial({color:0x88ecd3,depthTest:false,transparent:true,opacity:.85}));
    sectionLines.renderOrder=3;
    sectionLines.visible=$('#show-section').checked;
    scene.add(sectionLines);
  }else sectionLines=null;
  $('#section-stats').textContent=section.bounds?format(section.bounds.extent[0])+' H wide · '+format(section.bounds.extent[2])+' H deep':'No intersection in selected region';
  drawSection();requestRender();
}

function drawSection(){
  const c=$('#section-canvas'),r=c.getBoundingClientRect();
  if(!r.width||!r.height)return;
  c.width=Math.round(r.width*devicePixelRatio);c.height=Math.round(r.height*devicePixelRatio);
  const ctx=c.getContext('2d');ctx.scale(devicePixelRatio,devicePixelRatio);
  ctx.clearRect(0,0,r.width,r.height);
  if(!section?.bounds)return;
  const b=section.bounds,w=Math.max(.001,b.extent[0]),d=Math.max(.001,b.extent[2]),scale=Math.min((r.width-56)/w,(r.height-36)/d),cx=(b.min[0]+b.max[0])/2,cz=(b.min[2]+b.max[2])/2;
  ctx.strokeStyle='#30404f';ctx.beginPath();
  ctx.moveTo(r.width/2,0);ctx.lineTo(r.width/2,r.height);
  ctx.moveTo(0,r.height/2);ctx.lineTo(r.width,r.height/2);ctx.stroke();

  // Artist's field offset guide; not a measured anatomical landmark.
  const sulcusPx=r.width/2+(0.0122-cx)*scale;
  ctx.strokeStyle='#3fb950';ctx.setLineDash([4,4]);ctx.lineWidth=1.2;
  ctx.beginPath();ctx.moveTo(sulcusPx,0);ctx.lineTo(sulcusPx,r.height);ctx.stroke();ctx.setLineDash([]);

  // Diagnostic curvature estimate of a smoothed posterior envelope.
  if($('#show-comb')?.checked){
    const comb=computeCurvatureComb2D(section.segments,{cleftX:0.0122,combScale:0.0020});
    for(const lobe of [comb.left,comb.right]){
      if(lobe.length<2)continue;
      ctx.strokeStyle='rgba(242, 204, 96, 0.55)';ctx.lineWidth=1;
      ctx.beginPath();
      for(const spike of lobe){
        ctx.moveTo(r.width/2+(spike.base[0]-cx)*scale,r.height/2+(spike.base[1]-cz)*scale);
        ctx.lineTo(r.width/2+(spike.tip[0]-cx)*scale,r.height/2+(spike.tip[1]-cz)*scale);
      }
      ctx.stroke();
      ctx.strokeStyle='#f2cc60';ctx.lineWidth=1.25;
      ctx.beginPath();
      lobe.forEach((spike,idx)=>{
        const tx=r.width/2+(spike.tip[0]-cx)*scale,ty=r.height/2+(spike.tip[1]-cz)*scale;
        idx?ctx.lineTo(tx,ty):ctx.moveTo(tx,ty);
      });
      ctx.stroke();
    }
  }

  ctx.strokeStyle='#8ce7cf';ctx.lineWidth=1.6;ctx.beginPath();
  for(const [a,b]of section.segments){
    ctx.moveTo(r.width/2+(a[0]-cx)*scale,r.height/2+(a[2]-cz)*scale);
    ctx.lineTo(r.width/2+(b[0]-cx)*scale,r.height/2+(b[2]-cz)*scale);
  }
  ctx.stroke();
  ctx.fillStyle='#a8b5c8';ctx.font='10px system-ui';
  ctx.fillText('posterior −Z ↑ · green = field guide · gold = smoothed curvature estimate',7,12);
}

function regionPoints(){
  if(!activeGeometry)return [];
  const p=activeGeometry.positions,ids=project.mode==='native'?used:Array.from(new Set(activeGeometry.triangles)),out=[];
  for(let i=0;i<ids.length;i++){
    const id=ids[i],v=[p[id*3],p[id*3+1],p[id*3+2]];
    if(v[0]>=roi.x[0]&&v[0]<=roi.x[1]&&v[1]>=roi.y[0]&&v[1]<=roi.y[1]&&v[2]<=roi.z[1])out.push(v);
  }
  return out;
}
function referenceCameraForProjection(settings=cameraSettings,id='current'){
  const yaw=settings.yaw*Math.PI/180,pitch=settings.pitch*Math.PI/180;
  return createCamera({id,type:settings.type,position:[settings.targetX+Math.sin(yaw)*Math.cos(pitch)*settings.distance,settings.targetY+Math.sin(pitch)*settings.distance,Math.cos(yaw)*Math.cos(pitch)*settings.distance],target:[settings.targetX,settings.targetY,0],verticalSpan:settings.span,fovYDegrees:settings.fov,width:1024,height:1024,calibrated:false});
}
function projectedRegion(){
  const c=referenceCameraForProjection(),points=regionPoints(),pixels=[];
  for(let i=0;i<points.length;i+=Math.max(1,Math.floor(points.length/5000))){
    const hit=projectPoint(posePoint(points[i],pose),c);
    if(hit.visible)pixels.push(hit.pixel);
  }
  if(!pixels.length)return null;
  const min=[Infinity,Infinity],max=[-Infinity,-Infinity];
  for(const p of pixels)for(let k=0;k<2;k++){min[k]=Math.min(min[k],p[k]);max[k]=Math.max(max[k],p[k])}
  return {pixels,min,max,width:max[0]-min[0],height:max[1]-min[1],center:min.map((v,i)=>(v+max[i])/2)};
}
function updateReference(){const f=precedingStage(project.frame);activeFrame=profiles.frames.find(x=>x.frame_number===f);$('#frame-value').textContent=String(project.frame).padStart(4,'0');$('#reference-image').src='../../references/accepted-growth/frame_'+String(f).padStart(4,'0')+'.png';drawProjection()}
function drawProjection(){
  if(!activeFrame||!ready)return;
  const canvas=$('#reference-overlay'),size=$('#reference-wrap').clientWidth;
  canvas.width=Math.max(1,Math.round(size*devicePixelRatio));canvas.height=canvas.width;
  const ctx=canvas.getContext('2d');ctx.scale(canvas.width/1024,canvas.height/1024);ctx.clearRect(0,0,1024,1024);
  const projected=projectedRegion(),observed=activeFrame.paired_profile.visible_outside_width_px;
  if($('#show-overlay').checked){
    for(const [name,color]of [['left','#80ead5'],['right','#edcf77']]){
      const curve=activeFrame.lobes[name].selected_outside_curve_px;
      ctx.strokeStyle=color;ctx.lineWidth=4;ctx.beginPath();curve.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke();
    }
    if(projected){ctx.strokeStyle='#e5a7fa';ctx.lineWidth=4;ctx.setLineDash([14,10]);ctx.strokeRect(projected.min[0],projected.min[1],projected.width,projected.height);ctx.setLineDash([])}
  }
  $('#projection-status').textContent=projected?'Reference '+String(activeFrame.frame_number).padStart(4,'0')+' · visible outside width '+observed.toFixed(1)+' px; projected selected-region width '+projected.width.toFixed(1)+' px. Bounds are a proxy, not an occlusion-aware silhouette. Camera/pose uncalibrated.':'No region projects in this camera.';
  host.dataset.projectedWidth=projected?String(projected.width):'';
}
function updateAlternatives(){
  for(const m of alternativeMeshes)releaseMesh(m);alternativeMeshes=[];
  const d=dimensions?.bounds;if(!d)return;
  const centre=d.center,radii=d.extent.map(v=>Math.max(.001,v/2)),candidates=[.8,1,1.2].map(k=>({id:'depth-'+k,center:centre,radii:[radii[0],radii[1],radii[2]*k]}));
  const views=[['rear',180],['side',90],['rear-three-quarter',140]].map(([id,yaw])=>referenceCameraForProjection({...CAMERA_DEFAULTS,type:'orthographic',yaw,pitch:0,span:.55,targetY:centre[1]},id));
  const ranked=rankNextViews(candidates,views);
  $('#next-view').textContent='Suggested next view in canonical pose: '+ranked.recommendedCameraId+'. Declared ±20% ellipsoid-depth alternatives; this compares candidate disagreement, not anatomical confidence.';
  host.dataset.nextView=ranked.recommendedCameraId;
  if(!$('#depth-alternatives').checked)return;
  for(const [factor,color]of [[.8,0x73c8f3],[1.2,0xe8ad87]]){
    const out=new Float32Array(activeGeometry.positions);
    for(let i=0;i<out.length;i+=3){
      const x=out[i],y=out[i+1],z=out[i+2];
      if(x>=roi.x[0]&&x<=roi.x[1]&&y>=roi.y[0]&&y<=roi.y[1]&&z<=roi.z[1]){
        const ty=(y-roi.y[0])/(roi.y[1]-roi.y[0]),tx=(x-roi.x[0])/(roi.x[1]-roi.x[0]),w=Math.sin(Math.PI*ty)**2*Math.sin(Math.PI*tx)**2;
        out[i+2]=z+(z-roi.z[1])*(factor-1)*w;
      }
    }
    const g=makeGeometry({positions:posePositions(out,pose),triangles:activeGeometry.triangles});
    const m=new T.Mesh(g,new T.MeshBasicMaterial({color,wireframe:true,transparent:true,opacity:.12,depthWrite:false}));
    scene.add(m);alternativeMeshes.push(m);
  }
}
function download(name,data,type='application/json'){const url=URL.createObjectURL(new Blob([typeof data==='string'?data:JSON.stringify(data,null,2)],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000)}
function exportObj(){
  if(!activeGeometry)return;
  const p=activeGeometry.positions,t=activeGeometry.triangles,ids=Array.from(new Set(t)),remap=new Map(ids.map((id,i)=>[id,i+1])),h=sourceInfo.heightSourceUnits,o=sourceConfig.source_origin,lines=['# Rainee canonical UNPOSED geometry; source physical unit unknown','# '+(project.mode==='implicit'?'Closed regional artist proposal, not full-body geometry or accepted anatomy':'Working body with fixed FBX source stature'),'# H=1 reference stature = '+h+' source units'];
  for(const id of ids)lines.push('v '+[p[id*3]*h+o[0],p[id*3+1]*h+o[1],p[id*3+2]*h+o[2]].join(' '));
  for(let i=0;i<t.length;i+=3)lines.push('f '+[remap.get(t[i]),remap.get(t[i+1]),remap.get(t[i+2])].join(' '));
  download('Rainee-Lab-'+project.mode+'-'+String(project.frame).padStart(4,'0')+'-canonical.obj',lines.join('\n')+'\n','text/plain');
  status('Exported canonical '+(project.mode==='implicit'?'regional proposal':'body')+' · viewport pose excluded');
}

$('#geometry-mode').onchange=()=>{if($('#geometry-mode').value==='native'&&project.solverEngine==='argon-v5'){project=setSolverEngine(project,'legacy');$('#solver-engine').value='legacy'}resolution=24;rebuild()};
$('#solver-engine').onchange=async()=>{const previous=project;project=setSolverEngine(project,$('#solver-engine').value);if(project.solverEngine==='argon-v5'){$('#geometry-mode').value='implicit';project.mode='implicit'}$('#editing').disabled=true;try{if(!await rebuild()){project=previous;$('#solver-engine').value=previous.solverEngine;persist()}}finally{$('#editing').disabled=false}};
$('#argon-stages').onclick=async()=>{const previous=project;$('#editing').disabled=true;try{const next=useArgonV5Stages(project);status('Checking Argon v5 growth stages…');next.sequenceAudit=await auditProject(next);project=next;$('#geometry-mode').value='implicit';$('#solver-engine').value='argon-v5';resolution=24;await rebuild()}catch(e){project=previous;status(e.message,true)}finally{$('#editing').disabled=false}};
$('#source-frame').oninput=()=>{clearTimeout(rebuild.timer);rebuild.timer=setTimeout(()=>{restoreView(viewAt(project,Number($('#source-frame').value)));updateCamera();rebuild()},80)};
for(const b of document.querySelectorAll('[data-frame]'))b.onclick=()=>{$('#source-frame').value=b.dataset.frame;$('#source-frame').oninput()};
for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>{const v={front:[0,3],side:[90,3],back:[180,3],three:[140,9]}[b.dataset.view];cameraSettings.yaw=v[0];cameraSettings.pitch=v[1];updateCamera();if(Number($('#view-cheat')?.value||0)>0)applyPose();rememberView(false)};
$('#camera-type').onchange=()=>{cameraSettings.type=$('#camera-type').value;updateCamera();measure();rememberView(false)};
$('#reference-framing').onclick=()=>{cameraSettings={...cameraSettings,span:.74,targetX:0,targetY:.71,distance:2.4,fov:24};updateCamera();rememberView(false);status('Manual torso/rear framing applied · geometry unchanged')};
$('#align-bounds').onclick=()=>{try{if(cameraSettings.type!=='orthographic')throw Error('Bounds alignment currently requires orthographic projection.');if(Math.abs(Math.sin(cameraSettings.yaw*Math.PI/180))>.05)throw Error('Bounds alignment requires a front/rear view; side framing needs an explicit depth translation. Use manual camera controls.');const p=projectedRegion();if(!p||p.width<=0)throw Error('No projected rear region.');const curves=Object.values(activeFrame.lobes).flatMap(l=>l.selected_outside_curve_px),xs=curves.map(p=>p[0]),ys=curves.map(p=>p[1]),observed=Math.max(...xs)-Math.min(...xs),centre=[(Math.max(...xs)+Math.min(...xs))/2,(Math.max(...ys)+Math.min(...ys))/2],span=cameraSettings.span*p.width/observed;if(span<.22||span>2.4)throw Error('Required framing exceeds allowed span; review region/shape/pose.');cameraSettings.span=span;const newP=projectedRegion(),c=referenceCameraForProjection();const dx=(newP.center[0]-centre[0])/1024*span,dy=(centre[1]-newP.center[1])/1024*span;cameraSettings.targetX=Math.max(-.7,Math.min(.7,cameraSettings.targetX+c.right[0]*dx+c.trueUp[0]*dy));cameraSettings.targetY=Math.max(.15,Math.min(1.2,cameraSettings.targetY+c.right[1]*dx+c.trueUp[1]*dy));updateCamera();rememberView(false);status('Aligned projected width/centre · camera hypothesis changed; anatomy unchanged')}catch(e){status(e.message,true)}};
$('#reset-pose').onclick=()=>{pose={...POSE_DEFAULTS};write('pose-',pose);if($('#view-cheat'))$('#view-cheat').value=0;applyPose();rememberView(false)};
$('#view-cheat').oninput=()=>{applyPose();rememberView(false)};
$('#section-height').oninput=()=>{clearTimeout(updateSection.timer);updateSection.timer=setTimeout(updateSection,90)};
$('#show-section').onchange=()=>{if(sectionLines)sectionLines.visible=$('#show-section').checked;requestRender()};
$('#show-comb').onchange=()=>drawSection();
$('#show-overlay').onchange=requestRender;
$('#depth-alternatives').onchange=()=>{updateAlternatives();requestRender()};
$('#wire').onchange=()=>{if(mesh)mesh.material.wireframe=$('#wire').checked;requestRender()};
$('#context').onchange=()=>{if(contextMesh)contextMesh.visible=project.mode==='implicit'&&$('#context').checked;requestRender()};

function setShader(mat){
  activeMaterial=mat;
  if(mesh){const wf=mesh.material.wireframe;mesh.material=mat;mesh.material.wireframe=wf}
  requestRender();
}
$('#clay').onclick=()=>{sourceMaterial.color.set('#c4bfc2');sourceMaterial.roughness=1;sourceMaterial.metalness=0;setShader(sourceMaterial);status('Switched to Neutral Studio Clay shader')};
$('#zebra-mode').onclick=()=>{setShader(activeMaterial===zebraMaterial?sourceMaterial:zebraMaterial);status(activeMaterial===zebraMaterial?'Switched to diagnostic normal stripes':'Restored standard clay shader')};
$('#toon-mode').onclick=()=>{setShader(activeMaterial===toonMaterial?sourceMaterial:toonMaterial);status(activeMaterial===toonMaterial?'Switched to three-band toon preview':'Restored standard clay shader')};

$('#reset-roi').onclick=()=>{Object.assign(roi,structuredClone(roiDefaults));$('#roi-halfWidth').value=.22;$('#roi-low').value=.49;$('#roi-high').value=.73;$('#roi-front').value=.015;measure();updateSection();updateAlternatives();requestRender()};
async function commitTemplate(){if(project.mode!=='implicit')return;const candidate=storeTemplateStage(project,project.frame,read('anatomy-',ANATOMY_DEFAULTS),{audit:false});status('Checking 27 sampled growth states in background…');$('#editing').disabled=true;try{candidate.sequenceAudit=await auditProject(candidate);project=candidate;persist()}finally{$('#editing').disabled=false}}
$('#store-stage').onclick=async()=>{try{await commitTemplate();status('Stored stage '+String(precedingStage(project.frame)).padStart(4,'0')+' and shared thigh controls · all 27 sampled growth volumes ordered')}catch(e){status(e.message,true)}};
$('#refine').onclick=()=>{resolution=40;rebuild(true)};
$('#reset-shape').onclick=async()=>{try{const f=precedingStage(project.frame),initial=createProject(sourceInfo).templateStages[f];for(const k of THIGH_KEYS)initial[k]=project.thighParams[k];const candidate=storeTemplateStage(project,project.frame,initial,{audit:false});$('#editing').disabled=true;status('Checking reset stage in background…');candidate.sequenceAudit=await auditProject(candidate);project=candidate;resolution=24;rebuild()}catch(e){status(e.message,true)}finally{$('#editing').disabled=false}};
$('#save-view').onclick=()=>rememberView(true);$('#export-obj').onclick=exportObj;
$('#save-project').onclick=async()=>{try{if(project.mode==='implicit'&&(ACCEPTED_FRAMES.includes(project.frame)||project.frame>26))await commitTemplate();rememberView(false);project.artistNote=$('#quantity-note').value;download('Rainee-Shape-Lab-project.json',project);status('Saved current stages, shared thighs and independent view states · source geometry unchanged')}catch(e){status(e.message,true)}};
$('#import-project').onclick=()=>$('#project-file').click();
$('#project-file').onchange=async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>2000000)throw Error('Project JSON exceeds the 2 MB recipe limit.');$('#editing').disabled=true;status('Validating project and 27 growth states in background…');const imported=validateProject(JSON.parse(await file.text()),sourceInfo);imported.sequenceAudit=await auditProject(imported);project=imported;$('#geometry-mode').value=project.mode;$('#solver-engine').value=project.solverEngine;$('#source-frame').value=project.frame;$('#quantity-note').value=project.artistNote||'';restoreView(viewAt(project,project.frame));updateCamera();await rebuild();status('Imported project · source hash/stature and selected regional engine checked at 27 sampled states')}catch(error){status(error.message,true)}finally{$('#editing').disabled=false;e.target.value=''}};
$('#save-ledger').onclick=()=>download('Rainee-Dimension-ledger.json',{schema:'rainee-dimension-ledger-v1',source:sourceInfo,mode:project.mode,solverEngine:$('#solver-engine')?.value,sourceFrame:project.frame,endpointCacheFrame:cacheFrame(project.frame),canonicalStatureH:1,roi,dimensions,closedRegionalProposal:anatomyAudit,templateParameters:project.mode==='implicit'?read('anatomy-',ANATOMY_DEFAULTS):null,nativeControlVolumeRatio:lastNativeState?.actual_native_cage_ratio??null,camera:{...cameraSettings,calibrated:false},pose:{...pose,measurementsUsePose:false},evidence:project.evidence,reference:{frame:activeFrame.frame_number,sha256:activeFrame.image.sha256,visibleOutsideWidthPixels:activeFrame.paired_profile.visible_outside_width_px,units:'pixels; not 3D volume'},artistNote:$('#quantity-note').value,physicalUnitCalibration:null});

async function init(){
  sourceConfig=await get(HROOT+'viewer-config.json');
  const[b,t,cp,ct,m,p]=await Promise.all([
    get(HROOT+sourceConfig.body,'arrayBuffer'),
    get(HROOT+sourceConfig.triangles,'arrayBuffer'),
    get(HROOT+'cage-rest.bin','arrayBuffer'),
    get(HROOT+'cage-triangles.bin','arrayBuffer'),
    get(SEQ+'preview-manifest.json'),
    get('../../measurements/five-frame-20261013/profile-fit-candidate/profile-fit-candidate.json')
  ]);
  rawSource=new Float32Array(b);
  triangles=new Uint32Array(t);
  cageRest=new Float32Array(cp);
  cageTri=new Uint32Array(ct);
  nativeSamples=activeRearSamples(rawSource);
  used=Array.from(new Set(triangles));
  let foot=Infinity,top=-Infinity;
  for(const id of used){foot=Math.min(foot,rawSource[id*3+1]);top=Math.max(top,rawSource[id*3+1])}
  adapter={footY:foot,topY:top,inputWorkingStature:top-foot};
  canonicalSource=normalize(rawSource);
  sourceInfo={body:HROOT+sourceConfig.body,triangles:HROOT+sourceConfig.triangles,bodySha256:await sha(b),trianglesSha256:await sha(t),heightSourceUnits:sourceConfig.height_source_units,adapter,physicalUnits:null};
  unitContext=createUnitContext({heightSourceUnits:sourceInfo.heightSourceUnits});
  manifest=m;profiles=p;project=createProject(sourceInfo);
  try{
    const saved=JSON.parse(localStorage.getItem('rainee-shape-lab-project-v1'));
    if(saved){project=validateProject(saved,sourceInfo);project.sequenceAudit=await auditProject(project)}
  }catch{}
  $('#geometry-mode').value=project.mode;
  $('#solver-engine').value=project.solverEngine;
  $('#source-frame').value=project.frame;
  $('#quantity-note').value=project.artistNote||'';
  const view=viewAt(project,project.frame);
  restoreView(view);
  const material=new T.MeshBasicMaterial({color:0x718ca7,wireframe:true,transparent:true,opacity:.12,depthWrite:false});
  contextMesh=new T.Mesh(makeGeometry({positions:posePositions(canonicalSource,pose),triangles}),material);
  contextMesh.visible=false;scene.add(contextMesh);
  ready=true;$('#editing').disabled=false;updateCamera();await rebuild();
  try{
    const checks=await get('measurements/verification.json');
    $('#benchmark-status').textContent=(checks.passed?checks.testCount+' checks passed':'Checks unresolved')+' · known-geometry recovery and camera separation. These checks do not certify the experimental solvers or anatomical accuracy.';
  }catch{$('#benchmark-status').textContent='Benchmark results pending; no calibrated recovery claim.'}
  window.addEventListener('error',e=>status(e.message,true));
  window.addEventListener('unhandledrejection',e=>status(e.reason?.message||String(e.reason),true));
}
init().catch(e=>status(e.message,true));
