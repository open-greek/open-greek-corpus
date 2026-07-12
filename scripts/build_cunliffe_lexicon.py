#!/usr/bin/env python3
"""Ingest the structured Perseus / Scaife-Viewer digital Cunliffe lexicon into COG.

Source (public):
  Richard John Cunliffe, "A Lexicon of the Homeric Dialect" (London: Blackie and
  Son, 1924; public domain). Digitally encoded as TEI EpiDoc by the Perseus
  Digital Library (ed. Gregory Crane, "with many, many corrections by Helma Dik";
  Perseus Project, Tufts University), and restructured into citable ATLAS JSON by
  the Scaife-Viewer "Beyond Translation" project. Homer citations are already
  linked to canonical CTS URNs (tlg0012.tlg001 = Iliad, tlg0012.tlg002 = Odyssey).

  TEI:        https://github.com/gregorycrane/Homerica
              (cunliffe.lexentries.unicode.xml)
  ATLAS JSON: https://github.com/scaife-viewer/beyond-translation-site
              (backend/data/annotations/dictionaries/cunliffe-1-lex.json)

This script reads the ATLAS lexicon JSON and writes a structured reference dataset
under data/reference/cunliffe-lexicon/, preserving headword, sub-senses,
definitions, and every citation, and adding derived {corpus, book, line}
alongside each citation's CTS URN.

The output is REFERENCE material, not served corpus text: it does not enter the
source-precedence ladder, is not assigned a served work-id, and is not listed in
corpus_editions.json. It complements the OCR'd grammatical appendix already in
COG under data/reference/cunliffe-appendix/ (the conditional / relative-sentence
table). Lexicon + appendix together cover the two public-domain parts of Cunliffe.

Scope note: Cunliffe's companion index of Homeric proper and place names is a
separate, later work still under United States copyright (public domain only from
1 January 2027) and is deliberately NOT ingested here.

Run:
  python3 scripts/build_cunliffe_lexicon.py --lex /path/to/cunliffe-1-lex.json

Obtain the source JSON from the public Beyond-Translation repo above (it is also
the public data behind any local working copy).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data" / "reference" / "cunliffe-lexicon"

# CTS work-id -> corpus tag used across COG reference citations.
WORK_CORPUS = {"tlg0012.tlg001": "il", "tlg0012.tlg002": "od"}
CTS_RE = re.compile(
    r"urn:cts:greekLit:(tlg0012\.tlg00[12])\.perseus-grc2:(\d+)\.(\d+)$")
TAG_RE = re.compile(r"<[^>]+>")
MARKER_RE = re.compile(r"^([†*‡]+)")

PUBLIC_SOURCES = {
    "tei_repo": "https://github.com/gregorycrane/Homerica",
    "atlas_repo": "https://github.com/scaife-viewer/beyond-translation-site",
    "atlas_lex_path": "backend/data/annotations/dictionaries/cunliffe-1-lex.json",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_html(s: str | None) -> str | None:
    if not s:
        return None
    text = html.unescape(TAG_RE.sub(" ", s))
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def resolve_citation(raw: dict) -> dict:
    """Normalize one ATLAS citation to {ref, quote, corpus, book, line, cts_urn}."""
    data = raw.get("data") or {}
    cts = data.get("urn") or None
    ref = data.get("ref") or None
    quote = data.get("quote") or None
    corpus = book = line = None
    if cts:
        m = CTS_RE.match(cts)
        if m:
            corpus = WORK_CORPUS.get(m.group(1))
            book = int(m.group(2))
            line = int(m.group(3))
    return {
        "ref": ref,
        "quote": quote,
        "corpus": corpus,
        "book": book,
        "line": line,
        "cts_urn": cts,
    }


def convert_sense(sense: dict) -> dict:
    out = {
        "label": (sense.get("label") or "").strip() or None,
        "definition": (sense.get("definition") or "").strip() or None,
        "citations": [resolve_citation(c) for c in sense.get("citations", [])],
        "source_urn": sense.get("urn"),
    }
    children = sense.get("children") or []
    if children:
        out["subsenses"] = [convert_sense(c) for c in children]
    return out


def convert_entry(idx: int, entry: dict) -> dict:
    raw_hw = entry.get("headword") or ""
    dagger = asterisk = False
    m = MARKER_RE.match(raw_hw)
    headword = raw_hw
    if m:
        marks = m.group(1)
        dagger = "†" in marks
        asterisk = "*" in marks
        headword = raw_hw[m.end():]
    content_html = (entry.get("data") or {}).get("content")
    return {
        "id": f"cunliffe-lex-{idx:05d}",
        "n": idx,
        "headword": headword,
        "headword_raw": raw_hw,
        "dagger": dagger,
        "asterisk": asterisk,
        "content_html": content_html,
        "content_text": strip_html(content_html),
        "senses": [convert_sense(s) for s in entry.get("senses", [])],
        "source_urn": entry.get("urn"),
    }


def _iter_citations(senses):
    for s in senses:
        yield from s["citations"]
        yield from _iter_citations(s.get("subsenses", []))


def _count_senses(senses: list[dict]) -> int:
    return sum(1 + _count_senses(s.get("subsenses", [])) for s in senses)


def _max_depth(senses: list[dict]) -> int:
    if not senses:
        return 0
    return 1 + max(_max_depth(s.get("subsenses", [])) for s in senses)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lex", type=Path, required=True,
                    help="Path to cunliffe-1-lex.json (Beyond-Translation ATLAS).")
    args = ap.parse_args()
    if not args.lex.exists():
        raise SystemExit(
            f"Source not found: {args.lex}\nObtain it from {PUBLIC_SOURCES['atlas_repo']} "
            f"({PUBLIC_SOURCES['atlas_lex_path']}).")

    data = json.loads(args.lex.read_text(encoding="utf-8"))
    raw_entries = data.get("entries", [])
    entries = [convert_entry(i + 1, e) for i, e in enumerate(raw_entries)]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- statistics ----
    total = len(entries)
    with_hw = sum(1 for e in entries if e["headword"])
    with_senses = sum(1 for e in entries if e["senses"])
    with_content = sum(1 for e in entries if e["content_text"])
    dagger_n = sum(1 for e in entries if e["dagger"])
    asterisk_n = sum(1 for e in entries if e["asterisk"])
    sense_count = sum(_count_senses(e["senses"]) for e in entries)
    max_depth = max((_max_depth(e["senses"]) for e in entries), default=0)
    cit_total = cit_resolved = il = od = 0
    for e in entries:
        for c in _iter_citations(e["senses"]):
            cit_total += 1
            if c["line"] is not None:
                cit_resolved += 1
            if c["corpus"] == "il":
                il += 1
            elif c["corpus"] == "od":
                od += 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ---- write entries + headword index ----
    (OUT_DIR / "cunliffe_lexicon.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    index: dict[str, list[str]] = {}
    for e in entries:
        index.setdefault(e["headword"], []).append(e["id"])
    (OUT_DIR / "cunliffe_lexicon_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=0) + "\n", encoding="utf-8")

    stats = {
        "entries": total,
        "with_headword": with_hw,
        "with_senses": with_senses,
        "with_content_block": with_content,
        "dagger_marked": dagger_n,
        "asterisk_marked": asterisk_n,
        "senses_total_incl_subsenses": sense_count,
        "max_sense_depth": max_depth,
        "citations_total": cit_total,
        "citations_resolved_to_book_line": cit_resolved,
        "citation_resolution_rate": round(cit_resolved / cit_total, 5) if cit_total else 0,
        "iliad_citations": il,
        "odyssey_citations": od,
    }

    manifest = {
        "id": "cunliffe-lexicon",
        "title": "Cunliffe, A Lexicon of the Homeric Dialect (structured, Perseus/Scaife)",
        "kind": "reference",
        "status": "reference material - NOT a served text work",
        "not_served_note": (
            "This is reference / bonus material, not part of the served running-text "
            "corpus. It is a lexicon (reference), not a text edition, so it does NOT "
            "enter the source-precedence ladder, is NOT assigned a served work-id, and "
            "is NOT listed in corpus_editions.json or the work-id registry. It lives "
            "under data/reference/, entirely separate from data/corpus/."),
        "complements": (
            "data/reference/cunliffe-appendix/ holds Cunliffe's grammatical appendix (the "
            "conditional / relative-sentence table, OCR'd separately). This directory holds "
            "the main lexicon body. Cunliffe's companion index of Homeric proper and place "
            "names is a later work still under US copyright (public domain from 2027) and is "
            "not included here."),
        "provenance": {
            "author": "Richard John Cunliffe",
            "work": "A Lexicon of the Homeric Dialect",
            "year": 1924,
            "original_publisher": "London: Blackie and Son",
            "public_domain_text": True,
            "digital_encoding": (
                "TEI EpiDoc by the Perseus Digital Library (Perseus Project, Tufts "
                "University), edited by Gregory Crane, with many corrections by Helma Dik."),
            "restructured_by": (
                "Scaife-Viewer 'Beyond Translation' project (ATLAS citable JSON, with Homer "
                "citations linked to canonical CTS URNs)."),
            "tei_source_repo": PUBLIC_SOURCES["tei_repo"],
            "atlas_source_repo": PUBLIC_SOURCES["atlas_repo"],
            "atlas_source_file": PUBLIC_SOURCES["atlas_lex_path"],
            "atlas_source_sha256": sha256_of(args.lex),
            "atlas_source_label": data.get("label"),
            "atlas_source_urn": data.get("urn"),
        },
        "license": {
            "underlying_text": "Public domain (Cunliffe 1924; US public domain since 2020).",
            "digital_encoding_and_corrections": (
                "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0), "
                "the license under which the Perseus Digital Library releases its TEI text "
                "corpora and lexica (cf. PerseusDL/canonical-greekLit and PerseusDL/lexica, "
                "both CC BY-SA 4.0). The 1924 text is public domain; the TEI encoding and "
                "Helma Dik's corrections are the licensed derived scholarly layer."),
            "share_alike": (
                "CC BY-SA 4.0 requires attribution (Perseus Digital Library / Tufts "
                "University; ed. Gregory Crane; corrections Helma Dik; ATLAS structuring by "
                "the Scaife-Viewer Beyond Translation project) and share-alike on "
                "derivatives. This is compatible with COG's own CC BY-SA 4.0 license."),
            "derived_dataset": "CC BY-SA 4.0 (matching the corpus).",
        },
        "citation_scheme": {
            "cts_urns": "Each citation carries its canonical CTS URN "
                        "(urn:cts:greekLit:tlg0012.tlg001.perseus-grc2:BOOK.LINE for the "
                        "Iliad, tlg0012.tlg002 for the Odyssey).",
            "derived": "Alongside each citation we add {corpus: il|od, book, line} parsed "
                       "from the CTS URN, matching the cunliffe-appendix citation format.",
        },
        "structure": {
            "entry": "headword (Greek verbatim, digamma/metrical marks preserved), "
                     "headword_raw (with any leading † / * marker), dagger/asterisk flags, "
                     "content_html + content_text (inflection / etymology / cross-references "
                     "as encoded by Perseus), senses[], source_urn.",
            "sense": "label, definition, citations[], optional subsenses[] (nested to depth "
                     f"{max_depth}), source_urn.",
            "marker_note": "Cunliffe's leading † (word attested only in inflected forms) and "
                           "* (reconstructed / assumed form) are preserved as boolean flags "
                           "and in headword_raw, following Cunliffe's TEI; a later "
                           "Beyond-Translation extraction dropped these from the headword.",
        },
        "cross_check": (
            "An independent flattened plain-text transcription of the same 1924 lexicon "
            "exists at archive.org item 'CunliffeHomericLexicon' (file cunliffe.html); it is "
            "a markup-stripped export of this same Perseus text, useful only as a cross-check, "
            "not as a source."),
        "stats": stats,
        "files": {},
        "generated": now,
    }
    for fname in ["cunliffe_lexicon.json", "cunliffe_lexicon_index.json"]:
        p = OUT_DIR / fname
        manifest["files"][fname] = {"bytes": p.stat().st_size, "sha256": sha256_of(p)}

    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---- console report ----
    print(f"entries:                   {total}")
    print(f"  with headword:           {with_hw}")
    print(f"  with senses:             {with_senses}")
    print(f"  with content block:      {with_content}")
    print(f"  dagger / asterisk:       {dagger_n} / {asterisk_n}")
    print(f"senses (incl. subsenses):  {sense_count}  (max depth {max_depth})")
    print(f"citations total:           {cit_total}")
    print(f"  resolved to book+line:   {cit_resolved}  ({cit_resolved/cit_total:.2%})")
    print(f"  Iliad / Odyssey:         {il} / {od}")
    print(f"wrote -> {OUT_DIR}")


if __name__ == "__main__":
    main()
