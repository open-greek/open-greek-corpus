"""Source roles preserve dialogue, exclude editorial text, and cover every byte."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import herodas_source_observations as source


@pytest.fixture
def packet(monkeypatch):
    rows = [
        {"urn": source.WORK, "locus": "herodas_hk_0180.3", "text": "Οὕτω βόσκειν 6 χαλκίνδα P. supplied by R."},
        {"urn": source.WORK, "locus": "herodas_hk_0182.1", "text": "μήλασσον αὐτῷ— # ΛΑΜΠΡΙΣΚΟΣ # Μητροτίμη, μὴ ἐπεύχεο. 33 πθι P. 34 αὖρευ P."},
        {"urn": source.WORK, "locus": "herodas_hk_0346.1", "text": "ΜΗΤΡΩ Νοσσὶς εἶχεν."},
    ]
    monkeypatch.setattr(source, "ROW_ROLES", {row["locus"]: "M" for row in rows})
    monkeypatch.setattr(source, "INPUT_TEXTS_SHA256", source._texts_digest(rows))
    raw = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()
    monkeypatch.setattr(source, "INPUT_CORPUS_SHA256", hashlib.sha256(raw).hexdigest())
    return source.build_source_review(rows, "2026-10-22T03:00:00Z")


def test_all_existing_rows_have_explicit_source_assignments():
    assert len(source.ROW_ROLES) == 136
    assert len(source.PAGE_ROLES) == 21
    assert source.ROW_ROLES["herodas_hk_0472.4"] == "A"
    assert source.ROW_ROLES["herodas_hk_0472.5"] == "A"
    assert source.ROW_ROLES["herodas_hk_0472.6"] == "E"
    assert source.ROW_ROLES["herodas_hk_0477.1"] == "C"


def test_mixed_rows_preserve_literal_dialogue_and_separate_editorial_spans(packet):
    source.validate_source_review(packet)
    for row in packet["rows"]:
        assert "".join(span["text"] for span in row["spans"]) == row["original_text"]
        assert all(span["lexical_eligible"] == (span["role"] == "authorial") for span in row["spans"])
    row = packet["rows"][1]
    assert [s["role"] for s in row["spans"]] == ["authorial", "speaker", "authorial", "apparatus"]
    assert row["spans"][1]["text"] == " # ΛΑΜΠΡΙΣΚΟΣ # "
    assert row["spans"][2]["text"] == "Μητροτίμη, μὴ ἐπεύχεο."


def test_reading_and_complete_row_identity_cannot_be_replaced(packet):
    changed = deepcopy(packet)
    changed["rows"][0]["original_text"] = "A different reading"
    with pytest.raises(ValueError, match="preimages changed"):
        source.validate_source_review(changed)
    changed = deepcopy(packet)
    changed["rows"].pop()
    with pytest.raises(ValueError, match="accounting or preimages changed"):
        source.validate_source_review(changed)


@pytest.mark.parametrize("field,value", [("end", 2), ("start", 1), ("text", "replacement"), ("lexical_eligible", False), ("role", "commentary")])
def test_offsets_readings_and_admission_are_frozen(packet, field, value):
    packet["rows"][0]["spans"][0][field] = value
    with pytest.raises(ValueError, match="role or literal boundary changed"):
        source.validate_source_review(packet)


def test_duplicate_or_missing_mixed_boundary_is_rejected():
    with pytest.raises(ValueError, match="missing or repeated"):
        source._spans("herodas_hk_0180.3", "Dialogue without the reviewed apparatus")
    with pytest.raises(ValueError, match="missing or repeated"):
        source._spans("herodas_hk_0180.3", "Verse 6 χαλκίνδα P. 6 χαλκίνδα P.")


def test_time_zone_and_source_pin_are_required(packet, tmp_path):
    packet["reviewed_at"] = "2026-10-22T03:00:00"
    with pytest.raises(ValueError, match="time zone"):
        source.validate_source_review(packet)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"another PDF")
    with pytest.raises(ValueError, match="source scan changed"):
        source.verify_source_pdf(pdf)


def test_role_review_keeps_supplies_and_attribution_qualified():
    assert "bracketed supplies" in source.QUALIFICATION
    assert "not a full Herodas text" in source.QUALIFICATION
    row = source._reviewed_row({"locus": "herodas_hk_0472.3", "text": "Dialogue [existing supply]"})
    assert row["spans"][0]["text"] == "Dialogue [existing supply]"
    assert "not a certification" in row["qualification"]
