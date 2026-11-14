#!/usr/bin/env python3
"""Old addresses for the Aristophanes lines renumbered in corpus issue #139.

Five Perseus plays declare a single line citation, `//tei:l[@n=$1]`, but the
earlier ingest prefixed the strophe or antistrophe counter of a numbered lyric
container to each of its lines, so Peace 500 was served as `2.500`. The native
generator now follows the declaration. Releases through corpus-2026-11-07.1
carry the old addresses.

`changes.json` records every changed row: its position, old and new locus, and
the unchanged text hash, with both file hashes. `verify` rebuilds each earlier
file byte for byte from the current one. `alias_fragment` gives the work index
each old address as a passage alias. No old address equals a current locus, so
an alias never intercepts a current citation. Each play also has a top-level
`source_urn`/`locus_map` record, which annotation refreshes read to move
unchanged rows to their new addresses.

  python3 scripts/lyric_line_citations.py --record --base <git-revision>
  python3 scripts/lyric_line_citations.py --check
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/corpus_changes/aristophanes-line-citations-139"
AUTHORITY = AUDIT + "/changes.json"
ISSUE = "https://github.com/open-greek/open-greek-corpus/issues/139"
LAST_OLD_RELEASE = "corpus-2026-11-07.1"
DATE = "2026-11-13"
SOURCES = "data/release_build_inputs/source-repositories.json"
WORKS = {
    "aristophanes-comedy.vespae": "data/tlg0019/tlg004/tlg0019.tlg004.perseus-grc2.xml",
    "aristophanes-comedy.pax": "data/tlg0019/tlg005/tlg0019.tlg005.perseus-grc2.xml",
    "aristophanes-comedy.aves": "data/tlg0019/tlg006/tlg0019.tlg006.perseus-grc2.xml",
    "aristophanes-comedy.lysistrata": "data/tlg0019/tlg007/tlg0019.tlg007.perseus-grc2.xml",
    "aristophanes-comedy.ecclesiazusae": "data/tlg0019/tlg010/tlg0019.tlg010.perseus-grc2.xml",
}
RULE = ("An edition whose only citation pattern selects //tei:l[@n=$1] is cited by line "
        "number alone; strophe and antistrophe counters stay out of the locus.")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def corpus_path(slug):
    return f"data/corpus/{slug}.jsonl"


def record_path(slug):
    return f"data/corpus_changes/{slug}.line-citations-139.json"


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=1, sort_keys=True) + "\n").encode()


def rows(raw):
    lines = raw.decode("utf-8").splitlines(keepends=True)
    if any(not line.strip() for line in lines):
        raise ValueError("Corpus file has a blank row")
    return lines, [json.loads(line) for line in lines]


def relocate(line, row, old, new):
    """Return `line` with its locus changed from `old` to `new` and nothing else."""
    field = '"locus": '
    before, after = field + json.dumps(old, ensure_ascii=False), field + json.dumps(new, ensure_ascii=False)
    if row["locus"] != old or line.count(before) != 1:
        raise ValueError(f"Row does not carry exactly one locus {old!r}")
    moved = line.replace(before, after)
    if json.loads(moved) != {**row, "locus": new}:
        raise ValueError(f"Relocating {old!r} changed more than the locus")
    return moved


def compare(slug, old_raw, new_raw):
    """The ordered changes between two files that differ only in their loci."""
    _, old = rows(old_raw)
    _, new = rows(new_raw)
    if len(old) != len(new):
        raise ValueError(f"{slug}: row count changed")
    changes = []
    for position, (before, after) in enumerate(zip(old, new)):
        if {k: v for k, v in before.items() if k != "locus"} != {k: v for k, v in after.items() if k != "locus"}:
            raise ValueError(f"{slug}: row {position} changed outside its locus")
        if before["urn"] != slug:
            raise ValueError(f"{slug}: row {position} belongs to {before['urn']}")
        if before["locus"] != after["locus"]:
            changes.append({"position": position, "before": before["locus"], "after": after["locus"],
                            "text_sha256": sha(after["text"].encode())})
    old_loci, new_loci = [r["locus"] for r in old], [r["locus"] for r in new]
    if len(set(old_loci)) != len(old) or len(set(new_loci)) != len(new):
        raise ValueError(f"{slug}: duplicate locus")
    if {c["before"] for c in changes} & set(new_loci):
        raise ValueError(f"{slug}: an old address is still a current locus")
    return changes


def rebuild_before(slug, new_raw, changes):
    lines, parsed = rows(new_raw)
    for change in changes:
        position = change["position"]
        if sha(parsed[position]["text"].encode()) != change["text_sha256"]:
            raise ValueError(f"{slug}: text changed at row {position}")
        lines[position] = relocate(lines[position], parsed[position], change["after"], change["before"])
    return "".join(lines).encode("utf-8")


def source_pin(root, slug):
    path = WORKS[slug]
    perseus = json.loads((root / SOURCES).read_text())["repositories"]["perseus"]
    expected = perseus["files"][path]["sha256"]
    local = root / "sources/perseus" / path
    if not local.is_file() or sha(local.read_bytes()) != expected:
        raise ValueError(f"{slug}: source XML is missing or differs from its pin")
    return {"repository": "https://github.com/PerseusDL/canonical-greekLit",
            "revision": perseus["revision"], "path": path, "sha256": expected}


def locus_records(authority_raw):
    authority = json.loads(authority_raw)
    pin = {"path": AUTHORITY, "sha256": sha(authority_raw)}
    return {record_path(slug): dump({
        "what": "Line citations without lyric strophe counters",
        "date": authority["date"], "issue": authority["issue"], "source_urn": slug,
        "last_release_with_old_addresses": authority["last_release_with_old_addresses"],
        "text_unchanged": True, "authority": pin,
        "locus_map": {c["before"]: f"{slug}:{c['after']}" for c in work["changes"]}})
        for slug, work in authority["works"].items()}


def record(root, base):
    root = Path(root)
    works = {}
    for slug in WORKS:
        path = corpus_path(slug)
        old_raw = subprocess.run(["git", "-C", str(root), "show", f"{base}:{path}"],
                                 check=True, capture_output=True).stdout
        new_raw = (root / path).read_bytes()
        changes = compare(slug, old_raw, new_raw)
        if rebuild_before(slug, new_raw, changes) != old_raw:
            raise ValueError(f"{slug}: the earlier file cannot be rebuilt")
        works[slug] = {"path": path, "source": source_pin(root, slug), "rows": len(rows(new_raw)[1]),
                       "before_sha256": sha(old_raw), "after_sha256": sha(new_raw), "changes": changes}
    authority = dump({"schema": 1, "kind": "line-citation-renumbering", "date": DATE, "issue": ISSUE,
                      "rule": RULE, "last_release_with_old_addresses": LAST_OLD_RELEASE,
                      "counts": {"works": len(works),
                                 "changed_loci": sum(len(w["changes"]) for w in works.values())},
                      "works": works})
    outputs = {AUTHORITY: authority, **locus_records(authority)}
    for name, raw in outputs.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(raw)
    return verify(root)


def load(root):
    raw = (Path(root) / AUTHORITY).read_bytes()
    authority = json.loads(raw)
    if set(authority["works"]) != set(WORKS) or authority["counts"]["changed_loci"] != sum(
            len(w["changes"]) for w in authority["works"].values()):
        raise ValueError("Line citation record is incomplete")
    return raw, authority


def verify(root=ROOT):
    """Prove the recorded change exactly: hashes, inverse, and per-play maps."""
    root = Path(root)
    raw, authority = load(root)
    for slug, work in authority["works"].items():
        current = (root / work["path"]).read_bytes()
        if sha(current) != work["after_sha256"] or len(rows(current)[1]) != work["rows"]:
            raise ValueError(f"{slug}: current file differs from the recorded result")
        if sha(rebuild_before(slug, current, work["changes"])) != work["before_sha256"]:
            raise ValueError(f"{slug}: the earlier file cannot be rebuilt")
        source = root / "sources/perseus" / work["source"]["path"]
        if source.is_file() and sha(source.read_bytes()) != work["source"]["sha256"]:
            raise ValueError(f"{slug}: source XML differs from its pin")
    for name, expected in locus_records(raw).items():
        if (root / name).read_bytes() != expected:
            raise ValueError(f"Locus map differs from the authority: {name}")
    return authority["counts"]


def alias_fragment(root=ROOT):
    """Old addresses as passage aliases, while every target is current."""
    root = Path(root)
    if not (root / AUTHORITY).is_file():
        return None
    raw, authority = load(root)
    aliases = {}
    for slug, work in authority["works"].items():
        loci = {row["locus"] for row in rows((root / work["path"]).read_bytes())[1]}
        if any(c["after"] not in loci or c["before"] in loci for c in work["changes"]):
            raise ValueError(f"{slug}: a line citation alias no longer fits the current file")
        aliases[slug] = {c["before"]: {"slug": slug, "path": work["path"], "locus": c["after"]}
                         for c in work["changes"]}
    return {"aliases": aliases, "authority": {"path": AUTHORITY, "sha256": sha(raw)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--record", action="store_true", help="record the change against --base")
    mode.add_argument("--check", action="store_true", help="verify the recorded change")
    parser.add_argument("--base", help="git revision holding the earlier corpus files")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.record and not args.base:
        parser.error("--record requires --base")
    counts = record(args.root, args.base) if args.record else verify(args.root)
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
