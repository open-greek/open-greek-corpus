#!/usr/bin/env python3
"""Move Bekker's checked Photius index to paratext without changing its text.

Historical loci remain resolvable through explicit passage aliases. The exact
pre-repair file is archived, and --undo restores its bytes after any later
coverage additions have been unapplied.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SLUG = "photius.bibliotheca"
CORPUS = Path(f"data/corpus/{SLUG}.jsonl")
PARATEXT = Path("data/paratext/photius-bekker-index.jsonl")
ALIASES = Path("data/passage_aliases.json")
ARCHIVE = Path("data/corpus_changes/photius-bekker-index")
SOURCE_SHA256 = "95f5814a95ac9c0b26010c624dc605248f1937868d9fe1e15178ab6cd9f0ee68"
PAGE = re.compile(r"^helladius_chrestomathia_photius_bekker_v2_(\d{4})[.](\d+)$")


def is_index_locus(locus):
    """Shared delivery guard for the checked original second-volume OCR run."""
    match = PAGE.fullmatch(locus)
    return bool(match and int(match[1]) >= 281)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def jsonl(rows):
    return ("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n").encode()


def generate(raw):
    if sha(raw) != SOURCE_SHA256:
        raise ValueError("Photius input differs from the checked source snapshot")
    rows = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
    body, index, aliases, changes = [], [], {}, []
    for row in rows:
        match = PAGE.fullmatch(row["locus"])
        if not match or row["urn"] != SLUG:
            raise ValueError("Unreviewed Photius source identity")
        page = int(match[1])
        if not is_index_locus(row["locus"]):
            body.append(row)
            continue
        if not 281 <= page <= 318:
            raise ValueError("Unreviewed index boundary")
        moved = {**row, "slug": SLUG, "language": "grc", "class": "edition_index",
                 "why_not_served": "Bekker's edition index, beginning at combined scan 558 after codex 280 ends on scan 557; retained as paratext.",
                 "combined_scan_page": page + 277}
        index.append(moved)
        target = {"path": PARATEXT.as_posix(), "locus": row["locus"]}
        aliases[row["locus"]] = target
        changes.append({"original_path": CORPUS.as_posix(), "original_locus": row["locus"],
                        "destination": target, "original_text": row["text"],
                        "corrected_text": row["text"], "text_changed": False,
                        "evidence": "Manual inspection of the pinned combined Bekker scan: scan 557 ends codex 280, scan 558 is headed INDEX. Existing OCR page 0281 matches that index boundary.",
                        "date": "2026-10-18"})
    if len(body) != 3846 or len(index) != 501:
        raise ValueError("Checked Photius boundary counts changed")
    body_bytes, index_bytes = jsonl(body), jsonl(index)
    audit = {"schema_version": 1, "operation": "move-edition-index-to-paratext",
             "work": SLUG, "date": "2026-10-18", "source_sha256": SOURCE_SHA256,
             "body_sha256": sha(body_bytes), "paratext_sha256": sha(index_bytes),
             "source_scan": "https://archive.org/details/bibliothecaexrec00photuoft",
             "source_scan_sha256": "d7f4e5e1d2b9772a2cb5237c11ca53c91419e5a47ce92496cc8bd57f2340c4c6",
             "source_pages_checked": [557, 558], "body_rows": len(body), "index_rows": len(index),
             "changes": changes,
             "reversal": "Unapply later additions first, then run scripts/repair_photius_index.py --undo. The original file is retained byte-for-byte in before.jsonl.gz.",
             "generated_by": "scripts/repair_photius_index.py"}
    return body_bytes, index_bytes, aliases, audit


def input_bytes(root):
    archive = root / ARCHIVE / "before.jsonl.gz"
    return gzip.decompress(archive.read_bytes()) if archive.exists() else (root / CORPUS).read_bytes()


def apply(root=ROOT):
    raw = input_bytes(root)
    body, index, aliases, audit = generate(raw)
    current = (root / CORPUS).read_bytes()
    if current not in (raw, body):
        raise ValueError("Unapply later coverage changes before applying the index split")
    p = root / PARATEXT
    if p.exists() and p.read_bytes() != index:
        raise ValueError("Index paratext was independently modified")
    catalog = json.loads((root / ALIASES).read_text())
    own = catalog.setdefault("aliases", {}).setdefault(SLUG, {})
    for locus, target in aliases.items():
        if locus in own and own[locus] != target:
            raise ValueError("Historical passage alias already points elsewhere")
        own[locus] = target
    archive = root / ARCHIVE
    archive.mkdir(parents=True, exist_ok=True)
    (archive / "before.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
    (archive / "changes.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(index)
    (root / CORPUS).write_bytes(body)
    (root / ALIASES).write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    return audit


def check(root=ROOT):
    body, index, aliases, audit = generate(input_bytes(root))
    from repair_photius_apparatus import restore_legacy_bytes
    current = restore_legacy_bytes((root / CORPUS).read_bytes(), root)
    current_rows = {r["locus"]: r for r in map(json.loads, current.decode().splitlines())}
    for row in map(json.loads, body.decode().splitlines()):
        if current_rows.get(row["locus"]) != row:
            raise ValueError("A retained historical body passage changed")
    if set(aliases).intersection(current_rows):
        raise ValueError("Index passages are still present in primary text")
    if (root / PARATEXT).read_bytes() != index:
        raise ValueError("Index paratext differs from preserved text")
    current_aliases = json.loads((root / ALIASES).read_text())["aliases"][SLUG]
    if any(current_aliases.get(k) != v for k, v in aliases.items()):
        raise ValueError("A historical index destination is missing")
    return audit


def undo(root=ROOT):
    raw = input_bytes(root)
    body, index, aliases, audit = generate(raw)
    if (root / CORPUS).read_bytes() != body or (root / PARATEXT).read_bytes() != index:
        raise ValueError("Unapply later coverage additions or independent edits before undo")
    catalog = json.loads((root / ALIASES).read_text())
    current = catalog["aliases"][SLUG]
    if any(current.get(k) != v for k, v in aliases.items()):
        raise ValueError("Historical destinations changed after the split")
    for key in aliases:
        del current[key]
    if not current:
        del catalog["aliases"][SLUG]
    (root / CORPUS).write_bytes(raw)
    (root / PARATEXT).unlink()
    (root / ALIASES).write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--undo", action="store_true")
    args = parser.parse_args()
    result = apply() if args.apply else check() if args.check else undo() if args.undo else generate(input_bytes(ROOT))[3]
    print(json.dumps({key: result[key] for key in ("work", "body_rows", "index_rows", "body_sha256", "paratext_sha256")}))
