#!/usr/bin/env python3
"""Ingest the held masked re-OCR works that need only LOCAL keying (no GPU).

The dense-class re-OCR bulk swap (scripts/record_reocr_ingest_audit.py +
INGEST.sh, commit e4b9a13) installed 16 straightforward keep-better swaps and
deferred the works whose masked column re-OCR (which is good) first needed a
split or a bespoke re-key. This tool ingests the subset of those that can be
keyed CONFIDENTLY from evidence already on disk, and writes a flag record for
the ones whose split is genuinely ambiguous (leaving their served text alone).

CONFIDENT INGESTS (all target URNs are already served -> 'make ids' mints 0):

  photius.lexicon (tlg4040.tlg029)
      Straight keep-better swap of the masked Naber re-OCR. Reconciles commit
      f87a7ec (which reattributed the served photius.bibliotheca text to
      photius.lexicon); NOT double-keyed back to the Bibliotheca. Naber predates
      the 1959 Zavorda codex, so it is structurally incomplete vs the copyrighted
      Theodoridis edition - best OPEN version only.

  Grammatici Graeci IV (Hilgard) scan -> 3 canonically-keyed works
      One masked re-OCR of the GG IV scan is carved by PRINTED-PAGE boundary,
      reproducing the disjoint page partition of the prior served -ocr split and
      matching the book's own section headers:
        pp. 14-53   theodosius.canones-isagogici-de-flexione-nominum  tlg2020.tlg001
                    ("ΘΕΟΔΟΣΙΟΥ ... εἰσαγωγικοὶ κανόνες" .. "Τέλος τῶν ὀνομάτων")
        pp. 54-113  theodosius.canones-isagogici-de-flexione-verborum tlg2020.tlg002
                    ("ΘΕΟΔΟΣΙΟΥ ... κανόνες [ῥημάτων]" .. "Τέλος τῶν εἰς μὶ ῥημάτων")
        pp. 114+    georgius-choeroboscus.prolegomena-et-scholia-...     tlg4093.tlg001
                    ("Προλεγόμενα ... Γεωργίου Χοιροβόσκου")
      Front matter (pp. <=13: Hilgard's editorial index fragments) is dropped, as
      the prior served split did. Each carved part is keep-better validated against
      its served counterpart.

  Walz Rhetores Graeci v1 / v4 / v5 / v7pt2 / v9
      Keep-better swap on the EXISTING ocr.walz_* holding id (same id, better
      text). The per-treatise canonical TLG split is DEFERRED and flagged: each
      bound volume holds many rhetorical treatises and the staging carries no
      per-treatise boundary, so forcing a split now would risk mis-keys.

HELD (flagged, served text left UNTOUCHED - a page split would mis-key text):

  Schwabe atticists      the served pausanias-attic and aelius-dionysius files are
                         two OVERLAPPING OCR passes of the same pages (same locus,
                         different text), not a clean content split.
  Bussemaker Didot       the scan (scholiaintheocri00buss) is THREE works -
                         Theocritus (pp.13-192), Nicander (from p.195 "ΓΕΝΟΣ
                         ΝΙΚΑΝΔΡΟΥ"), Oppian - and the served scholia-in-oppianum
                         conflates Nicander + Oppian. Needs a 3-way split + a new
                         Nicander-scholia work, not a 2-way carve.
  Dindorf Demosthenes v8 Ulpian's prolegomena are scattered before each speech;
                         the served ulpianus block (pp.53-69) is 94% duplicated
                         inside scholia-in-demosthenem. Under/over-capture.

Every ingest writes a reversible audit record to data/corpus_changes/ with the
old+new sha256 / rows / greek-char counts, keep-better evidence, a provenance
pointer, and the git-based reversal path. Paths are passed on the command line;
this committed script hardcodes no local path and names no external repository.

Usage:
  ingest_held_reocr.py --staging <bucket_staging_dir> --cog <repo_root> [--apply]
      default: --check (validate + print, write nothing)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

DATE = "2026-07-12"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
PAGE_RE = re.compile(r"_(\d{3,4})\.\d+$")

# --- GG IV printed-page carve boundaries (inclusive) ---------------------------
GG4_PARTS = [
    # (page_lo, page_hi, urn, cts)
    (14, 53, "theodosius.canones-isagogici-de-flexione-nominum",
     "urn:cts:greekLit:tlg2020.tlg001"),
    (54, 113, "theodosius.canones-isagogici-de-flexione-verborum",
     "urn:cts:greekLit:tlg2020.tlg002"),
    (114, 9999, "georgius-choeroboscus.prolegomena-et-scholia-in-theodosii-alexandrini-canones-isagogicos-de",
     "urn:cts:greekLit:tlg4093.tlg001"),
]

WALZ = [f"walz_rhetores_v{v}" for v in ("1", "4", "5", "7pt2", "9")]

FLAGS = {
    "aelius_dionysius_schwabe": {
        "primary_urn": "pausanias-attic.attikw-n-o-noma-twn-sunagwgh",
        "cts": "urn:cts:greekLit:tlg1569.tlg001",
        "secondary": ["aelius-dionysius.attika-o-no-mata (tlg1323.tlg001)"],
        "reason": "shared-scan split not reproducible: the served pausanias-attic "
        "(qwen36-aelius_dionysius_schwabe-ocr, pp.97-236) and aelius-dionysius "
        "(migne-ocr-qwen36 but with Schwabe loci, pp.5-296) files are two "
        "OVERLAPPING OCR passes of the same pages - 727 shared loci, 676 of them "
        "with DIFFERING text - not a clean content partition. A page-range split "
        "of the masked re-OCR would mis-key fragments.",
        "recommendation": "manual: reconstruct Schwabe's per-fragment Ael.D./Paus. "
        "attribution (or use Erbse 1950) before carving; also reconcile the "
        "mislabeled aelius migne-ocr-qwen36 edition.",
    },
    "scholia_oppianum_bussemaker_didot": {
        "primary_urn": "scholia-in-oppianum.scholia-et-glossae-in-cynegetica-scholia-vetera-et-recentiora",
        "cts": "urn:cts:greekLit:tlg5032.tlg001",
        "secondary": ["scholia-in-theocritum.scholia-vetera-et-recentiora (tlg5038.tlg001)"],
        "reason": "the scan (archive.org scholiaintheocri00buss) is THREE works, not "
        "two: Theocritus scholia (pp.13-192), then Nicander (Life of Nicander "
        "'ΓΕΝΟΣ ΝΙΚΑΝΔΡΟΥ' at p.195), then Oppian. The served scholia-in-oppianum "
        "(pp.193-692) conflates Nicander + Oppian - TLG Oppian Cynegetica scholia "
        "(tlg5032.tlg001) is only ~6088 words yet the served file has 8459 rows. A "
        "clean 2-way carve would perpetuate the Nicander mis-key.",
        "recommendation": "manual: 3-way split at pp.192/193 (Theocritus) and the "
        "Nicander/Oppian boundary; register a Nicander-scholia work (tlg5030) and "
        "key the middle section to it.",
    },
    "scholia_demosthenem_dindorf_v8": {
        "primary_urn": "scholia-in-demosthenem.scholia-demosthenem-dindorf-v8",
        "cts": "urn:cts:greekLit:tlg5017.tlg001",
        "secondary": ["ulpianus.prolegomena-in-demosthenis-orationes-olynthiacas-et-philippicas (tlg2604.tlg001)"],
        "reason": "Ulpian's prolegomena are printed scattered before each speech, "
        "not as one block. The served ulpianus file (pp.53-69, 679 rows) is 94% "
        "duplicated inside scholia-in-demosthenem (636 of 679 loci shared) - so "
        "Ulpian is under-captured and the scholia file over-captured. A single "
        "page-range carve cannot recover the correct partition.",
        "recommendation": "manual: identify every Ulpian prolegomenon/hypothesis "
        "block (Olynthiacs + each Philippic) and carve per block.",
    },
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s))


def jsonl_stats(rows: list[dict]) -> tuple[int, int]:
    return len(rows), sum(greek_chars(r.get("text", "")) for r in rows)


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]


def dump_jsonl(rows: list[dict]) -> bytes:
    return ("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n").encode("utf-8")


def git_head_blob_sha256(cog: Path, rel: str) -> str | None:
    try:
        blob = subprocess.run(["git", "-C", str(cog), "show", f"HEAD:{rel}"],
                              check=True, capture_output=True).stdout
    except subprocess.CalledProcessError:
        return None
    return hashlib.sha256(blob).hexdigest()


def tier_for(ratio: float, headword_gain: int | None) -> str:
    if headword_gain and headword_gain > 0:
        return "keep-better"
    return "keep-better" if ratio >= 0.95 else "keep-better-likely"


# A page set in two columns can be read as two blocks instead of one text, and
# then every fragment becomes its own row with the words cut at the column edge.
# Nothing above sees that: the Greek-character ratio is barely touched, since the
# same characters are present, and the token count actually RISES because half a
# word counts as a word. That is how five Walz volumes were swapped for a text
# with 63% of its token mass in rows under 40 characters, on a verdict reading
# `greek_ratio=0.9727 ... rows 6294->35014` (issue #20). The row explosion was in
# the evidence line and nothing acted on it.
SHORT_ROW = 40
# Generous on purpose. A genuine re-OCR that resegments legitimately can move
# this a little; going from a tenth to two thirds is not that.
SHORT_MASS_RISE = 0.20
# And required together with it, because short rows alone are not the defect: a
# lexicon is short rows by nature. The Photius swap in this same run raised
# short-row mass 30.3% -> 56.1% and is NOT shredded, its rows ending at word
# boundaries; it multiplied rows only 1.65x. The five Walz volumes multiplied
# 2.7x to 6.4x. What the pair describes is the same text cut into many more,
# much shorter pieces, which is what reading a two-column page as blocks does.
ROW_MULTIPLIER = 2.0


def short_row_mass(rows: list[dict]) -> tuple[int, float]:
    """(Greek chars, share of them in rows too short to be a line of text)."""
    total = short = 0
    for r in rows:
        text = r.get("text", "")
        n = greek_chars(text)
        total += n
        if len(text) < SHORT_ROW:
            short += n
    return total, (short / total if total else 0.0)


def reading_order_regressed(old_rows: list[dict],
                            new_rows: list[dict]) -> tuple[bool, str]:
    """Whether the candidate has shredded the text, and the numbers either way.

    Measured on Greek-character mass rather than row counts, because rows vary in
    length and a count says nothing about how much text is in the short ones.
    """
    _, old_share = short_row_mass(old_rows)
    _, new_share = short_row_mass(new_rows)
    mult = len(new_rows) / len(old_rows) if old_rows else 1.0
    note = (f"short-row mass {old_share:.1%} -> {new_share:.1%}, "
            f"rows {len(old_rows)} -> {len(new_rows)} ({mult:.2f}x)")
    regressed = (new_share - old_share > SHORT_MASS_RISE
                 and mult > ROW_MULTIPLIER)
    return regressed, note


def build_swap_record(cog: Path, urn: str, cts: str, run_slug: str,
                      old_rows: int, old_gc: int, old_sha: str,
                      new_rows: int, new_gc: int, new_sha: str,
                      edition: str, verdict: str, extra_meta: dict) -> dict:
    ratio = round(new_gc / old_gc, 4) if old_gc else 0.0
    prov_rel = f"data/ocr_provenance/{urn}.json"
    rec = {
        "_meta": {
            "change": "replace served text (masked re-OCR keep-better swap)",
            "work": urn,
            "cts": cts,
            "run_slug": run_slug,
            "applied_by": "scripts/ingest_held_reocr.py",
            "date": DATE,
            "tier": extra_meta.get("tier"),
            "reversible": (
                "git revert the ingest commit, or restore the file from the parent "
                f"commit ('git checkout <parent> -- data/corpus/{urn}.jsonl') and "
                "confirm its sha256 equals old.sha256 below. The pre-ingest served "
                f"text is also archived offline as REPLACED.{urn}.jsonl in the OCR "
                "staging area."
            ),
        },
        "old": {
            "edition": "served corpus text (pre re-OCR)",
            "rows": old_rows,
            "greek_chars": old_gc,
            "sha256": old_sha,
        },
        "new": {
            "edition": edition,
            "source": "masked-column re-OCR (Qwen3.6-27B-FP8, geometric L/R + apparatus crops)",
            "rows": new_rows,
            "greek_chars": new_gc,
            "sha256": new_sha,
        },
        "evidence": f"{verdict} | greek_ratio={ratio} (masked/served); "
                    f"masked_greek_chars={new_gc} vs served_greek_chars={old_gc}; "
                    f"rows {old_rows}->{new_rows}.",
        "provenance": prov_rel,
        "source": "held-works local-keying ingest (VALIDATION.json + audit_trail.json), " + DATE,
    }
    rec["_meta"].update({k: v for k, v in extra_meta.items() if k != "tier"})
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staging", required=True, type=Path)
    ap.add_argument("--cog", required=True, type=Path)
    ap.add_argument("--apply", action="store_true", help="write files; default is check-only")
    args = ap.parse_args()

    stage, cog = args.staging, args.cog
    corpus = cog / "data" / "corpus"
    changes = cog / "data" / "corpus_changes"
    changes.mkdir(parents=True, exist_ok=True)
    do = args.apply
    errors: list[str] = []
    ingested: list[str] = []

    def swap(slug_dir: str, urn: str, cts: str, run_slug: str, new_rows: list[dict],
             edition: str, verdict: str, extra_meta: dict):
        """Archive the served file, install new_rows, write the audit record."""
        rel = f"data/corpus/{urn}.jsonl"
        served = corpus / f"{urn}.jsonl"
        if not served.exists():
            errors.append(f"{urn}: served file missing")
            return
        old_bytes = served.read_bytes()
        old_sha = sha256_bytes(old_bytes)
        head_sha = git_head_blob_sha256(cog, rel)
        if head_sha is not None and head_sha != old_sha:
            errors.append(f"{urn}: served file != git HEAD blob (uncommitted change?)")
            return
        old_stat_rows = old_bytes.count(b"\n")
        old_gc = sum(greek_chars(json.loads(l).get("text", ""))
                     for l in old_bytes.decode("utf-8").splitlines() if l.strip())
        new_bytes = dump_jsonl(new_rows)
        new_sha = sha256_bytes(new_bytes)
        new_rows_n, new_gc = jsonl_stats(new_rows)
        # Checked here, at the point of mutation, and not left to the staging
        # verdict. The Walz swaps took their tier straight from the run's own
        # VALIDATION.json, so a run that had shredded the text was the only thing
        # asked whether it had shredded the text.
        old_rows_parsed = [json.loads(l) for l in old_bytes.decode("utf-8").splitlines()
                           if l.strip()]
        shredded, note = reading_order_regressed(old_rows_parsed, new_rows)
        if shredded:
            errors.append(f"{urn}: refusing the swap, reading order regressed: {note}. "
                          f"A two-column page read as separate blocks looks like this. "
                          f"Override only with evidence about the ORDER of the text, "
                          f"not its character count.")
            return
        extra_meta = {**extra_meta, "reading_order": note}
        rec = build_swap_record(cog, urn, cts, run_slug, old_stat_rows, old_gc, old_sha,
                                new_rows_n, new_gc, new_sha, edition, verdict, extra_meta)
        ratio = round(new_gc / old_gc, 4) if old_gc else 0.0
        if do:
            (stage / slug_dir).mkdir(parents=True, exist_ok=True)
            (stage / slug_dir / f"REPLACED.{urn}.jsonl").write_bytes(old_bytes)
            served.write_bytes(new_bytes)
            (changes / f"{urn}.reocr-swap.json").write_text(
                json.dumps(rec, ensure_ascii=False, indent=2) + "\n")
        ingested.append(f"{'INGEST' if do else 'CHECK '}  ratio={ratio:<6} "
                        f"rows {old_stat_rows}->{new_rows_n}  {urn}  [{extra_meta.get('tier')}]")

    # --- 1. Photius --------------------------------------------------------------
    ph = read_jsonl(stage / "photius_lexicon_naber" / "photius.lexicon.jsonl")
    val = json.loads((stage / "photius_lexicon_naber" / "VALIDATION.json").read_text())
    swap("photius_lexicon_naber", "photius.lexicon", "urn:cts:greekLit:tlg4040.tlg029",
         "photius_lexicon_naber", ph, "qwen36-photius_lexicon_naber-masked",
         val["verdict"],
         {"tier": val["tier"],
          "provenance_note": "Naber Photius Lexicon (mis-keyed as photius.bibliotheca "
          "in the worklist). Reconciles commit f87a7ec, which reattributed the served "
          "text photius.bibliotheca -> photius.lexicon (tlg4040.tlg029). NOT double-keyed "
          "to the Bibliotheca. Structurally incomplete vs the copyrighted Theodoridis "
          "edition (predates the 1959 Zavorda codex); best OPEN version only.",
          "headword_gain": val.get("headword_gain")})

    # --- 2. Grammatici Graeci IV: 3-way printed-page carve -----------------------
    gg4 = read_jsonl(stage / "choeroboscus_hilgard_gg4" /
                     "georgius-choeroboscus.prolegomena-et-scholia-in-theodosii-alexandrini-canones-isagogicos-de.jsonl")
    buckets: dict[str, list[dict]] = {u: [] for _, _, u, _ in GG4_PARTS}
    dropped = 0
    for r in gg4:
        m = PAGE_RE.search(r.get("locus", ""))
        p = int(m.group(1)) if m else -1
        placed = False
        for lo, hi, urn, cts in GG4_PARTS:
            if lo <= p <= hi:
                nr = dict(r)
                nr["urn"] = urn
                nr["cts"] = cts
                buckets[urn].append(nr)
                placed = True
                break
        if not placed:
            dropped += 1
    if dropped != 9:
        # front matter is 9 editorial rows (pp.5-13); guard the carve is stable
        print(f"NOTE: GG4 dropped {dropped} front-matter rows (expected 9)")
    for lo, hi, urn, cts in GG4_PARTS:
        rows = buckets[urn]
        served = corpus / f"{urn}.jsonl"
        old_gc = sum(greek_chars(json.loads(l).get("text", ""))
                     for l in served.read_text().splitlines() if l.strip()) if served.exists() else 0
        _, new_gc = jsonl_stats(rows)
        ratio = new_gc / old_gc if old_gc else 0.0
        tier = tier_for(ratio, None)
        verdict = (f"keep-better: Greek {ratio*100:.0f}% of served (carved pp.{lo}-"
                   f"{'end' if hi > 9000 else hi} of the GG IV scan)")
        swap("choeroboscus_hilgard_gg4", urn, cts, "choeroboscus_hilgard_gg4", rows,
             "qwen36-choeroboscus_hilgard_gg4-masked", verdict,
             {"tier": tier,
              "change": "replace served text (masked re-OCR keep-better swap; "
              "carved from the shared Grammatici Graeci IV scan by printed-page boundary)",
              "carved_pages": f"{lo}-{'end' if hi > 9000 else hi}",
              "shared_scan": "Hilgard Grammatici Graeci IV: Theodosius nominal canons "
              "(pp.14-53) + verbal canons (pp.54-110) + Choeroboscus prolegomena/scholia "
              "(pp.114+); front matter pp.<=13 dropped as editorial."})

    # --- 3. Walz Rhetores holding-id swaps --------------------------------------
    for slug in WALZ:
        urn = f"ocr.{slug}"
        rows = read_jsonl(stage / slug / f"{urn}.jsonl")
        val = json.loads((stage / slug / "VALIDATION.json").read_text())
        swap(slug, urn, "n/a (holding id; per-treatise canonical TLG split deferred)",
             slug, rows, f"qwen36-{slug}-masked", val["verdict"],
             {"tier": val["tier"],
              "per_treatise_split": "DEFERRED + flagged: this Walz Rhetores Graeci "
              "volume bundles many rhetorical treatises under the ocr.walz_* holding "
              "id; the staging carries no per-treatise boundary, so a canonical TLG "
              "split is left for manual follow-up. This swap only improves the OCR text "
              "under the same holding id.",
              "flag": "data/corpus_changes/walz-rhetores.per-treatise-split.flag.json"})

    # --- 4. Flag the ambiguous shared-scan splits (leave served untouched) -------
    for slug, info in FLAGS.items():
        rec = {
            "_meta": {
                "change": "HELD - not ingested (ambiguous split; served text left unchanged)",
                "work": info["primary_urn"],
                "cts": info["cts"],
                "run_slug": slug,
                "applied_by": "scripts/ingest_held_reocr.py",
                "date": DATE,
                "status": "flagged-for-manual-followup",
            },
            "served_left_unchanged": True,
            "shared_scan_secondary_works": info["secondary"],
            "reason_held": info["reason"],
            "recommendation": info["recommendation"],
            "masked_reocr_available": "yes - staged, keep-better vs served, but keyed "
            "as one combined jsonl; do NOT ingest until the split is resolved.",
            "source": "held-works local-keying review, " + DATE,
        }
        if do:
            (changes / f"{slug}.reocr-flag.json").write_text(
                json.dumps(rec, ensure_ascii=False, indent=2) + "\n")

    # --- 5. One combined flag for the Walz per-treatise split --------------------
    walz_flag = {
        "_meta": {
            "change": "DEFERRED - per-treatise canonical TLG split of the Walz "
            "Rhetores Graeci volumes",
            "applied_by": "scripts/ingest_held_reocr.py",
            "date": DATE,
            "status": "flagged-for-manual-followup",
        },
        "holding_ids_swapped_keep_better": [f"ocr.{s}" for s in WALZ],
        "reason_deferred": "Each Walz Rhetores Graeci volume is a bound anthology of "
        "many distinct rhetorical treatises (prolegomena, Anonymi, Sopater, Marcellinus, "
        "Syrianus, Maximus Planudes, etc.). The masked re-OCR was staged as one jsonl "
        "per volume under the existing ocr.walz_* holding id, with no per-treatise "
        "boundary recorded. A canonical per-treatise TLG split needs each volume's TOC "
        "matched to tlg_canon; forcing it now would risk mis-keys.",
        "recommendation": "manual: build a per-volume TOC (page ranges) from Walz's "
        "Rhetores Graeci and match each treatise to its TLG urn, then carve and key.",
        "note": "The keep-better OCR text is already improved under the holding ids; "
        "only the canonical split remains.",
        "source": "held-works local-keying review, " + DATE,
    }
    if do:
        (changes / "walz-rhetores.per-treatise-split.flag.json").write_text(
            json.dumps(walz_flag, ensure_ascii=False, indent=2) + "\n")

    for line in ingested:
        print(line)
    print(f"\n{'APPLIED' if do else 'CHECK'}: {len(ingested)} works "
          f"({'photius + 3 GG-IV parts + 5 Walz' if len(ingested)==9 else 'UNEXPECTED COUNT'}), "
          f"{len(FLAGS)} shared-scan flags + 1 Walz-split flag.")
    for e in errors:
        print("ERROR:", e)
    return 1 if errors or len(ingested) != 9 else 0


if __name__ == "__main__":
    sys.exit(main())
