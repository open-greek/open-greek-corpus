"""Source identity must survive ambiguous titles, moved notes, and stale pins."""
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "gutenberg_audit", Path(__file__).resolve().parents[1] / "scripts/audit_glossapi_gutenberg.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_catalog_keeps_homonymous_titles_and_uses_author():
    raw = '''<h2>Author One, 1800-1900</h2><ul><li><a href="/ebooks/1">Διηγήματα</a></li></ul>
    <h2>Author Two, 1810-1910</h2><ul><li><a href="/ebooks/2">Διηγήματα</a></li></ul>
    <h2>Translator</h2><ul><li><a href="/ebooks/1">Διηγήματα</a></li></ul>'''.encode()
    candidates = audit.catalog_candidates(raw)[audit.fold("Διηγήματα")]
    assert len(candidates) == 2
    assert candidates[0]["creators"] == ["Author One, 1800-1900", "Translator"]
    chosen, method = audit.choose_candidate({"Author": "Author Two"}, candidates)
    assert chosen["ebook_id"] == 2 and method == "title_and_author"
    assert audit.choose_candidate({"Author": None}, candidates) == (None, "ambiguous")


def test_case_and_whitespace_are_ignored_but_accents_are_reported():
    assert audit.compare_text("ἄνθρωπος λέγει", "Title Ἄνθρωπος\nλέγει Footer")["coverage"] == 1
    assert audit.compare_text("ανθρωπος λεγει", "ἄνθρωπος λέγει")["coverage"] == 0
    assert audit.compare_text("ανθρωπος λεγει", "ἄνθρωπος λέγει", accents=False)["coverage"] == 1
    assert audit.compare_text("", "ἄνθρωπος")["coverage"] is None


def test_relocated_notes_do_not_become_an_ordered_match():
    first = "one two three four five six seven eight nine ten"
    note = "note alpha beta gamma delta epsilon zeta eta theta iota"
    last = "eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty"
    row, source = first + " " + note + " " + last, first + " " + last + " " + note
    assert audit.compare_text(row, source)["coverage"] < 1
    assert audit.window_coverage(row, source)["coverage"] == 1
    assert audit.window_coverage(row, "unrelated words have no exact eight word context")["coverage"] == 0


def test_metadata_records_editor_without_inventing_translator():
    raw = b'''<table class="bibrec"><tr><th>Editor</th><td>Rouse, 1863-1950</td></tr>
    <tr><th>eBook-No.</th><td>57629</td></tr></table>
    <a class="read-online-button" href="/cache/epub/57629/pg57629.html">Read</a>'''
    metadata, url = audit.book_metadata(raw, "https://www.gutenberg.org/ebooks/57629")
    assert metadata["Editor"] == ["Rouse, 1863-1950"]
    assert "Translator" not in metadata
    assert url == "https://www.gutenberg.org/cache/epub/57629/pg57629.html"


def test_cache_rejects_changed_bytes_and_unpinned_sources(tmp_path):
    name, url = "test.html", "https://www.gutenberg.org/ebooks/1"
    original = b"<html>source</html>"
    (tmp_path / name).write_bytes(original)
    pin = {"url": url, "sha256": audit.sha(original), "size": len(original)}
    cache = audit.SourceCache(tmp_path, {name: pin}, False, False)
    assert cache.get(name, url) == original
    (tmp_path / name).write_bytes(b"changed")
    with pytest.raises(ValueError, match="Changed pinned source"):
        cache.get(name, url)
    with pytest.raises(ValueError, match="Unpinned source"):
        cache.get("other.html", url)


def test_quality_does_not_hide_mixed_script_or_welded_tokens():
    result = audit.quality("ΘεοτοκίονὉ λaθος ἄνθρωπος \ufffd")
    assert result["mixed_script_tokens"] == 1
    assert result["case_join_tokens"] == 1
    assert result["replacement_characters"] == 1
    decomposed = audit.quality("α\u0313νθρωπος \u0313")
    assert decomposed["non_nfc_tokens"] == 1
    assert decomposed["orphan_combining_marks"] == 1
    assert audit.quality("λоγος")["mixed_script_tokens"] == 1  # Cyrillic o
    assert audit.quality("λόγος 123")["lexical_tokens"] == 1
    assert audit.quality("λόγος 123")["numeric_tokens"] == 1


def test_extraction_drops_website_boilerplate_but_keeps_scholarly_notes():
    raw = '<body><div id="pg-header">site</div><p>ἀρχή</p><p class="footnote">σημείωση</p><div id="pg-footer">license</div></body>'.encode()
    assert audit.source_body(raw) == "ἀρχή σημείωση"


def test_modern_editor_is_not_evidence_against_an_ancient_original():
    row = {"Text Number": 999, "Text": "ἄνδρα μοι ἔννεπε"}
    metadata = {"Author": ["Homer, 751? BCE"], "Editor": ["Editor, 1800-1900"]}
    result = audit.scope_assessment(row, metadata, "", {"exceptions": {}})
    assert result["disposition"] == "quarantined_scope"
    assert result["language"] is None


def test_review_fails_if_its_edition_evidence_is_absent():
    row = {"Text Number": 153, "Text": "ἄνδρα μοι ἔννεπε"}
    reviews = {"exceptions": {"153": {"required_source_fragments": ["syntax has been changed"]}}}
    with pytest.raises(ValueError, match="Review evidence missing"):
        audit.scope_assessment(row, {}, "unchanged classical edition", reviews)


def test_typographic_identity_preserves_the_tokenization_diagnostic():
    text = "θανατική εκτέλεσις του κακού ανθρώπου"
    spaced = "θ α ν α τ ι κ ή ε κ τ έ λ ε σ ι ς του κακού ανθρώπου"
    assert audit.compare_text(spaced, text)["coverage"] < 1
    assert audit.typographic_coverage(spaced, text, width=12)["coverage"] == 1
    assert audit.typographic_coverage(spaced, "unrelated source words", width=12)["coverage"] == 0


def test_published_audit_matches_its_code_source_pins_and_review_inputs():
    import json
    root=Path(__file__).resolve().parents[1]
    report=json.loads((root/'data/glossapi_gutenberg_identity_report.json').read_bytes())
    for field,name in (("source_manifest_sha256","data/glossapi_gutenberg_sources.json"),
                       ("source_decisions_sha256","data/glossapi_source_decisions.json"),
                       ("reviews_sha256","data/glossapi_gutenberg_reviews.json"),
                       ("generator_sha256","scripts/audit_glossapi_gutenberg.py")):
        assert report[field]==audit.sha((root/name).read_bytes())
    assert report['statistics']['rows']==214
    assert report['statistics']['identities']=={'text_matched':214}
    assert report['statistics']['scope_dispositions']=={'excluded_modern':213,'quarantined_adaptation':1}
    assert report['statistics']['eligible_whole_texts']==0
    assert report['recipe']['classifier_used_for_admission'] is False
