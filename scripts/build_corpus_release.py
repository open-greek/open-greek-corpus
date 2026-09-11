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
  python3 scripts/build_corpus_release.py --check   # before tagging: does the
                                                   # stored record still describe the corpus?
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
    "method": ("two independent blind raters per item over a random sample of "
               "the served overlay, stratified by the route that applied each "
               "correction; a correction counts sound only when both raters "
               "call it right and wrong only when both call it wrong"),
    "measured_on": ["2026-08-12"],
    "sample": {"drawn": 990, "rated": 803, "population": 245362,
               "seed": 20260812,
               "tool": "greek-ocr scripts/sample_applied_overlay.py"},
    # both-raters-right per route. The earlier 2026-08-02/03 figures used one
    # rater, so single_rater_rate below is what they compare against.
    "precision_by_corrector": {
        "agent/accepted": 0.979,
        "confusion/accepted": 0.847,
        "freq/accepted": 0.700,
        "freq/auto": 0.764,
        "llm/accepted": 0.536,
        "llm/auto": 0.825,
    },
    # Four of the six routes are no longer estimates. Each record was read on its
    # own by two blind raters, so these supersede precision_by_corrector above for
    # the same route - the README argues the same rule in prose. Kept as a nested
    # block rather than a second flat float per route, because a census has to
    # carry what a sample carries: how many were read, out of how many, and how
    # often the two raters agreed.
    #
    # `rated` is short of `cell_records` in every cell, and the gap is not error.
    # Staging drops a record that no longer resolves to a served row - the July
    # 2026 re-OCR replaced the text, or a carve moved it - so a census reads the
    # part of its cell the corpus still carries. Saying "the whole cell" would
    # overclaim by 840 records in confusion/accepted and by 24,863 in freq/auto.
    "censused_by_corrector": {
        "freq/accepted": {"cell_records": 84004, "rated": 75259, "sound": 0.781,
                          "ci95": [0.7781, 0.7840], "agreement": 0.937,
                          "reverted": 10933, "split_still_applied": 5541,
                          "split_with_a_wrong_verdict": 3238,
                          "measured_on": "2026-08-18"},
        "freq/auto": {"cell_records": 75547, "rated": 50684, "sound": 0.834,
                      "ci95": [0.8309, 0.8374], "agreement": 0.954,
                      "reverted": 5785, "split_still_applied": 2618,
                      "split_with_a_wrong_verdict": 1790,
                      "measured_on": "2026-08-19"},
        "confusion/accepted": {"cell_records": 16414, "rated": 15573,
                               "sound": 0.866, "ci95": [0.8607, 0.8714],
                               "agreement": 0.972, "reverted": 1512,
                               "split_still_applied": 573,
                               "split_with_a_wrong_verdict": 303,
                               "measured_on": "2026-08-21",
                               # 480 of the 15,573 were a second read of records
                               # the Eustathius confusion census had already
                               # called unanimously right, and they came back
                               # 99.8% right. Since they were selected for being
                               # right, including them lifts the cell by 0.42
                               # points, which is as wide as the interval: the
                               # 15,093 records read for the first time in this
                               # cell are 86.2% sound.
                               "sound_first_read_only": 0.862,
                               "first_read_records": 15093},
        "llm/accepted": {"cell_records": 2522, "rated": 2114, "sound": 0.497,
                         "ci95": [0.4759, 0.5185], "agreement": 0.921,
                         "reverted": 868, "split_still_applied": 195,
                         "split_with_a_wrong_verdict": 131,
                         "measured_on": "2026-08-12"},
        "what": ("both-raters-right over every staged record of the cell, read "
                 "one at a time rather than sampled; `reverted` is the records "
                 "both raters called wrong, which are out of the served text. "
                 "agent/accepted and llm/auto have not been censused and rest on "
                 "the sample above"),
        "split_still_applied": ("a census gate is asymmetric on purpose: it "
                                "reverts only where both raters call a record "
                                "wrong, because a bad correction left in place is "
                                "a measured defect while a reverted good one is "
                                "fresh OCR damage in text that was right. So the "
                                "records the raters disagreed on stay in the "
                                "served text, 8,927 of them across the four "
                                "cells, and 5,462 of those carry at least one "
                                "wrong verdict. That is the censuses' own "
                                "residual and it is not counted in any rate "
                                "above: read sound, reverted and this as three "
                                "bands, not two"),
        "evidence": "data/precision/cell_*/cell_gate.json in the upstream pipeline",
        "raters": ("two independent agent instances of one model family, each "
                   "shown the passage, both forms and the corrector's note, with "
                   "no verdict, corrector or status. Agreement is therefore a "
                   "reproducibility bound and not evidence of correctness: a "
                   "blind spot the model shares passes both raters"),
    },
    "corpus_weighted": {
        "sound": 0.762,
        "wrong": 0.177,
        "split_or_unsure": 0.060,
        "single_rater_rate": 0.779,
    },
    "superseded": {
        "measured_on": ["2026-08-02", "2026-08-03"],
        "precision_by_corrector": {"confusion": 0.93, "freq/auto": 0.85,
                                   "freq/accepted": 0.80, "llm/auto": 0.78},
        "why": ("those samples were drawn per corrector from slices chosen for "
                "being hard and mostly rested on n around 30 with one rater; "
                "compared one-rater to one-rater every cell but llm/auto was "
                "optimistic by 6 to 8 points"),
    },
    "wrong_rows_estimate": 43400,
    "reverted_since_measurement": {
        "records": 20545,
        "what": ("1,447 from the re-adjudication accepts pass, 868 from the "
                 "llm/accepted census, 10,933 from the freq/accepted census, "
                 "5,785 from the freq/auto census and 1,512 from the "
                 "confusion/accepted census, every one on a unanimous two-rater "
                 "verdict over a record read individually rather than sampled. "
                 "The wrong_rows_estimate above describes the overlay as it was "
                 "sampled on 2026-08-12; the served text now carries that many "
                 "fewer wrong corrections, and the estimate has not been "
                 "remeasured since"),
        "audits": ("greek-ocr data/corrections/cell_revert_*.json, whose record "
                   "lists sum to these figures"),
    },
    "applied_since_measurement": {
        "records": 14017,
        "what": ("the 2026-08-21 Eustathius bake. 16,570 records against the "
                 "Iliad commentary said auto or accepted while the rows still "
                 "held the OCR reading, so nothing had ever been applied. All "
                 "16,601 staged proposals were read by two blind raters across "
                 "two gates, freq/auto (16,081 read) and confusion/accepted "
                 "(520); 2,651 were rejected and 13,959 written, plus 58 active "
                 "records elsewhere that had gone unapplied"),
        "survivor_precision": {
            "freq/auto": {"rate": 0.971, "ci95": [0.944, 0.985], "rated": 275},
            "confusion/accepted": {"rate": 1.0, "ci95": [0.977, 1.0], "rated": 165},
            "what": ("a second blind two-rater read of a random sample of the "
                     "records the census KEPT, which is what the bake actually "
                     "wrote; the cells themselves read 83.8% and 92.1%. Read it "
                     "as reproducibility rather than truth, since the second "
                     "pair shares a model family with the first"),
            "evidence": "greek-ocr data/precision/gate_verify_eustathius_*/",
        },
    },
    # Reverting is not the mirror image of applying. A record names one misread
    # token and the rater judges that one occurrence, but the revert substitutes
    # whole-token across the row, so where the scan read the corrected form
    # correctly somewhere else in the same row the revert wrote the misreading
    # over it. Applying cannot do this: the misreading stands only where it is
    # wrong. Swept over every revert audit on 2026-09-11 and repaired against the
    # pre-apply text the corpus history holds, so these are restorations of what
    # the scan says, not new corrections.
    "repaired_over_reverts": {
        "rows": 1214,
        "tokens": 3064,
        "works": 131,
        "passes": 17,
        "what": ("tokens a revert overwrote although no correction had ever "
                 "made them. 1,047 of the rows come from the wholesale "
                 "llm/accepted revert of 2026-08-02 and the rest from the gated "
                 "census payouts; the worst single row had eleven ordinary "
                 "\u03ba\u03b1\u1f76 rewritten as \u039a\u1f22. No correction record "
                 "changed, because these are positions no record named"),
        "evidence": ("data/corrections/over_revert_repair_2026-09-11*.json in "
                     "the upstream pipeline, each carrying the row before and "
                     "after and the commit the fix was applied at"),
    },
    # Re-measured 2026-09-11 by the upstream scripts/measure_overlay_reach.py, which
    # is the first thing that could rebuild them: the previous trio was a 2026-08-03
    # hand count, and all three were the counter lines of one retirement run rather
    # than three measurements. `present` is the record's corrected form standing as a
    # whole Greek token in the row its OWN key names, with no carve routing, which is
    # the definition the README argues; the records a carve moved are accounted for
    # separately in overlay_reach below.
    "corrections_present": 121593,
    "corrections_present_works": 872,
    # Re-baselined to today, not left at the 2026-08-12 figure of 225,125.
    # population_check compares this against the local audit mirror at build time,
    # and a baseline the mirror can never match again reports stale=true forever,
    # which is a check nobody reads. Against today's figure it flags real drift.
    "active_records": 218482,
    "overlay_reach": {
        "what": ("where the active records sit relative to the served text. A "
                 "record keyed to a row a carve moved is not lost: the carve "
                 "audits, or the convention that a carved row keeps its Migne "
                 "page identity, place most of them"),
        "orphans": 96764,
        "placed_on_a_served_row": 72790,
        "accounted_for_but_not_served": 23572,
        "unaccounted": 402,
        "row_found_but_neither_form_standing": 125,
        "caveats": ("`placed` is weaker than `present`: 718 of the placed records "
                    "land on a row that does not carry the correction. 16 of the "
                    "convention placements are undecidable, because a row split at "
                    "a character offset leaves both halves carrying the form. The "
                    "23,572 point at text this corpus keeps but does not serve as "
                    "the primary reading: a second witness under "
                    "data/corpus_secondary, a leaf dropped as a repeat of another "
                    "with the audit naming the twin that kept it, Migne's apparatus "
                    "in data/paratext, or a row an audit archived verbatim"),
        "tool": "scripts/measure_overlay_reach.py in the upstream pipeline",
    },
    # The raw-OCR share above is an upper bound, and this is by how much. A work is
    # classed from its rows' `corrections` stamps, and a correction stamps the row it
    # edits before a carve moves that row into a per-work file, where nothing
    # re-stamps it. The stamps are deliberately NOT repaired to match: a corrected
    # form standing in a row is equally consistent with the corrector having written
    # it and with the scan having read it right all along, so stamping on presence
    # would invent provenance. restamp_rows.py is drop-only for the same reason.
    "stamp_gap": {
        "pairs": 49303,
        "works_affected": 264,
        "works_under_the_floor_only_because_of_it": 28,
        "raw_share_lower_bound": 0.0556,
        "raw_share_tokens_in_doubt": 564081,
        "what": ("row-and-method pairs where an active correction is standing in the "
                 "served row and the row carries no stamp for the method that made "
                 "it. pseudo-zonaras.lexicon reads 0.45% of its rows stamped against "
                 "2.65% from the standing corrections, and ten works read zero where "
                 "every row is corrected. Taking the 25 of those works still classed "
                 "raw at their word puts the raw-OCR share between 5.6% and the "
                 "published 6.4%, 564,081 tokens apart"),
        "tool": "scripts/measure_stamp_gap.py in the upstream pipeline",
    },
    "rater_disagreement": 0.055,
    "rater_kappa": 0.78,
    "caveats": [
        "Sampling stratifies by route and reweights to the overlay, so the "
        "corpus figure is not the sample average: freq/accepted holds 85,451 "
        "records and agent/accepted 1,376, and both were sampled to the same "
        "depth.",
        "6.0% of items are neither sound nor wrong but a split or unsure "
        "reading, and are reported as their own band rather than rounded into "
        "either side.",
        "The two raters disagree on 5.5% of items, so no figure here is finer "
        "than a few points.",
        "The estimate counts corrections that are wrong, not OCR errors that "
        "survive: a raw-OCR work has had no correction pass at all and none of "
        "these rates say anything about it.",
        "llm/accepted's 53.6% is the 2,522 records that survived the August "
        "2026 wholesale revert. All 2,114 of them still resolvable were then "
        "read individually and the 868 both raters called wrong were reverted, "
        "leaving 1,654 applied.",
        "prosodia/accepted (682 records) and engine/accepted (4) were below "
        "the sampling floor and are not covered by any figure here.",
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
    ap.add_argument("--check", action="store_true",
                    help="compare the stored release against the corpus as it "
                         "is now and exit non-zero if it no longer describes "
                         "it; writes nothing")
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

    if args.check:
        # For use BEFORE cutting a tag, and deliberately not part of `make`.
        # Drift here is the normal state between releases: the record describes
        # the last one and the corpus moves on, so a build that failed on it
        # would be red permanently and teach everyone to ignore it. What it
        # answers is the release-time question, whether the stored record still
        # describes the corpus you are about to tag. It does not regenerate,
        # because minting a release id is a decision, not a build step.
        if not args.out.exists():
            print(f"no {shown(args.out)}; nothing to check", file=sys.stderr)
            raise SystemExit(0)
        stored = json.loads(args.out.read_text(encoding="utf-8"))
        drift = []
        for path in (("pin", "corpus_sha256"), ("corpus", "tokens"),
                     ("corpus", "works")):
            was, now = stored, release
            for k in path:
                was = (was or {}).get(k)
                now = (now or {}).get(k)
            if was != now:
                drift.append(f"{'.'.join(path)}: record {was}, corpus now {now}")
        if drift:
            print(f"{shown(args.out)} no longer describes the served corpus:",
                  file=sys.stderr)
            for d in drift:
                print(f"    {d}", file=sys.stderr)
            print(f"  It describes release {stored.get('release_id')}. If you "
                  f"are about to cut a tag, rerun without --check and with the "
                  f"date you mean, so the record describes what you are "
                  f"tagging. Between releases this is expected.",
                  file=sys.stderr)
            raise SystemExit(1)
        print(f"{shown(args.out)} still describes the served corpus "
              f"({stored.get('release_id')})")
        raise SystemExit(0)

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
