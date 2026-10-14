// Source-frame policy. Stage ordinals are independent of cage-volume controls.
export const APPROVED_FRAMES=Object.freeze([0,10,18,26]);
export function cacheFrame(sourceFrame){
 const f=Number(sourceFrame);if(!Number.isFinite(f))throw Error('Source frame must be finite.');
 return Math.min(26,Math.max(0,Math.round(f)));
}
export function approvedReference(sourceFrame){
 const f=cacheFrame(sourceFrame);return APPROVED_FRAMES.filter(x=>x<=f).at(-1);
}
export function sequenceLabel(sourceFrame){
 const f=Math.max(0,Math.round(Number(sourceFrame))),reference=approvedReference(f),ordinal=APPROVED_FRAMES.indexOf(reference)+1;
 return f>26?`Frame ${String(f).padStart(4,'0')} · endpoint held from 0026`:`Frame ${String(f).padStart(4,'0')} · ${f===reference?'stage '+ordinal:'between approved stages'}`;
}
