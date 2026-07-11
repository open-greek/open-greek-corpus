#!/usr/bin/env python3
"""Generate the PTA -> slug crosswalk so build_corpus_loci can ingest the
Patristic Text Archive (sources/pta, BBAW, per-file CC BY / CC BY-SA).

PTA works are CapiTainS-shaped but keyed by pta ids (pta0001.pta001), the first
non-TLG ids through the TEI ingest. Every work's __cts__.xml carries dc
identifiers, usually including the TLG id; that is the authoritative mapping:

  TLG idno present and resolvable  -> the existing registry/crosswalk slug, so
                                      a PTA edition of a served work contests
                                      the SAME key (keep-max/dedup decides, and
                                      a Migne-OCR primary gets superseded)
  no TLG id / unresolvable         -> a minted <author>.<title> slug (reported;
                                      never a fabricated tlg urn)

Writes data/pta_crosswalk.json (the full report, rewritten each run) and merges
a "pta" alias into data/tlg_crosswalk.json entries (idempotent; existing cts/tlg
fields are never touched). crosswalk.slug_for() resolves pta ids through the
alias. Re-runnable.

  python scripts/build_pta_crosswalk.py
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import lxml.etree as ET

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources" / "pta" / "data"
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
OUT = REPO / "data" / "pta_crosswalk.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crosswalk import slug_for  # noqa: E402

TI = "{http://chs.harvard.edu/xmlns/cts}"
DC = "{http://purl.org/dc/elements/1.1/}"


def norm(name: str) -> str:
    d = unicodedata.normalize("NFD", name.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", d).strip("-")


# pta9999 is the PTA's vendored SEPTUAGINTA text-group: not patristic net-new,
# and its ~60 books would contest the served first1k LXX books key-by-key.
# The LXX sourcing question is handled separately (Swete work); skip it here.
SKIP_GROUPS = {"pta9999"}


def main() -> None:
    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    # this generator OWNS the pta namespace: strip every existing alias first
    # so re-runs never leave a stale alias on a renamed slug, and drop entries
    # that exist ONLY as pta aliases (minted by a previous run)
    for slug in [s for s, d in cw.items() if "pta" in d]:
        del cw[slug]["pta"]
        if not cw[slug]:
            del cw[slug]

    # pass 1: gather work metadata, count tlg claimants
    works = []
    tlg_claims: dict[str, list] = {}
    for wdir in sorted(SRC.glob("pta*/pta*")):
        cts_meta = wdir / "__cts__.xml"
        if not cts_meta.exists() or wdir.parent.name in SKIP_GROUPS:
            continue
        root = ET.parse(str(cts_meta)).getroot()
        pta_id = (root.get("urn") or "").rsplit(":", 1)[-1]
        title = next((t.text for t in root.iter(f"{TI}title") if t.text), "")
        idents = {t.text.split(":", 1)[0]: t.text.split(":", 1)[1]
                  for t in root.iter(f"{DC}identifier")
                  if t.text and ":" in t.text}
        tlg = (idents.get("TLG") or "").strip()
        gmeta = wdir.parent / "__cts__.xml"
        author = ""
        if gmeta.exists():
            groot = ET.parse(str(gmeta)).getroot()
            author = next((t.text for t in groot.iter(f"{TI}groupname") if t.text), "")
        works.append((pta_id, title, tlg, idents.get("CPG"), author))
        if re.fullmatch(r"tlg\d{4}\.tlg\d+[a-z]?", tlg):
            tlg_claims.setdefault(tlg, []).append(pta_id)

    # pass 2: resolve. A tlg id maps a pta work to the existing slug only when
    # that pta work is its UNIQUE claimant - when the PTA splits one canon work
    # into parts (In Job sermones 1-4 = 4 pta works on one tlg id), every part
    # gets its own minted slug instead, so keep-max can never drop the others.
    out = {}
    minted = tlg_mapped = 0
    slug_by_any = set(cw)
    for pta_id, title, tlg, cpg, author in works:
        slug = None
        how = "minted"
        if tlg in tlg_claims and len(tlg_claims[tlg]) == 1:
            resolved = slug_for(tlg)
            if resolved != tlg:               # registry/crosswalk knows the work
                slug = resolved
                how = "tlg"
                tlg_mapped += 1
        if slug is None:
            slug = f"{norm(author) or pta_id.split('.')[0]}.{norm(title) or pta_id.split('.')[1]}"
            while slug in slug_by_any:
                slug = f"{slug}-pta"          # homonym guard, never overwrite
            minted += 1
        slug_by_any.add(slug)
        out[pta_id] = {"slug": slug, "how": how, "tlg": tlg or None,
                       "cpg": cpg, "author": author, "title": title}

        entry = cw.setdefault(slug, {})
        entry["pta"] = pta_id
        if not entry.get("cts") and tlg and len(tlg_claims.get(tlg, [])) == 1:
            entry["cts"] = f"urn:cts:greekLit:{tlg}"
            entry.setdefault("tlg", tlg)
        entry.setdefault("author_slug", norm(author))
        entry.setdefault("title", title)

    # duplicate-slug check: two pta works must not share a slug
    seen = {}
    for pid, d in out.items():
        if d["slug"] in seen:
            print(f"  WARNING: {pid} and {seen[d['slug']]} both -> {d['slug']}",
                  file=sys.stderr)
        seen[d["slug"]] = pid

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
    CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0))
    print(f"pta works: {len(out)} | tlg-resolved: {tlg_mapped} | minted: {minted}")
    print(f"wrote {OUT.relative_to(REPO)}, merged aliases into "
          f"{CW_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
