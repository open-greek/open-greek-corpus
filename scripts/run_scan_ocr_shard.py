#!/usr/bin/env python3
"""Run a pinned disjoint ID selection without rewriting its full manifest."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import time
from urllib.request import urlopen

import run_scan_ocr as original
from scan_ocr_bundle import encode, inspect_leaf, sha


def selected_pages(manifest, ids_path, limit=None):
    ids = json.loads(ids_path.read_bytes())
    if not isinstance(ids, list) or any(not isinstance(identifier, str) for identifier in ids):
        raise ValueError("Shard IDs must be a JSON list of strings")
    if len(set(ids)) != len(ids):
        raise ValueError("Repeated selected shard identity")
    if limit is not None:
        if limit < 1:
            raise ValueError("Preflight limit must be positive")
        ids = ids[:limit]
    pages = {page["id"]: page for page in manifest["pages"]}
    if len(pages) != len(manifest["pages"]) or not set(ids) <= set(pages):
        raise ValueError("Unknown or repeated manifest identity")
    return [pages[identifier] for identifier in ids]


def metadata_for(args, manifest_raw, pages, runtime):
    manifest = json.loads(manifest_raw)
    if (runtime.get("model"), runtime.get("revision")) != (args.model, args.revision):
        raise ValueError("Server runtime belongs to a different checkpoint")
    ids = [page["id"] for page in pages]
    return {"model": args.model, "revision": args.revision, "prompt": manifest["prompt"],
            "temperature": 0, "max_tokens": args.max_tokens, "backend": "http",
            "manifest_sha256": sha(manifest_raw),
            "runner": "scripts/run_scan_ocr_shard.py", "runner_sha256": sha(Path(__file__).read_bytes()),
            "image_and_http_helper_sha256": sha(Path(original.__file__).read_bytes()),
            "manifest_archive": "manifests/" + sha(manifest_raw) + ".json",
            "prompt_policy": "base prompt plus page prompt_suffix, falling back to the source prompt_suffix",
            "runtime": runtime,
            "shard": {"selected_ids": ids, "selection_sha256": sha(encode(ids)),
                      "selection_archive": "selections/" + sha(encode(ids)) + ".json"}}


def run(args):
    manifest_raw = args.manifest.read_bytes()
    manifest = json.loads(manifest_raw)
    pages = selected_pages(manifest, args.ids, args.limit)
    runtime = json.loads(args.runtime_manifest.read_bytes())
    meta = metadata_for(args, manifest_raw, pages, runtime)
    existing = []
    if args.out.exists():
        old_meta, rows = inspect_leaf(args.out.read_bytes(), manifest_raw)
        if old_meta != meta:
            raise ValueError("Resume checkpoint, runtime, manifest, or selected IDs changed")
        existing = list(rows.values())
    done = {row["id"] for row in existing}
    pending = [page for page in pages if page["id"] not in done]
    if not pending:
        print("Every selected identity already has a retained outcome.")
        return
    with urlopen(args.base_url.rstrip("/") + "/models", timeout=30) as response:
        names = {model["id"] for model in json.load(response)["data"]}
    if args.model not in names:
        raise ValueError("Checkpoint is not served at this endpoint")
    images = original.prepare_images(dict(manifest, pages=pending), args.cache)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for relative, raw in [(meta["manifest_archive"], manifest_raw),
                          (meta["shard"]["selection_archive"], encode(meta["shard"]["selected_ids"]))]:
        path = args.out.parent / relative
        if path.exists() and path.read_bytes() != raw:
            raise ValueError("Retained manifest or shard selection changed")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    if not args.out.exists():
        args.out.write_text(json.dumps({"_meta": meta}, ensure_ascii=False) + "\n")

    def one(page):
        start = time.monotonic()
        image, digest = images[page["id"]]
        suffix = page.get("prompt_suffix", manifest["sources"][page["source"]].get("prompt_suffix", ""))
        prompt = manifest["prompt"] + (" " + suffix if suffix else "")
        try:
            result = original.http_prediction(args, image, prompt)
        except Exception as error:
            result = {"raw_prediction": "", "finish_reason": "error", "error": f"{type(error).__name__}: {error}"}
        return {"id": page["id"], "source": page["source"], "scan_page": page["scan_page"],
                "region": page.get("region", [0, 0, 1, 1]), "image_sha256": digest,
                "prompt_sha256": sha(prompt.encode()), **result,
                "seconds": round(time.monotonic() - start, 3)}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, page) for page in pending]
        for future in as_completed(futures):
            row = future.result()
            with args.out.open("a") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(json.dumps({key: value for key, value in row.items() if key != "raw_prediction"}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--cache", type=Path, default=Path("data/cache/scan-ocr"))
    parser.add_argument("--max-tokens", type=int, default=12000)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    run(args)


if __name__ == "__main__":
    main()
