#!/usr/bin/env python3
"""Record an auditable, reversible trail for a masked re-OCR "keep-better" swap.

The dense-class re-OCR fleet stages replacement text for a served work next to a
per-work validation report. A separate ingest step copies the staged jsonl over
the served jsonl, archiving the prior served text first. This tool reads that
staging tree plus the now-installed corpus files and emits one structured record
per swapped work into ``data/corpus_changes/``, so every text replacement carries:

  * the original served text (edition, row/char counts, sha256) - archived and
    still recoverable from git history at the parent commit;
  * the corrected (masked re-OCR) text (edition, row/char counts, sha256);
  * the keep-better evidence (Greek-volume ratio + signals from the validation
    report) and a pointer to the work's data/ocr_provenance record;
  * a date and an explicit reversal path.

Paths to the staging tree and corpus root are passed on the command line, so the
committed script hard-codes no local paths and names no external repository.

Usage:
  record_reocr_ingest_audit.py --staging <bucket_staging_dir> --cog <repo_root>
                               [--check]   # verify only, write nothing
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

DATE = "2026-07-12"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(p: Path) -> int:
    n = 0
    with p.open("rb") as fh:
        for _ in fh:
            n += 1
    return n


def git_head_blob_sha256(cog: Path, rel: str) -> str | None:
    """sha256 of the file's content at HEAD (the pre-ingest served text)."""
    try:
        blob = subprocess.run(
            ["git", "-C", str(cog), "show", f"HEAD:{rel}"],
            check=True, capture_output=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None
    return hashlib.sha256(blob).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True, type=Path,
                    help="bucket staging dir holding _staging_manifest.json + per-work dirs")
    ap.add_argument("--cog", required=True, type=Path, help="corpus repo root")
    ap.add_argument("--check", action="store_true",
                    help="verify hashes only; do not write audit records")
    args = ap.parse_args()

    manifest = json.loads((args.staging / "_staging_manifest.json").read_text())
    out_dir = args.cog / "data" / "corpus_changes"
    out_dir.mkdir(parents=True, exist_ok=True)

    installed = [
        w for w in manifest["staged"]
        if w.get("keep_better") is True and w.get("flag") is None
    ]

    written, errors = [], []
    for w in installed:
        urn = w["staged_urn"]
        slug = w["slug"]
        wdir = args.staging / slug
        replaced = wdir / f"REPLACED.{urn}.jsonl"
        installed_jsonl = args.cog / "data" / "corpus" / f"{urn}.jsonl"
        staged_jsonl = wdir / f"{urn}.jsonl"
        rel = f"data/corpus/{urn}.jsonl"

        if not replaced.exists():
            errors.append(f"{urn}: REPLACED archive missing ({replaced.name}) - not a swap?")
            continue
        if not installed_jsonl.exists():
            errors.append(f"{urn}: installed corpus file missing")
            continue

        old_sha = sha256_file(replaced)
        old_rows = line_count(replaced)
        new_sha = sha256_file(installed_jsonl)
        new_rows = line_count(installed_jsonl)

        # Integrity: the archived "original" must equal what git HEAD still holds
        # (the pre-ingest served text), and the installed file must equal the
        # staged source that was copied in.
        head_sha = git_head_blob_sha256(args.cog, rel)
        if head_sha is not None and head_sha != old_sha:
            errors.append(
                f"{urn}: archived original sha256 != git HEAD blob "
                f"({old_sha[:12]} vs {head_sha[:12]})")
            continue
        if staged_jsonl.exists():
            staged_sha = sha256_file(staged_jsonl)
            if staged_sha != new_sha:
                errors.append(
                    f"{urn}: installed file sha256 != staged source "
                    f"({new_sha[:12]} vs {staged_sha[:12]})")
                continue

        # Pull edition + evidence from the work's validation + provenance.
        val = json.loads((wdir / "VALIDATION.json").read_text())
        prov_rel = f"data/ocr_provenance/{w['prov_records'][0]}"
        prov = json.loads((args.cog / prov_rel).read_text())
        cts = prov.get("cts", "")
        new_edition = prov.get("edition", "masked re-OCR")

        ratio = w["greek_ratio"]
        signals = (
            f"greek_ratio={ratio} (masked/served); "
            f"masked_greek_chars={val.get('masked_greek_chars')} vs "
            f"served_greek_chars={val.get('served_greek_chars')}; "
            f"unique_greek_words {val.get('masked_unique_greek_words')} vs "
            f"{val.get('served_unique_greek_words')}"
        )
        if w.get("headword_gain") is not None:
            signals += f"; headword_gain=+{w['headword_gain']}"

        record = {
            "_meta": {
                "change": "replace served text (masked re-OCR keep-better swap)",
                "work": urn,
                "cts": cts,
                "run_slug": slug,
                "applied_by": "scripts/record_reocr_ingest_audit.py",
                "date": DATE,
                "tier": w["tier"],
                "reversible": (
                    "git revert the swap commit, or restore the file from the "
                    f"parent commit ('git checkout <parent> -- {rel}') and confirm "
                    "its sha256 equals old.sha256 below. The pre-ingest served "
                    f"text is also archived offline as REPLACED.{urn}.jsonl in the "
                    "OCR staging area."
                ),
            },
            "old": {
                "edition": "served corpus text (pre re-OCR)",
                "rows": old_rows,
                "greek_chars": val.get("served_greek_chars"),
                "sha256": old_sha,
            },
            "new": {
                "edition": new_edition,
                "source": "masked-column re-OCR (Qwen3.6-27B-FP8, geometric L/R + apparatus crops)",
                "rows": new_rows,
                "greek_chars": val.get("masked_greek_chars"),
                "sha256": new_sha,
            },
            "evidence": f"{val.get('verdict')} | {signals}. keep_better validated by "
                        f"bucket VALIDATION.json (tier={w['tier']}).",
            "provenance": prov_rel,
            "source": "dense-class re-OCR fleet keep-better validation "
                      "(VALIDATION.json + audit_trail.json), " + DATE,
        }
        if w.get("headword_gain") is not None:
            record["new"]["headwords_gain"] = w["headword_gain"]

        out_path = out_dir / f"{urn}.reocr-swap.json"
        if not args.check:
            out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        written.append((urn, w["tier"], ratio, old_rows, new_rows))

    for u, tier, ratio, o, n in written:
        flag = "  <-- borderline" if tier == "keep-better-likely" else ""
        print(f"{'CHECK' if args.check else 'WROTE'}  ratio={ratio:<6} rows {o}->{n}  {u}{flag}")
    print(f"\n{len(written)} works, {len(errors)} errors")
    for e in errors:
        print("ERROR:", e)
    return 1 if errors or len(written) != 16 else 0


if __name__ == "__main__":
    sys.exit(main())
