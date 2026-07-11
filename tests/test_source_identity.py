"""Tests for source_identity (owned, edition-aware source ids + tags)."""

import sys
from pathlib import Path

import pytest

from source_identity import (
    Registry, IdentityError, normalize_slug,
    ASSERTED, INFERRED_SCHEME, INFERRED_DEFAULT,
    canon_tag, render_century, era_for_century,
    Ref, Locus, parse_ref, scheme_levels, scheme_depth,
    ref_matches_scheme, is_numeric_ref,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_registry import clean_name  # noqa: E402


# --- canon name cleaning --------------------------------------------------
@pytest.mark.parametrize("raw, display, slug", [
    ("[2ARISTOMBROTUS]2", "Aristombrotus", "aristombrotus"),
    ("[2ASTRAMPSYCHUS Magus]2", "Astrampsychus Magus", "astrampsychus-magus"),
    ("APOLLONIUS RHODIUS", "Apollonius Rhodius", "apollonius-rhodius"),
    ("[HOMERUS]", "Homerus", "homerus"),
    ("[ATH]ENODORUS", "Athenodorus", "athenodorus"),   # split word rejoins
    ("THEUDO[TUS]", "Theudotus", "theudotus"),
    ("DIONYSIUS *METAQENOS", "Dionysius Metaqenos", "dionysius-metaqenos"),
])
def test_clean_name_strips_markup_and_titlecases(raw, display, slug):
    cleaned = clean_name(raw)
    assert cleaned == display
    assert normalize_slug(cleaned) == slug
    assert not any(ch in cleaned for ch in "[]{}*%")


def test_clean_name_keeps_space_separated_work_number():
    # a font-marker "2" is glued to a bracket; a real work number is space-
    # separated and must survive ("Olynthiaca 2", "... De Homero 2").
    assert clean_name("Olynthiaca 2") == "Olynthiaca 2"
    assert clean_name("[2Plutarchi]2 De Homero 2") == "Plutarchi De Homero 2"


# --- tags -----------------------------------------------------------------
def test_canon_tag_century_is_signed_int():
    assert canon_tag("century", -1) == "century:-1"
    assert canon_tag("century", "14") == "century:14"
    with pytest.raises(IdentityError):
        canon_tag("century", 0)             # no year/century 0


def test_canon_tag_value_normalized_and_dim_validated():
    assert canon_tag("Genre", "Narrative Poem") == "genre:narrative-poem"
    assert canon_tag("register", "vernacular") == "register:vernacular"
    with pytest.raises(IdentityError):
        canon_tag("bogus", "x")             # unknown dimension


def test_add_tag_dedupes_sorts_and_queries():
    r = Registry()
    r.mint_author("Homer")
    r.mint_work("homer", "Iliad")
    r.add_tag("homer.iliad", "era", "Archaic")
    r.add_tag("homer.iliad", "century", -8)
    r.add_tag("homer.iliad", "era", "archaic")   # dup -> no-op
    assert r.works["homer.iliad"].tags == ["century:-8", "era:archaic"]
    assert r.works_with_tag("century", -8) == ["homer.iliad"]
    assert r.works_with_tag("era", "classical") == []


def test_render_century_bce_ce():
    assert render_century(-1) == "1st c. BCE"
    assert render_century(-5) == "5th c. BCE"
    assert render_century(14) == "14th c. CE"
    assert render_century(3) == "3rd c. CE"


def test_era_for_century():
    assert era_for_century(-5) == "classical"
    assert era_for_century(-2) == "hellenistic"
    assert era_for_century(2) == "imperial"
    assert era_for_century(13) == "byzantine"
    assert era_for_century(17) == "early-modern"


def test_tags_survive_roundtrip(tmp_path):
    r = Registry()
    r.mint_author("Homer")
    r.mint_work("homer", "Iliad")
    r.add_tag("homer.iliad", "era", "archaic")
    p = tmp_path / "r.json"
    r.save(p)
    assert Registry.load(p).works["homer.iliad"].tags == ["era:archaic"]


# --- normalization --------------------------------------------------------
def test_normalize_strips_diacritics_articles_connectives():
    assert normalize_slug("Hómēros") == "homeros"
    assert normalize_slug("Basil of Caesarea") == "basil-caesarea"
    assert normalize_slug("The Iliad") == "iliad"
    assert normalize_slug("Apollonius' Argonautica") == "apollonius-argonautica"
    assert normalize_slug("  John   Chrysostom ") == "john-chrysostom"


def test_normalize_is_idempotent_across_spellings():
    assert normalize_slug("Chrysostom") == normalize_slug("Chrỳsostom")


# --- minting + immutability ----------------------------------------------
def test_mint_and_idempotent_alias_union():
    r = Registry()
    s = r.mint_author("Homer", aliases={"wikidata": "Q8275"})
    assert s == "homer"
    # re-mint unions new aliases, same slug
    s2 = r.mint_author("Homer", slug="homer", aliases={"viaf": "224924963"})
    assert s2 == "homer"
    assert r.authors["homer"].aliases == {"wikidata": "Q8275", "viaf": "224924963"}


def test_shared_name_must_be_qualified():
    r = Registry()
    with pytest.raises(IdentityError):
        r.mint_author("John")          # ALWAYS_QUALIFY
    assert r.mint_author("John Chrysostom") == "john-chrysostom"
    assert r.mint_author("John of Damascus") == "john-damascus"


def test_alias_conflict_is_immutable():
    r = Registry()
    r.mint_author("Homer", aliases={"wikidata": "Q8275"})
    with pytest.raises(IdentityError):
        r.mint_author("Homer", slug="homer", aliases={"wikidata": "Q9999"})


def test_unknown_alias_namespace_rejected():
    r = Registry()
    with pytest.raises(IdentityError):
        r.mint_author("Homer", aliases={"bogus": "x"})


# --- resolution / dedup ---------------------------------------------------
def _seed():
    r = Registry()
    r.mint_author("Homer", aliases={"wikidata": "Q8275", "tlg": "tlg0012"})
    r.mint_work("homer", "Iliad",
                aliases={"wikidata": "Q8275", "tlg": "tlg0012.tlg001"})
    return r


def test_resolve_prefers_wikidata():
    r = _seed()
    res = r.resolve_work(qid="Q8275", name="completely wrong name")
    assert res.slug == "homer.iliad"
    assert res.method == "wikidata"
    assert res.needs_confirm is False


def test_resolve_falls_back_to_alias_then_name():
    r = _seed()
    by_tlg = r.resolve_work(aliases={"tlg": "tlg0012.tlg001"})
    assert by_tlg.slug == "homer.iliad" and by_tlg.method == "alias:tlg"
    by_name = r.resolve_work(name="Iliad")
    assert by_name.slug == "homer.iliad" and by_name.needs_confirm is True


def test_same_work_dedups_on_qid_across_different_names():
    r = _seed()
    a = {"qid": "Q8275", "name": "Iliad"}
    b = {"qid": "Q8275", "name": "Ilias"}        # different spelling, same QID
    assert r.same_work(a, b) is True
    c = {"name": "Odyssey"}                        # unknown work
    assert r.same_work(a, c) is False


# --- editions + locus -----------------------------------------------------
def _seed_with_editions():
    r = _seed()
    r.mint_edition("homer.iliad", "west-1998", "West (1998)",
                   scheme="book.line", editor="West", year=1998,
                   make_default=True,
                   aliases={"hathitrust": "uc1.b000123"})
    r.mint_edition("homer.iliad", "glaux", "GLAUx text",
                   provider="glaux", scheme="book.line")
    return r


def test_locus_certainty_levels():
    r = _seed_with_editions()
    # explicit edition -> asserted
    a = r.locus_for_citation("homer.iliad", "9.458", edition="glaux")
    assert a.edition == "homer.iliad.glaux" and a.certainty == ASSERTED
    # recognized scheme -> inferred-scheme (picks first edition with that scheme)
    s = r.locus_for_citation("homer.iliad", "9.458", scheme="book.line")
    assert s.certainty == INFERRED_SCHEME
    # nothing -> inferred-default
    d = r.locus_for_citation("homer.iliad", "9.458")
    assert d.edition == "homer.iliad.west-1998" and d.certainty == INFERRED_DEFAULT


def test_default_edition_is_mutable_policy_not_identity():
    r = _seed_with_editions()
    stored = r.locus_for_citation("homer.iliad", "9.458", edition="glaux")
    # change the display default; the already-stored locus is untouched
    r.works["homer.iliad"].default_edition = "homer.iliad.glaux"
    assert stored.edition == "homer.iliad.glaux"  # unchanged identity
    fresh = r.locus_for_citation("homer.iliad", "1.1")
    assert fresh.edition == "homer.iliad.glaux" and fresh.certainty == INFERRED_DEFAULT


def test_unknown_edition_rejected():
    r = _seed_with_editions()
    with pytest.raises(IdentityError):
        r.locus_for_citation("homer.iliad", "1.1", edition="nonesuch")


def test_reference_edition_never_auto_defaults():
    r = _seed()
    # a reference-only (TLG-keyed) edition minted first must NOT become default
    r.mint_edition("homer.iliad", "allen-1931", "Allen OCT (1931)",
                   provider="tlg-e-reference", servable=False)
    assert r.works["homer.iliad"].default_edition is None
    # the first servable edition does
    r.mint_edition("homer.iliad", "perseus", "Perseus", servable=True)
    assert r.works["homer.iliad"].default_edition == "homer.iliad.perseus"
    # but an explicit make_default can still force a reference edition
    r.mint_edition("homer.iliad", "ref2", "ref", servable=False, make_default=True)
    assert r.works["homer.iliad"].default_edition == "homer.iliad.ref2"


# --- display + persistence ------------------------------------------------
def test_preferred_id_surfaces_wikidata_not_tlg():
    r = _seed()
    assert r.preferred_id("homer.iliad") == "wikidata:Q8275"  # never tlg


def test_save_load_roundtrip(tmp_path):
    r = _seed_with_editions()
    p = tmp_path / "reg.json"
    r.save(p)
    r2 = Registry.load(p)
    assert set(r2.authors) == {"homer"}
    assert set(r2.works) == {"homer.iliad"}
    w = r2.works["homer.iliad"]
    assert w.default_edition == "homer.iliad.west-1998"
    assert set(w.editions) == {"homer.iliad.west-1998", "homer.iliad.glaux"}
    assert w.editions["homer.iliad.west-1998"].aliases["hathitrust"] == "uc1.b000123"


# --- logical-locus grammar (CTS-URN passage semantics) --------------------
@pytest.mark.parametrize("ref, levels", [
    ("1", ("1",)),
    ("1.327", ("1", "327")),
    ("1.2.3", ("1", "2", "3")),
    ("327a", ("327a",)),                       # Stephanus page-letter
    ("Α.1", ("Α", "1")),                       # Greek book letter as a level
    ("I", ("I",)),                             # roman numeral
    ("sch_Ph.2", ("sch_Ph", "2")),            # scholion key
    ("porfyrogen-administrato.1",              # cog work-slug section: '-' is a
     ("porfyrogen-administrato", "1")),        # level character, not a range
])
def test_parse_ref_points(ref, levels):
    r = parse_ref(ref)
    assert isinstance(r, Ref)
    assert r.levels == levels
    assert r.is_range is False
    assert r.depth == len(levels)
    assert str(r) == ref                        # round-trips


def test_parse_ref_range_matching_depth():
    r = parse_ref("5.84-5.116")
    assert r.is_range is True
    assert r.levels == ("5", "84") and r.end == ("5", "116")
    assert r.depth == 2
    assert str(r) == "5.84-5.116"               # round-trips


def test_parse_ref_rejects_unmatched_range_depth():
    # the CTS shorthand the design forbids: endpoints of different depth
    with pytest.raises(IdentityError):
        parse_ref("5.84-116")
    with pytest.raises(IdentityError):
        parse_ref("1-2.3")


@pytest.mark.parametrize("bad", ["", "   ", ".1", "1.", "1..2", "..", "1.\t.2"])
def test_parse_ref_rejects_empty_levels(bad):
    with pytest.raises(IdentityError):
        parse_ref(bad)


def test_scheme_levels_and_depth():
    assert scheme_levels("book.chapter.line") == ("book", "chapter", "line")
    assert scheme_depth("book.chapter.line") == 3
    assert scheme_depth("section.line") == 2
    assert scheme_depth("line") == 1
    assert scheme_depth("") == 0 and scheme_levels("") == ()


def test_ref_matches_scheme():
    assert ref_matches_scheme("1.5", "book.line") is True
    assert ref_matches_scheme("1.5.3", "book.line") is False
    assert ref_matches_scheme("1", "book.line") is False
    # an unknown (empty) scheme cannot disprove a ref
    assert ref_matches_scheme("1.5.3", "") is True
    # accepts an already-parsed Ref too
    assert ref_matches_scheme(parse_ref("1.5"), "book.line") is True


def test_is_numeric_ref():
    assert is_numeric_ref("1.327") is True
    assert is_numeric_ref("327a") is True
    assert is_numeric_ref("5.84-5.116") is True          # numeric range
    assert is_numeric_ref("Α.1") is False                # Greek letter level
    assert is_numeric_ref("sch_Ph.2") is False           # scholion key
    assert is_numeric_ref("porfyrogen-administrato.1") is False


def test_locus_validates_grammar_on_construction():
    ok = Locus("homer.iliad.west-1998", "9.458")
    assert ok.parsed.levels == ("9", "458")
    # a malformed ref is rejected at construction, so no bad Locus can exist
    with pytest.raises(IdentityError):
        Locus("homer.iliad.west-1998", "5.84-116")
    with pytest.raises(IdentityError):
        Locus("homer.iliad.west-1998", "")


def test_locus_for_citation_optional_depth_validation():
    r = _seed_with_editions()                    # editions cite by book.line (depth 2)
    # depth-2 ref matches book.line under validate
    good = r.locus_for_citation("homer.iliad", "9.458", edition="glaux", validate=True)
    assert good.parsed.depth == 2
    # a depth-3 ref is allowed without validation but rejected with it
    r.locus_for_citation("homer.iliad", "9.458.2", edition="glaux")
    with pytest.raises(IdentityError):
        r.locus_for_citation("homer.iliad", "9.458.2", edition="glaux", validate=True)
