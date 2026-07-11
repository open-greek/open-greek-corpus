#!/usr/bin/env python3
"""Roll up the form-frequency lexicon (the "yardstick") from the WHOLE ingested
open corpus in data/corpus/*.jsonl, not from the TEI alone.

The yardstick must be defined by cog's own corpus, and must grow automatically
every time a TLG-only work is replaced by an open/PD source. So the lexicon is a
rollup over every ingested passage in data/corpus/*.jsonl: the open TEI editions
(written by build_corpus_loci.py), the Byzantine vernacular texts
(build_byzantine_vernacular_corpus.py), and the PD/CC ingests that fill the gaps
(calfa-co Patrologia Graeca,
byzantium.gr historians). Each ingester writes its passages to data/corpus and
merges into corpus_editions.json; this script is the single lexicon builder over
the union, so a new ingest flows into the yardstick with no extra step.

The TEI-parsing helpers below (body_text, detect_license, the drop set, the Greek
regex) remain the shared library that build_corpus_loci.py imports for ingest;
only the lexicon rollup moved here off the TEI and onto the ingested corpus.

Outputs (under data/):
  public_lexicon.tsv     form<TAB>count over every ingested passage
  coverage.json          per work urn: source, license, tokens, passages

  python build_public_corpus.py      # run AFTER the ingesters populate data/corpus
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import lxml.etree as ET

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources"
DATA = REPO / "data"
CORPUS = DATA / "corpus"
TEI_NS = "http://www.tei-c.org/ns/1.0"
_GK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")
# elements whose text is NOT the running edition text
DROP = {f"{{{TEI_NS}}}{t}" for t in ("note", "rdg", "bibl", "ref", "title",
                                     "speaker", "label", "head", "gap", "del")}
# The work part allows a single letter suffix: First1K splits some works into
# lettered sub-editions (tlg5034.tlg001a-d = Drachmann's Pindar scholia per
# ode-book), which the digits-only pattern silently skipped - 3.2MB of scholia
# TEI sat unserved because the filename never matched.
_WORK_RE = re.compile(r"((?:tlg|pta)\d+)\.((?:tlg|pta)\d+[a-z]?)\.")

# Per-source repo default license (all three TEI repos are CC BY-SA 4.0). Inline
# <licence> overrides this. NC licenses are EXCLUDED from the corpus (public-
# path: no non-commercial restriction); their works fall to the PD/OCR track.
# pta has NO repo default: its licensing is per file (147 BY-SA / 65 BY / 1
# BY-NC-SA), so a pta file without an inline <licence> stays "unknown" (excluded).
REPO_DEFAULT_LICENSE = {"first1k": "CC-BY-SA-4.0", "perseus": "CC-BY-SA-4.0",
                        "galenus_verbatim": "CC-BY-SA-4.0"}

_SIC = f"{{{TEI_NS}}}sic"
_CHOICE = f"{{{TEI_NS}}}choice"
_CORR = f"{{{TEI_NS}}}corr"


def is_dropped(el) -> bool:
    """True for elements whose text is NOT the running edition text: the DROP
    set, plus a <sic> whose parent <choice> also carries a <corr> (emit only the
    corrected reading, never both). A standalone <sic> outside such a pair IS
    the text (it just flags a printed anomaly) and is kept."""
    if el.tag in DROP:
        return True
    if el.tag == _SIC:
        parent = el.getparent()
        return (parent is not None and parent.tag == _CHOICE
                and parent.find(_CORR) is not None)
    return False


def detect_license(root, source: str) -> str:
    """License id for a TEI edition: inline <licence> target/text if present,
    else the source repo default."""
    for lic in root.iter(f"{{{TEI_NS}}}licence"):
        blob = ((lic.get("target") or "") + " " + "".join(lic.itertext())).lower()
        if "by-nc" in blob or "noncommercial" in blob:
            return "CC-BY-NC-SA"
        if "by-sa" in blob or "sharealike" in blob:
            return "CC-BY-SA-4.0"
        if "publicdomain" in blob or "cc0" in blob:
            return "CC0/PD"
        if "licenses/by/" in blob or "/by/4" in blob:
            return "CC-BY-4.0"
    return REPO_DEFAULT_LICENSE.get(source, "unknown")


def is_acceptable(lic: str) -> bool:
    """Exclude non-commercial (and unknown) licenses from the public corpus."""
    return "NC" not in lic and lic != "unknown"


def body_text(root) -> str:
    """Greek running text of a TEI edition: <body>, minus header/notes/variants."""
    body = root.find(f".//{{{TEI_NS}}}text/{{{TEI_NS}}}body")
    if body is None:
        return ""
    parts = []

    def walk(el):
        if is_dropped(el):
            if el.tail:
                parts.append(el.tail)
            return
        if el.text:
            parts.append(el.text)
        for ch in el:
            walk(ch)
        if el.tail:
            parts.append(el.tail)

    walk(body)
    return " ".join(parts)


def main() -> None:
    files = sorted(CORPUS.glob("*.jsonl"))
    if not files:
        sys.exit(f"no ingested corpus in {CORPUS} - run the ingesters first "
                 "(build_corpus_loci.py, build_byzantine_vernacular_corpus.py, ...)")
    print(f"rolling up {len(files)} ingested works in data/corpus/ ...",
          file=sys.stderr)

    lex: Counter[str] = Counter()
    coverage: dict[str, dict] = {}      # work urn -> {source, license, tokens, passages}
    for i, fp in enumerate(files):
        with fp.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                toks = [unicodedata.normalize("NFC", t)
                        for t in _GK.findall(rec.get("text", ""))]
                lex.update(toks)
                key = rec.get("urn") or fp.stem
                cov = coverage.setdefault(
                    key, {"source": rec.get("source"),
                          "license": rec.get("license"), "tokens": 0, "passages": 0})
                cov["tokens"] += len(toks)
                cov["passages"] += 1
        if i % 300 == 0:
            print(f"  {i}/{len(files)}", file=sys.stderr)

    DATA.mkdir(exist_ok=True)
    with (DATA / "public_lexicon.tsv").open("w", encoding="utf-8") as f:
        for form, n in lex.most_common():
            f.write(f"{form}\t{n}\n")
    (DATA / "coverage.json").write_text(
        json.dumps(coverage, ensure_ascii=False, indent=0, sort_keys=True))

    total_tokens = sum(v["tokens"] for v in coverage.values())
    print(f"\nworks: {len(coverage)} | total Greek tokens: {total_tokens:,}",
          file=sys.stderr)
    print(f"distinct forms: {len(lex):,}", file=sys.stderr)
    bysource = defaultdict(int)
    for v in coverage.values():
        bysource[v["source"]] += 1
    print(f"works by source: {dict(bysource)}", file=sys.stderr)
    print("wrote data/public_lexicon.tsv, coverage.json", file=sys.stderr)


if __name__ == "__main__":
    main()
