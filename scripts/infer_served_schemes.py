#!/usr/bin/env python3
"""Classify every served work's loci and infer a citation scheme where the
registry has none.

Many served works cite by clean logical loci (a DFHG fragment collection's
"1.1" is fragment.line) while their registry default edition declares no
scheme, so the served-canonical-locus yardstick undercounts them; ~800 more
served works are not registry keys at all and have no scheme anywhere. This
script scans every work's actual loci and writes a deterministic inference:

  logical-numeric   all (or >90% of) loci are dotted numerics ("3", "1.2",
                    "12.4a"); depth = the dominant dot depth. The inferred
                    scheme is the Canon's cit_scheme for the work when its
                    depth matches the observed depth (real level names),
                    otherwise generic "ref" / "ref.sub" / ... labels.
  edition-prefixed  loci carry an edition/page key ("pg074_0007.1",
                    "walz_rhetores_v5_0006.1"): physical, no inference.
  mixed             neither pattern dominates; no inference.

Consumed by build_registry.py (fills an EMPTY default-edition scheme, never
overrides a declared one, and marks it "scheme_inferred") and by
build_crosswalk_report.py (counts logical served loci for works absent from
the registry). Output: data/served_scheme_inference.json. Pure stdlib.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
SOURCING_MAP = DATA / "inventory" / "sourcing_map.csv"
OUT = DATA / "served_scheme_inference.json"

_LOGICAL = re.compile(r"^\d+[a-z]?(\.\d+[a-z]?)*$")
# an alphabetic stem with digits glued by underscores = edition/page keying
_PREFIXED = re.compile(r"^[a-z].*_\d")
DOMINANCE = 0.9


def canon_schemes() -> dict[str, list[str]]:
    """cts stem (tlgNNNN.tlgNNN) -> canon cit_scheme levels (lowercased)."""
    out: dict[str, list[str]] = {}
    if not SOURCING_MAP.exists():
        return out
    with SOURCING_MAP.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sch = [s.strip().lower() for s in
                   (row.get("cit_scheme") or "").split("/") if s.strip()]
            if sch:
                out[f"{row['tlg_id']}.tlg{row['work_id']}"] = sch
    return out


def main() -> None:
    editions = json.loads((DATA / "corpus_editions.json").read_text("utf-8"))
    canon = canon_schemes()

    result: dict[str, dict] = {}
    for slug in sorted(editions):
        fp = CORPUS / f"{slug}.jsonl"
        if not fp.exists():
            continue
        loci: list[str] = []
        with fp.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    loci.append(str(json.loads(line).get("locus", "")))
        if not loci:
            continue
        n = len(loci)
        n_log = sum(1 for x in loci if _LOGICAL.fullmatch(x))
        n_pre = sum(1 for x in loci if _PREFIXED.match(x))
        if n_log >= DOMINANCE * n:
            depths = {}
            for x in loci:
                if _LOGICAL.fullmatch(x):
                    d = x.count(".") + 1
                    depths[d] = depths.get(d, 0) + 1
            depth = max(depths, key=lambda d: (depths[d], -d))
            cts = (editions[slug].get("cts") or "").split("greekLit:")[-1]
            csch = canon.get(cts, [])
            if len(csch) == depth:
                scheme = ".".join(csch)
                basis = "canon cit_scheme (depth match)"
            else:
                scheme = ".".join(["ref"] + ["sub"] * (depth - 1))
                basis = "generic (canon scheme absent or depth mismatch)"
            result[slug] = {
                "class": "logical-numeric", "depth": depth,
                "scheme": scheme, "basis": basis,
                "sample": loci[:3],
            }
        elif n_pre >= DOMINANCE * n:
            result[slug] = {"class": "edition-prefixed", "sample": loci[:3]}
        else:
            result[slug] = {"class": "mixed", "sample": loci[:3]}

    counts: dict[str, int] = {}
    for v in result.values():
        counts[v["class"]] = counts.get(v["class"], 0) + 1
    payload = {"_meta": {"what": __doc__.split("\n")[0],
                         "works": len(result), "by_class": counts,
                         "dominance": DOMINANCE},
               "works": result}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1,
                              sort_keys=True) + "\n", encoding="utf-8")
    print(f"served-scheme inference: {counts} -> {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
