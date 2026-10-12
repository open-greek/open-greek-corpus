import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("epidoc", Path(__file__).parents[1] / "scripts/prepare_epidoc_pilot.py")
epidoc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(epidoc)


def source(tmp_path, body):
    path = tmp_path / "source.xml"
    path.write_text('''<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc>
    <titleStmt><title>Test</title></titleStmt><publicationStmt><availability>
    <ref type="license" target="https://creativecommons.org/licenses/by/3.0/"/>
    </availability></publicationStmt></fileDesc></teiHeader>
    <text><body><div type="edition"><div type="textpart" subtype="column" n="3"><ab>'''
    + body + '</ab></div></div></body></text></TEI>')
    return path


def test_keeps_all_readings_and_damage_without_concatenating_variants(tmp_path):
    src = source(tmp_path, '<lb n="1"/><choice><corr>ε</corr><sic>ο</sic></choice>ἶναι '
        '<supplied reason="lost">κα</supplied><unclear>ὶ</unclear><gap reason="lost" quantity="3" unit="character"/>'
        '<lb n="2" break="no"/><app><lem>α</lem><rdg>β</rdg></app>')
    original = src.read_bytes()
    out = tmp_path / "out"
    result = epidoc.prepare(src, out, source_url="https://example.org/source", revision="abc")
    assert result["lines"] == 2
    rows = [json.loads(line) for line in (out / 'passages.jsonl').read_text().splitlines()]
    assert rows[0]["text"].startswith("εἶναι [κα]")
    assert "ο" not in rows[0]["text"]
    assert rows[1]["text"] == "α"
    assert rows[1]["line_attributes"]["break"] == "no"
    assert any(s["text"] == "β" and not s["selected"] for s in rows[1]["spans"])
    assert (out / 'source.xml').read_bytes() == original
    assert src.read_bytes() == original


def test_context_spanning_line_boundary_is_preserved(tmp_path):
    src = source(tmp_path, '<lb n="1"/><unclear>α<lb n="2" break="no"/>β</unclear>')
    out = tmp_path / "out"
    epidoc.prepare(src, out, source_url="https://example.org/source", revision="abc")
    rows = [json.loads(line) for line in (out / 'passages.jsonl').read_text().splitlines()]
    assert rows[0]["text"] == "α\u0323"
    assert rows[1]["text"] == "β\u0323"


def test_ambiguous_apparatus_is_not_arbitrarily_resolved(tmp_path):
    src = source(tmp_path, '<lb n="1"/><app><rdg>α</rdg><rdg>β</rdg></app>')
    with pytest.raises(ValueError, match="Unresolved variant"):
        epidoc.prepare(src, tmp_path / "out", source_url="https://example.org/source", revision="abc")
