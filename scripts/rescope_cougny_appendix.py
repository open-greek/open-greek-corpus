#!/usr/bin/env python3
"""Re-scope the mislabeled thomas-patricius-anthol-dubner-v3 work.

The IA scan epigrammatumanth03grotuoft is NOT a "Thomas Patricius" work and
the volume is not Dubner's: it is vol. 3 of the Didot Anthologia Graeca =
E. Cougny, Epigrammatum Anthologia Palatina cum Planudeis et appendice nova
epigrammatum veterum ex libris et marmoribus ductorum, vol. III (Paris 1890),
i.e. Cougny's Appendix nova: dedicatory epigrams (App. I ep. 1 "Argo" at scan
p. 11), inscriptional epitaphs, the Bubastis stele (p. 406), oracles, Byzantine
epigrams (Romanos, p. 610). Thomas Patricius is merely one lemma author inside
it. The old slug also carried a wrong tlg4049.tlg001 crosswalk claim (tlg4049
is absent from the current TLG canon - a fabricated urn).

The work stays PRIMARY: Cougny's appendix collection has no open digital
edition (Perseus AP covers only the Palatine/Planudean books). Following the
jacobs-anthologia-graeca-t13 precedent (the upstream OCR pipeline's rescope_jacobs.py) this
script gives it an honest edition-scoped identity:

  1. renames the served work (file + per-row urn) to
     cougny-appendix-nova.didot-anthologia-v3 - loci keep their original
     thomas_patricius_anthol_dubner_v3_NNNN page stems, which are the stable
     key into the OCR provenance and the corrections log;
  2. drops the tlg4049.tlg001 claim from data/tlg_crosswalk.json and
     regenerates data/tlg_crosswalk.tsv (no urn is minted: the appendix is an
     edition-scoped collection, like the Jacobs t.13 works);
  3. adds a slug-only crosswalk entry documenting the identity;
  4. renames the work's data/needs_ocr_cleanup.json key so the cleanup flag
     follows the work.

Note: palladas-anthol-dubner-v2 is a second scan of the SAME printed book
(page offset -1); its rescope/dedup is a separate follow-up.

  python3 scripts/rescope_cougny_appendix.py            # dry-run
  python3 scripts/rescope_cougny_appendix.py --write
  then: python3 scripts/reconcile_corpus_editions.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
TSV_PATH = REPO / "data" / "tlg_crosswalk.tsv"
NEEDS_PATH = REPO / "data" / "needs_ocr_cleanup.json"

OLD_SLUG = "thomas-patricius-anthol-dubner-v3"
NEW_SLUG = "cougny-appendix-nova.didot-anthologia-v3"
_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")


def main() -> None:
    write = "--write" in sys.argv

    old_fp = CORPUS / f"{OLD_SLUG}.jsonl"
    new_fp = CORPUS / f"{NEW_SLUG}.jsonl"
    if new_fp.exists():
        sys.exit(f"ABORT: {new_fp.name} already exists")
    rows = [json.loads(l) for l in old_fp.open(encoding="utf-8") if l.strip()]
    gk = sum(len(_GK.findall(r["text"])) for r in rows)
    print(f"{OLD_SLUG}: {len(rows)} rows, {gk:,} Greek chars -> {NEW_SLUG}")

    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    old_claim = cw.get(OLD_SLUG, {}).get("tlg")
    print(f"crosswalk claim to drop: {old_claim}")
    needs = json.loads(NEEDS_PATH.read_text(encoding="utf-8"))
    print(f"needs_ocr_cleanup entry: {needs.get(OLD_SLUG)}")

    if not write:
        print("DRY RUN - nothing written (use --write)")
        return

    for r in rows:
        r["urn"] = NEW_SLUG
    new_fp.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8")
    old_fp.unlink()

    cw.pop(OLD_SLUG, None)
    cw[NEW_SLUG] = {
        "author_slug": "cougny-appendix-nova",
        "title": "Appendix nova epigrammatum (Didot Anthologia Graeca vol. 3)",
        "note": "edition-scoped work: Cougny, Epigrammatum Anthologia "
                "Palatina... et appendice nova, vol. III (Didot 1890); "
                "formerly mislabeled thomas-patricius-anthol-dubner-v3 with a "
                "fabricated tlg4049.tlg001 claim (tlg4049 not in the TLG "
                "canon); no tlg urn - no open edition of the appendix exists"}
    CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0),
                       encoding="utf-8")
    with TSV_PATH.open("w", encoding="utf-8") as f:
        f.write("slug\tcts_urn\ttlg\n")
        for s, d in sorted(cw.items()):
            if d.get("cts"):            # slug-only entries have no urn
                f.write(f"{s}\t{d['cts']}\t{d['tlg']}\n")

    if OLD_SLUG in needs:
        needs[NEW_SLUG] = needs.pop(OLD_SLUG)
        NEEDS_PATH.write_text(json.dumps(needs, ensure_ascii=False, indent=1,
                                         sort_keys=True), encoding="utf-8")

    print(f"renamed -> {NEW_SLUG}; crosswalk claim {old_claim} dropped, "
          f"slug-only entry added; tsv regenerated; "
          f"now run reconcile_corpus_editions.py")


if __name__ == "__main__":
    main()
