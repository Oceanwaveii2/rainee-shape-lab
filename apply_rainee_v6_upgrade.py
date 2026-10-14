"""Apply a reviewed text upgrade with source backups and rollback on failed tests.
Use the corrected bundle matching this revision, not Argon's original bundle.
"""
from pathlib import Path,PurePosixPath
import argparse,datetime,json,stat,subprocess,sys,zipfile

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path('.'))
    parser.add_argument('--bundle',type=Path)
    parser.add_argument('--node',default='node')
    args=parser.parse_args();repo=args.repo.resolve()
    if not (repo/'houdini/viewer-config.json').is_file():
        raise ValueError('Expected Rainee project root containing houdini/viewer-config.json')
    payload={}
    if args.bundle:
        with zipfile.ZipFile(args.bundle) as archive:
            total=0
            for info in archive.infolist():
                if info.is_dir():continue
                rel=PurePosixPath(info.filename);destination=repo.joinpath(*rel.parts).resolve()
                if (rel.is_absolute() or '..' in rel.parts or '\\' in info.filename or ':' in info.filename
                    or not destination.is_relative_to(repo) or any(part.startswith('.') for part in rel.parts)
                    or stat.S_ISLNK(info.external_attr>>16)
                    or rel.suffix.lower() not in {'.py','.ps1','.js','.mjs','.html','.md','.json','.txt','.vfl'}):
                    raise ValueError('Unexpected upgrade entry: '+info.filename)
                if info.file_size>8_000_000:raise ValueError('Oversized text entry')
                total+=info.file_size
                if total>80_000_000:raise ValueError('Upgrade exceeds text budget')
                if info.filename in payload:raise ValueError('Duplicate archive entry')
                data=archive.read(info);data.decode('utf-8');payload[info.filename]=data
        if 'verify_v6_supercomputer.py' not in payload:raise ValueError('Bundle lacks verification runner')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=repo/'.rainee-upgrade-backups'/stamp
    original={name:(repo/name).read_bytes() if (repo/name).is_file() else None for name in payload}
    if payload:
        for name,data in original.items():
            if data is not None:
                target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        backup.mkdir(parents=True,exist_ok=True)
        (backup/'manifest.json').write_text(json.dumps({'new_files':[n for n,b in original.items() if b is None]},indent=2))
    try:
        for name,data in payload.items():
            target=repo/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        subprocess.run([sys.executable,str(repo/'verify_v6_supercomputer.py'),'--node',args.node],cwd=repo,check=True)
    except BaseException:
        for name,data in original.items():
            target=repo/name
            if data is None:target.unlink(missing_ok=True)
            else:target.write_bytes(data)
        print('Verification failed; installed source files restored.',file=sys.stderr);raise
    print('Reviewed upgrade verified.'+(' Backups: '+str(backup) if payload else ''))

if __name__=='__main__':main()
