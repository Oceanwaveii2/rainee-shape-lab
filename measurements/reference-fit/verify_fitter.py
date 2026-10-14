"""Meaningful math, transfer and bounded-search checks for the regional fitter."""
from pathlib import Path
import json,numpy as np
from fit_regional_rear import describe,features,RearFitter,PARAMETERS,BOUNDS,ROOT

# A closed, irregular tetrahedral shell gives non-degenerate principal axes.
p=np.array([[0.,0,0],[2.,0,0],[0.,1.,0],[0.,0,.6]])
f=np.array([[0,2,1],[0,1,3],[0,3,2],[1,2,3]])
# Repetition does not modify relative moments; it makes the generic ROI sample
# count gate valid for this tiny known fixture without changing its measures.
f=np.tile(f,(6,1));a=describe(p,f)
t=.6;R=np.array([[np.cos(t),0,np.sin(t)],[0,1,0],[-np.sin(t),0,np.cos(t)]])
b=describe((p@R.T)*2.7+np.array([7.,-3.,4.]),f)
assert np.allclose([a['pca_middle_over_major'],a['pca_minor_over_major']],
 [b['pca_middle_over_major'],b['pca_minor_over_major']],rtol=1e-12,atol=1e-12)
# Split all faces into three at their centroid: exact surface covariance must
# be unchanged. The 5-95% centroid spans are intentionally approximation cues.
pp=p.tolist();ff=[]
for tri in f:
 m=p[tri].mean(0);i=len(pp);pp.append(m.tolist())
 ff.extend([[tri[0],tri[1],i],[tri[1],tri[2],i],[tri[2],tri[0],i]])
c=describe(np.array(pp),np.array(ff))
assert np.allclose(a['pca_std_axes_ascending'],c['pca_std_axes_ascending'],rtol=1e-12,atol=1e-12)
report=json.loads((ROOT/'reference-fit.json').read_text())
assert report['status']=='needs_registration' and report['comparison_ready'] is False and report['accepted_winner'] is None
assert report['diagnostic_search']['evaluations']<=95
candidate=report['diagnostic_candidate'];assert candidate is not None
assert all(lo<=candidate['parameters'][name]<=hi for name,(lo,hi) in zip(PARAMETERS,BOUNDS))
fit=RearFitter(report['target_shared_features']);x=[candidate['parameters'][k] for k in PARAMETERS]
_,entry=fit.evaluate(x,record=False)
assert np.isclose(entry['score'],candidate['score'],rtol=1e-9)
assert abs(entry['measured_cage_volume_ratio']/x[0]-1)<2e-6
v,f=fit.full_candidate(entry)
assert np.ptp(v[:,1])==np.ptp(fit.full[:,1])
assert np.isfinite(v).all() and candidate['jacobian_guard']['nonpositive']==0
mask=np.zeros(len(v),bool);mask[fit.region_point_ids]=True
result={'pass':True,'checks':['Exact surface PCA ratios invariant under rigid rotation, uniform scale and translation',
 'Exact surface covariance invariant under triangle subdivision','Unregistered target blocks accepted winner',
 'Objective evaluation count stays below95','Candidate parameters remain within declared bounds',
 'Candidate score reproducible from production field','Closed control-cage volume ratio matches volume parameter',
 'Full repaired candidate retains source height, finite points and positive sampled field orientation'],
 'evaluations':report['diagnostic_search']['evaluations'],'cage_ratio':entry['measured_cage_volume_ratio'],
 'candidate_height_drift':0.,'jacobian_min_determinant':candidate['jacobian_guard']['min_determinant'],
 'partial_objective_points':len(fit.region_point_ids),'partial_source_points_needed':len(fit.required_source_ids),
 'full_body_points':len(fit.full),'limitation':'Optimization hit the declared evaluation cap; candidate is exploratory and not accepted.'}
(ROOT/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
