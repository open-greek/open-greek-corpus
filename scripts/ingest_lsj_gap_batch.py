#!/usr/bin/env python3
"""Serve three LSJ-gap works whose open text we already have but don't yet serve.

Closes the ingest half of the LSJ citation-coverage batch (the resolver half -
Sophocles scholia + Gorgias remaps - lives in lsjpre). Each work here is text we
already hold, just not served under the crosswalk slug work_in_cog() looks for:

  1. Porphyry, Sententiae ad intelligibilia ducentes  tlg2034.tlg008
     -> slug porphyrius.sententiae-ad-intelligibilia-ducentes
     Reconstructed from GLAUx xml/2034-008.xml (44 sententiae, ~7.7k tokens).
  2. Porphyry, De antro nympharum                     tlg2034.tlg004
     -> slug porphyrius.de-antro-nympharum
     Reconstructed from GLAUx xml/2034-004.xml (36 sections, ~4.9k tokens).
  3. Scholia in Pindarum (scholia vetera, Drachmann)   tlg5034.tlg001
     -> slug scholia-in-pindarum.scholia-in-pindarum-scholia-vetera
     The First1K text is ALREADY in data/corpus/ but orphaned as four tlg-named
     files (tlg5034.tlg001a..d.jsonl, Olympian/Pythian/Nemean/Isthmian) that the
     crosswalk (which expects the single .001 slug) never picked up. We CONSOLIDATE
     the four into the slug file, prefixing each locus with its book (O./P./N./I.)
     so the four books' loci never collide, and archive the orphans.

All three are added to data/non_tei_authoritative.json so build_corpus_loci.py
never overwrites them. Reversible: archived originals live in data/corpus_changes/;
delete the slug .jsonl and the keep-list entry to revert.

GLAUx method mirrors ingest_glaux_pollux.py (NFC surface forms in document order,
artificial + 'G?' tokens dropped, detok hugs punctuation). License: ancient text
PD; GLAUx corpus CC BY-SA 4.0. First1K Pindar scholia: CC BY-SA (Perseus).

  python3 scripts/ingest_lsj_gap_batch.py            # dry run + report
  python3 scripts/ingest_lsj_gap_batch.py --apply    # write the served files

After --apply run `make all` (build_corpus_loci skips these via the keep-list).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

COG = Path(__file__).resolve().parent.parent
CORPUS = COG / "data" / "corpus"
CHANGES = COG / "data" / "corpus_changes"
NON_TEI = COG / "data" / "non_tei_authoritative.json"

_GKW = re.compile(r"[Ͱ-Ͽἀ-῿]+")
GAP_FORM = "G?"
NO_SPACE_BEFORE = set(",.;·)")
NO_SPACE_AFTER = set("(")


def glaux_dir() -> Path:
    root = os.environ.get("GLAUX_DIR")
    return (Path(root) if root else Path.home() / "Documents" / "glaux")


def detok(forms: list[str]) -> str:
    pieces: list[str] = []
    suppress = False
    quote_open = False
    for i, tok in enumerate(forms):
        is_quote = tok == '"'
        opening = is_quote and not quote_open
        closing = is_quote and quote_open
        space = not (i == 0 or suppress or tok in NO_SPACE_BEFORE or closing)
        pieces.append((" " if space else "") + tok)
        suppress = tok in NO_SPACE_AFTER or opening
        if is_quote:
            quote_open = not quote_open
    return "".join(pieces)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_glaux(glaux_id: str, div_attr: str) -> "OrderedDict[str, list[str]]":
    """locus -> surface forms in document order, grouped by the given div attr.

    Asserts each locus occupies a single contiguous run (setdefault grouping would
    otherwise silently reorder a split section)."""
    path = glaux_dir() / "xml" / f"{glaux_id}.xml"
    if not path.exists():
        raise SystemExit(f"ABORT: GLAUx source missing: {path} (set GLAUX_DIR)")
    loci: "OrderedDict[str, list[str]]" = OrderedDict()
    order: list[str] = []
    last = None
    dropped = 0
    for _e, el in ET.iterparse(str(path), events=("end",)):
        if el.tag != "word":
            continue
        if el.get("artificial"):
            el.clear(); continue
        form = unicodedata.normalize("NFC", el.get("form") or "")
        loc = (el.get(div_attr) or "").strip()
        if not form or not loc:
            el.clear(); continue
        if form == GAP_FORM:
            dropped += 1; el.clear(); continue
        if loc != last:
            order.append(loc); last = loc
        loci.setdefault(loc, []).append(form)
        el.clear()
    seen = set()
    for k in order:
        if k in seen:
            raise SystemExit(f"ABORT: locus {k!r} non-contiguous in {glaux_id}; "
                             "running-text reconstruction unreliable - not writing")
        seen.add(k)
    return loci, dropped


def glaux_rows(glaux_id: str, div_attr: str) -> tuple[list[tuple[str, str]], int]:
    loci, dropped = load_glaux(glaux_id, div_attr)
    # numeric sort when loci are integers, else lexical
    def key(k):
        return (0, int(k)) if k.isdigit() else (1, k)
    rows = [(loc, detok(loci[loc])) for loc in sorted(loci, key=key)]
    return rows, dropped


def pindar_rows() -> tuple[list[tuple[str, str]], list[Path]]:
    """Consolidate the four orphan First1K Pindar-scholia files into one work,
    prefixing loci by book so O./P./N./I. never collide."""
    books = [("a", "O"), ("b", "P"), ("c", "N"), ("d", "I")]
    rows: list[tuple[str, str]] = []
    srcs: list[Path] = []
    for suffix, book in books:
        src = CORPUS / f"tlg5034.tlg001{suffix}.jsonl"
        if not src.exists():
            raise SystemExit(f"ABORT: expected orphan file missing: {src}")
        srcs.append(src)
        for line in src.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            loc = r.get("locus")
            txt = r.get("text", "")
            if loc is None or not txt.strip():
                continue
            rows.append((f"{book}.{loc}", txt))
    return rows, srcs


JOBS = [
    {"kind": "glaux", "slug": "porphyrius.sententiae-ad-intelligibilia-ducentes",
     "tlg": "tlg2034.tlg008", "cts": "urn:cts:greekLit:tlg2034.tlg008",
     "glaux_id": "2034-008", "div_attr": "div_sententia", "edition": "glaux-2034-008",
     "name": "Porphyry, Sententiae ad intelligibilia ducentes",
     "incipit_prefix": "πᾶν μὲν σῶμα ἐν τόπῳ",
     "license": "PD (ancient text); GLAUx corpus CC BY-SA 4.0"},
    {"kind": "glaux", "slug": "porphyrius.de-antro-nympharum",
     "tlg": "tlg2034.tlg004", "cts": "urn:cts:greekLit:tlg2034.tlg004",
     "glaux_id": "2034-004", "div_attr": "div_section", "edition": "glaux-2034-004",
     "name": "Porphyry, De antro nympharum",
     "incipit_prefix": "ὅτι ποτὲ Ὁμήρῳ αἰνίττεται",
     "license": "PD (ancient text); GLAUx corpus CC BY-SA 4.0"},
    {"kind": "pindar", "slug": "scholia-in-pindarum.scholia-in-pindarum-scholia-vetera",
     "tlg": "tlg5034.tlg001", "cts": "urn:cts:greekLit:tlg5034.tlg001",
     "edition": "perseus-grc1-consolidated",
     "name": "Scholia in Pindarum (scholia vetera, Drachmann)",
     "license": "PD (ancient text); First1KGreek/Perseus CC BY-SA 4.0"},
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write the served corpus files (default: dry run)")
    args = ap.parse_args()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    CHANGES.mkdir(parents=True, exist_ok=True)
    keep = json.loads(NON_TEI.read_text(encoding="utf-8")) if NON_TEI.exists() else {}

    for job in JOBS:
        slug = job["slug"]
        if job["kind"] == "glaux":
            rows, dropped = glaux_rows(job["glaux_id"], job["div_attr"])
            prov = {"source": "glaux", "glaux_id": job["glaux_id"],
                    "repo": "github.com/alekkeersmaekers/glaux",
                    "method": ("running text per locus from GLAUx <word> surface "
                               f"forms (NFC) grouped by {job['div_attr']}, numeric "
                               "order; artificial + 'G?' tokens dropped"),
                    "dropped_gap": dropped}
            incipit = rows[0][1]
            if not incipit.startswith(job["incipit_prefix"]):
                raise SystemExit(f"ABORT {slug}: incipit {incipit[:40]!r} != expected "
                                 f"{job['incipit_prefix']!r}")
            archived = []
        else:  # pindar consolidation
            rows, srcs = pindar_rows()
            prov = {"source": "first1k", "consolidated_from":
                    [s.name for s in srcs],
                    "method": ("four First1K Pindar-scholia work files "
                               "(Olympian/Pythian/Nemean/Isthmian) merged; loci "
                               "prefixed O./P./N./I. to keep books distinct")}
            archived = srcs

        ntok = sum(len(_GKW.findall(t)) for _l, t in rows)
        dst = CORPUS / f"{slug}.jsonl"
        print(f"{'' if args.apply else 'DRY '}{job['name']}")
        print(f"  -> {slug}.jsonl : {len(rows)} loci, {ntok:,} Greek tokens")
        print(f"     first {rows[0][0]}: {rows[0][1][:72]}")
        print(f"     last  {rows[-1][0]}: ...{rows[-1][1][-56:]}")
        if not args.apply:
            continue

        with dst.open("w", encoding="utf-8") as f:
            for locus, text in rows:
                f.write(json.dumps({
                    "urn": slug, "edition": job["edition"], "locus": locus,
                    "source": prov["source"], "license": job["license"],
                    "text": text, "provenance": prov,
                }, ensure_ascii=False) + "\n")
        print(f"     wrote {dst.relative_to(COG)}")

        # archive + remove orphan tlg-named files (Pindar) so they don't double-serve
        for src in archived:
            arch = CHANGES / f"{src.stem}.pre-consolidation.jsonl"
            arch.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            src.unlink()
            print(f"     archived + removed orphan {src.name} -> {arch.name}")

        keep[slug] = {
            "kept_source": prov["source"], "kept_edition": job["edition"],
            "reason": (f"{job['name']} ({ntok} Greek tokens) served from "
                       f"{prov['source']}; LSJ-gap ingest 2026-07-14."),
            "as_of": today,
        }
        audit = CHANGES / f"{slug}.lsj-gap-ingest.json"
        audit.write_text(json.dumps({
            "_meta": {"change": "serve LSJ-gap work", "work": slug,
                      "tlg": job["tlg"], "cts": job["cts"],
                      "applied_by": "scripts/ingest_lsj_gap_batch.py", "date": today,
                      "reversible": (f"delete data/corpus/{slug}.jsonl and the "
                                     f"{slug} entry in data/non_tei_authoritative.json"
                                     + ("; restore the archived orphan jsonl files"
                                        if archived else ""))},
            "new": {"edition": job["edition"], "source": prov["source"],
                    "license": job["license"], "loci": len(rows), "tokens": ntok,
                    "incipit": rows[0][1][:120]},
            "provenance": prov,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"     keep-list + audit written")

    if args.apply:
        NON_TEI.write_text(json.dumps(keep, ensure_ascii=False, indent=1,
                                      sort_keys=True), encoding="utf-8")
        print(f"\nupdated {NON_TEI.relative_to(COG)}  (run `make all` to roll up)")
    else:
        print("\nDRY RUN - nothing written (use --apply)")


if __name__ == "__main__":
    main()
