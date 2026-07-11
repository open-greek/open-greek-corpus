#!/usr/bin/env python3
"""Walk Wikidata for the WORKS of authors that carry a TLG author id, so the
registry can enrich work-level data (Wikidata QID, genres, language) that the
TLG Canon alone doesn't give. There is no "TLG work id" property, so the route
is author-side: items that are `author of` (P50) an item with a TLG author id
(P3576). For each such work we keep its QID, English label, genres (P136),
languages (P407), and inception/publication year (P571/P577).

Result -> data/work_authority.json, keyed by the author's TLG id (tlgNNNN), value
a list of work records {qid, label, genres[], langs[], year}. build_registry
matches these to Canon works by normalized title (within the same author).

Pure stdlib; one paginated SPARQL query via curl. Re-runnable.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "work_authority.json"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "cog-work-authority-build/1.0 (contact: cisco)"
PAGE = 4000

QUERY = """
SELECT ?tlg ?work ?workLabel
       (SAMPLE(?laL) AS ?la) (SAMPLE(?grcL) AS ?grc) (SAMPLE(?elL) AS ?el)
       (GROUP_CONCAT(DISTINCT ?gl; separator="|") AS ?genres)
       (GROUP_CONCAT(DISTINCT ?ll; separator="|") AS ?langs)
       (MIN(?yr) AS ?year) WHERE {
  ?author wdt:P3576 ?tlg .
  ?work wdt:P50 ?author .
  # exclude only specific editions/translations (P629): those carry foreign-
  # language labels that could coincidentally match a Canon title (a Portuguese
  # "Ílias" -> "ilias"). NOT a P361 filter: major works are "part of" a cycle
  # (the Iliad is part of the Homeric epics, a tragedy part of its trilogy), so
  # filtering P361 wrongly drops them. Sub-parts ("Book I") survive but are
  # harmless - they don't match any Canon title and the match is unambiguous-only.
  FILTER NOT EXISTS { ?work wdt:P629 [] }
  ?work rdfs:label ?workLabel . FILTER(LANG(?workLabel) = "en")
  # the Latin label is the Canon's Latinised title form (Ilias, Odyssea); the
  # Greek labels are kept for future Greek-title matching.
  OPTIONAL { ?work rdfs:label ?laL . FILTER(LANG(?laL) = "la") }
  OPTIONAL { ?work rdfs:label ?grcL . FILTER(LANG(?grcL) = "grc") }
  OPTIONAL { ?work rdfs:label ?elL . FILTER(LANG(?elL) = "el") }
  OPTIONAL { ?work wdt:P136 ?g . ?g rdfs:label ?gl . FILTER(LANG(?gl) = "en") }
  OPTIONAL { ?work wdt:P407 ?l . ?l rdfs:label ?ll . FILTER(LANG(?ll) = "en") }
  OPTIONAL { ?work wdt:P571 ?inc . BIND(YEAR(?inc) AS ?yr) }
  OPTIONAL { ?work wdt:P577 ?pub . BIND(YEAR(?pub) AS ?yr) }
}
GROUP BY ?tlg ?work ?workLabel
ORDER BY ?work
LIMIT %d OFFSET %d
"""


def run(query):
    proc = subprocess.run(
        ["curl", "-sS", "--fail", "-G", SPARQL_ENDPOINT,
         "--data-urlencode", "query=" + query,
         "-H", "Accept: application/sparql-results+json",
         "-H", "User-Agent: " + USER_AGENT],
        capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit("Wikidata query failed (curl exit %d)" % proc.returncode)
    return json.loads(proc.stdout)["results"]["bindings"]


def norm_tlg(raw):
    m = re.search(r"\d+", raw)
    return "tlg" + m.group(0).zfill(4) if m else None


def main():
    by_author = {}
    offset, total = 0, 0
    while True:
        rows = run(QUERY % (PAGE, offset))
        if not rows:
            break
        total += len(rows)
        for r in rows:
            key = norm_tlg(r["tlg"]["value"])
            if not key:
                continue
            rec = {
                "qid": r["work"]["value"].rsplit("/", 1)[-1],
                "label": r["workLabel"]["value"],
            }
            for fld in ("la", "grc", "el"):
                v = r.get(fld, {}).get("value", "")
                if v:
                    rec[fld] = v
            g = r.get("genres", {}).get("value", "")
            la = r.get("langs", {}).get("value", "")
            if g:
                rec["genres"] = sorted(set(filter(None, g.split("|"))))
            if la:
                rec["langs"] = sorted(set(filter(None, la.split("|"))))
            if r.get("year", {}).get("value", ""):
                try:
                    rec["year"] = int(r["year"]["value"])
                except ValueError:
                    pass
            by_author.setdefault(key, []).append(rec)
        sys.stderr.write("  ...%d rows\n" % total)
        if len(rows) < PAGE:
            break
        offset += PAGE

    # dedupe per author by qid, stable order
    for key in by_author:
        seen, out = set(), []
        for rec in by_author[key]:
            if rec["qid"] not in seen:
                seen.add(rec["qid"])
                out.append(rec)
        by_author[key] = out

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(by_author, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    nworks = sum(len(v) for v in by_author.values())
    sys.stderr.write("Wrote %d works for %d TLG authors to %s\n"
                     % (nworks, len(by_author), OUT_PATH))


if __name__ == "__main__":
    main()
