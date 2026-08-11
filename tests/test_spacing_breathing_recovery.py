"""Issue #36: the 2026-08-07 capitals composition had no way back.

Its audit recorded a per-file sha256 pair and a histogram of the 14 distinct
substitutions, which is not a reversal: a histogram says ᾿Ι -> Ἰ happened four
thousand times, not where, and splitting every Ἰ would also split the ones the
sources already spelled that way. Worse, it keyed per-file records by BASENAME,
and 60 slugs exist in both data/corpus and data/corpus_secondary, so each pair
overwrote the other and 60 files went unrecorded entirely. Its own numbers said
so: the per-file counts summed to 28,514 against a stated 30,557, and the 60
lost files hold exactly the missing 2,043.

recover_spacing_breathing_sites.py rebuilt the site list from the commit that
applied the pass. These assert the rebuilt record is real: that it covers what
the audit's own totals claim, and that replaying it backwards over a file that
nothing has touched since gives back the bytes from before the pass.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

AUDIT = REPO / "data" / "corpus_changes" / "spacing-breathing-composition.json"


def _rec():
    if not AUDIT.exists():
        pytest.skip("capitals composition audit not present")
    rec = json.loads(AUDIT.read_text(encoding="utf-8"))
    if not isinstance(rec.get("files"), list):
        pytest.skip("site list not recovered in this tree")
    return rec


def test_the_record_covers_what_the_audit_claims():
    rec = _rec()
    sites = sum(len(spots) for b in rec["files"] for _i, spots in b["edits"])
    rows = sum(len(b["edits"]) for b in rec["files"])
    assert sites == rec["substitutions"]
    assert rows == rec["rows_touched"]
    # and it names more files than the basename keying could
    assert len(rec["files"]) == 738
    assert rec["files_the_basename_keying_LOST"]["count"] == 60


def test_every_file_is_named_by_path_not_basename():
    rec = _rec()
    paths = [b["file"] for b in rec["files"]]
    assert len(set(paths)) == len(paths)
    assert all(p.startswith(("data/corpus/", "data/corpus_secondary/")) for p in paths)
    # the collisions the old keying could not express are present as both sides
    names = [p.rsplit("/", 1)[-1] for p in paths]
    assert len(set(names)) < len(names)


def test_replaying_the_sites_backwards_restores_the_pre_pass_bytes():
    """Only over files nothing has been applied on top of, where the current
    bytes still are what the pass left. Read from the corpus, not a fixture."""
    rec = _rec()
    sha = lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()
    checked = 0
    for b in rec["files"]:
        fp = REPO / b["file"]
        if not fp.exists() or sha(fp.read_text(encoding="utf-8")) != b["sha256_after"]:
            continue
        rows = [json.loads(l) for l in
                fp.read_text(encoding="utf-8").splitlines() if l.strip()]
        for i, spots in b["edits"]:
            t = rows[i]["text"]
            for off, pair in reversed(spots):
                t = t[:off] + pair + t[off + 1:]
            rows[i]["text"] = t
        got = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        assert sha(got) == b["sha256_before"], b["file"]
        checked += 1
        if checked >= 40:
            break
    assert checked >= 40, f"only {checked} files are still at sha256_after"


def test_unapply_refuses_while_later_passes_sit_on_top():
    """The guard that stops a reversal quietly undoing everything after it."""
    rec = _rec()
    sha = lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest()
    moved = [b for b in rec["files"]
             if (REPO / b["file"]).exists()
             and sha((REPO / b["file"]).read_text(encoding="utf-8")) != b["sha256_after"]]
    if not moved:
        pytest.skip("nothing has been applied on top of the composition here")
    out = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "compose_spacing_breathings.py"),
         "--unapply"], capture_output=True, text=True, cwd=REPO)
    assert out.returncode != 0
    assert "applied on top of this pass" in (out.stdout + out.stderr)
    # and it must not have written anything
    for b in moved[:20]:
        assert sha((REPO / b["file"]).read_text(encoding="utf-8")) != b["sha256_before"]
