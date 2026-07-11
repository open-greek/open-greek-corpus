#!/usr/bin/env python3
"""Split the theodosius canons catch-all into its two canonical works.

theodosius.canones-isagogici-de-flexione-nominum (crosswalk tlg2020.tlg001)
served the WHOLE Theodosius canons range of Hilgard, Grammatici Graeci IV.1
(scan choeroboscus_hilgard_gg4, pages 0014-0110 = printed 3-99). That range
is two canonical works (TLG canon, tlge-tools data/tlg_canon.json):

  tlg2020.001 Canones isagogici de flexione nominum   (7,080 canon words)
  tlg2020.002 Canones isagogici de flexione verborum (10,673 canon words)

The printed boundary is clean at a page break, verified from the corpus rows:

  scan 0053 (printed 42) ends the nominal canons with the end-title
    "[Tel]os ton onomaton" (rows 0053.19/.33/.45 carry it and its apparatus);
  scan 0054 (printed 43) opens the verbal canons with the section head
    "THEODOSIOU GRAMM[ATIKOU] / eisagogikoi kanones peri [kliseos] /
    peri kliseos rhematon." and first canon "Enika. Typto..." (rows
    0054.1/.2/.8/.9/.3). No page carries text of both works.

This script:
  1. keeps the nominal zone (scan 0014-0053, printed 3-42) under the
     existing slug/urn (tlg2020.tlg001), rows byte-unchanged;
  2. moves the verbal zone (scan 0054-0110, printed 43-99) to a new work
     theodosius.canones-isagogici-de-flexione-verborum - the ONLY per-row
     change is the urn field; locus page stems keep their original scan
     identity (stable key into OCR provenance and corrections logs);
  3. adds the tlg2020.tlg002 crosswalk entry (canon-verified, not minted),
     notes the split on both entries, regenerates tlg_crosswalk.tsv;
  4. refreshes the ocr_works.json row for the nominal slug and adds a row
     for the verbal slug (diels_resplit_followups.py precedent);
  5. checks Greek-character conservation is exact (pure row reassignment)
     and that per-zone Greek token counts are sane against the canon word
     counts (verbal is the larger work in both).

Idempotent: rerunning after --write reports nothing to do. Derived files
(corpus_editions.json, coverage.json, registry, caches) are rebuilt by
reconcile_corpus_editions.py and the usual builders, not here.

  python3 scripts/rescope_theodosius_canones.py                # dry-run
  python3 scripts/rescope_theodosius_canones.py --write
  python3 scripts/rescope_theodosius_canones.py --audit out.json  # + backups
  then: python3 scripts/reconcile_corpus_editions.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
TSV_PATH = REPO / "data" / "tlg_crosswalk.tsv"
OW_PATH = REPO / "data" / "ocr_works.json"

NOM_SLUG = "theodosius.canones-isagogici-de-flexione-nominum"
VER_SLUG = "theodosius.canones-isagogici-de-flexione-verborum"
NOM_TLG = "tlg2020.tlg001"
VER_TLG = "tlg2020.tlg002"
VER_TITLE = "Canones isagogici de flexione verborum"

SCAN = "choeroboscus_hilgard_gg4"
FIRST_PAGE = 14          # scan page of printed p. 3 (nominal canons head)
FIRST_VERBAL_PAGE = 54   # scan page of printed p. 43 (verbal canons head)
LAST_PAGE = 110          # scan page of printed p. 99 (end of the canons)

# TLG canon word counts (tlge-tools data/tlg_canon.json, tlg2020 works
# 001/002, ed. Hilgard GG 4.1). OCR zones include Hilgard's apparatus and
# testimonia, so zone Greek tokens exceed these; ordering must match.
CANON_WORDS = {NOM_TLG: 7080, VER_TLG: 10673}

SPLIT_DATE = "2026-07-10"
_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")
_LOCUS = re.compile(rf"^{SCAN}_(\d{{4}})\.\d+$")


def page_of(row: dict) -> int:
    m = _LOCUS.match(row["locus"])
    if not m:
        sys.exit(f"ABORT: unexpected locus {row['locus']!r}")
    return int(m.group(1))


def zone_stats(rows: list[dict]) -> dict:
    return {
        "rows": len(rows),
        "pages": len({r["locus"].rsplit(".", 1)[0] for r in rows}),
        "greek_tokens": sum(1 for r in rows for t in r["text"].split()
                            if _GK.search(t)),
        "greek_chars": sum(len(_GK.findall(r["text"])) for r in rows),
    }


def check_boundary(nom: list[dict], ver: list[dict]) -> dict:
    """Content assertions: fail loudly if the data no longer matches the
    printed boundary this split encodes. Returns the evidence rows."""
    def texts(rows, page):
        return [r for r in rows if page_of(r) == page]

    ev = {}
    head = texts(nom, FIRST_PAGE)
    if not any("ΘΕΟΔΟΣΙΟΥ" in r["text"] for r in head):
        sys.exit(f"ABORT: page {FIRST_PAGE:04d} lacks the nominal-canons "
                 f"head (ΘΕΟΔΟΣΙΟΥ ...)")
    ev["nominal_head"] = [r["locus"] + " | " + r["text"][:80]
                          for r in head if "ΘΕΟΔΟΣΙΟΥ" in r["text"]
                          or "ὀνομάτων" in r["text"]][:3]

    tail = texts(nom, FIRST_VERBAL_PAGE - 1)
    if not any("τῶν ὀνομάτων" in r["text"] for r in tail):
        sys.exit(f"ABORT: page {FIRST_VERBAL_PAGE - 1:04d} lacks the "
                 f"nominal end-title (Τέλος τῶν ὀνομάτων)")
    ev["nominal_end_title"] = [r["locus"] + " | " + r["text"][:80]
                               for r in tail if "τῶν ὀνομάτων" in r["text"]][:3]

    vhead = texts(ver, FIRST_VERBAL_PAGE)
    if not any("ῥημάτων" in r["text"] for r in vhead) or \
            not any("Τύπτω" in r["text"] for r in vhead):
        sys.exit(f"ABORT: page {FIRST_VERBAL_PAGE:04d} lacks the "
                 f"verbal-canons head (περὶ κλίσεως ῥημάτων / Τύπτω)")
    ev["verbal_head"] = [r["locus"] + " | " + r["text"][:80]
                         for r in vhead if "ῥημάτων" in r["text"]
                         or "Τύπτω" in r["text"] or "ΘΕΟΔΟΣΙΟΥ" in r["text"]][:4]
    return ev


def corpus_stats_for_ocr_works(rows: list[dict]) -> dict:
    eds = Counter(r.get("edition") for r in rows)
    return {
        "edition": eds.most_common(1)[0][0],
        "pages": len({r["locus"].rsplit(".", 1)[0] for r in rows}),
        "n_passages": len(rows),
        "n_tokens": sum(1 for r in rows for t in r["text"].split()
                        if _GK.search(t)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--audit", metavar="PATH",
                    help="write an audit JSON (split metadata + full row "
                         "backups of the pre-split file) to PATH")
    args = ap.parse_args()

    nom_fp = CORPUS / f"{NOM_SLUG}.jsonl"
    ver_fp = CORPUS / f"{VER_SLUG}.jsonl"

    lines = [l for l in nom_fp.read_text(encoding="utf-8").splitlines()
             if l.strip()]
    rows = [json.loads(l) for l in lines]
    pages = sorted({page_of(r) for r in rows})

    if ver_fp.exists() and pages and pages[-1] < FIRST_VERBAL_PAGE:
        print(f"already applied: {ver_fp.name} exists and {nom_fp.name} "
              f"holds only pages {pages[0]:04d}-{pages[-1]:04d}")
        return
    if ver_fp.exists():
        sys.exit(f"ABORT: {ver_fp.name} exists but {nom_fp.name} still has "
                 f"verbal pages - inconsistent state, resolve manually")
    if pages[0] != FIRST_PAGE or pages[-1] != LAST_PAGE:
        sys.exit(f"ABORT: page range {pages[0]:04d}-{pages[-1]:04d}, "
                 f"expected {FIRST_PAGE:04d}-{LAST_PAGE:04d}")

    nom = [r for r in rows if page_of(r) < FIRST_VERBAL_PAGE]
    ver = [r for r in rows if page_of(r) >= FIRST_VERBAL_PAGE]
    assert len(nom) + len(ver) == len(rows)

    evidence = check_boundary(nom, ver)
    st_nom, st_ver = zone_stats(nom), zone_stats(ver)
    st_all = zone_stats(rows)

    # conservation: pure row reassignment, exact by construction; verify.
    kept = st_nom["greek_chars"] + st_ver["greek_chars"]
    if kept != st_all["greek_chars"]:
        sys.exit(f"ABORT: Greek chars {kept} != {st_all['greek_chars']}")

    # canon sanity: verbal is the larger work in the canon and must be in
    # the OCR zones too; OCR (text + apparatus) exceeds canon (text only).
    if not (st_ver["greek_tokens"] > st_nom["greek_tokens"]):
        sys.exit("ABORT: verbal zone smaller than nominal, contradicts canon")
    for tlg, st in ((NOM_TLG, st_nom), (VER_TLG, st_ver)):
        if st["greek_tokens"] < CANON_WORDS[tlg]:
            sys.exit(f"ABORT: {tlg} zone has {st['greek_tokens']} Greek "
                     f"tokens < canon {CANON_WORDS[tlg]} words")

    print(f"split {NOM_SLUG} at scan {FIRST_VERBAL_PAGE:04d} "
          f"(printed 43, verbal-canons head):")
    for name, st, tlg in (("nominal (keeps slug)", st_nom, NOM_TLG),
                          ("verbal  (new slug) ", st_ver, VER_TLG)):
        print(f"  {name}: {st['rows']} rows / {st['pages']} pages / "
              f"{st['greek_tokens']:,} Greek tokens / "
              f"{st['greek_chars']:,} Greek chars "
              f"-> {tlg} (canon {CANON_WORDS[tlg]:,} words)")
    print(f"  Greek char conservation: {kept:,} / {st_all['greek_chars']:,} "
          f"= 100.0000%")
    for k, v in evidence.items():
        print(f"  evidence {k}:")
        for line in v:
            print(f"    {line}")

    if args.audit:
        audit = {
            "date": SPLIT_DATE,
            "script": "scripts/rescope_theodosius_canones.py",
            "scan": SCAN,
            "boundary": {
                "first_verbal_scan_page": f"{FIRST_VERBAL_PAGE:04d}",
                "printed": "nominal 3-42 (scan 0014-0053), "
                           "verbal 43-99 (scan 0054-0110)",
                "evidence": evidence,
            },
            "works": {
                NOM_SLUG: dict(st_nom, tlg=NOM_TLG,
                               canon_words=CANON_WORDS[NOM_TLG]),
                VER_SLUG: dict(st_ver, tlg=VER_TLG,
                               canon_words=CANON_WORDS[VER_TLG]),
            },
            "original_file": nom_fp.name,
            "original_rows": [
                {"line": i, "assigned_to":
                    NOM_SLUG if page_of(r) < FIRST_VERBAL_PAGE else VER_SLUG,
                 "row": r}
                for i, r in enumerate(rows)],
            "written_at": _dt.datetime.now(_dt.timezone.utc)
                             .isoformat(timespec="seconds"),
        }
        Path(args.audit).write_text(
            json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"audit written: {args.audit} ({len(rows)} row backups)")

    if not args.write:
        print("DRY RUN - nothing written (use --write)")
        return

    # 1+2. corpus files: nominal rows byte-unchanged; verbal rows get the
    # new urn (only field changed), original file order preserved per zone.
    for r in ver:
        r["urn"] = VER_SLUG
    ver_fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                              for r in ver), encoding="utf-8")
    nom_fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                              for r in nom), encoding="utf-8")

    # 3. crosswalk: canon-verified tlg2020.tlg002 entry + split notes.
    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    if cw.get(NOM_SLUG, {}).get("tlg") != NOM_TLG:
        sys.exit(f"ABORT: crosswalk {NOM_SLUG} is not {NOM_TLG}")
    claimed = [s for s, d in cw.items() if d.get("tlg") == VER_TLG]
    if claimed:
        sys.exit(f"ABORT: {VER_TLG} already claimed by {claimed}")
    cw[NOM_SLUG]["note"] = (
        f"nominal canons only (Hilgard GG 4.1 printed 3-42, scan "
        f"{SCAN} 0014-0053); verbal canons split out to {VER_SLUG} "
        f"({SPLIT_DATE})")
    cw[VER_SLUG] = {
        "cts": f"urn:cts:greekLit:{VER_TLG}",
        "tlg": VER_TLG,
        "author_slug": "theodosius",
        "title": VER_TITLE,
        "note": (f"split from {NOM_SLUG} ({SPLIT_DATE}): verbal canons, "
                 f"Hilgard GG 4.1 printed 43-99, scan {SCAN} 0054-0110; "
                 f"work id verified in the TLG canon"),
    }
    CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0),
                       encoding="utf-8")
    with TSV_PATH.open("w", encoding="utf-8") as f:
        f.write("slug\tcts_urn\ttlg\n")
        for s, d in sorted(cw.items()):
            if d.get("cts"):            # slug-only entries have no urn
                f.write(f"{s}\t{d['cts']}\t{d['tlg']}\n")

    # 4. ocr_works: refresh the nominal row, add the verbal row after it.
    ow = json.loads(OW_PATH.read_text(encoding="utf-8"))
    idx = [i for i, w in enumerate(ow) if w.get("urn") == NOM_SLUG]
    if len(idx) != 1:
        sys.exit(f"ABORT: {len(idx)} ocr_works rows for {NOM_SLUG}")
    i = idx[0]
    template = dict(ow[i])
    ow[i].update(corpus_stats_for_ocr_works(nom), date=SPLIT_DATE)
    ver_row = dict(template, urn=VER_SLUG)
    ver_row.update(corpus_stats_for_ocr_works(ver), date=SPLIT_DATE)
    ow.insert(i + 1, ver_row)
    OW_PATH.write_text(json.dumps(ow, ensure_ascii=False, indent=1),
                       encoding="utf-8")

    print(f"written: {nom_fp.name} ({len(nom)} rows), "
          f"{ver_fp.name} ({len(ver)} rows), crosswalk + tsv, ocr_works; "
          f"now run reconcile_corpus_editions.py")


if __name__ == "__main__":
    main()
