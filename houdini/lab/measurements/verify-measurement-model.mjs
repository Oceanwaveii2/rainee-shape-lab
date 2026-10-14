/** CPU-only scientific verification. Run with Node; no production asset edits. */
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {canonicalizeBodyCoordinates,createUnitContext,convertQuantity,crossSectionSegments,
  inspectMeshTopology,measureEnclosedVolume,measureRearGeometry,recoverOrthographicAxisExtent} from '../measurement-model.mjs';
import {applyRigidPose,createCamera,projectPoint,projectPoints,fitReviewedEllipseSilhouette,
  orthographicEllipsoidProfile,evaluateDepthCandidates,rankNextViews} from '../reference-fit-model.mjs';

const report={schema:'rainee-measurement-synthetic-verification-v1',createdUTC:new Date().toISOString(),
  environment:{runtime:process.version,execution:'CPU-only Node, no browser/native scene or source asset mutation'},
  tests:[],limitations:['Synthetic geometry verifies numerical behavior; it does not establish reference likeness or calibrate imported characters.',
    'Authored growth control 2.5 is not a measured volume. Physical units remain unknown.',
    'Candidate recovery applies only inside the declared ellipsoid family and reviewed camera assumptions.']};
function near(actual,expected,tolerance=1e-9){assert.ok(Math.abs(actual-expected)<=tolerance,`${actual} vs ${expected}, tolerance ${tolerance}`);}
function test(name,run){const start=performance.now();const evidence=run()??{};report.tests.push({name,passed:true,...evidence,elapsedMs:performance.now()-start});}
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),sub=(a,b)=>a.map((v,i)=>v-b[i]),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function ellipsoidMesh(center,radii,{latitude=48,longitude=96,reverse=false}={}){
  const positions=[center[0],center[1]+radii[1],center[2]],triangles=[];
  for(let ring=1;ring<latitude;ring++){const theta=ring*Math.PI/latitude;
    for(let j=0;j<longitude;j++){const phi=j*Math.PI*2/longitude;
      positions.push(center[0]+radii[0]*Math.sin(theta)*Math.cos(phi),center[1]+radii[1]*Math.cos(theta),center[2]+radii[2]*Math.sin(theta)*Math.sin(phi));}}
  const bottom=positions.length/3;positions.push(center[0],center[1]-radii[1],center[2]);
  const point=i=>positions.slice(i*3,i*3+3),ring=(i,j)=>1+(i-1)*longitude+(j%longitude);
  function face(a,b,c){const va=point(a),vb=point(b),vc=point(c),out=sub(va,center),normal=cross(sub(vb,va),sub(vc,va));
    if((dot(normal,out)>0)!==reverse)triangles.push(a,b,c);else triangles.push(a,c,b);}
  for(let j=0;j<longitude;j++){face(0,ring(1,j),ring(1,j+1));face(bottom,ring(latitude-1,j+1),ring(latitude-1,j));}
  for(let i=1;i<latitude-1;i++)for(let j=0;j<longitude;j++){
    face(ring(i,j),ring(i+1,j),ring(i+1,j+1));face(ring(i,j),ring(i+1,j+1),ring(i,j+1));}
  return {positions:new Float64Array(positions),triangles:new Uint32Array(triangles)};
}
function combine(...meshes){const positions=[],triangles=[];for(const mesh of meshes){const offset=positions.length/3;
  positions.push(...mesh.positions);for(const i of mesh.triangles)triangles.push(i+offset);}return {positions:new Float64Array(positions),triangles:new Uint32Array(triangles)};}
const allROI={x:[null,null],y:[null,null],z:[null,null]},clearSingle={selfIntersectionStatus:'known-analytic-simple',componentRelationship:'single'};
const sourceHeight=2.3951061964,units=createUnitContext({heightSourceUnits:sourceHeight});
const center=[0,.61,-.07],radii=[.08,.06,.05],ellipsoid=ellipsoidMesh(center,radii),exactVolume=4*Math.PI/3*radii.reduce((a,b)=>a*b);

test('Explicit canonical adapter preserves stature and uniformly scales all axes',()=>{
  const foot=.00020352914,top=.99903368950,h=top-foot,input=new Float64Array([.16,foot,-.08,-.16,top,.08]),before=Array.from(input);
  const result=canonicalizeBodyCoordinates(input,{footY:foot,topY:top,heightSourceUnits:sourceHeight,reviewedBodyBounds:true});
  near(result.positions[1],0);near(result.positions[4],1);near(result.positions[0],.16/h);assert.deepEqual(Array.from(input),before);
  const converted=convertQuantity(.16,units);near(converted.value,.16*sourceHeight);
  assert.equal(convertQuantity(.16,units,{target:'physical'}).calibrated,false);
  assert.throws(()=>canonicalizeBodyCoordinates(input,{footY:foot,topY:top,heightSourceUnits:sourceHeight}),/reviewed/);
  return {inputWorkingStature:h,canonicalStature:result.positions[4]-result.positions[1],sourceWidth:converted.value,physicalCalibration:'absent'};
});
test('Triangle-plane sections recover central ellipsoid width/depth',()=>{
  const section=crossSectionSegments(ellipsoid,{axis:'y',value:.61},{roi:allROI});
  near(section.bounds.extent[0],.16,1e-12);near(section.bounds.extent[2],.10,1e-12);assert.equal(section.closedLoopCandidate,true);
  const off=crossSectionSegments(ellipsoid,{axis:'y',value:.64},{roi:allROI});
  const exactWidth=.16*Math.sqrt(1-(.03/.06)**2);near(off.bounds.extent[0],exactWidth,1e-4);
  return {centralWidth:section.bounds.extent[0],centralDepth:section.bounds.extent[2],offCenterExpectedWidth:exactWidth,
    offCenterRecoveredWidth:off.bounds.extent[0],offCenterAbsoluteError:Math.abs(off.bounds.extent[0]-exactWidth)};
});
test('ROI clips crossing segments even when original endpoints are outside',()=>{
  const square={positions:[-1,.61,-1,1,.61,-1,1,.61,1,-1,.61,1],triangles:[0,1,2,0,2,3]};
  const full=crossSectionSegments(square,{axis:'y',value:.61},{roi:allROI});
  assert.equal(full.segments.length,4);assert.equal(full.closedLoopCandidate,true);near(full.totalCurveLength,8);
  const clipped=crossSectionSegments(square,{axis:'y',value:.61},{roi:{x:[-.2,.2],y:[null,null],z:[null,null]}});
  assert.equal(clipped.segments.length,2);assert.equal(clipped.closedLoopCandidate,false);near(clipped.bounds.extent[0],.4);near(clipped.totalCurveLength,.8);
  return {coplanarBoundarySegments:full.segments.length,sharedDiagonalRemoved:true,clippedWidth:clipped.bounds.extent[0],clippedCurveLength:clipped.totalCurveLength};
});
test('Selected posterior descriptors and ROI cuts stay distinct from anatomy volume',()=>{
  const selected=measureRearGeometry(ellipsoid,{unitContext:units,sectionHeights:[.55,.61,.67],includeVolumeInspection:true,provenance:clearSingle});
  near(selected.dimensions.lateralWidth,.16);near(selected.dimensions.selectedHeight,.12);near(selected.dimensions.posteriorDepthSpan,.10);
  assert.equal(selected.boundaryLimited,false);assert.equal(selected.enclosedVolume.available,true);
  const cut=measureRearGeometry(ellipsoid,{roi:{x:[-.02,.02],y:[.49,.73],z:[null,.015]},sectionHeights:[.61],includeVolumeInspection:true,provenance:clearSingle});
  assert.equal(cut.boundaryLimited,true);assert.ok(cut.clippedTriangles>0);assert.equal(cut.enclosedVolume.available,false);near(cut.dimensions.lateralWidth,.04);
  return {selectedDimensions:selected.dimensions,sourceWidth:selected.sourceDimensions.lateralWidth.value,
    croppedSelectionWidth:cut.dimensions.lateralWidth,croppedVolumeWithheld:true};
});
test('Closedness and provenance gates prevent bogus imported/ROI volume',()=>{
  const topology=inspectMeshTopology(ellipsoid),measured=measureEnclosedVolume(ellipsoid,{topology,provenance:clearSingle});
  assert.equal(topology.closed,true);assert.equal(topology.componentCount,1);assert.equal(measured.available,true);
  const relativeError=Math.abs(measured.value-exactVolume)/exactVolume;assert.ok(relativeError<.003);
  const opened={positions:ellipsoid.positions,triangles:ellipsoid.triangles.slice(3)},openResult=measureEnclosedVolume(opened,{provenance:clearSingle});
  assert.equal(openResult.available,false);assert.equal(openResult.topology.boundaryEdges,3);
  assert.equal(measureEnclosedVolume(ellipsoid).available,false);
  const inconsistent={positions:ellipsoid.positions,triangles:new Uint32Array(ellipsoid.triangles)};
  [inconsistent.triangles[1],inconsistent.triangles[2]]=[inconsistent.triangles[2],inconsistent.triangles[1]];
  assert.equal(measureEnclosedVolume(inconsistent,{provenance:clearSingle}).available,false);
  return {triangleCount:topology.triangles,analyticVolume:exactVolume,triangulatedVolume:measured.value,relativeError,
    openBoundaryEdges:openResult.topology.boundaryEdges,uncheckedImportVolumeWithheld:true,inconsistentWindingWithheld:true};
});
test('Disjoint paired lobes sum volumes despite opposite global winding',()=>{
  const rr=[.06,.065,.05],mesh=combine(ellipsoidMesh([-.075,.61,-.07],rr),ellipsoidMesh([.075,.61,-.07],rr,{reverse:true}));
  const topology=inspectMeshTopology(mesh),result=measureEnclosedVolume(mesh,{topology,provenance:{selfIntersectionStatus:'known-analytic-simple',componentRelationship:'disjoint'}});
  const expected=2*4*Math.PI/3*rr.reduce((a,b)=>a*b),error=Math.abs(result.value-expected)/expected;
  assert.equal(topology.componentCount,2);assert.equal(result.available,true);assert.ok(error<.003);
  assert.ok(result.signedComponentVolumes[0]*result.signedComponentVolumes[1]<0);
  assert.equal(measureEnclosedVolume(mesh,{topology,provenance:clearSingle}).available,false);
  return {componentCount:topology.componentCount,analyticPairVolume:expected,triangulatedPairVolume:result.value,relativeError:error,
    signedComponentVolumes:result.signedComponentVolumes,incorrectSingleComponentDeclarationWithheld:true};
});

const front=createCamera({id:'front',position:[0,.61,1],target:[0,.61,0],width:800,height:600,verticalSpan:.5,calibrated:true,
  calibrationProvenance:'Known synthetic orthographic camera'});
const side=createCamera({...front,id:'side',position:[1,.61,0],target:[0,.61,0]});
const candidate={id:'known',center:[0,.61,0],radii};
function ellipse2D(cx,cy,a,b,angle=0,count=192){return Array.from({length:count},(_,i)=>{const t=i/count*2*Math.PI,x=a*Math.cos(t),y=b*Math.sin(t);
  return [cx+x*Math.cos(angle)-y*Math.sin(angle),cy+x*Math.sin(angle)+y*Math.cos(angle)];});}
test('Reviewed ellipse fitting recovers rotated contour support, not unseen depth',()=>{
  const points=ellipse2D(412,297,97,43,.44),fit=fitReviewedEllipseSilhouette(points,{reviewed:true,coverage:'full-contour',camera:front});
  assert.equal(fit.accepted2D,true);near(fit.center[0],412,1e-9);near(fit.center[1],297,1e-9);near(fit.radiusMajor,97,1e-8);near(fit.radiusMinor,43,1e-8);
  const expectedWidth=2*Math.hypot(97*Math.cos(.44),43*Math.sin(.44));near(fit.widthPixels,expectedWidth,1e-8);
  assert.ok(fit.implicitResidualRms<1e-12);
  assert.equal(fitReviewedEllipseSilhouette(points,{reviewed:false,camera:front}).observableCameraPlaneExtents.available,false);
  assert.equal(fitReviewedEllipseSilhouette(points,{reviewed:true,coverage:'partial-contour',camera:front}).accepted2D,false);
  return {radiusMajor:fit.radiusMajor,radiusMinor:fit.radiusMinor,widthPixels:fit.widthPixels,implicitResidualRms:fit.implicitResidualRms,
    unreviewedAndPartialProfilesNotAccepted:true};
});
test('Known camera/framing changes preserve recovered observable shape dimensions',()=>{
  const cam2=createCamera({...front,id:'different-framing',width:1920,height:1080,verticalSpan:.8});
  const oblique=createCamera({...front,id:'oblique',position:[Math.SQRT1_2,.61,Math.SQRT1_2],target:[0,.61,0]});
  const recovered=[];
  for(const cam of [front,cam2,side,oblique]){const profile=orthographicEllipsoidProfile(candidate,cam),fit=fitReviewedEllipseSilhouette(profile.points,{reviewed:true,coverage:'full-contour',camera:cam});
    const exactWidth=2*Math.sqrt((radii[0]*cam.right[0])**2+(radii[2]*cam.right[2])**2);
    near(fit.observableCameraPlaneExtents.rightSpan,exactWidth,1e-10);near(fit.observableCameraPlaneExtents.upSpan,.12,1e-10);
    recovered.push({cameraId:cam.id,width:fit.observableCameraPlaneExtents.rightSpan,height:fit.observableCameraPlaneExtents.upSpan,expectedWidth:exactWidth});}
  const projected=projectPoints(ellipsoid.positions,front),pixelX=Array.from(projected.pixels).filter((_,i)=>i%2===0);
  near(recoverOrthographicAxisExtent(Math.max(...pixelX)-Math.min(...pixelX),front).value,.16);
  assert.equal(recoverOrthographicAxisExtent(100,{...front,calibrated:false}).available,false);
  return {recovered,framingDoesNotRescaleCanonicalGeometry:true};
});
test('Perspective projection uses depth; pose is rigid and does not mutate geometry',()=>{
  const camera=createCamera({id:'perspective',type:'perspective',position:[0,0,0],target:[0,0,-1],width:1000,height:1000,fovYDegrees:90,calibrated:true});
  const projection=projectPoint([.1,.2,-2],camera);near(projection.pixel[0],525);near(projection.pixel[1],450);near(projection.depth,2);
  assert.equal(projectPoint([0,0,1],camera).visible,false);
  const twice=projectPoint([.1,.2,-4],camera);near(twice.pixel[0]-500,(projection.pixel[0]-500)/2);
  const pose={rotationEuler:[.2,.5,-.1],pivot:[0,.61,0],translation:[.1,0,0]},input=new Float64Array(ellipsoid.positions),before=Array.from(input);
  projectPoints(input,front,{pose});assert.deepEqual(Array.from(input),before);
  const p=[.1,.4,.2],q=[-.1,.6,-.3],pp=applyRigidPose(p,pose),qq=applyRigidPose(q,pose);
  near(Math.hypot(...sub(pp,qq)),Math.hypot(...sub(p,q)));assert.throws(()=>applyRigidPose(p,{scale:.5}),/cannot rescale/);
  const fit=fitReviewedEllipseSilhouette(ellipse2D(500,500,50,40),{reviewed:true,coverage:'full-contour',camera});
  assert.equal(fit.observableCameraPlaneExtents.available,false);
  return {pixel:projection.pixel,depth:projection.depth,perspectiveDepthHalvesPixelOffset:true,canonicalGeometryUnchanged:true,poseScaleRejected:true};
});
test('One front view leaves depth unresolved; the side view separates candidates',()=>{
  const candidates=[.04,.08,.16].map(depth=>({id:`depth-${depth}`,center:[0,.61,0],radii:[.08,.06,depth]})),truth=candidates[1];
  const observation={camera:front,points:orthographicEllipsoidProfile(truth,front).points,reviewed:true};
  const single=evaluateDepthCandidates(candidates,[observation],{tolerancePixels:.1});
  assert.equal(single.status,'underconstrained_single_view');assert.equal(single.supportedCandidateIds.length,3);
  const ranked=rankNextViews(candidates,[front,side]);assert.equal(ranked.recommendedCameraId,'side');near(ranked.rankings.find(r=>r.cameraId==='front').disagreementPixels,0);
  const second={camera:side,points:orthographicEllipsoidProfile(truth,side).points,reviewed:true};
  const paired=evaluateDepthCandidates(candidates,[observation,second],{tolerancePixels:.1});
  assert.deepEqual(paired.supportedCandidateIds,[truth.id]);assert.equal(paired.globalShapeUniquenessCertified,false);
  assert.equal(evaluateDepthCandidates(candidates,[{...observation,reviewed:false}]).status,'needs_profile_review_or_camera_calibration');
  const unusable=rankNextViews(candidates,[createCamera({...side,id:'clipped',verticalSpan:.02})]);assert.equal(unusable.recommendedCameraId,null);
  return {singleViewStatus:single.status,singleViewCompatibleDepths:single.supportedCandidateIds,recommendedNextView:ranked.recommendedCameraId,
    viewRanking:ranked.rankings,twoViewSupportedCandidateIds:paired.supportedCandidateIds,
    uniqueness:'Only in declared candidate family; no unrestricted 3D uniqueness claim',clippedViewsNotRecommended:true};
});
test('Invalid arrays/calibration and nonrigid transforms are rejected',()=>{
  assert.throws(()=>fitReviewedEllipseSilhouette([1,2,3]),/Complete/);
  assert.throws(()=>createCamera({width:Infinity}),/finite/);
  assert.throws(()=>createCamera({position:[0,0,0],target:[0,0,0]}),/Degenerate/);
  assert.throws(()=>applyRigidPose([0,0,0],{rotationMatrix:[2,0,0,0,1,0,0,0,1]}),/rigid/);
  assert.throws(()=>crossSectionSegments(ellipsoid,{axis:'y',value:.61},{tolerance:Infinity}),/finite/);
  assert.throws(()=>createUnitContext({heightSourceUnits:sourceHeight,physicalStature:1.8,physicalUnit:'m'}),/reviewed/);
  return {invalidInputsRejected:true};
});

report.passed=report.tests.every(t=>t.passed);report.testCount=report.tests.length;
const destination=new URL('./verification.json',import.meta.url);await writeFile(destination,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:report.passed,tests:report.testCount,report:fileURLToPath(destination),
  largestVolumeRelativeError:Math.max(...report.tests.map(t=>t.relativeError??0)),
  nextView:report.tests.find(t=>t.recommendedNextView)?.recommendedNextView},null,2));
