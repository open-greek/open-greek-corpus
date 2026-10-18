#!/usr/bin/env python3
"""Retain source-reviewed OCR retries under a separately pinned decoding policy.

The original greedy runner and benchmark remain immutable. These outcomes are
additional attempts by the same checkpoint, never additional independent votes.
Admission still requires a completed comparison against the pinned source scan.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

import run_scan_ocr as original

POLICY = {
    "id": "qwen-provider-instruct-retry-2026-10-18",
    "temperature": 0.7, "top_p": 0.8, "top_k": 20, "min_p": 0.0,
    "presence_penalty": 1.5, "repetition_penalty": 1.0, "seed": 20261018,
    "chat_template_kwargs": {"enable_thinking": False},
    "source_urls": ["https://huggingface.co/Qwen/Qwen3.6-27B#best-practices",
                    "https://huggingface.co/Qwen/Qwen3.8-27B-FP8#best-practices"],
    "scope": "Source-reviewed retry only; no automatic replacement or benchmark change.",
    "limits": "Provider settings may alter wording or mix scripts; every accepted outcome needs source comparison. A fixed seed does not guarantee identical results across hardware or batch schedules.",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def metadata(args, raw, manifest, runtime):
    if (runtime.get("model"), runtime.get("revision")) != (args.model, args.revision):
        raise ValueError("Retry server belongs to another checkpoint")
    scope = manifest.get("checkpoints")
    if scope and (args.model, args.revision) not in {(v["model"], v["revision"]) for v in scope}:
        raise ValueError("Checkpoint is outside the reviewed retry authority")
    if not manifest.get("review") or not manifest.get("pages") or not manifest.get("prompt"):
        raise ValueError("A source-reviewed request and explicit prompt are required")
    ids = [p["id"] for p in manifest["pages"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Repeated reviewed retry identity")
    return {"model": args.model, "revision": args.revision, "prompt": manifest["prompt"],
            "temperature": POLICY["temperature"], "max_tokens": args.max_tokens,
            "backend": "http", "manifest_sha256": sha(raw),
            "manifest_archive": "manifests/" + sha(raw) + ".json",
            "runner": "scripts/run_reviewed_scan_retry.py",
            "runner_sha256": sha(Path(__file__).read_bytes()),
            "image_helper_sha256": sha(Path(original.__file__).read_bytes()),
            "runtime": runtime, "generation_policy": POLICY,
            "prompt_policy": "base prompt plus page prompt_suffix, falling back to the source prompt_suffix"}


def payload(args, image, prompt):
    values = {key: value for key, value in POLICY.items()
              if key not in {"id", "source_urls", "scope", "limits"}}
    return {**values, "model": args.model, "max_tokens": args.max_tokens,
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," +
                     base64.b64encode(image.read_bytes()).decode()}},
                {"type": "text", "text": prompt}]}]}


def predict(args, image, prompt):
    request = Request(args.base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload(args, image, prompt)).encode(),
        headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=1800) as response:
        result = json.load(response)
    choice = result["choices"][0]
    output = {"raw_prediction": choice["message"].get("content") or "",
              "finish_reason": choice.get("finish_reason"),
              "generation_tokens": result.get("usage", {}).get("completion_tokens")}
    if choice["message"].get("reasoning_content"):
        output["retained_reasoning_content"] = choice["message"]["reasoning_content"]
    return output


def run(args):
    raw = args.manifest.read_bytes()
    manifest = json.loads(raw)
    meta = metadata(args, raw, manifest, json.loads(args.runtime_manifest.read_bytes()))
    pages = manifest["pages"][:args.limit] if args.limit else manifest["pages"]
    selected = {p["id"] for p in pages}
    done = set()
    if args.out.exists():
        rows = [json.loads(line) for line in args.out.read_bytes().splitlines() if line.strip()]
        if not rows or rows[0] != {"_meta": meta}:
            raise ValueError("Retry resume policy, source, runner or runtime changed")
        ids = [r["id"] for r in rows[1:]]
        if len(ids) != len(set(ids)) or not set(ids) <= {p["id"] for p in manifest["pages"]}:
            raise ValueError("Repeated or unknown retained retry outcome")
        done.update(ids)
    pending = [p for p in pages if p["id"] not in done]
    if not pending:
        print("Every selected retry already has a retained outcome.")
        return
    with urlopen(args.base_url.rstrip("/") + "/models", timeout=30) as response:
        served = {m["id"] for m in json.load(response)["data"]}
    if args.model not in served:
        raise ValueError("The reviewed checkpoint is not served")
    images = original.prepare_images(dict(manifest, pages=pending), args.cache)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    archive = args.out.parent / meta["manifest_archive"]
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists() and archive.read_bytes() != raw:
        raise ValueError("Retained retry request changed")
    archive.write_bytes(raw)
    if not args.out.exists():
        args.out.write_text(json.dumps({"_meta": meta}, ensure_ascii=False) + "\n")

    def one(page):
        start = time.monotonic()
        image, digest = images[page["id"]]
        suffix = page.get("prompt_suffix", manifest["sources"][page["source"]].get("prompt_suffix", ""))
        prompt = manifest["prompt"] + (" " + suffix if suffix else "")
        try:
            result = predict(args, image, prompt)
        except Exception as error:
            result = {"raw_prediction": "", "finish_reason": "error",
                      "error": f"{type(error).__name__}: {error}"}
        return {"id": page["id"], "source": page["source"], "scan_page": page["scan_page"],
                "region": page.get("region", [0, 0, 1, 1]), "image_sha256": digest,
                "prompt_sha256": sha(prompt.encode()), **result,
                "seconds": round(time.monotonic() - start, 3)}

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, page) for page in pending]
        for future in as_completed(futures):
            row = future.result()
            if row["id"] not in selected:
                raise ValueError("Unexpected retry outcome")
            with args.out.open("a") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(json.dumps({key: value for key, value in row.items() if key != "raw_prediction"}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runtime-manifest", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--cache", type=Path, default=Path("data/cache/scan-ocr"))
    parser.add_argument("--max-tokens", type=int, default=6000)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.workers < 1 or args.max_tokens < 1 or (args.limit is not None and args.limit < 1):
        parser.error("Workers, output limit and optional preflight count must be positive")
    run(args)


if __name__ == "__main__":
    main()
