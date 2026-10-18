"""Display variants never become ordinary attestations or join across gaps."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_ocr_quality_report as quality
import build_public_corpus as public
import build_work_lemma_counts as matrix
import measure_nonfinal_graves as graves
import reconcile_corpus_editions as editions
from frequency_projection import FrequencyProjection
from ocr_consensus import merge_witnesses


def corpus_fixture(tmp_path):
    data = tmp_path / "data"
    corpus = data / "corpus"
    corpus.mkdir(parents=True)
    witnesses = [{"id": str(i), "text": text,
                  "artifact_sha256": hashlib.sha256(text.encode()).hexdigest()}
                 for i, text in enumerate(["λόγος μὴτε σοφός", "λόγος μήτε σοφός"])]
    merged = {"urn": "merged", "locus": "1", "source": "first1k",
              "edition": "merged", "license": "CC0", **merge_witnesses(witnesses)}
    critical = {"urn": "papyrus", "locus": "1", "source": "dclp",
        "edition": "critical", "license": "CC0", "text": "βίος [ἀνθρώπου]",
        "analysis_text": "βίος", "critical_markup": {"schema": "epidoc-spans-v1"},
        "reading_text": "βίος ἀνθρώπου", "tokens": [
            {"form": "βίος", "start": 0, "end": 4, "lexical_eligible": True},
            {"form": "ἀνθρώπου", "start": 5, "end": 13, "lexical_eligible": False}]}
    raw = {"urn": "raw", "locus": "1", "source": "ocr", "edition": "scan",
           "license": "CC0", "text": "μὴτε λόγος"}
    for row in [merged, critical, raw]:
        (corpus / f"{row['urn']}.jsonl").write_text(json.dumps(row, ensure_ascii=False) + "\n")
    return data, [merged, critical, raw]


def test_export_totals_keep_surface_and_analysis_counts_distinct(tmp_path, monkeypatch):
    data, rows = corpus_fixture(tmp_path)
    monkeypatch.setattr(public, "DATA", data)
    monkeypatch.setattr(public, "CORPUS", data / "corpus")
    public.main()
    coverage = json.loads((data / "coverage.json").read_text())
    assert coverage["merged"]["tokens"] == 4
    assert coverage["merged"]["analysis_tokens"] == 2
    assert coverage["papyrus"]["tokens"] == 2
    assert coverage["papyrus"]["analysis_tokens"] == 1
    monkeypatch.setattr(editions, "CORPUS", data / "corpus")
    monkeypatch.setattr(editions, "CE", data / "corpus_editions.json")
    monkeypatch.setattr(editions, "WORK_IDS", data / "work_ids.json")
    editions.main()
    ce = json.loads((data / "corpus_editions.json").read_text())
    assert ce["merged"]["n_tokens"] == 4  # historical whitespace-group unit
    assert ce["merged"]["n_analysis_tokens"] == 2
    projection = FrequencyProjection(data)
    for row in rows:
        counts = matrix.tokenize_file(data / "corpus" / f"{row['urn']}.jsonl", projection)
        assert sum(counts[row["urn"]].values()) == coverage[row["urn"]]["analysis_tokens"]


def test_quality_attestation_and_denominator_exclude_display_alternatives(tmp_path, monkeypatch):
    data, rows = corpus_fixture(tmp_path)
    monkeypatch.setattr(quality, "CORPUS", data / "corpus")
    ce = {row["urn"]: {"source": row["source"]} for row in rows}
    projection = FrequencyProjection(data)
    attested, stats = quality.build_attestation(ce, projection)
    assert attested == {"λόγος", "σοφός", "βίος"}
    assert stats["n_token_occurrences"] == 3
    result = quality.unattested_stats(rows, attested, projection)
    assert result["n_surface_tokens"] == 8
    assert result["n_tokens"] == 5
    assert result["n_unattested"] == 1  # real raw μὴτε, not the displayed tie


def test_bigram_quality_does_not_join_neighbors_across_exclusions(tmp_path):
    data, rows = corpus_fixture(tmp_path)
    projection = FrequencyProjection(data)
    assert quality.work_bigrams(rows[:2], projection) == Counter()
    assert quality.work_bigrams(rows[2:], projection) == {("μητε", "λογοσ"): 1}
    opaque = {"text": "λόγος ⟦μὴτε ∥ μήτε⟧ σοφός", "analysis_text": "λόγος σοφός"}
    assert quality.work_bigrams([opaque], projection) == Counter()


def test_nonfinal_grave_measurement_matches_eligible_work_totals(tmp_path, monkeypatch):
    data, rows = corpus_fixture(tmp_path)
    monkeypatch.setattr(graves, "REPO", tmp_path)
    monkeypatch.setattr(graves, "DATA", data)
    for constant, name in [("OUT", "nonfinal_graves.json"), ("SHEET", "sheet.json"),
            ("MARK_SHEET", "marks.json"), ("THIRD_SHEET", "third.json")]:
        monkeypatch.setattr(graves, constant, data / name)
    monkeypatch.setattr(sys, "argv", ["measure_nonfinal_graves.py", "--write"])
    graves.main()
    report = json.loads((data / "nonfinal_graves.json").read_text())
    assert report["served_tokens"] == 5
    assert report["surface_served_tokens"] == 8
    assert report["tokens"] == 1
    assert report["works_touched"] == 1
    assert report["by_source"] == [{"source": "ocr", "tokens": 1, "rate": 0.5}]


def test_collated_bigrams_keep_only_original_adjacent_agreement(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "frequency_projection.json").write_text(json.dumps({
        "source_sha256": {}, "rows": {"w:1": [[0, 5], [6, 10], [16, 21]]}}))
    projection = FrequencyProjection(data)
    row = {"urn": "w", "locus": "1", "text": "λόγος βίος μήτε σοφός"}
    assert projection.segments(row) == ["λόγος βίος", "σοφός"]
    assert quality.work_bigrams([row], projection) == {("λογοσ", "βιοσ"): 1}


def test_critical_gap_breaks_adjacency_even_between_certain_tokens(tmp_path):
    row = {"text": "λόγος … βίος", "analysis_text": "λόγος βίος",
        "critical_markup": {"schema": "epidoc-spans-v1"},
        "reading_text": "λόγος … βίος", "tokens": [
            {"form": "λόγος", "start": 0, "end": 5, "lexical_eligible": True},
            {"form": "βίος", "start": 8, "end": 12, "lexical_eligible": True}]}
    assert quality.work_bigrams([row], FrequencyProjection(tmp_path)) == Counter()


def test_attestation_uses_row_sources_when_a_work_contains_mixed_editions(tmp_path, monkeypatch):
    data = tmp_path / "data"
    (data / "corpus").mkdir(parents=True)
    for slug in ["mostly-clean", "mostly-ocr"]:
        (data / "corpus" / f"{slug}.jsonl").write_text("\n".join(json.dumps(row) for row in [
            {"source": "first1k", "text": "βίος"},
            {"source": "ocr", "text": "μὴτε"},
            {"source": "ocr-masked", "text": "ἀνθρώπου"}]))
    monkeypatch.setattr(quality, "CORPUS", data / "corpus")
    attested, stats = quality.build_attestation({
        "mostly-clean": {"source": "first1k"}, "mostly-ocr": {"source": "ocr"}},
        FrequencyProjection(data))
    assert attested == {"βίος"}
    assert stats["n_works"] == 2
    assert stats["n_token_occurrences"] == 2
