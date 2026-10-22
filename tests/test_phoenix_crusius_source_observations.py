"""Source review preserves printed readings, author boundaries, and supplies."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import phoenix_crusius_source_observations as source


def rows():
    return [{"urn": source.WORK, "edition": source.EDITION,
             "locus": spec["locus"], "text": spec["original_text"]}
            for spec in source.SPECS]


def test_twenty_one_unique_source_verses_and_exact_preimages():
    review = source.build_source_review(rows())
    assert [r["verse"] for r in review["verses"]] == list(range(1, 22))
    assert len(source.BODY_LOCI) == 21
    assert review["scope_accounting"]["complete_collected_fragments"] is False
    assert review["scope"] == "Phoenix Coronistae, 21 verses"
    assert review["approved_primary_loci"] == [r["locus"] for r in source.SPECS]
    assert review["source"]["phoenix_printed_pages"] == [83, 84]
    assert all(r["original_row_sha256"] for r in review["verses"])


@pytest.mark.parametrize("verse,reading", [
    (2, "ἢ λέκος πυρῶν"), (3, "ἤμαιθον, ἢ ὅτι τις χρῄζει"),
    (5, "κορώνῃ· χἄλα"), (6, "αὕτη"), (7, "ἅλας δοὺς αὖθι"),
    (10, "ἡ κούρη"), (11, "κἀφνειὸν ἄνδρα κὠνομαστὸν"),
    (13, "κούρην εἰς τὰ γοῦνα κατθείη"), (14, "θάλος"),
    (15, "ὅκου πόδες φέρουσιν"), (16, "Μούσαισι πρὸς θύραις ᾄδων"),
    (17, "πλέονα <τού>τῳ"), (18, "ὦγαθοί"), (19, "δός, ὦ ἄναξ, δὸς"),
    (20, "κορώνῃ χεῖρα δοῦν ἀπαιτούσῃ"), (21, "τοσαῦτ’"),
])
def test_scan_orthography_is_not_replaced_by_ocr_or_other_editions(verse, reading):
    assert reading in source.SPECS[verse - 1]["corrected_text"]


def test_all_printed_supplies_have_whole_token_exclusions():
    supplies = [r for s in source.SPECS for r in s["editorial_supplies"]]
    assert [r["text"] for r in supplies] == ["<τ’>", "<τ’>", "<τι>", "<τού>τῳ"]
    assert all(not r["lexical_eligible"] for r in supplies)
    assert source.SPECS[16]["corrected_text"][
        supplies[-1]["start"]:supplies[-1]["end"]] == "<τού>τῳ"


def test_edition_gap_after_seventeen_is_not_silently_concatenated():
    boundary = source.BOUNDARY_OBSERVATIONS[-1]
    assert boundary["omission_after_verse"] == 17
    assert boundary["omission_before_verse"] == 18
    assert boundary["omission_marker"] == "***"


@pytest.mark.parametrize("locus,role", [
    ("phoenix_choliambi_crusius_0012.1", "volume-front-matter"),
    ("phoenix_choliambi_crusius_0033.1", "other-work-material"),
    ("phoenix_choliambi_crusius_0068.1", "other-work-quotation"),
    ("phoenix_choliambi_crusius_0068.2", "work-title"),
    ("phoenix_choliambi_crusius_0070.1", "other-work-material"),
    ("phoenix_choliambi_crusius_0072.1", "other-work-or-index"),
    ("phoenix_choliambi_crusius_0105.9", "volume-index"),
])
def test_volume_content_is_not_attributed_to_phoenix(locus, role):
    result = source.classify_locus(locus)
    assert result["text_role"] == role
    assert not result["lexical_eligible"]


def test_only_reviewed_twenty_one_loci_can_be_admitted():
    assert source.classify_locus("phoenix_choliambi_crusius_0068.3")["lexical_eligible"]
    assert source.classify_locus("phoenix_choliambi_crusius_0069.6")["lexical_eligible"]
    assert not source.classify_locus("phoenix_choliambi_crusius_0069.7")["lexical_eligible"]
    assert not source.classify_locus("phoenix_choliambi_crusius_0068.18")["lexical_eligible"]


@pytest.mark.parametrize("locus", ["other_0068.3", "phoenix_choliambi_crusius_0108.1", "phoenix_choliambi_crusius_0068.0"])
def test_unrecognized_source_loci_fail_closed(locus):
    with pytest.raises(ValueError):
        source.classify_locus(locus)


def test_changed_missing_duplicate_and_wrong_work_preimages_are_rejected():
    for mutate in (
        lambda r: r[0].update(text="different reading"),
        lambda r: r.pop(),
        lambda r: r.append(deepcopy(r[0])),
        lambda r: r[0].update(urn="herodas.mimiambi"),
        lambda r: r[0].update(edition="other-edition"),
    ):
        current = rows()
        mutate(current)
        with pytest.raises(ValueError):
            source.build_source_review(current)


def test_review_timestamp_is_explicit_and_utc():
    with pytest.raises(ValueError):
        source.build_source_review(rows(), reviewed_at="2026-10-22T03:40:59")
    review = source.build_source_review(rows(), reviewed_at="2026-10-22T04:00:00Z")
    assert {r["reviewed_at"] for r in review["verses"]} == {"2026-10-22T04:00:00Z"}


def test_compilation_does_not_mutate_authority_or_input_rows():
    current = rows()
    original = deepcopy(current)
    review = source.build_source_review(current)
    review["verses"][0]["corrected_text"] = "changed output"
    review["source"]["year"] = 2026
    assert current == original
    assert source.SOURCE["year"] == 1894
    assert source.SPECS[0]["corrected_text"].startswith("Ἐσθλοί")
