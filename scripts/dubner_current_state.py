"""Compose the frozen Dübner reviews with the later evidence continuation."""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

import dubner_layers as previous
import review_dubner_evidence as continuation

ROOT = continuation.ROOT


@lru_cache(maxsize=2)
def _scope_state(root_name, signature):
    root = Path(root_name)
    _,before,_ = continuation._checked(root_name,signature)
    base = continuation.previous.base
    scope,original = base.verify(root,active_only=False)
    reading_before = continuation.previous.archived_inputs(root)
    postimages = {}
    for name,expected in scope["outputs"].items():
        if expected is None:
            continue
        raw = reading_before.get(name,before.get(name))
        if raw is None:
            raw = (root/name).read_bytes()
        if continuation.sha(raw) != expected:
            raise ValueError("Dübner scope predecessor differs from checked admission: " + name)
        postimages[name] = raw
    return scope,original,postimages


def _scope(root):
    root = Path(root).absolute()
    return _scope_state(str(root),continuation.signature(root))


def verify_scope(root=ROOT, *, replacements=None, replay=False):
    if replacements is not None or not continuation.active(root):
        return previous.verify_scope(root,replacements=replacements,replay=replay)
    # The continuation's checked state already replays both frozen producers.
    # Do not repeat that full replay for every alias or primary-file lookup.
    scope,original,_ = _scope(root)
    return deepcopy(scope),deepcopy(original)


def scope_postimage_bytes(root,name):
    if not continuation.active(root):
        return previous.scope_postimage_bytes(root,name)
    base = continuation.previous.base
    base.local_path(root,name)
    _,_,postimages = _scope(root)
    if name not in postimages:
        raise ValueError("The scope repair does not own this historical postimage: " + name)
    return postimages[name]


def alias_fragment(root=ROOT):
    if not continuation.active(root):
        return previous.alias_fragment(root)
    _scope(root)
    base = continuation.previous.base
    fragment = json.loads((Path(root)/base.FRAGMENT).read_bytes())
    ledger = json.loads((Path(root)/"data/work_ids.json").read_bytes())["works"]
    if (ledger.get("ogc002861",{}).get("slug") != base.B
            or ledger["ogc002861"]["status"] != "retired"):
        raise ValueError("The retired Platonius identity must remain in its immutable ledger")
    return {**fragment,"authority":{"path":base.AUDIT+"/changes.json",
        "sha256":base.sha((Path(root)/base.AUDIT/"changes.json").read_bytes())}}


def metadata(root=ROOT):
    if not continuation.active(root):
        return previous.metadata(root)
    audit,_,_ = continuation._state(root)
    base = continuation.previous.base
    scope,_,_ = _scope(root)
    definitions = {value["slug"]:value for value in base.work_definitions().values()}
    authority = {"path":continuation.AUTHORITY,
        "sha256":continuation.sha((Path(root)/continuation.AUTHORITY).read_bytes())}
    return {slug:{**definitions[slug],**deepcopy(counts),"edition":base.EDITION,
        "sources":deepcopy(scope["sources"]),"authority":deepcopy(authority),
        "qualification":continuation.QUALIFICATION} for slug,counts in audit["works"].items()}


def validate_projection(row,root=ROOT):
    if not continuation.active(root):
        if "dubner_evidence_review" in row:
            raise ValueError("Dübner continuation row lacks an active authority")
        return previous.validate_projection(row,root)
    _,_,rows = continuation._state(root)
    if rows.get((row["urn"],row["locus"])) != row:
        raise ValueError("Dübner continuation projection differs from checked admission")
    return row["analysis_text"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",required=True)
    parser.add_argument("--root",type=Path,default=ROOT)
    args = parser.parse_args()
    if continuation.active(args.root):
        audit,_,_ = continuation.checked_state(args.root)
    else:
        audit,_ = previous.verify_scope(args.root,replay=True)
    print(json.dumps(audit["counts"],sort_keys=True))
