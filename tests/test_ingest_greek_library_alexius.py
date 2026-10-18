import gzip
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("alexius", ROOT / "scripts/ingest_greek_library_alexius.py")
alexius = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alexius)


def inputs():
    review = json.loads((ROOT / "data/ingest_reviews/greek-library-alexius.json").read_text())
    source = ROOT / "data/corpus_changes/alexius-ficker-1911/source.json.gz"
    if not source.exists():
        source = ROOT / "sources/greek_library/pilot/tlg9516.tlg002.local001.json.gz"
    return source, review


def test_every_changed_page_can_be_restored_to_the_source():
    source, review = inputs()
    raw, _ = alexius.generate(source, review, False)
    corrected, changes = alexius.generate(source, review)
    before = {r["locus"]: r["text"] for r in raw}
    restored = {r["locus"]: r["text"] for r in corrected}
    for change in changes:
        assert restored[change["locus"]] == change["corrected_text"]
        restored[change["locus"]] = change["original_text"]
    assert restored == before
    assert corrected[0]["text"].endswith("Ἐλυμήνατο")
    assert corrected[1]["text"].startswith("δὲ")
    assert "περιέρχεσθαι" in corrected[9]["text"]
    assert all("/" not in r["text"] for r in corrected)
    assert len(corrected) == 15


def test_different_source_is_refused(tmp_path):
    source, review = inputs()
    altered = tmp_path / "source.json.gz"
    altered.write_bytes(source.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Source changed"):
        alexius.generate(altered, review)
