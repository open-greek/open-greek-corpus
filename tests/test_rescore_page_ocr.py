import importlib.util
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
spec = importlib.util.spec_from_file_location("rescore", Path(__file__).parents[1] / "scripts/rescore_page_ocr.py")
rescore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rescore)


def line(identity, text, points):
    return (f'<TextLine id="{identity}"><Coords points="{points}"/>'
            f'<TextEquiv><Unicode>{text}</Unicode></TextEquiv></TextLine>')


def test_sorts_across_regions_and_within_a_region_without_changing_text(tmp_path):
    path = tmp_path / "page.xml"
    path.write_text('<PcGts xmlns="urn:test"><Page><TextRegion>'
                    + line("last", "τρία", "0,30 30,30 30,40 0,40")
                    + line("middle", "δύο", "0,20 30,20 30,29 0,29")
                    + '</TextRegion><TextRegion>'
                    + line("first", "ἕν", "0,0 30,0 30,10 0,10")
                    + '</TextRegion></Page></PcGts>')
    text, original, ordered = rescore.ordered_gold(path)
    assert text == "ἕν\nδύο\nτρία"
    assert [row["id"] for row in original] == ["last", "middle", "first"]
    assert [row["id"] for row in ordered] == ["first", "middle", "last"]


def test_refuses_side_by_side_columns(tmp_path):
    path = tmp_path / "page.xml"
    path.write_text('<PcGts xmlns="urn:test"><Page><TextRegion>'
                    + line("left", "ἕν", "0,0 30,0 30,10 0,10")
                    + line("right", "δύο", "40,0 70,0 70,10 40,10")
                    + '</TextRegion></Page></PcGts>')
    with pytest.raises(ValueError, match="Side-by-side"):
        rescore.ordered_gold(path)


def test_refuses_missing_geometry(tmp_path):
    path = tmp_path / "page.xml"
    path.write_text('<PcGts xmlns="urn:test"><Page><TextRegion><TextLine>'
                    '<TextEquiv><Unicode>ἕν</Unicode></TextEquiv>'
                    '</TextLine></TextRegion></Page></PcGts>')
    with pytest.raises(ValueError, match="Missing line coordinates"):
        rescore.ordered_gold(path)


def test_rescoring_is_audited_repeatable_and_keeps_raw_prediction(tmp_path):
    xml, image = tmp_path / "page.xml", tmp_path / "page.jpg"
    xml.write_text('<PcGts xmlns="urn:test"><Page><TextRegion>'
                   + line("last", "δύο", "0,20 30,20 30,30 0,30")
                   + line("first", "ἕν", "0,0 30,0 30,10 0,10")
                   + '</TextRegion></Page></PcGts>')
    image.write_bytes(b"test image")
    original = rescore.page_gold(xml)[1]
    manifest, source, audit, output = (tmp_path / name for name in
                                     ("manifest.json", "raw.jsonl", "audit.json", "scored.jsonl"))
    manifest.write_text(json.dumps({"pages": [{"id": "page", "split": "test", "volume": "edition",
        "xml": xml.name, "image": image.name, "xml_sha256": rescore.sha256(xml),
        "image_sha256": rescore.sha256(image),
        "gold_sha256": hashlib.sha256(original.encode()).hexdigest()}]}))
    prediction = "ἕν\nδύο"
    source.write_text(json.dumps({"_meta": {"manifest_sha256": rescore.sha256(manifest)}}) + "\n"
        + json.dumps({"id": "page", "split": "test", "volume": "edition",
                      "raw_prediction": prediction, "metrics": rescore.score(original, prediction)}) + "\n")
    source_bytes = source.read_bytes()
    rescore.rescore(tmp_path, manifest, audit, source, output)
    first_audit, first_output = audit.read_bytes(), output.read_bytes()
    rescore.rescore(tmp_path, manifest, audit, source, output)
    assert audit.read_bytes() == first_audit
    assert output.read_bytes() == first_output
    assert source.read_bytes() == source_bytes
    repaired = json.loads(output.read_text().splitlines()[1])
    assert repaired["raw_prediction"] == prediction
    assert repaired["metrics"]["cer"] == 0
    correction = json.loads(audit.read_text())["corrections"][0]
    assert correction["original_text"] == original
    assert correction["corrected_text"] == prediction
