import copy
import json
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from critical_text import (annotate, finalize_tokens, lexical_text, render_html, validate,
                           load_critical_editions, register_critical_editions, index_metadata)
import ingest_dclp63141 as ingest
import prepare_epidoc_pilot as pilot


def annotated(tmp_path, body):
    source = tmp_path / "source.xml"
    source.write_text('<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader><fileDesc>'
        '<titleStmt><title>Test</title></titleStmt><publicationStmt><availability>'
        '<ref type="license" target="https://creativecommons.org/licenses/by/3.0/"/>'
        '</availability></publicationStmt></fileDesc></teiHeader><text><body>'
        '<div type="edition"><div type="textpart" subtype="column" corresp="#FR1" n="3"><ab>'
        + body + '</ab></div></div></body></text></TEI>')
    out = tmp_path / "out"
    pilot.prepare(source, out, source_url="https://example.org", revision="1")
    rows = [annotate(json.loads(line)) for line in (out / "passages.jsonl").read_text().splitlines()]
    finalize_tokens(rows)
    return rows


def test_tokens_keep_status_offsets_and_exclude_damage_from_lexicon(tmp_path):
    rows = annotated(tmp_path, '<lb n="1"/>λόγος <unclear>θε</unclear>ός '
        '<supplied reason="lost">κα</supplied>λός <supplied reason="undefined" evidence="apograph">ναί</supplied> '
        'φ<gap reason="lost" quantity="2" unit="character"/>ς '
        '<choice><corr>ε</corr><sic>ο</sic></choice>ἶναι '
        '<app><lem>α</lem><rdg>β</rdg></app>')
    row = rows[0]
    assert row["analysis_text"] == "λόγος"
    assert lexical_text(row | {"critical_markup": {"schema": "epidoc-spans-v1"}}) == "λόγος"
    assert [(t["form"], t["status"]) for t in row["tokens"]] == [
        ("λόγος", ["extant"]), ("θεός", ["unclear"]), ("καλός", ["supplied"]),
        ("ναί", ["apograph"]), ("φ", ["fragment"]), ("ς", ["fragment"]),
        ("εἶναι", ["corrected"]), ("α", ["variant"])]
    assert "ο" not in [t["form"] for t in row["tokens"]]
    assert row["textparts"][0]["attributes"]["corresp"] == "#FR1"
    assert "⸢ναί⸣" in row["text"]
    corrupted = copy.deepcopy(row)
    corrupted["tokens"][0]["start"] += 1
    with pytest.raises(ValueError, match="offsets"):
        validate(corrupted)
    corrupted = copy.deepcopy(row)
    rejected = next(s["id"] for s in row["spans"] if not s["selected"])
    corrupted["tokens"][0]["span_ids"] = [rejected]
    with pytest.raises(ValueError, match="unselected"):
        validate(corrupted)
    corrupted = copy.deepcopy(row)
    corrupted["tokens"][1]["status"] = ["extant"]
    corrupted["tokens"][1]["lexical_eligible"] = True
    with pytest.raises(ValueError, match="source markup"):
        validate(corrupted)
    corrupted = copy.deepcopy(row)
    corrupted["locus"] = "3.99"
    with pytest.raises(ValueError, match="physical"):
        validate(corrupted)


def test_word_continuations_do_not_mint_two_complete_forms(tmp_path):
    rows = annotated(tmp_path, '<lb n="1"/>καὶ λό<lb n="2" break="no"/>γος τις')
    assert [r["analysis_text"] for r in rows] == ["καὶ", "τις"]
    assert rows[0]["tokens"][-1]["status"] == ["line_fragment"]
    assert rows[1]["tokens"][0]["status"] == ["line_fragment"]


def test_notes_deletions_and_milestones_never_become_ordinary_words(tmp_path):
    rows = annotated(tmp_path, '<lb n="1"/>α <note>β</note><del>γ</del><milestone rend="paragraphos"/> δ')
    assert rows[0]["analysis_text"] == "α δ"
    assert any(s["kind"] == "milestone" for s in rows[0]["spans"])
    assert any(s["text"] == "γ" and not s["selected"] for s in rows[0]["spans"])


def test_pinned_pilot_is_lossless_reproducible_and_all_markup_is_served(tmp_path):
    rows, manifest, artifacts = ingest.generate()
    assert len(rows) == 89
    all_nodes = {a["id"]: a for r in rows for s in r["spans"] for a in s["ancestors"]}
    for name in ("unclear", "gap", "supplied", "app", "corr", "sic", "lem", "rdg", "milestone"):
        assert sum(a["tag"] == name for a in all_nodes.values()) == manifest["markup_counts"][name]
    assert manifest["markup_counts"]["unclear"] == 219
    assert manifest["markup_counts"]["gap"] == 140
    assert manifest["markup_counts"]["supplied"] == 86
    assert rows[0]["physical_refs"]["custody_events"]
    assert all(validate(row) for row in rows)
    assert all(t["lemma"] is None and t["analysis"] is None for r in rows for t in r["tokens"])
    assert ingest.generate()[2] == artifacts
    ingest.apply(artifacts, tmp_path)
    assert (tmp_path / f"data/corpus/{ingest.SLUG}.jsonl").read_bytes() == artifacts[f"data/corpus/{ingest.SLUG}.jsonl"]
    ingest.undo(artifacts, tmp_path)
    assert not (tmp_path / f"data/corpus/{ingest.SLUG}.jsonl").exists()
    assert (tmp_path / "data/corpus_changes/dclp63141/changes.json").exists()


def test_html_exports_selected_and_rejected_readings_and_escaped_attributes():
    rows, manifest, artifacts = ingest.generate()
    page = artifacts["data/critical_editions/dclp63141/reader.html"].decode()
    assert "Alternative readings" in page
    assert "sic:" in page and "rdg:" in page
    assert "supplied" in page and "unclear" in page and "apograph" in page
    assert "CC BY 3.0" in page and "custody_events" in page
    assert "continues preceding word" in page
    assert "⸢" in page and "⸣" in page
    assert ingest.SOURCE_URL in page


def test_rejects_unknown_source_and_unaudited_edits(tmp_path):
    source = tmp_path / "source.xml"
    source.write_text("<TEI/>")
    with pytest.raises(ValueError, match="reviewed revision"):
        ingest.generate(source)
    rows, manifest, artifacts = ingest.generate()
    ingest.apply(artifacts, tmp_path)
    target = tmp_path / f"data/corpus/{ingest.SLUG}.jsonl"
    target.write_text("independent edit")
    with pytest.raises(ValueError, match="independently"):
        ingest.apply(artifacts, tmp_path)
    with pytest.raises(ValueError, match="changed since"):
        ingest.undo(artifacts, tmp_path)


def test_critical_projection_cannot_silently_fall_back_to_marked_display():
    assert lexical_text({"text": "λόγος"}) == "λόγος"
    assert lexical_text({"text": "⟦λόγος ∥ λογός⟧", "analysis_text": "", "ocr_consensus": {}}) == ""
    assert lexical_text({"text": "uncertain", "analysis_text": "certain"}) == "certain"
    with pytest.raises(ValueError, match="string"):
        lexical_text({"text": "uncertain", "analysis_text": None})
    with pytest.raises(ValueError, match="projection"):
        lexical_text({"critical_markup": {"schema": "epidoc-spans-v1"}, "text": "δ[έ]"})


def test_registry_and_reader_metadata_preserve_physical_identity(tmp_path):
    sys.path.insert(0, str(SCRIPTS.parent))
    from source_identity import Registry
    rows, manifest, artifacts = ingest.generate()
    ingest.apply(artifacts, tmp_path)
    source = tmp_path / manifest["source_path"]
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes((ingest.PILOT / "source.xml").read_bytes())
    manifests = load_critical_editions(tmp_path / "data")
    reg = Registry()
    register_critical_editions(reg, manifests)
    work = reg.works[ingest.SLUG]
    edition = work.editions[work.default_edition]
    assert work.author == "anonymous"
    assert work.aliases == {"cts": f"urn:cts:cogGreek:{ingest.SLUG}"}
    assert edition.scheme == "column.line"
    assert not edition.scheme_inferred
    assert edition.provider == "dclp"
    assert edition.license == "CC-BY-3.0"
    assert edition.aliases["trismegistos"] == "63141"
    assert reg.locus_for_citation(ingest.SLUG, "4.43", validate=True).ref == "4.43"
    assert index_metadata(manifests[ingest.SLUG])["reader_path"].endswith("reader.html")
    register_critical_editions(reg, manifests)
    assert len(reg.works) == 1
    source.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checksum"):
        load_critical_editions(tmp_path / "data")


def test_numeric_columns_are_not_reported_as_logical_loci(tmp_path, monkeypatch):
    import infer_served_schemes as inference
    rows, manifest, artifacts = ingest.generate()
    ingest.apply(artifacts, tmp_path)
    source = tmp_path / manifest["source_path"]
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes((ingest.PILOT / "source.xml").read_bytes())
    (tmp_path / "data/corpus_editions.json").write_text(json.dumps({ingest.SLUG: {"edition": ingest.EDITION}}))
    monkeypatch.setattr(inference, "DATA", tmp_path / "data")
    monkeypatch.setattr(inference, "CORPUS", tmp_path / "data/corpus")
    monkeypatch.setattr(inference, "REPO", tmp_path)
    monkeypatch.setattr(inference, "OUT", tmp_path / "data/served_scheme_inference.json")
    inference.main()
    work = json.loads(inference.OUT.read_text())["works"][ingest.SLUG]
    assert work["class"] == "physical"
    assert work["scheme"] == "column.line"
