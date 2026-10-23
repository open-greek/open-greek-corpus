"""A frozen source assessment must survive later repairs and reject drift."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_acharnians_source_pilot as pilot


@pytest.fixture
def retained(tmp_path):
    shutil.copytree(ROOT / pilot.BUNDLE, tmp_path / pilot.BUNDLE)
    return tmp_path


def test_frozen_scope_accounts_for_every_published_token_and_row():
    report = pilot.build()
    catalog = json.loads((ROOT / pilot.BUNDLE / "catalog-row.json").read_bytes())
    assert report["total"]["greek_tokens"] == int(catalog["tokens"])
    assert report["total"]["rows"] == int(catalog["passages"])
    assert sum(r["rows"] for r in report["regions"]) == report["total"]["rows"]
    assert sum(r["greek_tokens"] for r in report["regions"]) == report["total"]["greek_tokens"]
    assert report["corrections_applied"] == 0
    assert all(r["status"] == "observed_not_applied" for r in report["observations"])


def test_frozen_checker_does_not_need_current_primary_or_pdf_renderer(retained, monkeypatch):
    # The evidence remains inspectable after a future corrected work replaces
    # the primary, without importing the optional rendering dependency.
    monkeypatch.setitem(sys.modules, "pymupdf", None)
    report = pilot.build(retained)
    assert pilot.encoded(report) == (retained / pilot.REPORT).read_bytes()
    assert len(report["pages"]) == 10
    assert report["sample"]["source_pages_with_rows"] == 8  # Two section titles have no Greek primary rows.


@pytest.mark.parametrize("name", ["page-0073.png", "page-0073-tesseract.txt", "scandata.xml", "baseline.jsonl.gz", "catalog-row.json"])
def test_changed_retained_evidence_is_rejected(retained, name):
    path = retained / pilot.BUNDLE / name
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="frozen source pin"):
        pilot.build(retained)


def test_changed_manifest_cannot_redirect_scan_or_baseline(retained):
    path = retained / pilot.BUNDLE / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["pages"][0]["pdf_page"] = 10
    manifest["baseline"]["sha256"] = "0" * 64
    path.write_bytes(pilot.encoded(manifest))
    with pytest.raises(ValueError, match="Source manifest"):
        pilot.build(retained)


def test_scan_mapping_is_rechecked_even_if_manifest_pin_is_accidentally_revised(retained, monkeypatch):
    path = retained / pilot.BUNDLE / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["pages"][2]["printed_page"] = "17"
    raw = pilot.encoded(manifest)
    path.write_bytes(raw)
    monkeypatch.setattr(pilot, "MANIFEST_SHA", pilot.sha(raw))
    with pytest.raises(ValueError, match="PDF-to-scan mapping changed"):
        pilot.build(retained)


@pytest.mark.parametrize("mutation,error", [
    (lambda rows: rows[1].update(locus=rows[0]["locus"]), "Duplicate primary locus"),
    (lambda rows: rows[0].update(locus="scholia_aristoph_dubner_bad.1"), "Unexpected locus"),
    (lambda rows: rows[0].update(urn="another-work"), "Unexpected work attribution"),
    (lambda rows: rows[0].update(analysis_text="an excluded projection"), "unaccounted lexical exclusions"),
    (lambda rows: next(r for r in rows if r["locus"] == "scholia_aristoph_dubner_0073.9").update(text="changed reading"), "Observation preimage changed"),
])
def test_semantic_drift_cannot_silently_change_accounting_or_observation(mutation, error, monkeypatch):
    manifest, rows = pilot.load_bundle(ROOT)
    rows = deepcopy(rows)
    mutation(rows)
    monkeypatch.setattr(pilot, "load_bundle", lambda _: (manifest, rows))
    with pytest.raises(ValueError, match=error):
        pilot.build()


def test_current_baseline_option_detects_changed_primary(retained, monkeypatch):
    path = retained / pilot.PRIMARY
    path.parent.mkdir(parents=True)
    path.write_bytes(b"a future source repair")
    monkeypatch.setattr(sys, "argv", ["audit", "--root", str(retained), "--check-current"])
    with pytest.raises(ValueError, match="Current primary"):
        pilot.main()
    # The immutable historical audit is still valid.
    assert pilot.build(retained)["corrections_applied"] == 0


def test_generated_report_and_document_are_current():
    report = pilot.build()
    assert (ROOT / pilot.REPORT).read_bytes() == pilot.encoded(report)
    assert (ROOT / pilot.DOC).read_bytes() == pilot.markdown(report)
