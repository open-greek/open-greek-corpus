#!/usr/bin/env python3
"""Reassign the scan-checked De mensibus OCR without changing any reading.

Use --apply, --check, or --undo. The audit retains the exact original corpus
and metadata, so undo restores bytes rather than trying to reverse a rename.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "joannes-laurentius-lydus.de-magistratibus-populi-romani"
NEW = "joannes-laurentius-lydus.de-mensibus"
CTS = "urn:cts:greekLit:tlg2580.tlg002"
EDITION = "qwen36-lydus_mensibus_wuensch"
RUN_PREFIX = "lydus_mensibus_wuensch_"
SOURCE_SHA256 = "35b8b9016d849a3321dbefe50e3c2fbfba9735a13020d97d539a6e625598dc7c"
AUDIT = "data/corpus_changes/lydus-identity-53"
ALIASES = "data/passage_aliases.json"
EVIDENCE = {
    "issue": "https://github.com/open-greek/open-greek-corpus/issues/53",
    "source_url": "https://archive.org/details/ioannislaurenti02wuengoog",
    "pdf_sha256": "2f105e6ff81c6b04f1151d40325eaae65442c6fc6d4aff01fd6a2ede3fc4bb64",
    "checked_pdf_pages": [4, 38, 79],
    "evidence": "Manual inspection of the 306-page scan: scan 4 names Ioannis Laurentii Lydi Liber de mensibus, edited by Ricardus Wuensch, Leipzig 1898. Scans 38 and 79 belong to its preface, including quotations about the months. All served rows belong to the lydus_mensibus_wuensch OCR run. This is an edition-identity repair; it does not certify body/paratext separation or equate OCR page stems with printed pages. De magistratibus has a separate work anchor and receives none of these rows.",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def route(raw):
    rows, changes, aliases = [], [], {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if (row["urn"] != OLD or row["edition"] != EDITION
                or not row["locus"].startswith(RUN_PREFIX)):
            raise ValueError("Unreviewed Lydus source row")
        if row["locus"] in aliases:
            raise ValueError("Repeated Lydus locus")
        result = dict(row, urn=NEW)
        if "cts" in result:
            result["cts"] = CTS
        target = {"slug": NEW, "path": f"data/corpus/{NEW}.jsonl", "locus": row["locus"]}
        aliases[row["locus"]] = target
        changes.append({"source_work": OLD, "locus": row["locus"],
                        "original_assignment": {k: row[k] for k in ("urn", "cts") if k in row},
                        "corrected_assignment": {k: result[k] for k in ("urn", "cts") if k in result},
                        "destination": target, "text_sha256": sha(row["text"].encode()),
                        "text_changed": False, "evidence": "lydus-mensibus-1898"})
        rows.append(result)
    if not rows:
        raise ValueError("Empty Lydus source")
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode(), changes, aliases


def repair_metadata(root):
    import rename_work
    registry = json.loads((root / "data/source_registry.json").read_text())
    old_work, new_work = registry["works"][OLD], registry["works"][NEW]
    # Preserve both canonical inventory entries. A generic rename would replace
    # the existing De mensibus entry with the old De magistratibus metadata.
    ocr_editions = {NEW + key[len(OLD):]: value for key, value in old_work["editions"].items()
                    if value.get("provider") == "ocr"}
    if set(ocr_editions) != {NEW + "." + EDITION}:
        raise ValueError("Unreviewed Lydus editions")
    rename_work.rename(OLD, NEW, write=True, rebuild=False)
    old_work["editions"] = {key: value for key, value in old_work["editions"].items()
                            if value.get("provider") != "ocr"}
    old_work["default_edition"] = None
    new_work["editions"].update(ocr_editions)
    new_work.update(default_edition=NEW + "." + EDITION, best_source="open_corpus")
    registry["works"][OLD], registry["works"][NEW] = old_work, new_work
    (root / "data/source_registry.json").write_bytes(dump(registry))
    crosswalk = json.loads((root / "data/tlg_crosswalk.json").read_text())
    crosswalk.pop(OLD, None)
    crosswalk[NEW] = {"cts": CTS, "tlg": "tlg2580.tlg002",
                      "author_slug": new_work["author"], "title": new_work["title"]}
    (root / "data/tlg_crosswalk.json").write_text(json.dumps(crosswalk, ensure_ascii=False, indent=0))
    rename_work._write_crosswalk_tsv(crosswalk)
    works = json.loads((root / "data/ocr_works.json").read_text())
    for work in works:
        if work.get("urn") == OLD:
            work.update(urn=NEW, author="Joannes Laurentius Lydus", title="De Mensibus")
    (root / "data/ocr_works.json").write_bytes(dump(works))
    path = root / "data/inventory/ocr_edition_sources.json"
    sources = json.loads(path.read_text())
    sources[EDITION] = {"label": "Lydus, De mensibus (Wünsch 1898)",
                        "url": EVIDENCE["source_url"], "model": "Qwen3.6-27B"}
    path.write_bytes(dump(sources))


def run(root, mode):
    audit_dir = root / AUDIT
    audit_path = audit_dir / "changes.json"
    old_path, new_path = (f"data/corpus/{slug}.jsonl" for slug in (OLD, NEW))
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        snapshots = json.loads(gzip.decompress((audit_dir / "before.json.gz").read_bytes()))
        if mode == "undo":
            for path, expected in audit["outputs"].items():
                current = sha((root / path).read_bytes()) if (root / path).exists() else None
                if current != expected:
                    raise ValueError(f"Output changed since repair; refusing to overwrite: {path}")
            for path, text in snapshots.items():
                target = root / path
                if text is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_text(text)
            print("Restored exact Lydus inputs; rebuild derived reports.")
            return
        raw = snapshots[old_path].encode()
        if sha(raw) != SOURCE_SHA256 or audit["evidence"] != EVIDENCE:
            raise ValueError("Lydus source pin or evidence changed")
        output, changes, aliases = route(raw)
        if (root / new_path).read_bytes() != output or (root / old_path).exists():
            raise ValueError("Lydus corpus differs from replay")
        actual = json.loads((root / ALIASES).read_text())["aliases"].get(OLD)
        if changes != audit["changes"] or actual != aliases:
            raise ValueError("Lydus assignment audit or passage aliases differ from replay")
        print(f"Verified {len(changes)} reversible Lydus assignments; all text is unchanged.")
        return
    if mode in {"check", "undo"}:
        raise ValueError("The Lydus repair has not been applied")
    raw = (root / old_path).read_bytes()
    if sha(raw) != SOURCE_SHA256:
        raise ValueError("Lydus source changed; review it again")
    output, changes, aliases = route(raw)
    print(f"Reassign {len(changes)} passages from De magistratibus to De mensibus.")
    if mode != "apply":
        return
    if (root / new_path).exists():
        raise ValueError("De mensibus is already served; a rename would discard a reading")
    metadata = ["work_id_aliases", "tlg_crosswalk", "source_registry", "ocr_works",
                "work_ids", "author_ids", "corpus_editions", "work_index", "needs_ocr_cleanup"]
    paths = {f"data/{name}.json" for name in metadata}
    paths |= {old_path, new_path, ALIASES, "data/tlg_crosswalk.tsv", "data/inventory/ocr_edition_sources.json"}
    snapshots = {path: (root / path).read_text() if (root / path).exists() else None for path in sorted(paths)}
    alias_data = json.loads(snapshots[ALIASES])
    if OLD in alias_data["aliases"]:
        raise ValueError("Historical Lydus passage aliases already exist")
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "before.json.gz").write_bytes(gzip.compress(dump(snapshots), mtime=0))
    repair_metadata(root)
    (root / new_path).write_bytes(output)
    alias_data["aliases"][OLD] = aliases
    (root / ALIASES).write_bytes(dump(alias_data))
    import build_id_registry
    import reconcile_corpus_editions
    import build_work_index
    build_id_registry.build(write=True)
    reconcile_corpus_editions.main()
    build_work_index.build(write=True)
    audit_path.write_bytes(dump({"schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/repair_lydus_identity.py", "sources": {OLD: SOURCE_SHA256},
        "evidence": EVIDENCE, "changes": changes,
        "reversal": "python3 scripts/repair_lydus_identity.py --undo; rebuild derived reports",
        "outputs": {path: sha((root / path).read_bytes()) if (root / path).exists() else None for path in sorted(paths)}}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    for mode in ("apply", "check", "undo"):
        modes.add_argument("--" + mode, action="store_true")
    args = parser.parse_args()
    run(ROOT, next((mode for mode in ("apply", "check", "undo") if getattr(args, mode)), "dry-run"))
