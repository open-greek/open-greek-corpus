#!/usr/bin/env python3
"""Screen retained Photius OCR outcomes without choosing or editing a reading."""
from collections import Counter, defaultdict
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import unicodedata

from prepare_photius_coverage import ROOT, build, build_later_gap
from photius_retries import known_retry_manifests, known_supplement_manifests
from report_polytonic_loss import POLICY, detect


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


REPETITION_POLICY = {
    "minimum_identical_word_run": 8,
    "phrase_words": 8,
    "minimum_identical_phrase_occurrences": 4,
    "minimum_repeated_line_greek_letters": 20,
    "minimum_identical_line_occurrences": 4,
    "minimum_output_characters": 1000,
    "maximum_paired_greek_word_ratio": 1.8,
    "purpose": "Source-review candidates only; intentional repetition and sparse source pages can trigger these rules. No text selection or correction.",
}

APPARATUS_POLICY = {
    "editorial_terms": ["add", "om", "post", "corr", "malim", "cod", "mss", "Rothomagensis",
                        "Hoeschel", "Schott", "Scaliger", "Casaubon", "Fabricius", "Ruhnken"],
    "numbered_note_line_pattern": r"^[abαβ]\.\s*\d{1,2}\.",
    "purpose": "Candidate screen for critical notes among fresh Photius body predictions. A source review must establish the role; Greek-only apparatus may escape this screen.",
}


def words(text):
    return re.findall(r"[Ͱ-Ͽἀ-῿]+", unicodedata.normalize("NFC", text))


def repetition(text):
    tokens = words(text)
    run = max((len(list(group)) for _, group in itertools.groupby(tokens)), default=0)
    width = REPETITION_POLICY["phrase_words"]
    phrases = Counter(tuple(tokens[i:i + width]) for i in range(len(tokens) - width + 1))
    # Stable tie order does not depend on Counter insertion order.
    phrase, count = min(phrases.items(), key=lambda item: (-item[1], item[0])) if phrases else ((), 0)
    lines = Counter(line.strip() for line in text.splitlines()
                    if sum(c.isalpha() for c in "".join(words(line))) >= REPETITION_POLICY["minimum_repeated_line_greek_letters"])
    line, occurrences = min(lines.items(), key=lambda item: (-item[1], item[0])) if lines else ("", 0)
    return {"greek_word_runs": len(tokens), "maximum_identical_word_run": run,
            "most_repeated_phrase": {"words": list(phrase), "occurrences": count},
            "most_repeated_line": {"text": line if occurrences > 1 else None, "occurrences": occurrences}}


def screen(text, finish_reason="stop", error=None):
    marks = detect(text)
    repeat = repetition(text)
    terms = {term: len(re.findall(r"\b" + re.escape(term) + r"\b", text, flags=re.I))
             for term in APPARATUS_POLICY["editorial_terms"]}
    terms = {term: count for term, count in terms.items() if count}
    note_lines = len(re.findall(APPARATUS_POLICY["numbered_note_line_pattern"], text, flags=re.M))
    reasons = []
    if error or finish_reason != "stop":
        reasons.append("failed-or-length-terminated-outcome")
    if marks["flag"]:
        reasons.append("frozen-polytonic-mark-loss-screen")
    if repeat["maximum_identical_word_run"] >= REPETITION_POLICY["minimum_identical_word_run"]:
        reasons.append("identical-word-run")
    if repeat["most_repeated_phrase"]["occurrences"] >= REPETITION_POLICY["minimum_identical_phrase_occurrences"]:
        reasons.append("repeated-eight-word-phrase")
    if repeat["most_repeated_line"]["occurrences"] >= REPETITION_POLICY["minimum_identical_line_occurrences"]:
        reasons.append("repeated-output-line")
    if len(text) < REPETITION_POLICY["minimum_output_characters"]:
        reasons.append("short-output-needs-source-coverage-check")
    if terms or note_lines:
        reasons.append("editorial-apparatus-candidate")
    return {"characters": len(text), "polytonic": marks, "repetition": repeat,
            "apparatus_candidates": {"editorial_term_occurrences": terms, "numbered_note_lines": note_lines},
            "review_flags": reasons}


def audit(paths):
    policy_raw = (ROOT / "data/evaluation/polytonic-loss/policy.json").read_bytes()
    if json.loads(policy_raw) != POLICY:
        raise ValueError("Frozen polytonic policy differs from its detector")
    authority = {sha(encode(m)): m for m in [build(), build_later_gap()]}
    authority.update({digest: value[1] for digest, value in known_retry_manifests().items()})
    authority.update({digest: value[1] for digest, value in known_supplement_manifests().items()})
    files, rows, seen = [], [], set()
    for path in sorted(paths, key=lambda p: sha(p.read_bytes())):
        raw = path.read_bytes()
        digest = sha(raw)
        if digest in seen:
            raise ValueError("Repeated raw outcome file")
        seen.add(digest)
        lines = [line for line in raw.splitlines() if line.strip()]
        values = [json.loads(line) for line in lines]
        if not values or "_meta" not in values[0] or any("_meta" in value for value in values[1:]):
            raise ValueError("Ambiguous OCR metadata")
        meta = values[0]["_meta"]
        manifest = authority.get(meta.get("manifest_sha256"))
        if manifest is None or meta.get("prompt") != manifest["prompt"]:
            raise ValueError("Unknown pinned Photius request or prompt")
        jobs = {page["id"]: page for page in manifest["pages"]}
        present = set()
        for line, row in zip(lines[1:], values[1:]):
            identifier = row["id"]
            if identifier not in jobs or identifier in present:
                raise ValueError("Repeated or unknown Photius region")
            present.add(identifier)
            job = jobs[identifier]
            suffix = job.get("prompt_suffix", manifest["sources"][job["source"]].get("prompt_suffix", ""))
            prompt = manifest["prompt"] + (" " + suffix if suffix else "")
            if (row.get("region") != job["region"] or row.get("source") != job["source"]
                    or row.get("scan_page") != job["scan_page"] or row.get("prompt_sha256") != sha(prompt.encode())):
                raise ValueError("OCR region differs from its pinned source geometry or prompt")
            text = row.get("raw_prediction")
            if not isinstance(text, str):
                text = ""
            rows.append({"id": identifier, "scan_page": row["scan_page"], "region": row["region"],
                         "model": meta["model"], "revision": meta["revision"],
                         "manifest_sha256": meta["manifest_sha256"], "raw_file_sha256": digest,
                         "prediction_record_sha256": sha(line), "image_sha256": row.get("image_sha256"),
                         "finish_reason": row.get("finish_reason"), "error_present": bool(row.get("error")),
                         **screen(text, row.get("finish_reason"), row.get("error"))})
        files.append({"sha256": digest, "model": meta["model"], "revision": meta["revision"],
                      "manifest_sha256": meta["manifest_sha256"], "outcomes": len(present),
                      "expected_regions": len(jobs), "all_regions_returned": present == set(jobs)})
    groups = defaultdict(list)
    for row in rows:
        groups[(row["manifest_sha256"], row["id"])].append(row)
    for group in groups.values():
        # Pair comparisons need different independently retained checkpoints.
        if len(group) != 2 or len({(r["model"], r["revision"]) for r in group}) != 2:
            continue
        counts = [r["repetition"]["greek_word_runs"] for r in group]
        ratio = max(counts) / max(1, min(counts))
        for row in group:
            row["paired_greek_word_ratio"] = ratio
            if ratio > REPETITION_POLICY["maximum_paired_greek_word_ratio"]:
                row["review_flags"].append("different-output-length-between-checkpoints")
    rows.sort(key=lambda r: (r["model"], r["revision"], r["manifest_sha256"], r["id"]))
    return {"schema_version": 1, "work": "photius.bibliotheca",
            "scope": "All supplied retained outcomes, including failures; a partial snapshot does not establish full page coverage.",
            "frozen_mark_policy": {"path": "data/evaluation/polytonic-loss/policy.json", "sha256": sha(policy_raw)},
            "repetition_policy": REPETITION_POLICY, "apparatus_policy": APPARATUS_POLICY, "raw_files": files,
            "outcome_count": len(rows), "flagged_outcomes": sum(bool(row["review_flags"]) for row in rows),
            "flag_counts": dict(sorted(Counter(flag for row in rows for flag in row["review_flags"]).items())),
            "outcomes": rows, "selection_rule": None,
            "generated_by": "scripts/audit_photius_fresh.py"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ocr", type=Path, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.ocr)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(encode(report))
    print(json.dumps({k: report[k] for k in ("outcome_count", "flagged_outcomes", "flag_counts")}))
