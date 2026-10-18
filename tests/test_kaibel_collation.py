"""A collated attestation counts once; an unresolved reading never wins a tie."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import collate_kaibel_witnesses as collation
from frequency_projection import FrequencyProjection
import build_work_lemma_counts as matrix
from build_public_corpus import public_lexicon_tokens


def leaf(texts):
    tokens, row_tokens = [], []
    for i, text in enumerate(texts):
        indexes = []
        for match in collation.TOKEN.finditer(text):
            indexes.append(len(tokens))
            tokens.append({"locus": str(i), "start": match.start(),
                "end": match.end(), "form": match[0]})
        row_tokens.append(indexes)
    return {"tokens": tokens, "row_tokens": row_tokens}


def test_paragraph_and_split_lines_align_without_counting_a_token_twice():
    a = leaf(["ὁ δὲ λόγος ἔχει ταῦτα πάντα καλῶς καὶ σαφῶς"])
    b = leaf(["ταῦτα πάντα καλῶς καὶ σαφῶς", "ὁ δὲ λόγος ἔχει"])
    pairs = collation.token_pairs(a, b)
    assert len(pairs) == 9
    assert len({x for x, y in pairs}) == len({y for x, y in pairs}) == 9


def test_unresolved_alternative_is_not_arbitrarily_matched():
    a = leaf(["ὁ δὲ λόγος ἔχει ταῦτα πάντα καλῶς καὶ σαφῶς"])
    b = leaf(["ὁ δὲ λόγος ἔχει ταῦτα πάντα καλῶς καὶ κακῶς"])
    pairs = collation.token_pairs(a, b)
    assert len(pairs) == 8
    assert all(a["tokens"][i]["form"] == b["tokens"][j]["form"] for i, j in pairs)


def test_repeated_formula_is_matched_only_to_distinct_occurrences():
    a = leaf(["ὁ δὲ λόγος ἔχει", "ὁ δὲ λόγος ἔχει"])
    b = leaf(["ὁ δὲ λόγος ἔχει"])
    assert len(collation.token_pairs(a, b)) == 4


def projection_fixture(tmp_path):
    data = tmp_path / "data"
    (data / "corpus").mkdir(parents=True)
    rec = {"urn": "w", "locus": "1", "text": "λόγος κακῶς λόγος"}
    path = data / "corpus/w.jsonl"
    path.write_text(json.dumps(rec, ensure_ascii=False) + "\n")
    (data / "frequency_projection.json").write_text(json.dumps({
        "source_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()},
        "rows": {"w:1": [[0, 5]]}}))
    return data, path, rec


def test_both_form_and_work_frequency_use_exactly_one_agreed_occurrence(tmp_path):
    data, path, rec = projection_fixture(tmp_path)
    projection = FrequencyProjection(data)
    assert Counter(public_lexicon_tokens(projection.text(rec))) == {"λόγος": 1}
    assert matrix.tokenize_file(path, projection) == {"w": {"λόγος": 1}}


def test_changed_source_cannot_silently_reuse_a_frequency_projection(tmp_path):
    data, path, rec = projection_fixture(tmp_path)
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="stale"):
        FrequencyProjection(data)


def test_single_witness_material_counts_normally(tmp_path):
    projection = FrequencyProjection(tmp_path)
    assert projection.text({"urn": "unique", "locus": "1", "text": "μοναδικὸς λόγος"}) == "μοναδικὸς λόγος"


def test_committed_concordance_reproduces_and_keeps_every_source_reading():
    generated = collation.generate()
    for name, raw in generated.items():
        assert (ROOT / name).read_bytes() == raw
    record = json.loads(generated[collation.CONCORDANCE])
    pages, hashes = collation.read_pages(ROOT)
    represented = set(record["single_witness_pages"])
    for group in record["alternatives"]:
        represented.update(group["pages"])
        for page, reading in group["readings"].items():
            assert reading["rows"] == [{"locus": r["locus"], "text": r["text"]}
                for r in pages[page]["rows"]]
    assert represented == set(pages)
    assert record["source_sha256"] == hashes


def test_unresolved_bounds_are_explicit_and_do_not_pick_one_reading():
    doc = json.loads((ROOT / collation.CONCORDANCE).read_text())
    assert doc["summary"]["unresolved_source_token_occurrences"] > 0
    for group in doc["alternatives"]:
        upper = Counter(t["form"] for reading in group["readings"].values()
            for t in reading["unresolved_tokens"])
        assert group["unresolved_frequency_bounds"] == {
            form: {"lower": 0, "upper": n} for form, n in sorted(upper.items())}


def test_unapply_restores_unprojected_counts_without_changing_any_reader_text(tmp_path, monkeypatch):
    for name in [collation.OUTPUT, collation.CONCORDANCE, collation.AUDIT]:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    hashes = json.loads((ROOT / collation.OUTPUT).read_text())["source_sha256"]
    for name in hashes:
        destination = tmp_path / "data/corpus" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "data/corpus" / name, destination)
    monkeypatch.setattr(collation, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["collate_kaibel_witnesses.py", "--unapply"])
    collation.main()
    assert not (tmp_path / collation.OUTPUT).exists()
    for name, expected in hashes.items():
        assert hashlib.sha256((tmp_path / "data/corpus" / name).read_bytes()).hexdigest() == expected
