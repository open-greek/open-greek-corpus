"""The continued review preserves source variants, frozen receipts, and undo."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import dubner_current_state as current
import dubner_evidence_observations as observations
import review_dubner_evidence as repair
from citation_alias_state import _overlay
from ocr_consensus import merge_witnesses


@pytest.fixture(scope="module")
def networks():
    return json.loads(gzip.decompress((ROOT/repair.previous.NETWORKS).read_bytes()))


@pytest.mark.parametrize("key",observations.LAYOUTS)
def test_reviewed_cells_preserve_every_original_character_without_extra_votes(networks,key):
    original = next(w for w in networks[key]["ocr_consensus"]["witnesses"]
        if w["vote_group"].endswith("harvard"))
    projected,record = repair.route_columns(original,key,recorded_at="test")
    assert original == record["original_witness"]
    assert "".join(p["text"] for p in record["parts"]) == original["text"]
    full = {tuple(reference) for reference in record["complete_cells"]}
    duplicate = {(p["line"],p["cell"]) for p in record["duplicate_fragments"]}
    content = {(p["line"],p["cell"]) for p in record["parts"]
        if p["cell"] not in {"delimiter","line-ending"} and p["text"].strip()}
    assert not full & duplicate and full | duplicate == content
    assert len(duplicate) == len(observations.LAYOUTS[key]["duplicate_lines"])
    assert projected["vote_group"] == original["vote_group"]
    assert projected["id"] == original["id"]
    assert projected["source_artifact_sha256"] == original["artifact_sha256"]


def test_a_new_nonblank_column_cell_cannot_be_silently_dropped(networks):
    w = deepcopy(next(w for w in networks["aves:0271"]["ocr_consensus"]["witnesses"]
        if w["vote_group"].endswith("harvard")))
    lines = w["text"].splitlines()
    assert not lines[10].split("|")[1].strip()
    lines[10] += " νέον"
    w["text"] = "\n".join(lines)
    with pytest.raises(ValueError,match="unreviewed duplicate-column cell"):
        repair.route_columns(w,"aves:0271",recorded_at="test")


def test_index_linked_novel_reading_preserves_every_original_vote_and_variant(networks):
    key = "aves:0271"
    witnesses = []
    for w in networks[key]["ocr_consensus"]["witnesses"]:
        witnesses.append(repair.route_columns(w,key,recorded_at="test")[0]
            if w["vote_group"].endswith("harvard") else w)
    result = merge_witnesses(witnesses)
    decision = next(d for d in observations.READINGS if d[:2] == (key,453))
    before = deepcopy(result["ocr_consensus"]["slots"][453])
    record = repair.adjudicate(result,decision,recorded_at="test")
    repair.render(result)
    slot = result["ocr_consensus"]["slots"][453]
    assert record["original_slot"] == before
    assert slot["readings"] == before["readings"]
    assert slot["tied_readings"] == before["tied_readings"]
    assert slot["vote_status"] == "unresolved" and slot["status"] == "source-reviewed"
    assert slot["selected"] == "Φορβειά" and slot["lexical_eligible"]
    assert "toronto-0767-index" in record["source_captures"]
    assert "Φορβειά" in result["analysis_text"].split()
    assert {w["vote_group"] for w in result["ocr_consensus"]["witnesses"]} == {
        "dubner-1855-toronto","dubner-1855-harvard"}
    with pytest.raises(ValueError,match="source occurrence changed"):
        repair.adjudicate(result,decision,recorded_at="test")


def test_kappa_chi_candidates_include_valid_alternatives_and_choose_nothing():
    witnesses = [{"id":name,"vote_group":name,"text":text,"artifact_sha256":repair.sha(text.encode())}
        for name,text in (("one","οὐκ μακρόν"),("two","οὐχ μαχρόν"))]
    result = merge_witnesses(witnesses)
    before = deepcopy(result)
    report = repair.kappa_chi_inventory({"fixture:1":result})
    assert report["slots"] == 2
    assert {tuple(r["readings"]) for r in report["candidates"]} == {("οὐκ","οὐχ"),("μακρόν","μαχρόν")}
    assert before == result and result["analysis_text"] == ""


@pytest.fixture
def isolated(tmp_path):
    audit = json.loads((ROOT/repair.AUTHORITY).read_bytes())
    image = audit["source_sha256"]
    image = next(name for name in image if name.endswith(".png"))
    names = [*audit["outputs"],repair.AUTHORITY,repair.BEFORE,image]
    _overlay(ROOT,tmp_path,{Path(name).parts:(ROOT/name).read_bytes() for name in names})
    return tmp_path,audit,image


def test_invalidated_source_changes_signature_but_does_not_prevent_exact_undo(isolated):
    root,audit,image = isolated
    original = (root/image).read_bytes()
    initial = repair.signature(root)
    (root/image).write_bytes(original+b"invalidated")
    assert repair.signature(root) != initial
    with pytest.raises(ValueError,match="captured evidence changed"):
        repair.verify(root)
    before = repair.archived_inputs(root)
    repair.undo(root)
    assert not repair.active(root)
    for name,raw in before.items():
        assert ((root/name).read_bytes() if (root/name).is_file() else None) == raw
    with pytest.raises(ValueError,match="captured evidence changed"):
        repair.apply(root)
    (root/image).write_bytes(original)
    result = repair.apply(root)
    assert result == audit
    assert (root/repair.AUTHORITY).read_bytes() == (ROOT/repair.AUTHORITY).read_bytes()


def test_undo_refuses_a_later_primary_edit_without_touching_other_outputs(isolated):
    root,audit,_ = isolated
    primary = next(name for name in audit["outputs"] if name.startswith("data/corpus/"))
    (root/primary).write_bytes((root/primary).read_bytes()+b"later edit\n")
    network = (root/repair.NETWORKS).read_bytes()
    with pytest.raises(ValueError,match="Refusing to overwrite"):
        repair.undo(root)
    assert (root/repair.NETWORKS).read_bytes() == network


def test_rehashing_a_forged_projection_does_not_bypass_source_replay(isolated):
    root,audit,_ = isolated
    primary = next(name for name in audit["outputs"] if "scholia-in-equites-" in name)
    rows = [json.loads(line) for line in (root/primary).read_bytes().splitlines()]
    row = next(r for r in rows if "dubner_evidence_review" in r)
    row["analysis_text"] += " πλαστόν"
    forged = repair.jsonl(rows)
    (root/primary).write_bytes(forged)
    audit["outputs"][primary] = repair.sha(forged)
    (root/repair.AUTHORITY).write_bytes(repair.encoded(audit))
    with pytest.raises(ValueError,match="source replay differs"):
        repair.verify(root)


def test_current_projection_rejects_removed_audit_markers(monkeypatch):
    row = {"urn":"work","locus":"page","analysis_text":"λόγος","dubner_evidence_review":{}}
    monkeypatch.setattr(repair,"active",lambda root:True)
    monkeypatch.setattr(repair,"_state",lambda root:({}, {}, {("work","page"):row}))
    assert current.validate_projection(row,"fixture") == "λόγος"
    forged = {k:v for k,v in row.items() if k != "dubner_evidence_review"}
    with pytest.raises(ValueError,match="differs from checked admission"):
        current.validate_projection(forged,"fixture")


def test_published_accounting_distinguishes_layout_from_printed_reading_review():
    audit = json.loads((ROOT/repair.AUTHORITY).read_bytes())
    counts = audit["counts"]
    assert counts["retained_duplicate_fragments"] == 144
    assert counts["new_source_reviewed_slots"] == len(observations.READINGS) == 49
    assert counts["source_reviewed_slots"] == counts["reading_statuses"]["source-reviewed"]
    assert counts["layout_only_reading_statuses"]["unresolved"] == 72135
    assert counts["reading_statuses"]["unresolved"] == 72086
    assert counts["unresolved_reduction"] == 304
    assert counts["analysis_tokens"] == 199482
    assert counts["held_layout_pages"] == 0


def test_activity_probe_reads_preimages_once_per_output_state(tmp_path,monkeypatch):
    primary = "data/corpus/fixture.jsonl"
    for name,raw in ((repair.AUTHORITY,repair.encoded({"outputs":{primary:"unused"}})),
                     (repair.BEFORE,b"archive"),(primary,b"current")):
        path = tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    calls = []
    def before(root):
        calls.append(root)
        return {primary:b"original"}
    monkeypatch.setattr(repair,"archived_inputs",before)
    repair._active.cache_clear()
    assert repair.active(tmp_path) and repair.active(tmp_path)
    assert len(calls) == 1
    (tmp_path/primary).write_bytes(b"original")
    assert not repair.active(tmp_path) and len(calls) == 2


def test_metadata_cannot_mutate_the_checked_accounting(monkeypatch):
    slug = next(iter(repair.previous.base.work_definitions().values()))["slug"]
    counts = {"counts":{"unresolved":1},"primary_rows":1,"analysis_tokens":2}
    monkeypatch.setattr(repair,"active",lambda root:True)
    monkeypatch.setattr(repair,"_state",lambda root:({"works":{slug:counts}}, {}, {}))
    monkeypatch.setattr(current,"_scope",lambda root:({"sources":[]}, {}, {}))
    result = current.metadata(ROOT)
    result[slug]["counts"]["unresolved"] = 0
    assert counts["counts"]["unresolved"] == 1


def test_alias_adapter_still_requires_the_retired_whole_volume_identity(tmp_path,monkeypatch):
    base = repair.previous.base
    for name,value in ((base.FRAGMENT,{}),("data/work_ids.json",{
            "works":{"ogc002861":{"slug":base.B,"status":"served"}}})):
        path = tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(repair.encoded(value))
    monkeypatch.setattr(repair,"active",lambda root:True)
    monkeypatch.setattr(current,"_scope",lambda root:({}, {}, {}))
    with pytest.raises(ValueError,match="retired Platonius identity"):
        current.alias_fragment(tmp_path)
