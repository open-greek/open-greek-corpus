#!/usr/bin/env python3
"""Ingest the DFHG (Digital Fragmenta Historicorum Graecorum) corrected text of
Mueller's five FHG volumes, superseding our page-keyed OCR of the same edition.

DFHG (dfhg-project.org, Berti / Univ. Leipzig, CC BY-SA 4.0) is a manually
corrected transcription of the SAME Didot edition our FHG OCR works came from,
so it outranks OCR on the precedence ladder (a corrected human transcription
beats machine OCR of the same pages) while carrying the same PD source text.
Verified better than our qwen36 OCR in side-by-sides (fixes meaning-destroying
errors), and it adds volume 5 (5.1 + 5.2), which we never OCR'd.

Source layout (clone the six github.com/dfhg-project repos under sources/dfhg/):
  sources/dfhg/volume_{1,2,3,4,5_1,5_2}/data/xml/<AUTHOR>.xml

One file per FHG author; <extant_text>/<fragment> elements carry the Greek
<text>, the printed FHG <page>, the LOFTS cite_urn (a per-author fragment
sequence), plus witness/work/book labels. Latin <translation>/<commentary> are
not served.

Mapping to served works is PAGE-ANCHORED, per fragment, not name-matched. Every
existing FHG work's loci embed a scan page stem (theopompus_hist_fhg1_0123.4);
each DFHG fragment carries its printed FHG page; per scan base the (stem -
printed page) offset is constant. Offsets are seeded from author works whose
DFHG name matches their slug exactly, and bases with no name anchor (the second
scans of vols 2/3 backing the whole-volume remainder works) get a CONTENT
anchor: distinctive DFHG fragments are located in the served rows by bigram
overlap and the offset is voted. Content decides, names only seed (the Isyllus
lesson): NICOLAUS_DAMASCENUS lands on nicolaus-history.fragmenta because the
pages coincide.

Each fragment is assigned to the DEDICATED served work covering its page (an
author split across several works - Phlegon's De mirabilibus vs Olympiades -
replaces each of them with the right slice); fragments no dedicated work covers
(carve-outs from catch-all remainders, and all of volume 5) go to a per-author
work. Verdict summary in data/dfhg_mapping.json (rewritten every run):

  replace   work fully page-covered by its DFHG slice -> slice replaces it; the
            OCR file is displaced to corpus_secondary
  carve/new leftover fragments -> per-author work (<author>.fragmenta)
  skip      no Greek text (Latin-only author)
  special   NOT written: weak page coverage, a slug conflict, or the author is
            already served from open TEI (first1k/perseus fragment collections
            must not be duplicated by a parallel DFHG work)

Catch-all remainder works (the whole-volume slugs the FHG dissolution left
serving prolegomena/index/unmapped pages) then shed the rows DFHG now covers:
a row on a DFHG-covered printed page is displaced to corpus_secondary only if
its Greek bigrams are >=50% contained in that page's DFHG text (mixed boundary
pages keep their unmatched rows as primary - no silent loss).

No TLG urn is fabricated; new slugs without a crosswalk entry are flagged in
the report for a later canon pass.

Record format:
  {"urn": slug, "edition": "dfhg", "locus": "<vol>.<cite_no>",
   "source": "dfhg", "license": "CC-BY-SA-4.0", "text": ...,
   "page": <FHG printed page>, "work": <work label>, "witness": ...,
   "dfhg_flag": true when the text carries a (??) unresolved-reading marker}

Text normalization: NFC + the DFHG space+U+0313 elision artifact becomes the
corpus-standard U+2019 glued to its word. (??) markers are KEPT and flagged.

  python scripts/ingest_dfhg.py            # dry-run: report + mapping only
  python scripts/ingest_dfhg.py --write    # apply (then run reconcile_corpus_editions.py)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import lxml.etree as ET

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "sources" / "dfhg"
CORPUS = REPO / "data" / "corpus"
SECONDARY = REPO / "data" / "corpus_secondary"
MAPPING = REPO / "data" / "dfhg_mapping.json"
EDITIONS = REPO / "data" / "corpus_editions.json"

_GK = re.compile(r"[Ͱ-Ͽἀ-῿]")
_GK_LETTER = re.compile(r"[Ͱ-Ͽἀ-῿]")
# scan page stem inside an OCR locus: <base>_<NNNN>.<line> (a base may START
# with fhg: fhg_vol3_mueller_diocles_rhodius)
_STEM = re.compile(r"^(?P<base>.*fhg[0-9a-z_]*)_(?P<num>\d{4})\.")
# the DFHG elision artifact: word, SPACE, combining comma above -> word + U+2019
_ELISION = re.compile(" [̓᾿]")

VOL_NO = {"volume_1": 1, "volume_2": 2, "volume_3": 3, "volume_4": 4,
          "volume_5_1": 5, "volume_5_2": 5}
TEI_SOURCES = {"first1k", "perseus", "galenus_verbatim"}

# a dedicated (single-author) work vs a whole-volume remainder: page count cap
def _dedicated(n_stems: int, n_author_pages: int) -> bool:
    return n_stems <= 4 * n_author_pages + 20

DISPLACE_REASON = ("superseded by DFHG (Berti/Leipzig CC BY-SA 4.0), the corrected "
                   "transcription of the same Mueller FHG edition")

MIN_REPLACE_COVER = 0.5     # slice must page-cover this much of a work to replace it
MIN_ROW_CONTAIN = 0.5       # catch-all row bigram containment to displace


def norm_author(name: str) -> str:
    d = unicodedata.normalize("NFD", name.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", d).strip("-")


def clean_text(raw: str) -> str:
    t = unicodedata.normalize("NFC", " ".join(raw.split()))
    return _ELISION.sub("’", t)


def _norm_tok(t: str) -> str:
    d = unicodedata.normalize("NFD", t.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    return "".join(c for c in d if _GK_LETTER.match(c))


def _bigrams(text: str) -> set:
    toks = [w for t in text.split() if (w := _norm_tok(t))]
    return {(toks[i], toks[i + 1]) for i in range(len(toks) - 1)}


def parse_dfhg():
    out = []
    parser = ET.XMLParser(recover=True)
    for xml in sorted(SRC.glob("volume_*/data/xml/*.xml")):
        vol = VOL_NO[xml.relative_to(SRC).parts[0]]
        root = ET.parse(str(xml), parser).getroot()
        if root is None:
            print(f"  UNPARSEABLE {xml}", file=sys.stderr)
            continue
        author, frags = None, []
        for el in root:
            if el.tag not in ("extant_text", "fragment"):
                continue
            if author is None:
                a = el.find("author")
                author = (a.text or "").strip() if a is not None else ""
            cite = el.get("cite_urn") or ""
            cite_no = cite.rsplit(":", 1)[-1] if ":" in cite else ""
            fld = {f.tag: (f.text or "").strip() for f in el}
            page = fld.get("page", "")
            frags.append({
                "no": cite_no or str(len(frags) + 1),
                "page": int(page) if page.isdigit() else None,
                "work": fld.get("work", ""),
                "witness": fld.get("witness", ""),
                "text": clean_text(fld.get("text", "")),
            })
        if not frags:
            continue
        name = norm_author(author or xml.stem.replace("_", " "))
        out.append({"file": str(xml.relative_to(SRC)), "volume": vol,
                    "author": author, "name": name, "frags": frags,
                    "pages": {f["page"] for f in frags if f["page"] is not None},
                    "greek": sum(len(_GK.findall(f["text"])) for f in frags)})
    return out


def served_fhg_coverage():
    """{slug: {base: {stem_num: [row bigram sets]}}} for every primary work with
    loci on an FHG scan base. Bigram sets power the content anchoring and the
    catch-all containment gate; rows are kept in file order per stem."""
    cov: dict = defaultdict(lambda: defaultdict(dict))
    for fp in sorted(CORPUS.glob("*.jsonl")):
        slug = fp.name[:-6]
        with fp.open(encoding="utf-8") as f:
            for line in f:
                if '"locus"' not in line or "fhg" not in line:
                    continue
                r = json.loads(line)
                m = _STEM.match(r.get("locus", ""))
                if m:
                    cov[slug][m.group("base")].setdefault(
                        int(m.group("num")), []).append(_bigrams(r.get("text", "")))
    return {s: {b: st for b, st in bb.items()} for s, bb in cov.items()}


def base_volume(base: str) -> int | None:
    m = re.search(r"fhg[_ ]?(?:v(?:ol)?[_ ]?)?(\d)", base)
    return int(m.group(1)) if m else None


def derive_offsets(entries, coverage):
    """{base: offset}. Name anchors first; bases left without one (the second
    scans backing whole-volume remainders) get a content anchor: locate a few
    long distinctive DFHG fragments in the served rows by bigram overlap."""
    by_author = defaultdict(list)
    for slug in coverage:
        by_author[slug.split(".")[0]].append(slug)
    votes: dict[str, Counter] = defaultdict(Counter)
    anchors = []
    for e in entries:
        if not e["pages"] or e["volume"] == 5:
            continue
        for slug in by_author.get(e["name"], []):
            for base, stems in coverage[slug].items():
                if not stems or not _dedicated(len(stems), len(e["pages"])):
                    continue
                off_lo = min(stems) - min(e["pages"])
                off_hi = max(stems) - max(e["pages"])
                if abs(off_lo - off_hi) <= 3:
                    votes[base][(e["volume"], off_lo)] += 1
                    anchors.append({"author": e["author"], "slug": slug,
                                    "base": base, "volume": e["volume"],
                                    "offset": off_lo, "kind": "name"})
    # Content verification for EVERY base, voting the (volume, offset) PAIR:
    # an off-by-one offset would displace the wrong pages (rows on pages DFHG
    # does not actually cover), and a base's NAME can lie about
    # its volume (xanthus_fhg_v1 is a vol-4 scan serving Sostratus), so both
    # are taken from where the DFHG fragments actually land, name votes only
    # seed. Returns {base: {"volume": v, "offset": o}}.
    offsets: dict[str, dict] = {}
    all_bases = {b for bb in coverage.values() for b in bb}
    for base in sorted(all_bases):
        rows_by_stem: dict[int, list] = defaultdict(list)
        base_toks = set()
        for slug, bb in coverage.items():
            for num, rows in bb.get(base, {}).items():
                rows_by_stem[num].extend(rows)
            if base in bb:
                base_toks |= _name_tokens(slug.split(".")[0])
        name_vol = base_volume(base)
        spread = [(e, f) for e in entries
                  if e["volume"] == name_vol and e["volume"] != 5
                  for f in e["frags"]
                  if f["page"] is not None and len(f["text"]) > 400]
        targeted = [(e, f) for e in entries
                    if e["volume"] != 5 and (_name_tokens(e["name"]) & base_toks)
                    for f in e["frags"]
                    if f["page"] is not None and len(f["text"]) > 80]
        probes = targeted[:120] + spread[::max(1, len(spread) // 60)]
        ctr: Counter = Counter()
        for e, f in probes:
            fb = _bigrams(f["text"])
            if len(fb) < 8:
                continue
            best_num, best_ov = None, 0.0
            for num, rows in rows_by_stem.items():
                ov = max((len(fb & rb) / len(fb) for rb in rows if rb), default=0.0)
                if ov > best_ov:
                    best_num, best_ov = num, ov
            if best_num is not None and best_ov >= 0.35:
                ctr[(e["volume"], best_num - f["page"])] += 1
        top = ctr.most_common(1)[0] if ctr else (None, 0)
        name_ctr = votes.get(base, Counter())
        unanimous_agree = (top[1] >= 2 and len(ctr) == 1 and name_ctr
                           and name_ctr.most_common(1)[0][0] == top[0])
        strong = top[1] >= 5 and top[1] >= 0.6 * sum(ctr.values())
        if unanimous_agree or strong:
            vol, off = top[0]
            offsets[base] = {"volume": vol, "offset": off}
            anchors.append({"base": base, "volume": vol, "offset": off,
                            "kind": "content", "votes": {str(k): v for k, v in ctr.items()},
                            "name_votes": {str(k): v for k, v in name_ctr.items()}})
            if name_ctr and name_ctr.most_common(1)[0][0] != top[0]:
                print(f"  WARNING: base {base}: content (vol,off) {top[0]} != "
                      f"name-vote {dict(name_ctr)}", file=sys.stderr)
        elif name_ctr and name_ctr.most_common(1)[0][1] >= 3:
            vol, off = name_ctr.most_common(1)[0][0]
            offsets[base] = {"volume": vol, "offset": off}
            anchors.append({"base": base, "volume": vol, "offset": off,
                            "kind": "name-fallback",
                            "votes": {str(k): v for k, v in ctr.items()},
                            "name_votes": {str(k): v for k, v in name_ctr.items()}})
            print(f"  WARNING: base {base}: weak content votes {dict(ctr)}, "
                  f"using name-anchor {(vol, off)}", file=sys.stderr)
        else:
            print(f"  WARNING: base {base} DROPPED - no confident (vol, offset) "
                  f"(content {dict(ctr)}, name {dict(name_ctr)})", file=sys.stderr)
    return offsets, anchors


def _name_tokens(s: str) -> set:
    return set(s.split("-")) - {"history", "hist", "philosophy", "geography",
                                "music", "rhetor", "grammar", "fragmenta"}


def build_mapping(entries, coverage, offsets):
    editions = json.loads(EDITIONS.read_text(encoding="utf-8")) if EDITIONS.exists() else {}
    tei_authors = {slug.split(".")[0] for slug, v in editions.items()
                   if v.get("source") in TEI_SOURCES}

    # printed-page footprint per served work: {slug: {volume: set(pages)}},
    # deduped across redundant scans of the same volume
    work_pages: dict = defaultdict(lambda: defaultdict(set))
    for slug, bb in coverage.items():
        for base, stems in bb.items():
            bo = offsets.get(base)
            if bo is None:
                continue
            work_pages[slug][bo["volume"]] |= {num - bo["offset"] for num in stems}

    # DFHG text per (volume, printed page), for the shedding containment gate
    page_text_bigrams: dict = defaultdict(set)

    mapping = {"offsets": offsets, "authors": {}, "slices": {},
               "catchall_displace": {}, "specials": {}}
    slice_claims: dict = {}          # target slug -> author file (one owner)
    covered_pages: set = set()       # (vol, page) served from DFHG after apply

    def serve_pages(vol, frags):
        for f in frags:
            if f["page"] is not None and _GK.search(f["text"]):
                covered_pages.add((vol, f["page"]))
                page_text_bigrams[(vol, f["page"])] |= _bigrams(f["text"])

    for e in entries:
        key = e["file"]
        rec = {"author": e["author"], "volume": e["volume"], "greek": e["greek"],
               "n_frags": len(e["frags"]),
               "pages": [min(e["pages"]), max(e["pages"])] if e["pages"] else None}
        mapping["authors"][key] = rec
        if e["greek"] == 0:
            rec["verdict"] = "skip"
            continue

        # replace candidates: name-affine dedicated works with real page overlap.
        # Name affinity is required because Mueller prints several micro-authors
        # per page; pages alone cannot say who owns a one-fragment work.
        etoks = _name_tokens(e["name"])
        cands = []
        for slug, vols in work_pages.items():
            wpages = vols.get(e["volume"])
            if not wpages or len(wpages) > 3 * len(e["pages"]) + 10:
                continue                      # volume remainder, not a candidate
            if not (etoks & _name_tokens(slug.split(".")[0])):
                continue
            cover = len(e["pages"] & wpages) / len(wpages)
            if cover >= MIN_REPLACE_COVER:
                cands.append((cover, len(wpages), slug))
        # assign each fragment to the best candidate work covering its page
        cands.sort(reverse=True)
        slices: dict[str, list] = defaultdict(list)
        leftover = []
        for f in e["frags"]:
            tgt = None
            if f["page"] is not None:
                for _c, _n, slug in cands:
                    if f["page"] in work_pages[slug][e["volume"]]:
                        tgt = slug
                        break
            (slices[tgt] if tgt else leftover).append(f)

        rec["targets"] = {}
        for tgt, fr in sorted(slices.items(), key=lambda kv: -len(kv[1])):
            if tgt is None:
                continue
            gk = sum(len(_GK.findall(f["text"])) for f in fr)
            if slice_claims.get(tgt, key) != key:
                mapping["specials"][f"{key}->{tgt}"] = {
                    "why": f"work already claimed by {slice_claims[tgt]}",
                    "greek": gk}
                leftover.extend(fr)
                continue
            if not any(_GK.search(f["text"]) for f in fr):
                leftover.extend(fr)
                continue
            slice_claims[tgt] = key
            cover = next(c for c, _n, s in cands if s == tgt)
            rec["targets"][tgt] = {"n_frags": len(fr), "greek": gk,
                                   "cover": round(cover, 3)}
            mapping["slices"].setdefault(key, {})[tgt] = [f["no"] for f in fr]
            serve_pages(e["volume"], fr)

        leftover_gk = sum(len(_GK.findall(f["text"])) for f in leftover)
        if leftover_gk:
            if e["name"] in tei_authors and not rec["targets"]:
                rec["verdict"] = "special"
                mapping["specials"][key] = {
                    "why": f"author served from open TEI ({e['name']}.*) - "
                           f"parallel DFHG work would duplicate content",
                    "greek": leftover_gk}
            else:
                slug = new_slug(e)
                rec["leftover_slug"] = slug
                rec["leftover_greek"] = leftover_gk
                rec["leftover_frags"] = [f["no"] for f in leftover]
                serve_pages(e["volume"], leftover)
        if "verdict" not in rec:
            if rec["targets"] and rec.get("leftover_slug"):
                rec["verdict"] = "replace+carve"
            elif rec["targets"]:
                rec["verdict"] = "replace"
            elif rec.get("leftover_slug"):
                rec["verdict"] = "carve" if e["pages"] else "new"
            else:
                rec["verdict"] = "skip"

    # shedding plan: every served work NOT replaced sheds its rows on
    # DFHG-covered pages (the apply step gates each row by bigram containment)
    plan: dict = defaultdict(list)
    for slug, bb in coverage.items():
        if slug in slice_claims:
            continue
        for base, stems in bb.items():
            bo = offsets.get(base)
            if bo is None:
                continue
            for num in stems:
                if (bo["volume"], num - bo["offset"]) in covered_pages:
                    plan[slug].append((base, num))
    mapping["catchall_displace"] = {s: sorted(v) for s, v in plan.items()}
    mapping["_page_bigrams"] = page_text_bigrams        # in-memory only
    return mapping


_slug_taken = None


def new_slug(e) -> str:
    global _slug_taken
    if _slug_taken is None:
        _slug_taken = ({p.name[:-6] for p in CORPUS.glob("*.jsonl")} |
                       {p.name[:-6] for p in SECONDARY.glob("*.jsonl")})
    base = f"{e['name']}.fragmenta"
    slug = base if base not in _slug_taken else f"{e['name']}.fragmenta-fhg{e['volume']}"
    _slug_taken.add(slug)
    return slug


def records_for(e, slug, frag_nos=None):
    recs = []
    for f in e["frags"]:
        if frag_nos is not None and f["no"] not in frag_nos:
            continue
        if not _GK.search(f["text"]):
            continue
        r = {"urn": slug, "edition": "dfhg", "locus": f"{e['volume']}.{f['no']}",
             "source": "dfhg", "license": "CC-BY-SA-4.0", "text": f["text"]}
        if f["page"] is not None:
            r["page"] = f["page"]
        if f["work"]:
            r["work"] = f["work"]
        if f["witness"]:
            r["witness"] = f["witness"]
        if "(??)" in f["text"]:
            r["dfhg_flag"] = True
        recs.append(r)
    return recs


def displace_file(slug: str) -> None:
    src = CORPUS / f"{slug}.jsonl"
    dst = SECONDARY / f"{slug}.jsonl"
    recs = [json.loads(l) for l in src.open(encoding="utf-8") if l.strip()]
    for r in recs:
        r["rank"] = "secondary"
        r["secondary_reason"] = DISPLACE_REASON
    with dst.open("a" if dst.exists() else "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    src.unlink()


def apply_mapping(entries, mapping):
    by_file = {e["file"]: e for e in entries}
    page_bigrams = mapping.pop("_page_bigrams")
    offsets = mapping["offsets"]
    stats = Counter()
    SECONDARY.mkdir(parents=True, exist_ok=True)

    # 1. replacement slices + carve/new works
    for key, rec in mapping["authors"].items():
        e = by_file[key]
        for tgt, nos in mapping["slices"].get(key, {}).items():
            recs = records_for(e, tgt, set(nos))
            if not recs:
                continue
            if (CORPUS / f"{tgt}.jsonl").exists():
                displace_file(tgt)
            (CORPUS / f"{tgt}.jsonl").write_text(
                "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs),
                encoding="utf-8")
            stats["works_replaced"] += 1
            stats["greek_in"] += sum(len(_GK.findall(r["text"])) for r in recs)
        slug = rec.get("leftover_slug")
        if slug:
            recs = records_for(e, slug, set(rec["leftover_frags"]))
            if recs:
                out = CORPUS / f"{slug}.jsonl"
                if out.exists():
                    print(f"  ABORT-SKIP {slug}: unexpected existing file",
                          file=sys.stderr)
                    continue
                out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                       for r in recs), encoding="utf-8")
                stats["works_new"] += 1
                stats["greek_in"] += sum(len(_GK.findall(r["text"])) for r in recs)

    # 2. catch-all shedding, bigram-gated
    for slug, pairs in mapping["catchall_displace"].items():
        fp = CORPUS / f"{slug}.jsonl"
        if not fp.exists():
            continue
        drop = {(b, n) for b, n in map(tuple, pairs)}
        keep, moved = [], []
        for line in fp.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            m = _STEM.match(r.get("locus", ""))
            if not m or (m.group("base"), int(m.group("num"))) not in drop:
                keep.append(r)
                continue
            bo = offsets[m.group("base")]
            page = int(m.group("num")) - bo["offset"]
            vol = bo["volume"]
            pb = page_bigrams.get((vol, page), set())
            rb = _bigrams(r.get("text", ""))
            if rb and len(rb & pb) / len(rb) >= MIN_ROW_CONTAIN:
                r["rank"] = "secondary"
                r["secondary_reason"] = DISPLACE_REASON
                moved.append(r)
            else:
                keep.append(r)     # mixed page: unmatched row stays primary
        if not moved:
            continue
        if keep:
            fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                                  for r in keep), encoding="utf-8")
        else:
            fp.unlink()          # every row superseded: nothing left to serve
            stats["works_emptied"] += 1
        if moved:
            with (SECONDARY / f"{slug}.jsonl").open("a", encoding="utf-8") as f:
                for r in moved:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
        stats["catchall_rows_displaced"] += len(moved)
        print(f"  catch-all {slug}: kept {len(keep)}, displaced {len(moved)}")

    print(f"\napply: {dict(stats)}")
    print("now run: python scripts/reconcile_corpus_editions.py")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="apply the mapping")
    args = ap.parse_args()

    print("parsing DFHG XML ...", file=sys.stderr)
    entries = parse_dfhg()
    print(f"  {len(entries)} author files, "
          f"{sum(e['greek'] for e in entries):,} Greek chars", file=sys.stderr)
    print("scanning served FHG coverage ...", file=sys.stderr)
    coverage = served_fhg_coverage()
    print(f"  {len(coverage)} served works on FHG scan bases", file=sys.stderr)
    offsets, anchors = derive_offsets(entries, coverage)
    print(f"  offsets ({len(anchors)} anchors): {offsets}", file=sys.stderr)
    mapping = build_mapping(entries, coverage, offsets)

    verdicts = Counter(r.get("verdict", "?") for r in mapping["authors"].values())
    greek = Counter()
    for r in mapping["authors"].values():
        greek[r.get("verdict", "?")] += r["greek"]
    print("\nverdicts:", dict(verdicts))
    print("greek by verdict:", {k: f"{v:,}" for k, v in greek.items()})
    n_rows = {s: len(v) for s, v in mapping["catchall_displace"].items()}
    print(f"catch-all shedding: {len(n_rows)} works, {sum(n_rows.values())} stems")
    for s, n in sorted(n_rows.items(), key=lambda kv: -kv[1])[:12]:
        print(f"   {n:>5}  {s}")
    if mapping["specials"]:
        print(f"SPECIALS ({len(mapping['specials'])}):")
        for k, r in sorted(mapping["specials"].items()):
            print(f"  {k}: {r.get('why')} [{r.get('greek', 0):,} gk]")

    dump = {k: v for k, v in mapping.items() if not k.startswith("_")}
    dump["anchors"] = anchors
    MAPPING.write_text(json.dumps(dump, ensure_ascii=False, indent=1,
                                  sort_keys=True, default=sorted))
    print(f"mapping -> {MAPPING.relative_to(REPO)}")

    if args.write:
        apply_mapping(entries, mapping)


if __name__ == "__main__":
    main()
