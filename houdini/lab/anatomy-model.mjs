/** Deterministic regional implicit anatomy proposal, with no source-mesh edits.
 * Coordinates: canonical FBX-height H=1, +Y up, posterior -Z.
 * Distance-like fields are not exact Euclidean signed distances. The surface
 * is their zero set; geometric volume is measured from the final union mesh.
 */
export const ANATOMY_DEFAULTS=Object.freeze({
 lobeWidth:1,lobeHeight:1,rearProjection:1,upperPole:1.08,lowerPole:1,
 separation:1,attachment:.012,cleft:.75,asymmetry:0,pelvisWidth:1,pelvisDepth:1,
 thighFullness:1,thighOuter:1,thighFront:1,kneeTaper:.65
});
export const ANATOMY_RANGES=Object.freeze({
 lobeWidth:[.55,1.6],lobeHeight:[.65,1.55],rearProjection:[.55,2.1],
 upperPole:[.65,1.4],lowerPole:[.65,1.4],separation:[.5,1.5],attachment:[.003,.03],
 cleft:[0,1],asymmetry:[-.2,.2],pelvisWidth:[.8,1.2],pelvisDepth:[.8,1.3],
 thighFullness:[.65,1.5],thighOuter:[.5,1.5],thighFront:[.5,1.5],kneeTaper:[.3,.9]
});
const H_SOURCE=2.3951061964035034;
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const smooth=(a,b,v)=>{const t=clamp((v-a)/(b-a),0,1);return t*t*(3-2*t)};
const mix=(a,b,t)=>a+(b-a)*t;
function smoothUnion(a,b,k){const h=Math.max(k-Math.abs(a-b),0)/k;return Math.min(a,b)-k*h*h*.25}
function ellipsoid(p,c,r){const q=Math.hypot((p[0]-c[0])/r[0],(p[1]-c[1])/r[1],(p[2]-c[2])/r[2]);return (q-1)*Math.min(...r)}
function capsule(p,a,b,r){const d=p.map((v,i)=>v-a[i]),v=b.map((x,i)=>x-a[i]),den=v.reduce((s,x)=>s+x*x,0),t=den?clamp(d.reduce((s,x,i)=>s+x*v[i],0)/den,0,1):0;return Math.hypot(...d.map((x,i)=>x-t*v[i]))-r}

export function createAnatomyTemplate(overrides={}){
 const params={...ANATOMY_DEFAULTS};
 for(const [key,value] of Object.entries(overrides)){
  if(!(key in params))throw Error('Unknown anatomy control: '+key);
  const [lo,hi]=ANATOMY_RANGES[key];if(!Number.isFinite(value)||value<lo||value>hi)throw Error(key+' must be finite and between '+lo+' and '+hi);
  params[key]=value;
 }
 const pole=Math.max(params.upperPole,params.lowerPole),asym=1+Math.abs(params.asymmetry),rx=.079*params.lobeWidth*pole*asym,hy=.087*params.lobeHeight*asym,rz=.068*params.rearProjection*pole*asym;
 const maxThighX=.116+.07*params.thighFullness*params.thighOuter;
 const pad=Math.max(.018,params.attachment*4);
 const boundX=Math.max(.073*params.separation+rx,maxThighX,.084*params.pelvisWidth)+pad;
 const bounds={min:[-boundX,Math.min(.325,.61-hy,.482)-pad,Math.min(-.015-2*rz,-.070*params.pelvisDepth)-pad],max:[boundX,Math.max(.65,.61+hy)+pad,Math.max(.066*params.pelvisDepth,.074*params.thighFullness*params.thighFront)+pad]};
 return {params:Object.freeze(params),bounds,metadata:{
  status:'editable regional proposal; not accepted anatomy',model:'connected pelvic core, paired lobes, upper-thigh transitions',
  coordinate_system:'canonical H=1; +Y up; posterior -Z',height_reference_normalized:1,source_height_units:H_SOURCE,
  surface_scope:'closed regional template; not a complete body or a seamless source-FBX attachment',
  units:'linear coordinates in normalized height units; multipliers dimensionless; attachment in normalized height units',
  field:'distance-like implicit gauges with smooth unions; not an exact signed-distance field',
  volume:'enclosed final union surface, never a sum of overlapping component volumes',
  anatomical_acceptance:false,reference_fitted:false,neural_paper_implementation:false,
  independence:'thigh component fields use only thigh controls; lobe controls affect attachments near the pelvis',
  symmetry:'shared lobe controls plus signed asymmetry: negative enlarges left, positive enlarges right'
 }};
}

export function evaluateAnatomyComponents(point,template){
 const p=point,c=template.params;
 if(p.length!==3||!p.every(Number.isFinite))throw Error('Finite XYZ required.');
 const core=ellipsoid(p,[0,.567,.003],[.084*c.pelvisWidth,.085,.060*c.pelvisDepth]);
 const perineal=ellipsoid(p,[0,.516,.005],[.054*c.pelvisWidth,.055,.047*c.pelvisDepth]);
 function lobe(side){
  const a=1+side*c.asymmetry,hy=.087*c.lobeHeight*a,t=(p[1]-.61)/hy;
  const pole=mix(c.lowerPole,c.upperPole,smooth(-.35,.35,t)),rx=.079*c.lobeWidth*pole*a,rz=.068*c.rearProjection*pole*a;
  // Posterior projection changes the rear extent while the front pole stays
  // at z=-.015. It does not translate/widen the underlying pelvic core.
  return ellipsoid(p,[side*.073*c.separation,.61,-.015-rz],[rx,hy,rz]);
 }
 function thigh(side){
  const t=clamp((p[1]-.325)/.24,0,1),cx=side*mix(.112,.082,smooth(0,1,t));
  const fullness=smooth(.10,mix(.88,.63,c.kneeTaper),t);
  const radial=mix(.03,.068*c.thighFullness,fullness);
  const outward=smooth(-.004,.004,side*(p[0]-cx));
  const rx=radial*mix(.82,c.thighOuter,outward);
  const front=smooth(-.003,.003,p[2]-.018);
  const rz=mix(.027,.050*c.thighFullness,fullness)*mix(.8,c.thighFront,front);
  return ellipsoid(p,[cx,.445,.018],[rx,.12,rz]);
 }
 const attachRadius=.038+c.attachment*.3;
 return {core,perineal,leftLobe:lobe(-1),rightLobe:lobe(1),leftThigh:thigh(-1),rightThigh:thigh(1),
  leftAttachment:capsule(p,[-.052,.582,-.020],[-.073*c.separation,.609,-.052],attachRadius),
  rightAttachment:capsule(p,[.052,.582,-.020],[.073*c.separation,.609,-.052],attachRadius)};
}

export function evaluateAnatomy(point,template){
 const d=evaluateAnatomyComponents(point,template),c=template.params;
 let base=smoothUnion(d.core,d.perineal,c.attachment);
 base=smoothUnion(base,smoothUnion(d.leftThigh,d.rightThigh,c.attachment),c.attachment);
 base=smoothUnion(base,smoothUnion(d.leftAttachment,d.rightAttachment,c.attachment),c.attachment);
 const posterior=smooth(.045,.10,-point[2]);
 // Shared lobe smoothing is reduced by cleft hold. The structural core stays
 // connected; this does not cut a hole through the pelvis.
 const central=1-smooth(.01,.06,Math.abs(point[0]));
 const blend=c.attachment*(1-.9*c.cleft);
 const lobes=smoothUnion(d.leftLobe,d.rightLobe,blend);
 const join=c.attachment*(1-.85*c.cleft*posterior*central);
 return smoothUnion(base,lobes,join);
}

export function anatomyNormal(point,template,epsilon=1e-4){
 const gradient=[0,0,0];
 for(let axis=0;axis<3;axis++){const a=[...point],b=[...point];a[axis]+=epsilon;b[axis]-=epsilon;gradient[axis]=(evaluateAnatomy(a,template)-evaluateAnatomy(b,template))/(2*epsilon)}
 const n=Math.hypot(...gradient);return n>1e-12?gradient.map(v=>v/n):[0,1,0];
}

/** Consistent six-tetrahedron subdivision and shared global-edge vertices.
 * Resolution counts cells along the largest domain dimension, not all axes.
 */
export function extractAnatomy(template,{resolution=24}={}){
 if(!Number.isInteger(resolution)||resolution<12||resolution>72)throw Error('Draft/refinement resolution must be an integer from12 to72.');
 const {min,max}=template.bounds,extent=max.map((v,i)=>v-min[i]),h=Math.max(...extent)/resolution;
 const cells=extent.map(e=>Math.max(4,Math.ceil(e/h))),dims=cells.map(n=>n+1),step=extent.map((e,i)=>e/cells[i]),total=dims.reduce((a,b)=>a*b,1);
 const index=(x,y,z)=>x+dims[0]*(y+dims[1]*z),grid=new Float64Array(total),coordinate=id=>{const x=id%dims[0],yz=Math.floor(id/dims[0]),y=yz%dims[1],z=Math.floor(yz/dims[1]);return [min[0]+x*step[0],min[1]+y*step[1],min[2]+z*step[2]]};
 const isoEpsilon=Math.min(...step)*1e-5;
 for(let z=0;z<dims[2];z++)for(let y=0;y<dims[1];y++)for(let x=0;x<dims[0];x++){
  const id=index(x,y,z);let value=evaluateAnatomy([min[0]+x*step[0],min[1]+y*step[1],min[2]+z*step[2]],template);
  if(!Number.isFinite(value))throw Error('Non-finite implicit field.');
  if((x===0||y===0||z===0||x===cells[0]||y===cells[1]||z===cells[2])&&value<=0)throw Error('Implicit template touches the extraction boundary; expand bounds.');
  if(Math.abs(value)<isoEpsilon)value=isoEpsilon;grid[id]=value;
 }
 const points=[],normals=[],faces=[],edges=new Map(),eps=Math.min(...step)*.035;
 function edge(a,b){const key=a<b?a+','+b:b+','+a;if(edges.has(key))return edges.get(key);const pa=coordinate(a),pb=coordinate(b),t=grid[a]/(grid[a]-grid[b]),p=pa.map((v,i)=>v+(pb[i]-v)*t),id=points.length/3;points.push(...p);normals.push(...anatomyNormal(p,template,eps));edges.set(key,id);return id}
 function triangle(a,b,c,direction){const pa=points.slice(a*3,a*3+3),pb=points.slice(b*3,b*3+3),pc=points.slice(c*3,c*3+3),u=pb.map((v,i)=>v-pa[i]),v=pc.map((x,i)=>x-pa[i]),cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];if(cross.reduce((s,x,i)=>s+x*direction[i],0)<0)[b,c]=[c,b];faces.push(a,b,c)}
 const tetrahedra=[[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]];
 for(let z=0;z<cells[2];z++)for(let y=0;y<cells[1];y++)for(let x=0;x<cells[0];x++){
  const cube=[index(x,y,z),index(x+1,y,z),index(x+1,y+1,z),index(x,y+1,z),index(x,y,z+1),index(x+1,y,z+1),index(x+1,y+1,z+1),index(x,y+1,z+1)];
  for(const tet of tetrahedra){const ins=[],outs=[];for(const i of tet)(grid[cube[i]]<0?ins:outs).push(cube[i]);if(!ins.length||!outs.length)continue;
   const inside=coordinate(ins[0]),outside=coordinate(outs[0]),direction=outside.map((v,i)=>v-inside[i]);
   // Winding follows the linear field in this tetrahedron. A nonlinear-field
   // gradient at a tiny contour triangle can disagree with that interpolant.
   if(ins.length===1)triangle(edge(ins[0],outs[0]),edge(ins[0],outs[1]),edge(ins[0],outs[2]),direction);
   else if(ins.length===3)triangle(edge(outs[0],ins[0]),edge(outs[0],ins[1]),edge(outs[0],ins[2]),direction);
   else{const ac=edge(ins[0],outs[0]),ad=edge(ins[0],outs[1]),bc=edge(ins[1],outs[0]),bd=edge(ins[1],outs[1]);triangle(ac,ad,bd,direction);triangle(ac,bd,bc,direction)}
  }
 }
 return {positions:new Float32Array(points),normals:new Float32Array(normals),triangles:new Uint32Array(faces),bounds:structuredClone(template.bounds),metadata:{...template.metadata,extraction:'marching tetrahedra; consistent shared face diagonals and global-edge vertex reuse',resolution,grid_cells:cells,voxel_spacing:step,iso_classification_epsilon:isoEpsilon}};
}

export function measureAnatomyMesh(mesh){
 const p=mesh.positions,t=mesh.triangles,counts=new Map(),directions=new Map(),parents=Array.from({length:p.length/3},(_,i)=>i);let signedVolume=0,area=0,minArea=Infinity,degenerateTriangles=0;
 const root=a=>{while(parents[a]!==a){parents[a]=parents[parents[a]];a=parents[a]}return a};
 for(let i=0;i<t.length;i+=3){const ids=[t[i],t[i+1],t[i+2]],a=ids.map(id=>[p[id*3],p[id*3+1],p[id*3+2]]),u=a[1].map((v,k)=>v-a[0][k]),v=a[2].map((x,k)=>x-a[0][k]),cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]],triangleArea=Math.hypot(...cross)/2;
  area+=triangleArea;minArea=Math.min(minArea,triangleArea);if(!(triangleArea>1e-18))degenerateTriangles++;
  signedVolume+=(a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])+a[0][1]*(a[1][2]*a[2][0]-a[1][0]*a[2][2])+a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))/6;
  for(let j=0;j<3;j++){const q=ids[j],r=ids[(j+1)%3],key=q<r?q+','+r:r+','+q;counts.set(key,(counts.get(key)||0)+1);directions.set(key,(directions.get(key)||0)+(q<r?1:-1));parents[root(q)]=root(r)}
 }
 let boundaryEdges=0,nonManifoldEdges=0,inconsistentEdges=0;for(const [key,n]of counts){if(n===1)boundaryEdges++;else if(n!==2)nonManifoldEdges++;if(n===2&&directions.get(key)!==0)inconsistentEdges++}
 const connectedComponents=new Set(t.map(id=>root(id))).size,closed=boundaryEdges===0&&nonManifoldEdges===0&&inconsistentEdges===0;
 return {points:p.length/3,triangles:t.length/3,closed,boundaryEdges,nonManifoldEdges,inconsistentEdges,connectedComponents,degenerateTriangles,minimumTriangleArea:minArea,surfaceArea:area,signedVolume,volume:closed?Math.abs(signedVolume):null,volumeUnits:'normalized H cubed',sourceUnitVolume:closed?Math.abs(signedVolume)*H_SOURCE**3:null,status:'volume of this regional proposal, not a measured anatomical volume',heightReferenceNormalized:1};
}

/** Negative-field cell-centre integration measures the union once. */
export function measureAnatomyVoxels(template,{resolution=32}={}){
 if(!Number.isInteger(resolution)||resolution<12||resolution>96)throw Error('Voxel measurement resolution12..96 required.');
 const {min,max}=template.bounds,e=max.map((v,i)=>v-min[i]),h=Math.max(...e)/resolution,n=e.map(v=>Math.ceil(v/h)),s=e.map((v,i)=>v/n[i]);let inside=0;
 for(let z=0;z<n[2];z++)for(let y=0;y<n[1];y++)for(let x=0;x<n[0];x++)if(evaluateAnatomy([min[0]+(x+.5)*s[0],min[1]+(y+.5)*s[1],min[2]+(z+.5)*s[2]],template)<0)inside++;
 return {volume:inside*s[0]*s[1]*s[2],insideCells:inside,gridCells:n,spacing:s,method:'cell-centre integration of final implicit union; discretization dependent',volumeUnits:'normalized H cubed'};
}

export function anatomyCrossSection(mesh,{axis='y',value=.61}={}){
 const ax={x:0,y:1,z:2}[axis];if(ax===undefined||!Number.isFinite(value))throw Error('Finite slice and x/y/z axis required.');
 const p=mesh.positions,t=mesh.triangles,positions=[],segments=[],vertices=new Map();
 function hit(a,b){const key=a===b?'v'+a:a<b?a+','+b:b+','+a;if(vertices.has(key))return vertices.get(key);const da=p[a*3+ax]-value,db=p[b*3+ax]-value,u=a===b?0:da/(da-db),point=[0,1,2].map(k=>p[a*3+k]+u*(p[b*3+k]-p[a*3+k]));point[ax]=value;const id=positions.length/3;positions.push(...point);vertices.set(key,id);return id}
 for(let i=0;i<t.length;i+=3){const ids=[t[i],t[i+1],t[i+2]],hits=[];for(let j=0;j<3;j++){const a=ids[j],b=ids[(j+1)%3],da=p[a*3+ax]-value,db=p[b*3+ax]-value;if(Math.abs(da)<1e-10)hits.push(hit(a,a));else if(da*db<0)hits.push(hit(a,b))}const unique=[...new Set(hits)];if(unique.length===2)segments.push(...unique)}
 const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(let i=0;i<positions.length;i+=3)for(let k=0;k<3;k++){lo[k]=Math.min(lo[k],positions[i+k]);hi[k]=Math.max(hi[k],positions[i+k])}
 return {positions:new Float32Array(positions),segments:new Uint32Array(segments),axis,value,bounds:positions.length?{min:lo,max:hi,extent:hi.map((v,i)=>v-lo[i])}:null,status:'cross-section of regional proposal; no anatomical measurement acceptance'};
}
