"""Independent role admissions cannot hide changes from earlier authorities."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import citation_alias_state as state
import herodas_current_state as herodas
import photius_current_state as photius
import phoenix_current_state as phoenix
import repair_editorial_roles as role
import repair_phoenix_crusius as frozen
from frequency_projection import FrequencyProjection


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def original_inputs():
    archive = ROOT / role.AUDIT / "before.json.gz"
    if archive.exists():
        return json.loads(gzip.decompress(archive.read_bytes()))
    return {path: (ROOT / path).read_text() if (ROOT / path).exists() else None
            for path in role.CORE}


@pytest.fixture
def admitted(tmp_path, monkeypatch):
    before = original_inputs()
    before_raw = gzip.compress(json.dumps(before, ensure_ascii=False).encode(), mtime=0)
    outputs = {}
    for work, path in role.PRIMARY.items():
        rows = [json.loads(line) for line in before[path].splitlines()]
        chosen = dict(rows[0])
        if work == "herodas.mimiambi":
            chosen["editorial_role_review"] = {"authority": role.AUDIT + "/changes.json"}
        outputs[path] = (json.dumps(chosen, ensure_ascii=False) + "\n").encode()
    for path in role.RETAINED.values():
        outputs[path] = b'{"editorial_role_review":{},"text":"retained historical material"}\n'
    aliases = json.loads(before[role.ALIASES])
    aliases["aliases"]["herodas.mimiambi"] = {"historical": {
        "path": role.RETAINED["herodas.mimiambi"], "locus": "historical"}}
    outputs[role.ALIASES] = (json.dumps(aliases, ensure_ascii=False) + "\n").encode()
    outputs[role.AUDIT + "/before.json.gz"] = before_raw
    outputs[role.AUDIT + "/source-review.json"] = b'{"review":"pinned role evidence"}\n'
    overrides = {Path(path).parts: body for path, body in outputs.items() if path in role.CORE}
    # Materialize every ancestor of the archive, even when the production tree
    # already carries a later admission. Never write through an evidence link.
    overrides[(state.AUDIT / "unused-placeholder").parts] = b""
    # These fixtures isolate the frozen role/alias layer. Body recovery has its
    # own full-chain admission and chronological undo fixtures.
    body_authority = Path(herodas.AUDIT) / "changes.json"
    overrides[body_authority.parts] = b""
    state._overlay(ROOT, tmp_path, overrides)
    if (tmp_path / body_authority).is_file():
        (tmp_path / body_authority).unlink()
    directory = tmp_path / state.AUDIT
    assert not directory.is_symlink()
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    for path, body in outputs.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    audit = {"schema_version": 1,
        "inputs": {path: sha(value.encode()) if value is not None else None
                   for path, value in before.items()},
        "outputs": {path: sha(body) for path, body in outputs.items()}}
    (directory / "changes.json").write_text(json.dumps(audit))
    monkeypatch.setattr(herodas, "PREDECESSOR_SHA256", sha(outputs[herodas.PRIMARY]))
    calls = []
    def checked(candidate):
        calls.append(candidate)
        saved = json.loads((candidate / state.AUDIT / "changes.json").read_bytes())
        if saved != audit:
            raise ValueError("Role authority changed")
        for path, body in outputs.items():
            if not (candidate / path).is_file() or (candidate / path).read_bytes() != body:
                raise ValueError("Role review output changed: " + path)
        return audit, before, outputs
    monkeypatch.setattr(state, "_verify_role", checked)
    return tmp_path, before, outputs, calls


def test_active_alias_predecessor_preserves_all_other_current_inputs(admitted):
    root, before, outputs, calls = admitted
    with state.phoenix_alias_view(root) as previous:
        assert previous != root
        assert (previous / state.ALIASES).read_bytes() == before[role.ALIASES].encode()
        for path in role.CORE - {role.ALIASES}:
            assert (previous / path).read_bytes() == outputs[path]
    assert calls
    assert (root / state.ALIASES).read_bytes() == outputs[role.ALIASES]


def test_unchanged_nested_alias_file_keeps_the_checked_proof(admitted):
    root, before, _, _ = admitted
    with state.phoenix_alias_view(root) as previous:
        with state.phoenix_alias_view(previous) as nested:
            assert nested == previous
            assert (nested / state.ALIASES).read_bytes() == before[role.ALIASES].encode()


def test_authorized_alias_proof_rechecks_its_replay_recipes(admitted, monkeypatch):
    root, _, _, _ = admitted
    with state.phoenix_alias_view(root) as previous:
        with monkeypatch.context() as changed:
            actual = role.recipe_pins()
            changed.setattr(role, "recipe_pins", lambda: {**actual,
                "repair_editorial_roles.py": "invalidated recipe"})
            with pytest.raises(ValueError, match="source authority"):
                with state.phoenix_alias_view(previous):
                    pass


@pytest.mark.parametrize("relative", [*sorted(role.CORE - {role.ALIASES}),
    role.AUDIT + "/source-review.json", role.AUDIT + "/before.json.gz"])
def test_nested_alias_proof_rejects_changed_sources_and_current_core(admitted, tmp_path_factory, relative):
    root, _, _, _ = admitted
    target = tmp_path_factory.mktemp("changed-role-authority")
    with state.phoenix_alias_view(root) as previous:
        state._overlay(previous, target, {Path(relative).parts: b"changed authority"})
        with pytest.raises((ValueError, OSError), match="authority|gzip"):
            with state.phoenix_alias_view(target):
                pytest.fail("An alias file alone cannot authorize different source inputs")


def test_old_aliases_with_active_new_core_are_not_an_exact_undo(admitted):
    root, before, _, _ = admitted
    (root / state.ALIASES).write_text(before[role.ALIASES])
    with pytest.raises(ValueError, match="output changed"):
        with state.phoenix_alias_view(root):
            pass


def test_source_drift_between_verification_and_yield_is_rejected(admitted, monkeypatch):
    root, _, _, _ = admitted
    real = state._verify_role
    def changed(candidate):
        result = real(candidate)
        (candidate / state.AUDIT / "source-review.json").write_bytes(b"changed")
        return result
    monkeypatch.setattr(state, "_verify_role", changed)
    with pytest.raises(ValueError, match="during predecessor"):
        with state.phoenix_alias_view(root):
            pytest.fail("A changed input must not enter the predecessor view")


def test_source_and_alias_drift_during_validation_are_rejected(admitted):
    root, _, _, _ = admitted
    with pytest.raises(ValueError, match="during predecessor"):
        with state.phoenix_alias_view(root):
            (root / state.AUDIT / "source-review.json").write_bytes(b"changed")


@pytest.mark.parametrize("nested", [False, True])
def test_missing_active_or_nested_authority_is_rejected(admitted, tmp_path_factory, nested):
    root, _, _, _ = admitted
    def check(source):
        target = tmp_path_factory.mktemp("missing-role-authority")
        path = state.AUDIT / "changes.json"
        state._overlay(source, target, {path.parts: b""})
        (target / path).unlink()
        with pytest.raises(ValueError, match="frozen citation authority"):
            with state.phoenix_alias_view(target):
                pass
    if nested:
        with state.phoenix_alias_view(root) as previous:
            check(previous)
    else:
        check(root)


def test_exact_undo_remains_usable_when_its_source_was_removed(admitted):
    root, before, _, _ = admitted
    for path, text in before.items():
        if text is None:
            (root / path).unlink()
        else:
            (root / path).write_text(text)
    (root / state.AUDIT / "source-review.json").unlink()
    assert state.role_is_unapplied(root)
    with state.phoenix_alias_view(root) as restored:
        assert restored == root
        with state.phoenix_alias_view(restored) as nested:
            assert nested == root


def test_rehashed_undo_cannot_substitute_an_unknown_alias_preimage(admitted):
    root, before, _, _ = admitted
    forged = dict(before)
    forged[role.ALIASES] = '{"aliases": {"unreviewed": {}}}\n'
    for path, text in forged.items():
        if text is None:
            (root / path).unlink()
        else:
            (root / path).write_text(text)
    archived = gzip.compress(json.dumps(forged, ensure_ascii=False).encode(), mtime=0)
    (root / state.AUDIT / "before.json.gz").write_bytes(archived)
    path = root / state.AUDIT / "changes.json"
    audit = json.loads(path.read_bytes())
    audit["inputs"][role.ALIASES] = sha(forged[role.ALIASES].encode())
    audit["outputs"][(state.AUDIT / "before.json.gz").as_posix()] = sha(archived)
    path.write_text(json.dumps(audit))
    with pytest.raises(ValueError, match="authority changed"):
        with state.phoenix_alias_view(root):
            pytest.fail("The original alias baseline must remain independently pinned")


def chronological_undo(root, before):
    for path, text in before.items():
        if text is None:
            (root / path).unlink()
        else:
            (root / path).write_text(text)
    old_archive = ROOT / frozen.AUDIT
    old_before = json.loads(gzip.decompress((old_archive / "before.json.gz").read_bytes()))
    # Materialize the complete Phoenix authority before any evidence mutation.
    directory = root / frozen.AUDIT
    if directory.is_symlink():
        directory.unlink()
    else:
        shutil.rmtree(directory)
    shutil.copytree(old_archive, directory)
    for path, text in old_before.items():
        target = root / path
        if target.is_symlink():
            target.unlink()
        if text is None:
            target.unlink(missing_ok=True)
        else:
            target.write_text(text)
    # Both corrections remain removable when their evidentiary sources are lost.
    (root / state.AUDIT / "source-review.json").unlink()
    (directory / "source-scan.pdf").unlink()
    return directory


@pytest.mark.parametrize("defect", [None, "active-phoenix", "unknown-aliases", "changed-old-audit"])
def test_chronological_role_and_phoenix_undo_uses_two_literal_epochs(admitted, defect):
    root, before, _, _ = admitted
    directory = chronological_undo(root, before)
    if defect == "active-phoenix":
        (root / frozen.PRIMARY).write_bytes((ROOT / frozen.PRIMARY).read_bytes())
    elif defect == "unknown-aliases":
        (root / state.ALIASES).write_bytes(b'{"aliases":{"unreviewed":{}}}\n')
    elif defect == "changed-old-audit":
        path = directory / "changes.json"
        old = json.loads(path.read_bytes())
        old["outputs"][frozen.ALIASES] = "unknown later epoch"
        path.write_text(json.dumps(old))
    if defect is None:
        assert state.role_is_unapplied(root)
        with state.phoenix_alias_view(root) as restored:
            assert restored == root
        from editorial_role_manifestations import metadata
        assert metadata(root) == {}
    else:
        assert not state.role_is_unapplied(root)
        with pytest.raises(ValueError):
            with state.phoenix_alias_view(root):
                pytest.fail("A mixed or forged historical epoch must not be accepted")


def test_older_epoch_core_drift_is_rejected_during_two_undo_view(admitted):
    root, before, _, _ = admitted
    chronological_undo(root, before)
    with pytest.raises(ValueError, match="during predecessor"):
        with state.phoenix_alias_view(root):
            path = root / frozen.PRIMARY
            path.write_bytes(path.read_bytes() + b" ")


def test_older_epoch_core_drift_is_rejected_during_undo_recognition(admitted, monkeypatch):
    root, before, _, _ = admitted
    chronological_undo(root, before)
    previous = state._earlier_phoenix_undo
    def changed_after_recognition(*args):
        result = previous(*args)
        path = root / frozen.PRIMARY
        path.write_bytes(path.read_bytes() + b" ")
        return result
    monkeypatch.setattr(state, "_earlier_phoenix_undo", changed_after_recognition)
    with pytest.raises(ValueError, match="during undo recognition"):
        state.role_is_unapplied(root)


def test_genuine_pre_admission_root_and_empty_root_are_noops(admitted, tmp_path_factory):
    root, before, _, _ = admitted
    for path, text in before.items():
        if text is None:
            (root / path).unlink()
        else:
            (root / path).write_text(text)
    (root / state.AUDIT / "changes.json").unlink()
    with state.phoenix_alias_view(root) as older:
        assert older == root
    empty = tmp_path_factory.mktemp("pre-admission-empty")
    with state.phoenix_alias_view(empty) as older:
        assert older == empty


def test_missing_authority_with_trimmed_unmarked_hipponax_is_rejected(admitted):
    root, before, _, _ = admitted
    for path in role.RETAINED.values():
        (root / path).unlink()
    (root / role.PRIMARY["herodas.mimiambi"]).write_text(before[role.PRIMARY["herodas.mimiambi"]])
    (root / state.AUDIT / "changes.json").unlink()
    with pytest.raises(ValueError, match="frozen citation authority"):
        with state.phoenix_alias_view(root):
            pass


def test_frozen_phoenix_and_photius_layers_compose_with_later_roles(admitted):
    root, _, _, _ = admitted
    audit, _, _ = phoenix.verify(root)
    assert audit["counts"]["primary_rows"] == 21
    row = json.loads((root / frozen.PRIMARY).read_bytes().splitlines()[0])
    assert phoenix.lexical_segments(row, root)
    with photius.prior_alias_view(root) as previous:
        with state.phoenix_alias_view(previous) as nested:
            assert (nested / state.ALIASES).read_bytes() == (previous / state.ALIASES).read_bytes()
        with photius.continuation_view(previous):
            pass
    assert photius.final_metadata(root)["counts"]["current_uncertainty_spans"] == 0


def test_removed_editorial_spans_supply_no_manufactured_positional_context(tmp_path, monkeypatch):
    row = {"urn": "herodas.mimiambi", "locus": "mixed", "text": "λόγος μένει",
        "editorial_role_review": {"authority": role.AUDIT + "/changes.json"},
        "source_spans": [{"start": 0, "end": 5}, {"start": 24, "end": 29}]}
    checked = []
    def segments(candidate):
        checked.append(candidate)
        return ["λόγος", "μένει"]
    import herodas_current_state
    monkeypatch.setattr(herodas_current_state, "role_lexical_segments", segments)
    frequency = FrequencyProjection(tmp_path)
    assert frequency.text(row) == "λόγος μένει"
    assert frequency.segments(row) == ["λόγος", "μένει"]
    assert frequency.contextual_text(row) is None
    assert checked  # eligibility is still checked before withholding context


def test_cached_phoenix_projection_rechecks_changed_role_evidence_contents(admitted):
    root, _, _, _ = admitted
    row = json.loads((root / frozen.PRIMARY).read_bytes().splitlines()[0])
    assert phoenix.lexical_segments(row, root)
    path = root / state.AUDIT / "source-review.json"
    original = path.read_bytes()
    stamp = path.stat()
    path.write_bytes(original.replace(b"pinned", b"forged"))
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    assert path.stat().st_size == stamp.st_size
    with pytest.raises(ValueError, match="output changed"):
        phoenix.lexical_segments(row, root)


def test_cached_phoenix_projection_keeps_exact_row_and_private_segments(admitted):
    root, _, _, _ = admitted
    row = json.loads((root / frozen.PRIMARY).read_bytes().splitlines()[0])
    first = phoenix.lexical_segments(row, root)
    expected = list(first)
    first[0] = "modified returned list"
    assert phoenix.lexical_segments(row, root) == expected
    bad = dict(row, analysis_text="unreviewed reading")
    with pytest.raises(ValueError, match="postimage"):
        phoenix.lexical_segments(bad, root)
