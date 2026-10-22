"""Phoenix edition credits follow the exact reviewed work scope."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT)]
import reviewed_manifestations as reviewed
from source_identity import Registry

SLUG = "phoenix.fragmenta"
PRIMARY = f"data/corpus/{SLUG}.jsonl"
RETAINED = "data/paratext/crusius-1894-legacy.jsonl"
DIRECTORY = "data/corpus_changes/phoenix-crusius-review"
AUDIT = DIRECTORY + "/changes.json"
PACKET = DIRECTORY + "/source-review.json"
ORIGINAL_SHA = "9015e9406b4c768489e014c1874c064c3913738aa4954433b7932ea3ee914ce9"
SOURCE = {
    "url": "https://archive.org/download/herondaemimiamb01hero/herondaemimiamb01hero.pdf",
    "sha256": "999122f204d54ec0071749c354598adef4203ea6fc61b53e4a6b0f5df92aade1",
    "title": "Herondae mimiambi, Crusius 1894", "editor": "Crusius, Otto", "year": 1894,
}
EDITION = "crusius-1894-source-reviewed"
HISTORICAL = "qwen36-phoenix_choliambi_crusius"
APPROVED = [f"phoenix_choliambi_crusius_0068.{n}" for n in range(3, 18)]
APPROVED += [f"phoenix_choliambi_crusius_0069.{n}" for n in range(1, 7)]


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (json.dumps(value, ensure_ascii=False) + "\n").encode()
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def jsonl(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()


@pytest.fixture
def admission(tmp_path):
    rows = [{"urn": SLUG, "edition": EDITION, "source": "ocr", "license": "PD",
        "locus": locus, "text": "λόγος"} for locus in APPROVED]
    outside = [{"urn": SLUG, "edition": HISTORICAL, "source": "ocr", "license": "PD",
        "locus": f"legacy_{n}", "text": "Unseparated historical source reading",
        "class": "outside-work-edition-material"} for n in range(2728)]
    review_sha = put(tmp_path, PACKET, {"source": SOURCE,
        "approved_primary_loci": APPROVED, "scope": "Phoenix Coronistae, 21 verses"})
    audit = {"schema_version": 1, "inputs": {PRIMARY: ORIGINAL_SHA},
        "outputs": {PRIMARY: put(tmp_path, PRIMARY, jsonl(rows)),
            RETAINED: put(tmp_path, RETAINED, jsonl(outside))},
        "counts": {"primary_rows": 21, "retained_outside_primary": 2728,
            "original_rows": 2749, "changed_text_rows": 4},
        "evidence": {"original_corpus_sha256": ORIGINAL_SHA, "source": dict(SOURCE),
            "source_review": {"path": PACKET, "sha256": review_sha}}}
    put(tmp_path, AUDIT, audit)
    return tmp_path, audit


def registry():
    result = Registry()
    result.mint_author("Phoenix", slug="phoenix")
    result.mint_work("phoenix", "Fragmenta", slug=SLUG,
        aliases={"cts": "urn:cts:greekLit:tlg1606.tlg001"})
    result.mint_edition(SLUG, HISTORICAL, "Previously misassigned whole-volume OCR",
        provider="ocr", license="PD", make_default=True)
    return result


def test_only_the_reviewed_phoenix_work_scope_is_credited(admission):
    root, audit = admission
    reg = registry()
    metadata = reviewed.register_reviewed_manifestations(reg, root)
    assert set(metadata) == {SLUG}
    work = reg.works[SLUG]
    assert work.title == "Fragmenta"
    assert work.author == "phoenix"
    assert work.aliases == {"cts": "urn:cts:greekLit:tlg1606.tlg001"}
    assert work.default_edition == SLUG + "." + EDITION
    chosen = work.editions[work.default_edition]
    assert chosen.source == SOURCE["url"] and chosen.license == "PD"
    assert chosen.provider == "ocr" and chosen.storage == "primary" and chosen.servable
    assert chosen.editor == "Crusius, Otto" and chosen.year == 1894
    old = work.editions[SLUG + "." + HISTORICAL]
    assert old.storage == "paratext" and not old.servable
    composition = work.coverage_composition
    assert composition["counts"] == audit["counts"]
    assert composition["primary_quality"] == {
        "status": "source-reviewed", "scope": "Phoenix Coronistae, 21 verses", "passages": 21}
    assert "does not represent all surviving Phoenix fragments" in composition["qualification"]
    assert "have not been fully reviewed" in composition["qualification"]
    primary, outside = composition["components"]
    assert primary["passages"] == 21 and outside["passages"] == 2728
    assert outside["path"] == RETAINED and outside["storage"] == "paratext"
    assert "retained-primary" not in {c.get("role") for c in composition["components"]}


def test_phoenix_credits_are_idempotent_and_create_disabled_historical_edition(admission):
    root, _ = admission
    reg = registry()
    reg.works[SLUG].editions.clear()
    reviewed.register_reviewed_manifestations(reg, root)
    path = root / "registry.json"
    reg.save(path)
    first = path.read_bytes()
    restored = Registry.load(path)
    reviewed.register_reviewed_manifestations(restored, root)
    restored.save(path)
    assert path.read_bytes() == first
    assert not restored.works[SLUG].editions[SLUG + "." + HISTORICAL].servable


def test_no_audit_has_no_phoenix_claim(tmp_path):
    assert reviewed._phoenix(tmp_path) == {}


def test_exact_unapply_does_not_activate_reviewed_credits(admission, monkeypatch):
    root, _ = admission
    actual_sha = reviewed._sha
    monkeypatch.setattr(reviewed, "_sha", lambda path:
        ORIGINAL_SHA if path == root / PRIMARY else actual_sha(path))
    assert reviewed._phoenix(root) == {}


@pytest.mark.parametrize("name", [PRIMARY, RETAINED, PACKET])
def test_changed_active_output_or_packet_is_rejected(admission, name):
    root, _ = admission
    with (root / name).open("ab") as stream:
        stream.write(b" \n")
    with pytest.raises(ValueError, match="evidence changed"):
        reviewed._phoenix(root)


@pytest.mark.parametrize("field,value", [
    ("primary_rows", 2749), ("retained_outside_primary", 0),
    ("original_rows", 2750), ("changed_text_rows", 22), ("changed_text_rows", "4"),
])
def test_changed_work_partition_is_rejected(admission, field, value):
    root, audit = admission
    audit["counts"][field] = value
    put(root, AUDIT, audit)
    with pytest.raises(ValueError, match="assignment counts changed"):
        reviewed._phoenix(root)


@pytest.mark.parametrize("field,value", [("sha256", "other-source"),
    ("url", "https://example.org/another.pdf"), ("year", 1897)])
def test_changed_edition_source_is_rejected(admission, field, value):
    root, audit = admission
    audit["evidence"]["source"][field] = value
    put(root, AUDIT, audit)
    with pytest.raises(ValueError, match="source identity changed"):
        reviewed._phoenix(root)


@pytest.mark.parametrize("field,value", [("scope", "Entire anthology"),
    ("approved_primary_loci", APPROVED[:-1]), ("source", {**SOURCE, "sha256": "other-source"})])
def test_rehashed_packet_cannot_broaden_the_reviewed_scope(admission, field, value):
    root, audit = admission
    packet = json.loads((root / PACKET).read_text())
    packet[field] = value
    audit["evidence"]["source_review"]["sha256"] = put(root, PACKET, packet)
    put(root, AUDIT, audit)
    with pytest.raises(ValueError, match="review scope changed"):
        reviewed._phoenix(root)


@pytest.mark.parametrize("field,value", [("locus", "phoenix_choliambi_crusius_0068.2"),
    ("urn", "herodas.mimiambi"), ("edition", HISTORICAL), ("license", "unknown")])
def test_rehashed_primary_still_requires_the_approved_work_rows(admission, field, value):
    root, audit = admission
    rows = [json.loads(line) for line in (root / PRIMARY).read_text().splitlines()]
    rows[0][field] = value
    audit["outputs"][PRIMARY] = put(root, PRIMARY, jsonl(rows))
    put(root, AUDIT, audit)
    with pytest.raises(ValueError, match="primary row identity changed"):
        reviewed._phoenix(root)


@pytest.mark.parametrize("field,value", [("locus", APPROVED[0]),
    ("urn", "herodas.mimiambi"), ("class", "reviewed-Herodas-body")])
def test_rehashed_archive_cannot_claim_reviewed_constituent_roles(admission, field, value):
    root, audit = admission
    rows = [json.loads(line) for line in (root / RETAINED).read_text().splitlines()]
    rows[0][field] = value
    audit["outputs"][RETAINED] = put(root, RETAINED, jsonl(rows))
    put(root, AUDIT, audit)
    with pytest.raises(ValueError, match="outside-work rows changed"):
        reviewed._phoenix(root)


def test_bundled_scan_must_match_the_reviewed_source(admission):
    root, _ = admission
    put(root, DIRECTORY + "/source-scan.pdf", b"a different printed edition")
    with pytest.raises(ValueError, match="evidence changed"):
        reviewed._phoenix(root)


def test_rehashed_audit_cannot_change_the_original_corpus_pin(admission):
    root, audit = admission
    audit["inputs"][PRIMARY] = "another-preimage"
    put(root, AUDIT, audit)
    with pytest.raises(ValueError, match="original corpus pin changed"):
        reviewed._phoenix(root)
