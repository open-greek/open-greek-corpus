#!/usr/bin/env python3
"""Registry/metadata follow-ups for the Diels re-split (commit 3ed899b).

dissolve_diels.py dissolved seven wholesale presocratic volume scans into
per-chapter DK works; three metadata surfaces still described the old state:

1. source_registry.json - the 10 minted urn-less slugs (7 multi-author or
   canon-absent DK chapter works + 3 per-volume paratexta remainders) had no
   registry entry. Minimal honest entries are inserted here, keyed by the
   REAL corpus slug: author display name + title, empty aliases (no canon
   author/work exists - never fabricate), best_source open_corpus, matching
   the Registry.save shape (sorted, indent=1). Direct insertion is
   deliberate: the registry generator (build_registry.py) reads the vendored
   TLG inventory, which cannot know these works, and its corpus_editions
   fallback mints dishonest "anon-<slug>" twins keyed by the wrong slug (see
   anon-symmachus.symmachus-fragmenta), so - following the merge-producer
   pattern of needs_registry.py - this script owns exactly these entries and
   re-inserts them idempotently. DK chapter numbers live in the corpus rows.

2. ocr_works.json - 10 stale rows described the old wholesale works (whole
   475-page volumes under one slug, and the retired legacy placeholders).
   Rows whose urn still serves are refreshed from data/corpus (dominant
   edition, page-stem count, passage/Greek-token counts, date of refresh);
   rows for urns the re-split retired (2septem-sapientes-2.testimonia, and
   gorgias-rhetoric.testimonium whose file was the 1910 Wortindex scan) are
   removed - both retirements are documented in dissolve_diels.py and the
   3ed899b commit message, and the old rows stay in git history.

3. tlg_crosswalk.json - gorgias-rhetoric.testimonium (tlg0593.tlg001) is
   pruned: its only file was the Wortindex scan (displaced whole to
   corpus_secondary), so the canon Testimonium (46 words) was never actually
   served; pruning follows the displace_to_secondary.py --prune-crosswalk
   convention and the 2septem precedent in the same commit. Gorgias content
   now serves at gorgias-rhetoric.testimonia (tlg0593.tlg002). The tsv is
   regenerated.

Idempotent: a second run changes nothing.

  python3 scripts/diels_resplit_followups.py            # dry-run
  python3 scripts/diels_resplit_followups.py --write
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG_PATH = REPO / "data" / "source_registry.json"
OW_PATH = REPO / "data" / "ocr_works.json"
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
TSV_PATH = REPO / "data" / "tlg_crosswalk.tsv"
CORPUS = REPO / "data" / "corpus"

_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")
_STEM = re.compile(r"^(.*?_\d{3,4})(?:\.|$)")
REFRESH_DATE = "2026-07-09"

# --- 1. registry entries for the minted urn-less Diels slugs ----------------
# (author display name, work title, tags). No aliases: none of these authors
# or groups has a TLG canon entry (verified against the vendored canon by
# dissolve_diels.py, whose CH tables mark them urn=None).
MINTED = {
    "ameinias.testimonia-et-fragmenta":
        ("Ameinias", "Testimonia et Fragmenta", ["genre:testimonia"]),
    "parmiscus.testimonia-et-fragmenta":
        ("Parmiscus", "Testimonia et Fragmenta", ["genre:testimonia"]),
    "phaleas-et-hippodamus.testimonia-et-fragmenta":
        ("Phaleas et Hippodamus", "Testimonia et Fragmenta",
         ["genre:testimonia"]),
    "archippus-lysis-opsimus.testimonia-et-fragmenta":
        ("Archippus, Lysis, Opsimus", "Testimonia et Fragmenta",
         ["genre:testimonia"]),
    "diocles-echecrates-polymnastus-phanton-arion.testimonia-et-fragmenta":
        ("Diocles, Echecrates, Polymnastus, Phanton, Arion",
         "Testimonia et Fragmenta", ["genre:testimonia"]),
    "proros-amyclas-clinias.testimonia-et-fragmenta":
        ("Proros, Amyclas, Clinias", "Testimonia et Fragmenta",
         ["genre:testimonia"]),
    "simus-myonides-euphranor.testimonia-et-fragmenta":
        ("Simus, Myonides, Euphranor", "Testimonia et Fragmenta",
         ["genre:testimonia"]),
    "diels-fvs-1903.paratexta":
        ("Diels, Die Fragmente der Vorsokratiker (1903)",
         "Paratexta (front matter, Zusaetze, Namensverzeichnis)", []),
    "diels-fdv2-1906-1.paratexta":
        ("Diels, Die Fragmente der Vorsokratiker, 2. Aufl., Band I (1906)",
         "Paratexta (front matter, Zusaetze)", []),
    "diels-ppf-1901.paratexta":
        ("Diels, Poetarum Philosophorum Fragmenta (1901)",
         "Paratexta (front matter, indices)", []),
}

# --- 2. the stale ocr_works rows --------------------------------------------
REFRESH_URNS = [        # still served: refresh stats from data/corpus
    "nausiphanes.testimonia", "protagoras.testimonia", "anaxagoras.testimonia",
    "melissus.testimonia", "anaximander.testimonia", "empedocles.diels-ppf",
    "leucippus.testimonia", "cleostratus.testimonia",
]
RETIRED_URNS = [        # no longer served: drop the row (git keeps history)
    "2septem-sapientes-2.testimonia", "gorgias-rhetoric.testimonium",
]

PRUNE_CROSSWALK = {"gorgias-rhetoric.testimonium": "tlg0593.tlg001"}


def corpus_stats(slug: str) -> dict | None:
    fp = CORPUS / f"{slug}.jsonl"
    if not fp.exists():
        return None
    recs = [json.loads(l) for l in fp.open(encoding="utf-8") if l.strip()]
    eds = Counter(r.get("edition") for r in recs)
    stems = set()
    for r in recs:
        m = _STEM.match(str(r.get("locus", "")))
        stems.add(m.group(1) if m else str(r.get("locus", "")))
    return {
        "edition": eds.most_common(1)[0][0] if eds else "",
        "pages": len(stems),
        "n_passages": len(recs),
        "n_tokens": sum(1 for r in recs for t in str(r.get("text", "")).split()
                        if _GK.search(t)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    changed = []

    # 1. registry
    reg = json.loads(REG_PATH.read_text(encoding="utf-8"))
    for slug, (author_name, title, tags) in MINTED.items():
        if not (CORPUS / f"{slug}.jsonl").exists():
            print(f"  SKIP registry {slug}: not in data/corpus")
            continue
        aslug = slug.split(".")[0]
        if aslug not in reg["authors"]:
            reg["authors"][aslug] = {"name": author_name, "aliases": {}}
            changed.append(f"registry author + {aslug}")
        if slug not in reg["works"]:
            reg["works"][slug] = {
                "author": aslug, "title": title, "aliases": {},
                "default_edition": None, "best_source": "open_corpus",
                "tags": tags, "editions": {}}
            changed.append(f"registry work   + {slug}")

    # 2. ocr_works
    ow = json.loads(OW_PATH.read_text(encoding="utf-8"))
    for w in ow:
        if w.get("urn") in REFRESH_URNS:
            st = corpus_stats(w["urn"])
            if st is None:
                print(f"  WARNING {w['urn']}: listed as served but no corpus file")
                continue
            upd = dict(st, date=REFRESH_DATE)
            if any(w.get(k) != v for k, v in upd.items()):
                w.update(upd)
                changed.append(f"ocr_works refresh {w['urn']} "
                               f"({st['n_passages']} passages, "
                               f"{st['n_tokens']} tokens)")
    before = len(ow)
    ow = [w for w in ow if w.get("urn") not in RETIRED_URNS
          or (CORPUS / f"{w['urn']}.jsonl").exists()]
    if len(ow) != before:
        changed.append(f"ocr_works removed {before - len(ow)} retired rows "
                       f"({', '.join(RETIRED_URNS)})")

    # 3. crosswalk prune
    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    cw_dirty = False
    for slug, tlg in PRUNE_CROSSWALK.items():
        if cw.get(slug, {}).get("tlg") == tlg and \
                not (CORPUS / f"{slug}.jsonl").exists():
            del cw[slug]
            cw_dirty = True
            changed.append(f"crosswalk pruned {slug} ({tlg})")

    for c in changed:
        print(" ", c)
    if not changed:
        print("  nothing to do (already applied)")
        return
    if not args.write:
        print("(dry-run: nothing written; use --write)")
        return

    REG_PATH.write_text(json.dumps(
        {"authors": {s: reg["authors"][s] for s in sorted(reg["authors"])},
         "works": {s: reg["works"][s] for s in sorted(reg["works"])}},
        ensure_ascii=False, indent=1, sort_keys=False), encoding="utf-8")
    OW_PATH.write_text(json.dumps(ow, ensure_ascii=False, indent=1),
                       encoding="utf-8")
    if cw_dirty:
        CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0),
                           encoding="utf-8")
        with TSV_PATH.open("w", encoding="utf-8") as f:
            f.write("slug\tcts_urn\ttlg\n")
            for s, d in sorted(cw.items()):
                if d.get("cts"):        # pta-alias-only entries have no urn
                    f.write(f"{s}\t{d['cts']}\t{d['tlg']}\n")
    print("written.")


if __name__ == "__main__":
    main()
