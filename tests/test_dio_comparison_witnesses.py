import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import dio_comparison_witnesses as comparison


def test_source_identity_license_and_physical_pages_are_pinned(monkeypatch):
    document = {"id": "tlg0385.tlg001.local003", "origin": {"id": "source-library"},
        "license": {"url": comparison.LICENSE_URL}, "sourceCitation": "Cary VII, book123",
        "sourceRights": "Public-domain print; CC BY-SA 4.0 transcription", "revisionDate": "2026-10-07",
        "sections": [{"id": "section6", "label": "Page s6", "children": [],
                      "blocks": [{"type": "paragraph", "text": "λόγος καθαρός"}]}]}
    raw = json.dumps(document).encode()
    monkeypatch.setattr(comparison, "PINS", {document["id"]: {"volume": 7, "book": "book123",
        "json_sha256": hashlib.sha256(raw).hexdigest()}})
    result = comparison.load(blobs=[raw])
    assert result["pages"][(7, 6)]["license"] == "CC-BY-SA-4.0"
    assert result["originals"][document["id"]] == raw
    assert result["sources"][document["id"]]["separate_api_notice"]["tdm_reservation"] == 1
    with pytest.raises(ValueError, match="changed"):
        comparison.load(blobs=[raw + b" "])
    with pytest.raises(ValueError, match="repeated"):
        comparison.load(blobs=[raw, raw])


def test_only_reviewed_later_volumes_have_comparison_pins():
    assert {value["volume"] for value in comparison.PINS.values()} == {7, 8, 9}
    assert all(value["json_sha256"] and value["book_metadata_receipt_sha256"]
               and value["api_quote_receipt_sha256"] for value in comparison.PINS.values())
