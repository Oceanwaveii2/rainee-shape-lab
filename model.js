export const defaults={hip:1,seat:0,thigh:1,waist:1,pelvis:1,seatLift:0,hipY:.60,waistY:.715,thighY:.51,spread:.115,height:175,reverse:false};
export const study={...defaults,hip:1.4,seat:.055,thigh:1.3,waist:.90,pelvis:1.08,seatLift:.015};
export const specs=[['hip','Outer hip fullness',.65,2.5,.01],['seat','Rear projection',-.04,.18,.002],['thigh','Upper thigh volume',.7,2,.01],['waist','Waist taper',.55,1.35,.01],['pelvis','Pelvis breadth',.8,1.5,.01],['seatLift','Seat height offset',-.05,.07,.001]];
export const landmarks=[['hipY','Hip level',.3,.65,.005],['waistY','Waist level',.45,.8,.005],['thighY','Thigh level',.35,.6,.005],['spread','Hip falloff',.06,.22,.005]];
function bump(d,r){const t=Math.abs(d)/r;return t>=1?0:Math.pow(1-t*t,3);}
export function deform(base,out,p){
 const front=p.reverse?-1:1;
 for(let i=0;i<base.length;i+=3){const x=base[i],y=base[i+1],z=base[i+2];
  const coreWidth=.185-.095*Math.max(0,Math.min(1,(y-.63)/.05));
  const mask=1-Math.max(0,Math.min(1,(Math.abs(x)-coreWidth)/.035));
  const hip=mask*bump(y-p.hipY,p.spread),waist=mask*bump(y-p.waistY,.105)*bump(x,.24),thigh=mask*bump(y-p.thighY,.12),pelvis=mask*bump(y-p.hipY,.08);
  const rear=Math.max(0,Math.min(1,(-z*front+.015)/.09));
  out[i]=x*(1+(p.hip-1)*hip+(p.pelvis-1)*pelvis+(p.waist-1)*waist+(p.thigh-1)*thigh);
  out[i+1]=y+p.seatLift*hip*rear;
  out[i+2]=z*(1+(p.waist-1)*waist*.7+(p.thigh-1)*thigh*.55)-front*p.seat*hip*rear*bump(x,.3);
 }
 return out;
}
export function section(positions,indices,y,base=positions){let xmin=Infinity,xmax=-Infinity,zmin=Infinity,zmax=-Infinity,n=0;
 const limit=.205-.085*Math.max(0,Math.min(1,(y-.63)/.05));
 for(let t=0;t<indices.length;t+=3){for(let e=0;e<3;e++){const a=indices[t+e]*3,b=indices[t+(e+1)%3]*3;if(Math.abs(base[a])>limit||Math.abs(base[b])>limit)continue;const ya=positions[a+1],yb=positions[b+1];if((ya<=y&&yb>y)||(yb<=y&&ya>y)){const f=(y-ya)/(yb-ya),x=positions[a]+f*(positions[b]-positions[a]),z=positions[a+2]+f*(positions[b+2]-positions[a+2]);xmin=Math.min(xmin,x);xmax=Math.max(xmax,x);zmin=Math.min(zmin,z);zmax=Math.max(zmax,z);n++;}}}
 return n?{width:xmax-xmin,depth:zmax-zmin}:null;
}
export function validatePreset(input){const p={...defaults};for(const [key,,lo,hi] of [...specs,...landmarks,['height','Height',50,300]]){if(typeof input[key]!=='number'||!Number.isFinite(input[key])||input[key]<lo||input[key]>hi)throw Error('Invalid preset value: '+key);p[key]=input[key];}if(typeof input.reverse!=='boolean')throw Error('Invalid orientation');p.reverse=input.reverse;return p;}
