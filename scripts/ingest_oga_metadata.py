#!/usr/bin/env python3
"""Ingest the two Opera Graeca Adnotata (OGA) METADATA artifacts into cog.

OGA (Giuseppe G. A. Celano, Universitat Leipzig; CC BY-SA 4.0) is an annotated
collection of Greek texts. cog already holds the underlying texts (they are the
Perseus / First1KGreek / PTA editions), so this ingester takes ONLY OGA's
work-level METADATA, never any text:

  1. work chronology  -> data/oga_dating.json
     Per-work composition dating (CTS-URN -> ISO date + date-label), from
     work_chronology/texts/chronology_greek_works_plus_date_label.xml. Each urn
     is resolved to a cog work slug and given a derived signed century + era
     (the same era vocabulary as source_identity.era_for_century). The applied
     tags are written by build_registry.py, which FILLS a missing century/era
     and flags (never overwrites) a per-work disagreement; this file is the
     portable, provenance-carrying record it reads.

  2. PTA<->TLG duplicates -> data/oga_duplicates_tlg_pta.json
     The 90 pairs where OGA holds one work under both a PTA and a TLG CTS-URN,
     from urn_cts/texts/duplicates_tlg_pta.xml. Each side is resolved to its cog
     slug and the pair is flagged as already-deduped (same slug), a live dedup
     candidate (both served under DIFFERENT slugs), one-side, or neither. It is a
     reference map for review, not an instruction to merge.

It also pins the OGA upstream (per docs/pinning-discipline.md: cog pins its
upstreams by the Zenodo VERSION DOI, never the concept DOI, plus per-file
checksums and a retained local clone) into sources/oga/manifest.json.

The OGA clone location is $OGA_ROOT (default ~/Documents/oga), or --oga-root. The
build only needs the committed JSON outputs, not the clone.

  python scripts/ingest_oga_metadata.py            # regenerate all three outputs
  OGA_ROOT=/path/to/oga python scripts/ingest_oga_metadata.py

Reproducible: given the same OGA version the outputs are byte-stable (sorted, no
wall-clock). Version DOI 10.5281/zenodo.14206061.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import lxml.etree as ET

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from source_identity import era_for_century  # noqa: E402
import crosswalk  # noqa: E402  (crosswalk.slug_for resolves a tlg/cts/pta id -> slug)


def _resolve(idno: str) -> str | None:
    """Resolve a tlg/cts/pta id to a cog work slug, or None. crosswalk.slug_for
    returns the input UNCHANGED when it cannot resolve, so an id that comes back
    as itself (a cog slug is never a raw tlg/cts/pta id) is treated as a miss."""
    slug = crosswalk.slug_for(idno, default=None, warn=False)
    return slug if slug and slug != idno else None

DATA = REPO / "data"
OGA_VERSION = "v0.2.0"
OGA_VERSIONED_DIR = f"opera_graeca_adnotata_{OGA_VERSION}"
VERSION_DOI = "10.5281/zenodo.14206061"
LICENSE = "CC-BY-SA-4.0"
CITATION = ("Giuseppe G. A. Celano. 2024. Opera Graeca Adnotata (v0.2.0). "
            "Zenodo. https://doi.org/10.5281/zenodo.14206061")

DATING_OUT = DATA / "oga_dating.json"
DUP_OUT = DATA / "oga_duplicates_tlg_pta.json"
MANIFEST_OUT = REPO / "sources" / "oga" / "manifest.json"

# BCE dates in OGA's ISO field carry the em-dash (U+2014) instead of a minus, per
# the OGA README, to avoid confusion with the hyphen-minus year/month separator.
_BCE_SIGNS = ("—", "–", "−", "-")


def _year_to_century(y: int | None) -> int | None:
    """Signed proleptic year -> signed century (-428 -> -5, 14 -> 1; no year 0)."""
    if not y:
        return None
    return (y + 99) // 100 if y > 0 else -((abs(y) + 99) // 100)


def _century_from_formatted(fw: str) -> int | None:
    """Signed century of the MIDPOINT year of an OGA ISO 8601 range, e.g.
    '+0101-01/+0200-12' -> 2, '—0249-01/—0049-12' -> -2. Each '/'-joined
    endpoint begins with '+' (CE) or the em-dash (BCE); the year is its first
    3-4 digit run (the hyphen-minus that follows is the month separator)."""
    fw = (fw or "").strip()
    if not fw:
        return None
    years: list[int] = []
    for part in fw.split("/"):
        part = part.strip()
        if not part:
            continue
        sign = -1 if part[0] in _BCE_SIGNS else (1 if part[0] == "+" else None)
        m = re.search(r"(\d{3,4})", part)
        if sign is None or not m:
            continue
        years.append(sign * int(m.group(1)))
    if not years:
        return None
    return _year_to_century((min(years) + max(years)) // 2)


def _century_from_label(label: str) -> int | None:
    """Signed century of the midpoint of an OGA date-label, e.g. 'p2_2' -> 2,
    'm3_2/m2_1/m2_2/m1_1' -> -2. A token is [p|m]<century>_<half>: p = CE
    (positive), m = BCE (negative)."""
    label = (label or "").strip()
    if not label:
        return None
    cents: list[int] = []
    for tok in re.split(r"[/\s]+", label):
        m = re.match(r"([pm])(\d+)_", tok)
        if m:
            c = int(m.group(2))
            cents.append(c if m.group(1) == "p" else -c)
    if not cents:
        return None
    mid = (min(cents) + max(cents)) // 2
    return mid or max(cents)          # never 0


def _bool(s: str) -> bool:
    return (s or "").strip().lower() in ("yes", "true", "1")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _oga_root(cli: str | None) -> Path:
    root = Path(cli or os.environ.get("OGA_ROOT")
                or os.path.expanduser("~/Documents/oga"))
    if (root / OGA_VERSIONED_DIR).is_dir():
        return root / OGA_VERSIONED_DIR
    if (root / "work_chronology").is_dir():          # already the versioned dir
        return root
    sys.exit(f"OGA clone not found under {root} (set OGA_ROOT or --oga-root to "
             f"the dir containing {OGA_VERSIONED_DIR})")


# --------------------------------------------------------------------------
def ingest_dating(oga: Path) -> dict:
    """Parse the OGA work chronology, resolve each urn to a cog slug, derive a
    signed century + era, and return the data/oga_dating.json payload."""
    xml = oga / "work_chronology" / "texts" / "chronology_greek_works_plus_date_label.xml"
    root = ET.parse(str(xml)).getroot()
    works: dict[str, dict] = {}
    n_resolved = n_registry = n_served = n_no_century = 0
    for rec in root.iter("record"):
        d = {c.tag: (c.text or "").strip() for c in rec}
        urn = d.get("urn_cts", "")
        if not urn:
            continue
        c_fmt = _century_from_formatted(d.get("formatted_work_date", ""))
        c_lbl = _century_from_label(d.get("date_label", ""))
        century = c_fmt if c_fmt is not None else c_lbl
        slug = _resolve(urn)
        in_reg = bool(slug) and slug in _REG_WORKS
        served = bool(slug) and slug in _SERVED
        if slug:
            n_resolved += 1
        if in_reg:
            n_registry += 1
        if served:
            n_served += 1
        if century is None:
            n_no_century += 1
        works[urn] = {
            "title": d.get("title_labels") or d.get("title_from_print_edition", ""),
            "author": d.get("author", ""),
            "estimated_work_date": d.get("estimated_work_date", ""),
            "formatted_work_date": d.get("formatted_work_date", ""),
            "date_label": d.get("date_label", ""),
            "is_temporary_work_date": _bool(d.get("is_temporary_work_date", "")),
            "date_source": d.get("date_source", ""),
            "date_source_link": d.get("date_source_link", ""),
            "comment": d.get("comment_on_chronology", ""),
            "century": century,
            "era": era_for_century(century) if century is not None else None,
            "century_from_label": c_lbl,
            "cog_slug": slug,
            "in_registry": in_reg,
            "served": served,
        }
    payload = {
        "_meta": {
            "description": "OGA per-work composition dating (CTS-URN -> ISO date "
                           "+ date-label), resolved to a cog work slug with a "
                           "derived signed century + era. build_registry.py "
                           "applies these as century/era tags: it FILLS a missing "
                           "tag and flags (never overwrites) a disagreement; see "
                           "data/oga_dating_report.json for the applied audit.",
            "source": f"Opera Graeca Adnotata {OGA_VERSION}",
            "source_file": "work_chronology/texts/"
                           "chronology_greek_works_plus_date_label.xml",
            "version_doi": VERSION_DOI,
            "license": LICENSE,
            "citation": CITATION,
            "generated_by": "scripts/ingest_oga_metadata.py",
            "century_derivation": "signed century of the midpoint year of "
                                  "formatted_work_date (ISO 8601 range; em-dash = "
                                  "BCE), date_label used as the fallback",
            "tagging_policy": "fill gaps, never clobber; record both readings and "
                              "flag a per-work disagreement (Multi-Source Data)",
            "counts": {
                "dated_works": len(works),
                "resolved_to_slug": n_resolved,
                "with_registry_home": n_registry,
                "served": n_served,
                "no_derivable_century": n_no_century,
                "unresolved": len(works) - n_resolved,
            },
        },
        "works": {u: works[u] for u in sorted(works)},
    }
    return payload


def ingest_duplicates(oga: Path) -> dict:
    """Parse the OGA PTA<->TLG duplicate map, resolve both sides to cog slugs, and
    flag each pair (same-slug already-deduped / live-duplicate / one-side /
    neither). A reference for review, not an instruction to merge."""
    xml = oga / "urn_cts" / "texts" / "duplicates_tlg_pta.xml"
    root = ET.parse(str(xml)).getroot()
    pairs = []
    for r in root.iter("r"):
        tlg = r.find("tlg_idno").get("v")
        pta = r.find("pta_idno").get("v")
        tlg_slug = _resolve(tlg)
        pta_slug = _resolve(pta)
        tlg_served = bool(tlg_slug) and tlg_slug in _SERVED
        pta_served = bool(pta_slug) and pta_slug in _SERVED
        same = bool(tlg_slug) and tlg_slug == pta_slug
        if same:
            status = "same-slug"          # PTA edition already contests the TLG key
        elif tlg_served and pta_served:
            status = "live-duplicate"     # both served under distinct slugs
        elif tlg_served or pta_served:
            status = "one-side-served"
        else:
            status = "neither-served"
        pairs.append({
            "tlg": tlg, "pta": pta,
            "tlg_slug": tlg_slug, "tlg_served": tlg_served,
            "pta_slug": pta_slug, "pta_served": pta_served,
            "same_slug": same, "status": status,
        })
    pairs.sort(key=lambda p: (p["tlg"], p["pta"]))
    live = [p for p in pairs if p["status"] == "live-duplicate"]
    from collections import Counter
    by_status = dict(sorted(Counter(p["status"] for p in pairs).items()))
    payload = {
        "_meta": {
            "description": "OGA PTA<->TLG duplicate-work map: pairs where OGA holds "
                           "one work under both a PTA and a TLG CTS-URN. A reference "
                           "for corpus dedup review, NOT an instruction to merge. "
                           "`same-slug` pairs are already deduped (the PTA edition "
                           "contests the TLG key via build_pta_crosswalk.py); "
                           "`live-duplicate` pairs are served under two distinct "
                           "slugs and are the candidates for review.",
            "source": f"Opera Graeca Adnotata {OGA_VERSION}",
            "source_file": "urn_cts/texts/duplicates_tlg_pta.xml",
            "version_doi": VERSION_DOI,
            "license": LICENSE,
            "generated_by": "scripts/ingest_oga_metadata.py",
            "counts": {"pairs": len(pairs), "by_status": by_status,
                       "live_duplicates": len(live)},
        },
        "pairs": pairs,
        "live_duplicates": live,
    }
    return payload


def write_manifest(oga: Path) -> dict:
    """Pin the OGA upstream: version DOI (never the concept DOI), per-file
    SHA-256 checksums of the two ingested artifacts, license, and the retained
    local clone. Per docs/pinning-discipline.md."""
    files = {
        "work_chronology/texts/chronology_greek_works_plus_date_label.xml":
            oga / "work_chronology" / "texts"
            / "chronology_greek_works_plus_date_label.xml",
        "urn_cts/texts/duplicates_tlg_pta.xml":
            oga / "urn_cts" / "texts" / "duplicates_tlg_pta.xml",
    }
    manifest = {
        "source": "Opera Graeca Adnotata (OGA)",
        "role": "metadata-only (work dating + PTA/TLG duplicate map); no text "
                "ingested - the OGA texts are the Perseus / First1KGreek / PTA "
                "editions cog already holds",
        "version": OGA_VERSION,
        "version_doi": VERSION_DOI,
        "concept_doi_note": "The concept DOI floats to the latest release and is "
                            "deliberately NOT used as the pin (see "
                            "docs/pinning-discipline.md); pin the version DOI.",
        "license": LICENSE,
        "author": "Giuseppe G. A. Celano, Universitat Leipzig (NLP)",
        "citation": CITATION,
        "upstream": {
            "zenodo": f"https://doi.org/{VERSION_DOI}",
            "github": "https://github.com/OperaGraecaAdnotata/OGA",
        },
        "retained_clone": "$OGA_ROOT (default ~/Documents/oga); the versioned "
                          f"tree is {OGA_VERSIONED_DIR}/",
        "ingested_files": {
            rel: {"sha256": _sha256(p), "bytes": p.stat().st_size}
            for rel, p in sorted(files.items())
        },
        "derived_outputs": [
            "data/oga_dating.json",
            "data/oga_duplicates_tlg_pta.json",
            "data/oga_dating_report.json (written by build_registry.py)",
        ],
        "generated_by": "scripts/ingest_oga_metadata.py",
    }
    return manifest


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--oga-root", help="OGA clone dir (default $OGA_ROOT or "
                    "~/Documents/oga)")
    args = ap.parse_args()
    oga = _oga_root(args.oga_root)

    dating = ingest_dating(oga)
    _write_json(DATING_OUT, dating)
    dup = ingest_duplicates(oga)
    _write_json(DUP_OUT, dup)
    manifest = write_manifest(oga)
    _write_json(MANIFEST_OUT, manifest)

    dc = dating["_meta"]["counts"]
    pc = dup["_meta"]["counts"]
    print(f"oga dating: {dc['dated_works']} dated works, "
          f"{dc['resolved_to_slug']} resolved to a slug "
          f"({dc['with_registry_home']} with a registry home, "
          f"{dc['served']} served), {dc['unresolved']} unresolved")
    print(f"  -> {DATING_OUT.relative_to(REPO)}")
    print(f"oga duplicates: {pc['pairs']} pairs {pc['by_status']}; "
          f"{pc['live_duplicates']} live-duplicate candidate(s)")
    print(f"  -> {DUP_OUT.relative_to(REPO)}")
    print(f"oga pin: version DOI {VERSION_DOI} -> {MANIFEST_OUT.relative_to(REPO)}")


# Loaded once; the resolver (crosswalk.slug_for) reads source_registry +
# tlg_crosswalk itself, we only need the served set and the registry-home set.
_REG_WORKS: set = set()
_SERVED: set = set()


def _load_indexes() -> None:
    global _REG_WORKS, _SERVED
    reg = DATA / "source_registry.json"
    if reg.exists():
        _REG_WORKS = set(json.loads(reg.read_text(encoding="utf-8"))
                         .get("works", {}))
    ce = DATA / "corpus_editions.json"
    if ce.exists():
        _SERVED = set(json.loads(ce.read_text(encoding="utf-8")))


if __name__ == "__main__":
    _load_indexes()
    main()
