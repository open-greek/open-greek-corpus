from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_photius_retries import build_retry, encode


def test_checkpoint_specific_retries_pin_complete_source_body_in_order():
    for number, cut in ((47, .458), (50, .456)):
        result = build_retry(number)
        assert result["retry_of"]["page_id"] == f"photius-bekker-{number:04d}"
        assert result["retry_of"]["sha256"] == "92bb67209eaa7dcca53800c499c68b4c1a085cbb2d62f2909b27da99c0acdcd6"
        assert result["checkpoints"] == [{"model": "Qwen/Qwen3.8-27B-FP8", "revision": "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"}]
        assert [p["reading_order"] for p in result["pages"]] == list(range(4))
        assert all(p["scan_page"] == number for p in result["pages"])
        assert result["pages"][0]["region"][3] == result["pages"][1]["region"][1] == cut
        assert result["pages"][2]["region"][3] == result["pages"][3]["region"][1] == cut
        assert not result["review"]["accepted_for_primary_ingest"]
        assert encode(result) == (ROOT / f"data/ocr_requests/photius-bekker-page{number:04d}-retry.json").read_bytes()
