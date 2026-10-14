"""Seal Git-visible review files as a verified, sub-100 MB transfer ZIP.

The budget applies to the ZIP, not uncompressed or expanded geometry. Heavy
original local datasets and ignored exports are never modified or included.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 100_000_000
MANIFEST = "documentation/packet-file-manifest.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def visible_files():
    output = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    )
    names = sorted(set(output.decode("utf-8").split("\0")) - {"", MANIFEST})
    result = []
    for name in names:
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError("Path outside repository: " + name)
        if path.is_file():
            result.append(name)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    output = args.out.resolve()
    if output.is_relative_to(ROOT):
        raise ValueError("Transfer ZIP must be outside the source repository")
    names = visible_files()
    rows = [{"path": name, "bytes": (ROOT / name).stat().st_size,
             "sha256": sha((ROOT / name).read_bytes())} for name in names]
    manifest = {
        "schema": "rainee-argon-packet-files-v1", "files": rows,
        "self_hash_excluded": MANIFEST,
        "scope": "Git-visible source/data snapshot; excludes Git history, ignored exports and all heavy original local datasets."
    }
    (ROOT / MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    names.append(MANIFEST)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(names):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (ROOT / name).read_bytes(), compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Transfer ZIP CRC check failed")
        assert set(archive.namelist()) == set(names)
        for row in rows:
            data = archive.read(row["path"])
            assert len(data) == row["bytes"] and sha(data) == row["sha256"], row["path"]
    size = output.stat().st_size
    digest = sha(output.read_bytes())
    receipt = {
        "schema": "rainee-argon-transfer-receipt-v1", "archive": str(output),
        "archive_bytes": size, "decimal_megabytes": size / 1_000_000,
        "limit_decimal_bytes": LIMIT, "strict_archive_budget_passed": size < LIMIT,
        "uncompressed_snapshot_bytes": sum((ROOT / n).stat().st_size for n in names),
        "files": len(names), "largest_file_bytes": max((ROOT / n).stat().st_size for n in names),
        "sha256": digest, "crc_and_every_file_hash_verified": True,
        "archive_manifest": MANIFEST,
        "scope": "Transfer archive only; extracted files and decoded meshes can exceed 100 MB."
    }
    output.with_suffix(".sha256").write_text(digest + "  " + output.name + "\n", encoding="utf-8")
    output.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    if size >= LIMIT:
        raise ValueError("Transfer ZIP is over the requested 100,000,000-byte limit")


if __name__ == "__main__":
    main()
