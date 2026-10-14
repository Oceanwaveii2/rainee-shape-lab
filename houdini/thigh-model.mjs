// Same Rainee-specific shape function as the native VEX sculpt.
export const THIGH_DEFAULTS={fullness:0,outer:1,front:1,inner:.45,back:.25,taper:.6,peak:.64};
const smooth=(a,b,x)=>{const s=Math.max(0,Math.min(1,(x-a)/(b-a)));return s*s*(3-2*s)};
const lerp=(a,b,t)=>a+(b-a)*t;
const ys=[.33,.355,.38,.405,.43,.455,.48,.505,.53],xs=[.121,.110,.101,.093,.087,.086,.083,.079,.077],zs=[.007,.019,.031,.038,.041,.034,.030,.027,.018];
export function sculptThighs(source,authored,options={},output=new Float32Array(source.length)) {
 const c={...THIGH_DEFAULTS,...options};
 if(!Number.isFinite(c.fullness)||Object.values(c).some(v=>!Number.isFinite(v)))throw Error('Invalid thigh control');
 if(source.length!==authored.length||output.length!==source.length)throw Error('Geometry size mismatch');
 output.set(authored);if(c.fullness===0)return output;
 for(let i=0;i<source.length;i+=3){
  const x=source[i],y=source[i+1],z=source[i+2],ax=Math.abs(x);
  if(y<=.34||y>=.535||ax>=.205)continue;
  const t=Math.max(0,Math.min(1,(y-.34)/.195)),profile=smooth(0,c.peak,t)*(1-smooth(c.peak,1,t));
  const seat=smooth(.49,.555,y)*(1-smooth(.667,.73,y))*(1-smooth(-.045,.015,z))*(1-smooth(.18,.22,ax));
  const mask=Math.pow(profile,lerp(.65,2,c.taper))*(1-smooth(0,.025,seat))*(1-smooth(.18,.205,ax));
  if(mask===0)continue;
  let cx=xs[0],cz=zs[0];
  for(let j=1;j<ys.length;j++)if(y>=ys[j-1]){const u=smooth(ys[j-1],ys[j],y);cx=lerp(xs[j-1],xs[j],u);cz=lerp(zs[j-1],zs[j],u)}
  const dx=ax-cx,dz=z-cz,strength=c.fullness*mask;
  let mx=dx*strength*lerp(c.inner,c.outer,smooth(-.006,.006,dx));
  const mz=dz*strength*lerp(c.back,c.front,smooth(-.006,.006,dz));
  if(mx<0){const room=Math.max(ax-.006,0);mx=room>0?-room*(1-Math.exp(mx/room)):0}
  output[i]=authored[i]+(x<0?-1:1)*mx;output[i+2]=authored[i+2]+mz;
 }
 return output;
}
