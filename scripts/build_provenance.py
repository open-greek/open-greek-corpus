#!/usr/bin/env python3
"""Generate the OCR provenance table in the README: for each OCR'd work / volume,
its source, the model that OCR'd it, and whether it has been manually corrected yet.

Reads corpus_editions.json (which works are OCR), cgpg_works.json / ocr_works.json
(human descriptions), work_index.json (the served title, for the many OCR works whose
ledger description is blank or is a scan's running head), and
data/corrections_log/provenance.json (the list of works that have had a correction
pass, delivered by the OCR pipeline - a plain list of urns, nothing about how).
Rewrites the table between the OCR-PROVENANCE markers in README.md.

  python scripts/build_provenance.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
README = REPO / "README.md"
START = "<!-- OCR-PROVENANCE:START -->"
END = "<!-- OCR-PROVENANCE:END -->"

# The model that produced the recognition, per OCR source. The "ocr" default
# reflects the 2026-07 re-OCR campaign that re-read every served OCR page with
# Qwen3.6-27B (verified by per-family containment probes against the run dirs);
# editions read by something else carry a per-edition "model" override in
# data/inventory/ocr_edition_sources.json, which takes precedence below.
# The masked-column re-OCR fleet (geometric-column-mask pipeline, FP8 serving) is
# OGC's own OCR and folds into source "ocr"; a masked work is recognized by its
# edition slug (qwen36-*-masked / -singlecol) or its per-work data/ocr_provenance/
# record, which supplies the exact model, source scan, render DPI, and column
# geometry. MASKED_MODEL is the default label for a masked work lacking that record.
OCR_MODEL = {"cgpg": "calfa-co", "ocr": "Qwen3.6-27B"}
MASKED_MODEL = "Qwen3.6-27B-FP8"


def _load(name: str):
    fp = DATA / name
    return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else None


def _load_provenance() -> dict:
    """Per-work provenance for the masked-column re-OCR runs (model, source scan,
    render DPI, column geometry). Keyed by urn; one record per re-OCR'd work."""
    out: dict = {}
    pdir = DATA / "ocr_provenance"
    if pdir.is_dir():
        for fp in pdir.glob("*.json"):
            rec = json.loads(fp.read_text(encoding="utf-8"))
            out[rec.get("urn") or fp.stem] = rec
    return out


def masked_source(rec: dict) -> str | None:
    """Linked scan source for a masked re-OCR work, from its provenance record."""
    ss = rec.get("source_scan", {})
    pid = ss.get("public_id")
    if ss.get("source") == "archive.org" and pid:
        return f"[archive.org](https://archive.org/details/{pid})"
    return None


def masked_model(rec: dict) -> str:
    """OCR model label plus a masked-column-pipeline note (columns + render DPI)."""
    model = (rec.get("model") or "").split("/")[-1] or MASKED_MODEL
    cols = rec.get("layout_handling", {}).get("columns")
    dpi = rec.get("render_dpi")
    note = f"masked {cols}-col pipeline" if cols else "masked-column pipeline"
    if dpi:
        note += f", {dpi} dpi"
    return f"{model} ({note})"


def looks_like_page_header(desc: str) -> bool:
    """Whether a ledger description is a scan's running head rather than a title.

    ocr_works.json's `title` was harvested from the OCR of the first page for a
    whole family of fragment editions, so it holds whatever was printed across the
    top of that page: the play a fragment came from (`ΑΔΡΑΣΤΟΣ` for the whole of
    Achaeus' Fragmenta), a section rubric (`ΛΟΓΟΣ Αʹ`), sometimes half a column of
    running text. Printed running heads are set in capitals and our real titles are
    not, so "carries cased letters, none of them lowercase" separates the two
    cleanly - 486 of the table's 1,312 rows.

    Test for the ABSENCE of lowercase, not for all(isupper()): the Greek numeral
    sign in `ΛΟΓΟΣ Αʹ` (U+0374) is alpha but is neither upper nor lower, so
    all(isupper()) says False and 38 unmistakable running heads survive the filter.
    """
    return (bool(desc) and any(c.isalpha() for c in desc)
            and not any(c.islower() for c in desc))


def indexed_desc(urn: str, index: dict) -> str:
    """`Author - Title` from the work index, the fallback for a row whose ledger
    description is missing or is a running head. work_index.json is the reader-facing
    join and carries a real title for 940 of the 996 rows the ledgers cannot describe;
    the rest have no title there either (editors' paratexta, multi-author testimonia
    bundles, a few works the registry never titled) and are left blank rather than
    given an invented one.

    Two things in the index are not descriptions and must not be printed as if they
    were. 31 works are "titled" with the OCR delivery's file stem
    (`anthemius_dupuy_1777`), recognizable by the underscore no real title carries -
    printing it would just restate the Work column in worse spelling. And 36 authors
    have no display name, only their own slug (`boethus`), which the Work column
    already shows; prepending it earns nothing, so those rows get the bare title.
    """
    w = index.get(urn) or {}
    title = (w.get("title") or "").strip()
    if not title or "_" in title:
        return ""
    author = (w.get("author") or {})
    name = (author.get("name") or "").strip()
    return f"{name} - {title}" if name and name != (author.get("slug") or "") else title


def is_masked(edition: str, urn: str, prov_recs: dict) -> bool:
    """Whether a work's served (dominant) edition is a masked-column re-OCR run.
    Now that "ocr-masked" is folded into "ocr", the pipeline is recognized from the
    edition slug (qwen36-*-masked / *_masked, and the -singlecol masked variant,
    which matches its own per-work provenance record) rather than the source field.
    A work may ALSO carry a per-work provenance record for a NON-masked delivery
    (e.g. a full-page Migne PG redo whose Greek column is kept without a geometric
    crop): recognize the masked pipeline from the record's own geometric mask/crop
    method, not merely from a provenance record existing for the work."""
    ed = edition or ""
    if "-masked" in ed or "_masked" in ed or "-singlecol" in ed:
        return True
    rec = prov_recs.get(urn)
    if not rec or (rec.get("edition") or "") != ed:
        return False
    method = (rec.get("layout_handling", {}).get("method") or "").lower()
    return any(k in method for k in ("geometric", "mask", "crop"))


def main() -> None:
    ce = _load("corpus_editions.json") or {}
    # kind "secondary-witness" entries (a displaced CGPG copy of a slug whose
    # primary is another volume's carve) must not shadow the primary's desc
    cgpg = {w["urn"]: w for w in (_load("cgpg_works.json") or [])
            if w.get("kind") != "secondary-witness"}
    ocr = {w["urn"]: w for w in (_load("ocr_works.json") or [])}
    index = (_load("work_index.json") or {}).get("works") or {}
    srcs = _load("inventory/ocr_edition_sources.json") or {}
    # The Words column used to print ocr_works.json's / cgpg_works.json's own
    # n_tokens. Neither file is generated: both are ledgers that a dozen one-off
    # rescope/rekey/dissolve scripts edit in place, so their counts drift from
    # the text they describe - a sample of 200 found 30 off by more than half.
    # work_token_totals.json is derived from data/corpus by
    # build_work_lemma_counts.py, so prefer it and keep the ledger only as the
    # fallback for a work it has not reached.
    # Stale totals are worse than no totals: a file predating the CGPG carves
    # reports the whole Hesychius lexicon under the slug of its prefatory letter.
    # Fall back to the ledger rather than publish that.
    token_totals: dict[str, int] = {}
    totals_fp = DATA / "work_token_totals.json"
    corpus_mtime = max((fp.stat().st_mtime for fp in (DATA / "corpus").glob("*.jsonl")),
                       default=0)
    if totals_fp.exists() and totals_fp.stat().st_mtime >= corpus_mtime:
        token_totals = {urn: v.get("tokens") for urn, v in
                        (_load("work_token_totals.json") or {}).items()
                        if isinstance(v, dict)}
    elif totals_fp.exists():
        print("work_token_totals.json is older than data/corpus; falling back to "
              "the ledger counts. Run build_work_lemma_counts.py to refresh.",
              file=sys.stderr)
    prov_recs = _load_provenance()
    prov = _load("corrections_log/provenance.json") or {}
    corrected = set(prov.get("corrected_works", []))
    auto_corrected = set(prov.get("auto_corrected_works", []))
    # Authoritative edit status comes from the rows' own `corrections` stamps
    # (every edit method - confusion, dehyphenation, freq, ... - stamps the row),
    # so a work edited by a tool that bypassed the corrections-log overlay is
    # still marked. Manual methods (llm/agent) promote a work to "manual".
    MANUAL_TAGS = {"llm", "agent", "manual"}
    # "auto-corrected" claims a pass ran over the work, so it takes a minimum
    # share of rows actually stamped. The old test was a single stamped row,
    # which let a cross-work pass that touched six rows of a 2,950-row Eustathius
    # reclassify the whole thing and move the published raw-OCR share by a
    # million tokens. The bands are clear in the data: works a pass really
    # processed sit around 15% of rows stamped, works it merely grazed sit under
    # 1%.
    #
    # The threshold does NOT gate the manual promotion. "Manually corrected"
    # claims a person reviewed the text, which edit volume does not measure: a
    # clean work rightly comes back with few edits, and four walz_rhetores
    # volumes read near zero only because a per-treatise split re-keyed the rows
    # their corrections were stamped on.
    MIN_AUTO_COVERAGE = 0.01
    corpus_dir = DATA / "corpus"
    if corpus_dir.is_dir():
        for fp in corpus_dir.glob("*.jsonl"):
            tags: set = set()
            stamped = rows_seen = 0
            for line in fp.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rows_seen += 1
                if '"corrections"' in line:
                    row_tags = json.loads(line).get("corrections", [])
                    if row_tags:
                        stamped += 1
                        tags.update(row_tags)
            if not rows_seen:
                continue
            urn = fp.stem
            if tags & MANUAL_TAGS:
                corrected.add(urn)
                continue
            # The rows are authoritative in both directions for a work the corpus
            # actually serves, so a seed list claiming a correction the text
            # cannot show is treated as stale rather than believed.
            if stamped / rows_seen >= MIN_AUTO_COVERAGE:
                auto_corrected.add(urn)
            else:
                auto_corrected.discard(urn)
                corrected.discard(urn)

    def downloaded_from(urn: str, edition: str, src: str) -> str:
        # a linked source label; drop the domain parentheticals (roger-pearse.com,
        # archive.org) from the visible text but keep the link target
        url = (ocr.get(urn, {}).get("source_url")
               or (srcs.get(edition, {}) if isinstance(srcs.get(edition), dict) else {}).get("url"))
        label = (srcs.get(edition, {}).get("label") if isinstance(srcs.get(edition), dict) else None) \
            or edition
        if not label:
            return "-"
        label = re.sub(r",\s*[\w.-]+\.\w{2,}\)", ")", label)      # (elegiac+iambic, archive.org) -> (elegiac+iambic)
        label = re.sub(r"\s*\([\w.-]+\.\w{2,}\)", "", label).strip()   # (roger-pearse.com) -> ''
        return f"[{label}]({url})" if url else label

    rows = []
    for urn, m in sorted(ce.items()):
        src = m.get("source")
        if src not in OCR_MODEL:
            continue
        masked = is_masked(m.get("edition", ""), urn, prov_recs)
        if src == "ocr" and urn.startswith("ocr.") and not masked:
            continue          # ocr.* placeholder delivery pending per-work splitting
        if src == "cgpg":
            desc = cgpg.get(urn, {}).get("desc", "")
            name = urn.replace("cogPG.", "")
        else:
            w = ocr.get(urn, {})
            # " - ", the separator cgpg_works.json's descriptions already use, so one
            # column does not print two different dashes down its length.
            desc = " - ".join(p for p in (w.get("author", ""), w.get("title", "")) if p)
            name = urn
        # The ledgers describe barely a quarter of these rows: ocr_works.json has no
        # entry at all for 208 of them, a blank one for 301 more, and a harvested
        # running head for 486, which is how the Content column came to print
        # ΑΔΡΑΣΤΟΣ against the whole of Achaeus' Fragmenta. Fall back to the work
        # index, which titles all but 56 of the 996.
        # Only when the ledger has nothing usable: its descriptions are the richer
        # ones where they exist (they carry the Migne column range, the attribution
        # note, what a catena actually covers), so preferring the index wholesale
        # would flatten 316 good rows into a bare title.
        if not desc.strip() or looks_like_page_header(desc):
            desc = indexed_desc(urn, index) or desc
        status = ("manual" if urn in corrected
                  else "auto-corrected" if urn in auto_corrected
                  else "raw OCR")
        # Masked-column re-OCR works carry their own provenance record (model,
        # source scan, render DPI, column geometry); prefer it over the generic
        # per-source defaults so the table shows the FP8 masked-pipeline run. A masked
        # work lacking a provenance record still gets the FP8 masked-model label.
        rec = prov_recs.get(urn) if masked else None
        if rec:
            dl = masked_source(rec) or downloaded_from(urn, m.get("edition", ""), src)
            model = masked_model(rec)
        elif masked:
            dl = downloaded_from(urn, m.get("edition", ""), src)
            model = MASKED_MODEL
        else:
            dl = downloaded_from(urn, m.get("edition", ""), src)
            # A per-edition "model" in ocr_edition_sources.json overrides the source
            # default, so newer-model OCR (e.g. Qwen3.6-27B) isn't mislabeled with the
            # older campaign model.
            ed = srcs.get(m.get("edition", ""), {})
            model = (ed.get("model") if isinstance(ed, dict) else None) or OCR_MODEL[src]
        words = token_totals.get(urn, m.get("n_tokens", 0)) or 0
        rows.append((name, desc, dl, model, f"{words:,}", status))

    n_corr = sum(1 for r in rows if r[5] == "manual")
    n_auto = sum(1 for r in rows if r[5] == "auto-corrected")
    head = (f"{len(rows)} OCR'd works/volumes: {n_corr} manually corrected, "
            f"{n_auto} auto-corrected (deterministic glyph-confusion / frequency "
            f"passes; edited but not hand-reviewed), "
            f"{len(rows) - n_corr - n_auto} still raw OCR. Works are named by "
            f"their author.work slug; the TLG/CTS mapping is in `data/tlg_crosswalk.tsv`.\n\n")
    table = ["| Work (slug) | Content | Downloaded | OCR model | Words | Correction |",
             "|---|---|---|---|--:|---|"]
    for r in rows:
        table.append("| " + " | ".join(r) + " |")
    block = START + "\n" + head + "\n".join(table) + "\n" + END

    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("README is missing the OCR-PROVENANCE markers")
    out = text[:text.index(START)] + block + text[text.index(END) + len(END):]
    README.write_text(out, encoding="utf-8")
    print(f"provenance: {len(rows)} OCR works ({n_corr} manual, {n_auto} "
          f"auto-corrected) -> README")


if __name__ == "__main__":
    main()
