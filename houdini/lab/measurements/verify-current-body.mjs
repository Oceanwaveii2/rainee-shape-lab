/** Read-only source inspection; writes only a compact evidence report here. */
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {canonicalizeBodyCoordinates,createUnitContext,measureRearGeometry,DEFAULT_REAR_ROI} from '../measurement-model.mjs';
const root=new URL('../../',import.meta.url),config=JSON.parse(await readFile(new URL('viewer-config.json',root),'utf8'));
const positionPath=new URL(config.body,root),trianglePath=new URL(config.triangles,root);
const [pBuffer,tBuffer]=await Promise.all([readFile(positionPath),readFile(trianglePath)]);
const sha=b=>createHash('sha256').update(b).digest('hex');
const hashes={positions:sha(pBuffer),triangles:sha(tBuffer)};
const declaredSnapshot={positions:'ad055ae745bc884146420dfe872e279100de7a538da85be9f12fc2a590590aad',
  triangles:'2ce50eb65d270af04896c9175cbd812a4dff2d7993279622d2701d0dd598a3a4'};
if(hashes.positions!==declaredSnapshot.positions||hashes.triangles!==declaredSnapshot.triangles)
  throw new Error('Source snapshot changed. Re-review stature bounds before using this verification calibration.');
const p=new Float32Array(pBuffer.buffer,pBuffer.byteOffset,pBuffer.length/4),triangles=new Uint32Array(tBuffer.buffer,tBuffer.byteOffset,tBuffer.length/4);
const reviewed={footY:.00020352914,topY:.99903368950,heightSourceUnits:config.height_source_units,reviewedBodyBounds:true};
const canonical=canonicalizeBodyCoordinates(p,reviewed),start=performance.now();
const measured=measureRearGeometry({positions:canonical.positions,triangles},{roi:DEFAULT_REAR_ROI,
  sectionHeights:[.54,.58,.62,.66,.70],unitContext:createUnitContext({heightSourceUnits:config.height_source_units})});
const elapsedMs=performance.now()-start;
const report={schema:'rainee-current-body-operational-measurements-v1',createdUTC:new Date().toISOString(),
  status:'Selected surface descriptors verified on current source; anatomical calibration and reference fit remain provisional',
  source:{positions:fileURLToPath(positionPath),trianglePath:fileURLToPath(trianglePath),sha256:hashes,
    vertices:p.length/3,triangleCount:triangles.length/3,sourcePhysicalUnit:'unknown',sourceHeightUnits:config.height_source_units},
  statureAdapter:canonical.adapter,statureReview:{authority:'Parent explicitly supplied reviewed current native body bounds; all axes scaled uniformly',
    definition:'Native FBX full stature anchor, including its original top/ear finish; does not infer donor height or anatomy',
    sourceSnapshotRequired:declaredSnapshot},
  roi:measured.roi,bounds:measured.bounds,dimensions:measured.dimensions,sourceDimensions:measured.sourceDimensions,
  selectedTriangles:measured.selectedTriangles,clippedTriangles:measured.clippedTriangles,boundaryLimited:measured.boundaryLimited,
  boundaryContacts:measured.boundaryContacts,enclosedVolume:measured.enclosedVolume,warnings:measured.warnings,
  sections:measured.sections.map(s=>({y:s.value,bounds:s.bounds,segmentCount:s.segments.length,
    surfaceCurveLength:s.totalCurveLength,closedLoopCandidate:s.closedLoopCandidate,closureScope:s.closureScope,status:s.status})),
  CPU:{elapsedMs,runtime:process.version},noSourceMutations:true,noPoseBakedIntoMeasurements:true,
  scope:'Operational current geometry in canonical H=1. ROI cuts are not anatomical landmarks and authored growth is not body volume.'};
const destination=new URL('current-body-verification.json',import.meta.url);await writeFile(destination,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({report:fileURLToPath(destination),elapsedMs,dimensions:report.dimensions,
  boundaryLimited:report.boundaryLimited,volumeAvailable:report.enclosedVolume.available,sourceHashes:hashes},null,2));
