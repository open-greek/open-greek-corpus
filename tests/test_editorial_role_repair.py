"""Literal source-role replay, complete citation routing, and guarded reversal."""
from copy import deepcopy
import gzip
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import editorial_role_manifestations as manifestations
import repair_editorial_roles as repair


def read_jsonl(path):
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]


def replace_bytes(root, relative, raw):
    path = root / relative
    if path.is_symlink():
        path.unlink()
    path.write_bytes(raw)


def reseal_output(root, relative, raw):
    """An edited checksum must never substitute for source replay."""
    replace_bytes(root, relative, raw)
    path = root / repair.AUDIT / "changes.json"
    audit = json.loads(path.read_bytes())
    audit["outputs"][relative] = repair.sha(raw)
    path.write_bytes(repair.encoded(audit))


def core_state(root):
    return {relative: (root / relative).read_bytes() if (root / relative).is_file() else None
            for relative in repair.CORE}


@pytest.fixture(scope="session")
def applied_template(tmp_path_factory):
    """Compile once; individual cases link large immutable source artifacts."""
    target = tmp_path_factory.mktemp("editorial-role-template")
    archive = ROOT / repair.AUDIT
    if (archive / "changes.json").exists():
        before = json.loads(gzip.decompress((archive / "before.json.gz").read_bytes()))
        pdf = archive / "source-herodas.pdf"
        tei = archive / "source-hipponax.xml"
    else:
        # This path supports the first review before its archive is committed.
        # Published tests use the committed, self-contained source archive.
        pdf = Path(os.environ.get("HERODAS_REVIEW_SOURCE_PDF", ""))
        tei = ROOT / "sources/first1k/data/tlg0233/tlg001/tlg0233.tlg001.1st1K-grc1.xml"
        if not pdf.is_file() or not tei.is_file():
            pytest.skip("The first source-role review has not yet been archived")
        before = {relative: (ROOT / relative).read_text() if (ROOT / relative).is_file() else None
                  for relative in repair.CORE}
    for relative, text in before.items():
        if text is not None:
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    repair.run(target, "apply", source_pdf=pdf, source_tei=tei,
               reviewed_at="2026-10-22T20:00:00+00:00")
    repair.verify(target)
    return target


@pytest.fixture
def workspace(tmp_path, applied_template):
    for relative in repair.CORE:
        source = applied_template / relative
        if source.is_file():
            path = tmp_path / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(source.read_bytes())
    target_archive = tmp_path / repair.AUDIT
    target_archive.mkdir(parents=True, exist_ok=True)
    for source in (applied_template / repair.AUDIT).iterdir():
        target = target_archive / source.name
        if source.name in repair.SOURCE_FILES:
            target.symlink_to(source)
        else:
            target.write_bytes(source.read_bytes())
    return tmp_path


def test_real_source_partition_preserves_every_literal_character(workspace):
    audit, before, outputs = repair.verify(workspace)
    records = [json.loads(line) for line in gzip.decompress(
        (workspace / repair.AUDIT / "records.jsonl.gz").read_bytes()).splitlines()]
    assert len(records) == 141
    assert audit["counts"]["herodas.mimiambi"]["primary_rows"] == 62
    assert audit["counts"]["herodas.mimiambi"]["retained_spans"] == 84
    assert audit["counts"]["hipponax.fragmenta"]["primary_rows"] == 1
    assert audit["counts"]["hipponax.fragmenta"]["retained_spans"] == 4
    assert audit["counts"]["herodas.mimiambi"]["original_analysis_tokens"] == 2846
    assert audit["counts"]["herodas.mimiambi"]["primary_analysis_tokens"] == 2036
    assert audit["counts"]["herodas.mimiambi"]["retained_analysis_tokens"] == 810
    assert audit["counts"]["hipponax.fragmenta"]["original_analysis_tokens"] == 154
    assert audit["counts"]["hipponax.fragmenta"]["primary_analysis_tokens"] == 25
    assert audit["counts"]["hipponax.fragmenta"]["retained_analysis_tokens"] == 129
    for counts in audit["counts"].values():
        for basis in ("surface", "analysis"):
            assert counts[f"original_{basis}_tokens"] == (
                counts[f"primary_{basis}_tokens"] + counts[f"retained_{basis}_tokens"])
    for record in records:
        assert record["original_row"]["text"] == record["original_text"]
        if record["work"] == "herodas.mimiambi":
            spans = record["source_spans"]
            assert "".join(span["text"] for span in spans) == record["original_text"]
            assert spans[0]["start"] == 0
            assert spans[-1]["end"] == len(record["original_text"])
            for left, right in zip(spans, spans[1:]):
                assert left["end"] == right["start"]
            body = " ".join(span["text"].strip() for span in spans
                            if span["lexical_eligible"] and span["text"].strip())
            assert record["corrected_text"] == body
            assert [row["text"] for row in record["retained_rows"]] == [
                span["text"] for span in spans if not span["lexical_eligible"]]
        elif record["retained_rows"]:
            assert record["retained_rows"][0]["text"] == record["original_text"]
        else:
            assert record["corrected_row"] == record["original_row"]
    for work in repair.WORKS:
        original = {row["locus"]: row for row in [json.loads(line)
            for line in before[repair.PRIMARY[work]].splitlines()]}
        work_records = [record for record in records if record["work"] == work]
        assert {record["locus"] for record in work_records} == set(original)
        assert all(record["original_row"] == original[record["locus"]] for record in work_records)
        assert outputs[repair.PRIMARY[work]] == (workspace / repair.PRIMARY[work]).read_bytes()


def test_existing_variants_and_corrections_survive_without_new_spellings(workspace):
    _, before, _ = repair.verify(workspace)
    original_hipponax = [json.loads(line) for line in before[repair.PRIMARY["hipponax.fragmenta"]].splitlines()]
    primary = read_jsonl(workspace / repair.PRIMARY["hipponax.fragmenta"])
    assert primary == original_hipponax[:1]
    retained = read_jsonl(workspace / repair.RETAINED["hipponax.fragmenta"])
    for row, old in zip(retained, original_hipponax[1:], strict=True):
        assert all(row[key] == value for key, value in old.items())
    apparatus = next(row for row in retained if row["locus"] == "variants")
    assert all(reading in apparatus["text"] for reading in
               ("πολτοχάρυβδιν", "ποντοχάρυβδιν", "παντοχάρυβδιν", "Wachsmuth", "Meineke", "Bergk"))
    original_herodas = {row["locus"]: row for row in [json.loads(line)
        for line in before[repair.PRIMARY["herodas.mimiambi"]].splitlines()]}
    for relative in (repair.PRIMARY["herodas.mimiambi"], repair.RETAINED["herodas.mimiambi"]):
        for row in read_jsonl(workspace / relative):
            original = original_herodas[row.get("original_locus", row["locus"])]
            assert row.get("corrections") == original.get("corrections")


def test_all_old_citations_resolve_and_existing_aliases_remain_exact(workspace):
    _, before, _ = repair.verify(workspace)
    original = json.loads(before[repair.ALIASES])
    current = json.loads((workspace / repair.ALIASES).read_bytes())
    for work, aliases in original["aliases"].items():
        assert current["aliases"][work] == aliases
    for key in original.keys() - {"aliases"}:
        assert current[key] == original[key]
    for work in repair.WORKS:
        old_rows = [json.loads(line) for line in before[repair.PRIMARY[work]].splitlines()]
        destinations = current["aliases"][work]
        assert set(destinations) == {row["locus"] for row in old_rows}
        known = {relative: {row["locus"] for row in read_jsonl(workspace / relative)}
                 for relative in (repair.PRIMARY[work], repair.RETAINED[work])}
        for locus, destination in destinations.items():
            assert destination["path"] in known
            assert destination["locus"] == locus
            assert locus in known[destination["path"]]
    assert current["aliases"]["hipponax.fragmenta"]["variants"]["path"] == repair.RETAINED["hipponax.fragmenta"]


def test_apply_is_idempotent_and_undo_reapply_restore_exact_bytes(workspace):
    audit, before, _ = repair.verify(workspace)
    after = core_state(workspace)
    artifact_pins = {path: repair.sha((workspace / path).read_bytes()) for path in audit["outputs"]}
    repair.run(workspace, "apply")
    assert core_state(workspace) == after
    assert artifact_pins == {path: repair.sha((workspace / path).read_bytes()) for path in artifact_pins}
    repair.run(workspace, "undo")
    assert core_state(workspace) == {path: text.encode() if text is not None else None
                                     for path, text in before.items()}
    assert manifestations.metadata(workspace) == {}
    repair.run(workspace, "undo")
    repair.run(workspace, "apply")
    assert core_state(workspace) == after
    repair.verify(workspace)


@pytest.mark.parametrize("name", ["source-herodas.pdf", "source-hipponax.xml", "source-review.json", "records.jsonl.gz"])
def test_literal_undo_survives_removed_evidence(workspace, name):
    _, before, _ = repair.verify(workspace)
    (workspace / repair.AUDIT / name).unlink()
    repair.run(workspace, "undo")
    assert core_state(workspace) == {path: text.encode() if text is not None else None
                                     for path, text in before.items()}
    assert manifestations.metadata(workspace) == {}


@pytest.mark.parametrize("relative", sorted(repair.CORE))
def test_undo_refuses_changed_core_without_overwriting_any_file(workspace, relative):
    path = workspace / relative
    path.write_bytes(path.read_bytes() + b" ")
    before = core_state(workspace)
    with pytest.raises(ValueError, match="modified editorial"):
        repair.run(workspace, "undo")
    assert core_state(workspace) == before


def test_rehashed_alias_attack_still_fails_literal_replay(workspace):
    aliases = json.loads((workspace / repair.ALIASES).read_bytes())
    aliases["aliases"]["hipponax.fragmenta"]["variants"] = {
        "path": "data/corpus/hipponax.fragmenta.jsonl", "locus": "frag128", "slug": "hipponax.fragmenta"}
    reseal_output(workspace, repair.ALIASES, (json.dumps(aliases, ensure_ascii=False, indent=2) + "\n").encode())
    with pytest.raises(ValueError, match="replay"):
        repair.verify(workspace)


def test_rehashed_source_cannot_change_the_frozen_source_pin(workspace):
    relative = repair.AUDIT + "/source-hipponax.xml"
    raw = (workspace / relative).read_bytes().replace("πολτοχάρυβδιν".encode(), "παντοχάρυβδιν".encode(), 1)
    reseal_output(workspace, relative, raw)
    with pytest.raises(ValueError, match="source changed"):
        repair.verify(workspace)


@pytest.mark.parametrize("mutation", ["role", "offset", "spelling", "timestamp"])
def test_rehashed_review_cannot_change_roles_boundaries_or_spellings(workspace, mutation):
    relative = repair.AUDIT + "/source-review.json"
    review = json.loads((workspace / relative).read_bytes())
    row = next(row for row in review["rows"] if len(row["spans"]) > 1)
    if mutation == "role":
        row["spans"][0]["lexical_eligible"] = not row["spans"][0]["lexical_eligible"]
    elif mutation == "offset":
        row["spans"][0]["end"] -= 1
    elif mutation == "spelling":
        row["spans"][0]["text"] = "νέον κείμενον"
    else:
        review["reviewed_at"] = "2026-10-23T20:00:00+00:00"
    reseal_output(workspace, relative, repair.encoded(review))
    with pytest.raises(ValueError):
        repair.verify(workspace)


def test_rehashed_primary_cannot_silently_correct_a_reading(workspace):
    relative = repair.PRIMARY["herodas.mimiambi"]
    rows = read_jsonl(workspace / relative)
    rows[0]["text"] = "ἀνεξέταστον"
    reseal_output(workspace, relative, repair.jsonl(rows))
    with pytest.raises(ValueError, match="replay"):
        repair.verify(workspace)


def test_preimage_archive_cannot_redefine_published_aliases(workspace):
    relative = repair.AUDIT + "/before.json.gz"
    before = json.loads(gzip.decompress((workspace / relative).read_bytes()))
    aliases = json.loads(before[repair.ALIASES])
    aliases["aliases"]["invented.work"] = {}
    before[repair.ALIASES] = json.dumps(aliases)
    reseal_output(workspace, relative, gzip.compress(repair.encoded(before), mtime=0))
    audit_path = workspace / repair.AUDIT / "changes.json"
    audit = json.loads(audit_path.read_bytes())
    audit["inputs"][repair.ALIASES] = repair.sha(before[repair.ALIASES].encode())
    audit_path.write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError, match="aliases differ"):
        repair.run(workspace, "undo")


def test_metadata_cannot_hide_active_admission_by_forging_inputs(workspace):
    path = workspace / repair.AUDIT / "changes.json"
    audit = json.loads(path.read_bytes())
    audit["inputs"] = {name: repair.sha(raw) if raw is not None else None
                       for name, raw in core_state(workspace).items()}
    path.write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError):
        manifestations.metadata(workspace)


def test_metadata_exposes_partial_scope_and_retained_citation_paths(workspace):
    metadata = manifestations.metadata(workspace)
    assert set(metadata) == set(repair.WORKS)
    for work, item in metadata.items():
        composition = item["coverage_composition"]
        assert composition["manifest"] == repair.AUDIT + "/changes.json"
        assert "does not" in composition["qualification"]
        assert [(part["storage"], part["path"]) for part in composition["components"]] == [
            ("primary", repair.PRIMARY[work]), ("paratext", repair.RETAINED[work])]
        assert item["editions"][0]["servable"] is True
        assert item["editions"][1]["servable"] is False
    hipponax = metadata["hipponax.fragmenta"]
    assert "fragment 128" in hipponax["editions"][0]["name"]
    assert "not a complete edition" in hipponax["editions"][0]["note"]
    assert hipponax["coverage_composition"]["components"][1]["roles"] == {
        "critical-apparatus": 1, "editorial-commentary": 1,
        "external-testimonium": 1, "homeric-comparanda": 1}


def test_mixed_row_contexts_do_not_cross_excluded_speaker_labels(workspace):
    rows = read_jsonl(workspace / repair.PRIMARY["herodas.mimiambi"])
    mixed = next(row for row in rows if row["locus"] == "herodas_hk_0182.1")
    segments = repair.lexical_segments(mixed, workspace)
    assert len(segments) == 2
    assert "ΛΑΜΠΡΙΣΚΟΣ" not in " ".join(segments)
    assert " ".join(segments) == mixed["text"]
    for field, value in (("text", "changed"), ("edition", "unreviewed"),
                         ("analysis_text", "unexpected lexical override")):
        bad = deepcopy(mixed)
        bad[field] = value
        with pytest.raises(ValueError, match="postimage"):
            repair.lexical_segments(bad, workspace)


def test_historical_alias_view_preserves_previous_authority(workspace):
    from citation_alias_state import phoenix_alias_view
    _, before, _ = repair.verify(workspace)
    current = core_state(workspace)
    with phoenix_alias_view(workspace) as prior:
        assert (prior / repair.ALIASES).read_bytes() == before[repair.ALIASES].encode()
        assert (prior / repair.PRIMARY["herodas.mimiambi"]).read_bytes() == current[repair.PRIMARY["herodas.mimiambi"]]
    assert core_state(workspace) == current


def test_wrong_source_is_rejected_before_any_initial_apply_write(tmp_path, applied_template):
    _, before, _ = repair.verify(applied_template)
    for relative, text in before.items():
        if text is not None:
            path = tmp_path / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    wrong = tmp_path / "wrong.pdf"
    wrong.write_bytes(b"not the reviewed source")
    initial = core_state(tmp_path)
    with pytest.raises(ValueError, match="exact reviewed sources"):
        repair.run(tmp_path, "apply", source_pdf=wrong,
                   source_tei=applied_template / repair.AUDIT / "source-hipponax.xml")
    assert core_state(tmp_path) == initial
    assert not (tmp_path / repair.AUDIT).exists()


def test_real_pinned_tei_regenerates_exact_primary_and_retained_rows(tmp_path, applied_template, monkeypatch):
    """A normal selected ingest must reproduce the independently archived repair."""
    import build_corpus_loci as build
    import editorial_roles as roles
    source = tmp_path / roles.HIPPONAX_SOURCE["source_path"]
    source.parent.mkdir(parents=True)
    source.write_bytes((applied_template / repair.AUDIT / "source-hipponax.xml").read_bytes())
    data = tmp_path / "data"
    corpus = data / "corpus"
    corpus.mkdir(parents=True)
    expected = {}
    for relative in (roles.HIPPONAX_PARATEXT, repair.PRIMARY[roles.HIPPONAX_WORK], repair.ALIASES):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        expected[relative] = (applied_template / relative).read_bytes()
        path.write_bytes(expected[relative])
    monkeypatch.setattr(build, "REPO", tmp_path)
    monkeypatch.setattr(build, "SRC", tmp_path / "sources")
    monkeypatch.setattr(build, "DATA", data)
    monkeypatch.setattr(build, "CORPUS", corpus)
    monkeypatch.setattr(build, "NON_TEI_KEEP", data / "non_tei_authoritative.json")
    monkeypatch.setattr(build, "BEKKER_CONCORD", data / "bekker_concordance.json")
    monkeypatch.setattr(sys, "argv", ["build_corpus_loci.py", "--only", "tlg0233.tlg001"])
    build.main()
    assert {relative: (tmp_path / relative).read_bytes() for relative in expected} == expected
    metadata = json.loads((data / "corpus_editions.json").read_bytes())[roles.HIPPONAX_WORK]
    assert metadata["n_tokens"] == 25 and metadata["n_passages"] == 1
    diagnostics = json.loads((data / "corpus_loci_warnings.json").read_bytes())[roles.HIPPONAX_WORK]
    assert diagnostics["retained_editorial_sections"] == 4
    assert diagnostics["retained_editorial_tokens"] == 129
    assert diagnostics["retained_editorial_path"] == roles.HIPPONAX_PARATEXT
    assert diagnostics["extracted_source_chars"] == (
        diagnostics["primary_corpus_chars"] + diagnostics["retained_editorial_chars"])
    assert "dropped_chars" not in diagnostics
