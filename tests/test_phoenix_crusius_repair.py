"""Exact source accounting, conservative counts, and guarded undo for Phoenix."""
import copy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import phoenix_crusius_witnesses as witnesses
import repair_phoenix_crusius as repair
from critical_text import validate
from phoenix_crusius_source_observations import build_source_review


@pytest.fixture
def original():
    archived = ROOT / repair.AUDIT / "before.json.gz"
    if archived.exists():
        return json.loads(gzip.decompress(archived.read_bytes()))[repair.PRIMARY].encode()
    return (ROOT / repair.PRIMARY).read_bytes()


@pytest.fixture
def workspace(tmp_path, monkeypatch, original):
    for relative, body in [(repair.PRIMARY, original), (repair.ALIASES, repair.encoded({
            "schema_version": 1, "aliases": {"existing.work": {"1": {"path": "data/paratext/existing.jsonl", "locus": "1"}}}}))]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    packet = json.loads(gzip.decompress((ROOT / repair.AUDIT / "ocr-witnesses.json.gz").read_bytes()))
    monkeypatch.setattr(witnesses, "build_packet", lambda root: copy.deepcopy(packet))
    return tmp_path


def apply(root):
    repair.run(root, "apply", source_pdf=ROOT / repair.AUDIT / "source-scan.pdf",
               witness_root=Path("."), reviewed_at="2026-10-22T03:40:59Z")


def test_complete_partition_and_readings(original):
    rows = repair.parse_original(original)
    review = build_source_review(rows)
    outputs, changes, counts = repair.build_outputs(original, review, repair.encoded(review),
                                                   repair.encoded({"aliases": {}}))
    primary = [json.loads(line) for line in outputs[repair.PRIMARY].splitlines()]
    retained = [json.loads(line) for line in outputs[repair.RETAINED].splitlines()]
    assert counts == {"original_rows": 2749, "primary_rows": 21,
        "retained_outside_primary": 2728, "changed_text_rows": 18,
        "surface_tokens": 133, "lexical_tokens": 129, "excluded_supplied_tokens": 4,
        "source_scan_pages": [68, 69]}
    assert [row["locus"] for row in primary] == list(repair.PRIMARY_LOCI)
    assert {row["locus"] for row in primary + retained} == {row["locus"] for row in rows}
    originals = {row["locus"]: row for row in rows}
    for row in retained:
        assert all(row[key] == value for key, value in originals[row["locus"]].items())
    assert len(changes) == 2749
    assert sum(change["text_changed"] for change in changes) == 18
    assert all(change["original_text"] == change["original_row"]["text"] for change in changes)
    for row in primary:
        validate(row)
    # The entire partially supplied word is excluded, rather than retaining τῳ.
    supplied = [token for row in primary for token in row["tokens"] if not token["lexical_eligible"]]
    assert [token["form"] for token in supplied] == ["τ’", "τ’", "τι", "τούτῳ"]
    assert primary[16]["source_gap_after"]["kind"] == "printed-omission-divider"


def test_apply_replay_alias_preservation_and_exact_undo(workspace):
    before = {relative: (workspace / relative).read_bytes() for relative in [repair.PRIMARY, repair.ALIASES]}
    apply(workspace)
    audit, _, _ = repair.verify(workspace)
    snapshot = {relative: (workspace / relative).read_bytes() for relative in audit["outputs"]}
    repair.run(workspace, "apply")
    assert snapshot == {relative: (workspace / relative).read_bytes() for relative in snapshot}
    aliases = json.loads((workspace / repair.ALIASES).read_bytes())["aliases"]
    assert aliases["existing.work"]
    assert len(aliases[repair.WORK]) == 2749
    destinations = {relative: {json.loads(line)["locus"] for line in
        (workspace / relative).read_bytes().splitlines()} for relative in (repair.PRIMARY, repair.RETAINED)}
    for old_locus, target in aliases[repair.WORK].items():
        assert target["locus"] == old_locus
        assert target["locus"] in destinations[target["path"]]
    repair.run(workspace, "undo")
    assert before == {relative: (workspace / relative).read_bytes() for relative in before}
    assert not (workspace / repair.RETAINED).exists()
    repair.run(workspace, "apply")
    repair.verify(workspace)


@pytest.mark.parametrize("relative", [repair.PRIMARY, repair.RETAINED, repair.ALIASES,
    repair.AUDIT + "/before.json.gz"])
def test_refuses_drift_before_undo(workspace, relative):
    apply(workspace)
    target = workspace / relative
    target.write_bytes(target.read_bytes() + b" ")
    served = (workspace / repair.PRIMARY).read_bytes()
    with pytest.raises(ValueError, match="output changed"):
        repair.run(workspace, "undo")
    assert (workspace / repair.PRIMARY).read_bytes() == served


@pytest.mark.parametrize("relative", [repair.AUDIT + "/source-review.json",
    repair.AUDIT + "/records.jsonl.gz", repair.AUDIT + "/ocr-witnesses.json.gz",
    repair.AUDIT + "/source-scan.pdf"])
def test_literal_undo_survives_removed_or_invalidated_evidence(workspace, relative):
    original = (workspace / repair.PRIMARY).read_bytes()
    aliases = (workspace / repair.ALIASES).read_bytes()
    apply(workspace)
    (workspace / relative).unlink()
    repair.run(workspace, "undo")
    assert (workspace / repair.PRIMARY).read_bytes() == original
    assert (workspace / repair.ALIASES).read_bytes() == aliases
    assert not (workspace / repair.RETAINED).exists()


def test_rejects_primary_tampering_even_with_rehashed_output(workspace):
    apply(workspace)
    path = workspace / repair.PRIMARY
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[0]["text"] = "ἀνεξέταστον"
    path.write_bytes(repair.jsonl(rows))
    audit_path = workspace / repair.AUDIT / "changes.json"
    audit = json.loads(audit_path.read_bytes())
    audit["outputs"][repair.PRIMARY] = repair.sha(path.read_bytes())
    audit_path.write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError, match="replay"):
        repair.verify(workspace)


def test_direct_projection_rejects_analysis_or_provenance_tampering(workspace):
    apply(workspace)
    row = json.loads((workspace / repair.PRIMARY).read_bytes().splitlines()[0])
    assert repair.lexical_segments(row, workspace)
    for field, value in [("analysis_text", "τοῦτο"), ("edition", "unreviewed"),
                         ("text", "changed")]:
        bad = copy.deepcopy(row)
        bad[field] = value
        with pytest.raises(ValueError, match="postimage"):
            repair.lexical_segments(bad, workspace)


def test_generic_frequency_projection_uses_the_checked_exclusions(workspace, monkeypatch):
    apply(workspace)
    monkeypatch.setattr(repair, "ROOT", workspace)
    from frequency_projection import FrequencyProjection
    frequency = FrequencyProjection(workspace / "data")
    rows = [json.loads(line) for line in (workspace / repair.PRIMARY).read_bytes().splitlines()]
    verse17 = rows[16]
    assert "τούτῳ" in verse17["reading_text"]
    assert "τούτῳ" not in frequency.text(verse17)
    assert frequency.segments(verse17) == ["καὶ δόντι καὶ μὴ δόντι πλέονα", "γε"]
    assert frequency.contextual_text(verse17) is None


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "preimage", "source"])
def test_review_cannot_expand_or_change_its_authority(original, mutation):
    review = build_source_review(repair.parse_original(original))
    if mutation == "missing": review["verses"].pop()
    elif mutation == "duplicate": review["verses"].append(review["verses"][0])
    elif mutation == "preimage": review["verses"][0]["corrected_text"] = "ἄλλο"
    else: review["source"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="observations"):
        repair.build_outputs(original, review, repair.encoded(review), repair.encoded({"aliases": {}}))


def test_apply_refuses_wrong_scan_before_writing(workspace):
    scan = workspace / "wrong.pdf"
    scan.write_bytes(b"not the reviewed scan")
    with pytest.raises(ValueError, match="exact reviewed"):
        repair.run(workspace, "apply", source_pdf=scan, witness_root=Path("."))
    assert not (workspace / repair.AUDIT / "changes.json").exists()
    assert repair.sha((workspace / repair.PRIMARY).read_bytes()) == repair.ORIGINAL_SHA256


def test_dry_run_is_read_only(workspace):
    repair.run(workspace, "dry-run")
    assert not (workspace / repair.AUDIT).exists()
    assert not (workspace / repair.RETAINED).exists()

