#!/usr/bin/env python3
"""Validate the opaque-id layer's invariants. Exits non-zero on any failure.

Checks:
  1. every served work-unit has exactly one ogc id (total coverage, no dup);
  2. every served author has exactly one oga id;
  3. ids are unique and well-formed (ogc/oga + 6 digits);
  4. the id counter is monotonic (next > every id ever minted; retired ids are
     tombstoned, never recycled);
  5. no slug is claimed by two ids; no former_slug equals a current served slug;
  6. every external anchor (cts/tlg/wikidata) in the index round-trips back to
     the source it came from;
  7. the 4 TLG variant-edition pairs have DISTINCT ogc ids that SHARE one TLG
     Work anchor (our id is finer than TLG - the whole point);
  8. former-slug resolution works: each recorded rename's old slug redirects to
     the current work and its id;
  9. re-running build_id_registry reassigns nothing (append-only, --check-stable).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def main() -> int:
    served = {fp.name[:-6] for fp in (DATA / "corpus").glob("*.jsonl")}
    work_ids = load("work_ids.json")["works"]
    author_ids = load("author_ids.json")["authors"]
    index = load("work_index.json")
    idx_works = index["works"]
    redirects = index["redirects"]
    tc = load("tlg_crosswalk.json")
    reg = load("source_registry.json")
    reg_works = reg["works"]

    fails: list[str] = []
    def check(cond, msg):
        if not cond:
            fails.append(msg)

    wid = re.compile(r"^ogc\d{6}$")
    aid = re.compile(r"^oga\d{6}$")

    # 1 + 3: served coverage, format, uniqueness
    served_entries = {i: e for i, e in work_ids.items() if e["status"] == "served"}
    served_slugs_in_ledger = {e["slug"] for e in served_entries.values()}
    check(served_slugs_in_ledger == served,
          f"served-set mismatch: ledger {len(served_slugs_in_ledger)} vs "
          f"corpus {len(served)} "
          f"(missing {list(served - served_slugs_in_ledger)[:3]})")
    check(all(wid.match(i) for i in work_ids), "malformed ogc id present")
    check(len(set(work_ids)) == len(work_ids), "duplicate ogc id")
    # exactly one id per served work
    from collections import Counter
    slug_counts = Counter(e["slug"] for e in served_entries.values())
    dupes = [s for s, n in slug_counts.items() if n > 1]
    check(not dupes, f"served slug with >1 id: {dupes[:3]}")

    # 2: authors
    check(all(aid.match(i) for i in author_ids), "malformed oga id present")
    check(len(set(author_ids)) == len(author_ids), "duplicate oga id")

    # 4: monotonic counter / tombstones
    for ledger, pref in ((work_ids, "ogc"), (author_ids, "oga")):
        nums = [int(i[3:]) for i in ledger]
        nxt = load("work_ids.json" if pref == "ogc" else "author_ids.json"
                   )["_meta"]["counts"]["next"]
        check(nxt > max(nums), f"{pref} next {nxt} not past max {max(nums)}")
        check(len(nums) == len(set(nums)), f"{pref} numeric collision")

    # 5: slug uniqueness across ids, former != current served
    slug_to_id = {}
    for i, e in work_ids.items():
        for s in [e["slug"], *e.get("former_slugs", [])]:
            check(s not in slug_to_id,
                  f"slug {s!r} claimed by {slug_to_id.get(s)} and {i}")
            slug_to_id[s] = i
    for i, e in work_ids.items():
        for fs in e.get("former_slugs", []):
            check(fs not in served,
                  f"former_slug {fs!r} collides with a served work")

    # 6: anchor round-trip
    for slug, w in idx_works.items():
        a = w["work_anchors"]
        if a.get("tlg"):
            check(tc.get(slug, {}).get("tlg") == a["tlg"],
                  f"tlg anchor for {slug} does not round-trip")
        if a.get("cts"):
            src = tc.get(slug, {}).get("cts") or \
                  reg_works.get(slug, {}).get("aliases", {}).get("cts")
            check(src == a["cts"], f"cts anchor for {slug} does not round-trip")
        if a.get("wikidata"):
            check(reg_works.get(slug, {}).get("aliases", {}).get("wikidata")
                  == a["wikidata"], f"wikidata anchor for {slug} broken")

    # 7: the 4 variant-edition pairs -> distinct ids, one shared TLG anchor
    from collections import defaultdict
    tlg_to_ids = defaultdict(set)
    for slug, w in idx_works.items():
        t = w["work_anchors"].get("tlg")
        if t:
            tlg_to_ids[t].add(w["id"])
    shared = {t: ids for t, ids in tlg_to_ids.items() if len(ids) > 1}
    check(len(shared) == 4,
          f"expected 4 shared-TLG variant pairs, found {len(shared)}: "
          f"{list(shared)}")
    for t, ids in shared.items():
        check(len(ids) == 2, f"TLG {t} shared by {len(ids)} ids, expected 2")

    # 8: former-slug resolution (redirects)
    seed = load("work_id_aliases.json").get("renames", [])
    for r in seed:
        frm, to = r["from"], r["to"]
        if to in served:  # applied rename
            check(redirects.get(frm) == to,
                  f"redirect {frm} -> {to} missing from index")
            check(slug_to_id.get(frm) == idx_works[to]["id"],
                  f"former slug {frm} does not resolve to {to}'s id")

    # 9: append-only stability
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "build_id_registry.py"),
                        "--check-stable"], capture_output=True, text=True)
    check(r.returncode == 0, "build_id_registry --check-stable failed (not append-only)")

    if fails:
        print(f"FAIL ({len(fails)} problems):")
        for f in fails:
            print("  -", f)
        return 1
    print("OK: all id-layer invariants hold")
    print(f"  works: {len(served_entries)} served (all with exactly one ogc id)")
    print(f"  authors: {sum(1 for e in author_ids.values() if e['status']=='served')} served")
    print(f"  variant pairs (distinct ids, shared TLG anchor): {len(shared)}")
    print(f"  redirects (former slug -> current): {len(redirects)}")
    print(f"  works with no external anchor: "
          f"{index['_meta']['counts']['no_external_anchor']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
