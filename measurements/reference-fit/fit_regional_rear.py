"""Bounded CPU fitting of existing Rainee rear controls to local shape cues.

No donor height/body/topology is transferred. Provisional ROI/pose labels gate
adoption; a diagnostic numerical minimum is not an accepted anatomical fit.
"""
from pathlib import Path
import sys,json,hashlib,itertools,time,argparse
import numpy as np
from scipy.optimize import minimize

ROOT=Path(__file__).resolve().parent
APP=ROOT.parents[1]
HOUDINI=APP/'houdini'
sys.path.insert(0,str(HOUDINI));import rear_model
sys.path.insert(0,str(HOUDINI/'pelvic-repair'));from apply_repair import apply as apply_repair,load_recipe
sys.path.insert(0,str(APP/'measurements'));import model_compare

SOURCE_REGIONS={
 'rear':{'min':[-.180,.530,-.150],'max':[.180,.697,.010],
   'exclude_perineal_core':{'abs_x_max':.042,'y_max':.615,'z_min':-.075},
   'confidence':'Provisional posterior lobe/pelvis ROI, stable selected source triangle IDs; perineal core excluded.'},
 'waist':{'min':[-.100,.695,-.080],'max':[.100,.724,.100],
   'confidence':'Provisional central narrow torso surface window. Source is incomplete, so no closed waist circumference is claimed.'}}
BOUNDS=[(1.,2.5),(.4,1.6),(.4,1.6),(.4,1.6)]
PARAMETERS=['volume','lateral','vertical','projection']
METRIC_WEIGHTS={'rear_depth_over_width':.45,'rear_width_over_height':.45,
 'rear_pca_middle_over_major':1.,'rear_pca_minor_over_major':1.,
 'rear_to_waist_width':.20,'rear_to_waist_depth':.05}
DEFINITIONS={
 'area_weighted_spans':'Weighted 5th-to-95th percentiles of triangle centroids along lateral/up/depth; weights are true selected triangle areas.',
 'pca':'Exact area-integrated triangle surface covariance; square roots of ascending eigenvalues relative to the largest. Rotation invariant and independent of planar triangle subdivision for a fixed surface patch.',
 'membership':'Region selection is applied once to baseline triangle centroids, then locked while Rainee deforms. No dynamic box clipping.',
 'ratios':'No stature normalization from the target. Ratios within each surface patch or between rear and waist are dimensionless.',
 'not_measured':'Enclosed anatomical/tissue volume, waist circumference, hidden anatomy, donor height, facial identity, or production artistic match.'}

def weighted_quantile(x,w,q):
 order=np.argsort(x,kind='stable');xx=x[order];ww=w[order]
 c=(np.cumsum(ww)-.5*ww)/ww.sum()
 return np.interp(q,c,xx)

def describe(points,faces):
 tri=np.asarray(points,dtype=np.float64)[faces];centroid=tri.mean(1)
 weights=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
 keep=weights>1e-14;tri=tri[keep];centroid=centroid[keep];weights=weights[keep]
 if len(weights)<20:raise ValueError('Insufficient regional surface samples')
 low=np.array([weighted_quantile(centroid[:,a],weights,.05) for a in range(3)])
 high=np.array([weighted_quantile(centroid[:,a],weights,.95) for a in range(3)])
 span=high-low;mean=np.average(centroid,axis=0,weights=weights)
 # For a uniform triangle, E[pp^T] = (sum_i p_i p_i^T + ss^T)/12,
 # s=sum_i p_i. This retains within-triangle variance and avoids treating
 # triangle density as surface mass.
 centered=tri-mean;sumv=centered.sum(1)
 second=np.einsum('nki,nkj->nij',centered,centered)+np.einsum('ni,nj->nij',sumv,sumv)
 cov=np.einsum('nij,n->ij',second,weights)/(12*weights.sum())
 eig=np.linalg.eigvalsh(cov);r=np.sqrt(np.maximum(eig,0))
 return {'triangles':len(faces),'positive_area_triangles':len(weights),'surface_area':float(weights.sum()),
   'weighted_centroid':mean.tolist(),'weighted_quantile_05':low.tolist(),'weighted_quantile_95':high.tolist(),
   'weighted_spans':{'lateral':float(span[0]),'height':float(span[1]),'depth':float(span[2])},
   'pca_std_axes_ascending':r.tolist(),'depth_over_width':float(span[2]/span[0]),
   'width_over_height':float(span[0]/span[1]),'pca_middle_over_major':float(r[1]/r[2]),
   'pca_minor_over_major':float(r[0]/r[2]),'open_surface_patch':True}

def features(regions):
 r=regions['rear'];w=regions['waist'];a=r['weighted_spans'];b=w['weighted_spans']
 return {'rear_depth_over_width':r['depth_over_width'],'rear_width_over_height':r['width_over_height'],
   'rear_pca_middle_over_major':r['pca_middle_over_major'],'rear_pca_minor_over_major':r['pca_minor_over_major'],
   'rear_to_waist_width':a['lateral']/b['lateral'],'rear_to_waist_depth':a['depth']/b['depth']}

def roi_faces(v,f,config,extra=None):
 c=v[f].mean(1);keep=((c>=np.array(config['min']))&(c<=np.array(config['max']))).all(1)
 if extra is not None:keep&=extra
 exclusion=config.get('exclude_perineal_core')
 if exclusion:keep&=~((abs(c[:,0])<exclusion['abs_x_max'])&(c[:,1]<exclusion['y_max'])&(c[:,2]>exclusion['z_min']))
 return f[keep],keep

def target_descriptors(folder):
 target=json.loads((folder/'local-shape-constraints.json').read_text())
 v=np.fromfile(folder/'source-positions.bin','<f4').reshape(-1,3)
 f=np.fromfile(folder/'source-triangles.bin','<u4').reshape(-1,3)
 roles=np.fromfile(folder/'candidate-face-roles.bin','u1');extra=np.isin(roles,target['configuration']['candidate_role_ids'])
 oriented=v[:,[2,1,0]].astype(float) # Target source Z lateral, Y up, X depth.
 descriptions={};masks={}
 for name in ['rear','waist']:
  selected,mask=roi_faces(v,f,target['configuration']['regions'][name],extra)
  descriptions[name]=describe(oriented,selected);masks[name]=mask
 return target,descriptions,masks

class RearFitter:
 def __init__(self,target_features,maximum_evaluations=95):
  self.base=np.fromfile(APP/'assets/positions.bin','<f4').reshape(-1,3)
  self.cage=np.fromfile(HOUDINI/'cage-rest.bin','<f4').reshape(-1,3)
  self.cf=np.fromfile(HOUDINI/'cage-triangles.bin','<u4').reshape(-1,3)
  self.recipe=load_recipe();self.full,self.faces=apply_repair(self.base,self.recipe)
  selected={};self.masks={}
  for name,config in SOURCE_REGIONS.items():selected[name],self.masks[name]=roi_faces(self.full,self.faces,config)
  globalids=np.unique(np.concatenate([x.ravel() for x in selected.values()]))
  self.region_point_ids=globalids;remap=np.full(len(self.full),-1,dtype=int);remap[globalids]=np.arange(len(globalids))
  self.region_faces={k:remap[f] for k,f in selected.items()}
  old=globalids[globalids<len(self.base)];newids=globalids[globalids>=len(self.base)]-len(self.base)
  self.oldids=old;self.newids=newids
  binds=self.recipe['nearest_source'][newids]
  self.required_source_ids=np.unique(np.concatenate((old,binds.ravel())))
  sourcemap=np.full(len(self.base),-1,dtype=int);sourcemap[self.required_source_ids]=np.arange(len(self.required_source_ids))
  self.oldmap=sourcemap[old];self.bindmap=sourcemap[binds];self.bindweight=self.recipe['weights'][newids]
  self.target=target_features;self.history=[];self.maximum_evaluations=maximum_evaluations

 def evaluate(self,x,record=True):
  if record and len(self.history)>=self.maximum_evaluations:raise RuntimeError('Evaluation budget reached')
  x=np.clip(np.array(x,float),[b[0] for b in BOUNDS],[b[1] for b in BOUNDS]);controls=dict(zip(PARAMETERS[1:],x[1:]))
  amp,cage=rear_model.calibrate(self.cage,self.cf,float(x[0]),controls)
  src=self.base[self.required_source_ids];deformed=rear_model.deform(src,amp,controls)
  delta=deformed-src
  extra=self.recipe['new_baseline'][self.newids]+(delta[self.bindmap]*self.bindweight[:,:,None]).sum(1)
  local=np.vstack((deformed[self.oldmap],extra))
  regions={k:describe(local,f) for k,f in self.region_faces.items()};feat=features(regions)
  errors={k:float(np.log(feat[k]/self.target[k])) for k in METRIC_WEIGHTS}
  data=sum(METRIC_WEIGHTS[k]*errors[k]**2 for k in errors)
  # A small prior resolves parameter ambiguity without overriding measured cues.
  prior=.015*float(np.sum(((x-np.array([1.5,1.,1.,1.]))/np.array([1.5,1.2,1.2,1.2]))**2))
  score=data+prior
  entry={'parameters':dict(zip(PARAMETERS,x.tolist())),'amplitude':float(amp),'score':float(score),
    'data_score':float(data),'regularization_score':float(prior),'features':feat,'log_residuals':errors,
    'measured_cage_volume_ratio':float(rear_model.volume(cage,self.cf)/rear_model.volume(self.cage,self.cf)),
    'regions':regions}
  if record:self.history.append(entry)
  return score,entry

 def search(self):
  # Seventeen coarse checks + at most sixty Powell calls stay under 100 total.
  self.evaluate([1.,1.,1.,1.])
  for p in itertools.product([1.3,1.9],[.65,1.35],[.65,1.35],[.75,1.5]):self.evaluate(p)
  start=min(self.history,key=lambda e:e['score'])['parameters']
  result=minimize(lambda x:self.evaluate(x)[0],[start[k] for k in PARAMETERS],method='Powell',bounds=BOUNDS,
    options={'maxfev':60,'maxiter':8,'xtol':.02,'ftol':.002})
  ranked=sorted(self.history,key=lambda e:e['score']);candidate=None;guards=[]
  for e in ranked[:8]:
   c={k:e['parameters'][k] for k in PARAMETERS[1:]};guard=rear_model.jacobian_screen(self.base,e['amplitude'],c)
   guards.append({'score':e['score'],**guard})
   if guard['nonpositive']==0 and guard['min_determinant']>0.03:
    candidate={**e,'jacobian_guard':guard};break
  observed={k:{'min':min(e['features'][k] for e in self.history),'max':max(e['features'][k] for e in self.history),
    'target':self.target[k],'target_below_all_evaluated':self.target[k]<min(e['features'][k] for e in self.history),
    'target_above_all_evaluated':self.target[k]>max(e['features'][k] for e in self.history)} for k in self.target}
  return candidate,{'method':'17 coarse evaluations + bounded Powell, max60 extra objective calls','evaluations':len(self.history),
    'optimizer_success':bool(result.success),'optimizer_message':str(result.message),'jacobian_candidates_screened':guards,
    'observed_feature_ranges':observed,'observed_ranges_limitation':'Ranges cover the evaluated states, not a proof of global infeasibility over continuous parameter bounds.',
    'registration_independent_field_guard':'Finite-difference field orientation, not triangle contact or artistic acceptance'}

 def full_candidate(self,entry):
  c={k:entry['parameters'][k] for k in PARAMETERS[1:]}
  src=rear_model.deform(self.base,entry['amplitude'],c)
  return apply_repair(src,self.recipe)

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--target',type=Path,default=APP/'measurements/reference-01a13749')
 parser.add_argument('--diagnostic',action='store_true',help='Run soft constraints despite unregistered target; adoption stays disabled')
 args=parser.parse_args();started=time.time()
 target,tdesc,tmasks=target_descriptors(args.target);tf=features(tdesc);fit=RearFitter(tf)
 baseline=fit.evaluate([1.,1.,1.,1.],record=False)[1]
 axes_accepted=False;pose_accepted=False;rois_accepted=False
 comparison_ready=axes_accepted and pose_accepted and rois_accepted
 source_labels=np.zeros(len(fit.full),dtype=int)
 for i,(name,mask) in enumerate(fit.masks.items(),1):
  source_labels[np.unique(fit.faces[mask])]=i
  mask.astype('u1').tofile(ROOT/f'source-{name}-face-mask.bin')
 model_compare.preview(fit.full,source_labels,ROOT/'source-regional-roi-preview.png',caption='Source ROI candidates: turquoise rear, orange waist; original height retained')
 report={'status':'needs_registration','comparison_ready':comparison_ready,'accepted_winner':None,
  'target':str(args.target/'local-shape-constraints.json'),'source':'FBX-derived Rainee proxy plus local structural repair',
  'definitions':DEFINITIONS,'source_regions':SOURCE_REGIONS,'target_regions':target['configuration']['regions'],
  'target_axis_mapping':{'lateral':'source Z','height':'source Y','depth':'source X'},
  'registration':{'axes_accepted':axes_accepted,'local_pelvis_pose_accepted':pose_accepted,'ROI_correspondence_accepted':rois_accepted},
  'target_shared_descriptors':tdesc,'target_shared_features':tf,'source_baseline':baseline,
  'bounds':dict(zip(PARAMETERS,BOUNDS)),'metric_weights':METRIC_WEIGHTS,
  'held_source_controls':{k:v for k,v in rear_model.DEFAULTS.items() if k not in PARAMETERS},
  'equation':'E(theta) = sum_k w_k [log(m_k(theta)/t_k)]^2 + 0.015 ||(theta-theta_prior)/parameter_range||^2',
  'volume_equation':'Existing cage calibration solves |V_closed_cage(D(theta))| / |V_closed_cage(rest)| = volume by bisection; tissue volume is not measured.',
  'limitations':['Target rear/waist color-role ROIs are provisional outside-surface patches; hair, arms, clothing or pelvis overlap may contaminate descriptors.',
   'Target is posed with turned torso and bent leg. PCA ratios are rotation invariant for a fixed patch, but the patch selection itself is not pose invariant.',
   'Axis-aligned local spans and rear/waist ratios are low-weight diagnostic cues until local pelvis axes and corresponding patches are accepted.',
   'No donor height, topology, face, or global proportions are transferred. No enclosed anatomical volume is inferred.',
   'No numerical optimum is an accepted fit while comparison_ready is false. Artist approval here means accepted correspondence, not permission to execute local analysis.']}
 if args.diagnostic:
  candidate,search=fit.search();report['diagnostic_search']=search;report['diagnostic_candidate']=candidate
  (ROOT/'evaluated-candidates.json').write_text(json.dumps([{k:e[k] for k in ['parameters','amplitude','score','features']} for e in fit.history],indent=2))
  if candidate:
   cv,cf=fit.full_candidate(candidate);cv.astype('<f4').tofile(ROOT/'diagnostic-candidate-positions.bin');cf.astype('<u4').tofile(ROOT/'diagnostic-candidate-triangles.bin')
   assert np.ptp(cv[:,1])==np.ptp(fit.full[:,1])
   model_compare.preview(cv,source_labels,ROOT/'diagnostic-candidate-roi-preview.png',caption='Unregistered diagnostic candidate; source height/identity retained')
   report['candidate_checks']={'finite':bool(np.isfinite(cv).all()),'height_drift':float(np.ptp(cv[:,1])-np.ptp(fit.full[:,1])),
    'protected_source_points_max_displacement':float(np.max(np.abs(cv[:len(fit.base)][rear_model.region(fit.base)==0]-fit.base[rear_model.region(fit.base)==0]))),
    'field_orientation_passed':candidate['jacobian_guard']['nonpositive']==0}
   (ROOT/'parameter-preset-candidate.json').write_text(json.dumps({'enabled':False,'status':'unregistered diagnostic soft-constraint candidate',
    'parameters':candidate['parameters'],'amplitude':candidate['amplitude'],'source_height_transfer':False,
    'reason':'Local pelvis axes, pose and corresponding ROI selections are not accepted; do not automatically adopt.'},indent=2))
 else:report['diagnostic_search']={'status':'skipped','reason':'Target needs corresponding local pelvis/waist registration. --diagnostic permits a labeled exploratory candidate.'}
 report['elapsed_seconds']=time.time()-started
 report['input_hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [args.target/'local-shape-constraints.json',HOUDINI/'rear_model.py',HOUDINI/'cage-rest.bin']}
 (ROOT/'reference-fit.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({'status':report['status'],'comparison_ready':False,'target_features':tf,'source_features':baseline['features'],
  'search':report.get('diagnostic_search'),'candidate_parameters':report.get('diagnostic_candidate',{}).get('parameters') if report.get('diagnostic_candidate') else None,
  'elapsed_seconds':report['elapsed_seconds']},indent=2))

if __name__=='__main__':main()
