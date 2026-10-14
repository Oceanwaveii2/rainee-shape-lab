/** Camera/pose separation and reviewed low-dimensional silhouette fitting.
 * No I/O, neural model, realistic-body prior or imported-camera auto-calibration.
 */
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const unit=a=>{const d=Math.hypot(...a);if(!(d>1e-12))throw new RangeError('Degenerate camera/pose vector');return a.map(v=>v/d);};
const multiply=(A,p)=>[dot(A.slice(0,3),p),dot(A.slice(3,6),p),dot(A.slice(6,9),p)];
function vector3(v,label){if(!v||v.length!==3||Array.from(v).some(x=>!Number.isFinite(x)))throw new RangeError(`Finite 3D ${label} required`);return v;}
function rotationMatrix(pose={}) {
  if(pose.scale!==undefined&&pose.scale!==1)throw new RangeError('Pose cannot rescale canonical anatomy; use separately declared shape parameters');
  if(pose.rotationMatrix){
    const A=Array.from(pose.rotationMatrix);if(A.length!==9||A.some(v=>!Number.isFinite(v)))throw new RangeError('Finite row-major3x3 rotation required');
    const rows=[A.slice(0,3),A.slice(3,6),A.slice(6,9)];
    for(let i=0;i<3;i++)for(let j=0;j<3;j++)if(Math.abs(dot(rows[i],rows[j])-(i===j?1:0))>1e-6)throw new RangeError('Pose matrix must be rigid/orthonormal');
    if(dot(rows[0],cross(rows[1],rows[2]))<0)throw new RangeError('Pose rotation cannot reflect geometry');return A;
  }
  const [x,y,z]=vector3(pose.rotationEuler??[0,0,0],'rotation angles'),cx=Math.cos(x),sx=Math.sin(x),cy=Math.cos(y),sy=Math.sin(y),cz=Math.cos(z),sz=Math.sin(z);
  // Active XYZ rotation: Rz*Ry*Rx, all angles radians.
  return [cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx,
    sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx,-sy,cy*sx,cy*cx];
}
export function applyRigidPose(point,pose={}) {
  vector3(point,'point');const pivot=vector3(pose.pivot??[0,0,0],'pivot'),translation=vector3(pose.translation??[0,0,0],'translation'),p=multiply(rotationMatrix(pose),sub(point,pivot));
  return p.map((v,i)=>v+pivot[i]+translation[i]);
}
export function createCamera({id='camera',type='orthographic',position=[0,.61,1],target=[0,.61,0],up=[0,1,0],
  width=1024,height=1024,verticalSpan=1,fovYDegrees=40,intrinsics=null,near=1e-5,calibrated=false,calibrationProvenance=null}={}) {
  if(!['orthographic','perspective'].includes(type)||!(width>0&&height>0)||![width,height,near].every(Number.isFinite)||near<0)throw new RangeError('Valid camera type, finite viewport and nonnegative near plane required');
  vector3(position,'camera position');vector3(target,'camera target');vector3(up,'camera up');
  const forward=unit(sub(target,position)),right=unit(cross(forward,up)),trueUp=unit(cross(right,forward));
  let fx,fy,cx=width/2,cy=height/2;
  if(type==='orthographic'){if(!(verticalSpan>0)||!Number.isFinite(verticalSpan))throw new RangeError('Finite positive orthographic span required');fx=fy=height/verticalSpan;}
  else{if(!(fovYDegrees>0&&fovYDegrees<179))throw new RangeError('Perspective FOV must be in(0,179)degrees');fx=fy=height/(2*Math.tan(fovYDegrees*Math.PI/360));}
  if(intrinsics){if(type!=='perspective')throw new RangeError('Intrinsics apply to perspective camera');({fx,fy,cx=width/2,cy=height/2}=intrinsics);if(!(fx>0&&fy>0)||![fx,fy,cx,cy].every(Number.isFinite))throw new RangeError('Finite intrinsics and positive focal lengths required');}
  return {id,type,position:Array.from(position),target:Array.from(target),up:Array.from(up),forward,right,trueUp,
    width,height,verticalSpan,fovYDegrees,fx,fy,cx,cy,near,calibrated:Boolean(calibrated),calibrationProvenance,
    pixelsPerWorldRight:type==='orthographic'?fx:null,pixelsPerWorldUp:type==='orthographic'?fy:null,
    coordinateConvention:'Right/up/forward camera basis; positive depth into view; pixel origin top-left',
    measurementScope:calibrated?'Explicit reviewed camera, subject to its declared provenance':'Artist camera hypothesis; not calibrated imported reference'};
}
export function projectPoint(point,camera,{pose=null}={}) {
  vector3(point,'point');
  const world=pose?applyRigidPose(point,pose):Array.from(point),v=sub(world,camera.position),depth=dot(v,camera.forward);
  const x=dot(v,camera.right),y=dot(v,camera.trueUp),den=camera.type==='perspective'?depth:1;
  if(!(depth>camera.near))return {pixel:null,depth,visible:false,inViewport:false,reason:'Point behind near plane',world};
  const pixel=[camera.cx+camera.fx*x/den,camera.cy-camera.fy*y/den];
  return {pixel,depth,visible:true,inViewport:pixel[0]>=0&&pixel[0]<=camera.width&&pixel[1]>=0&&pixel[1]<=camera.height,world};
}
export function projectPoints(positions,camera,{pose=null}={}) {
  if(positions.length%3)throw new TypeError('Flat XYZ points required');
  const pixels=new Float64Array(positions.length/3*2),depths=new Float64Array(positions.length/3),visible=new Uint8Array(positions.length/3);
  for(let i=0;i<positions.length;i+=3){const p=projectPoint([positions[i],positions[i+1],positions[i+2]],camera,{pose});
    depths[i/3]=p.depth;visible[i/3]=p.visible?1:0;pixels[i/3*2]=p.pixel?.[0]??NaN;pixels[i/3*2+1]=p.pixel?.[1]??NaN;}
  return {pixels,depths,visible,geometryMutated:false,poseAppliedForProjectionOnly:Boolean(pose)};
}
export function observationParameterBlocks({identity={},shape={},pose={},camera={},appearance={}}={}) {
  return {identity,shape,pose,camera,appearance,
    policy:'Measure unposed canonical shape. Apply rigid pose and camera only during reprojection. Appearance does not rewrite anatomy.',
    units:'Shape coordinates H=1; source-unit conversion is separate; no inferred physical stature'};
}
function points2D(input){
  if(!input||(!Array.isArray(input[0])&&input.length%2))throw new RangeError('Complete 2D point pairs required');
  const p=Array.isArray(input[0])?input.map(v=>[v[0],v[1]]):Array.from({length:input.length/2},(_,i)=>[input[2*i],input[2*i+1]]);
  if(p.some(v=>v.length!==2||v.some(x=>!Number.isFinite(x))))throw new RangeError('Finite2D points required');return p;
}
function solve(A,b) {
  const n=b.length,M=A.map((row,i)=>[...row,b[i]]);
  for(let k=0;k<n;k++){
    let pivot=k;for(let r=k+1;r<n;r++)if(Math.abs(M[r][k])>Math.abs(M[pivot][k]))pivot=r;
    if(Math.abs(M[pivot][k])<1e-12)return null;[M[k],M[pivot]]=[M[pivot],M[k]];
    const d=M[k][k];for(let c=k;c<=n;c++)M[k][c]/=d;
    for(let r=0;r<n;r++)if(r!==k){const s=M[r][k];for(let c=k;c<=n;c++)M[r][c]-=s*M[k][c];}
  }
  return M.map(row=>row[n]);
}
/** General rotated2D ellipse fit. A fitted contour is NOT a3D body dimension. */
export function fitReviewedEllipseSilhouette(input,{reviewed=false,coverage='unknown',camera=null,weights=null}={}) {
  const points=points2D(input);
  if(weights&&weights.length!==points.length)throw new RangeError('One profile weight required for each point');
  if(points.length<8)return {available:false,status:'insufficient_profile_samples',accepted2D:false};
  const origin=[0,1].map(k=>points.reduce((s,p)=>s+p[k],0)/points.length);
  const scale=Math.sqrt(points.reduce((s,p)=>s+(p[0]-origin[0])**2+(p[1]-origin[1])**2,0)/points.length);
  if(!(scale>1e-12))return {available:false,status:'degenerate_profile',accepted2D:false};
  const ATA=Array.from({length:5},()=>Array(5).fill(0)),ATb=Array(5).fill(0);
  points.forEach((p,i)=>{const x=(p[0]-origin[0])/scale,y=(p[1]-origin[1])/scale,a=[x*x,2*x*y,y*y,x,y],w=weights?.[i]??1;
    if(!(w>=0&&Number.isFinite(w)))throw new RangeError('Nonnegative finite profile weights required');
    for(let r=0;r<5;r++){ATb[r]+=w*a[r];for(let c=0;c<5;c++)ATA[r][c]+=w*a[r]*a[c];}});
  const coefficients=solve(ATA,ATb);
  if(!coefficients)return {available:false,status:'rank_deficient_profile',accepted2D:false};
  const [a,b,c,d,e]=coefficients,det=a*c-b*b,tr=a+c,delta=Math.hypot(a-c,2*b),small=(tr-delta)/2,large=(tr+delta)/2;
  if(!(small>0&&det>0))return {available:false,status:'no_bounded_ellipse',accepted2D:false};
  const center=[-(c*d-b*e)/(2*det),-(-b*d+a*e)/(2*det)],k=1+a*center[0]**2+2*b*center[0]*center[1]+c*center[1]**2;
  if(!(k>0))return {available:false,status:'no_positive_ellipse_radius',accepted2D:false};
  let majorAngleRadians=.5*Math.atan2(2*b,a-c)+Math.PI/2;
  while(majorAngleRadians>Math.PI/2)majorAngleRadians-=Math.PI;
  const radiusMajor=Math.sqrt(k/small)*scale,radiusMinor=Math.sqrt(k/large)*scale,pixelCenter=center.map((v,i)=>v*scale+origin[i]);
  const cosine=Math.cos(majorAngleRadians),sine=Math.sin(majorAngleRadians);
  const halfWidth=Math.hypot(radiusMajor*cosine,radiusMinor*sine),halfHeight=Math.hypot(radiusMajor*sine,radiusMinor*cosine);
  const residuals=points.map(p=>{const x=(p[0]-origin[0])/scale-center[0],y=(p[1]-origin[1])/scale-center[1];return (a*x*x+2*b*x*y+c*y*y)/k-1;});
  const fit={available:true,status:reviewed&&coverage==='full-contour'?'reviewed_2d_ellipse':'diagnostic_2d_ellipse',accepted2D:reviewed&&coverage==='full-contour',
    center:pixelCenter,radiusMajor,radiusMinor,majorAngleRadians,widthPixels:2*halfWidth,heightPixels:2*halfHeight,
    implicitResidualRms:Math.sqrt(residuals.reduce((s,v)=>s+v*v,0)/residuals.length),reviewed,coverage,
    quantityScope:'Selected2D ellipse profile; no anatomical dimension, unseen depth, circumference or volume inferred'};
  if(camera?.type==='orthographic'&&camera.calibrated&&fit.accepted2D)
    fit.observableCameraPlaneExtents={available:true,rightSpan:fit.widthPixels/camera.fx,upSpan:fit.heightPixels/camera.fy,unit:'H',
      scope:'Extents along calibrated camera right/up; assign anatomical axes only after pose/orientation review'};
  else fit.observableCameraPlaneExtents={available:false,reason:camera?.type==='perspective'?'Perspective silhouette has depth-dependent scale; no3D span without an appropriate depth model':'Reviewed full contour and calibrated orthographic camera required'};
  return fit;
}

/** Exact orthographic silhouette of a declared ellipsoid, including rigid pose.
 * This small candidate FAMILY is an artist assumption, not an imported anatomy prior.
 */
export function orthographicEllipsoidProfile(candidate,camera,{sampleCount=128,pose=candidate.pose??null}={}) {
  if(camera.type!=='orthographic')return {available:false,reason:'Exact candidate ellipse predictor currently supports orthographic cameras only'};
  const radii=candidate.radii,center=candidate.center??[0,.61,0];
  if(!radii||radii.length!==3||Array.from(radii).some(v=>!(v>0)||!Number.isFinite(v)))throw new RangeError('Finite positive declared ellipsoid radii required');
  if(!Number.isInteger(sampleCount)||sampleCount<8)throw new RangeError('At least 8 silhouette samples required');
  vector3(center,'ellipsoid center');
  const rotation=rotationMatrix(candidate),poseRotation=rotationMatrix(pose??{}),axes=[[radii[0],0,0],[0,radii[1],0],[0,0,radii[2]]]
    .map(p=>multiply(poseRotation,multiply(rotation,p)));
  const projected=projectPoint(center,camera,{pose});if(!projected.visible)return {available:false,reason:'Candidate center behind camera'};
  const depthRadius=Math.hypot(...axes.map(axis=>dot(axis,camera.forward)));
  if(projected.depth-depthRadius<=camera.near)return {available:false,reason:'Candidate crosses near plane; clipped silhouette unsupported'};
  let a=0,b=0,c=0;
  for(const axis of axes){const x=camera.fx*dot(camera.right,axis),y=-camera.fy*dot(camera.trueUp,axis);a+=x*x;b+=x*y;c+=y*y;}
  const tr=a+c,delta=Math.hypot(a-c,2*b),major=Math.sqrt(Math.max(0,(tr+delta)/2)),minor=Math.sqrt(Math.max(0,(tr-delta)/2)),angle=.5*Math.atan2(2*b,a-c);
  const points=[];
  for(let i=0;i<sampleCount;i++){const t=i/sampleCount*Math.PI*2,x=major*Math.cos(t),y=minor*Math.sin(t);
    points.push([projected.pixel[0]+Math.cos(angle)*x-Math.sin(angle)*y,projected.pixel[1]+Math.sin(angle)*x+Math.cos(angle)*y]);}
  const inViewportFraction=points.filter(p=>p[0]>=0&&p[0]<=camera.width&&p[1]>=0&&p[1]<=camera.height).length/points.length;
  return {available:true,points,center:projected.pixel,radiusMajor:major,radiusMinor:minor,majorAngleRadians:angle,inViewportFraction,
    bounds:{min:[projected.pixel[0]-Math.sqrt(a),projected.pixel[1]-Math.sqrt(c)],max:[projected.pixel[0]+Math.sqrt(a),projected.pixel[1]+Math.sqrt(c)]},
    candidateAssumptions:'Declared ellipsoid surface family and optional rigid pose, not fitted anatomical truth',
    calibratedCamera:Boolean(camera.calibrated)};
}
function squaredDistance(a,b){return(a[0]-b[0])**2+(a[1]-b[1])**2;}
export function silhouetteDisagreement(first,second) {
  const a=points2D(first),b=points2D(second);if(!a.length||!b.length)return Infinity;
  const one=(u,v)=>u.reduce((sum,p)=>sum+v.reduce((best,q)=>Math.min(best,squaredDistance(p,q)),Infinity),0)/u.length;
  return Math.sqrt((one(a,b)+one(b,a))/2);
}
export function evaluateDepthCandidates(candidates,observations,{predictor=orthographicEllipsoidProfile,tolerancePixels=2}={}) {
  if(!(tolerancePixels>=0)||!Number.isFinite(tolerancePixels))throw new RangeError('Finite nonnegative fitting tolerance required');
  const calibrated=observations.length>0&&observations.every(o=>o.reviewed&&o.camera.calibrated);
  const evaluations=candidates.map(candidate=>{
    const residuals=observations.map(o=>{const prediction=predictor(candidate,o.camera);return prediction.available?silhouetteDisagreement(prediction.points,o.points):Infinity;});
    const rms=Math.sqrt(residuals.reduce((s,v)=>s+v*v,0)/Math.max(residuals.length,1));
    const withinDeclaredTolerance=residuals.length>0&&residuals.every(v=>v<=tolerancePixels);
    return {id:candidate.id,residualPixels:rms,perObservationResidualPixels:residuals,withinDeclaredTolerance,
      supportedInDeclaredFamily:calibrated&&withinDeclaredTolerance,radii:candidate.radii??null};
  });
  const supported=evaluations.filter(e=>e.supportedInDeclaredFamily);
  return {evaluations,supportedCandidateIds:supported.map(e=>e.id),
    status:!calibrated?'needs_profile_review_or_camera_calibration':supported.length>1&&observations.length===1?'underconstrained_single_view':supported.length>1?'multiple_supported_candidates':supported.length===1?'one_supported_candidate_in_declared_family':'no_candidate_fits_declared_observations',
    unresolvedDepth:supported.length>1,globalShapeUniquenessCertified:false,
    tolerancePixels,thresholdPolicy:'Artist/model acceptance tolerance, not a calibrated probability or confidence interval',
    scope:'Compatibility of explicitly proposed candidate shapes with reviewed observations; no hidden anatomy ground truth'};
}
export function rankNextViews(candidates,cameras,{predictor=orthographicEllipsoidProfile}={}) {
  const rankings=cameras.map(camera=>{
    const profiles=candidates.map(c=>predictor(c,camera)),valid=profiles.filter(p=>p.available&&(p.inViewportFraction??1)===1);let sum=0,pairs=0;
    for(let a=0;a<valid.length;a++)for(let b=a+1;b<valid.length;b++){sum+=silhouetteDisagreement(valid[a].points,valid[b].points);pairs++;}
    const disagreementPixels=pairs?sum/pairs:0;
    const normalizedDisagreement=disagreementPixels/Math.hypot(camera.width,camera.height);
    const coverage=valid.length/Math.max(candidates.length,1);
    return {cameraId:camera.id,disagreementPixels,normalizedDisagreement,validCandidateFraction:coverage,
      score:normalizedDisagreement*coverage,reason:'View separates fully framed proposed silhouettes; no texture/lighting loss used'};
  }).sort((a,b)=>b.score-a.score);
  return {rankings,recommendedCameraId:rankings[0]?.score>1e-9?rankings[0].cameraId:null,
    scope:'Candidate-family geometric disagreement heuristic; not guaranteed information gain',
    prerequisites:'Comparable useful framing, visibility and a consistent shape state; review poses/occlusions before requesting a view'};
}
