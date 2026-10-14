"""Re-run numerical and state tests; no report is evidence of reference likeness.
Python: numpy, scipy, Pillow. Node: pass --node if not on PATH.
Retained geometry is decoded in memory, preserving the lean repository budget.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, sys, time
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'measurements'),str(ROOT/'tools')]
from retained_asset import read_retained_asset

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node',default='node')
    args=parser.parse_args()
    report_path=ROOT/'verification-v6-supercomputer.json'
    report={'schema':'rainee-reviewed-v6-verification-v1','passed':False,'suites':[],
            'scope':'CPU numerical, mesh and saved-state checks; no browser/GPU, likeness, physical-contact or Class-A certification'}
    report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    commands=[
        [sys.executable,'measurements/test_model_compare.py'],
        [sys.executable,'measurements/test_local_shape_constraints.py'],
        [sys.executable,'measurements/test_v6_numerics.py'],
        [sys.executable,'houdini/test_curvilinear_v5_join.py'],
        [sys.executable,'tools/verify_upgrade_applier.py'],
        [args.node,'houdini/verify_curvilinear_v5.mjs'],
        [args.node,'houdini/lab/anatomy-model.verify.mjs'],
        [args.node,'houdini/lab/state-verification.mjs'],
        [args.node,'houdini/lab/engine-state.test.mjs'],
        [args.node,'houdini/lab/argon-v5.test.mjs'],
        [args.node,'houdini/lab/argon-source-parity.test.mjs'],
        [args.node,'measurements/v6-numerics.verify.mjs'],
        [args.node,'research/gaussian-growth/frosting-field.verify.mjs'],
        [args.node,'houdini/lab/measurements/verify-measurement-model.mjs'],
    ]
    try:
        import numpy as np
        import butt_data_supercomputer_v6 as bds
        import model_compare as mc
        for cmd in commands:
            start=time.monotonic()
            result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
            entry={'command':cmd,'passed':result.returncode==0,'seconds':round(time.monotonic()-start,3),
                   'stdout':result.stdout[-5000:],'stderr':result.stderr[-2000:]}
            report['suites'].append(entry)
            report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(('PASS ' if entry['passed'] else 'FAIL ')+cmd[1],flush=True)
            if not entry['passed']:
                raise RuntimeError(result.stdout+result.stderr)
        v4=np.frombuffer(read_retained_asset(ROOT/'houdini/body-v4-rest.bin'),dtype='<f4').reshape(-1,3).astype(float)
        fig=np.frombuffer(read_retained_asset(ROOT/'houdini/body-figurine-native.bin'),dtype='<f4').reshape(-1,3).astype(float)
        config={'y_fold_norm':.43,'y_waist_norm':.62,'cleft_yaw_offset_deg':0.,'spinal_torsion_deg':0.}
        dem,cal=mc.calibrated_intrinsic_pelvic(v4,config)
        donor,donor_cal=mc.calibrated_intrinsic_pelvic(fig,config)
        assert not cal.get('anatomical_calibration',True)
        assert np.isfinite(cal['nurbs_posterior_rms_error'])
        model=bds.ButtMorphableModel(max_components=4)
        model.add_donor('v4-working-body',dem['elevation'])
        model.add_donor('provisional-figurine-fit',donor['elevation'])
        model.add_donor('synthetic-radial-scale-1.25',dem['elevation']*1.25)
        projected=model.project(donor['elevation'])
        report['exploratory_training_diagnostic']={
            'v4_chart_fit_rms_pelvic_units':cal['nurbs_posterior_rms_error'],
            'figurine_chart_fit_rms_pelvic_units':donor_cal['nurbs_posterior_rms_error'],
            'training_donor_projection_rms':projected['rms_error'],
            'donor_count':3,'synthetic_donors':1,'held_out_accuracy':None,
            'scope':'Manual whole-body chart bounds; not anatomically calibrated. Training projection is not a prediction test.'}
        report['passed']=True
    except BaseException as error:
        report['error']=str(error);raise
    finally:
        report['module_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in [ROOT/'measurements/butt_data_supercomputer_v6.py',ROOT/'houdini/lab/lab-state.mjs',ROOT/'houdini/lab/anatomy-model.mjs']}
        report_path.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'suite_count':len(report['suites']),'report':str(report_path)}))

if __name__=='__main__':main()
