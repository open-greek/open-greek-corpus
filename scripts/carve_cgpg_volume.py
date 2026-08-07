#!/usr/bin/env python3
"""Carve a multi-work CGPG Migne volume dump (data/corpus/cogPG.<VOL>.jsonl)
into per-work corpus files, driven by the curated plan data/cgpg_carve_plan.json.

The plan is derived from the per-volume work-to-column research in
data/pd_research/cgpg_split_proposals.json (11 credited multi-work volumes,
consistency-reviewed) and data/pd_research/cgpg_zerocredit_identification.json
(7 zero-credit volumes). Each plan work names its target slug, its row ranges in
the volume's served loci, and one or more incipit anchors that must be found in
the named row before anything is written.

What a carve does (per volume):

  * every served row is assigned to exactly one bucket: a target work, the
    residual (rows that stay in the volume file: unassignable editorial matter,
    Latin dividers), or the duplicate-drop list (rescanned leaves, archived
    verbatim in the audit record);
  * a work's rows are moved verbatim - text byte-identical, extra row fields
    (corrections stamps etc.) preserved - re-keyed to the work slug with locus
    "<VOL>.<orig-locus>", so the Migne volume/page identity survives (the
    convention established by scripts/split_cedrenus_pg122.py);
  * rank "primary" works are written to data/corpus/<slug>.jsonl; works whose
    slug is already served from a better source per the precedence ladder
    (First1K TEI, byzantium.gr) carry rank "secondary" and are written to
    data/corpus_secondary/<slug>.jsonl with rank/secondary_reason on every row,
    never competing with the served primary;
  * "append": true adds this volume's rows to a per-work file an earlier volume
    created (the Theophylact John commentary spans PG123+PG124); idempotency is
    guarded by refusing a second append of the same "<VOL>." locus prefix;
  * TLG-bearing new primary works are registered in data/tlg_crosswalk.json
    (entry shape as build_dfhg_canon_pass.py) and the .tsv is regenerated;
  * data/cgpg_works.json gets one kind="work" entry per carved work and the
    volume entry is updated to the residual (works list cleared); run
    scripts/reconcile_cgpg_works.py afterwards to normalize serving status;
  * primary slugs inherit the volume's corrected_works flag in
    data/corrections_log/provenance.json (the correction pass was applied to
    the volume text these rows come from);
  * a reversible audit is written to data/corpus_changes/cogPG.<VOL>.per-work-
    split.json: old/new file hashes, the full locus map, the incipit-check
    results, and every dropped duplicate row archived verbatim.

Verification is hard-fail: exact row partition, incipit anchors (normalized
substring, with progressively shorter prefixes down to 20 normalized chars),
duplicate similarity (difflib, autojunk off, >= 0.60 against the kept row), and
exact Greek-token conservation (carved + residual + dropped == original).

The corrections-log mirror (data/corrections_log/applied.jsonl) keys cogPG.*
corrections by bare volume locus; per the rekey_corrections_log.py convention
those historical rows are left unchanged - the audit's locus map keeps the
linkage reconstructable.

Usage:
  carve_cgpg_volume.py --volume PG005            # check only, write nothing
  carve_cgpg_volume.py --volume PG005 --apply    # carve + write audit
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
PLAN_PATH = DATA / "cgpg_carve_plan.json"
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")
MIN_ANCHOR = 20          # shortest normalized incipit prefix accepted
DUP_MIN_SIM = 0.60       # dropped duplicate row vs kept row, difflib ratio


def greek_tokens(s: str) -> int:
    return sum(1 for t in s.split() if GREEK.search(t))


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def dump_rows(rows: list[dict]) -> bytes:
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows).encode("utf-8")


def read_rows(fp: Path) -> list[dict]:
    return [json.loads(l) for l in fp.read_text(encoding="utf-8").splitlines() if l.strip()]


def git_head_blob_sha256(rel: str) -> str | None:
    try:
        blob = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{rel}"],
                              check=True, capture_output=True).stdout
    except subprocess.CalledProcessError:
        return None
    return hashlib.sha256(blob).hexdigest()


def locus_major(locus: str) -> int:
    return int(str(locus).split(".")[0])


def locus_sort_key(locus: str):
    parts = str(locus).split(".")
    return tuple(int(p) if p.isdigit() else 0 for p in parts)


def normalize_anchor(s: str) -> str:
    """Fold an OCR string for anchor matching: strip diacritics, casefold,
    final sigma -> sigma, keep letters/digits only."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.casefold().replace("ς", "σ")
    return "".join(c for c in s if c.isalnum())


def find_anchor(incipit: str, text: str) -> tuple[int, int] | None:
    """Longest normalized slice of `incipit` found in `text`, allowing a small
    start offset for an OCR-garbled first word. Returns (offset, length) of the
    matched normalized slice, or None if no slice of MIN_ANCHOR chars matches."""
    n_inc = normalize_anchor(incipit)
    n_txt = normalize_anchor(text)
    if not n_inc:
        return None
    for off in (0, 3, 6, 10, 15, 20):
        rest = n_inc[off:]
        if len(rest) < MIN_ANCHOR:
            break
        for frac in (1.0, 0.8, 0.6, 0.4, 0.25):
            k = max(MIN_ANCHOR, int(len(rest) * frac))
            if k > len(rest):
                k = len(rest)
            if rest[:k] in n_txt:
                return (off, k)
    return None


def expand_ranges(ranges: list) -> set[int]:
    out: set[int] = set()
    for r in ranges:
        a, b = (r if isinstance(r, list) else (r, r))
        out.update(range(int(a), int(b) + 1))
    return out


def tlg_parts(tlg: str) -> tuple[str, str]:
    a, w = tlg.split(".")
    return a, w[3:] if w.startswith("tlg") else w


def rekey(row: dict, slug: str, vol: str, work: dict) -> dict:
    out = {"urn": slug, "edition": row["edition"],
           "locus": f"{vol}.{row['locus']}",
           "source": row["source"], "license": row["license"],
           "text": row["text"]}
    for k, v in row.items():        # preserve corrections stamps and the like
        if k not in out:
            out[k] = v
    if work.get("rank") == "secondary":
        out["rank"] = "secondary"
        out["secondary_reason"] = work["secondary_reason"]
    return out


class CarveError(SystemExit):
    pass


def fail(msg: str):
    raise CarveError(f"ERROR: {msg}")


def carve(vol_plan: dict, apply: bool) -> None:
    vol = vol_plan["volume"]
    src_urn = f"cogPG.{vol}"
    src_fp = DATA / "corpus" / f"{src_urn}.jsonl"
    audit_fp = DATA / "corpus_changes" / f"{src_urn}.per-work-split.json"

    if vol_plan.get("status") == "defer":
        print(f"{vol}: DEFERRED by plan ({vol_plan.get('defer_reason', 'see plan')}); nothing to do")
        return
    if audit_fp.exists():
        print(f"{vol}: audit record already present ({audit_fp.name}); already applied, no-op")
        return
    if not src_fp.exists():
        fail(f"{src_fp} missing and no audit record: unexpected state")

    old_bytes = src_fp.read_bytes()
    head = git_head_blob_sha256(f"data/corpus/{src_urn}.jsonl")
    if head is not None and head != sha256_bytes(old_bytes):
        fail(f"{src_urn}: working copy differs from git HEAD (uncommitted change?)")

    rows = read_rows(src_fp)
    by_locus: dict[str, dict] = {}
    for r in rows:
        l = str(r["locus"])
        if l in by_locus:
            fail(f"{src_urn}: duplicate locus {l}")
        by_locus[l] = r
    total_tok = sum(greek_tokens(r["text"]) for r in rows)

    # ---- buckets -------------------------------------------------------
    drops = vol_plan.get("drop_duplicates", [])
    drop_map: dict[str, str] = {}       # dropped locus -> kept original locus
    for d in drops:
        for a, b in zip(expand_sorted(d["loci"]), expand_sorted(d["duplicates_of"])):
            drop_map[str(a)] = str(b)
    for a, b in drop_map.items():
        if a not in by_locus:
            fail(f"drop list names absent locus {a}")
        if b not in by_locus:
            fail(f"drop {a}: claimed original {b} absent")
        if b in drop_map:
            fail(f"drop {a}: original {b} is itself dropped")
        sim = difflib.SequenceMatcher(None, by_locus[a]["text"], by_locus[b]["text"],
                                      autojunk=False).ratio()
        if sim < DUP_MIN_SIM:
            fail(f"drop {a}: similarity vs {b} is {sim:.3f} < {DUP_MIN_SIM} - not a duplicate?")

    residual_majors = expand_ranges(vol_plan.get("residual_ranges", []))
    residual_majors.update(int(x) for x in vol_plan.get("residual_loci", []))

    assigned: dict[str, str] = {}       # locus -> bucket name
    work_rows: dict[str, list[dict]] = {}
    for w in vol_plan["works"]:
        majors = expand_ranges(w["ranges"])
        picked = [l for l in by_locus
                  if locus_major(l) in majors and l not in drop_map
                  and locus_major(l) not in residual_majors]
        picked.sort(key=locus_sort_key)
        if w.get("row_order"):
            # explicit reading order (a scan pass bound a leaf out of numeric
            # order); must cover exactly the picked set
            ordered = [l for r in w["row_order"]
                       for l in sorted((x for x in picked
                                        if r[0] <= locus_major(x) <= r[1]),
                                       key=locus_sort_key)]
            if sorted(ordered) != sorted(picked) or len(ordered) != len(picked):
                fail(f"work {w['slug']}: row_order does not cover its rows exactly")
            picked = ordered
        if not picked:
            fail(f"work {w['slug']}: no rows in ranges {w['ranges']}")
        for l in picked:
            if l in assigned:
                fail(f"locus {l} claimed by both {assigned[l]} and {w['slug']}")
            assigned[l] = w["slug"]
        work_rows[w["slug"]] = [by_locus[l] for l in picked]

    residual = [by_locus[l] for l in by_locus
                if locus_major(l) in residual_majors and l not in drop_map]
    residual.sort(key=lambda r: locus_sort_key(str(r["locus"])))

    unassigned = [l for l in by_locus
                  if l not in assigned and l not in drop_map
                  and locus_major(l) not in residual_majors]
    if unassigned:
        fail(f"{len(unassigned)} served rows in no bucket: "
             f"{sorted(unassigned, key=locus_sort_key)[:20]}")

    # ---- incipit anchors ----------------------------------------------
    incipit_results: dict[str, list[dict]] = {}
    for w in vol_plan["works"]:
        res = []
        for chk in w["incipit_checks"]:
            l = str(chk["locus"])
            if l not in by_locus:
                fail(f"{w['slug']}: incipit anchor locus {l} not served")
            if assigned.get(l) != w["slug"]:
                fail(f"{w['slug']}: incipit anchor locus {l} assigned to "
                     f"{assigned.get(l)}")
            m = find_anchor(chk["text"], by_locus[l]["text"])
            if m is None:
                fail(f"{w['slug']}: incipit NOT FOUND in locus {l}: "
                     f"{chk['text'][:60]!r}")
            res.append({"locus": l, "incipit": chk["text"],
                        "matched_normalized_offset": m[0],
                        "matched_normalized_chars": m[1]})
        first = str(work_rows[w["slug"]][0]["locus"])
        if not any(str(c["locus"]) == first for c in w["incipit_checks"]):
            # allowed only when the plan documents why (e.g. a bare OCR'd Latin
            # title-page row precedes the text)
            if not w.get("notes"):
                fail(f"{w['slug']}: first carved row {first} has no incipit "
                     f"anchor and the plan carries no note explaining it")
        incipit_results[w["slug"]] = res

    # ---- token conservation -------------------------------------------
    carved_tok = sum(greek_tokens(r["text"]) for rs in work_rows.values() for r in rs)
    resid_tok = sum(greek_tokens(r["text"]) for r in residual)
    drop_tok = sum(greek_tokens(by_locus[l]["text"]) for l in drop_map)
    if carved_tok + resid_tok + drop_tok != total_tok:
        fail(f"token conservation FAILED: {carved_tok}+{resid_tok}+{drop_tok} "
             f"!= {total_tok}")

    # ---- output targets ------------------------------------------------
    writes: list[tuple[Path, bytes, str]] = []      # (path, bytes, mode-note)
    per_work_audit = []
    for w in vol_plan["works"]:
        slug = w["slug"]
        rs = work_rows[slug]
        out_rows = [rekey(r, slug, vol, w) for r in rs]
        secondary = w.get("rank") == "secondary"
        target = (DATA / ("corpus_secondary" if secondary else "corpus")
                  / f"{slug}.jsonl")
        if secondary and not (DATA / "corpus" / f"{slug}.jsonl").exists():
            fail(f"{slug}: rank=secondary but no served primary exists")
        if target.exists():
            if not w.get("append"):
                fail(f"{target} already exists (no append flag)")
            existing = read_rows(target)
            if any(str(r["locus"]).startswith(f"{vol}.") for r in existing):
                fail(f"{slug}: '{vol}.' loci already present (already applied?)")
            new_bytes = target.read_bytes() + dump_rows(out_rows)
            mode = "appended"
        else:
            if w.get("append"):
                fail(f"{slug}: append=true but {target} does not exist")
            new_bytes = dump_rows(out_rows)
            mode = "created"
        writes.append((target, new_bytes, mode))
        loci = [str(r["locus"]) for r in rs]
        per_work_audit.append({
            "slug": slug,
            "tlg": w.get("tlg"),
            "title": w["title"],
            "rank": w.get("rank", "primary"),
            **({"secondary_reason": w["secondary_reason"]} if secondary else {}),
            "file": str(target.relative_to(REPO)),
            "mode": mode,
            "rows": len(rs),
            "greek_tokens": sum(greek_tokens(r["text"]) for r in rs),
            "volume_loci": f"{loci[0]}-{loci[-1]}",
            "locus_map": f"{src_urn} locus N -> {slug} locus '{vol}.N'",
            "incipit_checks": incipit_results[slug],
            "evidence": w.get("evidence", ""),
            **({"notes": w["notes"]} if w.get("notes") else {}),
        })

    # ---- report --------------------------------------------------------
    print(f"{vol}: {len(rows)} rows / {total_tok} greek tokens ->")
    for wa in per_work_audit:
        tag = "SEC" if wa["rank"] == "secondary" else "   "
        print(f"  {tag} {wa['slug']:<70} {wa['rows']:>4} rows "
              f"{wa['greek_tokens']:>7} tok  loci {wa['volume_loci']} ({wa['mode']})")
    print(f"      residual: {len(residual)} rows / {resid_tok} tok; "
          f"dropped duplicates: {len(drop_map)} rows / {drop_tok} tok")

    if not apply:
        print("CHECK only (pass --apply to write)")
        return

    # ---- write corpus files -------------------------------------------
    for target, new_bytes, _ in writes:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(new_bytes)
    if residual:
        src_fp.write_bytes(dump_rows(residual))
    else:
        src_fp.unlink()

    # ---- tlg crosswalk for new tlg-bearing primary works ---------------
    cw_added = update_crosswalk(vol_plan)

    # ---- cgpg_works.json ----------------------------------------------
    update_cgpg_works(vol_plan, per_work_audit, residual, resid_tok)

    # ---- corrections provenance flag propagation ----------------------
    prov_added = propagate_corrected_flag(src_urn, vol_plan)

    # ---- audit ---------------------------------------------------------
    audit = {
        "_meta": {
            "change": f"split the {src_urn} whole-volume CGPG dump into per-work corpus files",
            "volume": vol,
            "source_urn": src_urn,
            "applied_by": "scripts/carve_cgpg_volume.py (plan: data/cgpg_carve_plan.json)",
            "date": vol_plan["date"],
            "plan_basis": vol_plan.get("basis", ""),
            "shared_row_rule": (
                "a served row holding a work boundary is assigned to exactly one "
                "work, normally the one whose incipit the row carries; the plan "
                "records the decision as the ranges themselves"),
            "reversible": (
                f"To revert: for every carved work file listed under 'works', drop "
                f"its rows whose locus starts '{vol}.' (delete the file when it was "
                f"'created'), strip the '{vol}.' prefix from their loci, re-insert "
                f"them and the archived 'dropped_duplicates' rows into "
                f"data/corpus/{src_urn}.jsonl together with the residual rows, "
                f"sorted by locus, and restore data/cgpg_works.json, "
                f"data/tlg_crosswalk.json/.tsv, and data/corrections_log/"
                f"provenance.json from the parent commit (or simply git revert the "
                f"commit; old sha256 below verifies). Every moved row's text is "
                f"byte-identical; only urn and locus changed."),
        },
        "old": {src_urn: {"rows": len(rows), "greek_tokens": total_tok,
                          "sha256": sha256_bytes(old_bytes)}},
        "works": per_work_audit,
        "residual": {
            "rows": len(residual), "greek_tokens": resid_tok,
            "loci": [str(r["locus"]) for r in residual],
            "note": vol_plan.get("residual_note", ""),
            **({"sha256": sha256_bytes(dump_rows(residual))} if residual else
               {"volume_file": "deleted (fully carved)"}),
        },
        "dropped_duplicates": {
            "note": vol_plan.get("duplicates_note", ""),
            "pairs": [{"dropped_locus": a, "duplicate_of_kept_locus": b,
                       "similarity": round(difflib.SequenceMatcher(
                           None, by_locus[a]["text"], by_locus[b]["text"],
                           autojunk=False).ratio(), 3)}
                      for a, b in sorted(drop_map.items(), key=lambda kv: locus_sort_key(kv[0]))],
            "rows_archived_verbatim": [by_locus[a] for a in
                                       sorted(drop_map, key=locus_sort_key)],
        },
        "token_conservation": {
            "original": total_tok, "carved": carved_tok,
            "residual": resid_tok, "dropped": drop_tok,
            "check": "carved + residual + dropped == original (exact)",
        },
        "crosswalk_entries_added": cw_added,
        "corrections_provenance_flag": prov_added,
        "corrections_mirror_note": (
            "data/corrections_log/applied.jsonl keys this volume's corrections by "
            "bare column locus under " + src_urn + "; per the "
            "rekey_corrections_log.py convention for cogPG.* bare-locus rows they "
            "are left unchanged (historical). The locus map above makes the "
            "linkage reconstructable."),
        "source": f"CGPG per-work carve of {vol}, plan data/cgpg_carve_plan.json",
    }
    audit_fp.parent.mkdir(parents=True, exist_ok=True)
    audit_fp.write_text(json.dumps(audit, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    print(f"APPLIED: wrote {len(writes)} work files, "
          f"{'rewrote residual' if residual else 'deleted'} {src_urn}, "
          f"audit {audit_fp.name}")


def expand_sorted(ranges: list) -> list[int]:
    return sorted(expand_ranges(ranges))


def update_crosswalk(vol_plan: dict) -> list[dict]:
    cw_path = DATA / "tlg_crosswalk.json"
    cw = json.loads(cw_path.read_text(encoding="utf-8"))
    added = []
    for w in vol_plan["works"]:
        tlg = w.get("tlg")
        if not tlg or w.get("rank") == "secondary":
            continue
        slug = w["slug"]
        cur = cw.get(slug)
        if cur:
            if cur.get("tlg") not in (None, tlg):
                fail(f"crosswalk: slug {slug} already maps to {cur['tlg']}")
            continue
        for other, oe in cw.items():
            if oe.get("tlg") == tlg:
                fail(f"crosswalk: {tlg} already claimed by {other}")
        cw[slug] = {"cts": f"urn:cts:greekLit:{tlg}", "tlg": tlg,
                    "author_slug": slug.split(".")[0], "title": w["title"]}
        added.append({"slug": slug, "tlg": tlg})
    if added:
        cw_path.write_text(json.dumps(cw, ensure_ascii=False, indent=0),
                           encoding="utf-8")
        with open(DATA / "tlg_crosswalk.tsv", "w", encoding="utf-8") as f:
            f.write("slug\tcts_urn\ttlg\n")
            for slug, d in sorted(cw.items()):
                other = next((f"{k}:{v}" for k, v in d.items()
                              if k not in ("cts", "tlg", "author_slug", "title")), "")
                f.write(f"{slug}\t{d.get('cts', '')}\t{d.get('tlg', other)}\n")
    return added


def update_cgpg_works(vol_plan: dict, per_work_audit: list[dict],
                      residual: list[dict], resid_tok: int) -> None:
    vol = vol_plan["volume"]
    src_urn = f"cogPG.{vol}"
    fp = DATA / "cgpg_works.json"
    vols = json.loads(fp.read_text(encoding="utf-8"))
    vol_idx = next((i for i, e in enumerate(vols)
                    if e.get("urn") == src_urn), None)
    if vol_idx is None:
        fail(f"cgpg_works.json: no entry for {src_urn}")
    vol_entry = vols[vol_idx]
    template = {k: vol_entry[k] for k in ("edition", "license", "source")}

    if residual:
        vol_entry["desc"] = (vol_entry["desc"].split(" (split per-work")[0]
                             + " (split per-work by scripts/carve_cgpg_volume.py; "
                               "residual rows only)")
        vol_entry["n_passages"] = len(residual)
        vol_entry["n_tokens"] = resid_tok
    else:
        vol_entry["desc"] = (vol_entry["desc"].split(" (split per-work")[0]
                             + " (fully split per-work by scripts/carve_cgpg_volume.py; "
                               "volume file removed)")
        vol_entry["n_passages"] = 0
        vol_entry["n_tokens"] = 0
    vol_entry["works"] = []

    plan_by_slug = {w["slug"]: w for w in vol_plan["works"]}
    new_entries = []
    for wa in per_work_audit:
        w = plan_by_slug[wa["slug"]]
        works_list = []
        if w.get("tlg"):
            a, wid = tlg_parts(w["tlg"])
            works_list.append({"tlg_id": a, "work_id": wid,
                               "title": w["title"],
                               "author": w.get("author_display", ""),
                               "cgpg_chosen": wa["rank"] == "primary"})
        # a secondary copy of a slug whose PRIMARY is another volume's cgpg
        # carve gets kind "secondary-witness": reconcile_cgpg_works.py (kind ==
        # "work" only) must not flip it to cgpg_chosen, and build_provenance
        # must not let it shadow the primary entry's desc
        kind = w.get("cgpg_works_kind", "work")
        new_entries.append({
            "volume": vol, "urn": wa["slug"], "kind": kind,
            "desc": f"{w.get('author_display', '')} - {w['title']} "
                    f"({vol} loci {wa['volume_loci']})".strip(" -"),
            **template,
            "n_passages": wa["rows"], "n_tokens": wa["greek_tokens"],
            "works": works_list,
            "cgpg_chosen": wa["rank"] == "primary" and kind == "work",
        })
    # drop any prior entries THIS volume contributed for these slugs
    # (idempotent re-add; another volume's entry for the same slug stays),
    # insert after the volume entry in plan order
    slugs = {e["urn"] for e in new_entries}
    vols = [e for e in vols
            if not (e.get("urn") in slugs and e.get("volume") == vol)]
    vol_idx = next(i for i, e in enumerate(vols) if e.get("urn") == src_urn)
    vols[vol_idx + 1:vol_idx + 1] = new_entries
    fp.write_text(json.dumps(vols, ensure_ascii=False, indent=1) + "\n",
                  encoding="utf-8")


def propagate_corrected_flag(src_urn: str, vol_plan: dict) -> list[str]:
    fp = DATA / "corrections_log" / "provenance.json"
    if not fp.exists():
        return []
    prov = json.loads(fp.read_text(encoding="utf-8"))
    corrected = prov.get("corrected_works", [])
    if src_urn not in corrected:
        return []
    added = []
    for w in vol_plan["works"]:
        if w.get("rank") == "secondary":
            continue        # the served primary is not this cgpg text
        if w["slug"] not in corrected:
            corrected.append(w["slug"])
            added.append(w["slug"])
    if added:
        prov["corrected_works"] = sorted(corrected)
        fp.write_text(json.dumps(prov, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")
    return added


def refresh_cgpg_works(vol_plan: dict) -> None:
    """Re-derive this volume's data/cgpg_works.json entries from its applied
    audit record (for repairing/regenerating the metadata without re-carving)."""
    vol = vol_plan["volume"]
    audit_fp = DATA / "corpus_changes" / f"cogPG.{vol}.per-work-split.json"
    if not audit_fp.exists():
        fail(f"{vol}: no audit record; carve not applied")
    audit = json.loads(audit_fp.read_text(encoding="utf-8"))
    update_cgpg_works(vol_plan, audit["works"], audit["residual"]["loci"],
                      audit["residual"]["greek_tokens"])
    print(f"{vol}: cgpg_works.json entries re-derived from {audit_fp.name}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", required=True, help="e.g. PG005")
    ap.add_argument("--plan", type=Path, default=PLAN_PATH)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--date", help="carve date for the audit record; overrides "
                                   "the plan entry's own `date`")
    ap.add_argument("--refresh-cgpg-works", action="store_true",
                    help="re-derive this volume's cgpg_works.json entries from "
                         "its applied audit record (no carving)")
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    vol_plan = next((v for v in plan["volumes"] if v["volume"] == args.volume), None)
    if vol_plan is None:
        fail(f"plan has no volume {args.volume}")
    # NOT plan["_meta"]["date"]. That is the date the plan file was authored, and
    # falling back to it stamps every later carve with it: PG113 and PG139 were
    # carved on 2026-08-07 and their audit records claimed 2026-07-31, a week
    # before the change they record (issue #29). The date is the one field in an
    # audit that nothing else in the file can be checked against, so it is
    # required rather than guessed.
    if args.date:
        vol_plan["date"] = args.date
    if not vol_plan.get("date"):
        fail(f"{args.volume} has no `date` in the plan; add the carve date to the "
             f"volume entry (or pass --date) rather than inheriting the plan's "
             f"authoring date")
    if args.refresh_cgpg_works:
        refresh_cgpg_works(vol_plan)
        return 0
    carve(vol_plan, args.apply)
    return 0


if __name__ == "__main__":
    sys.exit(main())
