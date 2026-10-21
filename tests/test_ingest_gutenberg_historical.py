"""Historical admission preserves apparatus, uncertainty, and existing data."""
import copy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
import ingest_gutenberg_historical as intake
from critical_text import finalize_tokens, validate


def test_pinned_homily_keeps_native_greek_sections_and_excludes_latin_notes():
    groups = intake.candidates()
    source, rows, notes = next(g for g in groups if g[0]["ebook_id"] == 37641)
    assert [r["locus"] for r in rows] == [str(n) for n in range(1,7)]
    assert rows[0]["text"].startswith("Καὶ τοῦτο οὐ νοήσαντες")
    assert not any("Quemadmodum" in r["text"] or "[2]" in r["text"] for r in rows)
    assert any("Reg." in n["text"] for n in notes)
    assert source["edition_qualification"].startswith("The citable edition is the pinned Gutenberg")


def test_inscription_retains_restorations_and_all_physical_line_boundaries():
    source, rows, notes = next(g for g in intake.candidates() if g[0]["ebook_id"] == 66595)
    assert len(rows) == 436 and len({r["locus"].split('.')[0] for r in rows}) == 19
    assert rows[0]["text"].startswith("Ἐτῶν δεκαε[ν]νέα")
    assert "δεκαεννέα" not in rows[0]["analysis_text"]
    assert all(validate(row) for row in rows)
    assert notes and all(n["text"] for n in notes)
    for previous,following in zip(rows,rows[1:]):
        if previous["text"].endswith('-'):
            assert not previous["tokens"][-1]["lexical_eligible"]
            assert not following["tokens"][0]["lexical_eligible"]


def test_cross_column_continuation_requires_explicit_source_authorization():
    _,rows,_ = next(g for g in intake.candidates() if g[0]["ebook_id"] == 66595)
    with pytest.raises(ValueError, match="column boundary"):
        finalize_tokens(copy.deepcopy(rows))
    assert all(validate(r) for r in rows)


def test_spaced_lacunae_do_not_admit_fragments_or_invent_reader_credits():
    _, rows, _ = next(g for g in intake.candidates() if g[0]["ebook_id"] == 66595)
    by_locus = {r["locus"]: r for r in rows}
    assert by_locus["II.11"]["text"].endswith("ψηφισσ. . .")
    assert "ψηφισσ" not in by_locus["II.11"]["analysis_text"]
    assert "ων" not in by_locus["II.12"]["analysis_text"].split()
    assert any(s["kind"] == "gap" for s in by_locus["II.11"]["spans"])
    manifest = {"title": "Greek inscription", "attribution": "Fairley 1898",
                "source_url": "https://www.gutenberg.org/ebooks/66595",
                "source_license": "Public domain", "source_path": "source.html"}
    page = intake.render_html(rows, manifest)
    assert "Fairley 1898 · Public domain" in page and "Pinned source HTML" in page
    assert "P.Herc." not in page and "DCLP" not in page and "CC BY 3.0" not in page


def test_established_work_identity_does_not_erase_disputed_attribution():
    source,_,_ = next(g for g in intake.candidates() if g[0]["ebook_id"] == 32549)
    assert source["disposition"] == "approved_subject_to_gates"
    assert source["cts"] == "urn:cts:greekLit:tlg2041.tlg004"
    assert source["attribution_status"] == "disputed"
    assert {r["author"] for r in source["attribution_readings"]} == {"Athanasius", "Marcellus of Ancyra"}


def test_verified_prose_identities_have_no_anonymous_registry_duplicates():
    registry = json.loads((intake.ROOT / "data/source_registry.json").read_text())
    for source, _, _ in intake.candidates():
        if not source.get("cts"):
            continue
        work = registry["works"][source["work"]]
        assert work["aliases"]["cts"] == source["cts"]
        assert work["default_edition"] == source["work"] + "." + source["edition"]
        invented_alias = "urn:cts:cogGreek:" + source["work"]
        assert not any(w["aliases"].get("cts") == invented_alias
                       for w in registry["works"].values())


def test_upstream_typo_reports_keep_both_readings_and_source_identity():
    source,_,_ = next(g for g in intake.candidates() if g[0]["ebook_id"] == 66595)
    changes = intake.upstream_corrections(source)
    assert len(changes) == 27
    assert changes[0]["original"] == "πρυκατηλειμένας"
    assert changes[0]["corrected"] == "προκατηλειμένας"
    assert all(c["source_sha256"] == source["source_sha256"] for c in changes)


def test_duplicate_scan_ignores_paragraph_boundary_and_pins_candidate_tokens(tmp_path,monkeypatch):
    words="ἄνδρα μοι ἔννεπε μοῦσα πολύτροπον ὃς μάλα πολλὰ πλάγχθη ἐπεὶ Τροίης ἱερὸν πτολίεθρον ἔπερσεν πολλῶν δ᾽ ἀνθρώπων ἴδεν ἄστεα καὶ νόον ἔγνω πολλὰ δ᾽ ὅ γ᾽ ἐν πόντῳ πάθεν ἄλγεα ὃν κατὰ θυμόν".split()
    path=tmp_path/"existing.jsonl"
    path.write_text('\n'.join(json.dumps({"urn":"existing","locus":str(i),"text":' '.join(part)})
                  for i,part in enumerate((words[:24],words[16:]))))
    pin=tmp_path/"pins.json";pin.write_text('{}')
    monkeypatch.setattr(intake,"PIN",pin)
    monkeypatch.setattr(intake,"DEDUP",tmp_path/"dedup.json")
    monkeypatch.setattr(intake,"baseline_files",lambda:[path])
    groups=[({"ebook_id":37641},[{"locus":"1","text":' '.join(words)}],[])]
    report=intake.scan_corpus(groups)
    assert report['matches']['37641:1'][0]['coverage']==1
    assert report['files']==1 and report['candidate_sha256']['37641:1']
    changed=[({"ebook_id":37641},[{"locus":"1","text":"different extracted passage"}],[])]
    with pytest.raises(ValueError,match="different extracted candidate"):
        intake.generate(changed)


def test_undo_refuses_an_independently_edited_admission(tmp_path,monkeypatch):
    monkeypatch.setattr(intake,"ROOT",tmp_path)
    artifacts={"data/corpus/work.jsonl":b"original",intake.AUDIT:b"audit"}
    intake.apply(artifacts)
    path=tmp_path/"data/corpus/work.jsonl"
    path.write_bytes(b"independent change")
    with pytest.raises(ValueError,match="independently modified"):
        intake.apply(artifacts,undo=True)
    path.write_bytes(b"original")
    intake.apply(artifacts,undo=True)
    assert not path.exists() and (tmp_path/intake.AUDIT).exists()


def test_recorded_admission_can_be_reversed_without_reloading_invalid_sources(tmp_path,monkeypatch):
    monkeypatch.setattr(intake,"ROOT",tmp_path)
    output="data/corpus/test.jsonl"
    audit={"output_sha256":{output:intake.sha(b"original")}}
    intake.apply({output:b"original",intake.AUDIT:intake.encoded(audit)})
    (tmp_path/output).write_bytes(b"independent change")
    with pytest.raises(ValueError,match="independently modified"):
        intake.undo_admission()
    (tmp_path/output).write_bytes(b"original")
    assert intake.undo_admission()==1
    assert not (tmp_path/output).exists() and (tmp_path/intake.AUDIT).exists()


def test_published_admission_pins_its_generator_inputs_and_every_output():
    root = intake.ROOT
    audit = json.loads((root/intake.AUDIT).read_bytes())
    assert audit["generator_sha256"] == intake.sha(Path(intake.__file__).read_bytes())
    assert audit["source_manifest_sha256"] == intake.sha(intake.PIN.read_bytes())
    assert audit["dedup_report_sha256"] == intake.sha(intake.DEDUP.read_bytes())
    for name, digest in audit["dependency_sha256"].items():
        assert intake.sha((root/"scripts"/name).read_bytes()) == digest
    for name, digest in audit["output_sha256"].items():
        assert intake.sha((root/name).read_bytes()) == digest


def test_lexical_projection_cannot_hide_a_damaged_reader_character():
    with pytest.raises(ValueError,match="text-quality defect"):
        intake.check_row_quality({'urn':'test','locus':'1','text':'θε\ufffdός','analysis_text':'θε ός'})
