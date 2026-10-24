"""Exact First1K duplicate consolidation preserves text, citations and IDs."""
import base64
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_pindar_duplicate_primaries as repair
from build_id_registry import Ledger


@pytest.fixture
def corpus(tmp_path):
    before = repair.archived_inputs(ROOT)
    for name in repair.input_pins():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(before[name])
    target = tmp_path / "scripts/repair_pindar_duplicate_primaries.py"
    target.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts/repair_pindar_duplicate_primaries.py", target)
    entries = {}
    for pair in repair.PAIRS:
        for key, slug in ((pair["old_id"], pair["old"]), (pair["canonical_id"], pair["canonical"])):
            entries[key] = {"slug": slug, "former_slugs": [], "status": "served"}
    (tmp_path / "data/work_ids.json").write_text(json.dumps({"works": entries}))
    unrelated = tmp_path / "data/corpus/unrelated.work.jsonl"
    unrelated.write_bytes(b'{"text":"unchanged"}\n')
    return tmp_path


def refresh_ids(root):
    path = root / "data/work_ids.json"
    entries = json.loads(path.read_bytes())["works"]
    ledger = Ledger("ogc", entries)
    ledger.refresh_status({path.stem for path in (root / "data/corpus").glob("*.jsonl")})
    path.write_text(json.dumps({"works": ledger.entries}))


def test_reader_index_preserves_old_citations_and_redirects_without_reassigning_ids(corpus, monkeypatch):
    import build_work_index as index
    repair.apply(corpus)
    refresh_ids(corpus)
    works = {pair["canonical"]: {"id": pair["canonical_id"]} for pair in repair.PAIRS}
    fragment = repair.alias_fragment(corpus)
    monkeypatch.setattr(index, "REPO", corpus)
    monkeypatch.setattr(index, "_active_passage_alias_fragments", lambda root: [fragment])
    aliases, authorities = index.load_active_passage_aliases(corpus / "data/passage_aliases.json", works)
    redirects = index.active_canonical_redirects(corpus, works, {})
    reader = {"works": works, "redirects": redirects, "passage_aliases": aliases}
    assert authorities[0]["retired_sources"] == fragment["retired_sources"]
    for pair in repair.PAIRS:
        old = pair["old"]
        assert redirects[old] == pair["canonical"]
        locus = next(iter(aliases[old]))
        assert index.resolve_citation(reader, old, locus)["storage"] == "secondary"
        assert index.resolve_citation(reader, old, "not-an-old-locus")["slug"] == pair["canonical"]


@pytest.mark.parametrize("mutation", ["wrong_id", "wrong_slug", "live_source", "collision"])
def test_reader_index_rejects_unproved_duplicate_redirects(corpus, monkeypatch, mutation):
    import build_work_index as index
    repair.apply(corpus)
    refresh_ids(corpus)
    works = {pair["canonical"]: {"id": pair["canonical_id"]} for pair in repair.PAIRS}
    fragment = repair.alias_fragment(corpus)
    old = repair.PAIRS[0]["old"]
    if mutation == "wrong_id":
        fragment["canonical_redirects"][old]["target_id"] = repair.PAIRS[1]["canonical_id"]
    elif mutation == "wrong_slug":
        fragment["canonical_redirects"][old]["slug"] = repair.PAIRS[1]["canonical"]
    elif mutation == "live_source":
        works[old] = {"id": repair.PAIRS[0]["old_id"]}
    monkeypatch.setattr(repair, "alias_fragment", lambda root: fragment)
    redirects = {old: "other.work"} if mutation == "collision" else {}
    with pytest.raises(ValueError, match="differs from its ledger"):
        index.active_canonical_redirects(corpus, works, redirects)


def test_exact_repair_preserves_canonical_bytes_and_every_original_row(corpus):
    before = repair.archived_inputs(corpus)
    audit = repair.apply(corpus, recorded_at="2026-10-24T00:00:00+00:00")
    assert audit["counts"] == {"pairs": 4, "original_primary_rows": 12,
        "primary_rows": 6, "secondary_rows": 6, "original_primary_analysis_tokens": 2890,
        "analysis_tokens": 1445, "duplicate_analysis_tokens_removed": 1445}
    for pair in repair.PAIRS:
        assert not (corpus / repair.primary(pair["old"])).exists()
        assert (corpus / repair.primary(pair["canonical"])).read_bytes() == before[repair.primary(pair["canonical"])]
        literal = [json.loads(line) for line in
            (corpus / f"data/corpus_secondary/{pair['canonical']}.jsonl").read_bytes().splitlines()]
        original = [json.loads(line) for line in before[repair.primary(pair["old"])].splitlines()]
        assert [row["original_row"] for row in literal] == original
        assert [row["text"] for row in literal] == [row["text"] for row in original]
        assert all(row["license"] == "CC-BY-SA-4.0" and not row["independent_witness"] for row in literal)
    assert (corpus / "data/corpus/unrelated.work.jsonl").read_bytes() == b'{"text":"unchanged"}\n'
    assert repair.verify(corpus)[0] == audit


def test_exact_undo_and_reapply_are_byte_stable(corpus):
    before = repair.archived_inputs(corpus)
    audit = repair.apply(corpus, recorded_at="2026-10-24T00:00:00+00:00")
    authority = (corpus / repair.AUDIT / "changes.json").read_bytes()
    outputs = {name: (corpus / name).read_bytes() if (corpus / name).exists() else None
               for name in audit["outputs"]}
    repair.undo(corpus)
    assert not repair.active(corpus)
    assert repair.alias_fragment(corpus) is None
    for name, raw in before.items():
        assert (corpus / name).read_bytes() == raw
    repair.apply(corpus)
    assert (corpus / repair.AUDIT / "changes.json").read_bytes() == authority
    assert {name: (corpus / name).read_bytes() if (corpus / name).exists() else None
            for name in outputs} == outputs


def test_aliases_keep_original_citations_and_both_immutable_identifiers(corpus):
    original_ledger = json.loads((corpus / "data/work_ids.json").read_bytes())["works"]
    repair.apply(corpus)
    with pytest.raises(ValueError, match="immutable identifier ledger"):
        repair.alias_fragment(corpus)  # rebuild status first, never reassign an ID
    refresh_ids(corpus)
    fragment = repair.alias_fragment(corpus)
    ledger = json.loads((corpus / "data/work_ids.json").read_bytes())["works"]
    assert set(ledger) == set(original_ledger)
    for pair in repair.PAIRS:
        assert ledger[pair["old_id"]]["slug"] == pair["old"]
        assert ledger[pair["old_id"]]["status"] == "retired"
        assert ledger[pair["canonical_id"]] == original_ledger[pair["canonical_id"]]
        assert fragment["retired_sources"][pair["old"]] == pair["old_id"]
        assert fragment["canonical_redirects"][pair["old"]] == {
            "slug": pair["canonical"], "source_id": pair["old_id"], "target_id": pair["canonical_id"]}
        for old_locus, target in fragment["aliases"][pair["old"]].items():
            assert target["current"]["slug"] == pair["canonical"]
            assert target["current"]["locus"] == old_locus
            assert target["storage"] == "secondary"


@pytest.mark.parametrize("field", ["urn", "license", "text", "locus", "edition"])
def test_no_field_other_than_urn_is_ignored_when_matching(corpus, field):
    before = repair.archived_inputs(corpus)
    name = repair.primary(repair.PAIRS[0]["old"])
    rows = [json.loads(line) for line in before[name].splitlines()]
    rows[0][field] = "wrong"
    # The fixed input pin rejects even an apparently harmless same-size change.
    before[name] = repair.jsonl(rows)
    with pytest.raises(ValueError, match="source input changed"):
        repair.build(corpus, before, recorded_at="fixed")


def test_both_current_and_archived_source_changes_are_detected(corpus):
    path = corpus / repair.source_path(repair.PAIRS[0])
    original = path.read_bytes()
    path.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="source input changed"):
        repair.apply(corpus)
    path.write_bytes(original)
    repair.apply(corpus)
    captured = corpus / repair.AUDIT / "sources" / (repair.PAIRS[0]["old"] + ".xml.gz")
    captured.write_bytes(captured.read_bytes() + b" ")
    with pytest.raises(ValueError, match="neither fully active"):
        repair.verify(corpus)


def test_changed_recipe_rejects_verification_but_undo_remains_available(corpus):
    repair.apply(corpus)
    script = corpus / "scripts/repair_pindar_duplicate_primaries.py"
    script.write_bytes(script.read_bytes() + b"\n# changed\n")
    with pytest.raises(ValueError, match="recipe"):
        repair.verify(corpus)
    repair.undo(corpus)
    assert (corpus / repair.primary(repair.PAIRS[0]["old"])).exists()


def test_changed_output_cannot_be_overwritten_by_undo(corpus):
    repair.apply(corpus)
    path = corpus / repair.primary(repair.PAIRS[0]["canonical"])
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="later Pindar output"):
        repair.undo(corpus)


def test_joint_output_and_audit_hash_forgery_fails_replay(corpus):
    repair.apply(corpus)
    path = corpus / repair.RECORDS
    path.write_bytes(gzip.compress(b'{"forged":true}\n', mtime=0))
    manifest = corpus / repair.AUDIT / "changes.json"
    audit = json.loads(manifest.read_bytes())
    audit["outputs"][repair.RECORDS] = repair.sha(path.read_bytes())
    manifest.write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError, match="literal replay differs"):
        repair.verify(corpus)


def test_unowned_secondary_output_is_never_overwritten(corpus):
    path = corpus / f"data/corpus_secondary/{repair.PAIRS[0]['canonical']}.jsonl"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"unrelated secondary\n")
    with pytest.raises(ValueError, match="unowned Pindar destination"):
        repair.apply(corpus)
    assert path.read_bytes() == b"unrelated secondary\n"


def test_invented_new_destination_preimage_is_rejected(corpus):
    repair.apply(corpus)
    archive = corpus / repair.AUDIT / "before.json.gz"
    before = json.loads(gzip.decompress(archive.read_bytes()))
    before[repair.RECORDS] = base64.b64encode(b"invented preimage").decode()
    archive.write_bytes(gzip.compress(repair.encoded(before), mtime=0))
    manifest = corpus / repair.AUDIT / "changes.json"
    audit = json.loads(manifest.read_bytes())
    audit["before_sha256"] = repair.sha(archive.read_bytes())
    manifest.write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError, match="invented preimage"):
        repair.verify(corpus)


def test_first1k_rebuild_without_crosswalk_does_not_recreate_raw_keys(corpus, monkeypatch):
    import build_corpus_loci as ingest
    repair.apply(corpus)
    monkeypatch.setattr(ingest, "SRC", corpus / "sources")
    monkeypatch.setattr(ingest, "DATA", corpus / "data")
    monkeypatch.setattr(ingest, "CORPUS", corpus / "data/corpus")
    monkeypatch.setattr(ingest, "NON_TEI_KEEP", corpus / "data/non_tei_authoritative.json")
    monkeypatch.setattr(ingest, "BEKKER_CONCORD", corpus / "data/bekker_concordance.json")
    monkeypatch.setattr(ingest, "slug_for", lambda urn: urn)
    monkeypatch.setattr(ingest, "load_text_corrections", lambda: {})
    monkeypatch.setattr(ingest, "load_order_overrides", lambda: {})
    monkeypatch.setattr(sys, "argv", ["build_corpus_loci.py", "--only", "tlg4170"])
    ingest.main()
    for pair in repair.PAIRS:
        assert not (corpus / repair.primary(pair["old"])).exists()
        assert (corpus / repair.primary(pair["canonical"])).is_file()
    # A source rebuild is also byte-identical to the retained canonical rows.
    repair.verify(corpus)


def test_conflicting_ingestion_concordance_is_rejected():
    with pytest.raises(ValueError, match="identity conflicts"):
        repair.ingestion_slug("tlg4170.tlg001a", "another.work")
    assert repair.ingestion_slug("tlg9999.tlg001", "another.work") == "another.work"
    assert repair.ingestion_slug("tlg4170.tlg001a",
        "vitae-pindari-et-varia-de-pindaro.tlg4170-tlg001a") == repair.PAIRS[0]["canonical"]


def test_publish_failure_restores_every_original_byte(corpus, monkeypatch):
    before = repair.archived_inputs(corpus)
    original_replace = repair.os.replace
    calls = 0

    def failed_replace(source, target):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("injected write failure")
        return original_replace(source, target)

    monkeypatch.setattr(repair.os, "replace", failed_replace)
    with pytest.raises(OSError, match="injected write failure"):
        repair.apply(corpus)
    for name, raw in before.items():
        assert (corpus / name).read_bytes() == raw
    assert not (corpus / repair.AUDIT / "changes.json").exists()


def test_orphaned_authority_cannot_authorize_a_partial_repair(corpus):
    authority = corpus / repair.AUDIT / "changes.json"
    authority.parent.mkdir(parents=True)
    authority.write_text("{}")
    with pytest.raises(ValueError, match="orphaned"):
        repair.apply(corpus)
