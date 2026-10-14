// Local-only resolver for numeric/API checks; no package installation.
const vendor=new URL('../../vendor/',import.meta.url);
export async function resolve(specifier,context,nextResolve){
 if(specifier==='three')return {url:new URL('package/build/three.module.js',vendor).href,shortCircuit:true};
 if(specifier.startsWith('three/addons/'))return {url:new URL('package/examples/jsm/'+specifier.slice(13),vendor).href,shortCircuit:true};
 if(specifier.startsWith('three/'))return {url:new URL('package/'+specifier.slice(6),vendor).href,shortCircuit:true};
 if(specifier==='@sparkjsdev/spark')return {url:new URL('spark/spark.module.js',vendor).href,shortCircuit:true};
 return nextResolve(specifier,context);
}
