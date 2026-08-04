#!/usr/bin/env python3
"""One row per served work: what it is, where it came from, how good it is, and
the sha256 of the bytes we serve.

data/corpus is fully git-tracked, so a git tag already pins the corpus byte for
byte. What a tag does NOT give anyone is a way to see what is inside it, or how
much of it to trust, without cloning 1.3 GB. That is this table's job: it joins
the per-work facts that already exist in six separate files into one flat page a
consumer can read, sort, filter and diff.

Nothing here is newly measured. Every column is a join:

  data/work_index.json            ogc id, slug, title, author (+ oga id), and the
                                  CTS / TLG / Wikidata anchors
  data/corpus_editions.json       winning edition, source, license, passages
  data/work_token_totals.json     tokens + tokens_lemmatized, counted over the
                                  served text itself (not the hand-edited ledgers)
  data/ocr_quality_report.json    unattested-token rate, for OCR-source works
  data/corpus/<slug>.jsonl        each row's own `corrections` stamp, read the way
                                  scripts/build_provenance.py reads it, plus the
                                  sha256 of the file
  data/served_scheme_inference.json   the locus classification (class / scheme /
                                  depth) exactly as that file states it

The scheme columns are that file's own `class`, `scheme` and `depth`, carried
through verbatim. A second, catalog-local classification of the same loci would
be a second answer to a question this repo has already answered, and the two
would drift the first time a locus convention changed.

Output: data/corpus_catalog.tsv, deterministic (sorted by slug, fixed column
order, no wall clock anywhere), so a rebuild that changes nothing is a no-op and
re-committing it is churn-free.

  python3 scripts/build_corpus_catalog.py
  python3 scripts/build_corpus_catalog.py --check     # report drift, write nothing
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
OUT = DATA / "corpus_catalog.tsv"

# Same two sources build_provenance.py and build_ocr_quality_report.py call OCR.
OCR_SOURCES = {"ocr", "cgpg"}

# A row stamped by one of these was edited by a human or an LLM acting as one, so
# the work counts as manually corrected; anything else (confusion, dehyphenation,
# freq, prosodia) is a deterministic pass. Kept identical to build_provenance.py's
# MANUAL_TAGS on purpose: two tables describing the same works must not disagree
# about which of them a person has looked at.
MANUAL_TAGS = {"llm", "agent", "manual"}

COLUMNS = [
    "slug", "work_id", "title", "author", "author_id",
    "cts_urn", "tlg", "wikidata",
    "source", "edition", "license", "passages", "tokens", "tokens_lemmatized",
    "correction", "unattested_rate",
    "scheme_class", "scheme", "scheme_depth",
    "sha256",
]

# work_token_totals.json is keyed by each corpus row's own `urn` field, falling
# back to the file stem (build_work_lemma_counts.py, tokenize_file). Exactly one
# work disagrees with its filename: philodemus.tlg1595-tlg601.jsonl carries
# "urn": "tlg1595.tlg601" on all 1,761 of its rows, the bare CTS work id it was
# ingested under, which was never rewritten when the work got its author.work
# slug. So the totals file keys that work by a dot where every other artifact in
# the repo keys it by the slug's dash. The fix belongs upstream, in the ingest
# that stamps the rows; until then this alias keeps the work from silently
# losing its token counts. Anything BEYOND this pair is a real key drift and
# stops the build - see check_token_totals_keys.
KNOWN_TOTALS_KEY_ALIASES = {"tlg1595.tlg601": "philodemus.tlg1595-tlg601"}

_WS = re.compile(r"\s+")


def shown(fp: Path) -> str:
    """Repo-relative path for a message, absolute when --out points elsewhere.
    Path.relative_to raises on a path outside the repo, and a crash while
    printing the success line would look like a build that failed."""
    try:
        return str(fp.relative_to(REPO))
    except ValueError:
        return str(fp)


def load(name: str):
    fp = DATA / name
    if not fp.exists():
        sys.exit(f"missing input {fp} - run the build that produces it first")
    return json.loads(fp.read_text(encoding="utf-8"))


def check_token_totals_keys(totals: dict, stems: set[str]) -> dict[str, str]:
    """Assert work_token_totals.json describes exactly the works we serve.

    A totals file whose key set has drifted from data/corpus is the failure mode
    that put the whole Hesychius lexicon under the slug of its prefatory letter
    in the README's word column: the counts stay plausible while naming the wrong
    work. So the key sets are compared before anything else runs.

    The comparison is informative rather than fatal for the one known, diagnosed
    alias above, because failing the build over it would only stop the catalog
    from being built at all while leaving the underlying stamp untouched. Any
    other difference exits non-zero.

    Returns the alias map actually applied (empty when the key sets match).
    """
    missing = stems - set(totals)                 # served, but no token count
    extra = set(totals) - stems                   # counted, but not served
    applied = {k: v for k, v in KNOWN_TOTALS_KEY_ALIASES.items()
               if k in extra and v in missing}
    unexplained_missing = missing - set(applied.values())
    unexplained_extra = extra - set(applied)
    if unexplained_missing or unexplained_extra:
        sys.exit(
            "work_token_totals.json does not describe the served corpus:\n"
            f"  {len(unexplained_missing)} served works with no token count: "
            f"{sorted(unexplained_missing)[:10]}\n"
            f"  {len(unexplained_extra)} counted works that are not served: "
            f"{sorted(unexplained_extra)[:10]}\n"
            "Rerun scripts/build_work_lemma_counts.py against the current "
            "data/corpus, or diagnose the key drift before publishing a catalog.")
    for stale, slug in sorted(applied.items()):
        print(f"WARNING: work_token_totals.json keys {slug} as {stale} - its "
              f"corpus rows carry a stale internal urn from ingest, so the "
              f"totals inherit it. Counting it under the slug; fix the row "
              f"stamps upstream.", file=sys.stderr)
    return applied


def warn_if_stale(fp: Path, newest_corpus: float) -> None:
    """Warn when an input predates the text it claims to describe.

    build_provenance.py learned this the hard way: work_token_totals.json older
    than data/corpus meant the README's word column reported the whole Hesychius
    lexicon under the slug of its prefatory letter, because the file predated the
    CGPG carves. The same stale file here would publish those counts as a citable
    fact.

    A warning, never fatal: a fresh clone stamps every file with the checkout
    time, so mtime ordering there is arbitrary and says nothing about content.
    """
    if fp.exists() and newest_corpus and fp.stat().st_mtime < newest_corpus:
        print(f"WARNING: {fp.name} is older than data/corpus - its counts may "
              f"predate the served text. Rerun the build that produces it.",
              file=sys.stderr)


def cell(value) -> str:
    """One TSV cell: never a tab, never a newline, never None.

    Two served titles carry an embedded newline from their TEI (the Euripides
    Hecuba scholia and one Severian of Gabala oration), which would silently
    split a row in half and shift every later column by one. Collapse whitespace
    instead of trusting the upstream string.
    """
    if value is None:
        return ""
    return _WS.sub(" ", str(value)).strip()


def scan_work(fp: Path) -> tuple[str, set[str]]:
    """(sha256 of the file, the union of its rows' `corrections` stamps).

    One read serves both: the hash is over the exact bytes git tracks, and the
    stamps are read from those same bytes, so the correction column can never
    describe a different revision of the file than the hash names. The cheap
    substring test before json.loads is build_provenance.py's - parsing every
    row of 1.3 GB to look for a key most rows do not have is the slow way.
    """
    raw = fp.read_bytes()
    tags: set[str] = set()
    for line in raw.decode("utf-8").splitlines():
        if '"corrections"' in line:
            tags.update(json.loads(line).get("corrections", []))
    return hashlib.sha256(raw).hexdigest(), tags


def correction_status(slug: str, source: str, tags: set[str],
                      manual_log: set[str], auto_log: set[str]) -> str:
    """manual / auto-corrected / raw-ocr / not-ocr, per build_provenance.py.

    The row stamps are authoritative: every edit method stamps the row it
    touched, so a work edited by a tool that bypassed the corrections-log overlay
    still shows up here. The log adds the works whose stamps predate the stamping
    convention; it lives in data/corrections_log/, which is gitignored, so a
    fresh clone falls back to the stamps alone rather than failing.

    The log only gets a vote on works we still serve from OCR. It records edits
    made to OCR text, and a work can leave OCR behind: galenus.institutio-logica
    was auto-corrected as OCR and is now served from the First1K TEI edition, so
    the log's claim is about bytes the source swap replaced. Stamps have no such
    problem - they are read out of the served file itself - so they still count
    wherever they appear.

    `not-ocr` is not "unedited": it means the served text is a digital edition,
    where a correction pass would be someone else's editorial work, not ours.
    """
    is_ocr = source in OCR_SOURCES
    if tags & MANUAL_TAGS or (is_ocr and slug in manual_log):
        return "manual"
    if tags or (is_ocr and slug in auto_log):
        return "auto-corrected"
    return "raw-ocr" if is_ocr else "not-ocr"


def build_rows() -> tuple[list[list[str]], dict]:
    index = load("work_index.json")["works"]
    editions = load("corpus_editions.json")
    totals = load("work_token_totals.json")
    quality = load("ocr_quality_report.json")["works"]
    schemes = load("served_scheme_inference.json")["works"]

    files = {fp.stem: fp for fp in CORPUS.glob("*.jsonl")}
    if not files:
        sys.exit(f"no served corpus in {CORPUS}")
    newest = max((fp.stat().st_mtime for fp in files.values()), default=0.0)
    for name in ("work_token_totals.json", "ocr_quality_report.json",
                 "served_scheme_inference.json", "corpus_editions.json"):
        warn_if_stale(DATA / name, newest)
    aliases = check_token_totals_keys(totals, set(files))
    for stale, slug in aliases.items():
        totals[slug] = totals.pop(stale)

    # The corrections log is a local, gitignored audit mirror (it names the AI
    # correctors), so treat it as optional enrichment and never as a required
    # input: the catalog has to build the same way from a fresh clone.
    log_fp = DATA / "corrections_log" / "provenance.json"
    log = json.loads(log_fp.read_text(encoding="utf-8")) if log_fp.exists() else {}
    manual_log = set(log.get("corrected_works", []))
    auto_log = set(log.get("auto_corrected_works", []))

    rows: list[list[str]] = []
    filled = dict.fromkeys(COLUMNS, 0)
    for slug in sorted(files):
        idx = index.get(slug, {})
        anchors = idx.get("work_anchors", {})
        author = idx.get("author", {})
        ed = editions.get(slug, {})
        tot = totals.get(slug, {})
        qual = quality.get(slug, {})
        sch = schemes.get(slug, {})
        sha, tags = scan_work(files[slug])
        source = ed.get("source", "")
        rate = qual.get("unattested_rate")
        row = [
            slug,
            cell(idx.get("id")),
            cell(idx.get("title")),
            cell(author.get("name")),
            cell(author.get("id")),
            cell(anchors.get("cts")),
            cell(anchors.get("tlg")),
            cell(anchors.get("wikidata")),
            cell(source),
            cell(ed.get("edition")),
            cell(ed.get("license")),
            cell(ed.get("n_passages")),
            cell(tot.get("tokens")),
            cell(tot.get("tokens_lemmatized")),
            correction_status(slug, source, tags, manual_log, auto_log),
            # Fixed 6 decimals, matching the report's own rounding: a bare repr
            # would print 0.07064 and 0.2725320000000001 in the same column.
            "" if rate is None else f"{rate:.6f}",
            cell(sch.get("class")),
            cell(sch.get("scheme")),
            cell(sch.get("depth")),
            sha,
        ]
        rows.append(row)
        for col, value in zip(COLUMNS, row):
            if value != "":
                filled[col] += 1
    stats = {"rows": len(rows), "filled": filled,
             "token_totals_aliases": aliases}
    return rows, stats


def render(rows: list[list[str]]) -> str:
    lines = ["\t".join(COLUMNS)]
    lines.extend("\t".join(r) for r in rows)
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--check", action="store_true",
                    help="compare against the committed catalog and report "
                         "drift; write nothing, exit 1 if it differs")
    args = ap.parse_args()

    rows, stats = build_rows()
    text = render(rows)

    if args.check:
        if not args.out.exists():
            sys.exit(f"{shown(args.out)} does not exist yet - build it first")
        old = args.out.read_text(encoding="utf-8")
        if old == text:
            print(f"catalog: {stats['rows']} rows, up to date")
            return
        # Name what moved, not just that something did. A catalog can go stale
        # two very different ways - works appearing or leaving, or the same works
        # changing (a re-OCR delivery changes a sha256 and nothing else) - and the
        # second is the one a bare byte-diff hides.
        was = {ln.split("\t", 1)[0]: ln for ln in old.splitlines()[1:]}
        now = {r[0]: "\t".join(r) for r in rows}
        changed = sum(1 for k in was.keys() & now.keys() if was[k] != now[k])
        sys.exit(f"catalog is stale: {len(now.keys() - was.keys())} works added, "
                 f"{len(was.keys() - now.keys())} removed, {changed} changed. "
                 f"Rerun scripts/build_corpus_catalog.py.")

    args.out.write_text(text, encoding="utf-8")
    print(f"catalog: {stats['rows']} works -> {shown(args.out)}")
    for col in COLUMNS:
        n = stats["filled"][col]
        print(f"  {col:<18} {n:>5} / {stats['rows']}"
              + ("" if n == stats["rows"] else
                 f"  ({stats['rows'] - n} blank)"), file=sys.stderr)


if __name__ == "__main__":
    main()
