/* Reviewed affine donor alignment. No mesh mutation, learned/nonrigid transfer,
 * camera inference or change to the canonical body's stature. Pure JS API. */
export const ACCEPTED_FRAMES=Object.freeze([0,10,18,26]);
export const SOURCE_REGIONS=Object.freeze({
 rear:{min:[-.180,.530,-.150],max:[.180,.697,.010],exclude_perineal_core:{abs_x_max:.042,y_max:.615,z_min:-.075}},
 waist:{min:[-.100,.695,-.080],max:[.100,.724,.100]},
 thigh:{min:[-.18,.34,-.12],max:[.18,.535,.12]}
});
const EPS=1e-10,rad=x=>x*Math.PI/180,deg=x=>x*180/Math.PI;
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const length=a=>Math.sqrt(dot(a,a));
const unit=a=>{const l=length(a);if(!Number.isFinite(l)||l<EPS)throw Error('Coincident or collinear semantic landmarks.');return a.map(x=>x/l)};
function finiteVector(v,name){if(!v||v.length!==3||!Array.from(v).every(Number.isFinite))throw Error(`${name} must contain three finite numbers.`)}
function mul(a,b){return Array.from({length:9},(_,i)=>{const r=Math.floor(i/3),c=i%3;return a[r*3]*b[c]+a[r*3+1]*b[c+3]+a[r*3+2]*b[c+6]})}
function transpose(a){return [a[0],a[3],a[6],a[1],a[4],a[7],a[2],a[5],a[8]]}
function mv(a,v){return [dot(a.slice(0,3),v),dot(a.slice(3,6),v),dot(a.slice(6,9),v)]}
function determinant(a){return dot(a.slice(0,3),cross(a.slice(3,6),a.slice(6,9)))}
export function validateGeometry(positions,triangles){
 if(!positions||positions.length<9||positions.length%3)throw Error('Geometry positions must be finite XYZ triples.');
 if(!triangles||triangles.length<3||triangles.length%3)throw Error('Triangle buffer must contain integer index triples.');
 for(const x of positions)if(!Number.isFinite(x))throw Error('Nonfinite geometry position.');
 const vertices=positions.length/3,used=new Uint8Array(vertices);let usedCount=0;
 for(const id of triangles){if(!Number.isInteger(id)||id<0||id>=vertices)throw Error('Triangle index is outside the position buffer.');if(!used[id]){used[id]=1;usedCount++}}
 const bounds={min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]};
 for(let id=0;id<vertices;id++)if(used[id])for(let k=0;k<3;k++){const x=positions[id*3+k];bounds.min[k]=Math.min(bounds.min[k],x);bounds.max[k]=Math.max(bounds.max[k],x)}
 if(!Number.isFinite(length(sub(bounds.max,bounds.min)))||length(sub(bounds.max,bounds.min))<EPS)throw Error('Geometry has no spatial extent.');
 return {vertices,triangles:triangles.length/3,indexed_vertices:usedCount,bounds};
}
export function canonicalizeBody(positions,triangles){
 const info=validateGeometry(positions,triangles),height=info.bounds.max[1]-info.bounds.min[1];
 if(height<EPS)throw Error('Canonical body has no indexed Y stature.');
 const result=new Float32Array(positions.length);
 for(let i=0;i<positions.length;i+=3){result[i]=positions[i]/height;result[i+1]=(positions[i+1]-info.bounds.min[1])/height;result[i+2]=positions[i+2]/height}
 return {positions:result,recipe:{height_in_input_coordinates:height,min_y_in_input_coordinates:info.bounds.min[1],normalized_stature:1,definition:'Canonical source only: indexed Y min/max mapped to0/1. Donor transforms never enter this normalization.'},info};
}
export function canonicalROI(region,recipe){
 const h=recipe.height_in_input_coordinates,y=recipe.min_y_in_input_coordinates;
 const roi={min:region.min.map((x,k)=>(x-(k===1?y:0))/h),max:region.max.map((x,k)=>(x-(k===1?y:0))/h)};
 if(region.exclude_perineal_core)roi.exclude_perineal_core={abs_x_max:region.exclude_perineal_core.abs_x_max/h,y_max:(region.exclude_perineal_core.y_max-y)/h,z_min:region.exclude_perineal_core.z_min/h};
 return roi;
}
function signedAxis(name){const m=/^([+-])([XYZ])$/.exec(name||'');if(!m)throw Error('Axis must be signed X, Y or Z.');const v=[0,0,0];v['XYZ'.indexOf(m[2])]=m[1]==='+'?1:-1;return v}
export function axisMatrix(axes={up:'+Y',front:'+Z'}){
 const up=signedAxis(axes.up),front=signedAxis(axes.front);
 if(Math.abs(dot(up,front))>.5)throw Error('Up and front axes must be different.');
 const lateral=cross(up,front),m=[...lateral,...up,...front];
 if(Math.abs(determinant(m)-1)>1e-8)throw Error('Axis frame must be right-handed.');return m;
}
export function registrationMatrix(registration){
 const r=registration,{scale=1,rotation_degrees=[0,0,0],translation=[0,0,0],pivot_source=[0,0,0]}=r;
 if(!Number.isFinite(scale)||scale<=1e-6||scale>1e6)throw Error('Donor scale must be finite, positive and nonsingular.');
 finiteVector(rotation_degrees,'Rotation');finiteVector(translation,'Translation');finiteVector(pivot_source,'Pivot');
 const[x,y,z]=rotation_degrees.map(rad),cx=Math.cos(x),sx=Math.sin(x),cy=Math.cos(y),sy=Math.sin(y),cz=Math.cos(z),sz=Math.sin(z);
 const rx=[1,0,0,0,cx,-sx,0,sx,cx],ry=[cy,0,sy,0,1,0,-sy,0,cy],rz=[cz,-sz,0,sz,cz,0,0,0,1];
 const rotation=mul(mul(rz,ry),rx),total=mul(rotation,axisMatrix(r.axes));
 const linear=total.map(x=>x*scale),offset=sub(translation,mv(linear,pivot_source));
 if(![...linear,...offset].every(Number.isFinite))throw Error('Transform coefficients overflowed; reduce coordinates or scale.');
 return {row_major:[linear[0],linear[1],linear[2],offset[0],linear[3],linear[4],linear[5],offset[1],linear[6],linear[7],linear[8],offset[2],0,0,0,1],rotation_row_major:total,determinant:scale**3,convention:'Column vectors: pCanonical = translation + Rz·Ry·Rx·axisMap·(uniformScale·(pSource−pivotSource)); stored matrix is row-major.'};
}
export function transformPoint(point,registration){finiteVector(point,'Point');const m=registrationMatrix(registration).row_major;return [m[0]*point[0]+m[1]*point[1]+m[2]*point[2]+m[3],m[4]*point[0]+m[5]*point[1]+m[6]*point[2]+m[7],m[8]*point[0]+m[9]*point[1]+m[10]*point[2]+m[11]]}
export function inversePoint(point,registration){finiteVector(point,'Point');const m=registrationMatrix(registration),d=sub(point,registration.translation||[0,0,0]),v=mv(transpose(m.rotation_row_major),d);return v.map((x,i)=>x/(registration.scale??1)+(registration.pivot_source||[0,0,0])[i])}
export function transformPositions(positions,registration){const m=registrationMatrix(registration).row_major,out=new Float64Array(positions.length);if(positions.length%3)throw Error('XYZ triples required.');for(let i=0;i<positions.length;i+=3){const x=positions[i],y=positions[i+1],z=positions[i+2];if(![x,y,z].every(Number.isFinite))throw Error('Nonfinite source geometry.');out[i]=m[0]*x+m[1]*y+m[2]*z+m[3];out[i+1]=m[4]*x+m[5]*y+m[6]*z+m[7];out[i+2]=m[8]*x+m[9]*y+m[10]*z+m[11]}return out}
export function validateROI(roi){finiteVector(roi.min,'ROI minimum');finiteVector(roi.max,'ROI maximum');if(roi.min.some((x,k)=>x>=roi.max[k]))throw Error('Each ROI minimum must be smaller than its maximum.');return roi}
export function selectRegionFaces(positions,triangles,roi){
 validateROI(roi);const selected=[];const exclusion=roi.exclude_perineal_core;
 for(let i=0;i<triangles.length;i+=3){const a=triangles[i]*3,b=triangles[i+1]*3,c=triangles[i+2]*3,p=[(positions[a]+positions[b]+positions[c])/3,(positions[a+1]+positions[b+1]+positions[c+1])/3,(positions[a+2]+positions[b+2]+positions[c+2])/3];
  if(p.some((x,k)=>x<roi.min[k]||x>roi.max[k]))continue;
  if(exclusion&&Math.abs(p[0])<exclusion.abs_x_max&&p[1]<exclusion.y_max&&p[2]>exclusion.z_min)continue;
  selected.push(triangles[i],triangles[i+1],triangles[i+2]);
 }return new Uint32Array(selected);
}
function weightedQuantile(values,weights,q){const order=values.map((_,i)=>i).sort((a,b)=>values[a]-values[b]),total=weights.reduce((a,b)=>a+b,0);let cumulative=0,lastCDF=0,lastValue=values[order[0]];
 for(const i of order){const cdf=(cumulative+.5*weights[i])/total;if(q<=cdf){if(cdf<=lastCDF||q<=lastCDF)return lastValue;return lastValue+(values[i]-lastValue)*(q-lastCDF)/(cdf-lastCDF)}lastCDF=cdf;lastValue=values[i];cumulative+=weights[i]}return lastValue;
}
export function regionMetrics(positions,triangles){
 const values=[[],[],[]],weights=[],sum=[0,0,0];let area=0,degenerate=0;const bounds={min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]};
 for(let i=0;i<triangles.length;i+=3){const ids=[triangles[i],triangles[i+1],triangles[i+2]],v=ids.map(id=>Array.from(positions.slice(id*3,id*3+3))),w=length(cross(sub(v[1],v[0]),sub(v[2],v[0])))/2;if(!Number.isFinite(w))throw Error('Nonfinite regional triangle.');if(w<1e-14){degenerate++;continue}
  weights.push(w);area+=w;for(let k=0;k<3;k++){const c=(v[0][k]+v[1][k]+v[2][k])/3;values[k].push(c);sum[k]+=w*c;for(const p of v){bounds.min[k]=Math.min(bounds.min[k],p[k]);bounds.max[k]=Math.max(bounds.max[k],p[k])}}
 }
 if(weights.length<3)return {status:'insufficient_selected_surface',triangles:triangles.length/3,positive_area_triangles:weights.length,degenerate_triangles:degenerate,open_surface_patch:true};
 const low=values.map(v=>weightedQuantile(v,weights,.05)),high=values.map(v=>weightedQuantile(v,weights,.95)),spans=high.map((x,k)=>x-low[k]);
 return {status:'provisional_proxy_surface_metrics',triangles:triangles.length/3,positive_area_triangles:weights.length,degenerate_triangles:degenerate,surface_area:area,area_weighted_centroid:sum.map(x=>x/area),weighted_quantile_05:low,weighted_quantile_95:high,weighted_spans:{lateral:spans[0],height:spans[1],depth:spans[2]},bounds,depth_over_width:spans[0]>EPS?spans[2]/spans[0]:null,width_over_height:spans[1]>EPS?spans[0]/spans[1]:null,open_surface_patch:true,definition:'True selected proxy triangle area; area-weighted5–95% triangle-centroid spans in aligned canonical coordinates. Box clipping and pose affect descriptors. No tissue volume or circumference.'};
}
function triad(points){const origin=points.pelvis,up=unit(sub(points.waist,origin)),lateralRaw=sub(points.lateral,origin),lateral=unit(sub(lateralRaw,up.map(x=>x*dot(lateralRaw,up)))),front=cross(lateral,up);return {origin,length:length(sub(points.waist,origin)),basis:[lateral[0],up[0],front[0],lateral[1],up[1],front[1],lateral[2],up[2],front[2]]}}
function eulerFromR(r){const y=Math.asin(Math.max(-1,Math.min(1,-r[6]))),c=Math.cos(y);return [deg(Math.abs(c)>1e-7?Math.atan2(r[7],r[8]):0),deg(y),deg(Math.abs(c)>1e-7?Math.atan2(r[3],r[0]):Math.atan2(-r[1],r[4]))]}
export function alignReviewedTriad(landmarks,axes,axesReviewed){
 if(!axesReviewed)throw Error('Review donor up/front axes before aligning landmarks.');
 const donor={},target={};for(const role of ['pelvis','waist','lateral']){const pair=landmarks[role];if(!pair?.reviewed)throw Error('Review all three semantic landmark pairs first.');finiteVector(pair.donor_source,role+' donor');finiteVector(pair.canonical,role+' canonical');donor[role]=pair.donor_source;target[role]=pair.canonical}
 const a=triad(donor),b=triad(target),desired=mul(b.basis,transpose(a.basis)),extra=mul(desired,transpose(axisMatrix(axes))),registration={scale:b.length/a.length,rotation_degrees:eulerFromR(extra),translation:Array.from(b.origin),pivot_source:Array.from(a.origin),axes:{...axes}};
 const residuals=Object.fromEntries(['pelvis','waist','lateral'].map(role=>[role,length(sub(transformPoint(donor[role],registration),target[role]))]));
 return {registration,residuals,method:'Reviewed three-point right-handed frame alignment; uniform scale from pelvis-to-waist distance, lateral marker sets roll/orientation only. This is a similarity transform, NOT nonrigid anatomy transfer.'};
}
export function frameGuard(frame){if(!ACCEPTED_FRAMES.includes(Number(frame)))throw Error('Only accepted0000/0010/0018/0026 donors;0049 is excluded.');return Number(frame)}
export function registrationExport({frame,registration,landmarks,axesReviewed,roi,selectionMode,metrics,provenance,canonical,notes='',method='manual_similarity_transform'}){
 frameGuard(frame);validateROI(roi);const matrix=registrationMatrix(registration);
 return {schema:'rainee.reviewed-affine-donor-registration.v1',created_at:new Date().toISOString(),frame_number:Number(frame),stage_ordinal:ACCEPTED_FRAMES.indexOf(Number(frame))+1,accepted_endpoint:26,excluded_frames:[49],status:'artist_registration_candidate; no automatic adoption',alignment_method:method,transform:{...structuredClone(registration),...matrix},artist_review:{axes_reviewed:Boolean(axesReviewed),semantic_landmarks:structuredClone(landmarks)},canonical:{...structuredClone(canonical),donor_scale_changes_canonical_stature:false},selected_region:{roi:structuredClone(roi),membership:selectionMode,metrics:structuredClone(metrics)},provenance:structuredClone(provenance),camera_equivalence_confirmed:false,nonrigid_pose_correspondence_confirmed:false,anatomical_correspondence_confirmed:false,physical_volume_inferred:false,stage_numbers_are_ordinal:true,face_reference_role:'Intent links only; no donor face/identity/height copied',notes};
}
