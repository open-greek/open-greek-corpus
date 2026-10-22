"""Source-role projection retains exact raw text and refuses unreviewed drift."""
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import herodas_body_witness_observations as observations


def fixture(monkeypatch, page, text):
    monkeypatch.setitem(observations.RAW_SHA256, page, observations.sha(text.encode()))
    return observations.project_qwen36(page, text)


def test_projection_uses_literal_offsets_and_covers_every_character(monkeypatch):
    text = "ἄρχη\nσυνέχεια\nλόγος\nλόγος\nΜΗΤΡΙΧΗ\nοὔδ’ εἶς.\nΓΥΛΛΙΣ\nἄκουσον δή\n" + "λόγος\n" * 18 + "ΜΗΤΡΙΧΗ\nτέλος\n"
    result = fixture(monkeypatch, 76, text)
    assert "".join(span["text"] for span in result["spans"]) == text
    assert [span["text"] for span in result["excluded_spans"]] == ["ΜΗΤΡΙΧΗ\n", "ΓΥΛΛΙΣ\n", "ΜΗΤΡΙΧΗ\n"]
    cursor = 0
    for span in result["spans"]:
        assert span["start"] == cursor
        assert text[span["start"]:span["end"]] == span["text"]
        cursor = span["end"]
    assert cursor == len(text)


def test_numbers_are_excluded_by_reviewed_role_without_rewriting_greek(monkeypatch):
    prefixes = observations.LINE_NUMBER_PREFIXES[136]
    lines = [prefixes.get(line, "") + "οἴκεις\n" for line in range(35)]
    text = "".join(lines)
    result = fixture(monkeypatch, 136, text)
    assert [span["text"] for span in result["excluded_spans"]] == list(prefixes.values())
    assert all(span["role"] == "line-number" for span in result["excluded_spans"])
    assert "".join(span["text"] for span in result["authorial_spans"]) == "οἴκεις\n" * 35


def test_four_molpinos_verses_remain_separate_from_title(monkeypatch):
    text = "ΜΟΛΠΙΝΟΣ\nἘπὴν τὸν ἑξήκοστον\nὦ Γρύλλε\nὡς τυφλὸς\nἤδη γὰρ\n"
    result = fixture(monkeypatch, 480, text)
    assert result["excluded_spans"][0]["role"] == "title"
    assert result["authorial_spans"][0]["text"].splitlines() == text.splitlines()[1:]


def test_xi_only_does_not_admit_uncertain_xia_or_source_notes(monkeypatch):
    text = "προσφὺς ὅκως τις χοιράδων ἀνηρίτης.\n...ἐγὼ μέντοι\nκαθεῖλον ἱστούς.\nAth. source note\nXI a. Strabo note\n"
    result = fixture(monkeypatch, 486, text)
    assert [span["text"] for span in result["authorial_spans"]] == [text.splitlines(keepends=True)[0]]
    assert [span["role"] for span in result["excluded_spans"]] == ["unadmitted-XIa", "apparatus"]
    assert "anonymous speech in Strabo" in result["excluded_spans"][0]["reason"]


def test_failed_444_prediction_is_not_a_body_vote(monkeypatch):
    result = fixture(monkeypatch, 444, "τὰ δεινὰ πνεύσαι, λᾶ\npartial prediction\n")
    assert result["authorial_spans"] == [] and result["eligible_for_comparison"] is False
    assert result["excluded_spans"][0]["role"] == "failed-recognition"
    assert "byte-identical" in result["excluded_spans"][0]["reason"]


def test_body_fragments_on_442_are_not_misclassified_as_apparatus(monkeypatch):
    lines = ["ΗΡΩΔΑ [VIII\n"] + ["λόγος\n"] * 26 + ["γρυπ(άνιος)\n", "ῥυπ(αρὸς)\n", "τ(\n", "τ(\n", "24 apparatus\n", "other note\n"]
    result = fixture(monkeypatch, 442, "".join(lines))
    body = "".join(span["text"] for span in result["authorial_spans"])
    assert "γρυπ(άνιος)" in body and "ῥυπ(αρὸς)" in body
    assert "apparatus" not in body
    assert [span["role"] for span in result["excluded_spans"]] == ["running-header", "apparatus"]


@pytest.mark.parametrize("page", [False, 72, "76", 543])
def test_unreviewed_pages_cannot_borrow_another_projection(page):
    with pytest.raises(ValueError, match="No reviewed"):
        observations.project_qwen36(page, "ἄγνωστον")


def test_changed_raw_reading_is_rejected_before_using_boundaries():
    with pytest.raises(ValueError, match="checksum changed"):
        observations.project_qwen36(76, "ἄγνωστον")


def test_reviewed_page_set_and_hashes_are_explicit():
    assert tuple(observations.RAW_SHA256) == observations.MISSING_PAGES
    assert len(observations.MISSING_PAGES) == 22
    assert all(len(digest) == 64 for digest in observations.RAW_SHA256.values())


def test_all_archived_real_predictions_replay_without_losing_characters():
    path = ROOT / "data/corpus_changes/herodas-headlam-knox-body/historical-witnesses.json.gz"
    if not path.exists():
        pytest.skip("The new historical witness archive has not been prepared yet")
    packet = json.loads(gzip.decompress(path.read_bytes()))
    review = observations.build_observations(packet)
    assert len(review["pages"]) == 22
    for result in review["pages"]:
        text = packet["pages"][str(result["page"])]["qwen36"]["files"]["grc"]["text"]
        assert "".join(span["text"] for span in result["spans"]) == text
        assert bool(result["authorial_spans"]) == (result["page"] != 444)
