/** Geometry measurements in canonical, UNPOSED, ground-normalized H=1 coordinates.
 * Selection extents are operational geometry, never inferred tissue dimensions.
 * Pure ES module: browser/Node; no I/O or external dependencies.
 */
export const DEFAULT_REAR_ROI = Object.freeze({
  x: Object.freeze([-.22, .22]), y: Object.freeze([.49, .73]),
  z: Object.freeze([null, .015]), label: 'Provisional selected posterior surface',
  confidence: 'Artist-editable source-coordinate ROI; not accepted anatomical segmentation',
});
const AXIS = {x: 0, y: 1, z: 2};
const sub = (a,b) => a.map((v,i)=>v-b[i]);
const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const dot = (a,b) => a.reduce((s,v,i)=>s+v*b[i],0);
const length = a => Math.hypot(...a);
const point = (p,i) => [p[3*i],p[3*i+1],p[3*i+2]];
function geometryCheck({positions:p,triangles:f}) {
  if (!p || !f || p.length%3 || f.length%3) throw new TypeError('Flat XYZ positions and triangle indices required');
  for (const v of p) if (!Number.isFinite(v)) throw new RangeError('Nonfinite geometry position');
  const n=p.length/3;
  for (const i of f) if (!Number.isInteger(i) || i<0 || i>=n) throw new RangeError('Invalid triangle index');
  return n;
}
function ranges(roi=DEFAULT_REAR_ROI) {
  return ['x','y','z'].map(a=>{
    const r=roi[a]??[null,null],low=r[0]??-Infinity,high=r[1]??Infinity;
    if (!(low<high)) throw new RangeError('ROI bounds must have positive span');
    return [low,high];
  });
}
function limits(r) {
  return r.flatMap(([low,high],axis)=>[
    ...(Number.isFinite(low)?[{axis,value:low,sign:1}]:[]),
    ...(Number.isFinite(high)?[{axis,value:high,sign:-1}]:[]),
  ]);
}
function clipPolygon(poly,planes,tolerance) {
  let clipped=false;
  for (const {axis,value,sign} of planes) {
    const next=[];
    for (let i=0;i<poly.length;i++) {
      const a=poly[i],b=poly[(i+1)%poly.length];
      const da=sign*(a[axis]-value),db=sign*(b[axis]-value);
      const ina=da>=-tolerance,inb=db>=-tolerance;
      if (ina) next.push(a);
      if (ina!==inb) {
        const t=da/(da-db);next.push(a.map((v,k)=>v+t*(b[k]-v)));clipped=true;
      } else if (!ina) clipped=true;
    }
    poly=next;if (!poly.length) break;
  }
  return {points:poly,clipped};
}
function clipSegment(a,b,r,tolerance) {
  let enter=0,leave=1;const d=sub(b,a);
  for (let axis=0;axis<3;axis++) {
    const [low,high]=r[axis];
    if (Math.abs(d[axis])<=tolerance) {
      if (a[axis]<low-tolerance||a[axis]>high+tolerance) return null;
    } else {
      const t1=(low-a[axis])/d[axis],t2=(high-a[axis])/d[axis];
      enter=Math.max(enter,Math.min(t1,t2));leave=Math.min(leave,Math.max(t1,t2));
      if (enter>leave+tolerance) return null;
    }
  }
  const aa=a.map((v,k)=>v+enter*d[k]),bb=a.map((v,k)=>v+leave*d[k]);
  return length(sub(aa,bb))>tolerance?[aa,bb]:null;
}
function boundsOf(points) {
  if (!points.length) return null;
  const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
  for (const p of points) for (let k=0;k<3;k++) {min[k]=Math.min(min[k],p[k]);max[k]=Math.max(max[k],p[k]);}
  return {min,max,extent:max.map((v,k)=>v-min[k]),center:max.map((v,k)=>(v+min[k])/2)};
}
const keyOf=(p,t)=>p.map(v=>Math.round(v/t)).join(',');

/** Exact triangle-plane sections, then segment clipping to explicit ROI.
 * Coplanar shared triangle edges cancel instead of adding artificial diagonals.
 */
export function crossSectionSegments(geometry,{axis='y',value},{roi=DEFAULT_REAR_ROI,tolerance=1e-7}={}) {
  geometryCheck(geometry);const k=typeof axis==='number'?axis:AXIS[axis];
  if (![0,1,2].includes(k)||!Number.isFinite(value)||!(tolerance>0)||!Number.isFinite(tolerance)) throw new RangeError('Valid plane and finite positive tolerance required');
  const r=ranges(roi),segments=[],coplanar=new Map(),seen=new Set();
  const {positions:p,triangles:f}=geometry;
  function add(a,b) {
    const clipped=clipSegment(a,b,r,tolerance);if (!clipped) return;
    const keys=clipped.map(v=>keyOf(v,tolerance)).sort(),key=keys.join('|');
    if (!seen.has(key)) {seen.add(key);segments.push(clipped);}
  }
  if (value<r[k][0]-tolerance||value>r[k][1]+tolerance) return {axis:k,value,segments:[],bounds:null,status:'outside_roi'};
  for (let j=0;j<f.length;j+=3) {
    const v=[point(p,f[j]),point(p,f[j+1]),point(p,f[j+2])],d=v.map(a=>a[k]-value);
    if (d.every(x=>x>tolerance)||d.every(x=>x<-tolerance)) continue;
    if (d.every(x=>Math.abs(x)<=tolerance)) {
      for (let e=0;e<3;e++) {
        const a=v[e],b=v[(e+1)%3],key=[keyOf(a,tolerance),keyOf(b,tolerance)].sort().join('|');
        const old=coplanar.get(key);coplanar.set(key,{count:(old?.count??0)+1,a,b});
      }
      continue;
    }
    const intersections=[];
    for (let e=0;e<3;e++) {
      const next=(e+1)%3,a=v[e],b=v[next],da=d[e],db=d[next];
      if (Math.abs(da)<=tolerance) intersections.push(a);
      if ((da>tolerance&&db<-tolerance)||(da<-tolerance&&db>tolerance)) {
        const t=da/(da-db);intersections.push(a.map((x,i)=>x+t*(b[i]-x)));
      }
    }
    const unique=[...new Map(intersections.map(v=>[keyOf(v,tolerance),v])).values()];
    if (unique.length>=2) {
      let best=[unique[0],unique[1]],distance=0;
      for (let a=0;a<unique.length;a++) for (let b=a+1;b<unique.length;b++) {
        const dist=length(sub(unique[a],unique[b]));if(dist>distance){best=[unique[a],unique[b]];distance=dist;}
      }
      add(...best);
    }
  }
  for (const edge of coplanar.values()) if (edge.count===1) add(edge.a,edge.b);
  const degrees=new Map();let totalCurveLength=0;
  for (const segment of segments) {
    totalCurveLength+=length(sub(...segment));
    for (const p of segment) {const key=keyOf(p,tolerance);degrees.set(key,(degrees.get(key)??0)+1);}
  }
  const closedLoopCandidate=segments.length>2&&[...degrees.values()].every(v=>v===2);
  return {axis:k,value,segments,bounds:boundsOf(segments.flat()),totalCurveLength,
    closedLoopCandidate,closureScope:'Endpoint-degree diagnostic only; self-intersection and enclosed area are not certified',
    status:segments.length?'selected_surface_section':'empty_section',quantityScope:'Surface intersections; not anatomical circumference'};
}

/** Explicit adapter for artist-reviewed full body bounds. Never auto-detects anatomy. */
export function canonicalizeBodyCoordinates(positions,{footY,topY,heightSourceUnits,reviewedBodyBounds=false}={}) {
  if (!reviewedBodyBounds) throw new RangeError('Body-stature bounds must be explicitly reviewed; props/ears/heels need an artist definition');
  const h=topY-footY;
  if (!(h>0)||!Number.isFinite(footY)||!Number.isFinite(topY)||!(heightSourceUnits>0)||!Number.isFinite(heightSourceUnits)) throw new RangeError('Explicit valid foot/top and source stature required');
  if (positions.length%3) throw new TypeError('Flat XYZ coordinates required');
  const result=new Float64Array(positions.length);
  for (let i=0;i<positions.length;i+=3) {
    if (![positions[i],positions[i+1],positions[i+2]].every(Number.isFinite)) throw new RangeError('Nonfinite geometry position');
    result[i]=positions[i]/h;result[i+1]=(positions[i+1]-footY)/h;result[i+2]=positions[i+2]/h;
  }
  return {positions:result,adapter:{footY,topY,inputWorkingStature:h,scaleToH1:1/h,heightSourceUnits,
    coordinateFrame:'canonical-unposed-ground-H1',authority:'Explicit artist-reviewed full-stature adapter',
    note:'All axes scaled uniformly; pose is applied separately for projection only; physical units remain unknown'}};
}
export function createUnitContext({heightSourceUnits,physicalStature=null,physicalUnit=null,physicalCalibrationReviewed=false}={}) {
  if (!(heightSourceUnits>0)||!Number.isFinite(heightSourceUnits)) throw new RangeError('Source stature must be explicit, finite and positive');
  if (physicalStature!==null&&(!(physicalStature>0)||!Number.isFinite(physicalStature)||!physicalCalibrationReviewed||typeof physicalUnit!=='string'||!physicalUnit.trim()))
    throw new RangeError('Physical conversion requires reviewed stature and an explicit physical unit');
  return Object.freeze({heightSourceUnits,normalizedUnit:'H',sourceUnit:'source units',physicalStature,physicalUnit,physicalCalibrationReviewed});
}
export function convertQuantity(value,unitContext,{power=1,target='source'}={}) {
  if (!Number.isFinite(value)||![1,2,3].includes(power)) throw new RangeError('Finite geometry quantity and length/area/volume power required');
  if (target==='normalized') return {value,unit:power===1?'H':`H^${power}`,calibrated:true};
  if (target==='source') return {value:value*unitContext.heightSourceUnits**power,unit:power===1?'source units':`source units^${power}`,calibrated:true,physical:false};
  if (target==='physical') {
    if (!unitContext.physicalCalibrationReviewed||unitContext.physicalStature===null)
      return {value:null,unit:null,calibrated:false,reason:'Real-world stature/unit calibration is absent'};
    return {value:value*unitContext.physicalStature**power,unit:power===1?unitContext.physicalUnit:`${unitContext.physicalUnit}^${power}`,calibrated:true,physical:true};
  }
  throw new RangeError('Unknown conversion target');
}

/** Indexed topology diagnostic; positional welding is deliberately not inferred. */
export function inspectMeshTopology(geometry,{areaTolerance=1e-14}={}) {
  const n=geometryCheck(geometry),{positions:p,triangles:f}=geometry,faceCount=f.length/3;
  const parent=Int32Array.from({length:faceCount},(_,i)=>i),edges=new Map();let degenerates=0;
  const find=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
  const join=(a,b)=>{a=find(a);b=find(b);if(a!==b)parent[b]=a;};
  for (let j=0;j<f.length;j+=3) {
    const v=[f[j],f[j+1],f[j+2]],area=length(cross(sub(point(p,v[1]),point(p,v[0])),sub(point(p,v[2]),point(p,v[0]))))/2;
    if (new Set(v).size<3||area<=areaTolerance) {degenerates++;continue;}
    for (let e=0;e<3;e++) {
      const a=v[e],b=v[(e+1)%3],lo=Math.min(a,b),hi=Math.max(a,b),key=lo*n+hi;
      if (!Number.isSafeInteger(key)) throw new RangeError('Mesh too large for bounded numeric edge keys');
      const old=edges.get(key),direction=a<b?1:-1;
      if(old){old.count++;old.balance+=direction;join(j/3,old.firstFace);}
      else edges.set(key,{count:1,balance:direction,firstFace:j/3});
    }
  }
  let boundaryEdges=0,nonmanifoldEdges=0,inconsistentEdges=0;
  for(const e of edges.values()){if(e.count===1)boundaryEdges++;if(e.count>2)nonmanifoldEdges++;if(e.count===2&&e.balance!==0)inconsistentEdges++;}
  const componentMap=new Map(),faceComponentIds=new Int32Array(faceCount);
  for(let i=0;i<faceCount;i++){const root=find(i);if(!componentMap.has(root))componentMap.set(root,componentMap.size);faceComponentIds[i]=componentMap.get(root);}
  return {vertices:n,triangles:faceCount,boundaryEdges,nonmanifoldEdges,inconsistentEdges,degenerateTriangles:degenerates,
    componentCount:componentMap.size,closed:faceCount>0&&boundaryEdges===0&&nonmanifoldEdges===0&&degenerates===0,
    consistentlyOriented:inconsistentEdges===0,selfIntersections:'not_checked',
    faceComponentIds,
    scope:'Indexed closedness/orientation only; no automatic self-intersection or anatomical validation'};
}
export function measureEnclosedVolume(geometry,{topology=null,provenance={}}={}) {
  geometryCheck(geometry);
  topology??=inspectMeshTopology(geometry);
  const blockers=[];
  if(!topology.closed)blockers.push('Open, degenerate or nonmanifold surface');
  if(!topology.consistentlyOriented)blockers.push('Inconsistent triangle orientation');
  if(!['reviewed-clear','known-analytic-simple'].includes(provenance.selfIntersectionStatus))blockers.push('Self-intersection clearance is unverified');
  if(!['disjoint','single'].includes(provenance.componentRelationship))blockers.push('Component overlap/containment relationship is unverified');
  if(provenance.componentRelationship==='single'&&topology.componentCount!==1)blockers.push('Declared single-component relationship does not match indexed topology');
  if(topology.triangles!==geometry.triangles.length/3||topology.vertices!==geometry.positions.length/3||topology.faceComponentIds?.length!==geometry.triangles.length/3)
    blockers.push('Supplied topology does not match geometry counts; recompute it for this mesh');
  if(blockers.length)return {available:false,value:null,unit:'H^3',topology,blockers,quantityScope:'Enclosed geometry volume only'};
  const {positions:p,triangles:f}=geometry,volumes=new Float64Array(topology.componentCount);
  // Translation-stable tetrahedral integration; disconnected disjoint lobes sum
  // absolute component volumes so opposite global winding cannot cancel them.
  const origin=point(p,f[0]);
  for(let j=0;j<f.length;j+=3){const a=sub(point(p,f[j]),origin),b=sub(point(p,f[j+1]),origin),c=sub(point(p,f[j+2]),origin);
    volumes[topology.faceComponentIds[j/3]]+=dot(a,cross(b,c))/6;}
  return {available:true,value:Array.from(volumes).reduce((s,v)=>s+Math.abs(v),0),signedComponentVolumes:Array.from(volumes),
    unit:'H^3',topology,quantityScope:'Enclosed authored geometry; not inferred tissue mass or anatomical volume',provenance};
}

export function measureRearGeometry(geometry,{roi=DEFAULT_REAR_ROI,sectionHeights=[.51,.54,.57,.60,.63,.66,.69,.72],
  tolerance=1e-7,unitContext=null,includeVolumeInspection=false,provenance={}}={}) {
  geometryCheck(geometry);if(!(tolerance>0)||!Number.isFinite(tolerance))throw new RangeError('Finite positive tolerance required');
  const r=ranges(roi),planes=limits(r),{positions:p,triangles:f}=geometry;
  const selectedIndices=[],min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity],contacts=new Set();let clippedTriangles=0,selectedTriangles=0;
  for(let j=0;j<f.length;j+=3){const triangle=[point(p,f[j]),point(p,f[j+1]),point(p,f[j+2])];
    if(r.some(([lo,hi],axis)=>triangle.every(v=>v[axis]<lo-tolerance)||triangle.every(v=>v[axis]>hi+tolerance)))continue;
    const clipped=clipPolygon(triangle,planes,tolerance);if(clipped.points.length<3)continue;
    selectedTriangles++;if(clipped.clipped)clippedTriangles++;
    for(const vertex of clipped.points){for(let axis=0;axis<3;axis++){min[axis]=Math.min(min[axis],vertex[axis]);max[axis]=Math.max(max[axis],vertex[axis]);}
      planes.forEach(({axis,value},i)=>{if(Math.abs(vertex[axis]-value)<=tolerance*2)contacts.add(i);});}
    if(includeVolumeInspection)selectedIndices.push(f[j],f[j+1],f[j+2]);}
  const bounds=selectedTriangles?{min,max,extent:max.map((v,k)=>v-min[k]),center:max.map((v,k)=>(v+min[k])/2)}:null;
  const sections=sectionHeights.map(value=>crossSectionSegments(geometry,{axis:'y',value},{roi,tolerance}));
  const boundaryContacts=planes.filter((_,i)=>contacts.has(i))
    .map(({axis,value,sign})=>({axis:['x','y','z'][axis],value,side:sign>0?'minimum':'maximum'}));
  const dimensions=bounds?{lateralWidth:bounds.extent[0],selectedHeight:bounds.extent[1],posteriorDepthSpan:bounds.extent[2]}:null;
  const sourceDimensions=dimensions&&unitContext?Object.fromEntries(Object.entries(dimensions).map(([k,v])=>[k,convertQuantity(v,unitContext)])):null;
  let volume={available:false,value:null,unit:'H^3',reason:clippedTriangles?'ROI cuts surface; closing caps/region definition are absent':'Closedness/provenance inspection not requested'};
  if(includeVolumeInspection&&!clippedTriangles&&selectedIndices.length)volume=measureEnclosedVolume({positions:p,triangles:selectedIndices},{provenance});
  return {coordinateFrame:'canonical-unposed-ground-H1',roi,bounds,dimensions,sourceDimensions,sections,
    selectedTriangles,clippedTriangles,boundaryContacts,boundaryLimited:boundaryContacts.length>0,enclosedVolume:volume,
    quantityScope:'Explicit selected outside-surface geometry; ROI height is a cut window, not anatomical rear height',
    warnings:[...(boundaryContacts.length?['ROI boundaries limit reported extents; expand/review ROI before interpreting full lobe dimensions']:[]),
      'Geometry and pixel/camera quantities remain separate; opacity and authored growth controls are not body-volume measurements']};
}

export function recoverOrthographicAxisExtent(pixelSpan,camera,{axis='right'}={}) {
  if(!['right','up'].includes(axis))throw new RangeError('Camera extent axis must be right or up');
  if(camera.type!=='orthographic'||!camera.calibrated) return {available:false,reason:'Reviewed orthographic camera calibration required'};
  const scale=axis==='right'?camera.pixelsPerWorldRight:camera.pixelsPerWorldUp;
  if(!(scale>0)||!Number.isFinite(pixelSpan))throw new RangeError('Positive camera scale and finite pixel span required');
  return {available:true,value:pixelSpan/scale,unit:'H',scope:`Observable span along camera ${axis}; not automatically an anatomical axis`};
}
