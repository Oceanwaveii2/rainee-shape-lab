import {auditTemplateSequence} from './lab-state.mjs';
/** The project carries the selected engine; the worker uses the renderer's dispatcher. */
export function auditProjectMessage({id,project}){try{return {id,audit:auditTemplateSequence(project)}}catch(error){return {id,error:error.message}}}
if(typeof self!=='undefined')self.onmessage=({data})=>self.postMessage(auditProjectMessage(data));
