"""A source-pinned Hipponax partition retains witnesses without lexical inflation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

from lxml import etree as ET
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_corpus_loci as build
import editorial_roles as roles


TEI = '''<TEI xmlns="http://www.tei-c.org/ns/1.0"><teiHeader>
<fileDesc><publicationStmt><availability><licence target="https://creativecommons.org/licenses/by-sa/4.0/">CC-BY-SA-4.0</licence></availability></publicationStmt></fileDesc>
</teiHeader><text><body><div type="edition" n="urn:cts:greekLit:tlg0233.tlg001.1st1K-grc1" xml:lang="grc">
<div type="textpart" subtype="section" n="frag128"><p><lb n="1"/>Μοῦσά μοι <lb n="2"/>τὴν πολτοχάρυβδιν</p></div>
<div type="textpart" subtype="section" n="similes"><head>HOMERI LOCI SIMILES</head><p>ἄνδρα μοι ἔννεπε</p></div>
<div type="textpart" subtype="section" n="testimonium"><head>TESTIMONIVM</head><p>Πολέμων δʼ ἱστορῶν</p></div>
<div type="textpart" subtype="section" n="variants"><head>VARIETAS LECTIONIS</head><p>πολτοχάρυβδιν Wachsmuth: ποντοχάρυβδιν Α, παντοχάρυβδιν Bergk</p></div>
<div type="textpart" subtype="section" n="commentary"><head>COMMENTARIVS</head><p>Corrige πολτοχάρυβδιν; ipsa vero Χάρυβδις</p></div>
</div></body></text></TEI>'''


def source_rows():
    output = []
    for parts, text, _, lines in build.iter_passages(ET.fromstring(TEI.encode())):
        row = {"urn": roles.HIPPONAX_WORK, "edition": roles.HIPPONAX_EDITION,
               "locus": ".".join(parts), "source": "first1k", "license": "CC-BY-SA-4.0",
               "text": text}
        if len(lines) > 1:
            row["text_lines"] = lines
        output.append(row)
    return output


def encoded(rows):
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()


def test_authorial_fragment_is_byte_identical_and_all_sections_are_accounted():
    original = source_rows()
    original[2]["additional_citation"] = {"reference": "Ath. XV 698b"}
    before = deepcopy(original)
    primary, retained = roles.partition_editorial_rows(roles.HIPPONAX_WORK, original)
    assert encoded(primary) == encoded(original[:1])
    assert len(primary) == 1 and len(retained) == 4
    assert primary[0]["text_lines"] == ["Μοῦσά μοι", "τὴν πολτοχάρυβδιν"]
    assert original == before
    for row, previous in zip(retained, original[1:]):
        assert all(row[key] == value for key, value in previous.items())
    assert retained[1]["additional_citation"] == {"reference": "Ath. XV 698b"}


def test_comparanda_testimony_variants_and_commentary_have_distinct_roles():
    _, retained = roles.partition_editorial_rows(roles.HIPPONAX_WORK, source_rows())
    assert [row["editorial_role"] for row in retained] == [
        "homeric-comparanda", "external-testimonium", "critical-apparatus", "editorial-commentary"]
    assert [row["lang"] for row in retained] == ["grc", "grc", "mul", "mul"]
    assert retained[0]["editorial_role_authority"]["source_citations"] == ["α 1", "υ 181", "Γ 417", "ρ 217", "Α 316"]
    assert retained[1]["editorial_role_authority"]["source_citations"] == ["Ath. XV 698b"]
    assert "πολτοχάρυβδιν Wachsmuth: ποντοχάρυβδιν Α, παντοχάρυβδιν Bergk" in retained[2]["text"]
    assert all(row["editorial_role_review"] == {"schema_version": 1,
        "authority": roles.ROLE_AUTHORITY, "work": roles.HIPPONAX_WORK} for row in retained)


@pytest.mark.parametrize("change", [
    lambda r: r.pop(),
    lambda r: r.append(deepcopy(r[0])),
    lambda r: r[0].update(locus="unreviewed"),
    lambda r: r[0].update(edition="another-edition"),
    lambda r: r[0].update(source="perseus"),
    lambda r: r[0].update(urn="homerus.ilyas"),
])
def test_partition_refuses_changed_section_set_or_manifestation(change):
    rows = source_rows()
    change(rows)
    with pytest.raises(ValueError):
        roles.partition_editorial_rows(roles.HIPPONAX_WORK, rows)


def test_other_works_keep_commentary_and_testimonium_without_changes():
    rows = source_rows()
    primary, retained = roles.partition_editorial_rows("different.work", rows)
    assert primary == rows and retained == []
    roles.validate_source("different.work", "different", "perseus", Path("does-not-exist.xml"))


def test_source_validation_requires_exact_reviewed_content(tmp_path, monkeypatch):
    path = tmp_path / "source.xml"
    path.write_text(TEI)
    monkeypatch.setitem(roles.HIPPONAX_SOURCE, "sha256", hashlib.sha256(path.read_bytes()).hexdigest())
    roles.validate_source(roles.HIPPONAX_WORK, roles.HIPPONAX_EDITION, "first1k", path)
    path.write_text(TEI.replace("Μοῦσά", "Μοῦσα"))
    with pytest.raises(ValueError, match="checksum changed"):
        roles.validate_source(roles.HIPPONAX_WORK, roles.HIPPONAX_EDITION, "first1k", path)
    with pytest.raises(ValueError, match="reviewed First1K"):
        roles.validate_source(roles.HIPPONAX_WORK, "another-edition", "first1k", path)


def test_retained_sidecar_is_reproducible_and_refuses_unrelated_replacement(tmp_path):
    _, retained = roles.partition_editorial_rows(roles.HIPPONAX_WORK, source_rows())
    build.write_editorial_paratext(tmp_path, roles.HIPPONAX_WORK, retained)
    path = tmp_path / roles.HIPPONAX_PARATEXT
    assert path.read_bytes() == encoded(retained)
    build.write_editorial_paratext(tmp_path, roles.HIPPONAX_WORK, retained)
    path.write_text("Unrelated retained records\n")
    with pytest.raises(ValueError, match="differs"):
        build.write_editorial_paratext(tmp_path, roles.HIPPONAX_WORK, retained)
    assert path.read_text() == "Unrelated retained records\n"


def test_only_generator_run_routes_four_sections_and_preserves_other_work_and_aliases(tmp_path, monkeypatch):
    source = tmp_path / "sources/first1k/data/tlg0233/tlg001/tlg0233.tlg001.1st1K-grc1.xml"
    source.parent.mkdir(parents=True)
    source.write_text(TEI)
    monkeypatch.setitem(roles.HIPPONAX_SOURCE, "sha256", hashlib.sha256(source.read_bytes()).hexdigest())
    data = tmp_path / "data"
    corpus = data / "corpus"
    corpus.mkdir(parents=True)
    untouched = corpus / "unrelated.work.jsonl"
    untouched.write_bytes(b'{"text":"preserved"}\n')
    aliases = data / "passage_aliases.json"
    aliases.write_bytes(b'{"aliases":{"existing":"retained"}}\n')
    (data / "corpus_editions.json").write_text(json.dumps({"unrelated.work": {
        "edition": "original", "source": "first1k", "n_tokens": 1, "n_passages": 1}}))
    monkeypatch.setattr(build, "REPO", tmp_path)
    monkeypatch.setattr(build, "SRC", tmp_path / "sources")
    monkeypatch.setattr(build, "DATA", data)
    monkeypatch.setattr(build, "CORPUS", corpus)
    monkeypatch.setattr(build, "NON_TEI_KEEP", data / "non_tei_authoritative.json")
    monkeypatch.setattr(build, "BEKKER_CONCORD", data / "bekker_concordance.json")
    monkeypatch.setattr(sys, "argv", ["build_corpus_loci.py", "--only", "tlg0233.tlg001"])
    build.main()
    original = source_rows()
    assert (corpus / (roles.HIPPONAX_WORK + ".jsonl")).read_bytes() == encoded(original[:1])
    paratext = data.parent / roles.HIPPONAX_PARATEXT
    retained = [json.loads(line) for line in paratext.read_text().splitlines()]
    assert [row["locus"] for row in retained] == ["similes", "testimonium", "variants", "commentary"]
    metadata = json.loads((data / "corpus_editions.json").read_text())
    assert metadata[roles.HIPPONAX_WORK]["n_passages"] == 1
    assert metadata[roles.HIPPONAX_WORK]["n_tokens"] == 4
    assert metadata["unrelated.work"]["edition"] == "original"
    diagnostics = json.loads((data / "corpus_loci_warnings.json").read_text())[roles.HIPPONAX_WORK]
    assert diagnostics["retained_editorial_sections"] == 4
    assert diagnostics["retained_editorial_tokens"] == 12
    assert diagnostics["extracted_source_chars"] == (
        diagnostics["primary_corpus_chars"] + diagnostics["retained_editorial_chars"])
    assert "dropped_chars" not in diagnostics
    assert untouched.read_bytes() == b'{"text":"preserved"}\n'
    assert aliases.read_bytes() == b'{"aliases":{"existing":"retained"}}\n'
