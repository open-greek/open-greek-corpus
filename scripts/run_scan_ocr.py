#!/usr/bin/env python3
"""Retain independent OCR witnesses of hash-pinned scan pages and regions.

This writes raw predictions, never edits corpus text. Run a small --limit first
before a long batch. Failed and truncated pages remain explicit in the output.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

from benchmark_page_ocr import PROMPT


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare_images(manifest, cache):
    import pymupdf
    cache.mkdir(parents=True, exist_ok=True)
    documents, images = {}, {}
    for page in manifest["pages"]:
        source = manifest["sources"][page["source"]]
        key = source["sha256"]
        if key not in documents:
            pdf = cache / (key + ".pdf")
            if not pdf.exists():
                with urlopen(source["url"], timeout=180) as response:
                    raw = response.read()
                if sha(raw) != key:
                    raise ValueError(f"Changed scan: {page['source']}")
                pdf.write_bytes(raw)
            if sha(pdf.read_bytes()) != key:
                raise ValueError(f"Corrupt scan cache: {page['source']}")
            documents[key] = pymupdf.open(pdf)
        document = documents[key]
        number = page["scan_page"]
        if not 1 <= number <= len(document):
            raise ValueError(f"Invalid scan page: {page['id']}")
        region = page.get("region", [0, 0, 1, 1])
        if len(region) != 4 or not (0 <= region[0] < region[2] <= 1 and 0 <= region[1] < region[3] <= 1):
            raise ValueError(f"Invalid page region: {page['id']}")
        sheet = document[number - 1]
        rect = sheet.rect
        clip = pymupdf.Rect(region[0] * rect.width, region[1] * rect.height,
                            region[2] * rect.width, region[3] * rect.height)
        scale = page.get("max_side", 2000) / max(clip.width, clip.height)
        pix = sheet.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False)
        raw = pix.tobytes("png")
        digest = sha(raw)
        path = cache / (digest + ".png")
        if not path.exists():
            path.write_bytes(raw)
        images[page["id"]] = (path, digest)
    for document in documents.values():
        document.close()
    return images


def http_prediction(args, image):
    payload = {"model": args.model, "temperature": 0, "top_p": 1,
               "max_tokens": args.max_tokens, "chat_template_kwargs": {"enable_thinking": False},
               "messages": [{"role": "user", "content": [
                   {"type": "image_url", "image_url": {"url": "data:image/png;base64," +
                                                           base64.b64encode(image.read_bytes()).decode()}},
                   {"type": "text", "text": PROMPT}]}]}
    req = Request(args.base_url.rstrip("/") + "/chat/completions",
                  data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=1800) as response:
        result = json.load(response)
    choice = result["choices"][0]
    return {"raw_prediction": choice["message"].get("content") or "",
            "finish_reason": choice.get("finish_reason"),
            "generation_tokens": result.get("usage", {}).get("completion_tokens")}


def run(args):
    raw_manifest = args.manifest.read_bytes()
    manifest = json.loads(raw_manifest)
    pages = manifest["pages"]
    if len({page["id"] for page in pages}) != len(pages):
        raise ValueError("Repeated scan page identity")
    if args.limit:
        pages = pages[:args.limit]
    metadata = {"model": args.model, "revision": args.revision, "prompt": PROMPT,
                "temperature": 0, "max_tokens": args.max_tokens, "backend": args.backend,
                "manifest_sha256": sha(raw_manifest), "runner_sha256": sha(Path(__file__).read_bytes())}
    if args.backend == "mlx":
        metadata["runtime"] = {name: importlib.metadata.version(name)
                               for name in ("mlx", "mlx-vlm", "transformers")}
    else:
        runtime = json.loads(args.runtime_manifest.read_text())
        if (runtime["model"], runtime["revision"]) != (args.model, args.revision):
            raise ValueError("Server runtime belongs to a different checkpoint")
        metadata["runtime"] = runtime
        with urlopen(args.base_url.rstrip("/") + "/models", timeout=30) as response:
            names = {m["id"] for m in json.load(response)["data"]}
        if args.model not in names:
            raise ValueError("Checkpoint is not served at this endpoint")
    existing = []
    if args.out.exists():
        rows = [json.loads(line) for line in args.out.read_text().splitlines() if line.strip()]
        if not rows or rows[0].get("_meta") != metadata:
            raise ValueError("Resume parameters differ")
        existing = rows[1:]
        known = {page["id"] for page in manifest["pages"]}
        if len({row["id"] for row in existing}) != len(existing) or any(row["id"] not in known for row in existing):
            raise ValueError("Repeated or unknown resumed scan page")
    done = {row["id"] for row in existing}
    pending = [page for page in pages if page["id"] not in done]
    if not pending:
        print("All selected pages already have retained results.")
        return
    images = prepare_images(dict(manifest, pages=pending), args.cache)
    if args.backend == "mlx":
        from huggingface_hub import snapshot_download
        from mlx_vlm import load, generate
        from mlx_vlm.prompt_utils import apply_chat_template
        import mlx.core as mx
        path = snapshot_download(args.model, revision=args.revision)
        model, processor = load(path)
        prompt = apply_chat_template(processor, model.config, PROMPT, num_images=1, enable_thinking=False)
        def predict(image):
            result = generate(model, processor, prompt, image=str(image), max_tokens=args.max_tokens,
                              temperature=0, verbose=False)
            count = getattr(result, "generation_tokens", None)
            mx.clear_cache()
            return {"raw_prediction": result.text, "generation_tokens": count,
                    "finish_reason": "length" if count is not None and count >= args.max_tokens else "stop"}
    else:
        predict = lambda image: http_prediction(args, image)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if not args.out.exists():
        args.out.write_text(json.dumps({"_meta": metadata}, ensure_ascii=False) + "\n")
    def one(page):
        start = time.monotonic()
        image, digest = images[page["id"]]
        try:
            result = predict(image)
        except Exception as error:
            result = {"raw_prediction": "", "finish_reason": "error",
                      "error": f"{type(error).__name__}: {error}"}
        return {"id": page["id"], "source": page["source"], "scan_page": page["scan_page"],
                "region": page.get("region", [0, 0, 1, 1]), "image_sha256": digest,
                **result, "seconds": round(time.monotonic() - start, 3)}
    with ThreadPoolExecutor(max_workers=1 if args.backend == "mlx" else args.workers) as pool:
        futures = [pool.submit(one, page) for page in pending]
        for future in as_completed(futures):
            row = future.result()
            with args.out.open("a") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(json.dumps({key: value for key, value in row.items() if key != "raw_prediction"}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=Path("data/cache/scan-ocr"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--backend", choices=("mlx", "http"), default="http")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--runtime-manifest", type=Path)
    parser.add_argument("--max-tokens", type=int, default=12000)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--limit", type=int)
    options = parser.parse_args()
    if options.backend == "http" and options.runtime_manifest is None:
        parser.error("HTTP inference requires --runtime-manifest")
    run(options)
