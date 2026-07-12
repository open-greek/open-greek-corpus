#!/usr/bin/env python3
"""Upload an annotation-export release payload to the Hugging Face Hub.

Export payloads (works/*.jsonl.gz plus manifest.json and any license audit) live
on the Hub, not in git (docs/annotation-export-contract.md, "Storage"). git
tracks only the exporter script and the per-release pointer stub that
scripts/export_oga_annotations.py writes next to the release dir.

    HF token: ~/.cache/huggingface/token (or `hf auth login`).
    python3 scripts/upload_annotation_export.py data/annotations/oga/oga-v1
        [--repo ciscoriordan/open-greek-corpus-annotation-exports]

The release dir's basename is the release id and becomes the path in the repo
(oga-v1/ and, as queue items 1b-1e are built, ptnk-v1/ and so on). Uses the Hub
API (never git-LFS). After uploading, verifies that the file list on the Hub
under <release-id>/ matches the local payload exactly.
"""
import argparse
import sys
from pathlib import Path

DEFAULT_REPO = "ciscoriordan/open-greek-corpus-annotation-exports"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("release_dir", help="local release dir, e.g. data/annotations/oga/oga-v1")
    ap.add_argument("--repo", default=DEFAULT_REPO, help="target HF dataset repo id")
    ap.add_argument("--private", action="store_true")
    args = ap.parse_args()

    src = Path(args.release_dir).resolve()
    release_id = src.name
    if not (src / "manifest.json").is_file():
        sys.exit(f"no manifest.json under {src}; not an export release dir")
    local = sorted(str(p.relative_to(src)) for p in src.rglob("*") if p.is_file())
    if not any(p.startswith("works/") for p in local):
        sys.exit(f"no works/ payload under {src}")

    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(args.repo, repo_type="dataset", exist_ok=True, private=args.private)
    print(f"uploading {len(local)} files from {src} -> {args.repo}/{release_id}/")
    api.upload_folder(
        repo_id=args.repo, repo_type="dataset",
        folder_path=str(src), path_in_repo=release_id,
        commit_message=f"annotation export {release_id}",
    )

    remote = sorted(
        p[len(release_id) + 1:]
        for p in api.list_repo_files(args.repo, repo_type="dataset")
        if p.startswith(release_id + "/")
    )
    if remote != local:
        missing = sorted(set(local) - set(remote))
        extra = sorted(set(remote) - set(local))
        sys.exit(f"VERIFY FAILED: local {len(local)} vs hub {len(remote)} files; "
                 f"missing on hub: {missing[:5]}...; extra on hub: {extra[:5]}...")
    print(f"verified: {len(remote)} files on the Hub under {release_id}/ match local")
    print(f"done: https://huggingface.co/datasets/{args.repo}/tree/main/{release_id}")


if __name__ == "__main__":
    main()
