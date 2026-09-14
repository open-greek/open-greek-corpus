"""Focused parser tests for the DCC Sappho source swap."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from ingest_dcc_sappho import (  # noqa: E402
    discover_page_paths, extract_page, heading_locus, is_reading_text,
)


def test_discovers_only_poem_pages_in_menu_order():
    page = b"""<a href='/sappho/frag-1'>one</a>
    <a href='/sappho/introduction'>intro</a>
    <a href='/sappho/brothers-poem'>brothers</a>"""
    # Production discovery has a minimum-size guard; pad with valid links here
    # so this unit test also exercises that guard's successful side.
    page += b"".join(
        f"<a href='/sappho/frag-{n}'>x</a>".encode() for n in range(2, 92)
    )
    paths = discover_page_paths(page)
    assert paths[:3] == ["/sappho/frag-1", "/sappho/brothers-poem", "/sappho/frag-2"]
    assert "/sappho/introduction" not in paths


def test_heading_parser_accepts_fragment_labels_not_prose_headings():
    assert heading_locus("104a") == "104a"
    assert heading_locus("Fragment 59: Continuation") == "59"
    assert heading_locus('Lines preceding "The Tithonus poem"') is None
    assert heading_locus("28a 28b 28c") is None


def test_extracts_greek_lines_and_drops_notes_numbers_and_commentary():
    page = """<article><div class='field--name-body'>
      <p>ποικιλόθρον’ ἀθανάτ’ Ἀφρόδιτα,<span class='line-number'>1</span></p>
      <p>παῖ Δίος<fn>Campbell prints a variant.</fn></p>
      <p><em>Π preserves the line beginnings and Π2 the endings.</em></p>
      <div class='field--name-commentary'><p>not this Greek λόγος</p></div>
    </div></article>""".encode()
    records = extract_page("/sappho/frag-1", page)
    assert len(records) == 1
    assert records[0]["locus"] == "1"
    assert records[0]["text_lines"] == [
        "ποικιλόθρον’ ἀθανάτ’ Ἀφρόδιτα,",
        "παῖ Δίος",
    ]
    assert "Campbell" not in records[0]["text"]
    assert "beginnings" not in records[0]["text"]


def test_grouped_pages_split_on_numeric_headings():
    page = """<article><div class='field--name-body'>
      <h4>104a</h4><p>Ἔσπερε πάντα φέρων</p>
      <h4>104b</h4><p>ἀστέρων πάντων κάλλιστος</p>
    </div></article>""".encode()
    records = extract_page("/sappho/frag-104-117", page)
    assert [record["locus"] for record in records] == ["104a", "104b"]


def test_reading_text_rejects_english_explanation_containing_greek():
    assert is_reading_text("ἀστέρων πάντων κάλλιστος")
    assert not is_reading_text("Π preserves the line beginnings and Π the line endings")
