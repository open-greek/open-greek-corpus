"""Duplicate citations and inactive admissions preserve exact alias stages."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import prepare_photius_review_campaign as campaign
import repair_photius_complete_review as layer
import repair_photius_historical_readings as historical
import build_work_index


PREFIX = "helladius_chrestomathia_photius_bekker_v2_"
PAIRS = {PREFIX + "0094.2": PREFIX + "0094.1", PREFIX + "0231.6": PREFIX + "0231.7"}


@pytest.fixture
def authority():
    rows = [{"urn": "photius.bibliotheca", "locus": PREFIX + suffix,
             "text": text, "source": "ocr", "prior_audit": {"readings": [text, "ἄλλο"]}}
            for suffix, text in [("0094.1", "ὁ λόγος"), ("0094.2", "ὁ λόγος"),
                                 ("0231.6", "ΚΕΦΑΛΑΙΟΝ"), ("0231.7", "ΚΕΦΑΛΑΙΟΝ")]]
    before = b"".join(campaign.canonical(row) + b"\n" for row in rows)
    records = []
    for row in rows:
        corrected = "" if row["locus"] in PAIRS else row["text"]
        record = {"locus": row["locus"], "original_row_sha256": campaign.row_sha(row),
            "complete": True, "complete_scan_review": True, "status": "reviewed-verified",
            "digital_counterparts_usable": False, "original_text": row["text"],
            "original_text_sha256": campaign.sha(row["text"].encode()),
            "corrected_text": corrected, "corrected_text_sha256": campaign.sha(corrected.encode()),
            "segments": [{"start": 0, "end": len(row["text"]), "original_text": row["text"],
                "corrected_text": corrected, "corrected_start": 0, "corrected_end": len(corrected),
                "verification": "verified", "readings": []}],
            "additional_lexical_exclusions": [], "uncertainty_exclusion_candidates": [],
            "nonbody_exclusion_candidates": []}
        if row["locus"] in PAIRS:
            record["duplicate_of"] = PAIRS[row["locus"]]
        records.append(record)
    review = {"schema": campaign.COMPILED_SCHEMA, "scope_complete": True,
        "admission_authorized": False, "campaign_id": "complete-review-test",
        "input_pins": {"corpus": {"sha256": campaign.sha(before)}},
        "counts": {"complete_scan_review_rows": len(rows), "passages": len(rows)},
        "source_library_credit": {}, "rows": records}
    aliases = b'{\n "schema_version": 1, "aliases": {"other.work": {"old": {"locus": "retained"}}}\n}\n'
    return before, review, aliases


def save(root, authority):
    before, review, aliases = authority
    outputs, audit = layer.artifacts(before, campaign.encode(review), aliases)
    for path, raw in {campaign.BASELINE: gzip.compress(before, mtime=0), **outputs}.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(raw)
    return outputs, audit


def test_duplicate_tombstones_keep_scope_and_prior_audits_with_checked_aliases(authority, tmp_path):
    outputs, audit = save(tmp_path, authority)
    rows = {row["locus"]: row for row in map(json.loads, outputs[campaign.CORPUS].splitlines())}
    assert len(rows) == audit["counts"]["fully_source_reviewed_rows"] == 4
    aliases = json.loads(outputs[layer.ALIASES])["aliases"]
    assert aliases["other.work"] == json.loads(authority[2])["aliases"]["other.work"]
    for source, target in PAIRS.items():
        row = rows[source]
        assert row["text"] == row["analysis_text"] == ""
        assert row["complete_source_review"]["disposition"] == "duplicate-citation-tombstone"
        assert row["complete_source_review"]["duplicate_of"] == target
        assert row["prior_audit"] == layer.restore_before_row(row, tmp_path)["prior_audit"]
        assert aliases["photius.bibliotheca"][source] == {
            "path": campaign.CORPUS.as_posix(), "slug": "photius.bibliotheca", "locus": target}
        disposition = next(d for d in audit["duplicate_dispositions"] if d["locus"] == source)
        assert disposition["canonical_row_sha256"] == campaign.row_sha(rows[target])
        assert disposition["tombstone_row_sha256"] == campaign.row_sha(row)
        assert layer.lexical_segments(row, tmp_path) == [""]


def test_alias_preimages_restore_without_live_sources_and_inactive_metadata_is_unavailable(authority, tmp_path, monkeypatch):
    outputs, audit = save(tmp_path, authority)
    assert layer.active_metadata(tmp_path)["duplicate_dispositions"] == audit["duplicate_dispositions"]
    assert layer.restore_before_alias_bytes(outputs[layer.ALIASES], tmp_path) == authority[2]
    assert layer.restore_before_alias_bytes(authority[2], tmp_path) == authority[2]
    layer.undo(tmp_path)
    assert (tmp_path / campaign.CORPUS).read_bytes() == authority[0]
    assert (tmp_path / layer.ALIASES).read_bytes() == authority[2]
    assert layer.active_metadata(tmp_path) is None
    # The check still verifies all frozen artifacts when the layer is inactive.
    monkeypatch.setattr(layer, "build", lambda root: (outputs, audit))
    assert layer.check(tmp_path) is None


@pytest.mark.parametrize("mutation", ["alias-only", "corpus-only", "unrelated-alias", "unrelated-corpus"])
def test_inactive_baseline_requires_one_exact_corpus_and_alias_stage(authority, tmp_path, mutation):
    outputs, _ = save(tmp_path, authority)
    if mutation == "alias-only":
        (tmp_path / layer.ALIASES).write_bytes(authority[2])
    elif mutation == "corpus-only":
        (tmp_path / campaign.CORPUS).write_bytes(authority[0])
    elif mutation == "unrelated-alias":
        (tmp_path / layer.ALIASES).write_bytes(outputs[layer.ALIASES] + b"\n")
    else:
        (tmp_path / campaign.CORPUS).write_bytes(outputs[campaign.CORPUS] + b"\n")
    with pytest.raises(ValueError, match="frozen admission"):
        layer.active_metadata(tmp_path)
    with pytest.raises(ValueError, match="reversible stage"):
        layer.undo(tmp_path)


@pytest.mark.parametrize("mutation", ["unknown-target", "self-target", "target-tombstone", "missing-disposition", "nonempty-tombstone"])
def test_admission_refuses_unchecked_or_ambiguous_duplicate_destinations(authority, mutation):
    before, original, aliases = authority
    review = deepcopy(original)
    duplicate = review["rows"][1]
    if mutation == "unknown-target":
        duplicate["duplicate_of"] = PREFIX + "0999.1"
    elif mutation == "self-target":
        duplicate["duplicate_of"] = duplicate["locus"]
    elif mutation == "target-tombstone":
        duplicate["duplicate_of"] = PREFIX + "0231.6"
    elif mutation == "missing-disposition":
        duplicate.pop("duplicate_of")
    else:
        duplicate["segments"][0]["corrected_text"] = duplicate["original_text"]
        duplicate["corrected_text"] = duplicate["original_text"]
        duplicate["corrected_text_sha256"] = duplicate["original_text_sha256"]
    with pytest.raises(ValueError, match="duplicate|empty"):
        layer.artifacts(before, campaign.encode(review), aliases)


def test_existing_independent_alias_cannot_be_overwritten(authority):
    before, review, raw = authority
    aliases = json.loads(raw)
    aliases["aliases"]["photius.bibliotheca"] = {next(iter(PAIRS)): {"locus": "elsewhere"}}
    with pytest.raises(ValueError, match="already points elsewhere"):
        layer.artifacts(before, campaign.encode(review), campaign.encode(aliases))


@pytest.mark.parametrize("role", ["editorial-note", "marginal-reference"])
def test_nonbody_tombstones_preserve_their_own_citations_without_invented_body_aliases(authority, tmp_path, role):
    before, original, aliases = authority
    review = deepcopy(original)
    nonbody = review["rows"][1]
    nonbody.pop("duplicate_of")
    nonbody["segments"][0]["text_role"] = role
    outputs, audit = save(tmp_path, (before, review, aliases))
    row = next(r for r in map(json.loads, outputs[campaign.CORPUS].splitlines()) if r["locus"] == nonbody["locus"])
    assert row["text"] == row["analysis_text"] == ""
    assert row["complete_source_review"]["disposition"] == "nonbody-citation-tombstone"
    assert row["locus"] not in json.loads(outputs[layer.ALIASES])["aliases"]["photius.bibliotheca"]
    assert len(audit["duplicate_dispositions"]) == 1
    assert layer.restore_before_row(row, tmp_path)["text"] == nonbody["original_text"]


def test_frozen_alias_preimage_and_dispositions_are_checked(authority, tmp_path):
    outputs, audit = save(tmp_path, authority)
    changed = deepcopy(audit)
    changed["duplicate_dispositions"][0]["duplicate_of"] = PREFIX + "0094.3"
    (tmp_path / layer.AUDIT).write_bytes(campaign.encode(changed))
    with pytest.raises(ValueError, match="duplicate citation aliases changed"):
        layer.active_metadata(tmp_path)
    (tmp_path / layer.AUDIT).write_bytes(outputs[layer.AUDIT])
    (tmp_path / layer.BEFORE_ALIASES).write_bytes(gzip.compress(authority[2] + b"\n", mtime=0))
    with pytest.raises(ValueError, match="frozen artifacts changed"):
        layer.restore_before_alias_bytes(outputs[layer.ALIASES], tmp_path)


def test_legacy_alias_hooks_expose_the_exact_preceding_authority(authority, tmp_path, monkeypatch):
    outputs, _ = save(tmp_path, authority)
    assert historical._current_artifact(tmp_path, layer.ALIASES) == authority[2]
    # No older alias archive exists in this miniature tree: the public hook
    # must still strip the complete layer before deciding there is no older one.
    assert historical.restore_before_alias_bytes(outputs[layer.ALIASES], tmp_path) == authority[2]
    monkeypatch.setattr(historical, "build", lambda root: ({
        campaign.CORPUS: authority[0], layer.ALIASES: authority[2]}, {"legacy": True}))
    assert historical.check(tmp_path) == {"legacy": True}


def test_canonical_resolver_routes_tombstone_citations_before_the_existing_empty_row(authority, tmp_path, monkeypatch):
    outputs, _ = save(tmp_path, authority)
    aliases = {"photius.bibliotheca": json.loads(outputs[layer.ALIASES])["aliases"]["photius.bibliotheca"]}
    works = {"photius.bibliotheca": {}}
    monkeypatch.setattr(build_work_index, "REPO", tmp_path)
    build_work_index.validate_passage_aliases(aliases, works)
    index = {"works": works, "passage_aliases": aliases}
    for source, target in PAIRS.items():
        assert build_work_index.resolve_citation(index, "photius.bibliotheca", source)["locus"] == target


def test_apply_can_replay_after_exact_undo_but_refuses_a_torn_alias_stage(authority, tmp_path, monkeypatch):
    outputs, audit = save(tmp_path, authority)
    monkeypatch.setattr(layer, "build", lambda root: (outputs, audit))
    layer.undo(tmp_path)
    assert layer.apply(tmp_path) == audit
    assert (tmp_path / campaign.CORPUS).read_bytes() == outputs[campaign.CORPUS]
    assert (tmp_path / layer.ALIASES).read_bytes() == outputs[layer.ALIASES]
    (tmp_path / layer.ALIASES).write_bytes(authority[2])
    with pytest.raises(ValueError, match="exact preceding corpus stage"):
        layer.apply(tmp_path)
