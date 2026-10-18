#!/usr/bin/env python3
"""Reproduce the Kaibel page and token concordance without changing reader text.

--write saves a hash-pinned reversible frequency projection and all unresolved
readings. --check verifies those generated artifacts. --unapply removes only
this projection after checking that it has not changed. Original primary and
secondary witnesses remain byte-identical throughout.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import difflib
import hashlib
import itertools
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
SLUGS = {s: f"kaibel-cgf-1899.volume-witness-{s}" for s in "rs"}
CARVES = {"d": "dinolochus.fragmentum", "b": "blaesus.fragmentum", "f": "sophron.fragmenta"}
TOKEN = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+(?:['’ʼ´`ʹ])?")
OUTPUT = "data/frequency_projection.json"
CONCORDANCE = "data/ocr_collations/kaibel-1899.json"
AUDIT = "data/corpus_changes/kaibel-witness-collation/changes.json"
# These damaged pages fall below the candidate threshold. Their distinct
# incipits and surrounding leaves were checked together, not inferred by offset.
REVIEWED_PAIRS = [(138, 132), (156, 150), (227, 221), (271, 265), (274, 268), (274, 274)]
EVIDENCE = {
    "source_url": "https://archive.org/details/comicorvmgraeco00kaibgoog",
    "pdf_sha256": "59f1e3751f1eb18c25789ccbec3a2e491a2be171198ef87d3480f9789a2a31e5",
    "checked_scan_pages": [27, 29, 65, 164, 220, 277],
    "method": "Compare page contents, including distinctive incipits, fragment numbers and neighboring leaves. OCR page keys drift and are not source scan page numbers. Match exact runs across arbitrary row pairs to tolerate interleaved columns and paragraph/line segmentation. No OCR witness wins a disagreement.",
    "reviewed_pair_evidence": {
        "r138:s132": "Shared Epicharmus Tria(k)ades and Troes fragments 115/129; damaged segmentation.",
        "r156:s150": "Scan 156, printed page 133, begins [Epicharmus] Poemata and includes the separately headed Pseudepicharmeia; S retains only those headings.",
        "r227:s221": "Shared Tarentine glosses beginning Hesychius 56, ἀλανέως; intervening glosses differ in OCR coverage.",
        "r271:s265": "Same omicron index leaf from ἄμνε through ὀφθαλμούς; S has systematic breathing/accent loss.",
        "r274:s268": "Same pi index leaf beginning ἔπρισεν, προδιδόμεν, προῆχε; interleaved columns.",
        "r274:s274": "A further reading of that pi index leaf, with the same fragment references and interleaved columns.",
    },
}


def dump(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_pages(root):
    pages, hashes = {}, {}
    for witness, slug in {**SLUGS, **CARVES}.items():
        path = root / "data/corpus" / (slug + ".jsonl")
        raw = path.read_bytes()
        hashes[path.name] = sha(raw)
        groups = defaultdict(list)
        for line in raw.splitlines():
            rec = json.loads(line)
            number = int(rec["locus"]) if witness == "f" else int(rec["locus"].rsplit("_", 1)[1].split(".")[0])
            groups[number].append(rec)
        for number, rows in groups.items():
            rows.sort(key=lambda r: int(r["locus"].rsplit(".", 1)[-1]))
            tokens = []
            row_tokens = []
            for row in rows:
                indexes = []
                for match in TOKEN.finditer(row["text"]):
                    indexes.append(len(tokens))
                    tokens.append({"locus": row["locus"], "start": match.start(),
                        "end": match.end(), "form": unicodedata.normalize("NFC", match[0])})
                row_tokens.append(indexes)
            pages[witness + str(number)] = {"work": slug, "page": number,
                "rows": rows, "tokens": tokens, "row_tokens": row_tokens}
    return pages, hashes


def page_pairs(pages):
    counters = {key: Counter(t["form"] for t in p["tokens"]) for key, p in pages.items()}
    pairs = []
    for a, b in itertools.combinations(pages, 2):
        if a[0] != "r" or b[0] != "s" or abs((int(a[1:]) - int(b[1:])) - 6) > 12:
            continue
        shared = sum((counters[a] & counters[b]).values())
        denominator = min(sum(counters[a].values()), sum(counters[b].values()))
        score = shared / max(denominator, 1)
        if shared >= 8 and score >= .55:
            pairs.append({"a": a, "b": b, "shared_tokens": shared,
                "containment": round(score, 6), "evidence": "distinctive page-content alignment"})
    existing = {(x["a"], x["b"]) for x in pairs}
    for r, s in REVIEWED_PAIRS:
        a, b = "r" + str(r), "s" + str(s)
        if (a, b) not in existing:
            pairs.append({"a": a, "b": b, "shared_tokens": sum((counters[a] & counters[b]).values()),
                "evidence": EVIDENCE["reviewed_pair_evidence"][a + ":" + b]})
    for a, b in [("d172", "s166"), ("d173", "s167"), ("d174", "s168"),
                 ("b208", "r214"), ("b208", "s214")]:
        pairs.append({"a": a, "b": b, "evidence": "Same source leaf in the separately carved author file; locus prefix and distinctive text checked against the anthology witnesses."})
    # Sophron's old fragment cutter joined neighboring scan rows, sometimes
    # duplicating their common tail/head. Anchor each fragment to its strongest
    # source-page match and adjacent leaves, rather than treating fragment
    # numbers as if they were scan numbers.
    for a in [key for key in pages if key.startswith("f")]:
        for witness, lo, hi in [("r", 175, 207), ("s", 169, 201)]:
            candidates = []
            for b in pages:
                if b[0] != witness or not lo <= int(b[1:]) <= hi:
                    continue
                matches = token_pairs(pages[a], pages[b])
                if len(matches) >= 4:
                    candidates.append((len(matches), b))
            if not candidates:
                continue
            best_n, best = max(candidates)
            for count, b in candidates:
                if count >= max(4, best_n * .25) and abs(int(b[1:]) - int(best[1:])) <= 2:
                    pairs.append({"a": a, "b": b, "aligned_candidate_tokens": count,
                        "evidence": "Exact token runs from the carved Sophron fragment align to this source leaf or its immediate neighbor."})
    return pairs


def token_pairs(a, b):
    """Exact runs within row pairs, plus runs over the full page token stream.

    Rows may be whole paragraphs or line fragments. Matching row pairs in any
    order accommodates a page whose columns were interleaved differently. A
    token occurrence is consumed at most once in a pair, even if the same
    formula occurs several times on that page.
    """
    proposals = []
    for ai, bi in [(list(range(len(a["tokens"]))), list(range(len(b["tokens"]))))] + list(
            itertools.product(a["row_tokens"], b["row_tokens"])):
        if not ai or not bi:
            continue
        av, bv = [[p["tokens"][i]["form"] for i in ids] for p, ids in [(a, ai), (b, bi)]]
        if len(set(av) & set(bv)) < 2:
            continue
        for match in difflib.SequenceMatcher(None, av, bv, autojunk=False).get_matching_blocks():
            # Complete identical short rows are also evidence, but a lone
            # common word inside unrelated text is not an aligned attestation.
            if match.size >= 4 or match.size >= 2 and match.size == len(av) == len(bv):
                proposals.append((match.size, tuple(ai[match.a:match.a + match.size]),
                    tuple(bi[match.b:match.b + match.size])))
    used_a, used_b, accepted = set(), set(), []
    for length, ai, bi in sorted(set(proposals), key=lambda p: (-p[0], p[1], p[2])):
        for x, y in zip(ai, bi):
            if x not in used_a and y not in used_b:
                used_a.add(x)
                used_b.add(y)
                accepted.append((x, y))
    return sorted(accepted)


def generate(root=ROOT):
    pages, hashes = read_pages(root)
    pairs = page_pairs(pages)
    parent = {k: k for k in pages}
    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k
    matches = []
    token_parent = {}
    token_pages = {}
    def token_find(k):
        if k not in token_parent:
            token_parent[k] = k
            token_pages[k] = {k[0]}
        if token_parent[k] != k:
            token_parent[k] = token_find(token_parent[k])
        return token_parent[k]
    for pair in pairs:
        a, b = pair["a"], pair["b"]
        parent[find(b)] = find(a)
        tokens = token_pairs(pages[a], pages[b])
        pair["aligned_token_occurrences"] = len(tokens)
        for i, j in tokens:
            x, y = (a, i), (b, j)
            # A connected component cannot identify two occurrences from the
            # same source page as one attestation through another witness.
            fx, fy = token_find(x), token_find(y)
            if fx == fy:
                continue
            members_x = token_pages[fx]
            members_y = token_pages[fy]
            if members_x & members_y:
                continue
            token_parent[fy] = fx
            token_pages[fx] |= token_pages.pop(fy)
            matches.append({"a": {"page": a, **pages[a]["tokens"][i]},
                "b": {"page": b, **pages[b]["tokens"][j]}})
    groups = defaultdict(list)
    for key in pages:
        groups[find(key)].append(key)
    collated = {k for keys in groups.values() if len(keys) > 1 for k in keys}
    unresolved_carves = {k for k in pages if k[0] == "f" and k not in collated}
    projection = {}
    for key in collated | unresolved_carves:
        for row in pages[key]["rows"]:
            projection[pages[key]["work"] + ":" + row["locus"]] = []
    token_groups = defaultdict(list)
    for token in token_parent:
        token_groups[token_find(token)].append(token)
    certain = Counter()
    for tokens in token_groups.values():
        if len(tokens) < 2:
            continue
        page, index = min(tokens, key=lambda t: (0 if t[0][0] in CARVES else 1, t))
        token = pages[page]["tokens"][index]
        projection[pages[page]["work"] + ":" + token["locus"]].append([token["start"], token["end"]])
        certain[token["form"]] += 1
    for spans in projection.values():
        spans.sort()
    alternatives = []
    for keys in sorted(groups.values(), key=lambda a: min(a)):
        if len(keys) < 2 and keys[0] not in unresolved_carves:
            continue
        readings = {}
        for key in sorted(keys):
            unresolved = [t for i, t in enumerate(pages[key]["tokens"])
                if len(token_groups.get(token_find((key, i)), [])) < 2]
            readings[key] = {"work": pages[key]["work"],
                "rows": [{"locus": row["locus"], "text": row["text"]} for row in pages[key]["rows"]],
                "unresolved_tokens": unresolved, "unresolved_count": len(unresolved)}
        upper = Counter()
        for reading in readings.values():
            upper.update(t["form"] for t in reading["unresolved_tokens"])
        alternatives.append({"pages": sorted(keys), "readings": readings,
            "alignment_status": "unresolved-carved-fragment" if len(keys) == 1 else "collated-leaves",
            "unresolved_frequency_bounds": {form: {"lower": 0, "upper": n}
                for form, n in sorted(upper.items())}})
    projection_doc = {"schema_version": 1, "source_sha256": hashes,
        "policy": "Count only aligned agreed token occurrences once on collated leaves; preserve unaligned alternatives outside scalar counts. Unpaired leaves remain countable.",
        "concordance": CONCORDANCE, "rows": dict(sorted(projection.items()))}
    concordance = {"schema_version": 1, "evidence": EVIDENCE, "source_sha256": hashes,
        "page_pairs": pairs, "token_matches": matches, "alternatives": alternatives,
        "single_witness_pages": sorted(set(pages) - collated - unresolved_carves),
        "summary": {"pages": len(pages), "collated_pages": len(collated),
            "page_groups": len(alternatives), "agreed_attestations": sum(certain.values()),
            "unresolved_carved_fragments": len(unresolved_carves),
            "agreed_frequency": dict(sorted(certain.items())),
            "unresolved_source_token_occurrences": sum(v["unresolved_count"]
                for group in alternatives for v in group["readings"].values())}}
    result = {OUTPUT: dump(projection_doc), CONCORDANCE: dump(concordance)}
    audit = {"schema_version": 1, "issue": "https://github.com/open-greek/open-greek-corpus/issues/56",
        "timestamp": "2026-10-18", "source_sha256": hashes,
        "original_text": "Unchanged in the primary and secondary witness files named by source_sha256.",
        "corrected_text": "No reader-text changes; frequency projection described by the token concordance.",
        "evidence": EVIDENCE, "outputs_sha256": {p: sha(v) for p, v in result.items()},
        "undo": "Run scripts/collate_kaibel_witnesses.py --unapply; all reader text is already the original text."}
    result[AUDIT] = dump(audit)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--unapply", action="store_true")
    args = ap.parse_args()
    if args.unapply:
        audit = json.loads((ROOT / AUDIT).read_text())
        for path, expected in audit["outputs_sha256"].items():
            if sha((ROOT / path).read_bytes()) != expected:
                raise SystemExit(f"Refusing to remove changed projection: {path}")
        for path in [*audit["outputs_sha256"], AUDIT]:
            (ROOT / path).unlink()
        return
    outputs = generate()
    for name, raw in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != raw:
                raise SystemExit(f"Stale Kaibel collation: {name}")
        elif args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    summary = json.loads(outputs[CONCORDANCE])["summary"]
    print(json.dumps({k: v for k, v in summary.items() if k != "agreed_frequency"}))


if __name__ == "__main__":
    main()
