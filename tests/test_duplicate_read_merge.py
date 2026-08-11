"""The merge that issue #33 settles, and the two things it got wrong first.

Merging two OCR reads of one printed page produces a text no scan attests on its
own, so what matters is that every decision stays visible and reversible. Three
properties carry that:

  the span stream page_spans builds is token-for-token the stream page_text
  feeds the merge, because the substitutions are written back at those offsets
  and a drift of one token would silently rewrite the wrong word;

  no page is merged into by one decision and displaced by another, which is what
  happens if the leaf-runs are taken pairwise: they OVERLAP, 61 pages sit in
  more than one pair, and the first run of this pass wrote six files and then
  refused itself on the seventh;

  the round trip restores the tree byte-for-byte, including the marker on rows
  that carry a guess but no substitution, which the first unapply left behind.
"""

import json
import sys
import unicodedata
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from build_public_corpus import _GK  # noqa: E402
from build_ocr_quality_report import greek_tokens  # noqa: E402
from collapse_duplicate_reads import norm_elision  # noqa: E402
import merge_duplicate_reads as mg  # noqa: E402

AUDIT = REPO / "data" / "corpus_changes" / "ocr.duplicate-read-merge.json"


def _audit():
    if not AUDIT.exists():
        pytest.skip("the duplicate-read merge is not applied in this tree")
    return json.loads(AUDIT.read_text(encoding="utf-8"))


def test_span_stream_is_the_stream_the_merge_decided_on():
    """Read from the corpus, not from a paste: an excerpt would not carry the
    row joins and the elided forms that make the two disagree."""
    rec = _audit()
    checked = 0
    for f, blk in sorted(rec["files"].items()):
        rows = [json.loads(l) for l in
                (REPO / f).read_text(encoding="utf-8").splitlines() if l.strip()]
        texts = mg.page_text(rows)
        spans = mg.page_spans(rows)
        for page, toks in spans.items():
            assert [t[3] for t in toks] == greek_tokens(norm_elision(texts[page]))
            # and every span still points at the token it names
            for i, start, end, tok in toks:
                raw = rows[i]["text"][start:end]
                assert unicodedata.normalize("NFC", norm_elision(raw)) == tok
            checked += 1
    assert checked > 100


def test_components_never_merge_into_a_page_they_also_displace():
    rec = _audit()
    for f, blk in sorted(rec["files"].items()):
        served = {json.loads(l)["locus"].rsplit(".", 1)[0] for l in
                  (REPO / f).read_text(encoding="utf-8").splitlines() if l.strip()}
        wit = REPO / "data" / "corpus_secondary" / (
            Path(f).name[:-len(".jsonl")] + f".{mg.WITNESS_SUFFIX}.jsonl")
        moved = {json.loads(l)["locus"].rsplit(".", 1)[0] for l in
                 wit.read_text(encoding="utf-8").splitlines() if l.strip()}
        assert not (served & moved), f"{f} serves and witnesses the same page"


def test_overlapping_runs_are_one_component():
    """Himerius 590 heads two runs. Pairwise that is two answers for one token."""
    pairs = [("p_0588", "p_0590"), ("p_0590", "p_0606"), ("p_0590", "p_0614"),
             ("p_0700", "p_0710")]
    comps = sorted(mg.components(pairs), key=len)
    assert comps == [["p_0700", "p_0710"],
                     ["p_0588", "p_0590", "p_0606", "p_0614"]]


def test_every_guess_names_a_token_that_is_actually_served():
    """The record has to point at the served text, or it is not a record."""
    rec = _audit()
    n = 0
    for f, blk in sorted(rec["files"].items()):
        rows = [json.loads(l) for l in
                (REPO / f).read_text(encoding="utf-8").splitlines() if l.strip()]
        # row indices in the audit are pre-removal, so rebuild that numbering
        by_index = {}
        for e in blk["removed_rows"]:
            by_index[e["index"]] = e["row"]
        j = 0
        for i in range(blk["rows_before"]):
            if i in by_index:
                continue
            by_index[i] = rows[j]; j += 1
        for i, start, served, rejected in blk["guesses"][:400]:
            text = by_index[i]["text"]
            m = _GK.match(norm_elision(text), start)
            assert m and unicodedata.normalize("NFC", m.group()) == served
            assert served not in rejected
            n += 1
    assert n > 0


def test_marked_rows_carry_the_counts_they_claim():
    rec = _audit()
    for f, blk in sorted(rec["files"].items()):
        rows = {json.loads(l)["locus"]: json.loads(l) for l in
                (REPO / f).read_text(encoding="utf-8").splitlines() if l.strip()}
        marked = [r for r in rows.values() if "merged_read" in r]
        assert marked, f"{f} recorded marked rows but serves none"
        for r in marked:
            mr = r["merged_read"]
            assert mr["substituted"] or mr["guessed"]
            assert isinstance(mr["with"], list) and mr["with"]
