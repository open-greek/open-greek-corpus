"""Policy and identity regressions for the discovery-only catalog audit."""
from scripts.audit_greek_library import build, disposition, work_key


def entry(**overrides):
    e = dict(id="tlg0001.tlg001.local001", origin="source-library", author="Author",
             title="A work", workPath="/works/tlg0001.tlg001.local001/",
             objectKey="works/tlg0001/tlg001/local001.json",
             license={"url": "https://creativecommons.org/licenses/by-sa/4.0/"})
    return e | overrides


def test_excluded_origin_cannot_be_cleared_by_site_license():
    for origin in ("tlg-e", "cllg-freed", "vesuvius"):
        assert disposition(entry(origin=origin))[0] == "excluded"


def test_restrictive_or_absent_edition_license_never_passes():
    for url in ("https://creativecommons.org/licenses/by-nc/4.0/",
                "https://creativecommons.org/licenses/by-nd/4.0/"):
        assert disposition(entry(license={"url": url}))[0] == "excluded"
    assert disposition(entry(license=None))[0] == "rights-review"


def test_work_key_keeps_lettered_subworks_and_drops_passages():
    assert work_key("urn:cts:greekLit:tlg0007.tlg082a.local001:1.2") == "tlg0007.tlg082a"


def test_same_title_does_not_establish_identity():
    works = {"other.work": {"title": "A work", "work_anchors": {"cts": "urn:cts:greekLit:tlg0002.tlg001"}}}
    row = build({"entries": [entry()]}, works, {})[0]
    assert row["coverage"] == "unmatched-anchor"
    assert row["possible_title_matches"] == "other.work"


def test_alternate_catalog_numbering_is_flagged_for_review():
    works = {"euripides.work": {"title": "A work", "work_anchors": {"tlg": "tlg0006.tlg034"}}}
    catalog = [{"slug": "euripides.work", "cts_urn": "urn:cts:greekLit:tlg0006.tlg001"}]
    row = build({"entries": [entry(id="tlg0006.tlg001.local001")]}, works, {}, catalog)[0]
    assert row["coverage"] == "catalog-anchor-review"
    assert row["catalog_anchor_slugs"] == "euripides.work"


def test_reviewed_volume_overlap_survives_regeneration():
    e = entry()
    reviews = {e["id"]: {"status": "overlap", "overlap_slug": "volume.opera"}}
    row = build({"entries": [e]}, {}, {}, reviews=reviews)[0]
    assert row["review_overlap_slug"] == "volume.opera"
    assert row["review_status"] == "overlap"


def test_reviewed_import_is_not_reported_as_a_new_missing_anchor():
    e = entry(origin="ocr-tgl")
    reviews = {e["id"]: {"status": "imported-reviewed", "overlap_slug": "new.work"}}
    works = {"new.work": {"title": "Reviewed edition", "work_anchors": {}}}
    row = build({"entries": [e]}, works, {}, reviews=reviews)[0]
    assert row["coverage"] == "reviewed-overlap"
