"""Missing-column requests retain exact source bounds without accepting text."""
import copy
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import prepare_photius_body_recovery as recovery


def inputs(root):
    for path in (recovery.LIBRARY, Path("data/corpus_changes/photius-bekker-index/before.jsonl.gz"),
                 Path("data/corpus_changes/photius-bekker-coverage/coverage.json")):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)


def test_frozen_pilot_and_complete_column_requests_reproduce():
    artifacts = recovery.build()
    assert {path: raw for path, raw in artifacts.items()} == {path: (ROOT / path).read_bytes() for path in artifacts}
    assert recovery.sha(artifacts[recovery.PILOT]) == "6ae81dc89954c388f33bef855bd46090fa619a166c15e9e0eeb5ccfedd0de927"
    review = json.loads(artifacts[recovery.REVIEW])
    request, pilot = (json.loads(artifacts[p]) for p in (recovery.REQUEST, recovery.PILOT))
    assert len(request["pages"]) == 9 and len(pilot["pages"]) == 2
    assert pilot["pages"] == request["pages"][:2]
    assert [p["scan_page"] for p in pilot["pages"]] == [66, 73]
    assert request["source_review"]["sha256"] == recovery.sha(artifacts[recovery.REVIEW])
    assert not request["review"]["accepted_for_primary_ingest"]
    for region in review["regions"]:
        jobs = sorted([p for p in request["pages"] if p["reconstructs"] == region["id"]], key=lambda p: p["reading_order"])
        assert [p["region"] for p in jobs] == region["strip_regions"]
        assert all(a["region"][3] == b["region"][1] for a, b in zip(jobs, jobs[1:]))
        assert all(p["max_side"] == 3600 for p in jobs)
    window = review["regions"][1]["source_library_window"]
    assert window["original_text"].startswith("νομίζων οἴκαδε")
    assert window["held_spans"][0]["original_text"] == "βεβλεῦσθ’ "
    assert review["regions"][1]["leading_source_fragment"]
    assert review["source_library_credit"]["separate_api_notice"]["tdm_reservation"] == 1


def test_preparer_uses_immutable_legacy_rows_after_corpus_changes(tmp_path):
    inputs(tmp_path)
    corpus = tmp_path / "data/corpus/photius.bibliotheca.jsonl"
    corpus.parent.mkdir(parents=True)
    corpus.write_text('An unrelated later projection must not become the source anchor.\n')
    assert recovery.build(tmp_path) == recovery.build()


@pytest.mark.parametrize("change", ["digital", "legacy", "license", "overlap", "nan", "clipped-window"])
def test_source_or_geometry_changes_require_new_review(tmp_path, monkeypatch, change):
    inputs(tmp_path)
    if change == "digital":
        path = tmp_path / recovery.LIBRARY
        path.write_bytes(path.read_bytes() + b" ")
    elif change == "legacy":
        path = tmp_path / "data/corpus_changes/photius-bekker-index/before.jsonl.gz"
        rows = list(map(json.loads, gzip.decompress(path.read_bytes()).splitlines()))
        next(r for r in rows if r["locus"].endswith("_0066.1"))["text"] += " ἄλλο"
        path.write_bytes(gzip.compress(b"".join((json.dumps(r, ensure_ascii=False) + "\n").encode() for r in rows), mtime=0))
    elif change == "license":
        path = tmp_path / "data/corpus_changes/photius-bekker-coverage/coverage.json"
        report = json.loads(path.read_bytes());report["source_library"]["license"]["url"] = "PD"
        path.write_text(json.dumps(report))
    else:
        cases = copy.deepcopy(recovery.CASES)
        if change == "overlap": cases[66]["cuts"][2] = cases[66]["cuts"][1]
        elif change == "nan": cases[66]["x"][0] = float("nan")
        else: cases[73]["window"][0] -= 1
        monkeypatch.setattr(recovery, "CASES", cases)
    with pytest.raises(ValueError):
        recovery.build(tmp_path)


def test_remaining_request_is_independent_and_reproduces_exact_boundaries():
    frozen = recovery.build()
    artifacts = recovery.build_remaining()
    assert artifacts == {path: (ROOT / path).read_bytes() for path in artifacts}
    assert recovery.build() == frozen
    assert set(artifacts).isdisjoint(frozen)
    review, request = (json.loads(artifacts[p]) for p in (recovery.REMAINING_REVIEW, recovery.REMAINING_REQUEST))
    assert {r["scan_page"] for r in review["regions"]} == {79, 90, 100, 148, 154, 189}
    assert len(request["pages"]) == 25
    assert request["source_review"]["sha256"] == recovery.sha(artifacts[recovery.REMAINING_REVIEW])
    assert request["sources"]["photius-bekker-legacy"]["sha256"] == recovery.PDF_SHA
    assert request["prompt"] == json.loads(frozen[recovery.REQUEST])["prompt"]
    assert review["source_library_credit"]["separate_api_notice"]["tdm_reservation"] == 1
    assert not request["review"]["accepted_for_primary_ingest"]
    for case in review["regions"]:
        parts = [p for p in request["pages"] if p["reconstructs"] == case["id"]]
        assert [p["region"] for p in parts] == case["strip_regions"]
        assert [p["reading_order"] for p in parts] == list(range(1, len(parts) + 1))
        assert all(a["region"][3] == b["region"][1] for a, b in zip(parts, parts[1:]))
        assert parts[0]["region"][:3:2] == case["region"][:3:2]
        assert parts[0]["region"][1] == case["region"][1]
        assert parts[-1]["region"][3] == case["region"][3]
        assert all(p["max_side"] == 3600 for p in parts)
        for anchor in case["legacy_anchors"]:
            assert recovery.row_sha(anchor["original_row"]) == anchor["row_sha256"]


def test_remaining_whole_word_completions_and_context_are_held():
    artifacts = recovery.build_remaining()
    review = json.loads(artifacts[recovery.REMAINING_REVIEW])
    cases = {r["scan_page"]: r for r in review["regions"]}
    assert cases[90]["leading_source_fragment"] == "νεύσαντες."
    assert cases[90]["trailing_source_fragment"] == "φερο-"
    assert cases[100]["leading_source_fragment"] == "ποις"
    assert cases[100]["trailing_source_fragment"] == "πολ-"
    assert cases[154]["leading_source_fragment"] == "κειτο"
    assert cases[148]["legacy_action"]["kind"] == "replace-incomplete-row"
    assert cases[148]["context_overlap"]["source_lines"] == 2
    assert cases[148]["context_overlap"]["existing_locus"].endswith("_0148.2")
    document = json.loads(gzip.decompress((ROOT / recovery.LIBRARY).read_bytes()))
    sections = {s["id"]: s for s in document["sections"]}
    for case in cases.values():
        window = case["source_library_window"]
        section = sections[window["section"]]
        text = "\n".join(b["text"] for b in section["blocks"])
        assert text[window["start"]:window["end"]] == window["original_text"]
        assert recovery.row_sha(section) == window["section_sha256"]
        for held in window["held_spans"]:
            other = sections[held["section"]]
            original = "\n".join(b["text"] for b in other["blocks"])
            assert original[held["start"]:held["end"]] == held["original_text"]
            assert recovery.row_sha(other) == held["section_sha256"]
            assert held["reason"]
            if held["section"] == window["section"]:
                assert min(held["end"], window["end"]) <= max(held["start"], window["start"])
    assert {h["original_text"] for h in cases[90]["source_library_window"]["held_spans"]} == {"ϰινδυνεύσαντες. ", "φερομένης"}
    assert cases[100]["source_library_window"]["held_spans"][0]["section"].endswith("s376")
    assert cases[148]["source_library_window"]["original_text"].startswith("αὐταῖς τοίνυν,")
    assert cases[154]["source_library_window"]["held_spans"][0]["original_text"] == "προὔκειτο "


def test_remaining_uses_immutable_legacy_rows_after_later_layers(tmp_path):
    inputs(tmp_path)
    corpus = tmp_path / "data/corpus/photius.bibliotheca.jsonl"
    corpus.parent.mkdir(parents=True)
    corpus.write_text('A later corpus projection is not a historical source.\n')
    assert recovery.build_remaining(tmp_path) == recovery.build_remaining()


@pytest.mark.parametrize("change", ["legacy", "overlap", "nan", "window", "held-text", "held-vote"])
def test_remaining_source_or_boundary_drift_rejects(tmp_path, monkeypatch, change):
    inputs(tmp_path)
    if change == "legacy":
        path = tmp_path / "data/corpus_changes/photius-bekker-index/before.jsonl.gz"
        rows = list(map(json.loads, gzip.decompress(path.read_bytes()).splitlines()))
        next(r for r in rows if r["locus"].endswith("_0189.2"))["text"] += " ἄλλο"
        path.write_bytes(gzip.compress(b"".join((json.dumps(r, ensure_ascii=False) + "\n").encode() for r in rows), mtime=0))
    else:
        cases = copy.deepcopy(recovery.REMAINING_CASES)
        if change == "overlap": cases[90]["cuts"][2] = cases[90]["cuts"][1]
        elif change == "nan": cases[90]["x"][1] = float("nan")
        elif change == "window": cases[90]["window"][0] -= 1
        elif change == "held-text":
            entry = list(cases[90]["held"][0]);entry[3] += "ἄλλο";cases[90]["held"][0] = tuple(entry)
        else:
            cases[90]["window"][0] = 1941
            cases[90]["expected_start"] = "ϰινδυνεύσαντες. "
        monkeypatch.setattr(recovery, "REMAINING_CASES", cases)
    with pytest.raises(ValueError):
        recovery.build_remaining(tmp_path)
