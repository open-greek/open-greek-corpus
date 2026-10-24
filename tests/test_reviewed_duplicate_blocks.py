"""Source-backed block collation preserves partial readings and literal undo."""
import gzip
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import repair_reviewed_duplicate_blocks as repair
from ocr_consensus import compact_corpus_consensus, restore_corpus_consensus, tokenize


@pytest.fixture(scope="module")
def frozen():
    before = repair.archived_inputs(ROOT)
    outputs, summaries, counts = repair.build(ROOT, before, recorded_at="2026-10-24T00:00:00+00:00")
    return {"before": before, "outputs": outputs, "groups": summaries, "counts": counts,
        "networks": json.loads(gzip.decompress(outputs[repair.NETWORKS])),
        "records": [json.loads(line) for line in gzip.decompress(outputs[repair.RECORDS]).splitlines()]}


def rows(raw):
    return list(map(json.loads, raw.splitlines()))


def staged_root(destination, frozen):
    for name in repair.INPUTS:
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(frozen["before"][name])
    capture = json.loads((ROOT / repair.AUDIT / "source-evidence.json").read_bytes())
    for name in [repair.AUDIT + "/source-evidence.json", *(item["path"] for item in capture["files"]),
                 *("scripts/" + name for name in repair.recipe_pins())]:
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    return destination


def test_every_literal_row_survives_and_unrelated_bytes_stay_unchanged(frozen):
    originals = {(row["urn"], row["locus"]): row
                 for record in frozen["records"] for row in record["original_rows"]}
    literal = {(row["urn"], row["locus"]): row
               for name, raw in frozen["outputs"].items() if name.startswith("data/corpus_secondary/")
               for row in rows(raw)}
    assert len(originals) == len(literal) == frozen["counts"]["original_rows"] == 119
    for identity, original in originals.items():
        assert {key: literal[identity][key] for key in original} == original
    for name in repair.PRIMARY:
        before = {json.loads(raw)["locus"]: raw for raw in frozen["before"][name].splitlines(keepends=True)}
        after = {json.loads(raw)["locus"]: raw for raw in frozen["outputs"][name].splitlines(keepends=True)}
        for locus in before.keys() & after.keys():
            assert before[locus] == after[locus]


def test_canonical_rows_preserve_the_upstream_source_and_license(frozen):
    for name, source, license_value in (
        (repair.PRIMARY[0], "cgpg", "CC-BY-4.0"), (repair.PRIMARY[1], "ocr", "PD")):
        canonical = [row for row in rows(frozen["outputs"][name]) if row.get("edition") == repair.EDITION]
        assert canonical
        assert all(row["source"] == source and row["license"] == license_value for row in canonical)


def test_one_occurrence_in_source_order_retains_all_35_additional_lines(frozen):
    name = f"data/corpus/{repair.HESYCHIUS}.jsonl"
    output = rows(frozen["outputs"][name])
    index = next(i for i, row in enumerate(output) if row["locus"] == "reviewed-duplicate.hesychius.0150")
    assert output[index - 1]["locus"] == "hesychius_masked_0142.55"
    assert output[index + 1]["locus"] == "hesychius_masked_0145.1"
    original = frozen["records"][-1]["original_rows"]
    tail = [row for row in original if row["locus"].startswith("hesychius_masked_0150.")
            and int(row["locus"].rsplit(".", 1)[1]) >= 39]
    assert len(tail) == 35
    # Every original token remains an explicit reading in the aligned network,
    # including one-sided text after the shorter witness's actual coverage.
    network = frozen["networks"]["hesychius:0143-0150"]["ocr_consensus"]
    available = [reading["text"] for slot in network["slots"] for reading in slot["readings"]]
    from collections import Counter
    required = Counter(token[0] for token in tokenize("\n".join(row["text"] for row in tail)))
    assert not required - Counter(available)
    for slot in network["slots"][-30:]:
        assert slot["selected"] is not None


def test_repeated_extractions_share_one_vote_and_ties_never_enter_scalars(frozen):
    unresolved = 0
    for result in frozen["networks"].values():
        network = result["ocr_consensus"]
        assert len({w["vote_group"] for w in network["witnesses"]}) == 1
        assert network["counts"].get("agreement", 0) == 0
        for slot in network["slots"]:
            if slot["status"] == "unresolved":
                unresolved += 1
                assert slot["selected"] is None and not slot["lexical_eligible"]
            assert all(len(reading["support_groups"]) == 1 for reading in slot["readings"])
        assert result["analysis_text"] == " ".join(slot["selected"] for slot in network["slots"] if slot["lexical_eligible"])
        compact = compact_corpus_consensus(result, {"path": repair.NETWORKS, "key": "test"})
        assert restore_corpus_consensus(compact, result) == result
    assert unresolved == 149


def test_apply_verify_alias_projection_and_exact_undo_reapply(tmp_path, frozen):
    root = staged_root(tmp_path, frozen)
    audit = repair.apply(root, recorded_at="2026-10-24T00:00:00+00:00")
    assert repair.active(root)
    assert repair.verify(root)[0] == audit
    fragment = repair.alias_fragment(root)
    assert sum(len(value) for value in fragment["aliases"].values()) == 119
    for name in repair.PRIMARY:
        assert repair.historical_bytes(root, name) == frozen["before"][name]
    assert repair.historical_bytes(root, "data/corpus/not-owned.jsonl") is None
    row = next(row for row in rows((root / repair.PRIMARY[0]).read_bytes()) if row.get("edition") == repair.EDITION)
    assert repair.validate_projection(row, root) == row["analysis_text"]
    stripped = dict(row)
    stripped.pop("reviewed_duplicate_block")
    with pytest.raises(ValueError, match="projection"):
        repair.validate_projection(stripped, root)
    frozen_outputs = {name: (root / name).read_bytes() for name in audit["outputs"]}
    repair.undo(root)
    assert not repair.active(root)
    repair.verify(root, active_only=False)
    assert all((root / name).read_bytes() == frozen["before"][name] for name in repair.PRIMARY)
    assert repair.apply(root) == audit
    assert all((root / name).read_bytes() == raw for name, raw in frozen_outputs.items())


def test_changed_source_invalidates_projection_but_still_allows_literal_undo(tmp_path, frozen):
    root = staged_root(tmp_path, frozen)
    repair.apply(root, recorded_at="2026-10-24T00:00:00+00:00")
    row = next(row for row in rows((root / repair.PRIMARY[0]).read_bytes()) if row.get("edition") == repair.EDITION)
    assert repair.validate_projection(row, root)
    capture = json.loads((root / repair.AUDIT / "source-evidence.json").read_bytes())
    path = root / capture["files"][-1]["path"]
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="evidence"):
        repair.validate_projection(row, root)
    repair.undo(root)
    assert all((root / name).read_bytes() == frozen["before"][name] for name in repair.PRIMARY)


def test_later_edits_are_not_overwritten_by_undo(tmp_path, frozen):
    root = staged_root(tmp_path, frozen)
    repair.apply(root, recorded_at="2026-10-24T00:00:00+00:00")
    path = root / repair.PRIMARY[0]
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="later duplicate output"):
        repair.undo(root)


def test_changed_recipe_invalidates_a_previously_cached_projection(tmp_path, frozen):
    root = staged_root(tmp_path, frozen)
    repair.apply(root, recorded_at="2026-10-24T00:00:00+00:00")
    row = next(row for row in rows((root / repair.PRIMARY[0]).read_bytes()) if row.get("edition") == repair.EDITION)
    assert repair.validate_projection(row, root)
    path = root / "scripts/reviewed_duplicate_block_observations.py"
    path.write_bytes(path.read_bytes() + b"\n# changed\n")
    with pytest.raises(ValueError, match="recipe file"):
        repair.validate_projection(row, root)
    repair.undo(root)


def test_jointly_edited_primary_and_output_hash_cannot_create_a_new_projection(tmp_path, frozen):
    root = staged_root(tmp_path, frozen)
    repair.apply(root, recorded_at="2026-10-24T00:00:00+00:00")
    name = repair.PRIMARY[0]
    values = rows((root / name).read_bytes())
    row = next(row for row in values if row.get("edition") == repair.EDITION)
    row["analysis_text"] += " ἀνεπιβεβαίωτον"
    raw = repair.jsonl(values)
    (root / name).write_bytes(raw)
    path = root / repair.AUDIT / "changes.json"
    audit = json.loads(path.read_bytes())
    audit["outputs"][name] = repair.sha(raw)
    path.write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError, match="literal replay"):
        repair.validate_projection(row, root)
