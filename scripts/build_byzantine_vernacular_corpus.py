"""Import the Byzantine vernacular texts (merged in from the now-deprecated
byzantine-vernacular-corpus) as the `byzantine_vernacular` source of the open corpus.

These are open (PD / CC BY-SA) plain-text vernacular verse/prose with no TLG/CTS
id, so they key in a cog-native CTS namespace (urn:cts:cogGreek:cogByz.<stem>)
and locus by line number, parallel to how the non-TLG First1K works key. Reads
sources/byzantine/ (vendored, committed) and writes:

  data/corpus/cogByz.<stem>.jsonl   one record per content line:
                                    {urn, edition, locus, source, license, text}
  data/corpus_editions.json         merged: adds the byzantine_vernacular works (winning edition)
  data/byzantine_vernacular_works.json   per-work metadata for the registry build

    python scripts/build_byzantine_vernacular_corpus.py

Line cleaning (drop editor metadata, fix Latin homoglyphs) mirrors the dilemma
extract_byzantine heuristics so the two stay consistent.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources" / "byzantine"
CORPUS = REPO / "data" / "corpus"
CE = REPO / "data" / "corpus_editions.json"
BYZ_WORKS = REPO / "data" / "byzantine_vernacular_works.json"

_GK_LO, _GK_HI = "Ͱ", "Ͽ"
_PO_LO, _PO_HI = "ἀ", "῿"
_LATIN_HOMOGLYPHS = {
    "A": "Α", "B": "Β", "E": "Ε", "Z": "Ζ", "H": "Η", "I": "Ι",
    "K": "Κ", "M": "Μ", "N": "Ν", "O": "Ο", "P": "Ρ", "T": "Τ",
    "X": "Χ", "Y": "Υ",
}
# Greek header lines (not caught by the Latin>Greek metadata heuristic).
_HEADER_RE = re.compile(r"^\s*(Συγγραφέας|Τίτλος|Πηγή|Δείτε\s|Επιμέλεια|σχετικό λήμμα)")


def _is_greek(c: str) -> bool:
    return _GK_LO <= c <= _GK_HI or _PO_LO <= c <= _PO_HI


def _line_is_metadata(line: str) -> bool:
    """A line with more Latin than Greek letters is an editor note / citation
    block / page header (mirrors dilemma's extract_byzantine)."""
    greek = latin = 0
    for c in line:
        if "A" <= c <= "Z" or "a" <= c <= "z":
            latin += 1
        elif _is_greek(c):
            greek += 1
    return latin > greek and latin > 3


def _fix_homoglyphs(line: str) -> str:
    return "".join(_LATIN_HOMOGLYPHS.get(c, c) if (c in _LATIN_HOMOGLYPHS) else c
                   for c in line)


def _edition_id(license: str) -> str:
    lic = license.lower()
    if "kalonaros" in lic:
        return "kalonaros-1940"
    if "wikisource" in lic:
        return "wikisource"
    return "byz-text"


# Established authorship for the few non-anonymous works (the texts carry only
# a "Συγγραφέας:" line for Bergadis; the rest are famous attributions). stem ->
# (author slug, English display, Greek display).
AUTHORS = {
    "apokopos": ("bergadis", "Bergadis", "Μπεργαδής"),
    "apokopos_bergadi": ("bergadis", "Bergadis", "Μπεργαδής"),
    "erotokritos": ("vitsentzos-kornaros", "Vitsentzos Kornaros", "Βιτσέντζος Κορνάρος"),
    "ptochoprodromika": ("ptochoprodromos", "Ptochoprodromos", "Πτωχοπρόδρομος"),
}
_GENRE_WORDS = {
    "epic": "epic", "satire": "satire", "chronicle": "chronicle",
    "romance": "romance", "fable": "fable", "narrative": "narrative-poem",
    "folk": "folk-poetry", "beast": "beast-poetry",
}


def _century(date: str) -> int | None:
    """Composition century (AD, positive) from a manifest date string."""
    m = re.search(r"(\d{1,2})(?:th|st|nd|rd)?\s*century", date or "")
    if m:
        return int(m.group(1))
    y = re.search(r"\b(1[0-9]{3})\b", date or "")          # a year like 1600
    return (int(y.group(1)) // 100) + 1 if y else None


def _facets(entry: dict) -> list[list]:
    """(dimension, value) facets from the manifest register/date fields."""
    reg = (entry.get("register") or "").lower()
    f = [["register", "vernacular"]]
    for w, g in _GENRE_WORDS.items():
        if w in reg:
            f.append(["genre", g])
    if "cretan" in reg:
        f.append(["dialect", "cretan"])
    c = _century(entry.get("date", ""))
    if c:
        f.append(["century", c])
    return f


def _stem(filename: str) -> str:
    return filename[:-4] if filename.endswith(".txt") else filename


def build():
    manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
    CORPUS.mkdir(parents=True, exist_ok=True)
    ce = json.loads(CE.read_text(encoding="utf-8")) if CE.exists() else {}
    byz_works = []
    n_pass_total = 0

    for e in manifest:
        stem = _stem(e["file"])
        key = f"cogByz.{stem}"
        ed = _edition_id(e["license"])
        raw = (SRC / e["file"]).read_text(encoding="utf-8")
        records, n_tok, loc = [], 0, 0
        for line in raw.split("\n"):
            line = line.strip()
            if not line or _line_is_metadata(line) or _HEADER_RE.match(line):
                continue
            line = unicodedata.normalize("NFC", _fix_homoglyphs(line))
            if not any(_is_greek(c) for c in line):
                continue
            loc += 1
            n_tok += len([t for t in line.split() if any(_is_greek(c) for c in t)])
            records.append({"urn": key, "edition": ed, "locus": str(loc),
                            "source": "byzantine_vernacular", "license": e["license"], "text": line})
        if not records:
            continue
        out = CORPUS / f"{key}.jsonl"
        out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                               for r in records), encoding="utf-8")
        ce[key] = {"edition": ed, "license": e["license"], "source": "byzantine_vernacular",
                   "n_passages": len(records), "n_tokens": n_tok}
        # author: a "Συγγραφέας:" line in the text, else the curated map, else anon
        a_slug, a_en, a_el = AUTHORS.get(stem, ("anonymous", "Anonymous", ""))
        m = re.search(r"Συγγραφέας:\s*(.+)", raw)
        if m and stem not in AUTHORS:
            a_el = m.group(1).strip()
        byz_works.append({
            "key": key, "title": e["title"], "title_el": e.get("title_el", ""),
            "author_slug": a_slug, "author_name": a_en or a_el,
            "edition": ed, "license": e["license"], "scheme": "line",
            "facets": _facets(e),
        })
        n_pass_total += len(records)

    CE.write_text(json.dumps(ce, ensure_ascii=False, indent=0), encoding="utf-8")
    BYZ_WORKS.write_text(json.dumps(byz_works, ensure_ascii=False, indent=1),
                         encoding="utf-8")
    print(f"byzantine_vernacular: {len(byz_works)} works, {n_pass_total} passages "
          f"-> data/corpus/cogByz.*.jsonl, data/byzantine_vernacular_works.json")


if __name__ == "__main__":
    build()
