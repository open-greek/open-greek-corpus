#!/usr/bin/env python3
"""Generate data/source_overrides.json: per-work source-precedence overrides
applied on top of the vendored sourcing_map.csv `best_source` verdict.

sourcing_map.csv (built in the separate inventory toolkit) only knows the open
TEI corpora, the TLG's own PD editions, and the handful of CGPG volumes it was
told about. Two cog-side discoveries are NOT in it and must override its verdict:

  byzantium_gr - clean public-domain Bonn/CSHB transcriptions on byzantium.gr
               (a manual transcription, so it beats OCR of any edition).
  migne_cgpg - the calfa-co CC-BY OCR of public-domain Migne, for the ~33 PG
               volumes the sourcing map never folded in.

It also DEMOTES a false migne_cgpg verdict: sourcing_map marks a work migne_cgpg by
matching its Migne volume NUMBER against CGPG, but CGPG only OCR'd 33 specific
volumes/parts, so a work whose volume CGPG never digitised (Damascene Sacra
parallela in PG95/96, Alexander Inventio crucis in PG87.3) is reset to migne_pd.

The precedence ladder (best first; see README "Source precedence"):

  open_corpus  open TEI critical edition (First1K / Perseus, CC BY-SA)
  byzantium_gr clean manual transcription of a PD edition (byzantium.gr)
  migne_cgpg   CC-BY OCR of a PD edition (calfa-co Patrologia Graeca)
  pd_edition   a PD edition we would have to OCR ourselves
  (TLG text is never a served source.)

This script is the reproducible record of the byzantium.gr + CGPG coverage
sweeps: it reads their result JSONs in data/pd_research/, looks up each work's
current verdict in sourcing_map.csv (the value being overridden), applies the
ladder, and writes a byte-stable, sorted override list. Re-runnable.

  python scripts/build_source_overrides.py
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SOURCING_MAP = DATA / "inventory" / "sourcing_map.csv"
BYZ_SWEEP = DATA / "pd_research" / "byzantium_sweep.json"
CGPG_COVERAGE = DATA / "pd_research" / "cgpg_coverage.json"
OUT = DATA / "source_overrides.json"

# The sweeps were run on this date; stamped (not wall-clock) for byte-stability.
AS_OF = "2026-06-28"


def _key(tlg_id: str, work_id: str) -> tuple[str, str]:
    """Normalise to (tlgNNNN, 3-digit work id)."""
    return tlg_id, str(work_id).zfill(3)


def load_sourcing_verdicts() -> dict[tuple[str, str], str]:
    """(tlg_id, work_id) -> current sourcing_map best_source (the 'over' value)."""
    verdicts = {}
    with SOURCING_MAP.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            verdicts[_key(row["tlg_id"], row["work_id"])] = row.get("best_source", "")
    return verdicts


def load_sourcing_rows() -> dict[tuple[str, str], dict]:
    """(tlg_id, work_id) -> the full sourcing_map row (for mpg_vols etc.)."""
    rows = {}
    with SOURCING_MAP.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows[_key(row["tlg_id"], row["work_id"])] = row
    return rows


def main() -> None:
    verdicts = load_sourcing_verdicts()
    byz = json.loads(BYZ_SWEEP.read_text(encoding="utf-8"))
    cgpg = json.loads(CGPG_COVERAGE.read_text(encoding="utf-8"))

    # records keyed by (tlg_id, work_id); byzantium_gr is assigned first so a CGPG
    # candidate for the same work is dropped (clean transcription wins).
    records: dict[tuple[str, str], dict] = {}

    def over_of(k):
        return verdicts.get(k, "unknown")

    # 1) byzantium_gr: gap matches + locked-unlock candidates -> source=byzantium_gr.
    byz_keys = set()
    for w in byz["gap_works_recoverable_as_text"]:
        k = _key(w["tlg_id"], w["work_id"])
        byz_keys.add(k)
        records[k] = {
            "tlg_id": k[0], "work_id": k[1], "source": "byzantium_gr",
            "over": over_of(k), "author": w.get("author", ""),
            "title": w.get("title", ""), "word_count": w.get("word_count", 0),
            "urls": w.get("byzantium_urls", []),
            "evidence": ["byzantium_sweep.json"],
        }
    for w in byz["byzantium_locked_unlock_candidates"]:
        k = _key(w["tlg_id"], w["work_id"])
        byz_keys.add(k)
        records[k] = {
            "tlg_id": k[0], "work_id": k[1], "source": "byzantium_gr",
            "over": over_of(k), "title": w.get("work", ""),
            "pages": ["https://byzantium.gr/keimena/" + p for p in w.get("pages", [])],
            "evidence": ["byzantium_sweep.json"],
        }

    # 2) CGPG: every gap or locked work in a covered volume -> source=migne_cgpg,
    #    unless byzantium_gr already claimed it (then annotate the byzantium_gr record).
    for vol in cgpg["volumes"]:
        pgvol = vol.get("volume", "")
        for w in vol.get("works", []):
            if w.get("status") not in ("gap", "locked"):
                continue                      # open_corpus / byzantium_gr: not ours
            k = _key(w["tlg"], w["work"])
            if k in byz_keys:                 # clean Bonn beats Migne OCR
                records[k].setdefault("also_in_cgpg", pgvol)
                continue
            over = over_of(k)
            if over == "migne_cgpg":          # sourcing map already says CGPG
                continue
            records[k] = {
                "tlg_id": k[0], "work_id": k[1], "source": "migne_cgpg",
                "over": over, "author": w.get("author", ""),
                "title": w.get("title", ""), "word_count": w.get("word_count", 0),
                "pg_volume": pgvol, "evidence": ["cgpg_coverage.json"],
            }

    # 3) Demote a FALSE migne_cgpg verdict. sourcing_map sets best_source=migne_cgpg
    #    by matching a work's Migne volume NUMBER against CGPG, but CGPG only OCR'd
    #    33 specific volumes/parts; a work claimed migne_cgpg yet present in NO
    #    CGPG-covered volume (Damascene Sacra parallela PG95/96; Alexander Inventio
    #    crucis PG87.3 - parts CGPG never digitised) is not CC-BY-reachable and
    #    falls back to migne_pd (Migne PD per the Canon pointer; own OCR needed).
    cgpg_works = {_key(w["tlg"], w["work"])
                  for vol in cgpg["volumes"] for w in vol.get("works", [])}
    sm_rows = load_sourcing_rows()
    for k, src in verdicts.items():
        if src == "migne_cgpg" and k not in cgpg_works and k not in records:
            row = sm_rows.get(k, {})
            records[k] = {
                "tlg_id": k[0], "work_id": k[1], "source": "migne_pd",
                "over": "migne_cgpg", "author": row.get("author", ""),
                "title": row.get("title", ""),
                "word_count": int(row.get("word_count") or 0),
                "mpg_vols": row.get("mpg_vols", ""),
                "evidence": ["cgpg_coverage.json", "sourcing_map.csv"],
            }

    # 4) Galenus Verbatim: works the corpus actually serves from the
    #    galenus_verbatim source (Sorbonne CC BY-SA TEI editions of Galen and
    #    pseudo-Galen, github.com/galenus-verbatim/galenus_cts). The sourcing map
    #    predates that repo, so works it marks pd_edition/locked are promoted to
    #    open_corpus. Works whose verdict is already open_corpus (first1k serves
    #    them or shares the version) need no override. Slug -> TLG identity comes
    #    from the registry aliases, with the crosswalk as fallback.
    slug2tlg: dict[str, str] = {}
    reg_path = DATA / "source_registry.json"
    if reg_path.exists():
        for slug, w in json.loads(reg_path.read_text(encoding="utf-8"))["works"].items():
            cts = (w.get("aliases") or {}).get("cts") or ""
            if "greekLit:" in cts:
                slug2tlg[slug] = cts.split("greekLit:")[-1]
    cw_path = DATA / "tlg_crosswalk.json"
    if cw_path.exists():
        for slug, d in json.loads(cw_path.read_text(encoding="utf-8")).items():
            if d.get("tlg"):
                slug2tlg.setdefault(slug, d["tlg"])
    ce_path = DATA / "corpus_editions.json"
    if ce_path.exists():
        for slug, info in sorted(json.loads(ce_path.read_text(encoding="utf-8")).items()):
            if info.get("source") != "galenus_verbatim":
                continue
            m = re.match(r"(tlg\d+)\.tlg(\d+)$", slug2tlg.get(slug, ""))
            if not m:
                continue
            k = _key(m.group(1), m.group(2))
            over = over_of(k)
            if over == "open_corpus" or k in records:
                continue
            row = sm_rows.get(k, {})
            records[k] = {
                "tlg_id": k[0], "work_id": k[1], "source": "open_corpus",
                "over": over, "author": row.get("author", ""),
                "title": row.get("title", ""),
                "word_count": int(row.get("word_count") or 0),
                "slug": slug, "edition": info.get("edition", ""),
                "evidence": ["corpus_editions.json", "sources/galenus_verbatim"],
            }

    # human-readable reason from the (source, over, overlap) shape
    def reason_for(r):
        src, over = r["source"], r.get("over", "")
        if src == "byzantium_gr":
            base = "clean PD Bonn transcription on byzantium.gr"
            if "also_in_cgpg" in r:
                base += f"; preferred over CGPG Migne OCR ({r['also_in_cgpg']})"
            if over == "locked":
                return base + "; unlocks a work otherwise behind an in-copyright edition"
            return base + "; a manual transcription beats OCR"
        if src == "migne_cgpg":
            base = f"CC-BY CGPG OCR of PD Migne ({r.get('pg_volume', '')})"
            if over == "locked":
                return base + "; unlocks a work otherwise behind an in-copyright edition"
            return base + "; ready CC-BY text beats OCRing a PD edition ourselves"
        if src == "migne_pd":
            return (f"sourcing_map says migne_cgpg (mpg_vols {r.get('mpg_vols', '')}) but "
                    "no CGPG-covered volume contains it; CGPG never OCR'd that volume, so "
                    "it falls back to Migne PD (our own OCR needed)")
        if src == "open_corpus":
            base = ("Galenus Verbatim (Sorbonne) CC BY-SA TEI edition "
                    f"({r.get('edition', '')}), the only open Greek source for this work")
            if over == "locked":
                return base + "; unlocks a work otherwise behind an in-copyright edition"
            return base + "; a ready CC BY-SA edition beats OCRing a PD edition ourselves"
        return ""

    out = []
    for k in sorted(records):
        r = records[k]
        r["reason"] = reason_for(r)
        # stable field order
        ordered = {f: r[f] for f in ("tlg_id", "work_id", "source", "over",
                                     "author", "title", "word_count") if f in r}
        for f in ("slug", "edition", "pg_volume", "mpg_vols", "also_in_cgpg", "urls",
                  "pages", "reason", "evidence"):
            if f in r:
                ordered[f] = r[f]
        out.append(ordered)

    by_source = {}
    for r in out:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1

    doc = {
        "_meta": {
            "description": "Per-work source-precedence overrides applied on top of "
            "sourcing_map.csv best_source. Ladder: open_corpus > byzantium_gr (clean PD "
            "Bonn transcription) > migne_cgpg (CC-BY Migne OCR) > pd_edition (own OCR). "
            "TLG text is never a served source. open_corpus overrides record works "
            "served from the Galenus Verbatim CC BY-SA TEI editions, which the "
            "sourcing map predates. See README 'Source precedence'.",
            "generated_by": "scripts/build_source_overrides.py",
            "generated_from": ["data/pd_research/byzantium_sweep.json",
                               "data/pd_research/cgpg_coverage.json",
                               "data/inventory/sourcing_map.csv",
                               "data/corpus_editions.json (galenus_verbatim works)"],
            "as_of": AS_OF,
            "count": len(out),
            "by_source": by_source,
        },
        "overrides": out,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}: {len(out)} overrides {by_source}")


if __name__ == "__main__":
    main()
