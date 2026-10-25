"""Reversibly adopt one explicitly credited Latte reading above the scan review."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import json
from pathlib import Path
import tempfile

import repair_hesychius_gap_readings as review
import repair_hesychius_missing_columns as base

ROOT, PRIMARY = base.ROOT, base.PRIMARY
AUDIT = "data/corpus_changes/hesychius-latte-reading"
AUTHORITY, PREIMAGE = AUDIT + "/changes.json", AUDIT + "/before.jsonl.gz"
NETWORKS = AUDIT + "/word-network.json.gz"
PREDECESSOR_SHA256 = "5049b1ee3bcfa6a8227ddc3c6176ef6df093c3f6f83b33f3abe6c1c7ba493bcc"
KEY, POSITION, READING = "schmidt-1867.column-259", 84, "ἀΐαχοι"
SOURCE = {
    "edition": "K. Latte, Hesychii Alexandrini lexicon, volume 1, 1953",
    "work": "4085.002", "alphabetic_letter": "alpha", "entry": 8275,
    "reading": READING, "consulted_on": "2026-10-25",
    "url": "https://stephanus.tlg.uci.edu/Iris/indiv/browser.jsp#doc=tlg&aid=4085&wid=002&ct=~x%22alpha%22y8275z1&rt=y&l=40&td=greek&links=tlg",
}
QUALIFICATION = (
    "Forty-four originally uncertain slots are resolved by the retained Schmidt scans, "
    "including two duplicate fragments. One further lexical reading, ἀΐαχοι, is "
    "explicitly adopted from Latte alpha 8275 at the owner's direction. Schmidt's "
    "diacritics at that occurrence remain unverified. Original OCR alternatives, "
    "votes, and the held scan-review decision remain available. This lexical "
    "projection establishes no contextual adjacency."
)


def recipe_pins():
    return {name: base.sha((Path(__file__).parent / name).read_bytes()) for name in
            ("adopt_hesychius_latte_reading.py", "ocr_consensus.py", "citation_alias_state.py")}


@contextmanager
def predecessor_view(root, raw):
    if base.sha(raw) != PREDECESSOR_SHA256:
        raise ValueError("Latte adoption predecessor changed")
    from citation_alias_state import _overlay
    with tempfile.TemporaryDirectory(prefix="hesychius-latte-predecessor-") as directory:
        view = Path(directory)
        _overlay(Path(root), view, {Path(PRIMARY).parts: raw})
        yield view


def build(root, predecessor, *, recorded_at):
    root = Path(root)
    with predecessor_view(root, predecessor) as view:
        old, _, _ = review.checked_state(view)
    networks = json.loads(gzip.decompress((root / review.NETWORKS).read_bytes()))
    result = networks[KEY]
    slot = result["ocr_consensus"]["slots"][POSITION]
    if slot["selected"] is not None or slot["lexical_eligible"] or slot["source_review"]["decision"] != "held":
        raise ValueError("The held Schmidt occurrence changed")
    record = {"key": KEY, "position": POSITION, "original_text": review._render(slot),
        "original_slot": deepcopy(slot), "corrected_text": READING,
        "decision": "owner-selected-later-edition-reading", "source": deepcopy(SOURCE),
        "schmidt_reading_confirmed": False, "recorded_at": recorded_at,
        "note": "Use Latte's reading for this occurrence; retain the uncertain Schmidt alternatives and scan-review hold."}
    slot["editorial_adoption"] = deepcopy(record)
    slot.update(selected=READING, status="editorially-adopted", lexical_eligible=True, lexical_exclusion=None)
    result["text"] = " ".join(text for item in result["ocr_consensus"]["slots"]
        if (text := READING if item["position"] == POSITION else review._render(item)))
    result["analysis_text"] = " ".join(item["selected"] for item in result["ocr_consensus"]["slots"] if item["lexical_eligible"])
    result["ocr_consensus"]["counts"] = dict(Counter(item["status"] for item in result["ocr_consensus"]["slots"]))
    result["ocr_consensus"]["policy"] += " One later editorial adoption from Latte is separately credited; it does not confirm Schmidt's printed diacritics."
    from ocr_consensus import compact_corpus_consensus
    output, changed = [], 0
    for raw in predecessor.splitlines(keepends=True):
        row = json.loads(raw)
        if row.get("edition") == base.EDITION and row.get("locus") == KEY:
            row.update(compact_corpus_consensus(result, {"path": NETWORKS, "key": KEY}))
            row["hesychius_latte_adoption"] = {"authority": AUTHORITY, "key": KEY, "position": POSITION}
            row["corrections"] = [*row["corrections"], "latte-reading-adoption"]
            raw, changed = base.jsonl([row]), changed + 1
        output.append(raw)
    if changed != 1:
        raise ValueError("Latte adoption must change exactly one corpus row")
    counts = deepcopy(old["counts"])
    counts.update(analysis_greek_tokens=sum(len(base.GREEK.findall(r["analysis_text"])) for r in networks.values()),
        surface_greek_tokens=sum(len(base.GREEK.findall(r["text"])) for r in networks.values()),
        reading_statuses=dict(sum((Counter(r["ocr_consensus"]["counts"]) for r in networks.values()), Counter())),
        column_reading_statuses={key.rsplit("-", 1)[1]: r["ocr_consensus"]["counts"] for key, r in networks.items()},
        editorial_adoption={"adopted_lexical_slots": 1, "unverified_schmidt_slots": 1})
    pins = {name: base.sha((root / name).read_bytes()) for name in review.authority_paths(root) if name != PRIMARY}
    return {PRIMARY: b"".join(output), NETWORKS: gzip.compress(base.encode({KEY: result}), mtime=0)}, counts, pins, record


def active(root=ROOT):
    root = Path(root)
    if (root / AUTHORITY).exists() != (root / PREIMAGE).exists():
        raise ValueError("Orphaned Latte adoption authority or preimage")
    if not (root / AUTHORITY).exists():
        if (root / PRIMARY).exists() and b'"hesychius_latte_adoption"' in (root / PRIMARY).read_bytes():
            raise ValueError("Latte adoption lacks its source authority")
        return False
    if base.sha((root / PRIMARY).read_bytes()) == PREDECESSOR_SHA256:
        return False
    return review.active(root)


def authority_paths(root=ROOT):
    return review.authority_paths(root) | {AUTHORITY, PREIMAGE, NETWORKS,
        *("scripts/" + name for name in recipe_pins())}


def signature(root):
    root = Path(root)
    return tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
        if (root / name).is_file() else (name, None, None) for name in sorted(authority_paths(root)))


def verify(root=ROOT, *, active_only=True):
    root = Path(root)
    audit = json.loads((root / AUTHORITY).read_bytes())
    archived = (root / PREIMAGE).read_bytes()
    predecessor = gzip.decompress(archived)
    if (audit.get("schema_version") != 1 or audit.get("predecessor_sha256") != PREDECESSOR_SHA256
            or audit.get("before_sha256") != base.sha(archived) or audit.get("recipe_sha256") != recipe_pins()
            or audit.get("qualification") != QUALIFICATION or set(audit.get("outputs", {})) != {PRIMARY, NETWORKS}):
        raise ValueError("Latte adoption authority changed")
    for name, expected in audit["recipe_sha256"].items():
        if base.sha((root / "scripts" / name).read_bytes()) != expected:
            raise ValueError("Latte adoption recipe changed: " + name)
    if active_only:
        for name, expected in audit["outputs"].items():
            if base.sha((root / name).read_bytes()) != expected:
                raise ValueError("Latte adoption output changed: " + name)
    outputs, counts, pins, record = build(root, predecessor, recorded_at=audit["recorded_at"])
    if (audit["outputs"] != {name: base.sha(raw) for name, raw in outputs.items()}
            or audit["counts"] != counts or audit["source_sha256"] != pins or audit["changes"] != [record]):
        raise ValueError("Latte adoption source replay differs from authority")
    return audit, predecessor


@lru_cache(maxsize=2)
def _checked(root_name, initial):
    root = Path(root_name)
    audit, predecessor = verify(root)
    rows = {(row["urn"], row["locus"]): row for row in map(json.loads, (root / PRIMARY).read_bytes().splitlines())
            if row.get("edition") == base.EDITION}
    if signature(root) != initial:
        raise ValueError("Latte adoption changed during verification")
    return audit, predecessor, rows


def checked_state(root=ROOT):
    root = Path(root).absolute()
    return deepcopy(_checked(str(root), signature(root)))


def apply(root=ROOT, *, recorded_at=None):
    root = Path(root)
    if active(root):
        raise ValueError("Latte adoption is already active")
    old = None
    if (root / AUTHORITY).exists():
        old, predecessor = verify(root, active_only=False)
        if recorded_at is not None and recorded_at != old["recorded_at"]:
            raise ValueError("Frozen Latte adoption timestamp changed")
        recorded_at = old["recorded_at"]
    else:
        if (root / NETWORKS).exists():
            raise ValueError("Unowned Latte adoption network")
        predecessor = (root / PRIMARY).read_bytes()
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    outputs, counts, pins, record = build(root, predecessor, recorded_at=recorded_at)
    if (root / PRIMARY).read_bytes() != predecessor or (root / NETWORKS).exists():
        raise ValueError("Refusing to overwrite a later Hesychius change")
    archive = gzip.compress(predecessor, mtime=0)
    audit = {"schema_version": 1, "recorded_at": recorded_at, "before_encoding": "gzip-jsonl",
        "before_sha256": base.sha(archive), "predecessor_sha256": PREDECESSOR_SHA256,
        "recipe_sha256": recipe_pins(), "source_sha256": pins,
        "outputs": {name: base.sha(raw) for name, raw in outputs.items()},
        "counts": counts, "qualification": QUALIFICATION, "changes": [record]}
    if old is not None and base.encode(audit) != (root / AUTHORITY).read_bytes():
        raise ValueError("Reapply must reproduce the frozen Latte adoption")
    base.publish(root, {**outputs, PREIMAGE: archive, AUTHORITY: base.encode(audit)})
    return audit


def undo(root=ROOT):
    root = Path(root)
    audit = json.loads((root / AUTHORITY).read_bytes())
    archive = (root / PREIMAGE).read_bytes()
    predecessor = gzip.decompress(archive)
    if (base.sha(archive) != audit["before_sha256"] or base.sha(predecessor) != PREDECESSOR_SHA256
            or set(audit["outputs"]) != {PRIMARY, NETWORKS}):
        raise ValueError("Latte adoption undo authority changed")
    for name, expected in audit["outputs"].items():
        if base.sha((root / name).read_bytes()) != expected:
            raise ValueError("Refusing to overwrite a later Hesychius change")
    base.publish(root, {PRIMARY: predecessor, NETWORKS: None})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "verify", "undo"))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.action == "undo":
        undo(args.root)
        print("Restored the exact pre-adoption Schmidt scan review")
    else:
        audit = apply(args.root) if args.action == "apply" else verify(args.root)[0]
        print(json.dumps(audit["counts"], sort_keys=True))
