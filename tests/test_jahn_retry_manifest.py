"""Enlarged retries retain the original page request and reading order."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_jahn_aristides as jahn


def test_page81_retry_pins_original_and_preserves_nonoverlapping_body_strips(tmp_path, monkeypatch):
    monkeypatch.setattr(jahn, "ROOT", tmp_path)
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(b"pinned scan")
    monkeypatch.setattr(jahn, "SOURCE_SHA256", hashlib.sha256(pdf.read_bytes()).hexdigest())
    original = tmp_path / "data/ingest_reviews/original.json"
    original.parent.mkdir(parents=True)
    original.write_text(json.dumps({"sources": {"jahn": {"license": "PD"}}, "pages": [
        {"id": "page81", "scan_page": 81, "printed_page": 8, "book": 1,
         "source": "jahn", "region": [.04, .04, .95, .92], "max_side": 2600}]}))
    before = original.read_bytes()
    result = jahn.prepare_page81_retry(pdf, original.with_name("retry.json"), original)
    assert original.read_bytes() == before
    assert result["retry_of"]["sha256"] == hashlib.sha256(before).hexdigest()
    assert result["retry_of"]["path"] == "data/ingest_reviews/original.json"
    strips = result["pages"]
    assert [s["reading_order"] for s in strips] == [1, 2, 3]
    assert all(s["reconstructs"] == "page81" and s["max_side"] > 2600 for s in strips)
    assert strips[0]["region"][3] == strips[1]["region"][1]
    assert strips[1]["region"][3] == strips[2]["region"][1]
    pdf.write_bytes(b"different scan")
    with pytest.raises(ValueError, match="differs"):
        jahn.prepare_page81_retry(pdf, original.with_name("retry.json"), original)
