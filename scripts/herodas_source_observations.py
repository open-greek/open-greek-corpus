#!/usr/bin/env python3
"""Source-verified roles in the existing, incomplete Headlam–Knox excerpt.

This review changes no spelling, supplies no missing verse, and does not decide
between critical restorations. Offsets address the exact currently served text,
including its historical transcription variants. Printed layout, not word shape
or lookup success, distinguishes dialogue from scholarly material.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path


WORK = "herodas.mimiambi"
INPUT_CORPUS_SHA256 = "266915ced62896c3503c2ae0bb59bfc202a7e25dfe6c8ff1035313cdfaa00274"
INPUT_TEXTS_SHA256 = "5d923cfe27226ba48755ce5b95193fb2520581717446da87bb2250c7081a9727"
SOURCE_SHA256 = "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a"
SOURCE = {
    "title": "Herodas: The Mimes and fragments",
    "editor": ["Walter Headlam (notes)", "A. D. Knox (editor)"],
    "year": 1922,
    "publisher": "Cambridge University Press",
    "url": "https://archive.org/details/mimesfragments00hero",
    "download_url": "https://archive.org/download/mimesfragments00hero/mimesfragments00hero.pdf",
    "filename": "mimesfragments00hero.pdf",
    "sha256": SOURCE_SHA256,
    "bytes": 35869325,
    "pdf_pages": 542,
}
QUALIFICATION = (
    "This role-only review covers all 136 rows of the existing excerpt, not a full "
    "Herodas text. It preserves every original reading, including OCR spelling, "
    "punctuation, incomplete clauses, bracketed supplies, and attribution variants. "
    "It does not certify complete critical markup or establish the transmitted "
    "status of restorations. Speaker labels identify the edition's printed roles; "
    "their exclusion does not adjudicate disputed distributions of dialogue."
)

# Explicit row assignments verified against all 21 corresponding scan pages.
# A means dialogue or a fragment printed as body; S is a printed speaker label;
# T is a title; H is a running header; P is apparatus; C is commentary;
# E is an editorial source/attribution note; M requires exact within-row cuts.
PAGE_ROLES = {
    72: "T S A S A S A S A A S A S A S A S A S A S A S A",
    73: "P P",
    74: "H S A S A S A S A P P",
    132: "T S A P P P",
    133: {2: "P"},
    180: "T S M",
    182: "M",
    236: "T S A A S A P P P P",
    238: "A A A A P",
    239: "P P P P P P",
    290: "T A S A A S A A S A A",
    292: "H S A S A S A S A S A S A S A S A S A S A",
    294: "A S A A S A",
    295: "P P",
    344: "T A S A A S A A",
    345: "P",
    346: "M M M M M M M",
    472: "T S A A A E",
    474: "C",
    476: "C C",
    477: "C C",
}
ROLE_NAMES = {"A": "authorial", "S": "speaker", "T": "title", "H": "running-header",
              "P": "apparatus", "C": "commentary", "E": "editorial-source-note"}
ROW_ROLES = {}
for _page, _roles in PAGE_ROLES.items():
    _mapping = _roles if isinstance(_roles, dict) else dict(enumerate(_roles.split(), 1))
    for _number, _role in _mapping.items():
        ROW_ROLES[f"herodas_hk_{_page:04d}.{_number}"] = _role

ROLE_EVIDENCE = {
    "authorial": "Printed as verse/dialogue in the main Greek text, above the apparatus; existing reading retained without restoration or attribution adjudication.",
    "speaker": "Separately typeset speaker name in the printed dialogue, not spoken words.",
    "title": "Separately typeset mime title, not spoken verse.",
    "running-header": "Running work/page heading above the dialogue, not spoken verse.",
    "apparatus": "Smaller-type textual notes below the dialogue or facing translation, identified by verse numbers, manuscript sigla, and named emendations.",
    "commentary": "Printed in the separately headed NOTES/commentary section, including quotations from other authors and discussion of readings.",
    "editorial-source-note": "Small-type source note below the fragments, quoting Zenobius and discussing Bergk's attribution; not printed as a Herodas fragment.",
}


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def _texts_digest(rows):
    return hashlib.sha256(_encoded([
        {"locus": row["locus"], "original_text": row.get("original_text", row.get("text"))}
        for row in rows
    ])).hexdigest()


def verify_source_pdf(path: str | Path) -> None:
    raw = Path(path).read_bytes()
    if len(raw) != SOURCE["bytes"] or hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Headlam–Knox source scan changed")


def _unique(text, marker):
    if text.count(marker) != 1:
        raise ValueError(f"Reviewed Herodas boundary is missing or repeated: {marker}")
    return text.index(marker)


def _span(text, start, end, role):
    if start >= end:
        raise ValueError("Reviewed Herodas span must contain literal text")
    return {"start": start, "end": end, "text": text[start:end], "role": role,
            "lexical_eligible": role == "authorial", "evidence": ROLE_EVIDENCE[role]}


def _spans(locus, text):
    code = ROW_ROLES[locus]
    if code != "M":
        return [_span(text, 0, len(text), ROLE_NAMES[code])]
    if locus == "herodas_hk_0180.3":
        apparatus = _unique(text, " 6 χαλκίνδα P.")
        return [_span(text, 0, apparatus, "authorial"),
                _span(text, apparatus, len(text), "apparatus")]
    if locus == "herodas_hk_0182.1":
        label = " # ΛΑΜΠΡΙΣΚΟΣ # "
        start = _unique(text, label)
        end = start + len(label)
        apparatus = _unique(text, " 33 πθι P.")
        if not end < apparatus:
            raise ValueError("Reviewed dialogue, speaker, and apparatus order changed")
        return [_span(text, 0, start, "authorial"), _span(text, start, end, "speaker"),
                _span(text, end, apparatus, "authorial"),
                _span(text, apparatus, len(text), "apparatus")]
    if locus.startswith("herodas_hk_0346."):
        number = int(locus.rsplit(".", 1)[1])
        label = "ΜΗΤΡΩ " if number in (1, 3, 5, 7) else "ΚΟΡΙΤΤΩ "
        if not text.startswith(label):
            raise ValueError("Reviewed Herodas inline speaker label changed")
        return [_span(text, 0, len(label), "speaker"),
                _span(text, len(label), len(text), "authorial")]
    raise ValueError(f"No reviewed mixed-row boundaries: {locus}")


def _reviewed_row(row):
    locus, text = row["locus"], row.get("original_text", row.get("text"))
    page = int(locus.split(".", 1)[0][-4:])
    result = {
        "locus": locus,
        "original_text": text,
        "source_page": page,
        "printed_page": str(page - 70),
        "spans": _spans(locus, text),
        "evidence": f"Manual inspection of the pinned Headlam–Knox 1922 scan, PDF page {page} (printed page {page - 70}); printed layout and note boundaries.",
    }
    if locus in {"herodas_hk_0472.4", "herodas_hk_0472.5"}:
        result["qualification"] = "Printed separately as IX a/IX b body fragments. The edition's placement is retained without a new attribution decision."
    elif locus == "herodas_hk_0472.3":
        result["qualification"] = "Printed body includes substantial bracketed supplies. Existing bracket variants and their lexical policy remain unchanged; this is not a certification of restored wording."
    elif page in {236, 238, 239}:
        result["qualification"] = "The edition explicitly notes disputed distributions of dialogue. Printed speaker assignments are preserved rather than adjudicated."
    return result


def build_source_review(rows: list[dict], reviewed_at: str, source_pdf: str | Path | None = None) -> dict:
    """Generate a complete role packet from exact unchanged baseline rows."""
    if source_pdf is not None:
        verify_source_pdf(source_pdf)
    if len(rows) != len(ROW_ROLES) or {row["locus"] for row in rows} != set(ROW_ROLES):
        raise ValueError("Herodas review does not account for every original row exactly once")
    if any(row.get("urn") != WORK for row in rows):
        raise ValueError("Herodas source review contains another work")
    raw = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()
    if hashlib.sha256(raw).hexdigest() != INPUT_CORPUS_SHA256 or _texts_digest(rows) != INPUT_TEXTS_SHA256:
        raise ValueError("Herodas baseline rows changed")
    packet = {"schema_version": 1, "reviewed_at": reviewed_at, "source": dict(SOURCE),
              "input_corpus_sha256": INPUT_CORPUS_SHA256,
              "rows": [_reviewed_row(row) for row in rows], "qualification": QUALIFICATION}
    validate_source_review(packet)
    return packet


def validate_source_review(packet: dict) -> None:
    """Check frozen source pins, literal preimages, all roles, and total offsets."""
    if set(packet) != {"schema_version", "reviewed_at", "source", "input_corpus_sha256", "rows", "qualification"}:
        raise ValueError("Herodas source-review fields changed")
    if packet["schema_version"] != 1 or packet["source"] != SOURCE or packet["qualification"] != QUALIFICATION:
        raise ValueError("Herodas source identity or review scope changed")
    if packet["input_corpus_sha256"] != INPUT_CORPUS_SHA256:
        raise ValueError("Herodas source review has another baseline")
    try:
        timestamp = datetime.fromisoformat(packet["reviewed_at"].replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("Herodas review requires an explicit timestamp") from error
    if timestamp.tzinfo is None:
        raise ValueError("Herodas review timestamp requires a time zone")
    rows = packet["rows"]
    if len(rows) != len(ROW_ROLES) or {row["locus"] for row in rows} != set(ROW_ROLES) or _texts_digest(rows) != INPUT_TEXTS_SHA256:
        raise ValueError("Herodas original row accounting or preimages changed")
    for row in rows:
        if row != _reviewed_row(row):
            raise ValueError(f"Herodas source role or literal boundary changed: {row['locus']}")
        cursor = 0
        for span in row["spans"]:
            if span["start"] != cursor or span["end"] <= cursor or span["text"] != row["original_text"][cursor:span["end"]]:
                raise ValueError("Herodas spans must cover the exact original text contiguously")
            cursor = span["end"]
        if cursor != len(row["original_text"]):
            raise ValueError("Herodas review left unclassified characters")


def review_counts(packet: dict) -> dict:
    validate_source_review(packet)
    spans = [span for row in packet["rows"] for span in row["spans"]]
    return {"rows": len(packet["rows"]), "scan_pages": len({row["source_page"] for row in packet["rows"]}),
            "spans": len(spans), "roles": dict(Counter(span["role"] for span in spans)),
            "mixed_rows": sum(len(row["spans"]) > 1 for row in packet["rows"]),
            "rows_with_authorial_text": sum(any(span["lexical_eligible"] for span in row["spans"]) for row in packet["rows"]),
            "wholly_editorial_rows": sum(not any(span["lexical_eligible"] for span in row["spans"]) for row in packet["rows"])}
