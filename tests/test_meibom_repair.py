"""A multi-author OCR delivery must split, merge, and reverse reproducibly."""
import hashlib
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_meibom_work_assignments as repair
import build_work_index as index


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(repair.dump(value))


def fixture(root, monkeypatch, primary_source="meibom1652"):
    registry = {"works": {slug: {"aliases": {"cts": "urn:cts:cogGreek:" + slug},
        "editions": {}, "default_edition": None} for slug in {r[2] for r in repair.RANGES}}}
    registry["works"][repair.OLD].update(default_edition="old")
    registry["works"][repair.OLD]["editions"]["old"] = {"servable": True}
    rows = [{"urn": repair.OLD, "edition": "old", "source": "ocr", "license": "PD",
        "locus": f"aristides_quintilianus_meibom_{scan:04d}.1", "text": "ὁ δὲ λόγος σαφής"}
        for scan in [1, 53, 60, 65, 201, 223, 279, 307, 347, 431, 481, 525, 614, 650, 681, 700]]
    primary = root / f"data/corpus/{repair.OLD}.jsonl"
    primary.parent.mkdir(parents=True)
    primary.write_bytes(repair.jsonl(rows))
    monkeypatch.setattr(repair, "INPUT_SHA256", hashlib.sha256(primary.read_bytes()).hexdigest())
    write(root / "data/source_registry.json", registry)
    write(root / "data/passage_aliases.json", {"schema_version": 1, "aliases": {}})
    write(root / "data/inventory/ocr_edition_sources.json", {})
    fresh = []
    for model in ["Qwen3.6-27B", "Qwen3.8-27B"]:
        path = root / (model + ".jsonl")
        records = [{"_meta": {"model": model, "revision": "pinned", "prompt": "Greek only", "backend": "test"}}]
        jobs = repair.fresh_jobs()["pages"] if primary_source == "meibom1652" else json.loads(
            (ROOT / "data/ingest_reviews/jahn-aristides-fresh-witnesses.json").read_text())["pages"]
        for job in jobs:
            records.append({"scan_page": job["scan_page"], "region": job["region"],
                "raw_prediction": "ὁ δὲ λόγος σαφής", "finish_reason": "stop",
                "image_sha256": str(job["scan_page"])})
        path.write_bytes(repair.jsonl(records))
        fresh.append(path)
    return rows, fresh


def test_apply_routes_all_authors_merges_all_pages_and_undo_is_exact(tmp_path, monkeypatch):
    original_rows, fresh = fixture(tmp_path, monkeypatch)
    before = {str(path.relative_to(tmp_path)): path.read_bytes() for path in (tmp_path / "data").rglob("*") if path.is_file()}
    repair.run_repair(tmp_path, "apply", fresh, primary_source="meibom1652")
    repair.run_repair(tmp_path, "check")
    primary = [json.loads(line) for line in (tmp_path / f"data/corpus/{repair.OLD}.jsonl").read_text().splitlines()]
    assert len(primary) == 164
    assert primary[0]["locus"] == "1.1" and primary[-1]["locus"] == "3.164"
    assert all(row["analysis_text"] == "ὁ δὲ λόγος σαφής" for row in primary)
    paratext = [json.loads(line) for line in (tmp_path / repair.PARATEXT).read_text().splitlines()]
    assert {r["source_page"]["scan_page"] for r in paratext} == {1, 53, 60}
    aliases = json.loads((tmp_path / "data/passage_aliases.json").read_text())["aliases"]
    target = aliases[repair.OLD]["aristides_quintilianus_meibom_0201.1"]
    assert target["slug"] == "cleonides.introductio-harmonica"
    assert target["storage"] == "secondary"
    assert aliases[repair.OLD]["aristides_quintilianus_meibom_0614.1"]["locus"] == "2.84"
    assert aliases[repair.OLD]["aristides_quintilianus_meibom_0650.1"]["locus"] == "3.114"
    monkeypatch.setattr(index, "REPO", tmp_path)
    index.validate_passage_aliases(aliases, {slug: {} for slug in {r[2] for r in repair.RANGES}})
    audit = json.loads((tmp_path / repair.AUDIT_DIR / "changes.json").read_text())
    assert [change["original_row"] for change in audit["assignments"]] == original_rows
    assert all(not change["text_changed"] for change in audit["assignments"])
    repair.run_repair(tmp_path, "undo")
    for name, expected in before.items():
        assert (tmp_path / name).read_bytes() == expected
    assert not (tmp_path / repair.PARATEXT).exists()
    assert not list((tmp_path / "data/corpus_secondary").glob("*.jsonl"))


def test_jahn_primary_keeps_every_old_meibom_reference_at_its_exact_secondary_text(tmp_path, monkeypatch):
    old, fresh = fixture(tmp_path, monkeypatch, primary_source="jahn1882")
    repair.run_repair(tmp_path, "apply", fresh)
    repair.run_repair(tmp_path, "check")
    primary = [json.loads(line) for line in (tmp_path / f"data/corpus/{repair.OLD}.jsonl").read_text().splitlines()]
    assert len(primary) == 97
    assert primary[0]["edition"] == repair.JAHN_EDITION
    assert primary[37]["locus"] == "2.38"
    assert primary[67]["locus"] == "3.68"
    assert primary[-1]["locus"] == "3.97"
    assert all(len(row["ocr_consensus"]["witnesses"]) == 2 for row in primary)
    aliases = json.loads((tmp_path / "data/passage_aliases.json").read_text())["aliases"][repair.OLD]
    for row in old:
        if repair.page_assignment(repair.scan_from_locus(row["locus"]))["work"] == repair.OLD:
            destination = aliases[row["locus"]]
            assert destination["storage"] == "secondary"
            assert destination["locus"] == row["locus"]
            preserved = [json.loads(line) for line in (tmp_path / destination["path"]).read_text().splitlines()]
            assert next(r["text"] for r in preserved if r["locus"] == row["locus"]) == row["text"]
    audit = json.loads((tmp_path / repair.AUDIT_DIR / "changes.json").read_text())
    assert audit["primary_source"]["sha256"] == "8ccfbe7e5c43dd4210235296fae29d2b8ffdce2f910e50a80c822e7eee5539c6"
    assert audit["primary_edition"] == repair.JAHN_EDITION


def test_fresh_ocr_requires_two_models_and_checked_geometry(tmp_path, monkeypatch):
    rows, fresh = fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="Two fresh model witnesses"):
        repair.prepare_inputs(tmp_path, fresh[:1], primary_source="meibom1652")
    records = [json.loads(line) for line in fresh[0].read_text().splitlines()]
    records[1]["region"] = [.02, .03, .52, .97]
    fresh[0].write_bytes(repair.jsonl(records))
    with pytest.raises(ValueError, match="unchecked crop"):
        repair.prepare_inputs(tmp_path, fresh, primary_source="meibom1652")


@pytest.mark.parametrize("updates, message", [
    ({"finish_reason": "length"}, "truncated"),
    ({"finish_reason": "error", "error": "request failed"}, "complete successfully"),
    ({"finish_reason": None}, "complete successfully"),
    ({"raw_prediction": "   "}, "no Greek reading"),
    ({"raw_prediction": "A failed request"}, "no Greek reading"),
])
def test_failed_fresh_attempts_cannot_satisfy_the_two_witness_requirement(tmp_path, monkeypatch, updates, message):
    rows, fresh = fixture(tmp_path, monkeypatch)
    records = [json.loads(line) for line in fresh[0].read_text().splitlines()]
    records[1].update(updates)
    fresh[0].write_bytes(repair.jsonl(records))
    with pytest.raises(ValueError, match=message):
        repair.prepare_inputs(tmp_path, fresh, primary_source="meibom1652")
    assert not (tmp_path / repair.AUDIT_DIR).exists()


def test_metadata_replay_allows_unrelated_changes_but_refuses_changed_assignments():
    before = {"works": {"old": {"title": "unchanged"}}}
    expected = {"works": {"old": {"title": "unchanged", "edition": "merged"}}}
    current = {"works": {"old": {"title": "unchanged", "edition": "merged"}, "other": {"title": "new"}}}
    repair.check_changed_fields(before, expected, current, "registry")
    current["works"]["old"]["edition"] = "wrong"
    with pytest.raises(ValueError, match="Changed Meibom metadata"):
        repair.check_changed_fields(before, expected, current, "registry")


def test_secondary_aliases_require_explicit_storage_and_matching_work(tmp_path, monkeypatch):
    monkeypatch.setattr(index, "REPO", tmp_path)
    path = tmp_path / "data/corpus_secondary/work.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text('{"locus":"1","text":"λόγος"}\n')
    target = {"path": "data/corpus_secondary/work.jsonl", "locus": "1", "slug": "work"}
    with pytest.raises(ValueError, match="Invalid passage alias work"):
        index.validate_passage_aliases({"work": {"old": target}}, {"work": {}})
    target["storage"] = "secondary"
    assert index.validate_passage_aliases({"work": {"old": target}}, {"work": {}})


def test_jahn_job_manifest_reproduces_all_books_and_stops_above_the_index():
    path = ROOT / "data/ingest_reviews/jahn-aristides-fresh-witnesses.json"
    doc = json.loads(path.read_text())
    pages = doc["pages"]
    assert [p["scan_page"] for p in pages] == list(range(74, 171))
    assert [p["printed_page"] for p in pages] == list(range(1, 98))
    assert [sum(p["book"] == book for p in pages) for book in [1, 2, 3]] == [37, 30, 30]
    assert pages[-1]["region"][3] == .4
    review = json.loads(path.with_name("jahn-layout-review.json").read_text())
    assert review["manifest_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert review["checked_scan_pages"] == list(range(74, 171))


def test_jahn_initial_running_head_preserves_raw_misread_label_and_offsets():
    raw = "\nΠΕΡΙ ΜΟΥΣΙΚΗΣ Β.\n97\nταῖς ψυχαῖς λόγος\n"
    page = {"scan_page": 170, "printed_page": 97, "book": 3}
    cleaned, edits = repair.clean_jahn_running_headers(raw, page)
    assert cleaned == "\n97\nταῖς ψυχαῖς λόγος\n"
    assert len(edits) == 1
    edit = edits[0]
    assert edit["authority_book"] == 3
    assert edit["original_text"] == raw[edit["start"]:edit["end"]] == "ΠΕΡΙ ΜΟΥΣΙΚΗΣ Β.\n"
    assert edit["corrected_text"] == ""
    assert edit["source"] and edit["timestamp"]
    restored = cleaned[:edit["start"]] + edit["original_text"] + cleaned[edit["start"]:]
    assert restored == raw


@pytest.mark.parametrize("scan,book", [(74, 1), (111, 2), (141, 3)])
def test_genuine_jahn_book_opening_titles_survive(scan, book):
    raw = "ΑΡΙΣΤΕΙΔΟΥ ΤΟΥ ΚΟΙΝΤΙΛΙΑΝΟΥ\nΠΕΡΙ ΜΟΥΣΙΚΗΣ\nΒιβλίον πρῶτον.\nλόγος"
    assert repair.clean_jahn_running_headers(raw, {"scan_page": scan, "printed_page": scan - 73, "book": book}) == (raw, [])


def test_jahn_running_head_rule_never_searches_through_authored_body():
    raw = "λέγει περὶ μουσικῆς ὁ λόγος\nΠΕΡΙ ΜΟΥΣΙΚΗΣ Α.\n"
    assert repair.clean_jahn_running_headers(raw, {"scan_page": 75, "printed_page": 2, "book": 1}) == (raw, [])


def test_jahn_admission_archives_full_network_and_preprocessing_for_replay(tmp_path, monkeypatch):
    old, fresh = fixture(tmp_path, monkeypatch, "jahn1882")
    original = "ΠΕΡΙ ΜΟΥΣΙΚΗΣ Β.\n97\nὁ δὲ λόγος σαφής"
    for path in fresh:
        records = [json.loads(line) for line in path.read_text().splitlines()]
        next(row for row in records if row.get("scan_page") == 170)["raw_prediction"] = original
        path.write_bytes(repair.jsonl(records))
    repair.run_repair(tmp_path, "apply", fresh)
    repair.run_repair(tmp_path, "check")
    primary = [json.loads(line) for line in (tmp_path / f"data/corpus/{repair.OLD}.jsonl").read_text().splitlines()]
    assert primary[-1]["analysis_text"] == "ὁ δὲ λόγος σαφής"
    assert "ΠΕΡΙ" not in primary[-1]["text"]
    assert all(w["original_text"] == original for w in primary[-1]["ocr_consensus"]["witnesses"])
    archive = json.loads(gzip.decompress((tmp_path / repair.AUDIT_DIR / "word-networks.json.gz").read_bytes()))
    from ocr_consensus import restore_corpus_consensus
    compact = {key: primary[-1][key] for key in ("text", "analysis_text", "ocr_consensus")}
    assert restore_corpus_consensus(compact, archive["97"]) == archive["97"]
    audit = json.loads((tmp_path / repair.AUDIT_DIR / "changes.json").read_text())
    final = audit["text_changes"][-1]
    assert all(w["text"] == original and w["preprocessing"][0]["authority_book"] == 3 for w in final["original_text"])
