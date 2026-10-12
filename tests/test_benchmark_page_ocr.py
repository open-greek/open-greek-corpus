import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("ocr_bench", Path(__file__).parents[1] / "scripts/benchmark_page_ocr.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


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
