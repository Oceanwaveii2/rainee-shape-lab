import {auditTemplateSequence} from './lab-state.mjs';
self.onmessage=({data:{id,project}})=>{try{self.postMessage({id,audit:auditTemplateSequence(project)})}catch(error){self.postMessage({id,error:error.message})}};
