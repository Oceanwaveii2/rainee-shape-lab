"""Exercise clean install, traversal rejection and rollback in disposable roots."""
from pathlib import Path
import subprocess,sys,tempfile,zipfile

ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='rainee-applier-test-') as folder:
    tmp=Path(folder);repo=tmp/'repo';(repo/'houdini').mkdir(parents=True)
    (repo/'houdini/viewer-config.json').write_text('{}')
    original=repo/'module.py';original.write_text('original\n')
    def run(bundle):return subprocess.run([sys.executable,str(ROOT/'apply_rainee_v6_upgrade.py'),'--repo',str(repo),'--bundle',str(bundle)],capture_output=True,text=True)
    unsafe=tmp/'unsafe.zip'
    with zipfile.ZipFile(unsafe,'w') as z:z.writestr('../outside.py','bad');z.writestr('verify_v6_supercomputer.py','')
    assert run(unsafe).returncode!=0 and not (tmp/'outside.py').exists() and original.read_text()=='original\n'
    failed=tmp/'failed.zip'
    with zipfile.ZipFile(failed,'w') as z:
        z.writestr('module.py','changed\n');z.writestr('new.py','new\n');z.writestr('verify_v6_supercomputer.py','raise SystemExit(7)\n')
    assert run(failed).returncode!=0 and original.read_text()=='original\n' and not (repo/'new.py').exists()
    good=tmp/'good.zip'
    with zipfile.ZipFile(good,'w') as z:z.writestr('module.py','upgraded\n');z.writestr('verify_v6_supercomputer.py','print("fixture verifier passed")\n')
    assert run(good).returncode==0 and original.read_text()=='upgraded\n'
print('PASS 3 isolated applier cases: preflight, rollback and verified install')
