"""Read-only comparison of the newly attached bust ZIP against the earlier ZIP."""
import hashlib,json,stat,zipfile
from pathlib import Path,PurePosixPath,PureWindowsPath

HERE=Path(__file__).resolve().parent
DOWNLOADS=Path('C:/Users/User/Downloads')
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def inspect(path):
    entries=[];seen=set();total=0
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            name=entry.filename.replace('\\','/');relative=PurePosixPath(name);win=PureWindowsPath(name)
            if relative.is_absolute() or win.is_absolute() or win.drive or '..' in relative.parts or ':' in name:
                raise ValueError('Unsafe archive path')
            if name.casefold() in seen or stat.S_ISLNK(entry.external_attr>>16):raise ValueError('Duplicate archive target or symlink')
            seen.add(name.casefold());total+=entry.file_size
            if total>512*1024*1024 or entry.file_size>256*1024*1024:raise ValueError('Archive exceeds bounded inspection size')
            data={'name':name,'bytes':entry.file_size,'compressed_bytes':entry.compress_size,'extension':relative.suffix.lower(),'directory':entry.is_dir()}
            if not entry.is_dir():
                with archive.open(entry) as stream:data['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            entries.append(data)
    return {'source_path':str(path.resolve()),'archive_bytes':path.stat().st_size,'archive_sha256':sha(path),
        'total_member_bytes':total,'entries':entries,'read_only':True,'extracted':False,'executed':False}

def main():
    old=inspect(DOWNLOADS/'f9f63233-cc50-4a28-8c61-7c45affbdbbb.zip')
    new=inspect(DOWNLOADS/'f9f63233-cc50-4a28-8c61-7c45affbdbbb (1).zip')
    oldmembers={e['name']:e.get('sha256') for e in old['entries'] if not e['directory']}
    newmembers={e['name']:e.get('sha256') for e in new['entries'] if not e['directory']}
    changes=[]
    for name in sorted(set(oldmembers)|set(newmembers)):
        if name not in oldmembers:changes.append({'name':name,'status':'added','new_sha256':newmembers[name]})
        elif name not in newmembers:changes.append({'name':name,'status':'removed','old_sha256':oldmembers[name]})
        elif oldmembers[name]!=newmembers[name]:changes.append({'name':name,'status':'changed','old_sha256':oldmembers[name],'new_sha256':newmembers[name]})
    inventory_path=HERE.parent/'worldgen-20261013/inventory.json'
    inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
    record=next(r for r in inventory['archives'] if r['archive_name']=='f9f63233-cc50-4a28-8c61-7c45affbdbbb.zip')
    status='exact_archive_duplicate' if old['archive_sha256']==new['archive_sha256'] else 'same_member_payloads_different_container' if not changes else 'revised_asset_payloads'
    report={'new':new,'earlier':old,'status':status,'member_payloads_identical':not changes,
        'changed_members':changes,'earlier_archive_matches_recorded_worldgen_sha256':old['archive_sha256']==record['archive_sha256'],
        'action':'No extraction or replacement. Reuse earlier copied bust assets.' if not changes else 'No extraction or replacement. Revised payloads inventoried for separate review.',
        'face_authority':'Additional generated3D candidate/reference only; no automatic exact face/camera acceptance or head replacement.',
        'provenance_inventory':str(inventory_path.resolve())}
    (HERE/'new-bust-archive.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'status':status,'member_payloads_identical':not changes,'changed_members':len(changes),
        'archive_bytes':new['archive_bytes'],'new_sha256':new['archive_sha256'],'extracted':False}))
if __name__=='__main__':main()
