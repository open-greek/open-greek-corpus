#!/usr/bin/env python3
"""Stage the pinned GlossAPI Ekklisiastika artifact without admitting it to OGC.

The upstream parquet is a useful discovery source, not a citable edition.  Its
rows have only title/category metadata and the dataset-card's collection URL;
they do not identify the underlying GOARCH page or edition.  This tool therefore
verifies the pinned artifact, cleans only explicit structural markup, reports
deduplication evidence, and quarantines every row until an editor resolves a
stable work and source URL.  It never writes data/corpus or public_lexicon.tsv.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DECISIONS = DATA / "glossapi_source_decisions.json"
DEFAULT_INPUT = DATA / "cache" / "glossapi" / "ekklisiastika-e3e66c08" / "litourgical_texts.parquet"
DEFAULT_OUTPUT = DATA / "glossapi_ekklisiastika_intake_report.json"
DEFAULT_CORPUS = DATA / "corpus"
SOURCE_KEY = "glossapi_ekklisiastika"
REQUIRED_COLUMNS = {"texts", "katigoria", "ypokatigoria", "titlos"}

# The labels are structural markers in the source, not lexical material.  A
# matched label can be split safely when it is glued to a following Greek word.
STRUCTURAL_LABELS = (
    "ΘΕΙΑ ΛΕΙΤΟΥΡΓΙΑ",
    "ΜΕΓΑ ΑΠΟΔΕΙΠΝΟΝ",
    "ΜΙΚΡΟΝ ΑΠΟΔΕΙΠΝΟΝ",
    "ΜΕΣΟΝΥΚΤΙΚΟΝ",
    "ΕΣΠΕΡΙΝΟΣ",
    "ΟΡΘΡΟΣ",
    "ΩΡΕΣ",
    "ΑΠΟΣΤΟΛΟΣ",
    "ΕΥΑΓΓΕΛΙΟΝ",
    "ΠΡΟΚΕΙΜΕΝΟΝ",
    "ΑΝΑΓΝΩΣΜΑ",
    "ΠΑΡΟΙΜΙΑ",
    "ΚΑΘΙΣΜΑ",
    "ΨΑΛΜΟΣ",
)
BIBLICAL_LABELS = (
    "ΑΠΟΣΤΟΛ",
    "ΕΥΑΓΓΕΛ",
    "ΠΡΟΚΕΙΜΕΝ",
    "ΑΝΑΓΝΩΣΜ",
    "ΠΑΡΟΙΜ",
    "ΨΑΛΜ",
)
PATRISTIC_URN_PREFIXES = (
    "athanasius-",
    "basilius-",
    "clemens-",
    "cyrillus-",
    "epiphanius-",
    "eusebius-",
    "joannes-chrysostomus",
    "joannes-damascenus",
    "origenes",
    "theodoretus",
)
GREEK_UPPER = "Α-ΩΆΈΉΊΌΎΏΪΫἈ-ἯἸ-ὟὨ-Ὧᾈ-ᾏᾘ-ᾟᾨ-ᾯᾸ-ΆῘ-ΊῨ-Ύ"
GREEK_LOWER = "α-ωάέήίόύώϊϋΐΰἀ-ῗῠ-ῴᾀ-ᾇᾐ-ᾗᾠ-ᾧᾰ-ᾷῐ-ῗῠ-ῧῲ-ῷ"
GREEK_LETTERS = GREEK_UPPER + GREEK_LOWER
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
UNKNOWN_JOIN_RE = re.compile(
    rf"(?<=[{GREEK_UPPER}]{{3}})(?=[{GREEK_UPPER}][{GREEK_LOWER}])"
)
JOINED_PRAYER_RE = re.compile(
    rf"(?P<label>ΕΥΧΗ\s+[{GREEK_UPPER}][{GREEK_UPPER}΄’']*)"
    rf"(?=[{GREEK_UPPER}][{GREEK_LOWER}])"
)
INLINE_EDITORIAL_MARKER_RE = re.compile(r"ΤΟ\s+ΑΚΟΥΤΕ")
MIN_PASSAGE_TOKENS = 4
NEAR_ANCHOR_WORDS = 8
MAX_INTERNAL_ANCHOR_FANOUT = 64


def _load_source() -> dict[str, Any]:
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    return next(item for item in decisions["sources"] if item["key"] == SOURCE_KEY)


def _display_path(path: Path) -> Path:
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact(path: Path, source: dict[str, Any]) -> None:
    artifact = source["artifact"]
    if not path.is_file():
        raise SystemExit(f"missing pinned Ekklisiastika artifact: {path}")
    if path.stat().st_size != artifact["size"]:
        raise SystemExit(
            f"artifact size mismatch: {path.stat().st_size} != {artifact['size']}"
        )
    actual = _sha256_file(path)
    if actual != artifact["sha256"]:
        raise SystemExit(f"artifact SHA-256 mismatch: {actual} != {artifact['sha256']}")


def _is_greek(char: str) -> bool:
    point = ord(char)
    return 0x0370 <= point <= 0x03FF or 0x1F00 <= point <= 0x1FFF


def _token_case_joins(text: str) -> list[str]:
    """Return Greek tokens with an adjacent lower-case -> upper-case join.

    The historical range constants deliberately include all polytonic letters
    for structural-label matching, so they cannot distinguish upper from lower
    case.  Unicode's case predicates can, and keep this detector confined to an
    actual in-token transition such as ``ΘεοτοκίονὉ``.
    """
    return [
        unicodedata.normalize("NFC", token)
        for token in WORD_RE.findall(text)
        if any(
            _is_greek(left) and _is_greek(right) and left.islower() and right.isupper()
            for left, right in zip(token, token[1:])
        )
    ]


def greek_tokens(text: str) -> list[str]:
    return [
        unicodedata.normalize("NFC", token).casefold()
        for token in WORD_RE.findall(text)
        if any(_is_greek(char) for char in token)
    ]


def _fold_token(token: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", token) if not unicodedata.combining(char)
    ).casefold()


def _digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug_component(value: str) -> str:
    value = unicodedata.normalize("NFC", value).casefold().strip()
    return _digest_text(value)[:16]


def _header_fold(value: str) -> str:
    return _fold_token("".join(char for char in value if _is_greek(char))).upper()


def _is_known_label(line: str) -> bool:
    folded = _header_fold(line)
    return any(folded.startswith(_header_fold(label)) for label in STRUCTURAL_LABELS)


def _is_biblical_label(line: str) -> bool:
    folded = _header_fold(line)
    return any(folded.startswith(_header_fold(label)) for label in BIBLICAL_LABELS)


def _is_structural_rubric(line: str) -> bool:
    if _is_known_label(line):
        return True
    letters = [char for char in line if _is_greek(char)]
    return bool(letters) and len(letters) >= 3 and len(line) <= 160 and not any(
        char.islower() for char in letters
    )


def _repair_known_label_boundaries(text: str) -> tuple[str, list[str]]:
    repairs: list[str] = []
    for label in STRUCTURAL_LABELS:
        pattern = re.compile(
            rf"(?<![{GREEK_LETTERS}]){re.escape(label)}(?=[{GREEK_UPPER}][{GREEK_LOWER}])"
        )
        text, count = pattern.subn(f"\n{label}\n", text)
        repairs.extend([label] * count)

    def replace_prayer(match: re.Match[str]) -> str:
        repairs.append(match.group("label"))
        return f"\n{match.group('label')}\n"

    return JOINED_PRAYER_RE.sub(replace_prayer, text), repairs


def _remove_inline_editorial_markers(text: str) -> tuple[str, list[str]]:
    """Remove exact service instructions from staged running text only.

    ``ΤΟ ΑΚΟΥΤΕ`` is a repeated performance instruction, not a Greek lexical
    item.  A space separates a following word when the source welded it directly
    to the marker without dropping the surrounding running text.
    """
    markers: list[str] = []

    def replace_marker(match: re.Match[str]) -> str:
        markers.append(match.group())
        return " "

    return INLINE_EDITORIAL_MARKER_RE.sub(replace_marker, text), markers


def _normalise_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[\t\f\v]+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def _paragraphs(
    text: str, record_id: str
) -> tuple[list[dict[str, Any]], int, list[str], list[str], list[str], Counter[str]]:
    text, markers = _remove_inline_editorial_markers(text)
    text, repairs = _repair_known_label_boundaries(text)
    passages: list[dict[str, Any]] = []
    rubrics: list[str] = []
    joins: list[str] = []
    token_case_joins: Counter[str] = Counter()
    current: list[str] = []
    current_biblical = False

    def flush() -> None:
        nonlocal current
        if not current:
            return
        passage_text = "\n".join(current).strip()
        tokens = greek_tokens(passage_text)
        if len(tokens) >= MIN_PASSAGE_TOKENS:
            canonical = " ".join(tokens)
            passages.append(
                {
                    "id": f"{record_id}.p{len(passages) + 1:04d}",
                    "tokens": tokens,
                    "canonical": canonical,
                    "folded_tokens": [_fold_token(token) for token in tokens],
                    "biblical_or_quotation": current_biblical,
                    "unresolved_join": bool(joins),
                }
            )
        current = []

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            flush()
            continue
        if _is_structural_rubric(line):
            flush()
            rubrics.append(line)
            current_biblical = _is_biblical_label(line)
            continue
        if UNKNOWN_JOIN_RE.search(line):
            joins.append(line[:160])
        token_case_joins.update(_token_case_joins(line))
        current.append(line)
    flush()
    return passages, len(rubrics), repairs, markers, sorted(set(joins)), token_case_joins


def _anchor_hashes(tokens: list[str]) -> set[bytes]:
    if len(tokens) < NEAR_ANCHOR_WORDS:
        return set()
    last = len(tokens) - NEAR_ANCHOR_WORDS
    starts = {0, last, last // 4, last // 2, (3 * last) // 4}
    return {
        hashlib.sha256(" ".join(tokens[start:start + NEAR_ANCHOR_WORDS]).encode("utf-8")).digest()
        for start in starts
    }


def _mark_internal_duplicates(passages: list[dict[str, Any]]) -> tuple[set[str], set[str], int]:
    exact: set[str] = set()
    by_hash: dict[str, list[str]] = defaultdict(list)
    for passage in passages:
        by_hash[_digest_text(passage["canonical"])].append(passage["id"])
    for ids in by_hash.values():
        if len(ids) > 1:
            exact.update(ids)

    by_anchor: dict[bytes, list[str]] = defaultdict(list)
    for passage in passages:
        for anchor in _anchor_hashes(passage["folded_tokens"]):
            by_anchor[anchor].append(passage["id"])
    shared: Counter[tuple[str, str]] = Counter()
    for ids in by_anchor.values():
        ids = sorted(set(ids))
        if len(ids) > MAX_INTERNAL_ANCHOR_FANOUT:
            continue
        for pair in combinations(ids, 2):
            shared[pair] += 1
    near: set[str] = set()
    for pair, count in shared.items():
        if count >= 2:
            near.update(pair)
    near.difference_update(exact)
    return exact, near, sum(1 for count in shared.values() if count >= 2)


def _corpus_family(record: dict[str, Any]) -> str:
    key = f"{record.get('urn', '')} {record.get('source', '')}".casefold()
    if record.get("source") in {"cgpg", "pta"}:
        return "patristic"
    if any(
        term in key
        for term in (
            "septuaginta",
            "new-testament",
            "new_testament",
            "novum-testamentum",
            "vetus-testamentum",
            "biblia",
        )
    ):
        return "biblical"
    if any(term in key for term in ("hymn", "kanon", "octoech", "oktoech")):
        return "hymnographic"
    if any(term in key for term in ("liturg", "eucholog", "akolouth")):
        return "liturgical"
    if str(record.get("urn", "")).casefold().startswith(PATRISTIC_URN_PREFIXES):
        return "patristic"
    return "other"


def _witness_evidence(record: dict[str, Any], relation: str) -> dict[str, str]:
    return {
        "relation": relation,
        "family": _corpus_family(record),
        "urn": str(record.get("urn", "")),
        "locus": str(record.get("locus", "")),
        "source": str(record.get("source", "")),
        "edition": str(record.get("edition", "")),
    }


def _find_corpus_matches(
    passages: list[dict[str, Any]], corpus_dir: Path
) -> tuple[set[str], set[str], Counter[str], dict[str, int], dict[str, list[dict[str, str]]]]:
    full_hashes: dict[str, list[str]] = defaultdict(list)
    anchors: dict[bytes, list[str]] = defaultdict(list)
    for passage in passages:
        full_hashes[_digest_text(passage["canonical"])].append(passage["id"])
        for anchor in _anchor_hashes(passage["folded_tokens"]):
            anchors[anchor].append(passage["id"])

    exact: set[str] = set()
    near: set[str] = set()
    families: Counter[str] = Counter()
    evidence: dict[str, list[dict[str, str]]] = defaultdict(list)
    scanned = {"files": 0, "passages": 0}
    for path in sorted(corpus_dir.glob("*.jsonl")):
        scanned["files"] += 1
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                tokens = greek_tokens(record.get("text", ""))
                if len(tokens) < MIN_PASSAGE_TOKENS:
                    continue
                scanned["passages"] += 1
                matching_exact = full_hashes.get(_digest_text(" ".join(tokens)), [])
                if matching_exact:
                    exact.update(matching_exact)
                    family = _corpus_family(record)
                    families[family] += len(matching_exact)
                    witness = _witness_evidence(record, "exact")
                    for passage_id in matching_exact:
                        evidence[passage_id].append(witness)
                hits: Counter[str] = Counter()
                for anchor in _anchor_hashes([_fold_token(token) for token in tokens]):
                    hits.update(anchors.get(anchor, []))
                for passage_id, count in hits.items():
                    if count >= 2:
                        near.add(passage_id)
                        family = _corpus_family(record)
                        families[family] += 1
                        evidence[passage_id].append(_witness_evidence(record, "near"))
    near.difference_update(exact)
    return exact, near, families, scanned, {
        passage_id: sorted(
            witnesses,
            key=lambda item: (
                item["relation"], item["family"], item["urn"], item["locus"], item["edition"],
            ),
        )
        for passage_id, witnesses in sorted(evidence.items())
    }


def _record_summary(
    row: dict[str, Any], index: int, source: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    record_id = f"{SOURCE_KEY}:{index:04d}"
    metadata = {
        "title": row.get("titlos"),
        "category": row.get("katigoria"),
        "subcategory": row.get("ypokatigoria"),
    }
    service_material = "\0".join((metadata[key] or "") for key in sorted(metadata))
    source_text = _normalise_text(row.get("texts") or "")
    passages, rubric_count, repairs, markers, joins, token_case_joins = _paragraphs(
        source_text, record_id
    )
    summary = {
        "source_record_id": record_id,
        "provisional_work_key": f"glossapi-ekklisiastika-{source['revision'][:12]}",
        "service_unit_key": f"glossapi-service-{_slug_component(service_material)}",
        "locus": f"row:{index:04d}",
        "passage_locus_scheme": f"row:{index:04d}.pNNNN",
        "provenance": {
            **metadata,
            "source_url": source["source_url"],
            "source_url_scope": "collection only; no per-record GOARCH URL in parquet",
            "repo": source["repo"],
            "revision": source["revision"],
            "dataset_license": source["license"],
            "underlying_source_rights": source["underlying_source_rights"],
            "artifact_sha256": source["artifact"]["sha256"],
        },
        "cleaning": {
            "source_characters": len(row.get("texts") or ""),
            "cleaned_characters": sum(len(passage["canonical"]) for passage in passages),
            "structural_rubrics_removed": rubric_count,
            "inline_editorial_markers_removed": len(markers),
            "inline_editorial_markers": sorted(set(markers)),
            "known_join_repairs": len(repairs),
            "known_join_labels": sorted(set(repairs)),
            "unresolved_join_boundaries": joins,
            "unresolved_token_case_join_forms": dict(sorted(token_case_joins.items())),
        },
        "passages": len(passages),
        "greek_tokens": sum(len(passage["tokens"]) for passage in passages),
        "biblical_or_quotation_passages": sum(
            passage["biblical_or_quotation"] for passage in passages
        ),
    }
    return summary, passages


def build_report(
    rows: Iterable[dict[str, Any]], source: dict[str, Any], corpus_dir: Path | None
) -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    passages: list[dict[str, Any]] = []
    record_for_passage: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows, 1):
        summary, row_passages = _record_summary(row, index, source)
        summaries.append(summary)
        passages.extend(row_passages)
        record_for_passage.update({passage["id"]: summary for passage in row_passages})

    within_exact, within_near, within_near_pairs = _mark_internal_duplicates(passages)
    if corpus_dir is None:
        corpus_exact, corpus_near, corpus_families, corpus_scan = set(), set(), Counter(), {
            "files": 0,
            "passages": 0,
        }
        corpus_evidence: dict[str, list[dict[str, str]]] = {}
    else:
        (
            corpus_exact,
            corpus_near,
            corpus_families,
            corpus_scan,
            corpus_evidence,
        ) = _find_corpus_matches(passages, corpus_dir)

    by_record: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for passage in passages:
        by_record[passage["id"].split(".p", 1)[0]].append(passage)
    dispositions = {"admitted": [], "rejected": [], "quarantined": [], "duplicate_only": []}
    for summary in summaries:
        row_passages = by_record[summary["source_record_id"]]
        passage_ids = {passage["id"] for passage in row_passages}
        duplicate_ids = (within_exact | within_near | corpus_exact | corpus_near) & passage_ids
        reasons = ["unresolved_source_work_identity"]
        if (summary["cleaning"]["unresolved_join_boundaries"]
                or summary["cleaning"]["unresolved_token_case_join_forms"]):
            reasons.append("unresolved_join_boundary")
        if summary["biblical_or_quotation_passages"]:
            reasons.append("biblical_or_quotation_requires_separate_witness")
        if duplicate_ids:
            reasons.append("duplicate_witness_requires_precedence_decision")
        summary["deduplication"] = {
            "within_source_exact_passages": len(passage_ids & within_exact),
            "within_source_near_passages": len(passage_ids & within_near),
            "existing_corpus_exact_passages": len(passage_ids & corpus_exact),
            "existing_corpus_near_passages": len(passage_ids & corpus_near),
        }
        summary["existing_corpus_matches"] = [
            {
                "passage_locus": passage["id"].removeprefix(f"{SOURCE_KEY}:"),
                "witnesses": corpus_evidence[passage["id"]],
            }
            for passage in row_passages
            if passage["id"] in corpus_evidence
        ]
        summary["admission"] = "quarantined"
        summary["reasons"] = reasons
        if passage_ids and duplicate_ids == passage_ids:
            summary["deduplication"]["resolution"] = "duplicate_only"
            dispositions["duplicate_only"].append(summary["source_record_id"])
        else:
            summary["deduplication"]["resolution"] = "not_resolved_as_duplicate"
            dispositions["quarantined"].append(summary["source_record_id"])

    category_counts = Counter((item["provenance"]["category"] or "") for item in summaries)
    return {
        "schema_version": 1,
        "source": {
            "key": source["key"],
            "repo": source["repo"],
            "revision": source["revision"],
            "dataset_license": source["license"],
            "source_url": source["source_url"],
            "underlying_source_rights": source["underlying_source_rights"],
            "artifact": source["artifact"],
        },
        "admission_policy": {
            "corpus_write_attempted": False,
            "public_lexicon_rebuild_attempted": False,
            "rule": (
                "No row is admitted until an editor supplies written GOARCH reuse permission "
                "or an independently licensed replacement, its exact required attribution, a "
                "stable work identity, per-record source URL, edition/locus mapping, and a "
                "precedence decision."
            ),
        },
        "statistics": {
            "source_rows": len(summaries),
            "staged_passages": len(passages),
            "greek_tokens_after_structural_cleaning": sum(item["greek_tokens"] for item in summaries),
            "structural_rubrics_removed": sum(
                item["cleaning"]["structural_rubrics_removed"] for item in summaries
            ),
            "inline_editorial_markers_removed": sum(
                item["cleaning"]["inline_editorial_markers_removed"] for item in summaries
            ),
            "known_join_repairs": sum(item["cleaning"]["known_join_repairs"] for item in summaries),
            "unresolved_join_boundaries": sum(
                len(item["cleaning"]["unresolved_join_boundaries"]) for item in summaries
            ),
            "unresolved_token_case_join_forms": sum(
                len(item["cleaning"]["unresolved_token_case_join_forms"])
                for item in summaries
            ),
            "unresolved_token_case_join_tokens": sum(
                sum(item["cleaning"]["unresolved_token_case_join_forms"].values())
                for item in summaries
            ),
            "biblical_or_quotation_passages": sum(
                item["biblical_or_quotation_passages"] for item in summaries
            ),
            "within_source_exact_duplicate_passages": len(within_exact),
            "within_source_near_duplicate_passages": len(within_near),
            "within_source_near_duplicate_pairs": within_near_pairs,
            "existing_corpus_exact_duplicate_passages": len(corpus_exact),
            "existing_corpus_near_duplicate_passages": len(corpus_near),
            "existing_corpus_match_families": dict(sorted(corpus_families.items())),
            "existing_corpus_scan": corpus_scan,
            "categories": dict(sorted(category_counts.items())),
        },
        "dispositions": dispositions,
        "records": summaries,
    }


def _load_rows(path: Path) -> list[dict[str, Any]]:
    table = pq.read_table(path)
    columns = set(table.column_names)
    if columns != REQUIRED_COLUMNS:
        raise SystemExit(f"unexpected parquet columns: {sorted(columns)}")
    return table.to_pylist()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument(
        "--skip-existing-corpus-dedup",
        action="store_true",
        help="write a staging-only report without the required existing-corpus comparison",
    )
    args = parser.parse_args()

    source = _load_source()
    verify_artifact(args.input, source)
    report = build_report(
        _load_rows(args.input),
        source,
        None if args.skip_existing_corpus_dedup else args.corpus_dir,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    stats = report["statistics"]
    print(
        f"staged {stats['source_rows']} rows / {stats['staged_passages']} passages; "
        f"admitted 0; quarantined {len(report['dispositions']['quarantined'])}; "
        f"duplicate-only {len(report['dispositions']['duplicate_only'])}"
    )
    print(f"wrote {_display_path(args.output)}")


if __name__ == "__main__":
    main()
