"""Verify the public corpus files and lexical totals against their release manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def validate(root=ROOT):
    from frequency_projection import lexical_text
    data = Path(root) / "data"
    manifest = json.loads((data / "public_export.json").read_bytes())
    for name in ("work_index.json", "source_registry.json", "corpus_editions.json"):
        if not (data / name).is_file():
            raise ValueError("Missing public identity or source metadata: " + name)
    index = json.loads((data / "work_index.json").read_bytes())
    if not set(manifest["works"]) <= set(index["works"]):
        raise ValueError("Public work index omits a corpus work")
    actual = {p.name for p in (data / "corpus").glob("*.jsonl")}
    if actual != set(manifest["files"]):
        raise ValueError("Corpus file set differs from the public manifest")
    totals = {"works": 0, "passages": 0, "tokens": 0}
    for name, expected in sorted(manifest["files"].items()):
        if Path(name).name != name or not name.endswith(".jsonl"):
            raise ValueError("Invalid corpus filename")
        raw = (data / "corpus" / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Corpus file hash differs: " + name)
        rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
        passages = len(rows)
        tokens = sum(len(re.findall(r"[Ͱ-Ͽἀ-῿̀-ͯ]+", lexical_text(row))) for row in rows)
        if {"passages": passages, "tokens": tokens, "sha256": expected} != manifest["works"][Path(name).stem]:
            raise ValueError("Corpus work totals differ: " + name)
        totals["works"] += 1
        totals["passages"] += passages
        totals["tokens"] += tokens
    digest = hashlib.sha256("".join(sorted(f"{Path(name).stem}\t{value}\n" for name, value in manifest["files"].items())).encode()).hexdigest()
    if digest != manifest["corpus_sha256"] or totals != manifest["totals"]:
        raise ValueError("Corpus release totals or content hash differ")
    return totals


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
