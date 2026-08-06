#!/usr/bin/env python3
"""Put back the Walz text that the masked-column re-OCR swap replaced.

On 2026-07-12 a re-OCR run using column masking was swapped in for five Walz
volumes, and it destroyed the reading order. The page is set in two columns; the
masked run read the columns as separate blocks and emitted each fragment as its
own row, cutting words in half at the column edge. Scan 0016 of v4 went from one
continuous row

    τῇ δόξῃ· ὥσπερ γὰρ ἡ δόξα ἄνευ λόγου προέχεται, οὕτω καὶ ἡ ἐμπειρία ...

to 53 stubs beginning `λογεῖ τῇ δόξῃ·`, `ται, οὕτω καὶ`, `πραγμάτων οὐκ`.
Across the five volumes 63.0% of the served token mass now sits in rows under 40
characters, against 8.7% before (issue #20).

The swap was not an accident, it passed a gate. The audit record's own evidence
line reads `keep-better: greek_ratio=0.9727 (masked/served); masked_greek_chars=
1075006 vs served_greek_chars=1105233; rows 6294->35014`, so the gate recorded
that the new text held 97% of the Greek, LOST 30,227 characters of it, and blew
the row count up 5.6x, and admitted it anyway. Nothing in it looked at reading
order. That is the actual defect, and scripts/ingest_held_reocr.py is where it
has to be fixed so this cannot recur; this script only undoes the damage.

Two things make the higher token count of the masked text not an argument for
keeping it. Splitting a word in half produces two tokens where there was one, so
a shredded text counts HIGHER while saying less: the +42,943 tokens are mostly
that. And the masked run carries FEWER Latin characters (6,280 against 8,194 in
v4), so it did not buy the apparatus either.

Recovery is exact rather than approximate. The pre-swap text is a git blob, and
each volume's swap record pins its sha256, so this refuses to write anything it
cannot verify byte for byte first.

Corrections need care and are the reason this is not `git checkout`. 519 were
applied to these urns on 2026-06-28, before the swap. Their loci are row-keyed
(`..._0063.2`) and the two texts have entirely different row ordinals, so a locus
does not survive; the SCAN PAGE does. Matching on page plus exact string:

    205  already present in the restored text, nothing to do
    209  re-appliable, exactly one row on that page holds the original
     25  ambiguous, several rows on the page hold it
     80  neither string anywhere on the page, so they corrected text that only
         the masked run produced

The 209 are re-applied. The 105 that are not are retired through the audit
record with their reason, never silently dropped.

  restore_walz_unmasked_text.py                 # check every volume, writes nothing
  restore_walz_unmasked_text.py --apply
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
CORPUS = DATA / "corpus"
CHANGES = DATA / "corpus_changes"
APPLIED = DATA / "corrections_log" / "applied.jsonl"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

# The commit that performed the swap; its parent holds the text being restored.
SWAP_COMMIT = "02641c2"
VOLUMES = ("v1", "v4", "v5", "v7pt2", "v9")
SHORT_ROW = 40
# Below this share of the masked page's characters, the restored page is not
# saying the same thing, and if it is also shorter the original run missed text.
COVERAGE_MIN = 0.75


def _fold(text: str) -> str:
    """Greek letters only, lowercased and accent-stripped, for comparing what
    two OCR runs of one page actually say rather than how they spelled it."""
    joined = "".join(_GK.findall(text or ""))
    return "".join(c for c in unicodedata.normalize("NFD", joined.lower())
                   if not unicodedata.combining(c))


def tokens(text: str) -> int:
    return len(_GK.findall(text or ""))


def scan_of(locus: str) -> str:
    return locus.rsplit("_", 1)[1].split(".")[0]


def blob_at(rev: str, path: str) -> bytes:
    r = subprocess.run(["git", "show", f"{rev}:{path}"], capture_output=True, cwd=REPO)
    if r.returncode != 0:
        raise SystemExit(f"cannot read {path} at {rev}: {r.stderr.decode()[:200]}")
    return r.stdout


def load_corrections() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    with APPLIED.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                if rec.get("urn"):
                    out[rec["urn"]].append(rec)
    return out


def restore(vol: str, apply: bool) -> dict:
    urn = f"ocr.walz_rhetores_{vol}"
    rel = f"data/corpus/{urn}.jsonl"
    served_fp = CORPUS / f"{urn}.jsonl"
    record = CHANGES / f"{urn}.reocr-swap.json"
    if not record.exists():
        raise SystemExit(f"{vol}: no swap record at {record}")
    swap = json.loads(record.read_text(encoding="utf-8"))
    want = (swap.get("old") or {}).get("sha256") or swap.get("old_sha256")
    if not want:
        raise SystemExit(f"{vol}: swap record carries no old sha256 to verify against")

    raw = blob_at(f"{SWAP_COMMIT}^", rel)
    got = hashlib.sha256(raw).hexdigest()
    # The gate. Nothing below runs on a blob that is not the recorded one.
    if got != want:
        raise SystemExit(f"{vol}: refusing to restore, blob sha256 {got[:16]} "
                         f"does not match the swap record's {want[:16]}")

    restored = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
    served = [json.loads(l) for l in
              served_fp.read_text(encoding="utf-8").splitlines() if l.strip()]

    # Carry forward what the served rows gained since, so the restore does not
    # also roll back schema. `cts` is the holding string every served row now
    # has; `edition` keeps naming the run the text actually came from.
    cts = next((r.get("cts") for r in served if r.get("cts")), None)
    for r in restored:
        if cts is not None:
            r["cts"] = cts

    by_page: dict[str, list[dict]] = defaultdict(list)
    for r in restored:
        by_page[scan_of(r["locus"])].append(r)
    served_by_page: dict[str, list[dict]] = defaultdict(list)
    for r in served:
        served_by_page[scan_of(r["locus"])].append(r)

    # Reverting the whole volume was the obvious move and it loses text. On most
    # pages the masked run only shredded what was already there, but on some the
    # ORIGINAL run is the deficient one: v1 scan 0159 reads `III. ΘΕΩΝΟΣ /
    # ΥΠΟΓΥΜΝΑΣΜΑΤΑ.` and nothing else, where the masked run has the whole page,
    # and several of v9's apparatus pages are the same. So the choice is made per
    # page: take the restored page unless it fails to account for the masked
    # one's content AND is materially shorter, which is what "the original run
    # missed text here" looks like. Compared accent-blind, because the masked run
    # drops diacritics on some pages and that is not a content difference.
    kept_masked: list[str] = []
    for page, srows in served_by_page.items():
        rrows = by_page.get(page)
        want = _fold(" ".join(r.get("text") or "" for r in srows))
        have = _fold(" ".join(r.get("text") or "" for r in (rrows or [])))
        if len(want) < 60:
            continue
        cw, ch = Counter(want), Counter(have)
        covered = sum(min(n, ch[c]) for c, n in cw.items()) / len(want)
        if not rrows or (covered < COVERAGE_MIN and len(have) < 0.9 * len(want)):
            by_page[page] = list(srows)
            kept_masked.append(page)
    restored = [r for page in sorted(by_page) for r in by_page[page]]

    reapplied, retired = [], []
    for c in CORRECTIONS.get(urn, []):
        rows = by_page.get(scan_of(c["locus"]), [])
        if not rows:
            retired.append({**c, "retired_because": "scan page absent from the restored text"})
            continue
        has_corr = [r for r in rows if c["corrected"] in (r.get("text") or "")]
        has_orig = [r for r in rows if c["original"] in (r.get("text") or "")]
        if has_corr and not has_orig:
            continue                                   # already in the text
        if len(has_orig) == 1 and not has_corr:
            row = has_orig[0]
            row["text"] = row["text"].replace(c["original"], c["corrected"], 1)
            reapplied.append({**c, "reapplied_at": row["locus"]})
            continue
        retired.append({**c, "retired_because":
                        "several rows on the page hold the original, so the row is "
                        "ambiguous once the locus no longer places it"
                        if len(has_orig) > 1 else
                        "neither string appears on that page, so it corrected text "
                        "only the masked run produced"})

    s_tok = sum(tokens(r.get("text") or "") for r in served)
    r_tok = sum(tokens(r.get("text") or "") for r in restored)
    s_short = sum(tokens(r.get("text") or "") for r in served
                  if len(r.get("text") or "") < SHORT_ROW)
    r_short = sum(tokens(r.get("text") or "") for r in restored
                  if len(r.get("text") or "") < SHORT_ROW)

    # The row set changes by design, so token conservation is the wrong check.
    # This is the one that would catch restoring the wrong volume or a partial
    # run: the restored page must account for most of what the masked page says.
    served_pages: dict[str, Counter] = defaultdict(Counter)
    for r in served:
        served_pages[scan_of(r["locus"])].update(_GK.findall(r.get("text") or ""))
    # A handful of pages exist only in the masked run, because the original run
    # skipped them and the masked one emitted degenerate repetition instead:
    # `ἄνθρωπος, ὁ, ἄνθρωπος, ἡ, ἄνθρωπος`, `ἸΛΙΟΝ | ἸΛΙΟΝ | ἸΛΙΟΝ`. They cannot
    # be covered by a page that does not exist, so they are held out of the check
    # and archived verbatim in the audit rather than dropped without trace.
    masked_only = [r for r in served if scan_of(r["locus"]) not in by_page]
    mo_tokens = sum(tokens(r.get("text") or "") for r in masked_only)
    worst, worst_page = 1.0, None
    for page, want_counts in served_pages.items():
        if page not in by_page:
            continue
        have = Counter()
        for r in by_page[page]:
            have.update(_GK.findall(r.get("text") or ""))
        total = sum(want_counts.values())
        if total < 20:
            continue
        covered = sum(min(n, have[t]) for t, n in want_counts.items()) / total
        if covered < worst:
            worst, worst_page = covered, page

    out = {
        "volume": vol, "urn": urn,
        "served_rows": len(served), "restored_rows": len(restored),
        "served_tokens": s_tok, "restored_tokens": r_tok,
        "served_short_share": round(s_short / max(s_tok, 1), 4),
        "restored_short_share": round(r_short / max(r_tok, 1), 4),
        "reapplied": len(reapplied), "retired": len(retired),
        "worst_page_coverage": round(worst, 4), "worst_page": worst_page,
        "masked_only_pages": len({scan_of(r["locus"]) for r in masked_only}),
        "masked_only_tokens": mo_tokens,
        "sha256_verified": got,
    }
    print(f"  {vol:6} rows {len(served):>6,} -> {len(restored):>6,}   "
          f"tokens {s_tok:>7,} -> {r_tok:>7,}   "
          f"short {out['served_short_share']:.1%} -> {out['restored_short_share']:.1%}   "
          f"corrections +{len(reapplied)} / retired {len(retired)}   "
          f"min shared-page coverage {worst:.1%}   "
          f"masked-only {out['masked_only_pages']}pp/{mo_tokens:,}tok")

    if not apply:
        return out

    before = hashlib.sha256(served_fp.read_bytes()).hexdigest()
    served_fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                 for r in restored), encoding="utf-8")
    audit = {
        "what": f"reverted the 2026-07-12 masked-column re-OCR swap on {urn}, "
                f"restoring the text from {SWAP_COMMIT}^",
        "date": "2026-08-06",
        "issue": "open-greek/open-greek-corpus#20",
        "why": "the masked run read a two-column page as separate blocks and emitted "
               "each fragment as a row, cutting words at the column edge; "
               f"{out['served_short_share']:.1%} of the served token mass sat in rows "
               f"under {SHORT_ROW} characters against "
               f"{out['restored_short_share']:.1%} before it",
        "overturns": {
            "record": f"data/corpus_changes/{urn}.reocr-swap.json",
            "its_evidence": swap.get("evidence"),
            "why_that_was_wrong": "the gate measured retained Greek characters and "
                                  "row count but never reading order, and its own "
                                  "line records losing Greek and a 5.6x row "
                                  "explosion while still passing",
        },
        "source_blob": {"rev": f"{SWAP_COMMIT}^", "path": rel, "sha256": got,
                        "matched_swap_record_old_sha256": True},
        "sha256_before": before,
        "sha256_after": hashlib.sha256(served_fp.read_bytes()).hexdigest(),
        "rows_before": len(served), "rows_after": len(restored),
        "tokens_before": s_tok, "tokens_after": r_tok,
        "worst_page_token_coverage": out["worst_page_coverage"],
        "dropped_masked_only_rows": [{"locus": r["locus"], "text": r.get("text")}
                                     for r in masked_only],
        "dropped_masked_only_note": "pages the original run skipped and the masked "
                                    "run filled with degenerate repetition; archived "
                                    "here verbatim so the drop is reversible",
        "corrections_reapplied": reapplied,
        "corrections_retired": retired,
        "reverse": f"the pre-revert text is the blob at {SWAP_COMMIT}, and "
                   f"sha256_before pins it",
    }
    fp = CHANGES / f"{urn}.masked-swap-revert.json"
    fp.write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    out["audit"] = str(fp.relative_to(REPO))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--volume", action="append", choices=VOLUMES)
    args = ap.parse_args()

    global CORRECTIONS
    CORRECTIONS = load_corrections()

    results = [restore(v, args.apply) for v in (args.volume or VOLUMES)]
    st = sum(r["served_tokens"] for r in results)
    rt = sum(r["restored_tokens"] for r in results)
    ss = sum(r["served_tokens"] * r["served_short_share"] for r in results)
    rs = sum(r["restored_tokens"] * r["restored_short_share"] for r in results)
    print(f"\n  {len(results)} volumes: {st:,} -> {rt:,} tokens, "
          f"short-row mass {ss / st:.1%} -> {rs / rt:.1%}, "
          f"{sum(r['reapplied'] for r in results)} corrections re-applied, "
          f"{sum(r['retired'] for r in results)} retired")
    if not args.apply:
        print("  check only; nothing written. Re-run with --apply.")


if __name__ == "__main__":
    main()
