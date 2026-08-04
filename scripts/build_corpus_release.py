#!/usr/bin/env python3
"""The dated, citable identity of one corpus snapshot: what is in it, how big
each source is, and what is wrong with it.

The six annotation exports each publish a release id and a content hash that a
consumer pins (docs/annotation-export-contract.md, docs/pinning-discipline.md).
The corpus itself had neither, so nothing a paper cites could be pinned. This
writes the corpus's half of that contract, as data/corpus_release.json.

The pin is the content hash, not the commit. data/corpus is git-tracked, so a
tag does fix the bytes, but a hash over the per-work sha256s survives things a
commit id does not: a mirror, a rehost, a re-import into another VCS. Same
reasoning as the export contract's hash over uncompressed payloads.

The quality block is not optional garnish. A citable artifact that states only
its size invites the reader to assume the text is uniformly trustworthy, and
this one is not: part of it is uncorrected OCR of pre-1930 editions, and the
corrections applied to the rest have a measured error rate of their own. Both
numbers ship with the release, in the same file, so a consumer cannot pick up
the counts without meeting the caveats.

Everything except the measured-precision block below is derived at run time from
data/corpus_catalog.tsv (build it first), so the release and the catalog cannot
disagree about a count. Deterministic and byte-stable: sorted keys, and the only
date in the file is the release date, which comes from CITATION.cff, from the
commit, or from --date. No wall clock, ever - the same snapshot rebuilt tomorrow
must produce the same bytes.

  python3 scripts/build_corpus_catalog.py          # first: the per-work table
  python3 scripts/build_corpus_release.py          # then: the release identity
  python3 scripts/build_corpus_release.py --date 2026-08-04 --sync-citation
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CATALOG = DATA / "corpus_catalog.tsv"
OUT = DATA / "corpus_release.json"
CITATION = REPO / "CITATION.cff"

OCR_SOURCES = {"ocr", "cgpg"}

# Human measurement, not derivable from anything in this repo: the correction
# records themselves live in the upstream OCR pipeline, and the precision
# figures come from blind philological rating of samples drawn from them. They
# are transcribed here from the README's "How good are the corrections?" section,
# which is the one place they are argued. Update BOTH when a new measurement
# lands; a stale number in a citable artifact is worse than no number, so the
# population size is recorded alongside and checked against the local audit
# mirror at run time (see corrections_block).
MEASURED = {
    "method": ("blind philological rating of stratified samples of the "
               "corrections actually present in the served text"),
    "measured_on": ["2026-08-02", "2026-08-03"],
    "precision_by_corrector": {
        "confusion": 0.93,
        "freq/auto": 0.85,
        "freq/accepted": 0.80,
        "llm/auto": 0.78,
    },
    "freq_accepted": {
        "precision": 0.80,
        "ci95": [0.74, 0.87],
        "n": 295,
        "remeasured_on": "2026-08-03",
        "wrong_rows": 13000,
        "wrong_rows_range": [9000, 17600],
    },
    "wrong_rows_estimate": 40000,
    "corrections_present": 120894,
    "corrections_present_works": 890,
    "active_records": 192151,
    "rater_disagreement": 0.086,
    "rater_kappa": 0.78,
    "caveats": [
        "Only the freq/accepted cell has been remeasured (n=295); the other "
        "cells still rest on their original samples of about 30 items each.",
        "Independent raters shown identical items disagree on 8.6% of them "
        "(kappa 0.78), so no figure here is finer than a few points.",
        "The estimate counts corrections that are wrong, not OCR errors that "
        "survive: a raw-OCR work has had no correction pass at all and none of "
        "these rates say anything about it.",
        "The worst cell measured, llm/accepted at 33%, was reverted to its OCR "
        "readings and is excluded from the figures above.",
        "The per-work unattested_rate in data/corpus_catalog.tsv is a triage "
        "signal, not a character error rate: a lexicon or a dialect glossary "
        "scores high on rare vocabulary without being misread.",
    ],
}


def shown(fp: Path) -> str:
    """Repo-relative path for a message, absolute when --out points elsewhere.
    Path.relative_to raises on a path outside the repo, and a crash while
    printing the success line would undo nothing but look like a failed build."""
    try:
        return str(fp.relative_to(REPO))
    except ValueError:
        return str(fp)


def read_catalog(fp: Path) -> list[dict]:
    if not fp.exists():
        sys.exit(f"missing {shown(fp)} - run scripts/build_corpus_catalog.py first")
    # QUOTE_NONE: the catalog is written by hand-joining tab-separated cells with
    # no quoting at all, so a double quote in a title is a literal character.
    # csv's default dialect treats one at the start of a field as an opening
    # quote and eats everything to the next one, columns included. Quoted titles
    # are not hypothetical here - Symbolum "Quicumque" Sp. is served today.
    with fp.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def n(row: dict, field: str) -> int:
    value = row.get(field) or ""
    return int(value) if value else 0


def git(*args: str) -> str | None:
    try:
        out = subprocess.run(("git", "-C", str(REPO), *args), check=True,
                             capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


def citation_fields() -> dict[str, str]:
    """The `version` and `date-released` CITATION.cff declares, if it exists.

    Read rather than assumed: CITATION.cff is hand-edited, and it is where the
    decision "this is the release we are cutting" is actually made. One owner per
    fact, per docs/pinning-discipline.md - the script should not mint a second
    release date that quietly disagrees with the one people cite.
    """
    if not CITATION.exists():
        return {}
    out = {}
    for line in CITATION.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^(version|date-released):\s*"?([^"\s]+)"?\s*$', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def resolve_date(explicit: str | None, cff_date: str | None,
                 commit_date: str | None) -> str:
    """The release date, from exactly one deterministic source.

    --date wins. Otherwise CITATION.cff's date-released, as long as it is not
    older than the commit: the file is edited ahead of the tag, so it legitimately
    names a day the last commit has not reached yet. A CITATION date that has
    fallen BEHIND the commit is stale rather than forward-looking, so the commit
    date wins and says so. Wall clock is never consulted - a release rebuilt a
    month later must come out byte-identical.
    """
    if explicit:
        return explicit
    if cff_date and commit_date and cff_date < commit_date:
        print(f"WARNING: CITATION.cff declares date-released {cff_date}, older "
              f"than the commit being released ({commit_date}). Using the commit "
              f"date; update CITATION.cff or pass --date.", file=sys.stderr)
        return commit_date
    if cff_date:
        return cff_date
    if commit_date:
        return commit_date
    sys.exit("no release date: not a git checkout and no CITATION.cff "
             "date-released - pass --date YYYY-MM-DD")


def corrections_block() -> dict:
    """The measured wrong-correction estimate, plus whether it still applies.

    data/corrections_log/ is a local, gitignored audit mirror of the fixes the
    upstream pipeline applied, so on a fresh clone there is nothing to check
    against and the block ships the measurement alone. Where the mirror IS
    present, its record count is compared with the population the precision was
    measured over: a correction campaign that runs after the measurement changes
    the denominator, and an estimate republished over a population it was never
    taken on is exactly the kind of stale claim a citable file must not make.
    Drift is recorded in the file itself, not just warned about on stderr, so a
    consumer reading the JSON alone still sees it.
    """
    block = dict(MEASURED)
    log = DATA / "corrections_log" / "applied.jsonl"
    if not log.exists():
        block["population_check"] = {
            "checked": False,
            "why": ("data/corrections_log/ is a local audit mirror and is not "
                    "published in this repository"),
        }
        return block
    records = sum(1 for _ in log.open(encoding="utf-8"))
    drifted = records != MEASURED["active_records"]
    block["population_check"] = {
        "checked": True,
        "records_now": records,
        "records_when_measured": MEASURED["active_records"],
        "stale": drifted,
    }
    if drifted:
        print(f"WARNING: the corrections log holds {records:,} records, but the "
              f"published precision was measured over "
              f"{MEASURED['active_records']:,}. The estimate is republished with "
              f"stale=true; remeasure and update MEASURED.", file=sys.stderr)
    return block


def build(rows: list[dict], catalog: Path, release_id: str, release_date: str,
          commit: str | None, commit_date: str | None,
          uncommitted_corpus: int | None) -> dict:
    per_source: dict[str, dict[str, int]] = {}
    per_license: dict[str, dict[str, int]] = {}
    per_status: dict[str, dict[str, int]] = {}
    totals = {"works": 0, "passages": 0, "tokens": 0, "tokens_lemmatized": 0}
    ocr = {"works": 0, "tokens": 0}
    raw = {"works": 0, "tokens": 0}
    pin_lines: list[str] = []

    for row in rows:
        tokens, passages = n(row, "tokens"), n(row, "passages")
        totals["works"] += 1
        totals["passages"] += passages
        totals["tokens"] += tokens
        totals["tokens_lemmatized"] += n(row, "tokens_lemmatized")
        for table, key in ((per_source, row["source"]),
                           (per_license, row["license"]),
                           (per_status, row["correction"])):
            bucket = table.setdefault(key, {"works": 0, "tokens": 0})
            bucket["works"] += 1
            bucket["tokens"] += tokens
        if row["source"] in OCR_SOURCES:
            ocr["works"] += 1
            ocr["tokens"] += tokens
            if row["correction"] == "raw-ocr":
                raw["works"] += 1
                raw["tokens"] += tokens
        # The corpus pin: a hash over (slug, per-work file hash), not over the
        # catalog file. Adding a column to the catalog must not change the
        # identity of the text the catalog describes.
        pin_lines.append(f"{row['slug']}\t{row['sha256']}\n")

    # Sorted here rather than trusting the catalog's row order: the pin has to be
    # a property of the text, and a reordered catalog naming the same files is
    # the same corpus.
    corpus_sha = hashlib.sha256("".join(sorted(pin_lines)).encode()).hexdigest()

    def share(part: int, whole: int) -> float:
        return round(part / whole, 4) if whole else 0.0

    release = {
        "release_id": release_id,
        "release_date": release_date,
        "title": "Open Greek Corpus",
        "license": "CC-BY-SA-4.0 (aggregate); see LICENSE and CITATION.cff for "
                   "the component licenses",
        "pin": {
            "corpus_sha256": corpus_sha,
            "how": ("sha256 over the sorted '<slug>\\t<per-work sha256>\\n' "
                    "lines of data/corpus/*.jsonl; independent of the catalog's "
                    "columns and of where the bytes are hosted"),
            "catalog": shown(catalog),
            "catalog_sha256": hashlib.sha256(catalog.read_bytes()).hexdigest(),
            "catalog_rows": len(rows),
        },
        "generated_from": {
            "commit": commit,
            "commit_date": commit_date,
            "note": ("the commit the catalog was built over. An artifact cannot "
                     "name the commit that carries it, so the tag names that "
                     "commit and corpus_sha256 is the byte pin"),
        },
        "corpus": totals,
        "sources": dict(sorted(per_source.items())),
        "licenses": dict(sorted(per_license.items())),
        "quality": {
            "correction_status": dict(sorted(per_status.items())),
            "raw_ocr": {
                "what": ("works whose served text is OCR that no correction "
                         "pass has touched; 'not-ocr' works are digital "
                         "editions, not corrected OCR"),
                "ocr_works": ocr["works"],
                "ocr_tokens": ocr["tokens"],
                "raw_works": raw["works"],
                "raw_tokens": raw["tokens"],
                "raw_share_of_ocr_tokens": share(raw["tokens"], ocr["tokens"]),
                "raw_share_of_corpus_tokens": share(raw["tokens"],
                                                    totals["tokens"]),
                "ocr_share_of_corpus_tokens": share(ocr["tokens"],
                                                    totals["tokens"]),
            },
            "wrong_corrections": corrections_block(),
            "per_work": ("data/corpus_catalog.tsv carries each work's source, "
                         "correction status, unattested-token rate and sha256; "
                         "quality is uneven by work and should be read there"),
        },
    }
    if uncommitted_corpus:
        # A release generated over a dirty data/corpus names a commit that does
        # not contain the text it just hashed, and the tag would pin the wrong
        # bytes. Say so in the file rather than only on stderr.
        release["generated_from"]["uncommitted_corpus_files"] = uncommitted_corpus
    return release


def sync_citation(release_id: str, release_date: str) -> None:
    """Rewrite only CITATION.cff's version and date-released.

    A surgical two-line substitution, not a YAML round-trip: dumping the file
    through a YAML writer would reflow the block scalars and drop the comments
    that explain the license fields, which are the part of that file most worth
    keeping.
    """
    text = CITATION.read_text(encoding="utf-8")
    new = re.sub(r"^version:.*$", f"version: {release_id}", text, count=1,
                 flags=re.M)
    new = re.sub(r"^date-released:.*$", f'date-released: "{release_date}"', new,
                 count=1, flags=re.M)
    if new != text:
        CITATION.write_text(new, encoding="utf-8")
        print(f"CITATION.cff: version {release_id}, date-released "
              f"{release_date}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--catalog", type=Path, default=CATALOG)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--date", help="release date YYYY-MM-DD (default: "
                                   "CITATION.cff's date-released, else the "
                                   "commit date)")
    ap.add_argument("--release-id", help="default: corpus-<release date>")
    ap.add_argument("--commit", help="override the recorded commit sha")
    ap.add_argument("--sync-citation", action="store_true",
                    help="also write the resolved release id and date back into "
                         "CITATION.cff")
    ap.add_argument("--print", dest="print_only", action="store_true",
                    help="print the release to stdout, write nothing")
    args = ap.parse_args()

    rows = read_catalog(args.catalog)
    # The release is only as current as the catalog it summarizes, and the
    # catalog is a function of data/corpus. Releasing a catalog built before the
    # last delivery would publish per-work hashes that no longer match the files
    # they name. Warned, not enforced: a fresh clone's mtimes are all the
    # checkout time and prove nothing.
    newest = max((fp.stat().st_mtime for fp in (DATA / "corpus").glob("*.jsonl")),
                 default=0.0)
    if newest and args.catalog.stat().st_mtime < newest:
        print(f"WARNING: {shown(args.catalog)} is older than data/corpus. Rerun "
              f"scripts/build_corpus_catalog.py before cutting a release.",
              file=sys.stderr)
    commit = args.commit or git("rev-parse", "HEAD")
    # %cs is the committer date as a bare YYYY-MM-DD, in no timezone the local
    # clock can shift: two people releasing the same commit get the same date.
    commit_date = git("show", "-s", "--format=%cs", "HEAD") if commit else None
    cff = citation_fields()
    release_date = resolve_date(args.date, cff.get("date-released"), commit_date)
    release_id = args.release_id or f"corpus-{release_date}"

    dirty = git("status", "--porcelain", "--", "data/corpus")
    uncommitted = len([ln for ln in dirty.splitlines() if ln.strip()]) if dirty else 0
    if uncommitted:
        print(f"WARNING: {uncommitted} file(s) under data/corpus are "
              f"uncommitted, so commit {(commit or '')[:12]} does not contain "
              f"the text this release hashes. Commit the corpus, then rerun.",
              file=sys.stderr)

    release = build(rows, args.catalog, release_id, release_date, commit,
                    commit_date, uncommitted)
    text = json.dumps(release, ensure_ascii=False, indent=1,
                      sort_keys=True) + "\n"

    if args.print_only:
        print(text, end="")
        return

    args.out.write_text(text, encoding="utf-8")
    if args.sync_citation:
        sync_citation(release_id, release_date)
    # `cff` was read before the sync, so only complain when nothing rewrote it;
    # warning about a mismatch we were just asked to fix is noise that trains
    # people to ignore the warning that matters.
    declared = None if args.sync_citation else cff.get("version")
    if declared and declared != release_id:
        print(f"WARNING: CITATION.cff declares version {declared}, this release "
              f"is {release_id}. Rerun with --sync-citation, or fix the file.",
              file=sys.stderr)

    q = release["quality"]["raw_ocr"]
    print(f"{release_id}: {release['corpus']['works']:,} works, "
          f"{release['corpus']['tokens']:,} tokens, "
          f"{len(release['sources'])} sources -> {shown(args.out)}")
    print(f"  raw OCR: {q['raw_works']:,} works, {q['raw_tokens']:,} tokens "
          f"({q['raw_share_of_corpus_tokens']:.1%} of the corpus, "
          f"{q['raw_share_of_ocr_tokens']:.1%} of its OCR)", file=sys.stderr)
    print(f"  corpus sha256 {release['pin']['corpus_sha256'][:16]}...",
          file=sys.stderr)


if __name__ == "__main__":
    main()
