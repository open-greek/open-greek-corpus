"""The apply/unapply round trip for scripts/repair_nonfinal_graves.py.

The audit stores each edit as an offset into the ORIGINAL row text plus the form
that sat there, which is small and reverses cleanly, but only if unapply walks a
row's edits FORWARD. Walking them backward puts every edit after the first at
the wrong offset the moment a repair is not the same length as what it replaced.

That never bit while the tranches were accent-only, because a grave and an acute
compose to one character either way. It bit immediately on the mark-moving
tranche, where seven forms are a vowel carrying two accents at once (ὲ́χει) that
composes one character shorter. Real case, hippolytus 6.15.1: ὲ́χει at offset 192
and αὶσθήσεις at 208 in one row, and unapply wrote the second one a character
late and then refused its own byte-for-byte check.

The forms here are read from the applied audit rather than pasted. The tranche
that proposed them is regenerated from the corpus and drains to zero rows the
moment the repair lands, so it is not a source a test can hold on to; the audit
is the permanent record of what was actually applied.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import repair_nonfinal_graves as rep  # noqa: E402

AUDIT = (REPO / "data" / "corpus_changes"
         / "nonfinal_grave_tranche_marks.applied.json")


def _forms():
    if not AUDIT.exists():
        pytest.skip("the mark-moving tranche is not applied in this tree")
    subs = json.loads(AUDIT.read_text(encoding="utf-8"))["substitutions"]
    pairs = [{"form": f, "target": t, "accent_only": False}
             for f, t in sorted(subs.items())]
    shrink = next((r for r in pairs if len(r["form"]) != len(r["target"])), None)
    same = next((r for r in pairs if len(r["form"]) == len(r["target"])), None)
    if not shrink or not same:
        pytest.skip("no length-changing repair in this audit")
    return shrink, same


def _stage(tmp_path, rows_text, tranche_rows):
    (tmp_path / "corpus").mkdir()
    (tmp_path / "corpus_changes").mkdir()
    src = tmp_path / "corpus" / "work.jsonl"
    src.write_text("".join(
        json.dumps({"locus": f"1.{i}", "source": "ocr", "text": t},
                   ensure_ascii=False) + "\n"
        for i, t in enumerate(rows_text)), encoding="utf-8")
    tr = tmp_path / "tranche.json"
    tr.write_text(json.dumps({"rows": tranche_rows}, ensure_ascii=False),
                  encoding="utf-8")
    return src, tr


def _run(monkeypatch, tmp_path, tranche, *args):
    monkeypatch.setattr(rep, "REPO", tmp_path)
    monkeypatch.setattr(rep, "DATA", tmp_path)
    monkeypatch.setattr(sys, "argv",
                        ["repair", "--tranche", tranche.name, *args])
    rep.main()


def test_unapply_restores_a_row_whose_first_repair_changed_length(
        tmp_path, monkeypatch):
    shrink, same = _forms()
    # Both forms in one row, the length-changing one FIRST. That ordering is the
    # whole test: with the shrinking form second, backward and forward agree.
    text = f"τοῦτο {shrink['form']} καὶ τὰ {same['form']} πάντα"
    src, tr = _stage(tmp_path, [text], [shrink, same])
    before = src.read_bytes()

    _run(monkeypatch, tmp_path, tr, "--allow-mark-moves", "--apply")
    after = json.loads(src.read_text(encoding="utf-8"))["text"]
    assert shrink["target"] in after and same["target"] in after
    assert shrink["form"] not in after and same["form"] not in after

    _run(monkeypatch, tmp_path, tr, "--unapply")
    assert src.read_bytes() == before


def test_mark_moving_targets_are_refused_without_the_flag(tmp_path, monkeypatch):
    """The rail is opt-in per run, not lifted for good."""
    shrink, _ = _forms()
    src, tr = _stage(tmp_path, [f"τοῦτο {shrink['form']} πάντα"], [shrink])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, tmp_path, tr, "--apply")
    assert "--allow-mark-moves" in str(e.value)
    assert not list((tmp_path / "corpus_changes").iterdir())


def test_a_target_that_changes_letters_is_refused_even_with_the_flag(
        tmp_path, monkeypatch):
    """--allow-mark-moves relaxes the marks, never the word."""
    bad = {"form": "ὲπὶ", "target": "ἀπό", "accent_only": False}
    src, tr = _stage(tmp_path, ["τοῦτο ὲπὶ πάντα"], [bad])
    with pytest.raises(SystemExit) as e:
        _run(monkeypatch, tmp_path, tr, "--allow-mark-moves", "--apply")
    assert "changes letters" in str(e.value)
