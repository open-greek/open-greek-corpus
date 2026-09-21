import json
from pathlib import Path

from scripts.stage_glossapi_ekklisiastika import (
    _corpus_family,
    _display_path,
    _load_source,
    build_report,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "glossapi_ekklisiastika_rows.json"


def _rows():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _corpus(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    record = {
        "urn": "septuaginta.psalmi",
        "locus": "103.1",
        "source": "first1k",
        "license": "CC-BY-SA-4.0",
        "text": "Εὐλόγει, ἡ ψυχή μου, τὸν Κύριον.",
    }
    (corpus / "psalmi.jsonl").write_text(
        json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return corpus


def test_stage_preserves_provenance_and_repairs_only_known_join_boundaries(tmp_path):
    report = build_report(_rows(), _load_source(), _corpus(tmp_path))
    first = report["records"][0]

    assert first["provenance"]["source_url"] == "https://glt.goarch.org/#02"
    assert first["provenance"]["title"] == "Δευτέρα"
    assert first["provenance"]["category"] == "ΟΚΤΩΗΧΟΣ"
    assert first["provenance"]["revision"] == "e3e66c08c7a51beb96dc642e012c5ed3de946100"
    assert first["provenance"]["artifact_sha256"] == (
        "ec4d18951392d90650f96fe5232d2527aa4deed2164b171a8501e50b408593ae"
    )
    assert first["cleaning"]["known_join_repairs"] == 1
    assert first["cleaning"]["structural_rubrics_removed"] >= 3
    assert first["biblical_or_quotation_passages"] == 1


def test_stage_quarantines_unresolved_boundaries_and_never_admits_raw_rows(tmp_path):
    report = build_report(_rows(), _load_source(), _corpus(tmp_path))
    third = report["records"][2]

    assert third["admission"] == "quarantined"
    assert "unresolved_source_work_identity" in third["reasons"]
    assert "unresolved_join_boundary" in third["reasons"]
    assert report["dispositions"]["admitted"] == []
    assert report["admission_policy"]["corpus_write_attempted"] is False
    assert report["admission_policy"]["public_lexicon_rebuild_attempted"] is False


def test_stage_reports_within_source_and_existing_biblical_witnesses(tmp_path):
    report = build_report(_rows(), _load_source(), _corpus(tmp_path))
    stats = report["statistics"]

    assert stats["within_source_exact_duplicate_passages"] == 2
    assert stats["existing_corpus_exact_duplicate_passages"] == 1
    assert stats["existing_corpus_match_families"] == {"biblical": 1}
    witnesses = report["records"][0]["existing_corpus_matches"]
    assert witnesses[0]["passage_locus"] == "0001.p0002"
    assert witnesses[0]["witnesses"] == [
        {
            "edition": "",
            "family": "biblical",
            "locus": "103.1",
            "relation": "exact",
            "source": "first1k",
            "urn": "septuaginta.psalmi",
        }
    ]


def test_stage_loci_are_stable_artifact_row_loci_not_claimed_edition_loci(tmp_path):
    report = build_report(_rows(), _load_source(), _corpus(tmp_path))

    assert [record["locus"] for record in report["records"]] == [
        "row:0001",
        "row:0002",
        "row:0003",
    ]
    assert all(record["provisional_work_key"].startswith("glossapi-ekklisiastika-")
               for record in report["records"])


def test_display_path_keeps_an_output_outside_the_repository_absolute(tmp_path):
    output = tmp_path / "report.json"
    assert _display_path(output) == output
    assert _display_path(ROOT / "data" / "report.json") == Path("data/report.json")


def test_corpus_family_uses_stable_urn_identity_when_the_witness_is_ocr():
    assert _corpus_family(
        {"urn": "athanasius-theology.expositiones-in-psalmos", "source": "ocr"}
    ) == "patristic"
    assert _corpus_family(
        {"urn": "novum-testamentum.evangelium-secundum-joannem", "source": "first1k"}
    ) == "biblical"
