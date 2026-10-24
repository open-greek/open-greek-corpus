"""Source-reviewed column order for the ten delimiter-bearing Dübner pages.

The decisions concern the order of literal OCR cells, not their spellings.
Sparse duplicated column snippets remain held: a permutation cannot establish
which occurrences refer to the same printed word.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/corpus_changes/dubner-layout-review"
REVIEW = AUDIT + "/source-review.json"
NETWORKS = "data/corpus_changes/dubner-1855-scope/word-networks.json.gz"
SCHEMA = "dubner-source-column-layout-v1"
PAGES = {
    "equites:0094": (94, 95), "equites:0101": (101, 102),
    "equites:0107": (107, 108), "equites:0109": (109, 110),
    "pax:0229": (229, 256), "pax:0245": (245, 272),
    "aves:0254": (254, 281), "aves:0271": (271, 298),
    "ranae:0316": (316, 343), "plutus:0415": (415, 440),
}
HELD = {
    "equites:0094": "The OCR combines full column text with partial repeated column snippets. A cell permutation would retain duplicate word occurrences; fragment-level source association is required.",
    "equites:0107": "The right-column snippets repeat parts of a later full transcription of that column. Their truncated readings remain contrary evidence; a permutation alone cannot deduplicate their votes.",
    "aves:0271": "Truncated right-column cells coexist with a full right-column transcription. The exact occurrence association and treatment of partial readings require a separate fragment review.",
}
EXPLANATIONS = {
    "equites:0101": "Both columns are populated on all 54 OCR lines. Read the complete left column before the right column, as printed.",
    "equites:0109": "Both columns are populated on all 54 OCR lines. Read the complete left column before the right column, as printed.",
    "plutus:0415": "Both columns are populated on all 54 OCR lines. Read the complete left column before the right column, as printed.",
    "aves:0254": "Rows 1–53 hold the left column. Its final συμ- continues with βολαῖς in the right cell of row 1. The first two right cells precede the right-column text stored in left cells 54–103; trailing pipes do not prove those are left-column readings.",
    "pax:0229": "The unmarked final line continues scholium 634 at the bottom of the right column. It follows all right cells, not the bottom of the left column.",
    "pax:0245": "The two unmarked final lines are the right-column ending headed 1096 Σίβυλλα, misnumbered 1086 by OCR. They follow the right cells; no numeral or spelling is changed by this order decision.",
    "ranae:0316": "The left column contains the end of the prior introduction and section IV. Section IV continues through the right cells and unmarked lines 18–24. The scholia below the right-column heading follow as left cells 54–74. Excluded printed headings remain excluded.",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode()


def image_path(scan, page):
    return f"{AUDIT}/pages/{scan}-{page:04d}.png"


def order_for(key, witness):
    from experiment_dubner_alignment import column_order
    if key in {"equites:0101", "equites:0109", "plutus:0415"}:
        if len(witness["text"].splitlines()) != 54:
            raise ValueError("Reviewed uniform column row count changed")
        return column_order(witness)
    if key == "aves:0254":
        return ([[i, "left"] for i in range(1, 54)] + [[i, "right"] for i in (1, 2)]
                + [[i, "left"] for i in range(54, 104)])
    if key in {"pax:0229", "pax:0245"}:
        trailing = [54] if key == "pax:0229" else [54, 55]
        return ([[i, side] for side in ("left", "right") for i in range(1, 54)]
                + [[i, "whole"] for i in trailing])
    if key == "ranae:0316":
        return ([[i, "left"] for i in range(1, 18)]
                + [[i, "left"] for i in range(25, 54)]
                + [[i, "right"] for i in range(1, 18)]
                + [[i, "whole"] for i in range(18, 25)]
                + [[i, "left"] for i in range(54, 75)])
    raise ValueError("This page has no approved column permutation")


def compile_review(root, files, reviewed_at):
    from dubner_witness_alignment import SOURCE_SCANS
    from experiment_dubner_alignment import candidate, line_cells, route_witness
    root = Path(root)
    raw = (root / NETWORKS).read_bytes()
    networks = json.loads(gzip.decompress(raw))
    descriptions = {(key, witness["id"]): candidate(witness)
        for key, result in networks.items() for witness in result["ocr_consensus"]["witnesses"]
        if candidate(witness) is not None}
    if {key for key, _ in descriptions} != set(PAGES) or len(descriptions) != len(PAGES):
        raise ValueError("The complete delimiter-bearing page inventory changed")
    file_map = {item["path"]: item["sha256"] for item in files}
    expected_paths = {image_path(scan, pages[index]) for pages in PAGES.values()
                      for index, scan in enumerate(("toronto", "harvard"))}
    if len(files) != len(expected_paths) or set(file_map) != expected_paths:
        raise ValueError("Every reviewed layout needs both retained source pages")
    decisions, held = {}, []
    for (key, identifier), description in sorted(descriptions.items()):
        toronto, harvard = PAGES[key]
        evidence = {"method": "Direct inspection of the printed columns in both pinned scans",
            "reviewed_at": reviewed_at,
            "source_pages": [{"scan": scan, "pdf_page": page,
                "pdf_sha256": SOURCE_SCANS[scan]["sha256"],
                "capture": image_path(scan, page), "capture_sha256": file_map[image_path(scan, page)]}
                for scan, page in (("toronto", toronto), ("harvard", harvard))],
            "qualification": "Reading order only; no OCR spelling or independent voter is inferred."}
        if key in HELD:
            held.append({"page_key": key, "witness_id": identifier,
                "reason": HELD[key], "evidence": evidence, "candidate": description})
            continue
        witness = next(w for w in networks[key]["ocr_consensus"]["witnesses"] if w["id"] == identifier)
        evidence["observation"] = EXPLANATIONS[key]
        expected_rows = {"aves:0254": 103, "pax:0229": 54, "pax:0245": 55,
                         "ranae:0316": 74}.get(key, 54)
        if len(witness["text"].splitlines()) != expected_rows:
            raise ValueError("Reviewed layout row count changed: " + key)
        nonblank = {(part["line"], part["cell"]) for part in line_cells(witness)
                    if part["cell"] not in {"delimiter", "line-ending"} and part["text"].strip()}
        order = [item for item in order_for(key, witness) if tuple(item) in nonblank]
        decision = {"approved": True, "reading_order": order, "evidence": evidence}
        route_witness(witness, key, decision)  # every nonblank source cell must survive
        decisions.setdefault(key, {})[identifier] = decision
    return {"schema": SCHEMA, "reviewed_at": reviewed_at,
        "baseline": {"path": NETWORKS, "sha256": sha(raw)},
        "sources": [{"id": scan, **SOURCE_SCANS[scan]} for scan in ("toronto", "harvard")],
        "files": files, "decisions": decisions, "held": held,
        "qualification": "Seven source-reviewed cell permutations and three held partial-duplicate layouts; not a census of OCR spelling accuracy."}


def build(root=ROOT):
    root = Path(root)
    path = root / REVIEW
    stored = json.loads(path.read_bytes())
    expected = compile_review(root, stored["files"], stored["reviewed_at"])
    if stored != expected:
        raise ValueError("Dübner layout observations do not reproduce their frozen review")
    for item in stored["files"]:
        name = Path(item["path"])
        if name.is_absolute() or ".." in name.parts or not name.as_posix().startswith(AUDIT + "/pages/"):
            raise ValueError("Unsafe Dübner layout capture path")
        if sha((root / name).read_bytes()) != item["sha256"]:
            raise ValueError("Dübner layout source capture changed: " + str(name))
    return stored
