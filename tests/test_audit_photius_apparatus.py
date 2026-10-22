import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_photius_apparatus as audit
import repair_photius_index as index


@pytest.fixture(scope='module')
def historical_root():
    from photius_current_state import predecessor_view
    with predecessor_view(ROOT) as previous:
        yield previous


def test_confirmed_lower_bound_is_distinct_from_heuristic_candidates(historical_root):
    report = audit.build(historical_root)
    assert report["historical_rows"] == 3846
    assert report["historical_pages"] == 236
    assert report["preserved_index_rows_outside_scope"] == 501
    assert report["confirmed_apparatus"]["rows"] == 10
    assert report["confirmed_apparatus"]["text_characters"] == 505
    assert report["candidate_screen"]["rows"] == 189
    assert report["candidate_screen"]["pages"] == 96
    assert report["changes_made"] == []
    assert "not a measured apparatus total" in report["candidate_screen"]["qualification"]


def test_new_edition_rows_do_not_change_historical_audit_but_changed_old_rows_fail(tmp_path):
    corpus = tmp_path / index.CORPUS
    corpus.parent.mkdir(parents=True)
    corpus.write_bytes(index.input_bytes(ROOT))
    archive = tmp_path / index.ARCHIVE / "before.jsonl.gz"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(gzip.compress(index.input_bytes(ROOT), mtime=0))
    before = audit.build(tmp_path)
    with corpus.open("a") as stream:
        stream.write(json.dumps({"locus": "photius_bekker1824_0013.1", "text": "νέον"}) + "\n")
    assert audit.build(tmp_path) == before
    rows = [json.loads(line) for line in corpus.read_text().splitlines()]
    next(r for r in rows if r["locus"].endswith("_0069.40"))["text"] += "νέον"
    corpus.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    with pytest.raises(ValueError, match="historical body changed"):
        audit.build(tmp_path)


def test_optional_scan_verification_rejects_an_unpinned_pdf(tmp_path, historical_root):
    path = tmp_path / "source.pdf"
    path.write_bytes(b"another scan")
    with pytest.raises(ValueError, match="Unexpected source scan"):
        audit.build(historical_root, source_scan=path)
