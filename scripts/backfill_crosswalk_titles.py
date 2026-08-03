#!/usr/bin/env python3
"""Fill the empty titles in data/tlg_crosswalk.json from the CTS metadata we
already vend.

2,580 of the crosswalk's 3,428 work entries carried `"title": ""` - the builder
only had titles for works whose source record happened to include one, and the
gap is why a truncated Philo entry could sit unnoticed (an empty title displays
as nothing rather than as something visibly wrong).

The titles exist locally. Every First1K and Perseus work ships a `__cts__.xml`
carrying `ti:title` per work urn (2,751 files under sources/), and First1K's
catalog.json and edition_metadata.csv cover stragglers. Preference order per
work: a Latin-language conventional title (the scholarly citation form), then
English, then whatever is there. Existing non-empty titles are never overwritten.

  python3 scripts/backfill_crosswalk_titles.py            # dry run
  python3 scripts/backfill_crosswalk_titles.py --write
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TI = "{http://chs.harvard.edu/xmlns/cts}"
WORK_URN = re.compile(r"urn:cts:greekLit:([a-z]+\w*\.[a-z]+\w*)")


def cts_titles() -> dict[str, str]:
    """work id (tlg0018.tlg024) -> title, from every __cts__.xml under sources/."""
    out: dict[str, str] = {}
    for fp in ROOT.glob("sources/*/data/**/__cts__.xml"):
        try:
            root = ET.parse(fp).getroot()
        except ET.ParseError:
            continue
        works = ([root] if root.tag == f"{TI}work" else
                 root.iter(f"{TI}work"))
        for w in works:
            m = WORK_URN.match(w.get("urn") or "")
            if not m:
                continue
            titles = {(t.get("{http://www.w3.org/XML/1998/namespace}lang") or ""):
                      (t.text or "").strip()
                      for t in w.findall(f"{TI}title") if (t.text or "").strip()}
            best = titles.get("lat") or titles.get("eng") or \
                (next(iter(titles.values())) if titles else "")
            if best and m.group(1) not in out:
                out[m.group(1)] = best
    return out


def flat_titles() -> dict[str, str]:
    """Fallbacks from First1K's catalog.json and edition_metadata.csv."""
    out: dict[str, str] = {}
    cat = ROOT / "sources/first1k/catalog.json"
    if cat.exists():
        for e in json.loads(cat.read_text(encoding="utf-8")).get("catalog", []):
            m = WORK_URN.match(e.get("urn") or "")
            name = (e.get("work_name") or "").strip()
            if m and name:
                out.setdefault(m.group(1), name)
    meta = ROOT / "sources/first1k/data/edition_metadata.csv"
    if meta.exists():
        with meta.open(encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                m = WORK_URN.match(row.get("URN") or "")
                name = (row.get("Title") or "").strip()
                if m and name:
                    out.setdefault(m.group(1), name)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    primary = cts_titles()
    fallback = flat_titles()
    print(f"titles from __cts__.xml: {len(primary):,}; "
          f"from flat catalogs: {len(fallback):,}")

    cw = json.loads((DATA / "tlg_crosswalk.json").read_text(encoding="utf-8"))
    n = Counter()
    for key, e in cw.items():
        if not isinstance(e, dict) or "title" not in e:
            continue
        n["work entries"] += 1
        if (e.get("title") or "").strip():
            n["already titled"] += 1
            continue
        tlg = (e.get("tlg") or "").strip()
        title = primary.get(tlg) or fallback.get(tlg)
        if title:
            e["title"] = title
            n["filled"] += 1
        else:
            n["still empty (no local source has this urn)"] += 1
    for k, v in n.most_common():
        print(f"    {v:>6,}  {k}")

    if not args.write:
        print("\ndry run; nothing written. Re-run with --write.")
        return
    (DATA / "tlg_crosswalk.json").write_text(
        json.dumps(cw, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote data/tlg_crosswalk.json")


if __name__ == "__main__":
    main()
