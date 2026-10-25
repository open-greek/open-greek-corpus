#!/usr/bin/env python3
"""Consolidate four identical First1K Pindar units without merging opaque IDs.

These are duplicate serializations of the same digital edition, not independent
textual witnesses. The canonical primary bytes stay unchanged. The four older
TLG-keyed primaries become literal secondary records with explicit citation and
identity concordances; the original opaque identifiers remain tombstoned.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/corpus_changes/pindar-duplicate-primaries"
FRAGMENT = AUDIT + "/passage-aliases.json"
RECORDS = AUDIT + "/records.jsonl.gz"
SECONDARY_EDITION = "first1k-pindar-former-primary-2026-10"
REVISION = "4c9c843d80ee94b4371f52add5f7d68bbfe7ba4c"
LICENSE = "CC-BY-SA-4.0"
QUALIFICATION = (
    "Four duplicate serializations of the same First1K edition are counted "
    "once. Equality is exact after removing only the work urn. No Greek text, "
    "source license, original citation, or opaque identifier is discarded; "
    "the duplicate IDs remain separate retired ledger entries with explicit "
    "canonical redirects, rather than being reassigned to another expression."
)
# The titles, CTS identifiers and license are recorded in the pinned First1K
# TEI headers; the equality check covers every field of all eight corpus files.
PAIRS = (
    {"old": "tlg4170.tlg001a", "canonical": "vitae-pindari-et-varia-de-pindaro.vita-ambrosiana",
     "old_id": "ogc003541", "canonical_id": "ogc003674", "title": "Vita Ambrosiana",
     "old_sha256": "5ba3a876364f1c068cf78e807a93686becdd1fe7c35d7d20fd9781ebc87f995b",
     "canonical_sha256": "e205ed723f440220922ff767e0b0d84a57ebd117df17492d2376afcf0149c16c",
     "source_sha256": "f86cfbab86a751069f46e1591489e86e64ec0518280254b28998cc144785e459"},
    {"old": "tlg4170.tlg001b", "canonical": "vitae-pindari-et-varia-de-pindaro.vita-thomana-et-hypothesis-olympiorum",
     "old_id": "ogc003542", "canonical_id": "ogc003676", "title": "Vita Thomana et hypothesis Olympiorum",
     "old_sha256": "e7e3c91912e77d86be39bc9b98ff1eea5b26f0b609339387e81b9034acdcaa7c",
     "canonical_sha256": "53a2f049e2e42e6213e0b4bd3ecc5e3354fc3b4156a9881fba880ea3725fd994",
     "source_sha256": "e1ceb1dc3471e51730cac58cf366c5c2e868c2b41e405e30ceed744f1b3546ca"},
    {"old": "tlg4170.tlg001c", "canonical": "vitae-pindari-et-varia-de-pindaro.vita-metrica",
     "old_id": "ogc003543", "canonical_id": "ogc003675", "title": "Vita Metrica",
     "old_sha256": "d4997334f6946c5f19d4717bbbf97dce578555e4af7ee09e80f576af87536384",
     "canonical_sha256": "c692c6f761a900b183f166aa219d43b2383fd03467708a74efe488a817983c51",
     "source_sha256": "9c4f318ad1fd6c95c725844d6e7bdc23a4e3bcb970a21b1d2217852b07c73619"},
    {"old": "tlg4170.tlg001d", "canonical": "vitae-pindari-et-varia-de-pindaro.pentathlon-et-de-novem-lyricis",
     "old_id": "ogc003544", "canonical_id": "ogc003673", "title": "Pentathlon et de novem lyricis",
     "old_sha256": "d42c9ad4042dd8676a84612e0437c905d8a5eccc8e51d778be58554b6e1fc3dc",
     "canonical_sha256": "ab2efdb7f521dd2464131865a4d2b8e09901a07b56dd46e8d1d374276125905a",
     "source_sha256": "6e31ccdebbc1204b5de53fdd07117e8ffd7fe8688c8bccc991c9bfcf80d70bba"},
)
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")


def primary(slug):
    return f"data/corpus/{slug}.jsonl"


def source_path(pair):
    return f"sources/first1k/data/tlg4170/{pair['old'].split('.')[1]}/{pair['old']}.1st1K-grc1.xml"


def source_metadata(pair):
    path = source_path(pair)
    return {"provider": "first1k", "edition": "1st1K-grc1", "license": LICENSE,
        "revision": REVISION, "sha256": pair["source_sha256"], "path": path,
        "url": "https://github.com/OpenGreekAndLatin/First1KGreek/blob/" + REVISION + "/" + path.removeprefix("sources/first1k/"),
        "title": pair["title"], "editor": "Drachmann, Anders Bjørn", "year": 1903,
        "cts": "urn:cts:greekLit:" + pair["old"]}


def input_pins():
    return {name: pin for pair in PAIRS for name, pin in (
        (primary(pair["old"]), pair["old_sha256"]),
        (primary(pair["canonical"]), pair["canonical_sha256"]),
        (source_path(pair), pair["source_sha256"]))}


def ingestion_slug(urn, resolved):
    """Resolve only the four source-identified units, even without a crosswalk.

    A future conflicting concordance must be reviewed rather than silently
    replacing the author and title confirmed by these First1K edition headers.
    This route also applies before the retrospective duplicate repair is active.
    """
    for pair in PAIRS:
        if urn == pair["old"]:
            # The full inventory's reference-only slug predates the titled
            # delivered expression. It shares the exact CTS anchor and must
            # also resolve here when the generated crosswalk is unavailable.
            inventory_slug = "vitae-pindari-et-varia-de-pindaro." + urn.replace(".", "-")
            if resolved not in (urn, pair["canonical"], inventory_slug):
                raise ValueError("Pindar First1K work identity conflicts with its reviewed route: " + urn)
            return pair["canonical"]
    return resolved


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode()


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode() for row in rows)


def local_path(root, name):
    path = Path(name)
    if (path.is_absolute() or ".." in path.parts or "\\" in name
            or not path.parts or path.parts[0] != "data"):
        raise ValueError("Unsafe Pindar repair output path: " + name)
    return Path(root) / path


def recipe_pins(root=ROOT):
    return {name: sha((Path(root) / "scripts" / name).read_bytes()) for name in
        ("repair_pindar_duplicate_primaries.py",)}


def publish(root, outputs):
    """Stage outputs first, and restore every changed preimage on an I/O error."""
    before = {name: local_path(root, name).read_bytes() if local_path(root, name).is_file() else None
              for name in outputs}
    staged, changed = {}, []
    try:
        for name, raw in outputs.items():
            path = local_path(root, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            if raw is not None:
                with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
                    stream.write(raw)
                    staged[name] = Path(stream.name)
        try:
            for name, raw in outputs.items():
                path = local_path(root, name)
                if raw is None:
                    path.unlink(missing_ok=True)
                else:
                    os.replace(staged[name], path)
                changed.append(name)
        except OSError:
            for name in reversed(changed):
                path = local_path(root, name)
                if before[name] is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(before[name])
            raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)


def check_inputs(before):
    if set(input_pins()) - set(before):
        raise ValueError("A pinned Pindar source input is missing")
    for name, pin in input_pins().items():
        if not isinstance(before[name], bytes) or sha(before[name]) != pin:
            raise ValueError("Pindar source input changed: " + name)


def archived_inputs(root):
    path = Path(root) / AUDIT / "before.json.gz"
    if not path.exists():
        return {name: (Path(root) / name).read_bytes() for name in input_pins()}
    decoded = json.loads(gzip.decompress(path.read_bytes()))
    return {name: None if raw is None else base64.b64decode(raw, validate=True)
            for name, raw in decoded.items()}


def build(root, before, *, recorded_at):
    check_inputs(before)
    outputs, records, aliases, redirects, summaries = {}, [], {}, {}, {}
    total_rows = total_tokens = 0
    for pair in PAIRS:
        old, canonical = pair["old"], pair["canonical"]
        originals = [json.loads(line) for line in before[primary(old)].splitlines() if line.strip()]
        kept = [json.loads(line) for line in before[primary(canonical)].splitlines() if line.strip()]
        if (not originals or len(originals) != len(kept)
                or len({row["locus"] for row in originals}) != len(originals)):
            raise ValueError("Pindar duplicate row accounting changed: " + old)
        secondary = f"data/corpus_secondary/{canonical}.jsonl"
        literal = []
        aliases[old] = {}
        for original, current in zip(originals, kept, strict=True):
            if (original.get("urn") != old or current.get("urn") != canonical
                    or original.get("source") != "first1k" or original.get("license") != LICENSE
                    or original.get("edition") != "1st1K-grc1"
                    or {key: value for key, value in original.items() if key != "urn"}
                    != {key: value for key, value in current.items() if key != "urn"}):
                raise ValueError("Pindar duplicate is not identical except for its work urn: " + old)
            locus = old + ".original." + original["locus"]
            target = {"slug": canonical, "path": secondary, "storage": "secondary", "locus": locus,
                "current": {"slug": canonical, "path": primary(canonical), "locus": current["locus"]},
                "scope": "exact-same-edition-row"}
            routed = dict(original, urn=canonical, edition=SECONDARY_EDITION, locus=locus,
                original_urn=old, original_locus=original["locus"], original_edition=original["edition"],
                original_row=original, source_role="literal-duplicate-serialization",
                pindar_duplicate_review={"authority": AUDIT + "/changes.json"},
                canonical_target=target["current"], independent_witness=False)
            literal.append(routed)
            aliases[old][original["locus"]] = target
            records.append({"original_path": primary(old), "original_sha256": pair["old_sha256"],
                "original_row": original, "original_text": original["text"],
                "corrected_text": current["text"], "canonical_row": current,
                "evidence": {"method": "Exact equality after removing only urn", "source": source_metadata(pair)},
                "destination": target, "recorded_at": recorded_at})
        tokens = sum(len(GREEK.findall(row["text"])) for row in kept)
        total_rows += len(kept)
        total_tokens += tokens
        summaries[canonical] = {"retired_source": old, "retired_id": pair["old_id"],
            "canonical_id": pair["canonical_id"], "primary_rows": len(kept), "secondary_rows": len(literal),
            "analysis_tokens": tokens, "source": source_metadata(pair), "secondary_path": secondary}
        redirects[old] = {"slug": canonical, "source_id": pair["old_id"], "target_id": pair["canonical_id"]}
        outputs[primary(old)] = None
        outputs[primary(canonical)] = before[primary(canonical)]
        outputs[secondary] = jsonl(literal)
        outputs[AUDIT + "/sources/" + old + ".xml.gz"] = gzip.compress(before[source_path(pair)], mtime=0)
    outputs[RECORDS] = gzip.compress(jsonl(records), mtime=0)
    outputs[FRAGMENT] = encoded({"schema_version": 1, "aliases": aliases,
        "retired_sources": {pair["old"]: pair["old_id"] for pair in PAIRS},
        "canonical_redirects": redirects})
    return outputs, summaries, {"pairs": len(PAIRS), "original_primary_rows": total_rows * 2,
        "primary_rows": total_rows, "secondary_rows": total_rows,
        "original_primary_analysis_tokens": total_tokens * 2, "analysis_tokens": total_tokens,
        "duplicate_analysis_tokens_removed": total_tokens}


def active(root=ROOT):
    root = Path(root)
    authority, archive = root / AUDIT / "changes.json", root / AUDIT / "before.json.gz"
    if authority.exists() != archive.exists():
        raise ValueError("An orphaned Pindar authority or preimage archive is present")
    if not authority.exists():
        return False
    audit = json.loads(authority.read_bytes())
    actual = {name: sha(local_path(root, name).read_bytes()) if local_path(root, name).is_file() else None
              for name in audit["outputs"]}
    if actual == audit["outputs"]:
        return True
    before = archived_inputs(root)
    if all((local_path(root, name).read_bytes() if local_path(root, name).is_file() else None) == before[name]
           for name in audit["outputs"]):
        return False
    raise ValueError("Pindar repair is neither fully active nor exactly unapplied")


def verify(root=ROOT, *, active_only=True, replay=True):
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("before_encoding") != "base64"
            or audit.get("inputs") != input_pins() or audit.get("qualification") != QUALIFICATION
            or audit.get("recipe_sha256") != recipe_pins(root)):
        raise ValueError("Pindar repair recipe, input pins, or qualification changed")
    archive = (root / AUDIT / "before.json.gz").read_bytes()
    if sha(archive) != audit["before_sha256"]:
        raise ValueError("Pindar literal preimage archive changed")
    before = archived_inputs(root)
    check_inputs(before)
    if set(before) != set(input_pins()) | set(audit["outputs"]):
        raise ValueError("Pindar preimage inventory changed")
    if any(before[name] is not None for name in set(audit["outputs"]) - set(input_pins())):
        raise ValueError("A newly created Pindar destination has an invented preimage")
    if active_only and not active(root):
        raise ValueError("Pindar repair is not active")
    if replay:
        outputs, summaries, counts = build(root, before, recorded_at=audit["recorded_at"])
        if ({name: sha(raw) if raw is not None else None for name, raw in outputs.items()} != audit["outputs"]
                or summaries != audit["works"] or counts != audit["counts"]):
            raise ValueError("Pindar literal replay differs")
    return audit, before


def alias_fragment(root=ROOT):
    root = Path(root)
    if not active(root):
        return None
    verify(root)
    entries = json.loads((root / "data/work_ids.json").read_bytes())["works"]
    for pair in PAIRS:
        for identifier, slug, status in ((pair["old_id"], pair["old"], "retired"),
                (pair["canonical_id"], pair["canonical"], "served")):
            entry = entries.get(identifier, {})
            if entry.get("slug") != slug or entry.get("status") != status or entry.get("former_slugs", []):
                raise ValueError("Pindar canonical redirect differs from its immutable identifier ledger: " + identifier)
    return {**json.loads((root / FRAGMENT).read_bytes()), "authority": {
        "path": AUDIT + "/changes.json", "sha256": sha((root / AUDIT / "changes.json").read_bytes())}}


def metadata(root=ROOT):
    return verify(root)[0]["works"] if active(root) else {}


def apply(root=ROOT, *, recorded_at=None):
    root = Path(root)
    authority = root / AUDIT / "changes.json"
    if active(root):
        raise ValueError("Pindar duplicate repair is already active")
    before = archived_inputs(root)
    old = None
    if authority.exists():
        old, _ = verify(root, active_only=False)
        if recorded_at is not None and recorded_at != old["recorded_at"]:
            raise ValueError("Reapplying the frozen Pindar audit cannot change its timestamp")
        recorded_at = old["recorded_at"]
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    outputs, summaries, counts = build(root, before, recorded_at=recorded_at)
    for name in outputs:
        if name not in before:
            if local_path(root, name).exists():
                raise ValueError("Refusing to overwrite an unowned Pindar destination: " + name)
            before[name] = None
    raw = gzip.compress(encoded({name: None if value is None else base64.b64encode(value).decode("ascii")
        for name, value in before.items()}), mtime=0)
    audit = {"schema_version": 1, "recorded_at": recorded_at, "before_encoding": "base64",
        "recipe_sha256": recipe_pins(root), "before_sha256": sha(raw), "inputs": input_pins(),
        "outputs": {name: sha(value) if value is not None else None for name, value in outputs.items()},
        "works": summaries, "counts": counts, "qualification": QUALIFICATION}
    if old is not None and encoded(audit) != authority.read_bytes():
        raise ValueError("Pindar reapply must reproduce the complete frozen audit")
    publish(root, {**outputs, AUDIT + "/before.json.gz": raw, AUDIT + "/changes.json": encoded(audit)})
    return audit


def undo(root=ROOT):
    """Restore exact preimages, including after source or recipe invalidation."""
    root = Path(root)
    audit = json.loads((root / AUDIT / "changes.json").read_bytes())
    raw = (root / AUDIT / "before.json.gz").read_bytes()
    if sha(raw) != audit["before_sha256"]:
        raise ValueError("Pindar undo archive changed")
    before = archived_inputs(root)
    check_inputs(before)
    outputs, _, _ = build(root, before, recorded_at=audit["recorded_at"])
    if ({name: sha(value) if value is not None else None for name, value in outputs.items()} != audit["outputs"]
            or any(before.get(name) is not None for name in set(outputs) - set(input_pins()))):
        raise ValueError("Pindar undo output inventory differs from its literal replay")
    for name, expected in audit["outputs"].items():
        current = sha(local_path(root, name).read_bytes()) if local_path(root, name).is_file() else None
        if current != expected:
            raise ValueError("Refusing to overwrite a later Pindar output: " + name)
    publish(root, {name: before[name] for name in audit["outputs"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("apply", "verify", "undo"))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.action == "undo":
        undo(args.root)
        print("Restored exact Pindar duplicate preimages")
    else:
        audit = apply(args.root) if args.action == "apply" else verify(args.root)[0]
        print(json.dumps(audit["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
