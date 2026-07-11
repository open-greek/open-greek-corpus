#!/usr/bin/env python3
"""Build the slug<->TLG crosswalk: the ONE place the TLG/CTS numbering is recorded.

Every corpus work is primarily identified by its registry author.work slug. The
TLG number (and its CTS URN) - the id other sources key on - is kept only here,
as a lookup, never as the primary id on files, records, or metadata keys.

Reads data/source_registry.json (works keyed by slug, with aliases.cts for the
~98% already registered) and, for the handful of corpus works the registry has no
slug for yet, mints a slug from the vendored TLG canon (author name + work title)
using the registry's own normalize_slug, so the minted slugs match house style.

Writes:
  data/tlg_crosswalk.json   slug -> {cts, tlg, author_slug, title}
  data/tlg_crosswalk.tsv    slug<TAB>cts_urn<TAB>tlg   (human-readable page)
And, for the one-time migration, a tlg_stem -> slug_stem rename map to stdout/opt.
"""
from __future__ import annotations
import json, os, re, sys, glob, argparse
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from source_identity import normalize_slug  # noqa: E402

CANON = Path(os.path.expanduser("~/Documents/tlge-tools/data/tlg_canon.json"))


def load_canon():
    c = json.load(open(CANON))
    authors = {a: d.get("name", "") for a, d in c["authors"].items()}          # '0001' -> NAME
    # works: list; index by (tlg_id, work_id-ish). Find title-ish + work id fields defensively.
    wl = c["works"]
    wtitle = {}
    for w in wl:
        tlg = w.get("tlg_id") or w.get("author") or ""
        wid = str(w.get("work_id") or w.get("work") or w.get("id") or "")
        title = w.get("title") or w.get("name") or w.get("la") or ""
        if tlg and wid:
            wtitle[(tlg, wid.lstrip("tlg").zfill(3))] = title
    return authors, wtitle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emit-rename-map", help="write tlg_stem->slug_stem JSON here (for migration)")
    args = ap.parse_args()

    reg = json.load(open(REPO / "data/source_registry.json"))
    cts2slug, slug_taken = {}, set(reg["works"].keys())
    for slug, w in reg["works"].items():
        cts = (w.get("aliases") or {}).get("cts")
        if cts:
            cts2slug[cts] = slug

    # tlgAUTHOR -> author_slug, from any registered work of that author
    authnum2slug = {}
    for slug, w in reg["works"].items():
        cts = (w.get("aliases") or {}).get("cts") or ""
        m = re.search(r"tlg(\d+)\.tlg\d+", cts)
        if m and w.get("author"):
            authnum2slug.setdefault("tlg" + m.group(1), w["author"])

    canon_auth, canon_wtitle = load_canon()

    corpus = [os.path.basename(f)[:-6] for f in glob.glob(str(REPO / "data/corpus/*.jsonl"))]
    # include TLG "X" works (dubia/spuria: tlgX01 etc.) as well as numeric work ids
    tlg_files = [u for u in corpus if re.match(r"tlg\d+\.tlg[X0-9]+$", u)]

    # seed from the existing crosswalk so re-running is idempotent and preserves
    # entries not derivable from tlg-named files (post-migration everything is a slug;
    # works added directly, e.g. off-registry Canon finds, live only here)
    cw_path = REPO / "data" / "tlg_crosswalk.json"
    crosswalk = json.loads(cw_path.read_text(encoding="utf-8")) if cw_path.exists() else {}
    rename, minted, unresolved = {}, [], []
    for stem in tlg_files:
        cts = f"urn:cts:greekLit:{stem}"
        author_tlg, work_tlg = stem.split(".")            # tlg0001, tlg001
        slug = cts2slug.get(cts)
        title = ""
        if slug is None:
            # off-canon OCR editions: author is known, the edition lives in the locus
            # prefix (e.g. 'empedocles_diels_ppf_0005.1' -> 'empedocles_diels_ppf').
            aslug = authnum2slug.get(author_tlg)
            if not aslug:
                name = canon_auth.get(author_tlg.replace("tlg", ""), "")
                aslug = normalize_slug(name) if name else None
            first = open(REPO / f"data/corpus/{stem}.jsonl").readline()
            locus = json.loads(first).get("locus", "") if first else ""
            desc = re.sub(r"_\d{2,4}[.\d]*$", "", locus)          # edition descriptor
            title = desc
            wslug = normalize_slug(desc) if desc else work_tlg
            if aslug:
                # avoid redundant 'empedocles.empedocles-diels-ppf'
                if wslug.startswith(aslug + "-"):
                    wslug = wslug[len(aslug) + 1:]
                base = f"{aslug}.{wslug}" if wslug else f"{aslug}.{work_tlg}"
                cand, n = base, 2
                while cand in slug_taken and cand not in rename.values():
                    cand = f"{base}-{n}"; n += 1
                slug = cand; slug_taken.add(cand); minted.append((stem, slug, title))
            elif wslug:
                slug = normalize_slug(wslug); slug_taken.add(slug); minted.append((stem, slug, title))
            else:
                unresolved.append(stem); slug = stem   # keep tlg stem as last resort
        rename[stem] = slug
        crosswalk[slug] = {"cts": cts, "tlg": stem,
                           "author_slug": slug.split(".")[0] if "." in slug else "", "title": title}

    # slug-named corpus works not yet in the crosswalk: works ingested straight
    # to their slug key (the registry already knew their CTS alias, e.g. the
    # Galenus Verbatim editions) never pass through the tlg-stem path above, so
    # pull their TLG/CTS identity from the registry to keep the page complete.
    alias_added = []
    for stem in corpus:
        if stem in crosswalk or re.match(r"tlg\d+\.tlg[X0-9]+$", stem):
            continue
        w = reg["works"].get(stem) or {}
        w_cts = (w.get("aliases") or {}).get("cts") or ""
        if "greekLit:" not in w_cts:
            continue
        tail = w_cts.split("greekLit:")[-1]
        crosswalk[stem] = {"cts": w_cts, "tlg": tail,
                           "author_slug": stem.split(".")[0] if "." in stem else "",
                           "title": w.get("title", "")}
        alias_added.append(stem)

    # write crosswalk (the TLG-mapping "page")
    json.dump(crosswalk, open(REPO / "data/tlg_crosswalk.json", "w"), ensure_ascii=False, indent=0)
    with open(REPO / "data/tlg_crosswalk.tsv", "w") as f:
        f.write("slug\tcts_urn\ttlg\n")
        for slug, d in sorted(crosswalk.items()):
            # non-TLG identifier systems (e.g. PTA works) have no cts/tlg pair;
            # emit their primary id in the tlg column so the row survives
            other = next((f"{k}:{v}" for k, v in d.items()
                          if k not in ("cts", "tlg", "author_slug", "title")), "")
            f.write(f"{slug}\t{d.get('cts', '')}\t{d.get('tlg', other)}\n")
    if args.emit_rename_map:
        json.dump(rename, open(args.emit_rename_map, "w"), ensure_ascii=False)

    print(f"tlg corpus files: {len(tlg_files)}")
    print(f"  registry-matched: {len(tlg_files) - len(minted) - len(unresolved)}")
    print(f"  newly minted:     {len(minted)}")
    print(f"  UNRESOLVED (kept tlg stem): {len(unresolved)}  {unresolved[:8]}")
    print(f"slug-keyed works added from registry aliases: {len(alias_added)}  "
          f"{alias_added[:6]}")
    print(f"\ncrosswalk -> data/tlg_crosswalk.json + .tsv  ({len(crosswalk)} works)")
    print("sample minted (tlg -> slug | title):")
    for stem, slug, title in minted[:20]:
        print(f"    {stem} -> {slug}   [{title[:40]}]")


if __name__ == "__main__":
    main()
