"""Describe the active Herodas and Hipponax source-role partition."""
from collections import Counter
from copy import deepcopy
import argparse
import json
from pathlib import Path

from repair_editorial_roles import AUDIT, PRIMARY, RETAINED, WORKS, _before, sha, verify

HERODAS_SOURCE = "https://archive.org/details/mimesfragments00hero"


def reviewed_run_metadata(row, root):
    """Identify the actual scan copy without inventing a whole-volume OCR run."""
    if row.get("urn") != WORKS[0] or row.get("edition") != "herodas-hk-ocr":
        return {}
    current = metadata(root)
    if WORKS[0] not in current:
        return {}
    return {"source_url": HERODAS_SOURCE,
        "scope_note": "Partial historical OCR of Headlam–Knox 1922. The source-role review covers the 21 scan pages represented by the old rows; 13 contain retained authorial text. The pinned source PDF has 542 pages. This does not assert complete OCR coverage of the edition."}


def metadata(root):
    """Combine current body coverage with the independently frozen role review."""
    from herodas_current_state import AUDIT as BODY_AUDIT, body_is_unapplied, role_predecessor_view
    root = Path(root)
    with role_predecessor_view(root) as previous:
        result = _role_metadata(previous)
        if not (root / BODY_AUDIT / "changes.json").is_file() or body_is_unapplied(root):
            return result
        from repair_herodas_body import manifestation_metadata
        recovered = manifestation_metadata(root)
        if set(recovered) - {WORKS[0]} or (recovered and WORKS[0] not in result):
            raise ValueError("Herodas body metadata cannot replace another source-role authority")
        if recovered:
            result[WORKS[0]] = _merge_body_metadata(result[WORKS[0]], recovered[WORKS[0]])
        return result


def _merge_body_metadata(previous, current):
    """Keep historical partition counts separate from expanded primary coverage."""
    result = {**deepcopy(previous), **deepcopy(current)}
    editions = {edition["key"]: deepcopy(edition) for edition in previous["editions"]}
    editions.update({edition["key"]: deepcopy(edition) for edition in current["editions"]})
    result["editions"] = list(editions.values())
    old = previous["coverage_composition"]
    coverage = {**deepcopy(old), **deepcopy(current["coverage_composition"])}
    components = {(item["edition"], item["storage"], item["path"]): deepcopy(item)
                  for item in old["components"]}
    components.update({(item["edition"], item["storage"], item["path"]): deepcopy(item)
                       for item in current["coverage_composition"]["components"]})
    coverage["components"] = list(components.values())
    coverage["source_role_review"] = deepcopy(old)
    result["coverage_composition"] = coverage
    return result


def _role_metadata(root):
    root = Path(root)
    path = root / AUDIT / "changes.json"
    if not path.exists():
        return {}
    audit = json.loads(path.read_bytes())
    _before(root, audit)
    from citation_alias_state import role_is_unapplied
    if role_is_unapplied(root):
        return {}
    verify(root)
    sources = {
        WORKS[0]: {"key": "herodas-hk-ocr", "name": "Headlam–Knox 1922, retained Herodas verse passages",
            "editor": "Headlam, Walter; Knox, Alfred", "year": 1922, "license": "PD", "provider": "ocr",
            "source": HERODAS_SOURCE, "paratext_key": "headlam-knox-editorial",
            "note": "Partial historical OCR, with headings, speaker labels, apparatus, and commentary separated by source role. Missing pages and OCR spellings have not been restored or comprehensively reviewed."},
        WORKS[1]: {"key": "1st1K-grc1", "name": "First1KGreek, Hipponax fragment 128 (Brandt 1888)",
            "editor": "Brandt, Paul", "year": 1888, "license": "CC-BY-SA-4.0", "provider": "first1k",
            "source": "https://archive.org/details/corpusculumpoesi01lipsuoft", "paratext_key": "brandt1888-editorial",
            "note": "Only the verse in TEI section frag128 is authorial primary text. Homeric parallels, external testimony, variants, and commentary remain separately citable. This is not a complete edition of all Hipponax fragments."},
    }
    result = {}
    for work, source in sources.items():
        counts = audit["counts"][work]
        outside = [json.loads(line) for line in (root / RETAINED[work]).read_bytes().splitlines()]
        roles = dict(sorted(Counter(row["editorial_role"] for row in outside).items()))
        base = {key: source[key] for key in ("key", "name", "editor", "year", "license", "provider", "source", "note")}
        base.update(scheme="scan-page.row" if work == WORKS[0] else "section", storage="primary", servable=True)
        paratext = dict(base, key=source["paratext_key"], name=source["name"] + ", excluded edition material",
                        storage="paratext", servable=False)
        result[work] = {"editions": [base, paratext], "default_edition": source["key"],
            "coverage_composition": {"policy": "source-reviewed-editorial-role-partition",
                "manifest": f"{AUDIT}/changes.json", "manifest_sha256": sha(path.read_bytes()),
                "qualification": audit["qualification"], "counts": counts,
                "primary_quality": {"status": "source-role-reviewed", "passages": counts["primary_rows"], "note": source["note"]},
                "components": [{"edition": source["key"], "storage": "primary", "path": PRIMARY[work],
                    "passages": counts["primary_rows"], "role": "authorial-verse", "license": source["license"], "source": source["source"]},
                    {"edition": source["paratext_key"], "storage": "paratext", "path": RETAINED[work],
                    "passages": counts["retained_spans"], "role": "editorial-material", "roles": roles,
                    "license": source["license"], "source": source["source"]}]}}
    return result


def sync_source_inventory(root, *, write=False):
    """Regenerate the edition-to-scan binding from the active review authority."""
    root = Path(root)
    if WORKS[0] not in metadata(root):
        return
    path = root / "data/inventory/ocr_edition_sources.json"
    current = json.loads(path.read_bytes())
    wanted = dict(current)
    wanted["herodas-hk-ocr"] = dict(current["herodas-hk-ocr"],
        label="Herodas, ed. Headlam–Knox 1922 (reviewed scan copy)", url=HERODAS_SOURCE)
    if current != wanted:
        if not write:
            raise ValueError("Herodas source inventory differs from the reviewed scan copy")
        path.write_text(json.dumps(wanted, ensure_ascii=False, indent=1) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    sync_source_inventory(args.root, write=args.write)
