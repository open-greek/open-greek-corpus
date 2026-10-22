"""Later Phoenix citations must not invalidate frozen Photius source judgments."""
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import photius_current_state as state
import repair_phoenix_crusius as phoenix


def original_aliases():
    before = json.loads(gzip.decompress((ROOT / phoenix.AUDIT / "before.json.gz").read_bytes()))
    return before[phoenix.ALIASES].encode()


def test_only_new_unrelated_aliases_are_hidden_from_frozen_validators():
    current = (ROOT / state.ALIASES).read_bytes()
    corpus = (ROOT / state.CORPUS).read_bytes()
    with state.prior_alias_view(ROOT) as previous:
        assert (previous / state.ALIASES).read_bytes() == original_aliases()
        assert (previous / state.CORPUS).read_bytes() == corpus
        assert (previous / phoenix.PRIMARY).read_bytes() == (ROOT / phoenix.PRIMARY).read_bytes()
    assert (ROOT / state.ALIASES).read_bytes() == current
    assert state.final_metadata(ROOT)["counts"]["current_uncertainty_spans"] == 0


def test_existing_alias_modification_is_rejected(tmp_path):
    aliases = json.loads((ROOT / state.ALIASES).read_bytes())
    work = next(key for key in aliases["aliases"] if key != phoenix.WORK)
    locus = next(iter(aliases["aliases"][work]))
    aliases["aliases"][work][locus]["locus"] = "changed"
    state._overlay(ROOT, tmp_path, {state.ALIASES.parts: phoenix.encoded(aliases)})
    with pytest.raises(ValueError, match="output changed"):
        with state.prior_alias_view(tmp_path):
            pass


def test_alias_mutation_during_historical_validation_is_rejected(tmp_path):
    raw = (ROOT / state.ALIASES).read_bytes()
    state._overlay(ROOT, tmp_path, {state.ALIASES.parts: raw})
    with pytest.raises(ValueError, match="during predecessor"):
        with state.prior_alias_view(tmp_path):
            (tmp_path / state.ALIASES).write_bytes(raw + b" ")


def test_untrusted_mixed_state_cannot_claim_to_be_a_historical_view(tmp_path):
    state._overlay(ROOT, tmp_path, {state.ALIASES.parts: original_aliases()})
    with pytest.raises(ValueError, match="output changed"):
        with state.prior_alias_view(tmp_path):
            pass


def test_nested_views_are_authorized_by_the_materialized_alias_file():
    with state.prior_alias_view(ROOT) as previous:
        with state.continuation_view(previous) as older:
            with state.prior_alias_view(older) as nested:
                assert (nested / state.ALIASES).read_bytes() == original_aliases()


def test_source_drift_immediately_after_verification_is_rejected(tmp_path, monkeypatch):
    source = Path(phoenix.AUDIT) / "source-scan.pdf"
    state._overlay(ROOT, tmp_path, {source.parts: (ROOT / source).read_bytes()})
    original_verify = phoenix.verify
    def changed_after_verify(root):
        result = original_verify(root)
        (root / source).write_bytes((root / source).read_bytes() + b"changed")
        return result
    monkeypatch.setattr(phoenix, "verify", changed_after_verify)
    with pytest.raises(ValueError, match="during predecessor"):
        with state.prior_alias_view(tmp_path):
            pytest.fail("A changed source must not become visible in a checked view")


def test_exact_undo_is_recognized_without_requiring_an_invalidated_new_source(tmp_path):
    before = json.loads(gzip.decompress((ROOT / phoenix.AUDIT / "before.json.gz").read_bytes()))
    retained = Path(phoenix.RETAINED)
    scan = Path(phoenix.AUDIT) / "source-scan.pdf"
    overrides = {state.ALIASES.parts: before[phoenix.ALIASES].encode(),
        Path(phoenix.PRIMARY).parts: before[phoenix.PRIMARY].encode(), retained.parts: b"",
        scan.parts: b""}
    # This tests the historical Phoenix undo, before later independent role
    # admissions. Mixing that undo with newer active role aliases is invalid.
    import repair_editorial_roles as roles
    role_before = ROOT / roles.AUDIT / "before.json.gz"
    missing = []
    if role_before.exists():
        original = json.loads(gzip.decompress(role_before.read_bytes()))
        for path, text in original.items():
            if path != roles.ALIASES:
                overrides[Path(path).parts] = text.encode() if text is not None else b""
                if text is None:
                    missing.append(Path(path))
        authority = Path(roles.AUDIT) / "changes.json"
        overrides[authority.parts] = b""
        missing.append(authority)
    state._overlay(ROOT, tmp_path, overrides)
    for path in missing:
        (tmp_path / path).unlink()
    (tmp_path / retained).unlink()
    (tmp_path / scan).unlink()
    with state.prior_alias_view(tmp_path) as previous:
        assert previous == tmp_path


@pytest.mark.parametrize("relative", [phoenix.PRIMARY, phoenix.RETAINED,
    phoenix.AUDIT + "/source-review.json", phoenix.AUDIT + "/source-scan.pdf"])
def test_nested_alias_authorization_is_bound_to_source_and_postimage_pins(tmp_path, relative):
    path = Path(relative)
    with state.prior_alias_view(ROOT) as previous:
        state._overlay(previous, tmp_path, {path.parts: (previous / path).read_bytes() + b" "})
        with pytest.raises(ValueError, match="source authority"):
            with state.prior_alias_view(tmp_path):
                pytest.fail("A nested view must retain the verified Phoenix authority")


@pytest.mark.parametrize("nested", [False, True])
def test_active_or_nested_review_cannot_lose_its_authority(tmp_path, nested):
    authority = Path(phoenix.AUDIT) / "changes.json"
    def removed(root):
        state._overlay(root, tmp_path, {authority.parts: (root / authority).read_bytes()})
        (tmp_path / authority).unlink()
        with pytest.raises(ValueError, match="frozen authority"):
            with state.prior_alias_view(tmp_path):
                pytest.fail("A reviewed state cannot discard its source authority")
    if nested:
        with state.prior_alias_view(ROOT) as previous:
            removed(previous)
    else:
        removed(ROOT)

