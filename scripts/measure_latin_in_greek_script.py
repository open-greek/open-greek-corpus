#!/usr/bin/env python3
"""Find served text that is Latin spelled in Greek letters and counted as Greek.

Two works in this corpus survive only partly in Greek. Polycarp's letter to the
Philippians has chapters 10-12 and 14 in Latin alone, and the Shepherd of Hermas
loses its Greek partway through the Similitudes. The editions this corpus took
them from print the Latin, and somewhere upstream it was transliterated into
Greek script, so it tokenizes as Greek and is counted as Greek:

    ιν ηις εργο στατε ετ δομινι εχεμπλαρ σεqυιμινι     (Polycarp 10.1)
    = in his ergo state et domini exemplar sequimini
    ηαξξ ϝοβις σξριπσι περ ξρεσξεντεμ                   (Polycarp 14.1)
    = haec vobis scripsi per Crescentem

It is a small class and a real one: these tokens enter the lexicon, the lemma
frequency table and the released Greek total, and no Greek word among them is a
Greek word.

THE TEST, and why it is two tests. A single signal is not enough either way.
Unaccented Greek is common in this corpus (display heads, all-caps OCR, some
inscriptions), so accent-poverty alone over-reports. And a few Latin-looking
tokens prove nothing, because Greek has its own ιν-, ετ- shaped fragments once
OCR has damaged them. So a row has to be BOTH almost entirely unaccented AND
carry at least MIN_MARKERS distinct Latin function words in their transliterated
spellings. The marker list deliberately holds no word that is also Greek: προ,
περι and και transliterate onto real Greek words and would convict Greek text of
being Latin.

WHAT THIS DOES NOT DO. It does not delete or re-encode anything. Whether these
tokens should be dropped, kept but flagged, or kept and excluded from the Greek
counts is a disposition, and the three answers give three different published
totals.

  python3 scripts/measure_latin_in_greek_script.py
  python3 scripts/measure_latin_in_greek_script.py --write
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
OUT = DATA / "latin_in_greek_script.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_public_corpus import _GK  # noqa: E402

# Latin function words as this transliteration renders them. None of these is
# also a Greek word; that is the point of the list, not an accident of it.
MARKERS = {
    "ετ", "ιν", "εστ", "νον", "σεδ", "αυτεμ", "ενιμ", "υτ", "σι", "ειυς",
    "εσσε", "νιηιλ", "ϝος", "ϝοβις", "ϝεστρα", "ομνιβυς", "ομνες", "ταμεν",
    "συμ", "συντ", "ατ", "αδ", "εχ", "εργο", "ερgο", "ιλλο", "ιλλυμ", "ηις",
    "ηοξ", "νοβις", "κυι", "θυι", "σιξυτ", "ιτα", "ιαμ", "ϝελ", "νεξ", "απυδ",
    "ιντερ", "ποστ", "αντε", "προπτερ", "σινε",
}
MIN_TOKENS = 20      # below this a row is too short to judge either way
MIN_MARKERS = 5      # distinct Latin function words the row must carry
MAX_ACCENT = 0.05    # combining marks per token; Greek prose here runs far above


def accent_rate(text: str, tokens: int) -> float:
    marks = sum(1 for c in unicodedata.normalize("NFD", text)
                if unicodedata.combining(c))
    return marks / max(tokens, 1)


def scan() -> list[dict]:
    """Rows the two signals confirm, plus short rows inside a confirmed run.

    The floors are strict on purpose and they under-report: Polycarp 10.1 is
    "in his ergo state et domini exemplar sequimini" and carries four distinct
    markers where five are required, and Hermas has five more like it. Rather
    than lower the floor, which would start convicting Greek, a low-accent row
    whose neighbour in the same work is confirmed joins it. A short Latin
    sentence in the middle of a Latin chapter is Latin; position settles what
    the row alone is too short to say, and it cannot reach outside a run.
    """
    out = []
    for fp in sorted((DATA / "corpus").glob("*.jsonl")):
        rows = [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines()
                if l.strip()]
        marked = []
        for r in rows:
            text = r.get("text") or ""
            toks = _GK.findall(text)
            if not toks:
                marked.append(None)
                continue
            hits = {w for w in (t.lower() for t in toks) if w in MARKERS}
            rate = accent_rate(text, len(toks))
            low = rate < MAX_ACCENT
            sure = low and len(toks) >= MIN_TOKENS and len(hits) >= MIN_MARKERS
            marked.append({"work": fp.name[:-len(".jsonl")],
                           "locus": str(r["locus"]), "tokens": len(toks),
                           "distinct_markers": len(hits),
                           "accent_rate": round(rate, 4), "low_accent": low,
                           "confirmed": sure,
                           "opens": " ".join(text.split())[:70]})
        if not any(m and m["confirmed"] for m in marked):
            continue
        for i, m in enumerate(marked):
            if not m or m["confirmed"] or not m["low_accent"]:
                continue
            nb = [marked[j] for j in (i - 1, i + 1)
                  if 0 <= j < len(marked) and marked[j]]
            if any(n["confirmed"] for n in nb):
                m["by_run"] = True
        out.extend(m for m in marked
                   if m and (m["confirmed"] or m.get("by_run")))
    out.sort(key=lambda r: (r["work"], r["locus"]))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    rows = scan()
    by_work: collections.Counter = collections.Counter()
    for r in rows:
        by_work[r["work"]] += r["tokens"]
    total = sum(by_work.values())
    print(f"Latin in Greek script: {len(rows)} rows, {total:,} tokens, "
          f"{len(by_work)} works")
    for w, n in by_work.most_common():
        print(f"    {w[:56]:<56} {n:>6,}")
    for r in rows[:4]:
        print(f"    {r['work'][:26]:<26} {r['locus']:<10} {r['opens'][:56]}")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "served rows that are Latin spelled in Greek letters, so they "
                "tokenize as Greek and are counted as Greek",
        "issue": "open-greek/open-greek-corpus#34",
        "why_these_two_works": "both survive only partly in Greek. Polycarp's "
            "Philippians has chapters 10-12 and 14 in Latin alone (13 is Greek, "
            "preserved in Eusebius' quotation), and the Shepherd of Hermas loses "
            "its Greek partway through the Similitudes. The editions print the "
            "Latin and it was transliterated into Greek script upstream.",
        "test": {
            "why_two_signals": "accent-poverty alone over-reports, because "
                "display heads, all-caps OCR and some inscriptions are "
                "unaccented Greek. A few Latin-looking tokens alone prove "
                "nothing either, since damaged Greek produces such shapes. A row "
                "must be both.",
            "min_tokens": MIN_TOKENS, "min_distinct_markers": MIN_MARKERS,
            "max_accent_rate": MAX_ACCENT,
            "markers_exclude_greek_words": "no marker is also a Greek word. προ, "
                "περι and και transliterate onto real Greek and would convict "
                "Greek text of being Latin.",
        },
        "NOT_A_DISPOSITION": "nothing is deleted or re-encoded here. Drop, keep "
            "but flag, or keep and exclude from the Greek counts are three "
            "different published totals, and which one is right is a call for "
            "cisco.",
        "run_context": "a low-accent row too short or too marker-poor to "
            "confirm on its own is included when its neighbour in the same work "
            "is confirmed. Polycarp 10.1 is exactly that case: it is 'in his "
            "ergo state et domini exemplar sequimini' and carries four markers "
            "where five are asked. Lowering the floor instead would start "
            "convicting Greek, so the floor stays and position does the rest.",
        "rows": len(rows), "tokens": total,
        "confirmed_rows": sum(1 for r in rows if r["confirmed"]),
        "confirmed_tokens": sum(r["tokens"] for r in rows if r["confirmed"]),
        "by_run_rows": sum(1 for r in rows if r.get("by_run")),
        "by_run_tokens": sum(r["tokens"] for r in rows if r.get("by_run")),
        "by_work": [{"work": w, "tokens": n} for w, n in by_work.most_common()],
        "detail": rows,
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
