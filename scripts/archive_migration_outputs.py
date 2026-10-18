#!/usr/bin/env python3
"""Archive historical outputs verified against the migration's recorded hashes.

These snapshots let undo tests exercise an older migration's exact output
state after unrelated migrations have changed shared metadata. Production
undo guards remain strict and continue to reject later edits. Bytes come from
the specified Git revision or an exact matching later migration's input archive.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def archive(root, audit_dir, revision):
    root = Path(root)
    relative = Path(audit_dir)
    if relative.is_absolute() or ".." in relative.parts or relative.parts[:2] != ("data", "corpus_changes"):
        raise ValueError("Audit must be a repository-relative corpus change directory")
    commit = subprocess.check_output(["git", "rev-parse", revision + "^{commit}"], cwd=root, text=True).strip()
    audit = json.loads((root / relative / "changes.json").read_text())
    snapshots, provenance = {}, {}
    archived = []
    for path in sorted((root / "data/corpus_changes").glob("*/before.json.gz")):
        value = json.loads(gzip.decompress(path.read_bytes()))
        archived.append((path, value))
    for path, digest in audit["outputs"].items():
        result = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=root, capture_output=True)
        if digest is None:
            if result.returncode == 0:
                raise ValueError(f"Expected an absent historical output: {path}")
            snapshots[path] = None
        else:
            if result.returncode or hashlib.sha256(result.stdout).hexdigest() != digest:
                matches = [(archive_path, before[path]) for archive_path, before in archived
                           if isinstance(before.get(path), str)
                           and hashlib.sha256(before[path].encode()).hexdigest() == digest]
                if not matches:
                    raise ValueError(f"No historical output matches the migration's recorded hash: {path}")
                archive_path, text = matches[0]
                snapshots[path] = text
                provenance[path] = {"before_archive": archive_path.relative_to(root).as_posix(),
                                    "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest()}
            else:
                snapshots[path] = result.stdout.decode("utf-8")
                provenance[path] = {"git_commit": commit}
    record = {"schema_version": 1, "source_commit": commit,
              "generator": "scripts/archive_migration_outputs.py", "sources": provenance, "files": snapshots}
    raw = (json.dumps(record, ensure_ascii=False, indent=1) + "\n").encode()
    target = root / relative / "after.json.gz"
    target.write_bytes(gzip.compress(raw, mtime=0))
    return len(snapshots)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    print(f"Archived {archive(ROOT, args.audit, args.revision)} verified historical outputs")
