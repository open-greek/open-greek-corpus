#!/usr/bin/env python3
"""Resolve the DFHG ingest's held-back "specials" (data/dfhg_mapping.json).

ingest_dfhg.py held back author files whose author looked TEI-served (a
parallel DFHG work would duplicate content). The 2026-07-09 content
investigation (session e0a83cbd) verdicted each one; this script applies the
verdicts. Evidence per case:

PRIMARY ingests (content measured absent from the served corpus):

  DIODORUS_SICULUS.xml (24.6k Greek chars, 35 Constantinian De insidiis
    excerpts). Served Diodorus = books 1-5 + 11-20 only (perseus,
    diodorus-siculus.bibliotheca-historica-lib-1-20); the excerpts are from
    the FRAGMENTARY books 6-8 and 30-40, none served (probes for distinctive
    passages - Bellerophon, Catiline - hit nothing). Split at the TLG work
    boundary (canon tlg0060: tlg001 = lib 1-20, tlg003 = lib 21-40):
      books 30-40 -> diodorus-siculus.fragmenta-lib-21-40  (crosswalk
                     tlg0060.tlg003, canon-clean and unclaimed)
      books 6-8   -> diodorus-siculus.fragmenta-lib-6-8    (slug-only: TLG
                     folds these into tlg001, which the extant-books work
                     rightly holds)
    Known cross-attribution: 9/35 excerpts also appear inside the FHG-II OCR
    remainder works (demochares.fhg2, clearchus-philosophy.fragmenta) whose
    scan covered the De insidiis prolegomena pages; DFHG's Roman-numeral page
    fields kept the page-anchored shed from reaching them. Follow-up shed
    candidate, not a blocker.

  ANTIPATER.xml / DEMADES.xml / DINARCHUS.xml / XENOCRATES.xml (vol 4; 70 /
    126 / 956 / 127 Greek chars) -> <author>.fragmenta-fhg, slug-only.
    All four are HOMONYM collisions, not duplicates: the served TEI works
    belong to a different person (Antipater of Tarsus the Stoic vs the
    historian of Rhodes; the orator Demades vs a mythographic scholion; the
    orator Dinarchus vs the poet/mythographer - Demetrius Magnes ap. Dion.
    Hal. De Dinarcho 1 lists four Deinarchoi; Xenocrates of Chalcedon vs the
    chronicler). Probes: none of the fragments appear under the served
    slugs. No canon author exists for any of the four Mueller persons, so no
    urn is assigned (never fabricate).

SECONDARY ingests (same author as a served open-TEI fragment collection, so
they must not become a parallel primary; but their unique text is preserved
as rank=secondary in data/corpus_secondary/):

  HECATAEUS_ABDERITA.xml (14.1k Greek chars) vs first1k
    hecataeus-abderita.fragmenta-2 (tlg1390.tlg004): only ~13% verbatim
    overlap; the big Aegyptiaca excerpts (Diod. 1.46, 40.3/Photius) are not
    served under any Hecataeus slug (40.3 is served NOWHERE). Kept secondary
    pending a merge/promotion decision.
  EPIMENIDES.xml (700 Greek chars) vs first1k epimenides.fragmenta-2: same
    person (Epimenides of Crete), ~2/7 fragments verbatim-served, the
    genealogical scholia largely unserved. Secondary, same reasoning.
  DIONYSIUS_BYZANTIUS.xml (3.6k Greek chars, resolved 2026-07-09) vs first1k
    dionysius-byzantius.per-bosporum-navigatio: the served TEI is a proem-only
    stub (1 passage, 1,055 Greek chars), and the two FHG V fragments (the
    closing part of the Anaplus Bospori from BM cod. add. 19391, first ed.
    Yates, plus the stone-cow epigram) measure 0.021 / 0.000 word-bigram
    containment in it - complementary, not duplicate. Ingested as
    dionysius-byzantius.fragmenta-fhg, rank=secondary (same author as a
    served open-TEI work, Hecataeus Abd. precedent).

Verified served, no action (documented here for the record):
  MENECRATES_XANTHIUS.xml -> already fully served at
    menecrates-xanthius.fragmenta (4/4 fragments verbatim, carve slug).
  DAMON.xml / DAMON(1).xml -> the identical single fragment (Athen. 10.442c)
    is served twice, at damon.fragmenta and damon-history.fragmentum (both
    dfhg) - a duplicate worth a later dedup, nothing missing.

Record format matches ingest_dfhg.records_for (urn/edition/locus/source/
license/text + page/work/witness/dfhg_flag); Diodorus rows also carry the
"book" label ("6", "7", "8", "30-40") parsed from the Greek numeral heading.
Never overwrites: an existing target file aborts that work. After --write,
run reconcile_corpus_editions.py.

  python3 scripts/ingest_dfhg_specials.py            # dry-run
  python3 scripts/ingest_dfhg_specials.py --write
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import lxml.etree as ET

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources" / "dfhg"
CORPUS = REPO / "data" / "corpus"
SECONDARY = REPO / "data" / "corpus_secondary"
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
TSV_PATH = REPO / "data" / "tlg_crosswalk.tsv"

_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")
_ELISION = re.compile(" [̓᾿]")

GREEK_NUM = {"Ϛ": "6", "Ζ": "7", "Η": "8"}       # the units seen in this file


def clean_text(raw: str) -> str:
    t = unicodedata.normalize("NFC", " ".join(raw.split()))
    return _ELISION.sub("’", t)


def parse_book(label: str) -> str:
    """'ΕΚ ΒΙΒΛ. Ϛʹ' -> '6'; 'ΕΚ ΒΙΒΛ. Λʹ-Μʹ' -> '30-40'."""
    if "Λ" in label and "Μ" in label:
        return "30-40"
    for gl, arab in GREEK_NUM.items():
        if gl in label:
            return arab
    return ""


def parse_file(rel: str, vol: int) -> list[dict]:
    parser = ET.XMLParser(recover=True)
    root = ET.parse(str(SRC / rel), parser).getroot()
    frags = []
    for el in root:
        if el.tag not in ("extant_text", "fragment"):
            continue
        cite = el.get("cite_urn") or ""
        no = cite.rsplit(":", 1)[-1] if ":" in cite else str(len(frags) + 1)
        fld = {c.tag: (c.text or "").strip() for c in el}
        page = fld.get("page", "")
        frags.append({"no": no, "vol": vol,
                      "page": int(page) if page.isdigit() else None,
                      "work": fld.get("work", ""),
                      "witness": fld.get("witness", ""),
                      "book": fld.get("book", ""),
                      "text": clean_text(fld.get("text", ""))})
    return frags


def records(frags: list[dict], slug: str, with_book: bool = False) -> list[dict]:
    recs = []
    for f in frags:
        if not _GK.search(f["text"]):
            continue
        r = {"urn": slug, "edition": "dfhg", "locus": f"{f['vol']}.{f['no']}",
             "source": "dfhg", "license": "CC-BY-SA-4.0", "text": f["text"]}
        if f["page"] is not None:
            r["page"] = f["page"]
        if f["work"]:
            r["work"] = f["work"]
        if f["witness"]:
            r["witness"] = f["witness"]
        if with_book and parse_book(f["book"]):
            r["book"] = parse_book(f["book"])
        if "(??)" in f["text"]:
            r["dfhg_flag"] = True
        recs.append(r)
    return recs


SEC_REASON = {
    "hecataeus-abderita.fragmenta-fhg": (
        "parallel FHG collection of the first1k-served hecataeus-abderita."
        "fragmenta-2 (tlg1390.tlg004); ~13% verbatim overlap measured "
        "2026-07-09, kept secondary pending merge/promotion"),
    "epimenides.fragmenta-fhg": (
        "parallel FHG collection of the first1k-served epimenides."
        "fragmenta-2 (same Epimenides of Crete); ~2/7 fragments already "
        "verbatim-served, kept secondary pending merge/promotion"),
    "dionysius-byzantius.fragmenta-fhg": (
        "complementary FHG V fragments (Anaplus Bospori finis e cod. Mus. "
        "Brit. add. 19391, ed. Yates, + the stone-cow epigram) of the "
        "first1k-served dionysius-byzantius.per-bosporum-navigatio, which "
        "is a proem-only stub (1,055 gk chars); 0% bigram overlap measured "
        "2026-07-09, kept secondary pending merge/promotion"),
}


def gk_count(recs: list[dict]) -> int:
    return sum(len(_GK.findall(r["text"])) for r in recs)


def write_file(path: Path, recs: list[dict]) -> bool:
    if path.exists():
        print(f"  ABORT-SKIP {path.name}: file exists", file=sys.stderr)
        return False
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                            for r in recs), encoding="utf-8")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    dry = not args.write

    jobs_primary: list[tuple[str, list[dict]]] = []

    dio = parse_file("volume_2/data/xml/DIODORUS_SICULUS.xml", 2)
    late = [f for f in dio if parse_book(f["book"]) == "30-40"]
    early = [f for f in dio if parse_book(f["book"]) in ("6", "7", "8")]
    other = [f for f in dio if f not in late and f not in early]
    if other:
        sys.exit(f"ABORT: {len(other)} Diodorus fragments with unrecognized "
                 f"book labels: {[f['book'] for f in other]}")
    jobs_primary.append(("diodorus-siculus.fragmenta-lib-21-40",
                         records(late, "diodorus-siculus.fragmenta-lib-21-40",
                                 with_book=True)))
    jobs_primary.append(("diodorus-siculus.fragmenta-lib-6-8",
                         records(early, "diodorus-siculus.fragmenta-lib-6-8",
                                 with_book=True)))

    for xml, slug in [("ANTIPATER", "antipater.fragmenta-fhg"),
                      ("DEMADES", "demades.fragmenta-fhg"),
                      ("DINARCHUS", "dinarchus.fragmenta-fhg"),
                      ("XENOCRATES", "xenocrates.fragmenta-fhg")]:
        frags = parse_file(f"volume_4/data/xml/{xml}.xml", 4)
        jobs_primary.append((slug, records(frags, slug)))

    jobs_secondary: list[tuple[str, list[dict]]] = []
    for rel, vol, slug in [
            ("volume_2/data/xml/HECATAEUS_ABDERITA.xml", 2,
             "hecataeus-abderita.fragmenta-fhg"),
            ("volume_4/data/xml/EPIMENIDES.xml", 4,
             "epimenides.fragmenta-fhg"),
            ("volume_5_1/data/xml/DIONYSIUS_BYZANTIUS.xml", 5,
             "dionysius-byzantius.fragmenta-fhg")]:
        frags = parse_file(rel, vol)
        recs = records(frags, slug)
        for r in recs:
            r["rank"] = "secondary"
            r["secondary_reason"] = SEC_REASON[slug]
        jobs_secondary.append((slug, recs))

    for slug, recs in jobs_primary:
        print(f"  primary   {slug}: {len(recs)} passages, {gk_count(recs):,} gk")
    for slug, recs in jobs_secondary:
        print(f"  secondary {slug}: {len(recs)} passages, {gk_count(recs):,} gk")
    if dry:
        print("(dry-run: nothing written; use --write)")
        return

    n = 0
    for slug, recs in jobs_primary:
        if recs and write_file(CORPUS / f"{slug}.jsonl", recs):
            n += 1
    SECONDARY.mkdir(parents=True, exist_ok=True)
    for slug, recs in jobs_secondary:
        if recs and write_file(SECONDARY / f"{slug}.jsonl", recs):
            n += 1

    # crosswalk: the lib-21-40 work is canon-clean (tlg0060.tlg003, Walton's
    # Bibliotheca historica lib. 21-40); never overwrite an existing claim.
    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    slug = "diodorus-siculus.fragmenta-lib-21-40"
    if (CORPUS / f"{slug}.jsonl").exists() and slug not in cw and \
            not any(d.get("tlg") == "tlg0060.tlg003" for d in cw.values()):
        cw[slug] = {"cts": "urn:cts:greekLit:tlg0060.tlg003",
                    "tlg": "tlg0060.tlg003",
                    "author_slug": "diodorus-siculus",
                    "title": "Bibliotheca historica (lib. 21-40)"}
        CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0),
                           encoding="utf-8")
        with TSV_PATH.open("w", encoding="utf-8") as f:
            f.write("slug\tcts_urn\ttlg\n")
            for s, d in sorted(cw.items()):
                if d.get("cts"):        # pta-alias-only entries have no urn
                    f.write(f"{s}\t{d['cts']}\t{d['tlg']}\n")
        print(f"  crosswalk: {slug} -> tlg0060.tlg003")

    print(f"wrote {n} works; now run: python3 scripts/reconcile_corpus_editions.py")


if __name__ == "__main__":
    main()
