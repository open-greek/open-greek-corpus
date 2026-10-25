#!/usr/bin/env python3
"""Repair the reviewed Hesychius and Kaibel work assignments without editing text.

Run with --apply to write the repair, --check to replay its archived inputs,
or --undo to restore every file changed by the repair. Source snapshots and
per-row assignment changes are retained under data/corpus_changes/.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/corpus_changes/ocr-work-assignments-54-55"
HESYCHIUS = (
    "hesychius-lexicography.lexicon-o",
    "hesychius-lexicography.lexicon-p-w",
)
KAIBEL = {
    "rhinthon.fragmenta": "kaibel-cgf-1899.volume-witness-r",
    "sopater-comedy.fragmenta": "kaibel-cgf-1899.volume-witness-s",
}
KAIBEL_RUNS = {
    "rhinthon_kaibel_cgf_1899_": KAIBEL["rhinthon.fragmenta"],
    "sopater_kaibel_cgf_": KAIBEL["sopater-comedy.fragmenta"],
}
SOURCE_HASHES = {
    HESYCHIUS[0]: "244c0c51a5465b6c97d56a9cf811841ca84c4091a9aa1fbcbd496ab220a59d84",
    HESYCHIUS[1]: "ce48aad66add115da0def0380475ced2a86c6f677bd0b46b157af581b3daa65e",
    "rhinthon.fragmenta": "7cbda89b45ad6a1994d8a6ae7ed3e9caf3142bb19fdd1f18cb28d7b2e64b3f81",
    "sopater-comedy.fragmenta": "303c13317c12f139af6a000cdfb1505aaee7fbb6fe3742272e9d802bf2755fe0",
}
PARATEXT = "data/paratext/hesychius-schmidt-ethnica.jsonl"
ALIASES = "data/passage_aliases.json"
VOLUME_AUTHOR = "kaibel-cgf-1899"
VOLUME_NAME = "Comicorum Graecorum Fragmenta I.1 (Kaibel 1899)"
EVIDENCE = {
    "hesychius": {
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/54",
        "source_url": "https://archive.org/details/hesychiialexand00schmgoog",
        "pdf_sha256": "aaa3e3e2c8d83e8f2f7e1c1a1ecc84236855be83db80afeaa1685290c23678aa",
        "checked_pdf_pages": [625, 626, 627, 728, 864, 865, 866, 874],
        "evidence": "Manual scan inspection: scan 626 has omicron entries in columns 1167-1168; scan 627 has pi entries in columns 1171-1172. Columns 1169-1170 are absent from this scan. Scan 864 ends omega at columns 1591-1592. Scan 865 begins the separately headed Glossae ethnicae index, which continues through scan 874. Route by this physical sequence, including continuation lines, rather than an OCR initial. No text is corrected.",
    },
    "kaibel": {
        "issue": "https://github.com/open-greek/open-greek-corpus/issues/55",
        "source_url": "https://archive.org/details/comicorvmgraeco00kaibgoog",
        "pdf_sha256": "59f1e3751f1eb18c25789ccbec3a2e491a2be171198ef87d3480f9789a2a31e5",
        "checked_pdf_pages": [8, 10, 65],
        "evidence": "Manual scan inspection: the volume is Kaibel's Comicorum Graecorum Fragmenta I.1 (1899); printed page 42, scan 65, contains Tzetzes' Iambi technici, including verse 86. Both supposed author files contain this page and sections headed Epicharmus and Sophron. They are overlapping OCR witnesses of the anthology, not the collected fragments of either named author. Preserve both witnesses under a collective volume identity; do not infer author boundaries from drifting OCR page keys.",
    },
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def dump(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def jsonl(rows) -> bytes:
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()


def hesychius_section(page: int) -> str:
    if 20 <= page <= 626:
        return HESYCHIUS[0]
    if 627 <= page <= 864:
        return HESYCHIUS[1]
    if 865 <= page <= 874:
        return "paratext"
    raise ValueError(f"Unreviewed Hesychius scan page: {page}")


def assign(row):
    """Return (repository path, reassigned row, evidence key). Text is invariant."""
    old = row["urn"]
    result = dict(row)
    if old in HESYCHIUS:
        match = re.fullmatch(r"hesychius_masked_(\d+)\.(\d+)", row["locus"])
        if not match:
            raise ValueError(f"Unreviewed Hesychius locus: {row['locus']}")
        target = hesychius_section(int(match[1]))
        if target == "paratext":
            result.update(lang="grc", **{"class": "edition_index"},
                          why_not_served="Schmidt's Glossae ethnicae index, outside the alphabetical lexicon")
            return PARATEXT, result, "hesychius"
        result["urn"] = target
        result["cts"] = "urn:cts:greekLit:tlg4085.tlg" + ("002" if target == HESYCHIUS[0] else "003")
        return f"data/corpus/{target}.jsonl", result, "hesychius"
    if old in KAIBEL:
        result["urn"] = KAIBEL[old]
        result.pop("cts", None)
        return f"data/corpus/{result['urn']}.jsonl", result, "kaibel"
    raise ValueError(f"Unreviewed work: {old}")


def row_order(row):
    return tuple(int(part) if part.isdigit() else part
                 for part in re.split(r"(\d+)", row["locus"]))


def route(source_bytes):
    outputs, changes, aliases = defaultdict(list), [], {}
    seen = set()
    for slug, raw in source_bytes.items():
        for line in raw.decode().splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row["urn"] != slug:
                raise ValueError(f"Wrong input work: {slug}, {row['urn']}")
            path, corrected, evidence = assign(row)
            identity = (path, corrected["locus"])
            if identity in seen:
                raise ValueError(f"Repeated destination: {identity}")
            seen.add(identity)
            assert row["text"] == corrected["text"]
            outputs[path].append(corrected)
            if corrected != row or path.startswith("data/paratext/"):
                target = {"path": path, "locus": row["locus"]}
                if path.startswith("data/corpus/"):
                    target["slug"] = corrected["urn"]
                aliases.setdefault(slug, {})[row["locus"]] = target
                changes.append({"source_work": slug, "locus": row["locus"],
                    "original_assignment": {k: row[k] for k in ("urn", "cts") if k in row},
                    "corrected_assignment": {k: corrected[k] for k in ("urn", "cts") if k in corrected},
                    "destination": target, "text_sha256": sha(row["text"].encode()),
                    "text_changed": False, "evidence": evidence})
    return {path: jsonl(rows if path.startswith("data/corpus/kaibel-") else sorted(rows, key=row_order))
            for path, rows in outputs.items()}, changes, aliases


def route_secondary(snapshots):
    outputs, changes = {}, []
    for old, new in KAIBEL.items():
        raw = snapshots.get(f"data/corpus_secondary/{old}.jsonl")
        if raw is None:
            continue
        rows = []
        target = f"data/corpus_secondary/{new}.jsonl"
        for line in raw.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            _, corrected, evidence = assign(row)
            rows.append(corrected)
            changes.append({"source_work": old, "source_storage": "secondary",
                "locus": row["locus"], "original_assignment": {k: row[k] for k in ("urn", "cts") if k in row},
                "corrected_assignment": {k: corrected[k] for k in ("urn", "cts") if k in corrected},
                "destination": {"path": target, "locus": row["locus"], "slug": new},
                "text_sha256": sha(row["text"].encode()), "text_changed": False, "evidence": evidence})
        outputs[target] = jsonl(rows)
    return outputs, changes


def repair_metadata(root):
    # Use the supported rename tool so opaque expression ids follow the volumes.
    import rename_work
    original = json.loads((root / "data/source_registry.json").read_text())
    for old, new in KAIBEL.items():
        rename_work.rename(old, new, write=True, rebuild=False)
    registry = json.loads((root / "data/source_registry.json").read_text())
    attributions = json.loads((root / "data/pseudo_author_attributions.json").read_text())
    crosswalk = json.loads((root / "data/tlg_crosswalk.json").read_text())
    attributions["authors"][VOLUME_AUTHOR] = {"name": VOLUME_NAME, "aliases": {},
        "note": "Collective edition label; the two OCR witnesses overlap and have not been collated."}
    registry["authors"][VOLUME_AUTHOR] = {"name": VOLUME_NAME, "aliases": {}}
    for old, new in KAIBEL.items():
        witness = new.rsplit("-", 1)[-1].upper()
        title = f"{VOLUME_NAME}, OCR witness {witness}"
        attributions["works"][new] = {"author": VOLUME_AUTHOR, "title": title,
            "evidence": EVIDENCE["kaibel"], "volume_witness": {"volume": "kaibel-cgf-i-1-1899",
                "witness": witness, "collation_status": "overlapping-uncollated-witness"}}
        work = registry["works"][new]
        work.update(author=VOLUME_AUTHOR, title=title,
                    aliases={"cts": f"urn:cts:cogGreek:{new}"}, tags=[], best_source="open_corpus")
        work["editions"] = {key: value for key, value in work["editions"].items()
                            if value.get("provider") == "ocr"}
        # Restore the real author's inventory row without the misassigned OCR.
        canonical = original["works"][old]
        canonical["editions"] = {k: v for k, v in canonical["editions"].items()
                                  if v.get("provider") != "ocr"}
        if canonical.get("default_edition") not in canonical["editions"]:
            canonical["default_edition"] = None
        registry["works"][old] = canonical
        crosswalk[new] = {"cts": f"urn:cts:cogGreek:{new}", "tlg": "",
                          "author_slug": VOLUME_AUTHOR, "title": title}
        crosswalk.pop(old, None)
    for path, value in [("data/source_registry.json", registry),
                        ("data/pseudo_author_attributions.json", attributions),
                        ("data/tlg_crosswalk.json", crosswalk)]:
        raw = json.dumps(value, ensure_ascii=False, indent=0).encode() if path.endswith("tlg_crosswalk.json") else dump(value)
        (root / path).write_bytes(raw)
    rename_work._write_crosswalk_tsv(crosswalk)
    ocr = json.loads((root / "data/ocr_works.json").read_text())
    for record in ocr:
        if record.get("urn") in KAIBEL:
            record["urn"] = KAIBEL[record["urn"]]
            record["author"] = VOLUME_NAME
            record["title"] = attributions["works"][record["urn"]]["title"]
    (root / "data/ocr_works.json").write_bytes(dump(ocr))
    sources_path = root / "data/inventory/ocr_edition_sources.json"
    sources = json.loads(sources_path.read_text())
    for edition, witness in [("qwen36-rhinthon_kaibel_cgf_1899", "R"), ("qwen36-sopater_kaibel_cgf", "S")]:
        sources[edition] = {"label": f"{VOLUME_NAME}, OCR witness {witness}",
                            "url": EVIDENCE["kaibel"]["source_url"], "model": "Qwen3.6-27B"}
    sources_path.write_bytes(dump(sources))


def run(root, mode):
    audit_dir = root / AUDIT
    audit_path = audit_dir / "changes.json"
    if audit_path.exists():
        audit = json.loads(audit_path.read_text())
        snapshots = json.loads(gzip.decompress((audit_dir / "before.json.gz").read_bytes()))
        if mode == "undo":
            for path, expected in audit["outputs"].items():
                current = sha((root / path).read_bytes()) if (root / path).is_file() else None
                if current != expected:
                    raise ValueError(f"Output changed since repair; refusing to overwrite: {path}")
            for path, text in snapshots.items():
                target = root / path
                if text is None:
                    target.unlink(missing_ok=True)
                else:
                    target.write_text(text)
            print("Restored the exact inputs; derived reports must be rebuilt.")
            return
        source = {slug: snapshots[f"data/corpus/{slug}.jsonl"].encode() for slug in SOURCE_HASHES}
        for slug, raw in source.items():
            if sha(raw) != SOURCE_HASHES[slug]:
                raise ValueError(f"Archived source differs from its pin: {slug}")
        if audit["evidence"] != EVIDENCE:
            raise ValueError("Assignment evidence changed; review the affected source again")
        outputs, changes, aliases = route(source)
        secondary_outputs, secondary_changes = route_secondary(snapshots)
        outputs.update(secondary_outputs)
        changes.extend(secondary_changes)
        for path, raw in outputs.items():
            from reviewed_duplicate_state import historical_bytes
            previous = historical_bytes(root, path)
            actual = previous if previous is not None else (root / path).read_bytes()
            if actual != raw:
                raise ValueError(f"Repaired corpus differs from replay: {path}")
        current_aliases = json.loads((root / ALIASES).read_text())["aliases"]
        if changes != audit["changes"] or any(current_aliases.get(slug) != targets
                                               for slug, targets in aliases.items()):
            raise ValueError("Assignment audit or passage aliases differ from replay")
        print(f"Verified {len(changes)} reversible assignments; all text is unchanged.")
        return
    if mode in {"check", "undo"}:
        raise ValueError("The assignment repair has not been applied")
    source = {slug: (root / f"data/corpus/{slug}.jsonl").read_bytes() for slug in SOURCE_HASHES}
    for slug, raw in source.items():
        if sha(raw) != SOURCE_HASHES[slug]:
            raise ValueError(f"Source changed; review assignments again: {slug}")
    outputs, changes, aliases = route(source)
    secondary_paths = {f"data/corpus_secondary/{slug}.jsonl" for slug in [*KAIBEL, *KAIBEL.values()]}
    secondary_snapshots = {path: (root / path).read_text() if (root / path).exists() else None
                           for path in secondary_paths}
    secondary_outputs, secondary_changes = route_secondary(secondary_snapshots)
    outputs.update(secondary_outputs)
    changes.extend(secondary_changes)
    print(json.dumps(dict(Counter(change["evidence"] for change in changes))))
    if mode != "apply":
        return
    source_paths = {f"data/corpus/{slug}.jsonl" for slug in SOURCE_HASHES}
    source_paths |= {f"data/corpus_secondary/{slug}.jsonl" for slug in KAIBEL}
    for path in set(outputs) | {ALIASES}:
        if path not in source_paths and (root / path).exists():
            raise ValueError(f"Repair destination already exists: {path}")
    metadata = ["work_id_aliases", "tlg_crosswalk", "source_registry", "ocr_works",
                "pseudo_author_attributions", "work_ids", "author_ids", "corpus_editions", "work_index"]
    paths = {f"data/{name}.json" for name in metadata} | set(outputs) | {ALIASES, "data/tlg_crosswalk.tsv"}
    paths |= {f"data/corpus/{slug}.jsonl" for slug in SOURCE_HASHES}
    paths |= secondary_paths
    paths.add("data/inventory/ocr_edition_sources.json")
    snapshots = {path: (root / path).read_text() if (root / path).exists() else None for path in sorted(paths)}
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "before.json.gz").write_bytes(gzip.compress(dump(snapshots), mtime=0))
    # Rename before writing reassigned rows, so the rename tool sees its sources.
    repair_metadata(root)
    for path, raw in outputs.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(raw)
    (root / ALIASES).write_bytes(dump({"schema_version": 1,
        "generated_by": "scripts/repair_ocr_work_assignments.py", "aliases": aliases}))
    import build_id_registry
    import reconcile_corpus_editions
    import build_work_index
    build_id_registry.build(write=True)
    reconcile_corpus_editions.main()
    build_work_index.build(write=True)
    audit = {"schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
        "generator": "scripts/repair_ocr_work_assignments.py", "sources": SOURCE_HASHES,
        "evidence": EVIDENCE, "changes": changes,
        "reversal": "python3 scripts/repair_ocr_work_assignments.py --undo; rebuild derived reports",
        "outputs": {path: sha((root / path).read_bytes()) if (root / path).exists() else None
                    for path in sorted(paths)}}
    audit_path.write_bytes(dump(audit))
    print(f"Wrote {len(changes)} assignment changes and exact reversible source snapshots.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    for mode in ("apply", "check", "undo"):
        modes.add_argument(f"--{mode}", action="store_true")
    args = parser.parse_args()
    run(ROOT, next((mode for mode in ("apply", "check", "undo") if getattr(args, mode)), "dry-run"))


if __name__ == "__main__":
    main()
