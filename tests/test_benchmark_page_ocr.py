import importlib.util
import json
import time
import pytest
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("ocr_bench", Path(__file__).parents[1] / "scripts/benchmark_page_ocr.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


@pytest.mark.parametrize("field,value", [("split", "calibration"), ("volume", "other")])
def test_manifest_rejects_changed_page_identity(field, value):
    page = {"id": "test-page", "split": "test", "volume": "edition"}
    with pytest.raises(ValueError, match="Changed benchmark identity"):
        bench.validate_page_rows({"pages": [page]}, [{**page, field: value}], complete=True)


def test_resume_rejects_pages_outside_selected_split():
    page = {"id": "test-page", "split": "test", "volume": "edition"}
    with pytest.raises(ValueError, match="outside selected benchmark"):
        bench.validate_page_rows({"pages": []}, [page])


def test_manifest_requires_unique_complete_results():
    page = {"id": "test-page", "split": "test", "volume": "edition"}
    with pytest.raises(ValueError, match="entire pinned benchmark"):
        bench.validate_page_rows({"pages": [page]}, [], complete=True)
    with pytest.raises(ValueError, match="Repeated page identity"):
        bench.validate_page_rows({"pages": [page]}, [page, page])


def test_scores_repetitions_without_trimming():
    result = bench.score("λόγος", "λόγος λόγος λόγος")
    assert result["cer"] > 1
    assert result["length_ratio"] > 2
    assert result["wer"] == 2


def test_diacritics_are_primary_errors_and_folded_separately():
    result = bench.score("λόγος", "λογος")
    assert result["char_errors"] == 1
    assert result["folded_char_errors"] == 0
    assert bench.score("λόγος", "λόγος")["char_errors"] == 0


def test_page_xml_uses_only_line_transcription(tmp_path):
    xml = tmp_path / "PG_1-2.xml"
    xml.write_text('''<PcGts xmlns="urn:test"><Page imageFilename="PG_1-2.jpg"><TextRegion><TextLine>
    <Word><TextEquiv><Unicode>nested duplicate</Unicode></TextEquiv></Word>
    <TextEquiv index="1"><Unicode>wrong alternative</Unicode></TextEquiv>
    <TextEquiv index="0"><Unicode>λόγος</Unicode></TextEquiv>
    </TextLine></TextRegion></Page></PcGts>''')
    assert bench.page_gold(xml) == ("PG_1-2.jpg", "λόγος")
    xml.with_suffix(".jpg").write_bytes(b"fixture")
    a = bench.prepare(tmp_path, tmp_path / "manifest.json")
    b = bench.prepare(tmp_path, tmp_path / "manifest.json")
    assert a == b
    assert len(a["pages"]) == 1
    assert a["pages"][0]["volume"] == "pg-1"


def test_edition_groups_recognize_both_ground_truth_conventions():
    assert bench.edition_group("grc_tlg_mpg145-302") == "pg-145"
    assert bench.edition_group("grc_grna_or_407") == "gregory-nazianzus-orations"


def test_empty_pages_are_included_in_aggregate():
    rows = [{"split": "test", "metrics": bench.score("λόγος", "")},
            {"split": "test", "metrics": bench.score("λόγος", "λόγος")}]
    result = bench.summarize(rows)["test"]
    assert result["pages"] == 2
    assert result["cer"] == 0.5
    assert result["empty_pages"] == 1


def test_http_request_keeps_image_and_disables_thinking(tmp_path, monkeypatch):
    image = tmp_path / "page.png"
    image.write_bytes(b"page image")
    captured = {}
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self):
            return json.dumps({"choices": [{"message": {"content": "λόγος"},
                                            "finish_reason": "stop"}],
                               "usage": {"completion_tokens": 3}}).encode()
    def open_request(request, **kwargs):
        captured.update(json.loads(request.data))
        return Response()
    monkeypatch.setattr(bench, "urlopen", open_request)
    result = bench.http_completion(SimpleNamespace(model="pinned", max_tokens=12000,
                                                  base_url="http://localhost/v1"), image)
    assert captured["chat_template_kwargs"] == {"enable_thinking": False}
    assert captured["messages"][0]["content"][0]["image_url"]["url"] == "data:image/png;base64,cGFnZSBpbWFnZQ=="
    assert captured["messages"][0]["content"][1]["text"] == bench.PROMPT
    assert result == {"raw_prediction": "λόγος", "finish_reason": "stop", "generation_tokens": 3}


def test_failed_http_pages_remain_in_scores(tmp_path, monkeypatch):
    image, xml = tmp_path / "page.png", tmp_path / "page.xml"
    image.write_bytes(b"image")
    xml.write_bytes(b"xml")
    monkeypatch.setattr(bench, "page_gold", lambda path: ("page.png", "λόγος"))
    def fail(*args):
        raise TimeoutError("server timeout")
    monkeypatch.setattr(bench, "http_completion", fail)
    row = bench.http_page(SimpleNamespace(root=tmp_path), {
        "id": "page", "split": "test", "volume": "test", "image": image.name,
        "xml": xml.name, "image_sha256": bench.sha256(image), "xml_sha256": bench.sha256(xml)})
    summary = bench.summarize([row])["test"]
    assert summary["cer"] == 1
    assert summary["failed_pages"] == 1
    assert "TimeoutError" in row["error"]


def test_paired_diagnostics_exclude_calibration_and_preserve_editions():
    left = [{"id": "cal", "split": "calibration", "volume": "a", "metrics": bench.score("abcde", "wrong")},
            {"id": "test-a", "split": "test", "volume": "a", "metrics": bench.score("abcde", "abcxy")},
            {"id": "test-b", "split": "test", "volume": "b", "metrics": bench.score("abcde", "abcxy")}]
    right = [{**r, "metrics": bench.score("abcde", "abcde")} for r in left]
    result = bench.paired_diagnostics(left, right, "test")
    assert {r["id"] for r in result["page_changes"]} == {"test-a", "test-b"}
    assert result["paired_page_bootstrap"]["cer_change_ci95"] == [-0.4, -0.4]
    assert set(result["by_volume"]) == {"a", "b"}


def test_concurrent_http_run_keeps_page_identity(tmp_path, monkeypatch):
    pages = []
    for index, gold in enumerate(("λόγος", "θεός")):
        stem = f"page-{index}"
        image, xml = tmp_path / f"{stem}.png", tmp_path / f"{stem}.xml"
        image.write_bytes(bytes([index]))
        xml.write_text(f'<PcGts xmlns="urn:test"><Page imageFilename="{image.name}">'
                       f'<TextRegion><TextLine><TextEquiv><Unicode>{gold}</Unicode>'
                       '</TextEquiv></TextLine></TextRegion></Page></PcGts>')
        pages.append({"id": stem, "split": "calibration" if index == 0 else "test",
                      "volume": "edition", "image": image.name, "xml": xml.name,
                      "image_sha256": bench.sha256(image), "xml_sha256": bench.sha256(xml)})
    manifest, runtime, output = (tmp_path / name for name in ("pages.json", "runtime.json", "output.jsonl"))
    manifest.write_text(json.dumps({"pages": pages}))
    runtime.write_text(json.dumps({"model": "pinned", "revision": "abc"}))
    class ModelsResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self):
            return b'{"data":[{"id":"pinned"}]}'
    monkeypatch.setattr(bench, "urlopen", lambda *args, **kwargs: ModelsResponse())
    def completion(args, image):
        first = image.name == "page-0.png"
        if first:
            time.sleep(0.02)
        return {"raw_prediction": "λόγος" if first else "θεός", "finish_reason": "stop"}
    monkeypatch.setattr(bench, "http_completion", completion)
    bench.run(SimpleNamespace(root=tmp_path, manifest=manifest, out=output,
        runtime_manifest=runtime, backend="http", base_url="http://localhost/v1",
        model="pinned", revision="abc", workers=2, split="all", limit=None, max_tokens=12000))
    rows = [json.loads(line) for line in output.read_text().splitlines()][1:]
    assert [r["id"] for r in rows] == ["page-1", "page-0"]
    assert all(r["metrics"]["cer"] == 0 for r in rows)
    summary = json.loads(output.with_suffix(".summary.json").read_text())["metrics"]
    assert summary["test"]["pages"] == summary["calibration"]["pages"] == 1
