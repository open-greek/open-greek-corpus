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


def test_preexisting_view_is_not_reinterpreted_as_a_new_alias_change(tmp_path):
    state._overlay(ROOT, tmp_path, {state.ALIASES.parts: original_aliases()})
    with state.prior_alias_view(tmp_path) as previous:
        assert previous == tmp_path

