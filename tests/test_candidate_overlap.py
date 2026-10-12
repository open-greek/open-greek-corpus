import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("overlap", Path(__file__).parents[1] / "scripts/audit_candidate_overlap.py")
overlap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlap)


def test_imported_candidate_does_not_match_itself(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    candidate = corpus / "new.work.jsonl"
    candidate.write_text(json.dumps({"urn": "new.work", "text": "λόγος θεός μέγας καλός"}) + "\n")
    other = corpus / "old.work.jsonl"
    other.write_text(json.dumps({"urn": "old.work", "text": "λογος θεος μεγας καλος"}) + "\n")
    result = overlap.audit(candidate, corpus, size=2)
    assert result["excluded_candidate_slugs"] == ["new.work"]
    assert result["screened_works"] == 1
    assert result["matches"][0]["work"] == "old.work"
    assert result["matches"][0]["matched_windows"] == 2
    assert result["corpus_sha256"]
