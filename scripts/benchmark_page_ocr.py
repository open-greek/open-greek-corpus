#!/usr/bin/env python3
"""Pin PAGE XML ground truth and measure OCR without discarding failed pages.

prepare records immutable image/XML hashes and a fixed calibration/test split.
run uses a pinned multimodal model through MLX; score can also evaluate external
predictions. The raw transcription is retained, including repetitions and errors.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import re
import platform
import time
import unicodedata
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

SOURCE = "https://zenodo.org/records/20008699"
PROMPT = ("Transcribe the printed text in this image exactly, in reading order, "
          "one line per printed line. Preserve Greek accents, breathing marks, "
          "punctuation, and printed hyphens. Do not correct, translate, summarize, "
          "or add explanations. Return only the transcription.")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).split())


def fold(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold())
                   if not unicodedata.combining(c)).replace("ς", "σ")


def distance(a, b):
    try:
        from rapidfuzz.distance import Levenshtein
        return Levenshtein.distance(a, b)
    except ImportError:
        if len(a) < len(b):
            a, b = b, a
        previous = list(range(len(b) + 1))
        for i, x in enumerate(a, 1):
            current = [i]
            for j, y in enumerate(b, 1):
                current.append(min(previous[j] + 1, current[-1] + 1,
                                   previous[j - 1] + (x != y)))
            previous = current
        return previous[-1]


def page_gold(path):
    root = ET.parse(path).getroot()
    ns = {"p": root.tag.split("}")[0][1:]}
    page = root.find("p:Page", ns)
    if page is None:
        raise ValueError(f"Not PAGE XML: {path}")
    # Only line-level TextEquiv; nested word transcriptions are not additional text.
    lines = []
    for line in page.findall(".//p:TextLine", ns):
        alternatives = line.findall("p:TextEquiv", ns)
        alternatives.sort(key=lambda e: int(e.get("index", "0")))
        if alternatives:
            text = alternatives[0].findtext("p:Unicode", default="", namespaces=ns)
            if text.strip():
                lines.append(text.strip())
    if not lines:
        raise ValueError(f"No line-level ground truth: {path}")
    return page.get("imageFilename"), "\n".join(lines)


def score(gold, prediction):
    gold, prediction = normalize(gold), normalize(prediction)
    gw, pw = gold.split(), prediction.split()
    errors = distance(gold, prediction)
    word_errors = distance(gw, pw)
    fg, fp = fold(gold), fold(prediction)
    return {"gold_chars": len(gold), "pred_chars": len(prediction),
            "char_errors": errors, "cer": errors / max(1, len(gold)),
            "gold_words": len(gw), "word_errors": word_errors,
            "wer": word_errors / max(1, len(gw)),
            "folded_char_errors": distance(fg, fp), "folded_gold_chars": len(fg),
            "length_ratio": len(prediction) / max(1, len(gold)),
            "empty": not prediction}


def edition_group(name):
    match = re.search(r"(?:mpg|PG[_ -]*)(\d+)", name, flags=re.I)
    if match:
        return "pg-" + match.group(1)
    if name.startswith("grc_grna_or_"):
        return "gregory-nazianzus-orations"
    return "unknown"


def prepare(root, output, count=100, seed=20261012, groups=None):
    pages = []
    for xml in sorted(root.rglob("*.xml")):
        try:
            image_name, text = page_gold(xml)
        except (ET.ParseError, ValueError):
            continue
        image = xml.parent / (image_name or "")
        if not image.is_file():
            image = next((xml.with_suffix(ext) for ext in (".jpg", ".png", ".jpeg")
                          if xml.with_suffix(ext).is_file()), None)
        if image is None or not text.strip():
            continue
        group = edition_group(xml.stem)
        if groups and group not in groups:
            continue
        pages.append({"id": xml.relative_to(root).with_suffix("").as_posix(),
                      "xml": xml.relative_to(root).as_posix(),
                      "image": image.relative_to(root).as_posix(),
                      "xml_sha256": sha256(xml), "image_sha256": sha256(image),
                      "gold_sha256": hashlib.sha256(text.encode()).hexdigest(),
                      "gold_chars": len(normalize(text)),
                      "volume": group})
    # Round-robin volumes after seeded shuffling prevents the largest volume
    # from consuming the sample; the untouched test set is fixed before tuning.
    rng = random.Random(seed)
    groups = {}
    for page in pages:
        groups.setdefault(page["volume"], []).append(page)
    for group in groups.values():
        rng.shuffle(group)
    selected = []
    while groups and len(selected) < count:
        for volume in sorted(list(groups)):
            if len(selected) >= count:
                break
            selected.append(groups[volume].pop())
            if not groups[volume]:
                del groups[volume]
    within_volume = Counter()
    for page in selected:
        i = within_volume[page["volume"]]
        page["split"] = "calibration" if i % 5 == 0 else "test"
        within_volume[page["volume"]] += 1
    manifest = {"schema_version": 1, "source": SOURCE, "license": "CC-BY-4.0",
                "selection_seed": seed, "available_pages": len(pages),
                "normalization": "NFC and whitespace only; no output trimming or failed-page exclusion",
                "pages": selected}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def summarize(rows):
    result = {}
    for split in ("calibration", "test", "all"):
        subset = [r for r in rows if split == "all" or r["split"] == split]
        if not subset:
            continue
        chars = sum(r["metrics"]["gold_chars"] for r in subset)
        words = sum(r["metrics"]["gold_words"] for r in subset)
        folded = sum(r["metrics"]["folded_gold_chars"] for r in subset)
        result[split] = {"pages": len(subset),
                        "cer": sum(r["metrics"]["char_errors"] for r in subset) / max(1, chars),
                        "wer": sum(r["metrics"]["word_errors"] for r in subset) / max(1, words),
                        "folded_cer": sum(r["metrics"]["folded_char_errors"] for r in subset) / max(1, folded),
                        "empty_pages": sum(r["metrics"]["empty"] for r in subset),
                        "failed_pages": sum(bool(r.get("error")) for r in subset),
                        "truncated_pages": sum(r.get("finish_reason") == "length" for r in subset),
                        "length_outliers": sum(not 0.6 <= r["metrics"]["length_ratio"] <= 1.6 for r in subset),
                        "max_page_cer": max(r["metrics"]["cer"] for r in subset)}
    return result


def http_completion(args, image):
    """Send one complete page, with thinking explicitly disabled."""
    mime = "image/png" if image.suffix.lower() == ".png" else "image/jpeg"
    payload = {"model": args.model, "temperature": 0, "top_p": 1,
               "max_tokens": args.max_tokens, "chat_template_kwargs": {"enable_thinking": False},
               "messages": [{"role": "user", "content": [
                   {"type": "image_url", "image_url": {"url":
                    f"data:{mime};base64," + base64.b64encode(image.read_bytes()).decode()}},
                   {"type": "text", "text": PROMPT}]}]}
    request = Request(args.base_url.rstrip("/") + "/chat/completions",
                      data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=900) as response:
        result = json.load(response)
    choice = result["choices"][0]
    return {"raw_prediction": choice["message"].get("content") or "",
            "finish_reason": choice.get("finish_reason"),
            "generation_tokens": result.get("usage", {}).get("completion_tokens")}


def http_page(args, page):
    image, xml = args.root / page["image"], args.root / page["xml"]
    if sha256(image) != page["image_sha256"] or sha256(xml) != page["xml_sha256"]:
        raise ValueError(f"Changed benchmark input: {page['id']}")
    _, gold = page_gold(xml)
    start = time.monotonic()
    try:
        prediction = http_completion(args, image)
    except Exception as error:
        # Failed pages remain in the denominator and keep their error evidence.
        prediction = {"raw_prediction": "", "error": f"{type(error).__name__}: {error}",
                      "finish_reason": "error", "generation_tokens": None}
    return {"id": page["id"], "split": page["split"], "volume": page["volume"],
            **prediction, "metrics": score(gold, prediction["raw_prediction"]),
            "seconds": round(time.monotonic() - start, 3)}


def run(args):
    manifest = json.loads(args.manifest.read_text())
    backend = getattr(args, "backend", "mlx")
    metadata = {"manifest_sha256": sha256(args.manifest), "model": args.model,
                "revision": args.revision, "prompt": PROMPT, "temperature": 0,
                "max_tokens": args.max_tokens, "runner": "scripts/benchmark_page_ocr.py",
                "runner_sha256": sha256(Path(__file__)),
                "backend": backend,
                "runtime_versions": {name: importlib.metadata.version(name)
                                     for name in ("mlx", "mlx-vlm", "transformers")} if backend == "mlx"
                                    else {"python": platform.python_version()}}
    if backend == "http":
        runtime = json.loads(args.runtime_manifest.read_text())
        if runtime["model"] != args.model or runtime["revision"] != args.revision:
            raise ValueError("Server runtime manifest belongs to a different model revision")
        metadata.update(inference_runtime=runtime, workers=args.workers)
        with urlopen(args.base_url.rstrip("/") + "/models", timeout=30) as response:
            available = {item["id"] for item in json.load(response)["data"]}
        if args.model not in available:
            raise ValueError("Requested model is not served by this endpoint")
    pages = [p for p in manifest["pages"] if args.split == "all" or p["split"] == args.split]
    if args.limit:
        pages = pages[:args.limit]
    rows = []
    if args.out.exists():
        existing = [json.loads(line) for line in args.out.read_text().splitlines()]
        if existing[0]["_meta"] != metadata:
            raise ValueError("Resume parameters differ from the existing run")
        rows = existing[1:]
    done = {row["id"] for row in rows}
    pending = [p for p in pages if p["id"] not in done]
    if pending and backend == "http":
        args.out.parent.mkdir(parents=True, exist_ok=True)
        if not args.out.exists():
            args.out.write_text(json.dumps({"_meta": metadata}) + "\n")
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(http_page, args, page) for page in pending]
            for future in as_completed(futures):
                row = future.result()
                rows.append(row)
                with args.out.open("a") as stream:
                    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                print(json.dumps({k: v for k, v in row.items() if k != "raw_prediction"}), flush=True)
    elif pending:
        from huggingface_hub import snapshot_download
        from mlx_vlm import load, generate
        from mlx_vlm.prompt_utils import apply_chat_template
        model_path = snapshot_download(args.model, revision=args.revision)
        print(f"Loading {args.model}@{args.revision}", flush=True)
        model, processor = load(model_path)
        prompt = apply_chat_template(processor, model.config, PROMPT, num_images=1,
                                     enable_thinking=False)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        if not args.out.exists():
            args.out.write_text(json.dumps({"_meta": metadata}) + "\n")
        for page in pending:
            image, xml = args.root / page["image"], args.root / page["xml"]
            if sha256(image) != page["image_sha256"] or sha256(xml) != page["xml_sha256"]:
                raise ValueError(f"Changed benchmark input: {page['id']}")
            _, gold = page_gold(xml)
            start = time.monotonic()
            print(f"Starting {page['id']}", flush=True)
            result = generate(model, processor, prompt, image=str(image),
                              max_tokens=args.max_tokens, temperature=0, verbose=False)
            raw = result.text
            row = {"id": page["id"], "split": page["split"], "volume": page["volume"],
                   "raw_prediction": raw, "metrics": score(gold, raw),
                   "seconds": round(time.monotonic() - start, 3),
                   "generation_tokens": getattr(result, "generation_tokens", None)}
            rows.append(row)
            with args.out.open("a") as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(json.dumps({k: v for k, v in row.items() if k != "raw_prediction"}), flush=True)
    summary = {"_meta": metadata, "metrics": summarize(rows)}
    args.out.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary["metrics"], indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--root", type=Path, required=True)
    prepare_parser.add_argument("--out", type=Path, required=True)
    prepare_parser.add_argument("--count", type=int, default=100)
    prepare_parser.add_argument("--seed", type=int, default=20261012)
    prepare_parser.add_argument("--groups", nargs="+",
                                help="Restrict to named edition groups before sampling")
    runner = sub.add_parser("run")
    for name in ("root", "manifest", "out"):
        runner.add_argument(f"--{name}", type=Path, required=True)
    runner.add_argument("--model", required=True)
    runner.add_argument("--revision", required=True)
    runner.add_argument("--split", choices=("calibration", "test", "all"), default="calibration")
    runner.add_argument("--backend", choices=("mlx", "http"), default="mlx")
    runner.add_argument("--base-url", default="http://127.0.0.1:8000/v1")
    runner.add_argument("--runtime-manifest", type=Path)
    runner.add_argument("--workers", type=int, default=4)
    runner.add_argument("--limit", type=int)
    runner.add_argument("--max-tokens", type=int, default=12000)
    comparison = sub.add_parser("compare")
    comparison.add_argument("--baseline", type=Path, required=True)
    comparison.add_argument("--candidate", type=Path, required=True)
    comparison.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        data = prepare(args.root, args.out, args.count, args.seed, args.groups)
        print(json.dumps({"available": data["available_pages"], "selected": len(data["pages"])}))
    elif args.command == "run":
        if args.backend == "http" and (not args.runtime_manifest or args.workers < 1):
            parser.error("HTTP inference requires --runtime-manifest and positive --workers")
        run(args)
    else:
        def read(path):
            records = [json.loads(line) for line in path.read_text().splitlines()]
            return records[0]["_meta"], records[1:]
        base_meta, baseline = read(args.baseline)
        cand_meta, candidate = read(args.candidate)
        for key in ("manifest_sha256", "prompt", "temperature", "max_tokens"):
            if base_meta[key] != cand_meta[key]:
                raise ValueError(f"Comparison conditions differ: {key}")
        if {r["id"] for r in baseline} != {r["id"] for r in candidate}:
            raise ValueError("Comparison page sets differ")
        if any(len({r["id"] for r in rows}) != len(rows) for rows in (baseline, candidate)):
            raise ValueError("Repeated page identities in comparison")
        if {r["id"]: r["split"] for r in baseline} != {r["id"]: r["split"] for r in candidate}:
            raise ValueError("Comparison page splits differ")
        if base_meta.get("backend", "mlx") != cand_meta.get("backend", "mlx"):
            raise ValueError("Comparison inference backends differ")
        base_summary, cand_summary = summarize(baseline), summarize(candidate)
        split = "test" if "test" in base_summary else "all"
        base_score, cand_score = base_summary[split], cand_summary[split]
        result = {"baseline": base_meta, "candidate": cand_meta,
                  "baseline_file_sha256": sha256(args.baseline),
                  "candidate_file_sha256": sha256(args.candidate),
                  "pages": sorted(r["id"] for r in baseline),
                  "evaluation_split": split,
                  "baseline_scores": base_score, "candidate_scores": cand_score,
                  "baseline_by_split": base_summary, "candidate_by_split": cand_summary,
                  "candidate_cer_change": cand_score["cer"] - base_score["cer"],
                  "scope": ("Held-out benchmark pages; results do not establish corpus-wide accuracy."
                            if split == "test" else
                            "Calibration preflight only; insufficient for corpus-wide accuracy claims."),
                  "generated_by": "scripts/benchmark_page_ocr.py compare"}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"baseline_cer": base_score["cer"], "candidate_cer": cand_score["cer"]}))


if __name__ == "__main__":
    main()
