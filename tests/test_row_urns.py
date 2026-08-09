"""A served work's rows must carry its own slug, or the work leaves every join.

build_work_lemma_counts.py and build_provenance.py key their per-work rollups on
the row's `urn`, falling back to the filename only when the field is absent.
Everything else in the repo keys on the slug. When the two disagree the work is
filed under a key no other artifact uses, and a join against the catalog drops
it without erroring: philodemus.tlg1595-tlg601 sat in work_token_totals.json as
`tlg1595.tlg601` with 10,043 lemmatized tokens and nothing under its own slug.
Nothing failed, the work was simply not in the answer.

That is a bad failure to leave to a reader noticing a total is short, so it is
asserted here. The rows are delivered by an upstream pipeline, so a new file can
reintroduce it at any delivery; scripts/align_row_urns_to_slugs.py repairs it.

data/corpus_secondary is deliberately NOT checked. A witness file there is named
<slug>.<witness-kind>.jsonl and its rows correctly carry the urn of the work
they witness, not the filename. Asserting this invariant over that directory
would demand renaming 7,653 rows across 46 files to works that do not exist.
"""

import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"


def test_no_served_row_carries_a_urn_that_is_not_its_slug():
    bad = []
    for fp in sorted(CORPUS.glob("*.jsonl")):
        slug = fp.name[:-len(".jsonl")]
        with open(fp, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                urn = json.loads(line).get("urn")
                if urn and urn != slug:
                    bad.append(f"{fp.name}: urn {urn!r}")
                    break
    assert not bad, ("run scripts/align_row_urns_to_slugs.py --apply; "
                     f"these files would drop out of every catalog join: {bad}")


@pytest.mark.parametrize("slug", ["philodemus.tlg1595-tlg601"])
def test_the_known_case_is_in_the_per_work_totals_under_its_slug(slug):
    """The symptom, not the cause, so the fix is checked where it was felt."""
    totals = json.loads((REPO / "data" / "work_token_totals.json")
                        .read_text(encoding="utf-8"))
    assert slug in totals, f"{slug} is missing from work_token_totals.json"
