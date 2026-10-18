"""Reviewed horizontal crop changes retain all model attempts and parent links."""
import copy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ingest_photius_coverage as ingest
import photius_retries as retries
from prepare_photius_retries import build_retry, build_supplement, CHECKPOINT38
from test_ingest_photius_coverage import (multiple_retry_fixture, nested_supplement_fixture)


def encoded_rows(meta, rows):
    return b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in [{"_meta": meta}, *rows]) + b"\n"


def geometry_fixture(tmp_path, monkeypatch, nested=False, mutate=None, old_failure=False):
    monkeypatch.setattr(retries, "known_gutter_manifests", lambda: {})
    if nested:
        paths, bases, reviews, first, second = nested_supplement_fixture(tmp_path, monkeypatch)
        supplements = [first, second]
        parent = build_supplement(50, "left-lower-part02")
        old_file = second
        parent_path = next(path for path, request in retries.known_supplement_manifests().values()
                           if request == parent)
    else:
        paths, bases, reviews = multiple_retry_fixture(tmp_path)
        supplements = []
        parent = build_retry(50)
        old_file = next(p for p in bases if p.name == "retry-50-0.jsonl")
        parent_path = retries.known_retry_manifests()[retries.sha(retries.encode(parent))][0]
    if old_failure:
        values = [json.loads(line) for line in old_file.read_bytes().splitlines()]
        values[1].update(finish_reason="length", raw_prediction="καὶ " * 20, error="retained exact error")
        old_file.write_bytes(encoded_rows(values[0]["_meta"], values[1:]))
    lines = old_file.read_bytes().splitlines()
    old_meta = json.loads(lines[0])["_meta"]
    old_rows = {json.loads(line)["id"]: (json.loads(line), line) for line in lines[1:]}
    targets = parent["pages"][:2] if nested else [parent["pages"][0], parent["pages"][2]]
    authority_raw = retries.encode({"kind": "synthetic-reviewed-column-boundaries",
                                  "source": parent["sources"], "targets": [p["id"] for p in targets]})
    authority_path = "data/ocr_requests/photius-gutter-source-review.json"
    request = {"supplements": {"manifest_path": parent_path, "manifest_sha256": retries.sha(retries.encode(parent)),
                    "page_id": "photius-bekker-0050", "replaces_regions": [p["id"] for p in targets]},
               "sources": parent["sources"], "prompt": parent["prompt"], "checkpoints": [CHECKPOINT38],
               "review": {"source_authority": {"path": authority_path, "sha256": retries.sha(authority_raw)}},
               "replacement_conditions": {}, "pages": []}
    for i, old in enumerate(targets):
        box = old["region"].copy()
        # One inward edge shift and one outward shift: neither implies a partition.
        box[0] += .001 if i == 0 else -.001
        page = {**old, "id": old["id"] + "-gutter", "region": box,
                "replaces_region": old["id"], "max_side": 3600, "reading_order": i}
        row, line = old_rows[old["id"]]
        request["pages"].append(page)
        request["replacement_conditions"][old["id"]] = {
            "kind": "source-confirmed-column-boundary-error",
            "old_manifest_sha256": retries.sha(retries.encode(parent)),
            "source_pdf_sha256": parent["sources"][old["source"]]["sha256"],
            "source_review_sha256": retries.sha(authority_raw),
            "original_region": old["region"], "new_region": box,
            "raw_file_sha256": retries.sha(old_file.read_bytes()),
            "prediction_record_sha256": retries.sha(line),
            "raw_prediction_sha256": retries.sha(row["raw_prediction"].encode()),
            "finish_reason": row["finish_reason"]}
    if mutate:
        mutate(request)
    catalog = {retries.sha(retries.encode(request)): ("data/ocr_requests/test-gutter.json", request)}
    monkeypatch.setattr(retries, "known_gutter_manifests", lambda: catalog)
    monkeypatch.setattr(retries, "source_authority", lambda: (authority_path, authority_raw))
    metadata = {**old_meta, "manifest_sha256": retries.sha(retries.encode(request)), "prompt": request["prompt"]}
    rows = [{"id": job["id"], "source": job["source"], "scan_page": job["scan_page"],
             "region": job["region"], "image_sha256": "c" * 64,
             "prompt_sha256": retries.sha((request["prompt"] + " " + job["prompt_suffix"]).encode()),
             "raw_prediction": "ὁ σαφὴς λόγος ἀκριβῶς ἀνεγνώσθη.", "finish_reason": "stop"}
            for job in request["pages"]]
    new_file = tmp_path / "gutter.jsonl"
    new_file.write_bytes(encoded_rows(metadata, rows))
    supplements.append(new_file)
    review = next(p for p in reviews if p.name == "review-50.json")
    review.unlink()
    _, models, _ = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                              allow_unreviewed_retry_preparation=True)
    base = build_retry(50)
    all_requests = [r for _, r in retries.known_supplement_manifests().values()]
    retries.write_source_review(models, [p for p in bases if p.name == "retry-50-0.jsonl"], review,
        "Synthetic completed scan review of crop boundaries", {p["id"]: "Complete source lines" for p in base["pages"]},
        "2026-10-18T12:00:00Z", base, supplements,
        {p["id"]: "Complete source lines after horizontal crop review" for r in all_requests for p in r["pages"]})
    return paths, bases, reviews, supplements, request, old_rows


@pytest.mark.parametrize("nested", [False, True])
def test_reviewed_geometry_keeps_current_siblings_and_every_ancestor(tmp_path, monkeypatch, nested):
    paths, bases, reviews, supplements, request, old_rows = geometry_fixture(tmp_path, monkeypatch, nested)
    _, models, evidence = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
        bases, reviews, supplement_paths=list(reversed(supplements)))
    assembly = models[(CHECKPOINT38["model"], CHECKPOINT38["revision"])]["photius-bekker-0050"][2]["reviewed_retry"]
    held = {p["id"]: p for p in assembly["held_retry_strips"]}
    assert all(held[target] == old_rows[target][0] for target in request["supplements"]["replaces_regions"])
    assert {p["id"] for p in assembly["strips"]} >= {p["id"] for p in request["pages"]}
    assert not {p["id"] for p in assembly["strips"]} & set(request["supplements"]["replaces_regions"])
    assert len(assembly["strips"]) == (7 if nested else 4)
    assert len(assembly["held_retry_strips"]) == (4 if nested else 2)
    assert assembly["original_record"]["finish_reason"] == "length"
    retained = next(e for e in evidence if e["manifest"]["retry_of"]["page_id"] == "photius-bekker-0050")
    assert len(retained["supplements"]) == (3 if nested else 1)
    assert next(s for s in retained["supplements"] if "source_authority" in s)["source_authority"]["raw"]
    other = next(row for (model, _), rows in models.items() if model != CHECKPOINT38["model"]
                 for identifier, (_, _, row) in rows.items() if identifier == "photius-bekker-0050")
    assert "reviewed_retry" not in other


@pytest.mark.parametrize("field,value,message", [
    ("raw_file_sha256", "0" * 64, "exact retained attempt"),
    ("prediction_record_sha256", "0" * 64, "exact retained attempt"),
    ("raw_prediction_sha256", "0" * 64, "exact retained attempt"),
    ("finish_reason", "length", "exact retained attempt"),
    ("old_manifest_sha256", "0" * 64, "source-reviewed bounds"),
    ("source_pdf_sha256", "0" * 64, "source-reviewed bounds"),
    ("source_review_sha256", "0" * 64, "source-reviewed bounds"),
])
def test_geometry_requires_exact_old_attempt_and_source(tmp_path, monkeypatch, field, value, message):
    def change(request):
        next(iter(request["replacement_conditions"].values()))[field] = value
    with pytest.raises(ValueError, match=message):
        geometry_fixture(tmp_path, monkeypatch, mutate=change)


@pytest.mark.parametrize("change,message", [
    (lambda r: r["pages"][0]["region"].__setitem__(1, .001), "source-reviewed bounds"),
    (lambda r: r["pages"][0].__setitem__("max_side", 2200), "source-reviewed bounds"),
    (lambda r: r["pages"][0].__setitem__("source", "unknown"), "source-reviewed bounds"),
    (lambda r: r["pages"][0].__setitem__("scan_page", 51), "source-reviewed bounds"),
    (lambda r: r["supplements"].__setitem__("manifest_path", "wrong.json"), "exact parent authority"),
    (lambda r: r["review"]["source_authority"].__setitem__("sha256", "0" * 64), "exact source authority"),
    (lambda r: r["checkpoints"].append({"model": "second", "revision": "second"}), "one checkpoint"),
])
def test_geometry_cannot_change_unreviewed_lines_source_parent_or_checkpoint(tmp_path, monkeypatch, change, message):
    with pytest.raises(ValueError, match=message):
        geometry_fixture(tmp_path, monkeypatch, mutate=change)


def test_known_crop_repairs_cannot_be_omitted(tmp_path, monkeypatch):
    paths, bases, reviews, supplements, request, _ = geometry_fixture(tmp_path, monkeypatch)
    path = next(p for p in reviews if p.name == "review-50.json")
    review = json.loads(path.read_bytes())
    review.pop("reviewed_supplements")
    for part in review["strip_reviews"]:
        part.pop("completed_by_supplements", None)
        part.pop("reading_basis", None)
    path.write_bytes(retries.encode(review))
    with pytest.raises(ValueError, match="requires its reviewed geometry repair"):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()], bases, reviews)


def test_archived_geometry_authority_replays_and_remains_reversible(tmp_path, monkeypatch):
    paths, bases, reviews, supplements, _, _ = geometry_fixture(tmp_path, monkeypatch, nested=True)
    document = {"id": "test-source", "license": {"text": "CC BY-SA4.0"}, "sourceRights": "Retained rights"}
    monkeypatch.setattr(ingest, "load_source_library", lambda p: (b"source", document, {}))
    artifacts, report = ingest.generate(paths, tmp_path / "source", tmp_path, retry_paths=bases,
                                        retry_review=reviews, supplement_paths=supplements)
    retry = next(r for r in report["reviewed_retries"] if r["scan_page"] == 50)
    geometry = next(s for s in retry["supplements"] if "source_authority" in s)
    authority = geometry["source_authority"]
    assert artifacts[Path(authority["path"])] == retries.source_authority()[1]
    assert report["covered_authorial_scan_pages"] == 545
    assert len(json.loads(gzip.decompress(artifacts[Path(report["full_networks"]["path"])]))) == 310
    before = (tmp_path / ingest.CORPUS).read_bytes()
    ingest.apply(artifacts, report, tmp_path)
    ingest.prepare_report_inputs(tmp_path, report, [ingest.scan_manifest(), ingest.build_later_gap()])
    missing = copy.deepcopy(report)
    target = next(s for r in missing["reviewed_retries"] for s in r["supplements"] if "source_authority" in s)
    target.pop("source_authority")
    with pytest.raises(ValueError, match="exact source authority"):
        ingest.prepare_report_inputs(tmp_path, missing, [ingest.scan_manifest(), ingest.build_later_gap()])
    archived = tmp_path / authority["path"]
    archived.write_bytes(archived.read_bytes() + b" ")
    with pytest.raises(ValueError, match="report pin"):
        ingest.prepare_report_inputs(tmp_path, report, [ingest.scan_manifest(), ingest.build_later_gap()])
    archived.write_bytes(artifacts[Path(authority["path"])])
    ingest.undo(tmp_path)
    assert (tmp_path / ingest.CORPUS).read_bytes() == before


def test_exact_failed_old_geometry_can_receive_a_successful_repair(tmp_path, monkeypatch):
    paths, bases, reviews, supplements, request, _ = geometry_fixture(tmp_path, monkeypatch, old_failure=True)
    _, models, _ = ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                              bases, reviews, supplement_paths=supplements)
    assembly = models[(CHECKPOINT38["model"], CHECKPOINT38["revision"])]["photius-bekker-0050"][2]["reviewed_retry"]
    held = next(r for r in assembly["held_retry_strips"] if r.get("error"))
    assert held["finish_reason"] == "length" and held["error"] == "retained exact error"
    assert all(retries.successful(r) for r in assembly["strips"])


def test_old_selected_child_prevents_replacing_its_ancestor(tmp_path, monkeypatch):
    paths, bases, reviews, supplements, request, _ = geometry_fixture(tmp_path, monkeypatch)
    # Pretend another known source remedy already descends from the first old
    # region. Geometry cannot bypass it by omitting its raw attempt from inputs.
    known = retries.known_supplement_manifests()
    other = copy.deepcopy(request)
    other.pop("replacement_conditions")
    other["supplements"]["replaces_region"] = other["supplements"].pop("replaces_regions")[0]
    other["pages"] = [other["pages"][0]]
    other["pages"][0]["id"] = "already-selected-child"
    known[retries.sha(retries.encode(other))] = ("data/ocr_requests/older-child.json", other)
    monkeypatch.setattr(retries, "known_supplement_manifests", lambda: known)
    with pytest.raises(ValueError, match="stale ancestor or a second remedy"):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                   bases, reviews, supplement_paths=supplements)


def test_every_replaced_leaf_needs_its_parent_completion_marker(tmp_path, monkeypatch):
    paths, bases, reviews, supplements, request, _ = geometry_fixture(tmp_path, monkeypatch)
    path = next(p for p in reviews if p.name == "review-50.json")
    review = json.loads(path.read_bytes())
    target = request["supplements"]["replaces_regions"][1]
    next(r for r in review["strip_reviews"] if r["id"] == target).pop("completed_by_supplements")
    path.write_bytes(retries.encode(review))
    with pytest.raises(ValueError, match="explicit supplemental completion"):
        ingest.prepare_fresh_inputs(paths, [ingest.scan_manifest(), ingest.build_later_gap()],
                                   bases, reviews, supplement_paths=supplements)
