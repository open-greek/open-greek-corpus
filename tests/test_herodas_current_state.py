"""Later body admissions must preserve the frozen role review's exact inputs."""
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
import herodas_current_state as state
import phoenix_current_state as phoenix
import repair_editorial_roles as roles
import repair_phoenix_crusius as frozen_phoenix


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def recovered(tmp_path, monkeypatch):
    # The published role postimage remains the independent baseline even after
    # a later body admission has changed the production primary.
    original = json.loads(gzip.decompress((ROOT / roles.AUDIT / "before.json.gz").read_bytes()))
    review = json.loads((ROOT / roles.AUDIT / "source-review.json").read_bytes())
    role_outputs, _, _ = roles.build_outputs(original, review)
    previous = role_outputs[state.PRIMARY]
    assert sha(previous) == state.PREDECESSOR_SHA256
    row = dict(json.loads(previous.splitlines()[0]), locus="herodas_hk_body_0076.1",
        text="λόγος μένει", analysis_text="λόγος μένει",
        herodas_body_recovery={"authority": state.AUDIT + "/changes.json"})
    current = previous + (json.dumps(row, ensure_ascii=False) + "\n").encode()
    before = {state.PRIMARY: previous.decode()}
    archive = gzip.compress(json.dumps(before, ensure_ascii=False).encode(), mtime=0)
    evidence = state.AUDIT + "/source-review.json"
    outputs = {state.PRIMARY: current, state.AUDIT + "/before.json.gz": archive,
        evidence: b'{"review":"pinned body evidence"}\n'}
    audit = {"schema_version": 1, "inputs": {state.PRIMARY: sha(previous)},
        "outputs": {path: sha(raw) for path, raw in outputs.items()},
        "recipe_sha256": {"body.py": "stable recipe"}}
    audit_raw = (json.dumps(audit) + "\n").encode()
    materialized = {**role_outputs, **outputs, state.AUDIT + "/changes.json": audit_raw,
        # All probes below may write these files. Materialize them, rather than
        # writing through a symlink into a production source packet.
        roles.AUDIT + "/source-review.json": (ROOT / roles.AUDIT / "source-review.json").read_bytes()}
    aliases._overlay(ROOT, tmp_path, {Path(path).parts: raw for path, raw in materialized.items()})
    for path, raw in materialized.items():
        if path.startswith(state.AUDIT + "/"):
            target = tmp_path / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    calls = []
    def pinned_before(root, saved):
        if saved.get("inputs") != audit["inputs"]:
            raise ValueError("Body input changed")
        raw = (root / state.AUDIT / "before.json.gz").read_bytes()
        if sha(raw) != saved["outputs"][state.AUDIT + "/before.json.gz"]:
            raise ValueError("Body preimage changed")
        decoded = json.loads(gzip.decompress(raw))
        if decoded != before:
            raise ValueError("Body literal preimage changed")
        return decoded
    def checked(root, *, active=True):
        calls.append(root)
        saved = json.loads((root / state.AUDIT / "changes.json").read_bytes())
        if saved != audit or module.recipe_pins() != audit["recipe_sha256"]:
            raise ValueError("Body authority changed")
        pinned_before(root, saved)
        for path, raw in outputs.items():
            if (active or path != state.PRIMARY) and (root / path).read_bytes() != raw:
                raise ValueError("Body output changed: " + path)
        return saved, before, outputs
    module = SimpleNamespace(CORE={state.PRIMARY}, _before=pinned_before, verify=checked,
        recipe_pins=lambda: {"body.py": "stable recipe"},
        authority_paths=lambda root: tuple(outputs) + (state.AUDIT + "/changes.json",))
    module.manifestation_metadata = lambda root: {"herodas.mimiambi": {
        "editions": [{"key": "herodas-hk-ocr", "name": "Expanded body with explicit qualifications"}],
        "default_edition": "herodas-hk-ocr",
        "coverage_composition": {"policy": "qualified-body-recovery",
            "manifest": state.AUDIT + "/changes.json", "manifest_sha256": sha(audit_raw),
            "counts": {"original_passages": 62, "recovered_passages": 1, "primary_passages": 63},
            "primary_quality": {"status": "mixed-review-scope"},
            "components": [{"edition": "herodas-hk-ocr", "storage": "primary", "path": state.PRIMARY,
                "passages": 63, "role": "authorial-verse", "license": "PD"}]}}}
    def lexical(candidate, root=None):
        if candidate != row:
            raise ValueError("Body row changed")
        return ["λόγος", "μένει"]
    module.lexical_segments = lexical
    monkeypatch.setitem(sys.modules, "repair_herodas_body", module)
    return tmp_path, before, outputs, module, calls


def test_checked_primary_predecessor_keeps_other_inputs_and_real_primary(recovered):
    root, before, outputs, _, calls = recovered
    with state.role_predecessor_view(root) as previous:
        assert previous != root
        assert (previous / state.PRIMARY).read_bytes() == before[state.PRIMARY].encode()
        assert (previous / roles.ALIASES).read_bytes() == (root / roles.ALIASES).read_bytes()
        assert state.verify_roles(previous)[0]["counts"]["herodas.mimiambi"]["primary_rows"] == 62
    assert len(calls) == 1
    assert (root / state.PRIMARY).read_bytes() == outputs[state.PRIMARY]


def test_nested_primary_predecessor_and_old_alias_layers_compose(recovered):
    root, before, _, _, calls = recovered
    with state.role_predecessor_view(root) as previous:
        with state.role_predecessor_view(previous) as nested:
            assert nested == previous
        with aliases.phoenix_alias_view(previous) as old_aliases:
            with state.role_predecessor_view(old_aliases) as nested:
                assert (nested / state.PRIMARY).read_bytes() == before[state.PRIMARY].encode()
    assert len(calls) == 1
    assert phoenix.verify(root)[0]["counts"]["primary_rows"] == 21


@pytest.mark.parametrize("relative", [state.PRIMARY, state.AUDIT + "/source-review.json",
    state.AUDIT + "/before.json.gz", roles.AUDIT + "/source-review.json",
    roles.RETAINED["herodas.mimiambi"]])
def test_nested_view_cannot_reuse_primary_proof_for_changed_authority(recovered, tmp_path_factory, relative):
    root, _, _, _, _ = recovered
    target = tmp_path_factory.mktemp("changed-body-proof")
    with state.role_predecessor_view(root) as previous:
        aliases._overlay(previous, target, {Path(relative).parts: b"invalidated source"})
        with pytest.raises((ValueError, OSError), match="authority|preimage|gzip|Body|identity"):
            with state.role_predecessor_view(target):
                pytest.fail("A predecessor file cannot authorize different source evidence")


def test_nested_recipe_change_is_not_covered_by_an_earlier_proof(recovered, monkeypatch):
    root, _, _, module, _ = recovered
    with state.role_predecessor_view(root) as previous:
        with monkeypatch.context() as changed:
            changed.setattr(module, "recipe_pins", lambda: {"body.py": "changed recipe"})
            with pytest.raises(ValueError, match="source authority"):
                with state.role_predecessor_view(previous):
                    pass


def test_nested_view_keeps_the_frozen_role_recipe_bound(recovered, monkeypatch):
    root, _, _, _, _ = recovered
    with state.role_predecessor_view(root) as previous:
        original = roles.recipe_pins()
        with monkeypatch.context() as changed:
            changed.setattr(roles, "recipe_pins", lambda: {**original,
                "repair_editorial_roles.py": "changed frozen recipe"})
            with pytest.raises(ValueError, match="source authority"):
                with state.role_predecessor_view(previous):
                    pass


@pytest.mark.parametrize("during_verify", [True, False])
def test_source_drift_before_or_after_yield_is_rejected(recovered, monkeypatch, during_verify):
    root, _, _, module, _ = recovered
    evidence = root / state.AUDIT / "source-review.json"
    checked = module.verify
    if during_verify:
        def mutate(candidate, **kwargs):
            result = checked(candidate, **kwargs)
            evidence.write_bytes(b"changed")
            return result
        monkeypatch.setattr(module, "verify", mutate)
    with pytest.raises(ValueError, match="during predecessor"):
        with state.role_predecessor_view(root):
            if during_verify:
                pytest.fail("Changed evidence cannot enter a checked view")
            evidence.write_bytes(b"changed")


@pytest.mark.parametrize("nested", [False, True])
def test_missing_active_or_nested_body_authority_is_rejected(recovered, tmp_path_factory, nested):
    root, _, _, _, _ = recovered
    def check(candidate):
        target = tmp_path_factory.mktemp("missing-body-proof")
        path = Path(state.AUDIT) / "changes.json"
        aliases._overlay(candidate, target, {path.parts: b""})
        (target / path).unlink()
        with pytest.raises(ValueError, match="frozen body authority"):
            with state.role_predecessor_view(target):
                pass
    if nested:
        with state.role_predecessor_view(root) as previous:
            check(previous)
    else:
        check(root)


def test_missing_body_authority_cannot_hide_a_removed_marker(recovered):
    root, _, _, _, _ = recovered
    path = root / state.PRIMARY
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[-1].pop("herodas_body_recovery")
    path.write_bytes(b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows))
    (root / state.AUDIT / "changes.json").unlink()
    with pytest.raises(ValueError, match="frozen body authority"):
        with state.role_predecessor_view(root):
            pass


def test_missing_body_authority_cannot_trust_a_resealed_older_output_pin(recovered):
    root, _, _, _, _ = recovered
    primary = root / state.PRIMARY
    rows = [json.loads(line) for line in primary.read_bytes().splitlines()]
    rows[-1].pop("herodas_body_recovery")
    primary.write_bytes(b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows))
    path = root / roles.AUDIT / "changes.json"
    audit = json.loads(path.read_bytes())
    audit["outputs"][state.PRIMARY] = sha(primary.read_bytes())
    path.unlink()  # materialize before changing a linked older authority
    path.write_text(json.dumps(audit))
    (root / state.AUDIT / "changes.json").unlink()
    with pytest.raises(ValueError, match="frozen body authority"):
        with state.role_predecessor_view(root):
            pass


def test_exact_body_undo_needs_no_source_or_replay_recipe(recovered, monkeypatch):
    root, before, _, module, _ = recovered
    (root / state.PRIMARY).write_text(before[state.PRIMARY])
    (root / state.AUDIT / "source-review.json").unlink()
    def unavailable(*args, **kwargs):
        pytest.fail("Literal undo cannot require invalidated source or recipe checks")
    monkeypatch.setattr(module, "recipe_pins", unavailable)
    monkeypatch.setattr(module, "verify", unavailable)
    assert state.body_is_unapplied(root)
    with state.role_predecessor_view(root) as previous:
        assert previous == root


@pytest.mark.parametrize("defect", ["archive", "primary", "baseline"])
def test_literal_undo_requires_exact_archive_preimage_and_primary(recovered, defect):
    root, before, _, _, _ = recovered
    (root / state.PRIMARY).write_text(before[state.PRIMARY])
    if defect == "archive":
        (root / state.AUDIT / "before.json.gz").write_bytes(b"changed archive")
    elif defect == "primary":
        with (root / state.PRIMARY).open("ab") as stream:
            stream.write(b" ")
    else:
        path = root / state.AUDIT / "changes.json"
        audit = json.loads(path.read_bytes())
        audit["inputs"][state.PRIMARY] = "unknown baseline"
        path.write_text(json.dumps(audit))
    with pytest.raises(ValueError):
        with state.role_predecessor_view(root):
            pytest.fail("A mixed preimage is not a literal undo")


def test_old_role_and_phoenix_undo_remain_valid_with_persisted_body_archive(recovered):
    root, _, _, _, calls = recovered
    old_before = json.loads(gzip.decompress((ROOT / roles.AUDIT / "before.json.gz").read_bytes()))
    for path, text in old_before.items():
        target = root / path
        target.unlink(missing_ok=True)
        if text is not None:
            target.write_text(text)
    (root / state.AUDIT / "source-review.json").unlink()
    with state.role_predecessor_view(root) as previous:
        assert previous == root
    assert aliases.role_is_unapplied(root)
    assert state.body_is_unapplied(root)
    phoenix_before = json.loads(gzip.decompress((ROOT / frozen_phoenix.AUDIT / "before.json.gz").read_bytes()))
    # Materialize every changed primary and alias before restoring an old epoch.
    for path, text in phoenix_before.items():
        target = root / path
        if target.is_symlink():
            target.unlink()
        if text is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(text)
    assert aliases.role_is_unapplied(root)
    assert state.body_is_unapplied(root)
    with state.role_predecessor_view(root) as previous:
        assert previous == root
    with aliases.phoenix_alias_view(root):
        pass
    # Neither source-invalidated undo epoch required the latest replay engine.
    assert not calls


def test_projection_cache_rechecks_body_evidence_and_keeps_rows_literal(recovered):
    root, before, _, _, _ = recovered
    row = next(json.loads(line) for line in before[state.PRIMARY].splitlines()
               if json.loads(line).get("editorial_role_review"))
    segments = state.role_lexical_segments(row, root)
    expected = list(segments)
    segments[0] = "modified returned segments"
    assert state.role_lexical_segments(row, root) == expected
    with pytest.raises(ValueError, match="postimage"):
        state.role_lexical_segments(dict(row, text="unreviewed text"), root)
    path = root / state.AUDIT / "source-review.json"
    stamp = path.stat()
    path.write_bytes(path.read_bytes().replace(b"pinned", b"forged"))
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    with pytest.raises(ValueError, match="Body output changed"):
        state.role_lexical_segments(row, root)


def test_phoenix_projection_cache_also_rechecks_latest_body_evidence(recovered):
    root, _, _, _, _ = recovered
    row = json.loads((root / frozen_phoenix.PRIMARY).read_bytes().splitlines()[0])
    assert phoenix.lexical_segments(row, root)
    path = root / state.AUDIT / "source-review.json"
    stamp = path.stat()
    path.write_bytes(path.read_bytes().replace(b"pinned", b"forged"))
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    with pytest.raises(ValueError, match="Body output changed"):
        phoenix.lexical_segments(row, root)


def test_published_pre_recovery_roots_and_empty_roots_are_noops(recovered, tmp_path_factory):
    root, before, _, _, _ = recovered
    (root / state.PRIMARY).write_text(before[state.PRIMARY])
    (root / state.AUDIT / "changes.json").unlink()
    with state.role_predecessor_view(root) as previous:
        assert previous == root
    empty = tmp_path_factory.mktemp("empty-before-recovery")
    with state.role_predecessor_view(empty) as previous:
        assert previous == empty


def test_noop_view_cannot_outlive_a_changed_admission(recovered):
    root, before, _, _, _ = recovered
    (root / state.PRIMARY).write_text(before[state.PRIMARY])
    (root / state.AUDIT / "changes.json").unlink()
    with pytest.raises(ValueError, match="admission changed"):
        with state.role_predecessor_view(root):
            with (root / state.PRIMARY).open("ab") as stream:
                stream.write(b" ")


def test_body_undo_recognition_rechecks_its_literal_core(recovered, monkeypatch):
    root, before, _, _, _ = recovered
    (root / state.PRIMARY).write_text(before[state.PRIMARY])
    checked = state._is_unapplied
    def changed(candidate, saved):
        result = checked(candidate, saved)
        with (candidate / state.PRIMARY).open("ab") as stream:
            stream.write(b" ")
        return result
    monkeypatch.setattr(state, "_is_unapplied", changed)
    with pytest.raises(ValueError, match="during undo recognition"):
        state.body_is_unapplied(root)


def test_current_metadata_preserves_old_partition_and_updates_primary_component(recovered):
    from editorial_role_manifestations import metadata
    root, _, _, _, _ = recovered
    current = metadata(root)
    herodas = current["herodas.mimiambi"]
    scope = herodas["coverage_composition"]
    assert scope["counts"]["primary_passages"] == 63
    assert scope["source_role_review"]["counts"]["primary_rows"] == 62
    assert scope["source_role_review"]["counts"]["original_analysis_tokens"] == 2846
    primary = [item for item in scope["components"] if item["storage"] == "primary"]
    assert len(primary) == 1 and primary[0]["passages"] == 63
    outside = [item for item in scope["components"] if item["storage"] == "paratext"]
    assert len(outside) == 1 and outside[0]["passages"] == 84
    assert len({item["key"] for item in herodas["editions"]}) == 2
    assert current["hipponax.fragmenta"]["coverage_composition"]["counts"]["primary_rows"] == 1


def test_quality_role_counts_keep_the_historical_scope_after_body_recovery(recovered):
    from build_ocr_quality_report import herodas_role_qualification
    root, _, _, _, _ = recovered
    role_scope = herodas_role_qualification(root)
    assert role_scope["counts"]["original_rows"] == 136
    assert role_scope["counts"]["primary_rows"] == 62
    assert role_scope["counts"]["original_analysis_tokens"] == 2846
    assert role_scope["counts"]["primary_analysis_tokens"] == 2036
    assert "not character error rate" in role_scope["qualification"]


def test_frequency_dispatch_uses_latest_body_eligibility_before_old_role_marker(recovered):
    from frequency_projection import FrequencyProjection, lexical_text
    _, _, outputs, _, _ = recovered
    row = json.loads(outputs[state.PRIMARY].splitlines()[-1])
    assert lexical_text(row) == "λόγος μένει"
    frequency = FrequencyProjection.__new__(FrequencyProjection)
    frequency.rows = {}
    assert frequency.text(row) == "λόγος μένει"
    assert frequency.segments(row) == ["λόγος", "μένει"]
    assert frequency.contextual_text(row) is None
