"""Source, projection, and byte-exact reversal gates for the missing leaf."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_hesychius_missing_columns as repair


@pytest.fixture
def corpus(tmp_path):
    for name in repair.recipe_pins():
        path = tmp_path / "scripts" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "scripts" / name, path)
    for name in (repair.PRIMARY, *repair.OCR_FILES, repair.AUDIT + "/source-evidence.json"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == repair.PRIMARY and repair.active(ROOT):
            from hesychius_gap_state import predecessor_bytes
            path.write_bytes(predecessor_bytes(ROOT))
        else:
            shutil.copyfile(ROOT / name, path)
    capture = json.loads((ROOT / repair.AUDIT / "source-evidence.json").read_bytes())
    for row in [*capture["images"], *capture["columns"]]:
        path = tmp_path / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / row["path"], path)
    return tmp_path


def test_editorial_scopes_preserve_literal_partition():
    text = "† αὐθόρης· αὐτὸς βλέπων. ἀ(υχ)άν· ἀλκήν. [μάνδρας] τέλος"
    retained, excluded = repair.source_role_spans(text)
    assert "".join(row["text"] for row in sorted(retained + excluded, key=lambda r: r["start"])) == text
    assert {row["text"] for row in excluded} == {"† αὐθόρης", "ἀ(υχ)άν", "[μάνδρας]"}
    assert "αὐτὸς βλέπων" in " ".join(row["text"] for row in retained)


def test_source_reviewed_dagger_cannot_be_lost_by_ocr():
    retained, excluded = repair.source_role_spans("αὐλεῖται· ἀκροαταὶ αὐλοῦντες", column=260)
    assert excluded[0]["text"] == "αὐλεῖται·"
    assert "ἀκροαταὶ αὐλοῦντες" in retained[0]["text"]
    _, excluded = repair.source_role_spans("ἡ αὐλεῖται· ἀκροαταὶ αὐλοῦντες", column=260)
    assert excluded[0]["text"] == "ἡ αὐλεῖται·"
    retained, excluded = repair.source_role_spans("ἢ + κίλλα τις δίδυμος")
    assert excluded[0]["text"] == "+ κίλλα"
    _, excluded = repair.source_role_spans("Πέρσαι <Περγαῖοι>. τέλος ⟨ἄλλο⟩")
    assert [row["text"] for row in excluded] == ["<Περγαῖοι>", "⟨ἄλλο⟩"]


@pytest.mark.parametrize("text", ["λέξις [ἄλλο", "λέξις )", "λέξις ([ἄλλο)]"])
def test_unbalanced_editorial_signs_fail_closed(text):
    with pytest.raises(ValueError, match="editorial scope"):
        repair.source_role_spans(text)


def test_full_source_replay_and_exact_undo_reapply(corpus):
    before = (corpus / repair.PRIMARY).read_bytes()
    audit = repair.apply(corpus, recorded_at="2026-10-24T00:00:00+00:00")
    assert repair.verify(corpus)[0] == audit
    assert audit["counts"]["primary_columns_added"] == 2
    assert audit["counts"]["literal_witnesses"] == 8
    assert repair.predecessor_bytes(corpus) == before
    raw = (corpus / repair.PRIMARY).read_bytes()
    # Removing only the two declared insertions must recover every old byte.
    stripped = b"".join(line for line in raw.splitlines(keepends=True)
        if json.loads(line).get("edition") != repair.EDITION)
    assert stripped == before
    additions = [json.loads(line) for line in raw.splitlines()
        if json.loads(line).get("edition") == repair.EDITION]
    assert [row["source_printed_columns"] for row in additions] == [[259], [260]]
    for row in additions:
        assert repair.validate_projection(row, corpus) == row["analysis_text"]
        assert repair.lexical_segments(row, corpus) == []
    output_sha = audit["outputs"]
    frozen_audit = (corpus / repair.AUTHORITY).read_bytes()
    repair.undo(corpus)
    assert not repair.active(corpus)
    assert (corpus / repair.PRIMARY).read_bytes() == before
    assert not (corpus / repair.WITNESSES).exists()
    repair.apply(corpus)
    assert (corpus / repair.AUTHORITY).read_bytes() == frozen_audit
    assert {name: repair.sha((corpus / name).read_bytes()) for name in output_sha} == output_sha


def test_evidence_invalidation_rejects_projection_but_allows_undo(corpus):
    repair.apply(corpus)
    row = next(json.loads(line) for line in (corpus / repair.PRIMARY).read_bytes().splitlines()
               if json.loads(line).get("edition") == repair.EDITION)
    repair.validate_projection(row, corpus)  # populate validated cache
    path = corpus / repair.AUDIT / "source-evidence/ghent-column-259.png"
    path.write_bytes(path.read_bytes() + b"invalidated")
    with pytest.raises(ValueError, match="source evidence changed"):
        repair.validate_projection(row, corpus)
    repair.undo(corpus)
    assert repair.sha((corpus / repair.PRIMARY).read_bytes()) == repair.PREDECESSOR_SHA256


def test_all_physical_scans_and_checkpoint_readings_are_required(corpus):
    path = corpus / repair.OCR_FILES[0]
    rows = path.read_bytes().splitlines(keepends=True)
    path.write_bytes(b"".join(rows[:-1]))
    with pytest.raises(ValueError, match="Pinned fresh Hesychius OCR artifact changed"):
        repair.apply(corpus)


def test_jointly_rehashed_output_cannot_forge_source_replay(corpus):
    repair.apply(corpus)
    path = corpus / repair.PRIMARY
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    target = next(row for row in rows if row.get("edition") == repair.EDITION)
    target["analysis_text"] += " πλαστόν"
    path.write_bytes(repair.jsonl(rows))
    audit_path = corpus / repair.AUTHORITY
    audit = json.loads(audit_path.read_bytes())
    audit["outputs"][repair.PRIMARY] = repair.sha(path.read_bytes())
    audit_path.write_bytes(repair.encode(audit))
    with pytest.raises(ValueError, match="source replay differs"):
        repair.verify(corpus)


def test_marker_stripping_and_recipe_changes_cannot_bypass_authority(corpus):
    repair.apply(corpus)
    row = next(json.loads(line) for line in (corpus / repair.PRIMARY).read_bytes().splitlines()
               if json.loads(line).get("edition") == repair.EDITION)
    stripped = dict(row)
    stripped.pop("hesychius_gap_recovery")
    with pytest.raises(ValueError, match="lexical projection differs"):
        repair.validate_projection(stripped, corpus)
    recipe = corpus / "scripts/hesychius_gap_observations.py"
    recipe.write_bytes(recipe.read_bytes() + b"\n# invalidated evidence\n")
    with pytest.raises(ValueError, match="recipe changed"):
        repair.verify(corpus)
    repair.undo(corpus)


def test_predecessor_and_neighborhood_are_exact(corpus):
    path = corpus / repair.PRIMARY
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="predecessor changed"):
        repair.apply(corpus)


def test_narrow_older_duplicate_undo_epoch_is_inactive(corpus):
    import repair_reviewed_duplicate_blocks as older
    repair.apply(corpus)
    repair.undo(corpus)
    # Reproduce the older layer's exact undo state, including all its outputs.
    before = older.archived_inputs(ROOT)
    for name in (older.AUDIT + "/changes.json", older.AUDIT + "/before.json.gz"):
        path = corpus / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    audit = json.loads((corpus / older.AUDIT / "changes.json").read_bytes())
    for name in audit["outputs"]:
        path = corpus / name
        if before[name] is None:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(before[name])
    assert not older.active(corpus)
    assert not repair.active(corpus)
    path = corpus / repair.PRIMARY
    path.write_bytes(path.read_bytes() + b"\n")
    assert repair.active(corpus)
