"""Exact scan exclusions preserve body, historical citations, and old replays."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_photius_apparatus as repair
import repair_photius_index as index
import audit_photius_apparatus as historical_audit
import build_work_index
from frequency_projection import FrequencyProjection, lexical_text


def fixture_review(tmp_path):
    original = index.input_bytes(ROOT)
    corpus = tmp_path / index.CORPUS
    corpus.parent.mkdir(parents=True, exist_ok=True)
    corpus.write_bytes(original)
    aliases = tmp_path / index.ALIASES
    aliases.parent.mkdir(parents=True, exist_ok=True)
    aliases.write_bytes(repair.encode({"aliases": {}}))
    index.apply(tmp_path)
    body, historical = repair._historical(tmp_path)
    # A later coverage row is outside the original historical manifestation.
    fresh = {"urn": index.SLUG, "locus": "photius_bekker1824_0013.1", "text": "νεώτερον σῶμα",
             "analysis_text": "νεώτερον σῶμα", "source": "fixture", "ocr_consensus": {"witnesses": [{"text": "νεώτερον"}]}}
    with corpus.open("ab") as stream:
        stream.write(repair.jsonl([fresh]))
    pages = {}
    mixed = "helladius_chrestomathia_photius_bekker_v2_0069.39"
    for locus, row in historical.items():
        match = index.PAGE.fullmatch(locus)
        number = int(match[1])
        page = pages.setdefault(number, {"scan_page": number, "printed_page": number + 265,
            "source_pdf_sha256": repair.SOURCE_SHA, "source_url": repair.SOURCE_URL,
            "reviewed_at": "2026-10-18", "evidence": "Synthetic test authority, not a production classification.", "rows": []})
        exclusions = []
        if number == 69 and 40 <= int(match[2]) <= 49:
            exclusions = [{"start": 0, "end": len(row["text"]), "original_text": row["text"],
                           "classification": "critical-apparatus", "source_region": [.05, .7, .95, .95]}]
        elif locus == mixed:
            # This deliberately synthetic interior exclusion tests that words on
            # either side never become an invented adjacent bigram.
            start, end = row["text"].index("λαμπρὰ"), row["text"].index("ἦν")
            exclusions = [{"start": start, "end": end, "original_text": row["text"][start:end],
                           "classification": "ocr_markup", "source_region": [.1, .3, .5, .4]}]
        page["rows"].append({"locus": locus, "full_row_text": row["text"],
                             "row_sha256": repair.row_sha(row), "exclusions": exclusions})
    review = {"schema_version": 1, "work": index.SLUG, "kind": "source-reviewed-apparatus-exclusions",
              "source": {"url": repair.SOURCE_URL, "sha256": repair.SOURCE_SHA},
              "historical_body_sha256": repair.sha(body), "reviewed_at": "2026-10-18", "pages": list(pages.values())}
    target = tmp_path / repair.REVIEW
    target.parent.mkdir(parents=True)
    target.write_bytes(repair.encode(review))
    return review, mixed, fresh


def test_source_layer_moves_pure_notes_preserves_mixed_body_and_exact_reversal(tmp_path, monkeypatch):
    review, mixed, fresh = fixture_review(tmp_path)
    before = (tmp_path / index.CORPUS).read_bytes()
    aliases_before = (tmp_path / index.ALIASES).read_bytes()
    old_audit = historical_audit.build(tmp_path)
    artifacts, report = repair.build(tmp_path)
    assert report["counts"]["reviewed_pages"] == 236
    assert report["counts"]["reviewed_historical_rows"] == 3846
    assert report["counts"]["moved_rows"] == 10 and report["counts"]["mixed_rows"] == 1
    assert report["counts"]["primary_rows_after"] == 3837
    repair.apply(tmp_path)
    rows = {row["locus"]: row for row in map(json.loads, (tmp_path / index.CORPUS).read_bytes().splitlines())}
    assert rows[fresh["locus"]] == fresh
    assert rows[mixed]["editorial_layer"]["original_text"] in before.decode()
    expected_body = repair.retain_spans(rows[mixed]["editorial_layer"]["original_text"], rows[mixed]["editorial_layer"]["excluded_spans"])
    assert rows[mixed]["editorial_layer"]["body_spans"] == expected_body
    assert rows[mixed]["text"] == "\n".join(span["text"] for span in expected_body)
    assert lexical_text(rows[mixed]) == rows[mixed]["text"]
    projection = FrequencyProjection(tmp_path / "data")
    assert projection.segments(rows[mixed]) == [span["text"] for span in expected_body]
    assert len(projection.segments(rows[mixed])) == 2
    assert projection.contextual_text(rows[mixed]) is None
    notes = {row["locus"]: row for row in map(json.loads, (tmp_path / repair.PARATEXT).read_bytes().splitlines())}
    old = "helladius_chrestomathia_photius_bekker_v2_0069.40"
    aliases = json.loads((tmp_path / index.ALIASES).read_bytes())["aliases"]
    monkeypatch.setattr(build_work_index, "REPO", tmp_path)
    build_work_index.validate_passage_aliases(aliases, {index.SLUG: {}})
    resolved = build_work_index.resolve_citation({"works": {index.SLUG: {}}, "passage_aliases": aliases}, index.SLUG, old)
    assert resolved == {"path": repair.PARATEXT.as_posix(), "locus": old}
    assert old not in rows and notes[old]["full_row_text"] == notes[old]["text"]
    assert notes[mixed]["editorial_spans"] == rows[mixed]["editorial_layer"]["excluded_spans"]
    assert repair.restore_legacy_bytes((tmp_path / index.CORPUS).read_bytes(), tmp_path) == before
    assert historical_audit.build(tmp_path) == old_audit
    index.check(tmp_path)
    repair.check(tmp_path)
    assert repair.active_metadata(tmp_path)["counts"] == report["counts"]
    assert repair.build(tmp_path) == (artifacts, report)
    repair.undo(tmp_path)
    assert (tmp_path / index.CORPUS).read_bytes() == before
    assert (tmp_path / index.ALIASES).read_bytes() == aliases_before
    assert not (tmp_path / repair.PARATEXT).exists()
    assert repair.active_metadata(tmp_path) is None
    assert repair.restore_legacy_bytes(before, tmp_path) == before
    assert (tmp_path / repair.AUDIT).exists()  # The correction trail remains.


@pytest.mark.parametrize("change", ["missing-page", "missing-row", "row-sha", "full-text", "offset", "span-text",
                                    "overlap", "classification", "bbox", "nan", "source", "lower-bound"])
def test_unreviewed_or_changed_source_decisions_fail_closed(tmp_path, change):
    review, _, _ = fixture_review(tmp_path)
    page = next(p for p in review["pages"] if p["scan_page"] == 69)
    row = next(r for r in page["rows"] if r["locus"].endswith(".40"))
    span = row["exclusions"][0]
    if change == "missing-page": review["pages"].pop()
    elif change == "missing-row": page["rows"].pop()
    elif change == "row-sha": row["row_sha256"] = "0" * 64
    elif change == "full-text": row["full_row_text"] += "νέον"
    elif change == "offset": span["end"] += 1
    elif change == "span-text": span["original_text"] = "unreviewed"
    elif change == "overlap": row["exclusions"].append(copy.deepcopy(span))
    elif change == "classification": span["classification"] = "guessed-body"
    elif change == "bbox": span["source_region"] = [0, 0, 2, 1]
    elif change == "nan": span["source_region"][0] = float("nan")
    elif change == "source": page["source_pdf_sha256"] = "0" * 64
    else: row["exclusions"] = []
    (tmp_path / repair.REVIEW).write_bytes(repair.encode(review))
    with pytest.raises(ValueError):
        repair.build(tmp_path)


@pytest.mark.parametrize("target", [index.CORPUS, index.ALIASES, repair.PARATEXT, repair.AUDIT,
                                    repair.ARCHIVE / "source-review.json", repair.ARCHIVE / "before-corpus.jsonl.gz"])
def test_old_guards_do_not_accept_edits_outside_the_exact_reviewed_layer(tmp_path, target):
    fixture_review(tmp_path)
    repair.apply(tmp_path)
    changed = tmp_path / target
    raw = changed.read_bytes()
    if target.name.endswith(".gz"):
        changed.write_bytes(gzip.compress(gzip.decompress(raw) + b" ", mtime=0))
    else:
        changed.write_bytes(raw + b" ")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        repair.restore_legacy_bytes((tmp_path / index.CORPUS).read_bytes(), tmp_path)
    with pytest.raises((ValueError, json.JSONDecodeError)):
        repair.undo(tmp_path)


def test_invalidated_published_source_can_be_unapplied_from_the_frozen_archive(tmp_path):
    fixture_review(tmp_path)
    repair.apply(tmp_path)
    before = gzip.decompress((tmp_path / repair.ARCHIVE / "before-corpus.jsonl.gz").read_bytes())
    (tmp_path / repair.REVIEW).write_bytes(b"invalidated")
    with pytest.raises(ValueError, match="invalidated"):
        index.check(tmp_path)
    repair.undo(tmp_path)
    assert (tmp_path / index.CORPUS).read_bytes() == before


def test_frequency_projection_rejects_an_independent_body_projection_edit(tmp_path):
    fixture_review(tmp_path)
    repair.apply(tmp_path)
    row = next(row for row in map(json.loads, (tmp_path / index.CORPUS).read_bytes().splitlines()) if row.get("editorial_layer"))
    row["analysis_text"] += " νόθον"
    with pytest.raises(ValueError, match="retained body spans"):
        lexical_text(row)


def test_registry_credits_current_body_and_separate_editorial_manifestation(tmp_path):
    from test_reviewed_manifestations import photius_fixture, registry
    import reviewed_manifestations as reviewed
    photius_fixture(tmp_path)
    fixture_review(tmp_path)
    with (tmp_path / index.CORPUS).open("ab") as stream:
        for number in range(14, 322):
            stream.write(repair.jsonl([{"urn": index.SLUG, "locus": f"photius_bekker1824_{number:04d}.1",
                                       "text": "νεώτερος λόγος", "source": "synthetic-coverage-fixture"}]))
    path = tmp_path / "data/corpus_changes/photius-bekker-coverage/coverage.json"
    coverage = json.loads(path.read_bytes())
    coverage["new_corpus_sha256"] = repair.sha((tmp_path / index.CORPUS).read_bytes())
    coverage["legacy_source"] = {"url": repair.SOURCE_URL, "sha256": repair.SOURCE_SHA}
    path.write_bytes(repair.encode(coverage))
    frozen_coverage = path.read_bytes()
    repair.apply(tmp_path)
    reg = registry(index.SLUG)
    metadata = reviewed.register_reviewed_manifestations(reg, tmp_path)[index.SLUG]
    work = reg.works[index.SLUG]
    assert work.title == "Unqualified Work title"
    assert work.coverage_composition["components"][0]["passages"] == 3836
    assert work.coverage_composition["editorial_layer"]["counts"]["moved_rows"] == 10
    edition = work.editions[index.SLUG + ".bekker1825-reviewed-editorial-matter"]
    assert edition.storage == "paratext" and not edition.servable and edition.license == "PD"
    assert metadata["coverage_composition"]["editorial_layer"]["audit"]["sha256"] == repair.sha((tmp_path / repair.AUDIT).read_bytes())
    assert path.read_bytes() == frozen_coverage
    with (tmp_path / repair.PARATEXT).open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError):
        reviewed.reviewed_manifestation_metadata(tmp_path)
