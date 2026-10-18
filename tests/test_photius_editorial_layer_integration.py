"""Real pinned historical and fresh inputs replay through one later layer."""
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_photius_apparatus as layer
import repair_photius_body as body
import repair_photius_fresh as fresh
import repair_photius_index as index
import audit_photius_apparatus as old_audit


def copy_input(root, path):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / path, target)


def source_preimages(source):
    paths = (layer.AUDIT, layer.ARCHIVE / "before-corpus.jsonl.gz", layer.ARCHIVE / "before-aliases.json.gz")
    present = [(source / path).exists() for path in paths]
    if not any(present):
        return {path: (source / path).read_bytes() for path in (index.CORPUS, index.ALIASES)}
    if not all(present):
        raise ValueError("Integration fixture has incomplete frozen preimages")
    audit = json.loads((source / layer.AUDIT).read_bytes())
    before = {index.CORPUS: gzip.decompress((source / paths[1]).read_bytes()),
              index.ALIASES: gzip.decompress((source / paths[2]).read_bytes())}
    if any(layer.sha(raw) != audit["inputs"][path.as_posix()] for path, raw in before.items()):
        raise ValueError("Integration fixture frozen preimages differ from their audit")
    return before


def real_inputs(root):
    for path, raw in source_preimages(ROOT).items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    for path in (index.ARCHIVE / "before.jsonl.gz", index.PARATEXT,
                 index.ARCHIVE / "changes.json", layer.REVIEW, body.REVIEW, body.LIBRARY,
                 fresh.REVIEW, fresh.ORIGINAL_NETWORK):
        copy_input(root, path)
    authority = json.loads((root / fresh.REVIEW).read_bytes())
    for item in authority["records"]:
        copy_input(root, item["witness"]["raw_file"]["path"])
        copy_input(root, item["witness"]["manifest_path"])


def test_real_historical_and_fresh_corrections_have_one_exact_replay_and_undo(tmp_path, monkeypatch):
    real_inputs(tmp_path)
    copy_input(tmp_path, body.REVIEW7)
    before = (tmp_path / index.CORPUS).read_bytes()
    aliases_before = (tmp_path / index.ALIASES).read_bytes()
    old = {row["locus"]: row for row in map(json.loads, before.splitlines())}
    audit_before = old_audit.build(tmp_path)
    original_networks = (tmp_path / fresh.ORIGINAL_NETWORK).read_bytes()
    artifacts, audit = layer.build(tmp_path)
    assert audit["counts"]["body_corrected_rows"] == 2 and audit["counts"]["fresh_corrected_rows"] == 1
    assert audit["counts"]["moved_rows"] == 368 and audit["counts"]["mixed_rows"] == 21
    assert audit["fresh_correction"]["counts"]["witnesses_before"] == audit["fresh_correction"]["counts"]["witnesses_after"] == 2
    assert audit["fresh_correction"]["paratext"]["rows"] == 2
    layer.apply(tmp_path)
    # Full pytest also runs after the real checkout has been corrected. Its
    # fixtures must still start from the exact original coverage admission.
    monkeypatch.setattr(sys.modules[__name__], "ROOT", tmp_path)
    replica = tmp_path / "post-application-fixture"
    real_inputs(replica)
    assert (replica / index.CORPUS).read_bytes() == before
    assert (replica / index.ALIASES).read_bytes() == aliases_before
    assert len((replica / index.CORPUS).read_bytes().splitlines()) == 4155
    assert layer.check(tmp_path) == audit
    assert layer.restore_legacy_bytes((tmp_path / index.CORPUS).read_bytes(), tmp_path) == before
    assert old_audit.build(tmp_path) == audit_before
    index.check(tmp_path)
    updated = {row["locus"]: row for row in map(json.loads, (tmp_path / index.CORPUS).read_bytes().splitlines())}
    assert len(updated) == 3787
    assert all(updated[locus] == row for locus, row in old.items()
               if locus.startswith("photius_bekker1824_") and locus != fresh.LOCUS)
    assert updated[fresh.LOCUS]["ocr_consensus"]["full_network"]["path"].startswith(layer.ARCHIVE.as_posix())
    assert (tmp_path / fresh.ORIGINAL_NETWORK).read_bytes() == original_networks
    masked = next(w for w in updated[fresh.LOCUS]["ocr_consensus"]["witnesses"] if w["model"] == fresh.MODEL)
    assert masked["text"].startswith("ΤΑ ΠΕΡΙ ΗΡΑΚΛΕΙΔΗΝ.")
    assert len(masked["abstention_audit"]["excluded_spans"]) == 2
    assert len((tmp_path / fresh.PARATEXT).read_bytes().splitlines()) == 2
    metadata = layer.active_metadata(tmp_path)
    assert metadata["fresh_correction"]["paratext"]["license"] == "CC-BY-4.0"
    (tmp_path / fresh.REVIEW).write_bytes(b"source invalidated")
    with pytest.raises(ValueError, match="invalidated"):
        layer.check(tmp_path)
    layer.undo(tmp_path)
    assert (tmp_path / index.CORPUS).read_bytes() == before
    assert (tmp_path / index.ALIASES).read_bytes() == aliases_before
    assert not (tmp_path / layer.PARATEXT).exists() and not (tmp_path / fresh.PARATEXT).exists()
    assert (tmp_path / fresh.ORIGINAL_NETWORK).read_bytes() == original_networks
    assert gzip.decompress((tmp_path / layer.ARCHIVE / "fresh-before-networks.json.gz").read_bytes()) == gzip.decompress(original_networks)


def test_registry_exposes_separate_fresh_apparatus_with_exact_current_pins(tmp_path):
    from test_reviewed_manifestations import registry
    import reviewed_manifestations as reviewed
    real_inputs(tmp_path)
    report_path = Path("data/corpus_changes/photius-bekker-coverage/coverage.json")
    copy_input(tmp_path, report_path)
    report = json.loads((tmp_path / report_path).read_bytes())
    for path in [Path(item["path"]) for item in report["fresh_ocr_files"]] + [Path(report["source_library"]["body_comparison_audit"]["path"])]:
        copy_input(tmp_path, path)
    layer.apply(tmp_path)
    metadata = reviewed.register_reviewed_manifestations(registry("photius.bibliotheca"), tmp_path)["photius.bibliotheca"]
    components = metadata["coverage_composition"]["components"]
    assert components[0]["passages"] == 3477
    note = next(c for c in components if c.get("role") == "fresh-witness-editorial-paratext")
    assert note["passages"] == 2 and note["license"] == "CC-BY-4.0"
    assert note["paratext"]["sha256"] == layer.sha((tmp_path / fresh.PARATEXT).read_bytes())
    assert metadata["coverage_composition"]["editorial_layer"]["fresh_correction"]["counts"]["changed_rows"] == 1


def test_fixture_without_later_archives_preserves_the_pre_application_inputs(tmp_path):
    for path, raw in ((index.CORPUS, b"original corpus"), (index.ALIASES, b"original aliases")):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    assert source_preimages(tmp_path) == {index.CORPUS: b"original corpus", index.ALIASES: b"original aliases"}


@pytest.mark.parametrize("change", ["corpus", "aliases", "missing-audit", "missing-corpus", "missing-aliases"])
def test_fixture_rejects_changed_or_incomplete_frozen_preimages(tmp_path, change):
    archive = tmp_path / layer.ARCHIVE
    archive.mkdir(parents=True)
    before = {index.CORPUS: b"original corpus", index.ALIASES: b"original aliases"}
    (tmp_path / layer.AUDIT).write_bytes(layer.encode({"inputs": {path.as_posix(): layer.sha(raw) for path, raw in before.items()}}))
    corpus = archive / "before-corpus.jsonl.gz"
    aliases = archive / "before-aliases.json.gz"
    corpus.write_bytes(gzip.compress(before[index.CORPUS], mtime=0))
    aliases.write_bytes(gzip.compress(before[index.ALIASES], mtime=0))
    if change == "corpus": corpus.write_bytes(gzip.compress(b"changed corpus", mtime=0))
    elif change == "aliases": aliases.write_bytes(gzip.compress(b"changed aliases", mtime=0))
    elif change == "missing-audit": (tmp_path / layer.AUDIT).unlink()
    elif change == "missing-corpus": corpus.unlink()
    else: aliases.unlink()
    with pytest.raises(ValueError, match="frozen preimages"):
        source_preimages(tmp_path)
