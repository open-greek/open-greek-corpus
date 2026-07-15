#!/usr/bin/env python3
"""Split the Cedrenus v2 (913-1057) span out of the raw cogPG.PG122 volume dump
and serve it under the canonical Cedrenus work.

STATE BEFORE: George Cedrenus' Compendium historiarum (tlg3018.tlg001) was served
only as its PG121 half, georgius-cedrenus.compendium-historiarum.jsonl (calfa-co
CGPG OCR, loci 19-590), which ends at the death of the emperor Alexander (913 CE:
"...τὴν βασιλείαν παραδοὺς Κωνσταντίνῳ τῷ οἰκείῳ ἀνεψιῷ"). The 913-1057
continuation lived only inside data/corpus/cogPG.PG122.jsonl, an unsplit whole-
Migne-volume dump (Migne PG tomus 122 = Bonn/CSHB Bekker, Cedrenus vol. 2). That
dump opens at 913 ("...ἀποθανόντος Ἀλεξάνδρου εἰς Κωνσταντῖνον...", loc 12) and,
after the end of Cedrenus, also carries the Scylitzes continuatus and a Psellus
metrical Song-of-Songs commentary.

WHAT THIS DOES: it moves the 913-1057 Cedrenus span (loci 12-189) out of
cogPG.PG122 and appends it to georgius-cedrenus.compendium-historiarum, re-keyed
to the served work's urn with loci "PG122.<page>" (the PG121 half keeps its bare
page loci 19-590, so the volume tag disambiguates the two Migne tomes and avoids a
locus collision). Nothing is OCR'd: the text is moved verbatim; only its urn and
locus change. The residual cogPG.PG122 (loci 190-679: Scylitzes continuatus +
Psellus) is left as the volume dump. Token totals are conserved (moved, not lost).

BOUNDARY (1057, end of the Skylitzes/Cedrenus recension): loc 189 ends the
narrative with Isaac Komnenos' coronation ("...βασιλεὺς αὐτοκράτωρ Ῥωμαίων
ἀναγορεύεται"); loc 190 opens the Scylitzes continuatus, whose incipit "...αὐτίκα
τῷ βασιλικῷ νομίσματι σπαθηφόρος διαχαράττεται..." is verbatim the byzantium.gr
scylitzes-continuatus.continuatio-scylitzae (tlg3064.tlg002) skylitzes0.1. That
continuation (1057-1079) is already served cleanly by byzantium.gr, so it is NOT
folded into Cedrenus and stays in cogPG.PG122.

ATTRIBUTION DECISION (option a): serve the span as the Cedrenus work
(tlg3018.tlg001), because the text IS Cedrenus' Compendium historiarum vol. 2. For
811-1057 that text is verbatim-equivalent to Ioannes Skylitzes' Synopsis
historiarum (tlg3063.tlg001); byzantium.gr's Skylitzes (joannes-scylitzes.
synopsis-historiarum) covers only through 912, so this fills the 913-1057 gap in
the Skylitzes-recension content while keeping the accurate Cedrenus label rather
than silently relabeling Cedrenus as Skylitzes. The Skylitzes overlap is noted in
the provenance/audit, not encoded by relabeling.

CORRECTIONS MIRROR: data/corrections_log/applied.jsonl keys cogPG.PG122
corrections by bare column locus. scripts/rekey_corrections_log.py deliberately
leaves such cogPG.* bare-locus rows unchanged ("they document history and the next
upstream mirror regeneration supersedes them"), so this script does NOT rewrite
the mirror. The exact locus mapping (cogPG.PG122 N -> georgius-cedrenus PG122.N,
N in 12..189) is recorded in the audit so the linkage is reconstructable.

A reversible audit is written to data/corpus_changes/ and OCR provenance for the
added PG122 half to data/ocr_provenance/. Idempotent: a second run is a no-op.

Usage:
  split_cedrenus_pg122.py [--cog <repo_root>] [--apply]
      default: --check (validate + print, write nothing)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

DATE = "2026-07-14"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")

SOURCE_URN = "cogPG.PG122"                                  # raw Migne PG122 dump
DEST_URN = "georgius-cedrenus.compendium-historiarum"       # served Cedrenus work
CTS = "urn:cts:greekLit:tlg3018.tlg001"
TLG = "tlg3018.tlg001"
CONT_URN = "scylitzes-continuatus.continuatio-scylitzae"    # byzantium.gr, tlg3064.tlg002
SKYL_URN = "joannes-scylitzes.synopsis-historiarum"         # byzantium.gr, tlg3063.tlg001

# Migne PG122 page loci: 12-189 are Cedrenus vol.2 (913 -> Isaac Komnenos, 1057);
# 190-243 the Scylitzes continuatus; 275-679 the Psellus Song-of-Songs commentary.
LAST_CEDRENUS_LOCUS = 189
FIRST_CONTINUATUS_LOCUS = 190
LOCUS_PREFIX = "PG122."          # tags the moved rows' loci (PG121 half is bare)

# Seam / boundary anchors (verbatim substrings that must be present in the OCR):
INCIPIT_913 = "ἀποθανόντος Ἀλεξάνδρου"          # loc 12, opens Cedrenus vol.2 (913)
CORONATION_1057 = "ἀναγορεύεται"                # loc 189, Isaac Komnenos crowned
CONTINUATUS_INCIPIT = "αὐτίκα τῷ βασιλικῷ νομίσματι"   # loc 190, = byz.gr continuatus


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s))


def greek_tokens(s: str) -> int:
    return sum(1 for t in s.split() if GREEK.search(t))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def dump_rows(rows: list[dict]) -> bytes:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")


def read_rows(fp: Path) -> list[dict]:
    return [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines() if l.strip()]


def git_head_blob_sha256(cog: Path, rel: str) -> str | None:
    try:
        blob = subprocess.run(["git", "-C", str(cog), "show", f"HEAD:{rel}"],
                              check=True, capture_output=True).stdout
    except subprocess.CalledProcessError:
        return None
    return hashlib.sha256(blob).hexdigest()


def rekey(row: dict) -> dict:
    """Move a PG122 Cedrenus row onto the served work; text is byte-identical."""
    return {
        "urn": DEST_URN,
        "edition": row["edition"],
        "locus": f"{LOCUS_PREFIX}{row['locus']}",
        "source": row["source"],
        "license": row["license"],
        "text": row["text"],
    }


def provenance_record(moved: list[dict]) -> dict:
    gc = sum(greek_chars(r["text"]) for r in moved)
    tok = sum(greek_tokens(r["text"]) for r in moved)
    loci = sorted(int(r["locus"]) for r in moved)
    return {
        "urn": DEST_URN,
        "cts": CTS,
        "edition": "cgpg",
        "source": "calfa-co Patrologia Graeca (CC-BY OCR of public-domain Migne PG)",
        "coverage_note": (
            "Two-volume delivery for one work (George Cedrenus, Compendium "
            "historiarum, tlg3018.tlg001). The PG121 half (creation -> 913, loci "
            "19-590) was delivered by the upstream CGPG pipeline. THIS record "
            "documents the PG122 half (913 -> 1057, loci PG122.12..PG122.189) split "
            "out of the raw cogPG.PG122 volume dump and appended by "
            "scripts/split_cedrenus_pg122.py. The PG121 half's served bytes are "
            "unchanged; the PG122 rows are appended after them."
        ),
        "source_scan": {
            "edition_printed": "Migne, Patrologia Graeca, tomus 122 (George "
            "Cedrenus, Compendium historiarum vol. 2 = Bonn/CSHB Bekker 1839)",
            "source": "calfa-co Patrologia Graeca OCR of the public-domain Migne scan",
            "source_url": "https://github.com/calfa-co/Patrologia-Graeca",
            "volume_loci_kept": f"{loci[0]}-{loci[-1]} (of the PG122 dump's 12-679)",
        },
        "model": "calfa-co",
        "layout_handling": {
            "method": "Migne two-column page, Greek text with facing Latin "
            "translation; the CGPG OCR keeps the Greek column",
            "columns": 2,
            "provenance": "text taken verbatim from the delivered cogPG.PG122 rows; "
            "no re-OCR was performed by this split",
        },
        "segmentation": "one served record per calfa-co page of the PG122 volume; "
        "the volume's bare page locus N is re-keyed 'PG122.N' so the two Migne tomes "
        "(PG121 bare loci 19-590, PG122 'PG122.*') do not collide within the work.",
        "work_boundary": {
            "span": "913 CE (death of Alexander) -> 1057 CE (coronation of Isaac I "
            "Komnenos), the extent of the Skylitzes/Cedrenus recension",
            "start": f"loc 12: '{INCIPIT_913}...' (opens Cedrenus vol. 2 at 913)",
            "end": f"loc 189: Isaac Komnenos crowned ('...βασιλεὺς αὐτοκράτωρ "
            f"Ῥωμαίων {CORONATION_1057}')",
            "excluded_after_1057": (
                "loci 190-243 are the Scylitzes continuatus (incipit loc 190 "
                f"'...{CONTINUATUS_INCIPIT} σπαθηφόρος διαχαράττεται...', verbatim = "
                f"{CONT_URN} / tlg3064.tlg002 skylitzes0.1), already served by "
                "byzantium.gr; loci 275-679 are a Psellus metrical Song-of-Songs "
                "commentary. Both remain in cogPG.PG122 and are NOT folded here."
            ),
        },
        "skylitzes_overlap": (
            "For 811-1057, Cedrenus' Compendium historiarum reproduces Ioannes "
            f"Skylitzes' Synopsis historiarum (tlg3063.tlg001) near-verbatim. "
            f"byzantium.gr's Skylitzes ({SKYL_URN}) covers only through 912, so this "
            "PG122 Cedrenus span fills the 913-1057 gap in the Skylitzes-recension "
            "content. It is served under the accurate Cedrenus attribution, not "
            "relabeled as Skylitzes."
        ),
        "counts": {"rows": len(moved), "greek_chars": gc, "tokens": tok},
        "date": DATE,
        "note": "Derived reproducibly by scripts/split_cedrenus_pg122.py from the "
        "in-repo cogPG.PG122 dump. Re-running the script reproduces these rows.",
    }


def audit_record(old_dest: bytes, old_src: bytes,
                 new_dest: bytes, new_src: bytes,
                 moved: list[dict], residual: list[dict],
                 old_dest_rows: int, old_src_rows: int) -> dict:
    moved_tok = sum(greek_tokens(r["text"]) for r in moved)
    moved_gc = sum(greek_chars(r["text"]) for r in moved)
    resid_tok = sum(greek_tokens(r["text"]) for r in residual)
    loci = sorted(int(r["locus"]) for r in moved)
    return {
        "_meta": {
            "change": "split the Cedrenus v2 (913-1057) span out of the raw "
            "cogPG.PG122 volume dump and serve it under the canonical Cedrenus work",
            "moved_from": SOURCE_URN,
            "moved_to": DEST_URN,
            "cts": CTS,
            "applied_by": "scripts/split_cedrenus_pg122.py",
            "date": DATE,
            "attribution_decision": (
                "Served as the Cedrenus work (tlg3018.tlg001), the accurate label: "
                "the text IS Cedrenus' Compendium historiarum vol. 2 (Migne PG122 / "
                "Bonn Bekker). For 811-1057 it is verbatim-equivalent to Skylitzes' "
                "Synopsis historiarum (tlg3063.tlg001); byzantium.gr's Skylitzes "
                "stops at 912, so this fills the 913-1057 gap without relabeling "
                "Cedrenus as Skylitzes. The post-1057 Scylitzes continuatus and the "
                "Psellus Song-of-Songs commentary in the same volume are excluded "
                "(the continuatus is already served by byzantium.gr, tlg3064.tlg002)."
            ),
            "reversible": (
                "The PG121 half is byte-unchanged: the moved rows are appended to it "
                "with loci 'PG122.<page>'. To revert: drop every "
                f"data/corpus/{DEST_URN}.jsonl row whose locus starts '{LOCUS_PREFIX}' "
                "and re-insert it into data/corpus/cogPG.PG122.jsonl with locus "
                "= locus without the 'PG122.' prefix (page order 12..189), then "
                "restore data/cgpg_works.json's PG122 entry. Equivalently: git revert "
                "the commit, or restore both files from the parent commit and confirm "
                "their sha256 equal old.*.sha256 below. Every moved row is byte-"
                "identical in text; only urn and locus changed."
            ),
        },
        "boundary_evidence": {
            "first_moved_loc12": INCIPIT_913,
            "last_moved_loc189": CORONATION_1057,
            "first_residual_loc190": CONTINUATUS_INCIPIT
            + " (= byzantium.gr scylitzes-continuatus skylitzes0.1)",
        },
        "old": {
            SOURCE_URN: {"rows": old_src_rows, "greek_tokens": 224974,
                         "sha256": sha256_bytes(old_src)},
            DEST_URN: {"rows": old_dest_rows, "greek_tokens": 220540,
                       "sha256": sha256_bytes(old_dest)},
        },
        "moved": {
            "rows": len(moved),
            "greek_chars": moved_gc,
            "greek_tokens": moved_tok,
            "volume_loci": f"{loci[0]}-{loci[-1]}",
            "locus_map": f"cogPG.PG122 locus N -> {DEST_URN} locus '{LOCUS_PREFIX}N' "
            f"for N in {loci[0]}..{loci[-1]} (Migne PG122 pages)",
        },
        "new": {
            SOURCE_URN: {"rows": len(residual), "greek_tokens": resid_tok,
                         "scope": "residual: Scylitzes continuatus (190-243) + "
                         "Psellus Song-of-Songs commentary (275-679)",
                         "sha256": sha256_bytes(new_src)},
            DEST_URN: {"rows": old_dest_rows + len(moved),
                       "greek_tokens": 220540 + moved_tok,
                       "scope": "PG121 (creation-913) + PG122 (913-1057)",
                       "sha256": sha256_bytes(new_dest)},
        },
        "corrections_mirror_note": (
            "data/corrections_log/applied.jsonl keys the moved span's corrections by "
            "bare column locus under cogPG.PG122; per the rekey_corrections_log.py "
            "convention for cogPG.* bare-locus rows they are left unchanged "
            "(historical, superseded on the next upstream mirror regeneration). The "
            "locus map above makes the linkage reconstructable."
        ),
        "cgpg_works_update": (
            "data/cgpg_works.json PG122 entry: works cleared (Cedrenus now served "
            "directly via its own key), desc + n_passages/n_tokens set to the residual."
        ),
        "provenance": f"data/ocr_provenance/{DEST_URN}.json",
        "source": "Cedrenus PG122 (913-1057) split, " + DATE,
    }


def update_cgpg_works(cog: Path, residual: list[dict], apply: bool) -> str:
    fp = cog / "data" / "cgpg_works.json"
    vols = json.loads(fp.read_text(encoding="utf-8"))
    for vol in vols:
        if vol.get("volume") == "PG122" and vol.get("urn") == SOURCE_URN:
            vol["desc"] = ("Scylitzes continuatus + Psellus (Cedrenus v2 913-1057 "
                           "split to " + DEST_URN + " / " + TLG + ")")
            vol["n_passages"] = len(residual)
            vol["n_tokens"] = sum(greek_tokens(r["text"]) for r in residual)
            vol["works"] = []
            break
    else:
        return "cgpg_works.json: PG122 entry NOT FOUND (skipped)"
    if apply:
        fp.write_text(json.dumps(vols, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")
    return (f"cgpg_works.json PG122 -> works=[], n_passages={len(residual)}, "
            f"n_tokens={sum(greek_tokens(r['text']) for r in residual)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cog", type=Path, default=Path(__file__).resolve().parent.parent,
                    help="corpus repo root (default: this script's repo)")
    ap.add_argument("--apply", action="store_true",
                    help="write files; default is check-only")
    args = ap.parse_args()

    cog = args.cog
    corpus = cog / "data" / "corpus"
    src_fp = corpus / f"{SOURCE_URN}.jsonl"
    dest_fp = corpus / f"{DEST_URN}.jsonl"
    errors: list[str] = []

    for fp in (src_fp, dest_fp):
        if not fp.exists():
            errors.append(f"missing corpus file: {fp}")
    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1

    old_src = src_fp.read_bytes()
    old_dest = dest_fp.read_bytes()
    src_rows = read_rows(src_fp)
    dest_rows = read_rows(dest_fp)

    # --- guards: clean tree (served files match git HEAD)
    for rel, sha in ((f"data/corpus/{SOURCE_URN}.jsonl", sha256_bytes(old_src)),
                     (f"data/corpus/{DEST_URN}.jsonl", sha256_bytes(old_dest))):
        head = git_head_blob_sha256(cog, rel)
        if head is not None and head != sha:
            errors.append(f"{rel}: file != git HEAD blob (uncommitted change?)")

    # --- guard: idempotency (already split?)
    if any(str(r["locus"]).startswith(LOCUS_PREFIX) for r in dest_rows):
        errors.append(f"{DEST_URN}: '{LOCUS_PREFIX}' loci already present (already applied?)")

    # --- guard: source loci are bare integers as expected
    if not all(str(r["locus"]).isdigit() for r in src_rows):
        errors.append(f"{SOURCE_URN}: not all loci are bare integers")

    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1

    moved = [r for r in src_rows if int(r["locus"]) <= LAST_CEDRENUS_LOCUS]
    residual = [r for r in src_rows if int(r["locus"]) >= FIRST_CONTINUATUS_LOCUS]

    # --- guard: partition is exact and non-trivial
    if len(moved) + len(residual) != len(src_rows):
        errors.append("partition drops/overlaps rows (loci between "
                      f"{LAST_CEDRENUS_LOCUS} and {FIRST_CONTINUATUS_LOCUS}?)")
    if not moved or not residual:
        errors.append(f"empty partition: moved={len(moved)} residual={len(residual)}")

    # --- guard: seam anchors pin the 913 / 1057 boundary
    if moved:
        first_moved = min(moved, key=lambda r: int(r["locus"]))
        last_moved = max(moved, key=lambda r: int(r["locus"]))
        if INCIPIT_913 not in first_moved["text"]:
            errors.append(f"loc {first_moved['locus']}: missing 913 incipit '{INCIPIT_913}'")
        if int(last_moved["locus"]) != LAST_CEDRENUS_LOCUS or CORONATION_1057 not in last_moved["text"]:
            errors.append(f"loc {last_moved['locus']}: missing 1057 coronation marker '{CORONATION_1057}'")
    if residual:
        first_resid = min(residual, key=lambda r: int(r["locus"]))
        if int(first_resid["locus"]) != FIRST_CONTINUATUS_LOCUS or CONTINUATUS_INCIPIT not in first_resid["text"]:
            errors.append(f"loc {first_resid['locus']}: missing continuatus incipit '{CONTINUATUS_INCIPIT}'")

    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1

    # --- build new bytes
    moved_rekeyed = [rekey(r) for r in moved]
    new_dest = old_dest + dump_rows(moved_rekeyed)     # PG121 untouched, PG122 appended
    new_src = dump_rows(residual)                      # verbatim residual rows

    # --- guard: token conservation (no text lost)
    src_tok = sum(greek_tokens(r["text"]) for r in src_rows)
    moved_tok = sum(greek_tokens(r["text"]) for r in moved)
    resid_tok = sum(greek_tokens(r["text"]) for r in residual)
    if moved_tok + resid_tok != src_tok:
        errors.append(f"token conservation FAILED: {moved_tok}+{resid_tok} != {src_tok}")
    # moved rows keep byte-identical text
    if [r["text"] for r in moved] != [r["text"] for r in moved_rekeyed]:
        errors.append("moved rows' text changed (must be verbatim)")
    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1

    cw_msg = update_cgpg_works(cog, residual, args.apply)

    dest_tok = sum(greek_tokens(r["text"]) for r in dest_rows)
    print(f"moved {len(moved)} rows / {moved_tok} greek tokens (loci "
          f"{min(int(r['locus']) for r in moved)}-{max(int(r['locus']) for r in moved)}) "
          f"{SOURCE_URN} -> {DEST_URN}")
    print(f"{DEST_URN}: {len(dest_rows)} -> {len(dest_rows) + len(moved)} rows, "
          f"{dest_tok} -> {dest_tok + moved_tok} greek tokens")
    print(f"{SOURCE_URN}: {len(src_rows)} -> {len(residual)} rows, "
          f"{src_tok} -> {resid_tok} greek tokens (residual)")
    print(" ", cw_msg)

    if args.apply:
        changes = cog / "data" / "corpus_changes"
        prov_dir = cog / "data" / "ocr_provenance"
        changes.mkdir(parents=True, exist_ok=True)
        prov_dir.mkdir(parents=True, exist_ok=True)
        dest_fp.write_bytes(new_dest)
        src_fp.write_bytes(new_src)
        (changes / f"{DEST_URN}.pg122-cedrenus-split.json").write_text(
            json.dumps(audit_record(old_dest, old_src, new_dest, new_src,
                                    moved, residual, len(dest_rows), len(src_rows)),
                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (prov_dir / f"{DEST_URN}.json").write_text(
            json.dumps(provenance_record(moved), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"APPLIED: rewrote both corpus files + cgpg_works.json (+ audit + provenance)")
    else:
        print("CHECK only (pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
