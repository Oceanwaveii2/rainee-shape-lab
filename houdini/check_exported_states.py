import numpy as np,json,pathlib
r=pathlib.Path(__file__).resolve().parent;report=json.loads((r/'verification-native.json').read_text());base=np.fromfile(r/'body-1x.bin',dtype='<f4').reshape(-1,3)
protected=(base[:,1]>.73)|(base[:,1]<.49)|(base[:,2]>=.015)|(np.abs(base[:,0])>=.22)
report['exported_simulated_body_checks']=[]
for f in [24,48,72]:
 p=np.fromfile(r/f'body-sim-{f}.bin',dtype='<f4').reshape(-1,3);assert len(p)==len(base);assert np.isfinite(p).all()
 drift=float(np.ptp(p[:,1])-np.ptp(base[:,1]));fixed=float(np.max(np.abs(p[protected]-base[protected])))
 assert abs(drift)<1e-7 and fixed<1e-7
 report['exported_simulated_body_checks'].append({'frame':f,'height_drift':drift,'max_protected_displacement':fixed})
report['max_sampled_volume_error']=max(d['relative_volume_error'] for d in report['dynamic'])
assert report['max_sampled_volume_error']<.01
report['dynamic_smoke_passed']=all(not d['solver_errors'] for d in report['dynamic']) and report['max_sampled_volume_error']<.01
(r/'verification-native.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['exported_simulated_body_checks'],indent=2));print('MAX_VOLUME_ERROR',report['max_sampled_volume_error'])
