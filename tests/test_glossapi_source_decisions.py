"""Policy guards for the pinned GlossAPI historical-source decisions."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "data" / "glossapi_source_decisions.json"
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _load():
    return json.loads(DECISIONS.read_text(encoding="utf-8"))


def test_glossapi_decisions_pin_three_historical_candidates():
    data = _load()
    sources = data["sources"]
    assert {item["key"] for item in sources} == {
        "glossapi_gutenberg_greek",
        "glossapi_ekklisiastika",
        "glossapi_archetai",
    }
    for source in sources:
        assert COMMIT.fullmatch(source["revision"])
        assert SHA256.fullmatch(source["artifact"]["sha256"])
        assert source["artifact"]["size"] > 0
        assert source["required_gates"]
        assert source["admission_output"]


def test_glossapi_decisions_preserve_the_ogc_consumer_boundary():
    data = _load()
    contract = data["consumer_contract"]
    assert contract["direct_glossapi_to_dilemma"] is False
    assert "public_lexicon.tsv" in contract["dilemma_input"]
    assert "release/content hash" in contract["dilemma_input"]

    by_key = {item["key"]: item for item in data["sources"]}
    assert by_key["glossapi_gutenberg_greek"]["decision"] == (
        "hold_for_identity_recovery"
    )
    assert by_key["glossapi_ekklisiastika"]["decision"] == (
        "blocked_pending_underlying_rights_and_identity"
    )
    assert by_key["glossapi_archetai"]["decision"] == "ocr_quarantine"


def test_no_historical_candidate_is_a_direct_frequency_source():
    data = _load()
    assert "No raw GlossAPI historical frequency" in (
        data["consumer_contract"]["frequency_rule"]
    )
    for source in data["sources"]:
        combined = " ".join(source["required_gates"] + [source["admission_output"]])
        assert "deduplic" in combined.lower() or "duplicate" in combined.lower()


def test_ekklisiastika_requires_cleaning_and_cycle_deduplication():
    data = _load()
    source = next(
        item for item in data["sources"]
        if item["key"] == "glossapi_ekklisiastika"
    )
    policy = " ".join(source["required_gates"] + [source["admission_output"]])
    assert "rubric" in policy.lower()
    assert "run-together" in policy.lower()
    assert "oktoechos" in policy.lower()
    assert "n-gram frequency" in policy.lower()
    assert source["source_url"] == "https://glt.goarch.org/#02"
    assert "per-record" in source["source_url_scope"]
    rights = source["underlying_source_rights"]
    assert rights["status"] == "blocked_pending_written_permission"
    assert rights["commercial_redistribution_authorized"] is False
    assert rights["required_attribution"] is None
    assert rights["terms_url"] == "https://www.goarch.org/-/terms-of-use"
