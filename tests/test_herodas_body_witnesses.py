"""Historical witnesses remain exact, separate, deterministic, and qualified."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import herodas_body_witnesses as witnesses


def runs(tmp_path, pages=(76, 78)):
    roots = {}
    for kind, spec in witnesses.RUNS.items():
        root = tmp_path / kind
        root.mkdir()
        roots[kind] = root
        (root / "_timing.json").write_text(json.dumps({
            "model": spec["model"], "pages": 542, "seconds": 10.5,
            "gpu": "personal-machine", "work_directory": "/private/personal-path",
            "private_repository": "private/project", "command": "unrecorded command"}))
        (root / "manifest.jsonl").write_text("".join(json.dumps({
            "page": f"herodas_hk_{page:04}", "chars": 12, "greek_chars": 8,
            "private_path": "/private/personal-path"}) + "\n" for page in pages))
        for page in pages:
            (root / f"herodas_hk_{page:04}.md").write_bytes(f"# ΜΗΤΡΙΧΗ\r\n<tab/>λέξις {kind}\n".encode())
            (root / f"herodas_hk_{page:04}.grc.txt").write_text("ἡμέων\n" if kind == "legacy" else "ἡμῶν\n")
    return roots


def test_selected_raw_files_and_disagreement_are_retained_exactly(tmp_path):
    roots = runs(tmp_path)
    packet = witnesses.build_packet(roots["legacy"], roots["qwen36"], [78, 76])
    assert packet["selected_pages"] == [76, 78]
    assert set(packet["pages"]) == {"76", "78"}
    for page in (76, 78):
        for kind, root in roots.items():
            record = packet["pages"][str(page)][kind]
            assert record["id"].endswith(f"-p{page:04}")
            for label, suffix in (("md", ".md"), ("grc", ".grc.txt")):
                raw = (root / f"herodas_hk_{page:04}{suffix}").read_bytes()
                assert record["files"][label]["text"].encode() == raw
                assert record["files"][label]["sha256"] == witnesses.sha(raw)
    assert packet["pages"]["76"]["legacy"]["files"]["grc"]["text"] == "ἡμέων\n"
    assert packet["pages"]["76"]["qwen36"]["files"]["grc"]["text"] == "ἡμῶν\n"


def test_legacy_is_diagnostic_and_unknown_execution_details_are_not_invented(tmp_path):
    roots = runs(tmp_path)
    packet = witnesses.build_packet(roots["legacy"], roots["qwen36"], [76])
    assert packet["runs"]["legacy"]["counted_vote"] is False
    assert packet["runs"]["legacy"]["role"] == "diagnostic-only"
    assert packet["runs"]["qwen36"]["counted_vote"] is True
    for run in packet["runs"].values():
        assert run["model_revision"] is None and run["historical_prompt_sha256"] is None
        assert run["serving_revision"] is None
        assert "not body coverage" in run["provenance_qualification"]


def test_metadata_keeps_input_checksums_without_paths_hosts_commands_or_private_names(tmp_path):
    roots = runs(tmp_path)
    packet = witnesses.build_packet(roots["legacy"], roots["qwen36"], [76])
    raw = witnesses.encoded(packet)
    assert b"personal-path" not in raw and b"personal-machine" not in raw
    assert b"private/project" not in raw and str(tmp_path).encode() not in raw
    assert b"unrecorded command" not in raw
    for kind, root in roots.items():
        assert packet["runs"][kind]["metadata"]["_timing.json"]["raw_sha256"] == witnesses.sha((root / "_timing.json").read_bytes())


def test_archive_is_byte_reproducible_and_self_contained(tmp_path):
    roots = runs(tmp_path)
    packet = witnesses.build_packet(roots["legacy"], roots["qwen36"], [76])
    assert witnesses.compressed(packet) == witnesses.compressed(deepcopy(packet))
    out = tmp_path / "archive.json.gz"
    receipt = witnesses.write_packet(packet, out)
    assert receipt["sha256"] == witnesses.sha(out.read_bytes())
    assert receipt["json_sha256"] == witnesses.sha(gzip.decompress(out.read_bytes()))
    assert witnesses.load_packet(out) == packet
    assert witnesses.write_packet(packet, out) == receipt
    packet["pages"]["76"]["qwen36"]["files"]["grc"]["text"] = "changed"
    with pytest.raises(ValueError, match="transcription"):
        witnesses.write_packet(packet, out)
    assert witnesses.load_packet(out)["pages"]["76"]["qwen36"]["files"]["grc"]["text"] == "ἡμῶν\n"


@pytest.mark.parametrize("pages", [[], [0], [543], [True], [76, 76], ["76"]])
def test_page_selection_cannot_silently_expand_or_repeat(pages):
    with pytest.raises(ValueError):
        witnesses.selected_pages(pages)


def test_default_pages_use_the_reviewed_source_inventory():
    from herodas_body_source_observations import BODY_PAGES
    assert witnesses.selected_pages() == [page["scan_page"] for page in BODY_PAGES]


def test_manifest_preserves_truncated_retry_history_without_counting_extra_votes(tmp_path):
    roots = runs(tmp_path, pages=(444,))
    manifest = roots["qwen36"] / "manifest.jsonl"
    manifest.write_text(json.dumps({"page": "herodas_hk_0444", "chars": 13542,
        "greek_chars": 4886, "truncated": True}) + "\n" + json.dumps({
        "page": "herodas_hk_0444", "chars": 912, "greek_chars": 498,
        "truncated": True, "tiled": True}) + "\n")
    packet = witnesses.build_packet(roots["legacy"], roots["qwen36"], [444])
    entries = packet["runs"]["qwen36"]["metadata"]["manifest.jsonl"]["selected_entries"]
    assert [entry["chars"] for entry in entries] == [13542, 912]
    assert all(entry["truncated"] for entry in entries)
    assert entries[-1]["tiled"] is True
    assert len(packet["pages"]["444"]) == 2
    assert packet["runs"]["legacy"]["counted_vote"] is False
    witnesses.validate_packet(packet)


def test_missing_page_file_and_manifest_entry_fail_instead_of_zero_coverage(tmp_path):
    roots = runs(tmp_path)
    (roots["qwen36"] / "herodas_hk_0076.md").unlink()
    with pytest.raises(FileNotFoundError):
        witnesses.build_packet(roots["legacy"], roots["qwen36"], [76])
    with pytest.raises(ValueError, match="every selected page"):
        witnesses.build_packet(roots["legacy"], roots["qwen36"], [80])


def test_model_mismatch_and_repeated_run_directory_fail(tmp_path):
    roots = runs(tmp_path)
    with pytest.raises(ValueError, match="distinct run"):
        witnesses.build_packet(roots["legacy"], roots["legacy"], [76])
    path = roots["qwen36"] / "_timing.json"
    metadata = json.loads(path.read_text())
    metadata["model"] = "unreviewed/model"
    path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="different recognizer"):
        witnesses.build_packet(roots["legacy"], roots["qwen36"], [76])


@pytest.mark.parametrize("mutation", ["page", "source", "vote", "revision", "fact", "metadata-extra", "top-extra"])
def test_loaded_packet_cannot_change_qualification_or_page_authority(tmp_path, mutation):
    roots = runs(tmp_path)
    packet = witnesses.build_packet(roots["legacy"], roots["qwen36"], [76])
    if mutation == "page":
        packet["pages"]["76"]["qwen36"]["pdf_page"] = 78
    elif mutation == "source":
        packet["source"]["sha256"] = "0" * 64
    elif mutation == "vote":
        packet["runs"]["legacy"]["counted_vote"] = True
    elif mutation == "revision":
        packet["runs"]["qwen36"]["model_revision"] = "invented"
    elif mutation == "fact":
        packet["runs"]["qwen36"]["metadata"]["_timing.json"]["facts"]["private_path"] = "/private/path"
    elif mutation == "metadata-extra":
        packet["runs"]["qwen36"]["metadata"]["_timing.json"]["raw_log"] = "private log"
    else:
        packet["raw_log"] = "private log"
    with pytest.raises(ValueError):
        witnesses.validate_packet(packet)


def test_inputs_are_rechecked_after_reading_to_reject_midbuild_drift(tmp_path, monkeypatch):
    roots = runs(tmp_path)
    target = roots["qwen36"] / "herodas_hk_0076.grc.txt"
    original = Path.read_bytes
    count = 0

    def changing_read(path):
        nonlocal count
        if path == target:
            count += 1
            if count == 2:
                return b"changed after the archived read"
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", changing_read)
    with pytest.raises(ValueError, match="changed during"):
        witnesses.build_packet(roots["legacy"], roots["qwen36"], [76])
