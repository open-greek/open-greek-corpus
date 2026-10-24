"""Explicit page identities and asymmetric overlap remain diagnostic evidence."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sweep_duplicate_leaves import find_runs, overlap_diagnostics, page_of, page_units


def test_pg_dotted_marker_run_is_recognized_without_treating_book_citations_as_pages():
    assert page_of("PG073.483") == ("PG073", 483)
    assert page_of("hesychius_masked_0143") == ("hesychius_masked", 143)
    assert page_of("3.2") is None
    assert page_of("PG073.483.1") is None
    hits = [{"file": "data/corpus/cyril.jsonl", "locus_a": f"PG073.{n}",
             "locus_b": f"PG073.{n + 4}", "served": True,
             "tokens_b": 400, "containment": 0.9} for n in range(483, 487)]
    runs = find_runs(hits)
    assert len(runs) == 1
    assert runs[0]["first_page"] == 483 and runs[0]["last_page"] == 486
    assert runs[0]["page_offset"] == 4 and runs[0]["second_copy_pages"] == 4
    assert all(hit["same_item"] and hit["run"] for hit in hits)


def test_partial_prefix_does_not_hide_unique_text_in_the_longer_reading():
    a = "ἄλφα βῆτα γάμμα δέλτα ἕψιλον ζῆτα"
    b = a + " ἦτα θῆτα ἰῶτα κάππα λάμβδα μῦ νῦ ξῖ ὄμικρον"
    result = overlap_diagnostics(a, b)
    assert result["partial_overlap"]
    assert result["bigram_coverage_a"] == 1
    assert result["bigram_coverage_b"] < 0.5
    assert result["ordered_overlap"]["unmatched_tokens_a"] == 0
    assert result["ordered_overlap"]["unmatched_tokens_b"] == 9


def test_reviewed_page_projection_does_not_hide_unrelated_page_pairs():
    rows = [{"source": "ocr", "locus": "hesychius_masked_0142.1", "text": "ἄλφα"},
            {"source": "ocr", "locus": "reviewed-duplicate.hesychius.0150", "text": "βῆτα",
             "edition": "reviewed-duplicate-block-consensus-2026-10",
             "reviewed_duplicate_block": {
                 "authority": "data/corpus_changes/reviewed-duplicate-blocks/changes.json"},
             "ocr_consensus": {"storage": "compact-slots-v1"}},
            {"source": "ocr", "locus": "hesychius_masked_0145.1", "text": "γάμμα"}]
    assert len(page_units(rows)) == 3
    rows[1] = {"source": "ocr", "locus": "3.2", "text": "βῆτα"}
    assert page_units(rows) is None
