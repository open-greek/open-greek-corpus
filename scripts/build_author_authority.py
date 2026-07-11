#!/usr/bin/env python3
"""Build an authoritative crosswalk from TLG author id to external authority ids.

Wikidata stores TLG author IDs as a dedicated property (P3576, "TLG author ID"),
so no fuzzy name matching is needed. This script issues ONE bulk SPARQL query to
the public Wikidata endpoint to retrieve, for every item carrying a TLG author ID,
its TLG id value, the item QID, and (optionally) its VIAF (P214) and GND (P227) ids.

The result is written to data/author_authority.json, keyed by the TLG author id
normalised to the "tlgNNNN" form used in data/inventory/work_inventory.json (the numeric
part zero-padded to 4 digits, e.g. "12" -> "tlg0012"). Each value is
{"wikidata": "Qxxxx", "viaf": "...", "gnd": "..."} with absent ids omitted. When a
single TLG id maps to several QIDs (rare), the lowest-numbered QID is kept and the
others are recorded under a "_multi" key on that entry.

Pure stdlib; the HTTP call is made with curl via subprocess. Re-runnable: it always
re-queries Wikidata and overwrites the output file.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "author_authority.json"

TLG_AUTHOR_ID_PROPERTY = "P3576"  # "TLG author ID" on Wikidata
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "cog-authority-build/1.0 (contact: cisco)"

# One row per item: SAMPLE the authority ids, take the earliest (MIN) year for
# each date so multiple precision-variants/sources don't explode the row count.
# YEAR() returns a signed proleptic year (negative = BCE), e.g. Plato birth -428.
SPARQL_QUERY = """
SELECT ?tlg ?item (SAMPLE(?viaf) AS ?viaf) (SAMPLE(?gnd) AS ?gnd)
       (SAMPLE(?isni) AS ?isni)
       (MIN(?by) AS ?birth) (MIN(?dy) AS ?death) (MIN(?fy) AS ?floruit) WHERE {
  ?item wdt:P3576 ?tlg .
  OPTIONAL { ?item wdt:P214 ?viaf . }
  OPTIONAL { ?item wdt:P227 ?gnd . }
  OPTIONAL { ?item wdt:P213 ?isni . }
  OPTIONAL { ?item wdt:P569 ?b . BIND(YEAR(?b) AS ?by) }
  OPTIONAL { ?item wdt:P570 ?d . BIND(YEAR(?d) AS ?dy) }
  OPTIONAL { ?item wdt:P1317 ?f . BIND(YEAR(?f) AS ?fy) }
} GROUP BY ?tlg ?item
"""


def run_query():
    """Return the SPARQL result bindings as a list of dicts."""
    proc = subprocess.run(
        [
            "curl",
            "-sS",
            "--fail",
            "-G",
            SPARQL_ENDPOINT,
            "--data-urlencode",
            "query=" + SPARQL_QUERY,
            "-H",
            "Accept: application/sparql-results+json",
            "-H",
            "User-Agent: " + USER_AGENT,
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit("Wikidata query failed (curl exit %d)" % proc.returncode)
    data = json.loads(proc.stdout)
    return data["results"]["bindings"]


def normalize_tlg(raw):
    """Normalise a raw TLG author id to the 'tlgNNNN' form (4-digit zero pad).

    Returns None for values that have no parseable numeric part.
    """
    m = re.search(r"\d+", raw)
    if not m:
        return None
    return "tlg" + m.group(0).zfill(4)


def qid_num(qid):
    """Sort key: numeric part of a QID for picking the lowest one."""
    m = re.search(r"\d+", qid)
    return int(m.group(0)) if m else float("inf")


def build(bindings):
    """Collapse SPARQL bindings into the keyed crosswalk dict."""
    # tlg_key -> list of {wikidata, viaf, gnd}
    grouped = {}
    for row in bindings:
        raw_tlg = row["tlg"]["value"]
        key = normalize_tlg(raw_tlg)
        if key is None:
            continue
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        entry = {"wikidata": qid}
        if "viaf" in row:
            entry["viaf"] = row["viaf"]["value"]
        if "gnd" in row:
            entry["gnd"] = row["gnd"]["value"]
        if "isni" in row:
            entry["isni"] = row["isni"]["value"]
        for fld in ("birth", "death", "floruit"):
            if fld in row and row[fld].get("value", "") not in ("", None):
                try:
                    entry[fld] = int(row[fld]["value"])
                except (ValueError, TypeError):
                    pass
        grouped.setdefault(key, {})
        # Merge per-QID (OPTIONALs can produce duplicate rows per item).
        cur = grouped[key].get(qid)
        if cur is None:
            grouped[key][qid] = entry
        else:
            cur.update({k: v for k, v in entry.items() if v})

    out = {}
    for key in sorted(grouped):
        qids = sorted(grouped[key], key=qid_num)
        chosen = grouped[key][qids[0]]
        record = {"wikidata": chosen["wikidata"]}
        for fld in ("viaf", "gnd", "isni", "birth", "death", "floruit"):
            if fld in chosen:
                record[fld] = chosen[fld]
        if len(qids) > 1:
            record["_multi"] = qids  # all QIDs seen, lowest kept above
        out[key] = record
    return out


def main():
    bindings = run_query()
    sys.stderr.write("Retrieved %d rows from Wikidata.\n" % len(bindings))
    crosswalk = build(bindings)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(crosswalk, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    multi = [k for k, v in crosswalk.items() if "_multi" in v]
    sys.stderr.write(
        "Wrote %d TLG author ids to %s (%d with multiple QIDs).\n"
        % (len(crosswalk), OUT_PATH, len(multi))
    )


if __name__ == "__main__":
    main()
