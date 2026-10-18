import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import prepare_photius_geometry as geometry
from prepare_photius_retries import build_retry, build_supplement, CHECKPOINT36, CHECKPOINT38


def retained_run(tmp_path, request, checkpoint, *, failed=None):
    meta = {**checkpoint, "manifest_sha256": geometry.sha(geometry.encode(request)), "prompt": request["prompt"]}
    rows = [{"id": job["id"], "source": job["source"], "scan_page": job["scan_page"],
             "region": job["region"], "image_sha256": "a" * 64,
             "prompt_sha256": geometry.sha((request["prompt"] + " " + job["prompt_suffix"]).encode()),
             "raw_prediction": "ὁ λόγος σαφὴς καὶ καλός.",
             "finish_reason": "length" if job["id"] == failed else "stop"} for job in request["pages"]]
    path = tmp_path / (meta["manifest_sha256"] + ".jsonl")
    path.write_bytes(b"\n".join(json.dumps(r, ensure_ascii=False).encode() for r in [{"_meta": meta}, *rows]) + b"\n")
    return path


def source_fixture(tmp_path, monkeypatch, bounds):
    # Structural tests keep the real source pin without shipping its 600 pages.
    import fitz
    original_sha = geometry.sha
    pdf = tmp_path / "source.pdf"; pdf.write_bytes(b"source-pdf-fixture")
    monkeypatch.setattr(geometry, "sha", lambda raw: geometry.SOURCE_SHA if raw == pdf.read_bytes() else original_sha(raw))
    monkeypatch.setattr(fitz, "open", lambda _: object())
    monkeypatch.setattr(geometry, "source_contact", lambda _, page, edges: geometry.encode({"page": page, "edges": edges}))
    monkeypatch.setattr(geometry, "SOURCE_BOUNDS", bounds)
    return pdf


def test_geometry_authority_pins_each_old_leaf_and_exact_source_edges(tmp_path, monkeypatch):
    bounds = {207: [.035, .485, .488, None]}
    pdf = source_fixture(tmp_path, monkeypatch, bounds)
    parent = build_retry(207)
    path = retained_run(tmp_path, parent, CHECKPOINT36)
    authority, images = geometry.build_authority([path], pdf)
    assert len(authority["groups"]) == 1 and len(images) == 1
    group = authority["groups"][0]
    assert group["model"] == CHECKPOINT36["model"]
    assert {t["id"] for t in group["targets"]} == {p["id"] for p in parent["pages"]}
    raw = geometry.encode(authority)
    request_path, request = geometry.request_for_group(authority, raw, group)
    assert request["checkpoints"] == [CHECKPOINT36]
    assert request["review"]["accepted_for_primary_ingest"] is False
    assert request["review"]["source_authority"]["sha256"] == geometry.sha(raw)
    assert len(request["replacement_conditions"]) == 2
    lines = path.read_bytes().splitlines()
    for old, new, line in zip(parent["pages"], request["pages"], lines[1:]):
        assert new["source"] == old["source"] and new["scan_page"] == old["scan_page"]
        assert new["region"][1::2] == old["region"][1::2]
        condition = request["replacement_conditions"][old["id"]]
        assert condition["raw_file_sha256"] == geometry.sha(path.read_bytes())
        assert condition["prediction_record_sha256"] == geometry.sha(line)
        assert condition["source_pdf_sha256"] == geometry.SOURCE_SHA
        assert condition["original_region"] == old["region"] and condition["new_region"] == new["region"]
    monkeypatch.setattr(geometry, "source_authority", lambda: (geometry.AUTHORITY.as_posix(), raw))
    assert geometry.known_gutter_manifests() == {geometry.sha(geometry.encode(request)): (request_path, request)}
    altered = copy.deepcopy(group); altered["targets"][0]["new_region"][1] += .01
    with pytest.raises(ValueError, match="reviewed source edges"):
        geometry.request_for_group(authority, raw, altered)


def test_nested_geometry_uses_current_leaves_and_preserves_failed_ancestor(tmp_path, monkeypatch):
    pdf = source_fixture(tmp_path, monkeypatch, {50: [None, .490, .505, None]})
    base = build_retry(50)
    failed = next(job["id"] for job in base["pages"] if job["id"].endswith("left-lower"))
    base_raw = retained_run(tmp_path, base, CHECKPOINT38, failed=failed)
    child = build_supplement(50, "left-lower")
    child_raw = retained_run(tmp_path, child, CHECKPOINT38)
    authority, _ = geometry.build_authority([base_raw, child_raw], pdf)
    targets = {t["id"] for group in authority["groups"] for t in group["targets"]}
    assert failed not in targets
    assert {p["id"] for p in child["pages"]} <= targets
    assert geometry.encode(geometry.build_authority([child_raw, base_raw], pdf)[0]) == geometry.encode(authority)
    with pytest.raises(ValueError, match="retained raw attempt"):
        geometry.build_authority([base_raw], pdf)
    with pytest.raises(ValueError, match="duplicate old attempts"):
        geometry.build_authority([base_raw, child_raw, child_raw], pdf)


def test_geometry_can_repair_an_exact_failed_leaf_without_relabeling_its_outcome(tmp_path, monkeypatch):
    pdf = source_fixture(tmp_path, monkeypatch, {207: [.035, .485, .488, None]})
    parent = build_retry(207)
    failed = parent["pages"][0]["id"]
    path = retained_run(tmp_path, parent, CHECKPOINT36, failed=failed)
    authority, _ = geometry.build_authority([path], pdf)
    request = geometry.request_for_group(authority, geometry.encode(authority), authority["groups"][0])[1]
    assert request["replacement_conditions"][failed]["finish_reason"] == "length"
    rows = path.read_bytes().splitlines(); path.write_bytes(b"\n".join(rows[:-1]) + b"\n")
    with pytest.raises(ValueError, match="every old retry outcome"):
        geometry.build_authority([path], pdf)


def test_actual_pinned_requests_reproduce_without_invented_or_reordered_targets():
    path, raw = geometry.source_authority()
    if raw is None:
        pytest.skip("Source-reviewed geometry authority has not been prepared")
    authority = json.loads(raw)
    assert path == geometry.AUTHORITY.as_posix()
    catalog = geometry.known_gutter_manifests()
    assert len(catalog) == len(authority["groups"])
    assert sum(len(r["pages"]) for _, r in catalog.values()) == sum(len(g["targets"]) for g in authority["groups"])
    for filename, request in catalog.values():
        assert (geometry.ROOT / filename).read_bytes() == geometry.encode(request)
        assert len(request["checkpoints"]) == 1
        assert len({p["replaces_region"] for p in request["pages"]}) == len(request["pages"])
