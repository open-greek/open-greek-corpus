"""Later source proofreading keeps earlier body/role proofs content bound."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import citation_alias_state as aliases
import herodas_current_state as body_state
import herodas_review_state as state
import repair_editorial_roles as roles
from test_herodas_current_state import recovered


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def proofread(recovered, monkeypatch):
    root, body_before, body_outputs, body, body_calls = recovered
    before = body_outputs[state.PRIMARY]
    rows = [json.loads(line) for line in before.splitlines()]
    for row in rows:
        row["herodas_reading_review"] = {"authority": state.AUDIT + "/changes.json"}
        row["analysis_text"] = row.get("analysis_text", row["text"])
    current = b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)
    archive = gzip.compress(json.dumps({state.PRIMARY: before.decode()}, ensure_ascii=False).encode(), mtime=0)
    source = state.AUDIT + "/source-pin.txt"
    evidence = state.AUDIT + "/observations.json"
    outputs = {state.PRIMARY: current, state.AUDIT + "/before.json.gz": archive,
        evidence: b'{"review":"pinned source readings"}\n'}
    audit = {"schema_version": 1, "inputs": {state.PRIMARY: sha(before)},
        "outputs": {path: sha(raw) for path, raw in outputs.items()},
        "recipe_sha256": {"reading.py": "stable recipe"}, "sources": {source: sha(b"source")}}
    target = root / state.AUDIT
    target.mkdir(parents=True)
    for path, raw in {**outputs, source: b"source", state.AUDIT + "/changes.json": json.dumps(audit).encode()}.items():
        candidate = root / path
        if candidate.is_symlink():
            candidate.unlink()
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_bytes(raw)
    calls = []

    def literal(root, saved):
        if saved.get("inputs") != audit["inputs"]:
            raise ValueError("Reading predecessor changed")
        raw = (root / state.AUDIT / "before.json.gz").read_bytes()
        if sha(raw) != saved["outputs"][state.AUDIT + "/before.json.gz"]:
            raise ValueError("Reading literal preimage changed")
        decoded = json.loads(gzip.decompress(raw))
        if decoded != {state.PRIMARY: before.decode()}:
            raise ValueError("Reading literal predecessor changed")
        return before

    def checked(root, *, active=True):
        calls.append(root)
        saved = json.loads((root / state.AUDIT / "changes.json").read_bytes())
        if saved != audit or module.recipe_pins() != audit["recipe_sha256"]:
            raise ValueError("Reading authority changed")
        literal(root, saved)
        for path, raw in {**outputs, source: b"source"}.items():
            if (active or path != state.PRIMARY) and (root / path).read_bytes() != raw:
                raise ValueError("Reading source or output changed: " + path)
        return saved, before, current

    module = SimpleNamespace(INPUT_SHA256=sha(before), PRIMARY=state.PRIMARY,
        _before=literal, verify=checked, recipe_pins=lambda: {"reading.py": "stable recipe"},
        authority_paths=lambda root: tuple(outputs) + (source, state.AUDIT + "/changes.json"))
    module.manifestation_metadata = lambda root: {"herodas.mimiambi": {
        "editions": [{"key": "herodas-hk-ocr", "name": "Proofread body with explicit uncertainty"}],
        "default_edition": "herodas-hk-ocr", "coverage_composition": {
            "policy": "source-reviewed-reading-corrections", "manifest": state.AUDIT + "/changes.json",
            "manifest_sha256": sha((root / state.AUDIT / "changes.json").read_bytes()),
            "qualification": "Source proofreading with preserved critical exclusions.",
            "counts": {"passages": len(rows), "older_passages_reviewed": 62, "remaining_uncertainty_slots": 2},
            "components": [{"edition": "herodas-hk-ocr", "storage": "primary", "path": state.PRIMARY,
                "passages": len(rows), "role": "authorial-verse", "license": "PD"}]}}}
    def lexical(row, root=None):
        if row not in rows:
            raise ValueError("Reading row changed")
        return []
    module.lexical_segments = lexical
    monkeypatch.setattr(state, "PREDECESSOR_SHA256", sha(before))
    monkeypatch.setitem(sys.modules, "repair_herodas_readings", module)
    return root, before, current, module, calls, body_before, source, evidence


def test_latest_predecessor_composes_body_role_and_alias_views(proofread):
    root, before, current, _, calls, body_before, _, _ = proofread
    with state.predecessor_view(root) as previous:
        assert previous != root and (previous / state.PRIMARY).read_bytes() == before
        with state.predecessor_view(previous) as nested:
            assert nested == previous
        with body_state.role_predecessor_view(previous) as role_previous:
            assert (role_previous / state.PRIMARY).read_bytes() == body_before[state.PRIMARY].encode()
            with aliases.phoenix_alias_view(role_previous):
                pass
    assert (root / state.PRIMARY).read_bytes() == current
    assert len(calls) == 1
    assert body_state.verify_body(root)[2][state.PRIMARY] == before


@pytest.mark.parametrize("relative", [state.PRIMARY, state.AUDIT + "/observations.json",
    state.AUDIT + "/source-pin.txt", state.AUDIT + "/before.json.gz"])
def test_nested_materialization_cannot_detach_latest_source_proof(proofread, tmp_path_factory, relative):
    root, *_ = proofread
    target = tmp_path_factory.mktemp("changed-reading-view")
    with state.predecessor_view(root) as previous:
        aliases._overlay(previous, target, {Path(relative).parts: b"invalidated evidence"})
        with pytest.raises((ValueError, OSError), match="authority|preimage|gzip|Reading|identity|predecessor"):
            with state.predecessor_view(target):
                pytest.fail("Changed evidence cannot inherit a live predecessor proof")


def test_nested_recipe_change_cannot_reuse_latest_proof(proofread, monkeypatch):
    root, _, _, module, *_ = proofread
    with state.predecessor_view(root) as previous:
        with monkeypatch.context() as changed:
            changed.setattr(module, "recipe_pins", lambda: {"reading.py": "changed recipe"})
            with pytest.raises(ValueError, match="source authority"):
                with state.predecessor_view(previous):
                    pass


def test_materializing_manifest_and_predecessor_cannot_hide_changed_evidence(proofread, tmp_path_factory):
    root, before, _, _, _, _, source, _ = proofread
    target = tmp_path_factory.mktemp("detached-reading-chain")
    with state.predecessor_view(root) as previous:
        manifest = state.AUDIT + "/changes.json"
        aliases._overlay(previous, target, {
            Path(state.PRIMARY).parts: before,
            Path(manifest).parts: (previous / manifest).read_bytes(),
            Path(source).parts: b"forged",
        })
        with pytest.raises(ValueError, match="materialized.*source authority"):
            with state.predecessor_view(target):
                pass


def test_active_view_rechecks_content_after_same_size_same_mtime_mutation(proofread):
    root, _, _, _, _, _, source, _ = proofread
    path = root / source
    stamp = path.stat()
    with pytest.raises(ValueError, match="source authority"):
        with state.predecessor_view(root):
            path.write_bytes(b"forged")
            os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))


def test_materialized_literal_view_rechecks_source_after_entry(proofread, tmp_path_factory):
    root, before, _, _, _, _, source, _ = proofread
    target = tmp_path_factory.mktemp("materialized-reading-mutation")
    with state.predecessor_view(root) as previous:
        manifest = state.AUDIT + "/changes.json"
        aliases._overlay(previous, target, {
            Path(state.PRIMARY).parts: before,
            Path(manifest).parts: (previous / manifest).read_bytes(),
            Path(source).parts: (previous / source).read_bytes(),
        })
        with pytest.raises(ValueError, match="nested.*source authority"):
            with state.predecessor_view(target):
                (target / source).write_bytes(b"forged")


def test_missing_latest_authority_and_stripped_markers_fail_closed(proofread):
    root, _, current, *_ = proofread
    (root / state.AUDIT / "changes.json").unlink()
    with pytest.raises(ValueError, match="requires its reading review authority"):
        with state.predecessor_view(root):
            pass
    rows = [json.loads(line) for line in current.splitlines()]
    for row in rows:
        row.pop("herodas_reading_review")
    (root / state.PRIMARY).write_bytes(b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows))
    with pytest.raises(ValueError, match="authority"):
        with state.predecessor_view(root):
            pass


def test_literal_undo_epochs_need_no_surviving_latest_sources(proofread):
    root, before, _, _, calls, body_before, source, evidence = proofread
    (root / state.PRIMARY).write_bytes(before)
    (root / source).unlink()
    (root / evidence).unlink()
    assert state.is_unapplied(root)
    with state.predecessor_view(root) as previous:
        assert previous == root
    (root / state.PRIMARY).write_text(body_before[state.PRIMARY])
    assert state.is_unapplied(root) and body_state.body_is_unapplied(root)
    with body_state.role_predecessor_view(root) as previous:
        assert previous == root
    older = json.loads(gzip.decompress((root / roles.AUDIT / "before.json.gz").read_bytes()))
    for relative, text in older.items():
        target = root / relative
        if target.is_symlink():
            target.unlink()
        if text is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(text)
    assert state.is_unapplied(root) and aliases.role_is_unapplied(root)
    with state.predecessor_view(root) as previous:
        assert previous == root
    assert calls == []


def test_resealed_body_output_cannot_authorize_unknown_bytes_without_latest_review(proofread):
    root, _, current, *_ = proofread
    (root / state.AUDIT / "changes.json").unlink()
    rows = [json.loads(line) for line in current.splitlines()]
    for row in rows:
        row.pop("herodas_reading_review")
    altered = b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)
    (root / state.PRIMARY).write_bytes(altered)
    path = root / body_state.AUDIT / "changes.json"
    manifest = json.loads(path.read_bytes())
    manifest["outputs"][state.PRIMARY] = sha(altered)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="authority"):
        with state.predecessor_view(root):
            pass


def test_latest_metadata_keeps_historical_partition_and_body_counts(proofread):
    from editorial_role_manifestations import metadata
    from build_ocr_quality_report import herodas_role_qualification
    root, *_ = proofread
    current = metadata(root)
    scope = current["herodas.mimiambi"]["coverage_composition"]
    assert scope["policy"] == "source-reviewed-reading-corrections"
    assert scope["source_role_review"]["counts"]["primary_rows"] == 62
    assert scope["body_recovery"]["counts"]["recovered_passages"] == 1
    assert scope["counts"]["remaining_uncertainty_slots"] == 2
    quality = herodas_role_qualification(root)
    assert quality["counts"]["primary_rows"] == 62
    assert quality["later_body_recovery"]["counts"]["recovered_passages"] == 1
    assert quality["later_reading_review"]["counts"]["remaining_uncertainty_slots"] == 2
    assert current["hipponax.fragmenta"]["coverage_composition"]["counts"]["primary_rows"] == 1


def test_latest_frequency_marker_precedes_inherited_body_and_role_markers(proofread):
    from frequency_projection import FrequencyProjection, lexical_text
    root, _, current, *_ = proofread
    row = json.loads(current.splitlines()[-1])
    assert row.get("herodas_body_recovery") and row.get("herodas_reading_review")
    assert lexical_text(row) == row["analysis_text"]
    frequency = FrequencyProjection.__new__(FrequencyProjection); frequency.rows = {}
    assert frequency.segments(row) == []
    assert frequency.contextual_text(row) is None


def test_projection_signature_changes_with_latest_evidence(proofread):
    root, _, _, _, _, _, _, evidence = proofread
    before = body_state.projection_signature(root)
    (root / evidence).write_bytes(b"changed")
    assert body_state.projection_signature(root) != before
