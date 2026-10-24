#!/usr/bin/env python3
"""Retain fresh pinned-checkpoint OCR of the two recovered Hesychius columns.

Images are captured and hash checked by capture_hesychius_gap.py. This command
never changes served text. Independent checkpoints and physical scan identities
remain explicit; repeated runs of a checkpoint do not create additional votes.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

PROMPT = (
    "Transcribe all the printed text in this image exactly, in reading order, "
    "one line per printed line. Include Greek text, Latin reference citations, "
    "and reference numbers. Preserve all Greek accents, breathing marks, "
    "punctuation, editorial parentheses, square brackets, daggers, and printed "
    "hyphens. Do not omit citation lines or their delimiters. Do not correct, translate, summarize, "
    "complete a cut-off entry, or add explanations. Return only the transcription."
)
MODELS = {
    "qwen38": ("mlx-community/Qwen3.8-27B-8bit", "815b83c0df8ffd1d1b5244cf75fd6ef14fca9ef9"),
    "qwen36": ("mlx-community/Qwen3.6-27B-8bit", "c5a593c1475a746e43a543b0a02bd2b357e5745f"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run(args):
    from huggingface_hub import snapshot_download
    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    import mlx.core as mx

    root = Path(__file__).resolve().parents[1]
    raw = args.manifest.read_bytes()
    manifest = json.loads(raw)
    model_id, revision = MODELS[args.checkpoint]
    metadata = {"checkpoint": args.checkpoint, "model": model_id, "revision": revision,
        "prompt": PROMPT, "prompt_sha256": sha(PROMPT.encode()), "temperature": 0,
        "max_tokens": args.max_tokens, "manifest_sha256": sha(raw),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "runtime": {name: importlib.metadata.version(name)
                    for name in ("mlx", "mlx-vlm", "transformers")}}
    done = set()
    if args.out.exists():
        rows = [json.loads(line) for line in args.out.read_text().splitlines()]
        if rows[0].get("_meta") != metadata:
            raise ValueError("Resume checkpoint, prompt, or manifest differs")
        done = {r["id"] for r in rows[1:]}
    selected = [r for r in manifest["columns"] if r["id"] not in done]
    if args.limit:
        selected = selected[:args.limit]
    if not selected:
        print("All selected columns already retained.")
        return
    model, processor = load(snapshot_download(model_id, revision=revision))
    prompt = apply_chat_template(processor, model.config, PROMPT,
                                 num_images=1, enable_thinking=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if not args.out.exists():
        args.out.write_text(json.dumps({"_meta": metadata}, ensure_ascii=False) + "\n")
    for column in selected:
        path = root / column["path"]
        if sha(path.read_bytes()) != column["sha256"]:
            raise ValueError("Column crop changed: " + column["id"])
        started = time.monotonic()
        result = generate(model, processor, prompt, image=str(path),
                          max_tokens=args.max_tokens, temperature=0, verbose=False)
        count = getattr(result, "generation_tokens", None)
        record = {"id": column["id"], "source": column["source"],
            "printed_column": column["printed_column"], "image_sha256": column["sha256"],
            "raw_prediction": result.text, "generation_tokens": count,
            "finish_reason": "length" if count is not None and count >= args.max_tokens else "stop",
            "seconds": round(time.monotonic() - started, 3)}
        with args.out.open("a") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(json.dumps({k: v for k, v in record.items() if k != "raw_prediction"}), flush=True)
        mx.clear_cache()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--checkpoint", choices=MODELS, required=True)
    parser.add_argument("--max-tokens", type=int, default=4500)
    parser.add_argument("--limit", type=int)
    run(parser.parse_args())
