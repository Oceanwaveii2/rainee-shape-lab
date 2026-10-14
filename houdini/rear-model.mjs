export const REAR_DEFAULTS={lateral:1,vertical:1,projection:1,separation:.15,upper_pole:1.15,lower_pole:1,cleft_hold:.75};
function smooth(a,b,x){const s=Math.max(0,Math.min(1,(x-a)/(b-a)));return s*s*(3-2*s)}
export function deformRear(base,amp,controls=REAR_DEFAULTS,out=new Float64Array(base.length)){
 const c={...REAR_DEFAULTS,...controls};out.set(base);if(amp===0)return out;
 for(let i=0;i<base.length;i+=3){const x=base[i],y=base[i+1],z=base[i+2],ax=Math.abs(x);if(y<=.49||y>=.73||z>=.015||ax>=.22)continue;
  const mask=smooth(.49,.555,y)*(1-smooth(.667,.73,y))*(1-smooth(-.045,.015,z))*(1-smooth(.18,.22,ax));
  const cleft=1-c.cleft_hold*.7*(1-smooth(.004,.035,ax)),a=amp*mask*cleft,sx=1+a*c.lateral,cs=1+a*c.separation,cx=.073;
  const nx=ax<=cx?cx*cs*Math.pow(Math.min(ax/cx,1),sx/cs):cx*cs+(ax-cx)*sx;
  const pole=c.lower_pole+(c.upper_pole-c.lower_pole)*smooth(.595,.625,y);
  out[i]=(x<0?-1:1)*nx;out[i+1]=y+a*(y-.61)*c.vertical*pole;out[i+2]=z-a*(.025-z)*c.projection;
 }
 return out;
}
export function enclosedVolume(p,t){let sum=0;for(let i=0;i<t.length;i+=3){const a=3*t[i],b=3*t[i+1],c=3*t[i+2];sum+=p[a]*(p[b+1]*p[c+2]-p[b+2]*p[c+1])+p[a+1]*(p[b+2]*p[c]-p[b]*p[c+2])+p[a+2]*(p[b]*p[c+1]-p[b+1]*p[c])}return Math.abs(sum/6)}
export function calibrateRear(cage,triangles,ratio,controls=REAR_DEFAULTS){if(!Number.isFinite(ratio)||ratio<1||ratio>4)throw Error('Rear volume must be between 1× and 4×');const rest=enclosedVolume(cage,triangles);if(ratio===1)return {amplitude:0,cage:cage.slice(),ratio:1};let low=0,high=4,work=new Float64Array(cage.length);if(enclosedVolume(deformRear(cage,high,controls,work),triangles)<rest*ratio)throw Error('Shape cannot reach this volume');for(let i=0;i<32;i++){const mid=(low+high)/2;if(enclosedVolume(deformRear(cage,mid,controls,work),triangles)<rest*ratio)low=mid;else high=mid}const amplitude=(low+high)/2;deformRear(cage,amplitude,controls,work);return {amplitude,cage:work,ratio:enclosedVolume(work,triangles)/rest}}
export function activeRearSamples(body){const p=[];for(let i=0;i<body.length;i+=3)if(body[i+1]>.49&&body[i+1]<.73&&body[i+2]<.015&&Math.abs(body[i])<.22)p.push(body[i],body[i+1],body[i+2]);return new Float64Array(p)}
export function screenRear(samples,amp,c=REAR_DEFAULTS){if(!amp)return {minimum:1,nonpositive:0};const e=2e-5,derivatives=[];for(let k=0;k<3;k++){const a=samples.slice(),b=samples.slice();for(let i=k;i<a.length;i+=3){a[i]+=e;b[i]-=e}const pa=deformRear(a,amp,c),pb=deformRear(b,amp,c);for(let i=0;i<pa.length;i++)pa[i]=(pa[i]-pb[i])/(2*e);derivatives.push(pa)}let minimum=Infinity,nonpositive=0;const[a,b,d]=derivatives;for(let i=0;i<a.length;i+=3){const det=a[i]*(b[i+1]*d[i+2]-b[i+2]*d[i+1])-b[i]*(a[i+1]*d[i+2]-a[i+2]*d[i+1])+d[i]*(a[i+1]*b[i+2]-a[i+2]*b[i+1]);minimum=Math.min(minimum,det);if(det<=0)nonpositive++}return {minimum,nonpositive}}
