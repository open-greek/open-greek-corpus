import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import audit_photius_fresh as audit
from prepare_photius_coverage import build


def test_stop_does_not_hide_repetition_or_mark_loss():
    loop = audit.screen("ἢ " * 12 + "καὶ ὁ λόγος σαφής ἐστιν.", "stop")
    assert "identical-word-run" in loop["review_flags"]
    phrase = "ἔσφαγη ἢ ὡς ἄλλοι φασίν ἤφανίσθη ὁ δὲ δεύτερος\n"
    result = audit.screen(phrase * 5, "stop")
    assert "repeated-eight-word-phrase" in result["review_flags"]
    assert "repeated-output-line" in result["review_flags"]
    monotonic = audit.screen("ο λογος σαφης και καλος εστιν. " * 20)
    assert "frozen-polytonic-mark-loss-screen" in monotonic["review_flags"]
    assert audit.screen("ὁ λόγος", "length")["review_flags"][0] == "failed-or-length-terminated-outcome"


def test_editorial_notes_are_flagged_without_claiming_all_apparatus_is_detected():
    result = audit.screen("καὶ ὁ λόγος.\na. 35. καὶ τῶν AC· ὧν add A.\nb. 40. κεχρημένος om pr C.")
    assert "editorial-apparatus-candidate" in result["review_flags"]
    assert result["apparatus_candidates"] == {"editorial_term_occurrences": {"add": 1, "om": 1}, "numbered_note_lines": 2}
    assert "editorial-apparatus-candidate" not in audit.screen("ὁ λόγος σαφής ἐστιν.")["review_flags"]
    # Adding the separate apparatus screen must not change the pinned stop-loop authority.
    assert audit.sha(audit.encode(audit.REPETITION_POLICY)) == "5c6cdf1c4f971f5ed7e650ad7f1699e5e437e039e52ec38bfba2427a3ee00c94"


def fixture(tmp_path, model, text):
    manifest = build()
    page = manifest["pages"][0]
    meta = {"model": model, "revision": model * 40, "manifest_sha256": audit.sha(audit.encode(manifest)),
            "prompt": manifest["prompt"]}
    suffix = page.get("prompt_suffix", manifest["sources"][page["source"]].get("prompt_suffix", ""))
    row = {"id": page["id"], "source": page["source"], "scan_page": page["scan_page"],
           "region": page["region"], "image_sha256": "a" * 64,
           "prompt_sha256": audit.sha((manifest["prompt"] + (" " + suffix if suffix else "")).encode()),
           "raw_prediction": text, "finish_reason": "stop"}
    path = tmp_path / f"{model}.jsonl"
    path.write_bytes(b"\n".join(json.dumps(value, ensure_ascii=False).encode() for value in [{"_meta": meta}, row]) + b"\n")
    return path


def test_partial_snapshots_keep_all_outcomes_and_exact_record_hashes(tmp_path):
    paths = [fixture(tmp_path, "a", "ὁ λόγος σαφὴς καὶ καλός ἐστιν. " * 50),
             fixture(tmp_path, "b", "ἢ " * 12)]
    report = audit.audit(paths)
    assert report == audit.audit(list(reversed(paths)))
    assert report["outcome_count"] == 2 and report["selection_rule"] is None
    assert all(not r["all_regions_returned"] for r in report["raw_files"])
    assert all(r["expected_regions"] == 267 for r in report["raw_files"])
    assert all("different-output-length-between-checkpoints" in r["review_flags"] for r in report["outcomes"])
    assert report["outcomes"][0]["prediction_record_sha256"] == audit.sha(paths[0].read_bytes().splitlines()[1])
    assert all("/Users/" not in json.dumps(row) for row in report["raw_files"])
    with pytest.raises(ValueError, match="Repeated raw"):
        audit.audit([paths[0], paths[0]])
    rows = [json.loads(line) for line in paths[0].read_bytes().splitlines()]
    rows[1]["region"] = [0, 0, .5, 1]
    paths[0].write_bytes(b"\n".join(json.dumps(row).encode() for row in rows) + b"\n")
    with pytest.raises(ValueError, match="geometry"):
        audit.audit(paths)
