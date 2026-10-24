"""Validate current Dübner readings without rewriting the frozen scope repair.

The source partition remains a separate authority. A later reading review may
replace its primary projections only when it preserves their exact postimages
and verifies every current output. Original passage aliases still resolve to
the literal witnesses owned by the scope repair.
"""
from __future__ import annotations

import argparse
from functools import lru_cache
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
READINGS = "data/corpus_changes/dubner-1855-readings"


def _base():
    import repair_dubner_scholias
    return repair_dubner_scholias


@lru_cache(maxsize=4)
def _active_status(root, signature):
    import repair_dubner_readings
    return repair_dubner_readings.active(Path(root))


def _reading_layer(root):
    root = Path(root)
    authority = root / READINGS / "changes.json"
    archive = root / READINGS / "before.json.gz"
    if authority.is_file() != archive.is_file():
        raise ValueError("Dübner reading authority or predecessor archive is missing")
    if not authority.is_file():
        return None
    audit = json.loads(authority.read_bytes())
    names = [READINGS + "/changes.json", READINGS + "/before.json.gz", *audit["outputs"]]
    signature = tuple((name, (root / name).stat().st_size, (root / name).stat().st_mtime_ns)
        if (root / name).is_file() else (name, None, None) for name in names)
    import repair_dubner_readings
    return repair_dubner_readings if _active_status(str(root.absolute()), signature) else None


def verify_scope(root=ROOT, *, replacements=None, replay=False):
    """Check every frozen scope output against its proved historical bytes.

    A reading producer supplies its checked literal preimages while validating
    itself. Other consumers first validate that producer; no missing or changed
    output is waived merely because a later authority exists.
    """
    root = Path(root)
    base = _base()
    if replacements is None:
        later = _reading_layer(root)
        if later is None:
            return base.verify(root, replay=replay)
        _, replacements = (later.verify(root, replay=True) if replay else later.checked_state(root))
    audit, original = base.verify(root, active_only=False, replay=replay)
    for name, expected in audit["outputs"].items():
        if name in replacements:
            raw = replacements[name]
        else:
            path = base.local_path(root, name)
            raw = path.read_bytes() if path.is_file() else None
        if (base.sha(raw) if raw is not None else None) != expected:
            raise ValueError("Frozen Dübner output differs from its checked predecessor: " + name)
    return audit, original


def scope_postimage_bytes(root, name):
    root = Path(root)
    base = _base()
    base.local_path(root, name)
    later = _reading_layer(root)
    if later is None:
        audit, _ = base.verify(root)
        replacements = {}
    else:
        _, replacements = later.checked_state(root)
        audit, _ = verify_scope(root, replacements=replacements)
    if name not in audit["outputs"] or audit["outputs"][name] is None:
        raise ValueError("The scope repair does not own this historical postimage: " + name)
    return replacements[name] if name in replacements else (root / name).read_bytes()


def metadata(root=ROOT):
    root = Path(root)
    base = _base()
    later = _reading_layer(root)
    if later is None:
        return base.metadata(root)
    audit, before = later.checked_state(root)
    scope, _ = verify_scope(root, replacements=before)
    definitions = {value["slug"]: value for value in base.work_definitions().values()}
    return {slug: {**definitions[slug], **counts, "edition": base.EDITION,
        "authority": {"path": READINGS + "/changes.json",
                      "sha256": base.sha((root / READINGS / "changes.json").read_bytes())},
        "sources": scope["sources"], "qualification": audit["qualification"]}
        for slug, counts in audit["works"].items()}


def alias_fragment(root=ROOT):
    root = Path(root)
    base = _base()
    later = _reading_layer(root)
    if later is None:
        return base.alias_fragment(root)
    verify_scope(root)
    fragment = json.loads((root / base.FRAGMENT).read_bytes())
    ledger = json.loads((root / "data/work_ids.json").read_bytes())["works"]
    if (ledger.get("ogc002861", {}).get("slug") != base.B
            or ledger["ogc002861"]["status"] != "retired"):
        raise ValueError("The retired Platonius identity must remain in its immutable ledger")
    return {**fragment, "authority": {"path": base.AUDIT + "/changes.json",
        "sha256": base.sha((root / base.AUDIT / "changes.json").read_bytes())}}


def validate_projection(row, root=ROOT):
    later = _reading_layer(root)
    if later is None:
        return _base().validate_projection(row, root)
    return later.validate_projection(row, root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", required=True)
    args = parser.parse_args()
    later = _reading_layer(args.root)
    current = (later.verify(args.root, replay=True)[0] if later
               else verify_scope(args.root, replay=True)[0])
    print(json.dumps(current["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
