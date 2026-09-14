#!/usr/bin/env python3
"""Measure and attribute grave-accented lemma residue (issue #4).

The headline counts come from the per-work lemma table. Surface reachability is
reported for continuity with earlier audits, but is not a repair gate: the
corpus printing an acute spelling does not prove that spelling is a headword.
The independently backed partition uses the same ancient/Byzantine dictionary
inventories as Dilemma 1.2.1+ and OGC's validator.

When the fresh form->lemma cache is present, the audit also attributes mappings
to five exclusive routes: a live structured Dilemma result, model/identity
fallback, stale cache, an OGC-accepted supplied/normalized lemma, or a
nonlexical/editorial token. Structured attribution runs with ``guess=False``;
only unresolved forms need a batched default comparison.

  python3 scripts/measure_grave_residue.py            # report
  python3 scripts/measure_grave_residue.py --write    # -> data/grave_residue.json
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
WORK_LEMMAS = DATA / "work_lemma_counts.tsv.gz"
FORM_LEMMAS = DATA / "cache" / "form_lemma.tsv.gz"
FORM_LEMMA_META = DATA / "cache" / "form_lemma_meta.json"
OUT = DATA / "grave_residue.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_lemma_map import (VARIA, PRINTED_FORMS,  # noqa: E402
                                lower_initial, to_acute,
                                trusted_citation_headwords)


ROUTE_LABELS = {
    "structured": "live structured Dilemma emission",
    "fallback": "OGC identity echo / no-guess fallback / model residue",
    "stale_cache": "stale cache residue",
    "accepted_source": "validator-accepted supplied or normalized lemma residue",
    "nonlexical": "nonlexical/editorial garbage",
}


def load_totals() -> dict[str, int]:
    out: dict[str, int] = {}
    with gzip.open(WORK_LEMMAS, "rt", encoding="utf-8") as f:
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[2].isdigit():
                out[p[1]] = out.get(p[1], 0) + int(p[2])
    return out


def has_greek_letter(value: str) -> bool:
    return any(
        unicodedata.category(char).startswith("L")
        and (0x0370 <= ord(char) <= 0x03FF or 0x1F00 <= ord(char) <= 0x1FFF)
        for char in value
    )


def cache_version() -> str | None:
    if not FORM_LEMMA_META.exists():
        return None
    return json.loads(FORM_LEMMA_META.read_text(encoding="utf-8")).get(
        "dilemma_version")


def installed_dilemma_version() -> str:
    import dilemma

    version_file = Path(dilemma.__file__).resolve().parent.parent / "VERSION"
    return version_file.read_text().strip() if version_file.exists() else "unknown"


def mapping_route(*, form: str, lemma: str, cache_is_current: bool,
                  nonlexical: bool, structured: list[dict],
                  current: str | None) -> str:
    """Classify one cache mapping after higher-confidence routes go first."""
    if nonlexical:
        return "nonlexical"
    if not cache_is_current:
        return "stale_cache"
    if any(candidate.get("lemma") == lemma
           and candidate.get("source") not in {"identity", "model", "nonlexical"}
           for candidate in structured):
        return "structured"
    if current == lemma:
        return "fallback"
    return "accepted_source"


def classify_cache_routes(grave: dict[str, int]) -> dict | str:
    """Attribute cache mappings that feed the grave residue.

    ``surface_tokens`` uses public_lexicon.tsv and is a mapping-level diagnostic;
    the authoritative residue token count remains the per-work rollup. The two
    can differ for quotation-mark aliases handled after cache lookup.
    """
    try:
        from dilemma import Dilemma
    except ImportError:
        return "Dilemma unavailable; route attribution omitted"

    d = Dilemma(lang="grc")
    by_route: dict[str, dict] = {
        route: {"what": label, "forms": 0, "lemmas": 0, "tokens": 0,
                "surface_tokens": 0, "examples": []}
        for route, label in ROUTE_LABELS.items()
    }
    nonlexical_lemmas = {
        lemma: tokens for lemma, tokens in grave.items()
        if not d.is_lexical(lemma)
    }
    nonlexical = by_route["nonlexical"]
    nonlexical["forms"] = None
    nonlexical["lemmas"] = len(nonlexical_lemmas)
    nonlexical["tokens"] = sum(nonlexical_lemmas.values())
    nonlexical["examples"] = [
        {"lemma": lemma, "tokens": tokens}
        for lemma, tokens in sorted(
            nonlexical_lemmas.items(), key=lambda item: -item[1]
        )[:12]
    ]
    lexical_grave = set(grave) - set(nonlexical_lemmas)
    base = {
        "what": "exclusive attribution of grave residue, with nonlexical "
                "lemmas decided directly and lexical mappings traced through "
                "the form-to-lemma cache",
        "current_dilemma_version": installed_dilemma_version(),
        "per_work_residue_tokens": sum(grave.values()),
        "lexical_residue_lemmas": len(lexical_grave),
        "lexical_residue_tokens": sum(grave[lemma] for lemma in lexical_grave),
        "by_route": by_route,
    }
    # This is the common post-1.2.3 result, and deliberately does not depend on
    # an ignored local cache. A clean checkout reproduces the committed audit.
    if not lexical_grave:
        base["cache_required"] = False
        return base
    if not FORM_LEMMAS.exists() or not FORM_LEMMA_META.exists():
        base["cache_required"] = True
        base["unattributed"] = "form_lemma cache or metadata absent"
        return base

    mappings = []
    with gzip.open(FORM_LEMMAS, "rt", encoding="utf-8") as handle:
        for line in handle:
            form, sep, lemma = line.rstrip("\n").partition("\t")
            if sep and lemma in lexical_grave:
                mappings.append((form, lemma))

    current_version = installed_dilemma_version()
    built_version = cache_version()
    cache_is_current = built_version in {"unknown", current_version}
    prepared = []
    compare_forms = []
    for form, lemma in mappings:
        is_nonlexical = not d.is_lexical(form)
        candidates = [] if is_nonlexical else [
            {"lemma": candidate.lemma, "source": candidate.source,
             "via": candidate.via}
            for candidate in d.lemmatize_verbose(form, guess=False)
        ]
        prepared.append((form, lemma, is_nonlexical, candidates))
        if cache_is_current and not is_nonlexical \
                and not any(c["lemma"] == lemma for c in candidates):
            compare_forms.append(form)

    current_outputs = {}
    for start in range(0, len(compare_forms), 5000):
        chunk = compare_forms[start:start + 5000]
        current_outputs.update(zip(chunk, d.lemmatize_batch(chunk)))

    route_lemmas: dict[str, set[str]] = defaultdict(set)
    for form, lemma, is_nonlexical, candidates in prepared:
        current = (lemma if any(c["lemma"] == lemma for c in candidates)
                   else current_outputs.get(form))
        route = mapping_route(
            form=form, lemma=lemma, cache_is_current=cache_is_current,
            nonlexical=is_nonlexical, structured=candidates, current=current,
        )
        bucket = by_route[route]
        bucket["forms"] += 1
        bucket["surface_tokens"] += PRINTED_FORMS.get(form, 0)
        route_lemmas[route].add(lemma)
        if len(bucket["examples"]) < 12:
            bucket["examples"].append({
                "form": form, "lemma": lemma,
                "surface_tokens": PRINTED_FORMS.get(form, 0),
                "current_default": current,
                "structured": candidates[:4],
            })
    for route, lemmas in route_lemmas.items():
        by_route[route]["lemmas"] = len(lemmas)

    mapped_tokens = sum(bucket["surface_tokens"] for bucket in by_route.values())
    base.update({
        "cache_required": True,
        "cache_dilemma_version": built_version,
        "cache_version_matches": cache_is_current,
        "mappings": len(mappings),
        "surface_tokens": mapped_tokens,
        "surface_vs_lexical_rollup_delta": (
            mapped_tokens - base["lexical_residue_tokens"]),
        "surface_token_caveat": "surface counts are diagnostic; per-work rollup "
                                "tokens are authoritative and may include aliases",
    })
    return base


# Dictionary headword inventories from the sibling public repo open-greek/dilemma
# (https://github.com/open-greek/dilemma), checked out beside this one. These are
# an authority INDEPENDENT of the lemmatizer that produced this residue, which is
# the gap the `why_no_external_authority` note used to record.
#
# Which lists, and why not all eleven. Included are the scholarly ancient and
# Byzantine lexica: LSJ and LSJ10, the Lexikon zur byzantinischen Graezitaet,
# DGE, Montanari's VLG, Cunliffe's Homeric lexicon, the Perseus aggregate of
# L&S/Pape/Bailly, and Aristarchus' Words in Progress. Excluded are
# ag_headwords, which is Wiktionary-derived and lists 72 of these grave lemmas
# as headwords themselves, which no real lexicon does, and mg_headwords, which
# is Modern Greek and answers a different question.
HEADWORD_FILES = ("lsj", "lsj10", "lbg", "dge", "vlg", "cunliffe", "pd", "wip")
DILEMMA = REPO.parent / "dilemma" / "data"


def load_headwords() -> tuple[set, list[dict]]:
    """(headword set, per-source provenance). Empty when the sibling checkout is
    absent, and the caller must then omit the partition rather than publish it
    as zero, which would read as a far stronger claim than no data supports."""
    words = trusted_citation_headwords()
    prov = []
    for name in HEADWORD_FILES:
        fp = DILEMMA / f"{name}_headwords.json"
        if not fp.exists():
            continue
        raw = json.loads(fp.read_text(encoding="utf-8"))
        got = {e["lemma"] if isinstance(e, dict) else e for e in raw}
        got = {unicodedata.normalize("NFC", w) for w in got if isinstance(w, str)}
        prov.append({"source": name, "entries": len(got),
                     "sha256": hashlib.sha256(fp.read_bytes()).hexdigest()})
    return words, prov


def by_correction_status(grave: dict) -> dict:
    """Where the residue physically sits, by how the text under it was made.

    This is the evidence the `limitation` label rests on, and until now it
    existed only in a comment on the issue: no script, no build rule, nothing to
    invalidate it. That is the failure this file was itself written to fix, one
    artifact over, so leaving it in a comment was the same mistake twice.

    The join is total or it is nothing. work_lemma_counts.tsv.gz is keyed on the
    row's urn, corpus_catalog.tsv on the slug, and those agreed for every work
    only after 2026-08-09 (philodemus.tlg1595-tlg601 carried a stale urn and its
    10,043 lemmatized tokens sat under a key the catalog does not have). So the
    unmatched bucket is published rather than dropped, and the buckets have to
    sum to the class or this refuses to write.
    """
    import csv
    import gzip

    cls, lem_total = {}, {}
    with open(DATA / "corpus_catalog.tsv", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            cls[row["slug"]] = row.get("correction") or "unknown"
            lem_total[row["slug"]] = int(row.get("tokens_lemmatized") or 0)

    tok: dict = {}
    lem: dict = {}
    unmatched = {"tokens": 0, "lemmas": 0, "keys": set()}
    with gzip.open(DATA / "work_lemma_counts.tsv.gz", "rt", encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t"):
            if len(row) < 3 or row[1] not in grave:
                continue
            k, n = row[0], int(row[2])
            if k not in cls:
                unmatched["tokens"] += n
                unmatched["lemmas"] += 1
                unmatched["keys"].add(k)
                continue
            c = cls[k]
            tok[c] = tok.get(c, 0) + n
            lem.setdefault(c, set()).add(row[1])

    stratum = {}
    for c in sorted(set(cls.values())):
        mass = sum(v for k, v in lem_total.items() if cls[k] == c)
        stratum[c] = {"grave_tokens": tok.get(c, 0),
                      "grave_lemmas": len(lem.get(c, ())),
                      "lemmatized_tokens_in_this_class": mass,
                      "rate": round(tok.get(c, 0) / mass, 6) if mass else None}
    ocr = sum(v["grave_tokens"] for c, v in stratum.items() if c != "not-ocr")
    ocr_mass = sum(v["lemmatized_tokens_in_this_class"]
                   for c, v in stratum.items() if c != "not-ocr")
    born = stratum.get("not-ocr", {})
    total = sum(v["grave_tokens"] for v in stratum.values()) + unmatched["tokens"]
    return {"what": "the grave-lemma class split by how the text under it was "
                    "produced, which is the evidence the `limitation` label "
                    "rests on",
            "classes_come_from": "the `correction` column of "
                                 "data/corpus_catalog.tsv, which is itself "
                                 "derived and not intrinsic to the text",
            "by_class": stratum,
            "unmatched": {"tokens": unmatched["tokens"],
                          "lemmas": unmatched["lemmas"],
                          "keys": sorted(unmatched["keys"])},
            "ocr_derived_rate": round(ocr / ocr_mass, 6) if ocr_mass else None,
            "born_digital_rate": born.get("rate"),
            "lift": (round((ocr / ocr_mass) / born["rate"], 2)
                     if ocr_mass and born.get("rate") else None),
            "reading": "the class is not an OCR problem that belongs to another "
                       "issue. It sits over born-digital text at a floor no text "
                       "repair reaches, and the raw-OCR stratum #2 scopes holds "
                       "only a small part of it.",
            "_sum": total}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    totals = load_totals()
    grave = {k: v for k, v in totals.items()
             if VARIA in unicodedata.normalize("NFD", k)}
    reachable, unreachable = {}, {}
    by_lemma_unreached = 0
    for lemma, n in grave.items():
        acute = to_acute(lemma)
        # Either spelling counts as the target: the capital may be positional,
        # and #19's fold handles that separately, so refusing to see the
        # lowercase acute here would understate what is reachable.
        # sorted, not a bare set: which candidate wins when both are printed
        # decided by set iteration order, so the published file changed between
        # runs (Κμὴ resolved to κμή or Κμή depending on the process).
        cands = sorted({acute, to_acute(lower_initial(lemma))} - {lemma})
        # Printed attestation is the real test; the lemma-table one is kept only
        # to show how much the old reference was hiding.
        hit = next((c for c in cands
                    if has_greek_letter(c) and PRINTED_FORMS.get(c, 0)), None)
        if not any(totals.get(c, 0) for c in cands):
            by_lemma_unreached += n
        (reachable if hit else unreachable)[lemma] = (n, hit)

    # Slightly above audit_lemma_table's count, which classifies each lemma once
    # and lets an earlier class claim some of these first. Same population.
    gt, rt = sum(grave.values()), sum(n for n, _ in reachable.values())
    ut = sum(n for n, _ in unreachable.values())

    # Independent authority: is either case of the repair target a dictionary
    # headword? The exact-case set also gates validate_lemma_map.py; allowing the
    # lowercase candidate here makes this broader report an upper bound because
    # positional-capital repair is measured separately by issue #19.
    heads, prov = load_headwords()
    backed = {}
    if heads:
        for lemma, n in grave.items():
            cands = sorted({to_acute(lemma), to_acute(lower_initial(lemma))} - {lemma})
            hit = next((c for c in cands if c in heads), None)
            if hit:
                backed[lemma] = (n, hit)
        # Control: comparably rare lemmas that carry no grave. Without it the
        # headline share means nothing, because rare lemmas are rare in
        # dictionaries too.
        rare_other = {k: v for k, v in totals.items()
                      if v <= 10 and VARIA not in unicodedata.normalize("NFD", k)}
        ctrl = sum(1 for k in rare_other if k in heads)
        rare_grave = {k: v for k, v in grave.items() if v <= 10}
        gctrl = sum(1 for k in rare_grave if k in heads or
                    any(c in heads for c in
                        sorted({to_acute(k), to_acute(lower_initial(k))} - {k})))
        backed_tokens = sum(n for n, _ in backed.values())
        print(f"  headword-backed {len(backed):>6,} lemmas "
              f"{backed_tokens:>8,} tokens "
              f"({backed_tokens / gt if gt else 0:.1%} of the residue), "
              f"against {len(heads):,} headwords from {len(prov)} lexica")
        print(f"    control: {ctrl / max(len(rare_other), 1):.1%} of non-grave "
              f"lemmas at <=10 tokens are headwords, against "
              f"{gctrl / max(len(rare_grave), 1):.1%} of grave ones")
    else:
        print("  headword-backed: sibling checkout open-greek/dilemma absent, "
              "partition omitted")

    corpus_total = sum(totals.values())
    print(f"grave residue: {len(grave):,} lemmas, {gt:,} tokens "
          f"({gt / corpus_total if corpus_total else 0:.6%} of the lemmatized corpus)")
    print(f"  surface-reachable {len(reachable):>6,} lemmas {rt:>8,} tokens "
          f"{rt / gt if gt else 0:>6.1%}  the corpus prints an acute counterpart")
    print(f"  surface-unreachable {len(unreachable):>6,} lemmas {ut:>8,} tokens "
          f"{ut / gt if gt else 0:>6.1%}  the corpus prints no acute counterpart under "
          f"either case")
    print(f"\n  measured the OLD way, against the lemma table rather than the "
          f"printed text,\n  the unreachable share reads {by_lemma_unreached:,} "
          f"tokens ({by_lemma_unreached / gt if gt else 0:.1%}). That difference is the "
          f"reference\n  being narrower than the table it governs, not a fact "
          f"about the residue.")
    print("\n  largest unreachable, which is what the residue actually is:")
    for lemma, (n, _) in sorted(unreachable.items(), key=lambda kv: -kv[1][0])[:12]:
        print(f"    {lemma:<16} {n:>6,}")
    print("\n  largest reachable, and note that reachable does NOT mean worth "
          "repairing:\n  a target attested at 2 or 10 tokens is shrapnel too, so "
          "moving onto it\n  empties the audit class without producing a headword:")
    for lemma, (n, hit) in sorted(reachable.items(), key=lambda kv: -kv[1][0])[:8]:
        print(f"    {lemma:<16} {n:>6,} -> {hit} ({totals.get(hit, 0):,})")

    split = by_correction_status(grave)
    if split["_sum"] != sum(grave.values()):
        raise SystemExit(f"ERROR: correction-status buckets sum to "
                         f"{split['_sum']}, class holds {sum(grave.values())}")
    del split["_sum"]
    print(f"  by correction status: " + ", ".join(
        f"{c} {v['grave_tokens']:,} ({v['rate']:.4%})" if v["rate"] is not None
        else f"{c} {v['grave_tokens']:,}"
        for c, v in sorted(split["by_class"].items())))
    lift = f"{split['lift']}x" if split["lift"] is not None else "n/a"
    print(f"    OCR-derived {split['ocr_derived_rate']:.4%} against born-digital "
          f"{split['born_digital_rate']:.4%}, a {lift} lift; "
          f"unmatched {split['unmatched']['tokens']}")

    routes = classify_cache_routes(grave)
    if isinstance(routes, str):
        print(f"  cache routes: {routes}")
    else:
        print("  cache routes:")
        for route in ROUTE_LABELS:
            bucket = routes["by_route"][route]
            forms = ("n/a" if bucket["forms"] is None
                     else f"{bucket['forms']:,}")
            tokens = bucket["tokens"] or bucket["surface_tokens"]
            print(f"    {route:<15} {forms:>6} forms "
                  f"{bucket['lemmas']:>6,} lemmas {tokens:>8,} tokens")
        if routes.get("cache_required"):
            if routes.get("unattributed"):
                print(f"    lexical attribution incomplete: "
                      f"{routes['unattributed']}")
            else:
                print(f"    cache Dilemma {routes['cache_dilemma_version']}; "
                      f"current {routes['current_dilemma_version']}; "
                      f"version match={routes['cache_version_matches']}")

    if not args.write:
        print("\nreport only; re-run with --write.")
        return
    OUT.write_text(json.dumps({
        "what": "grave-lemma residue measured by surface reachability, "
                "independent headword backing, and cache/emission route",
        "issue": "open-greek/open-greek-corpus#4",
        "source": "data/work_lemma_counts.tsv.gz, plus the `correction` column "
                  "of data/corpus_catalog.tsv for the by_correction_status block",
        "by_correction_status": split,
        "cache_route_attribution": routes,
        "why_not_the_annotation_exports": "the annotation exports come from the "
            "same lemmatizer that produced this residue, so they cannot "
            "independently confirm a headword for it. Dictionary headword "
            "inventories can, and the headword_backed block below is that test.",
        "headword_backed": ({
            "what": "grave lemmas whose acute counterpart is a headword in a "
                    "published lexicon, which is an authority independent of the "
                    "lemmatizer that produced this residue",
            "repair_rule_relation": "the exact-case target set is the same "
                                    "independent inventory that gates OGC grave "
                                    "normalization. This measurement also checks "
                                    "a lowercase target, so its count is an upper "
                                    "bound that includes issue #19 candidates.",
            "sources": prov,
            "excluded_sources": {
                "ag_headwords": "Wiktionary-derived, and lists 72 of these grave "
                                "lemmas as headwords themselves, which no lexicon "
                                "does",
                "mg_headwords": "Modern Greek, a different question",
            },
            "headwords": len(heads),
            "lemmas": len(backed),
            "tokens": sum(n for n, _ in backed.values()),
            "share_of_residue": round(
                sum(n for n, _ in backed.values()) / gt if gt else 0, 4),
            "control": {
                "what": "the same test on lemmas that carry no grave, at the same "
                        "rarity, because rare lemmas are rare in dictionaries too",
                "non_grave_lemmas_le_10_tokens_backed": round(
                    ctrl / max(len(rare_other), 1), 4),
                "grave_lemmas_le_10_tokens_backed": round(
                    gctrl / max(len(rare_grave), 1), 4),
            },
            "largest": [{"lemma": k, "tokens": n, "headword": h}
                        for k, (n, h) in sorted(
                            backed.items(), key=lambda kv: -kv[1][0])[:20]],
        } if heads else "sibling checkout open-greek/dilemma absent; not measured"),
        "lemmas": len(grave), "tokens": gt,
        "share_of_lemmatized_corpus": round(
            gt / corpus_total if corpus_total else 0, 10),
        "reachable": {"lemmas": len(reachable), "tokens": rt,
                      "caveat": "surface-reachable is not a repair gate or an "
                                "estimate of what is worth touching: "
                                "many targets are themselves shrapnel attested at a "
                                "handful of tokens (λλά at 10, μονονοχί at 2), and "
                                "merging onto those empties the audit class without "
                                "producing a headword"},
        "unreachable": {"lemmas": len(unreachable), "tokens": ut,
                        "note": "the corpus prints no acute counterpart under "
                                "either case, so a rule that moves a grave lemma "
                                "onto its acute has no surface target. This does "
                                "not by itself distinguish OCR, an inflected "
                                "non-headword, or an editorial symbol; use "
                                "cache_route_attribution for that distinction"},
        "superseded": {"was": "an earlier version of this file reported the "
                              "unreachable share as 77.4% and said no rule of "
                              "this shape could reach it regardless of threshold",
                       "wrong_because": "it tested whether the acute exists as a "
                                        "LEMMA in the per-work table. The accent "
                                        "argument is about the printed text, and "
                                        "the rule's own reference table was "
                                        "narrower than the table it governs "
                                        "(83,078 lemmas against 275,871)",
                       "measured_the_old_way_tokens": by_lemma_unreached},
        "largest_unreachable": [
            {"lemma": k, "tokens": n}
            for k, (n, _) in sorted(unreachable.items(),
                                    key=lambda kv: -kv[1][0])[:40]],
        "largest_reachable": [
            {"lemma": k, "tokens": n, "target": h, "target_tokens": totals.get(h, 0)}
            for k, (n, h) in sorted(reachable.items(),
                                    key=lambda kv: -kv[1][0])[:40]],
    }, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
