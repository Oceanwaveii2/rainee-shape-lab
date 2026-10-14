"""Validate a local model ZIP and extract data assets only; never execute entries."""
import argparse,hashlib,json,stat,zipfile
from pathlib import Path,PurePosixPath,PureWindowsPath

ALLOWED={".obj",".glb",".gltf",".bin",".mtl",".png",".jpg",".jpeg",".webp",".json"}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("zip");parser.add_argument("--out",required=True);args=parser.parse_args()
    source=Path(args.zip);out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    entries=[];total=0
    with zipfile.ZipFile(source) as archive:
        seen=set()
        for entry in archive.infolist():
            name=entry.filename.replace("\\","/");path=PurePosixPath(name);win=PureWindowsPath(entry.filename)
            if path.is_absolute() or win.is_absolute() or win.drive or ".." in path.parts or ":" in name or "\x00" in name:
                raise ValueError("Unsafe archive path")
            mode=entry.external_attr>>16
            if stat.S_ISLNK(mode):raise ValueError("Archive symlinks are not extracted")
            resolved=(out/Path(*path.parts)).resolve()
            if not resolved.is_relative_to(out):raise ValueError("Archive path escapes output")
            if name.casefold() in seen:raise ValueError("Duplicate archive target")
            seen.add(name.casefold());total+=entry.file_size
            if total>512*1024*1024 or entry.file_size>256*1024*1024:raise ValueError("Archive exceeds bounded size")
            allowed=path.suffix.lower() in ALLOWED or name.endswith(".mtl.original")
            entries.append({"name":name,"bytes":entry.file_size,"compressed_bytes":entry.compress_size,
                "directory":entry.is_dir(),"extract":allowed and not entry.is_dir()})
        for entry,report in zip(archive.infolist(),entries):
            if not report["extract"]:continue
            target=(out/report["name"]).resolve();target.parent.mkdir(parents=True,exist_ok=True)
            data=archive.read(entry) # CRC is validated by zipfile.
            digest=hashlib.sha256(data).hexdigest();report["sha256"]=digest
            if target.exists() and hashlib.file_digest(target.open("rb"),"sha256").hexdigest()!=digest:
                raise ValueError("Existing output differs; refusing overwrite")
            if not target.exists():target.write_bytes(data)
    report={"archive_source":str(source.resolve()),"archive_bytes":source.stat().st_size,
        "archive_sha256":hashlib.file_digest(source.open("rb"),"sha256").hexdigest(),
        "total_uncompressed_bytes":total,"output_root":str(out),"entries":entries,
        "safety":"Validated relative paths, no drives/traversal/duplicates/symlinks; bounded sizes; asset allowlist; CRC checked; no execution."}
    (out/"archive-inventory.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"output":str(out),"total_uncompressed_bytes":total,"assets_extracted":sum(e["extract"] for e in entries)}))
if __name__=="__main__":main()
