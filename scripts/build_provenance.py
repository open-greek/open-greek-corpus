#!/usr/bin/env python3
"""Generate the OCR provenance table in the README: for each OCR'd work / volume,
its source, the model that OCR'd it, and whether it has been manually corrected yet.

Reads corpus_editions.json (which works are OCR), cgpg_works.json / ocr_works.json
(human descriptions), and data/corrections_log/provenance.json (the list of works that
have had a correction pass, delivered by the OCR pipeline - a plain list of urns,
nothing about how). Rewrites the table between the OCR-PROVENANCE markers in README.md.

  python scripts/build_provenance.py
"""

from __future__ import annotations

import json
import re
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


def is_masked(edition: str, urn: str, prov_recs: dict) -> bool:
    """Whether a work's served (dominant) edition is a masked-column re-OCR run.
    Now that "ocr-masked" is folded into "ocr", the pipeline is recognized from the
    edition slug (qwen36-*-masked / *_masked, and the -singlecol masked variant,
    which matches its own per-work provenance record) rather than the source field."""
    ed = edition or ""
    if "-masked" in ed or "_masked" in ed:
        return True
    rec = prov_recs.get(urn)
    return bool(rec and (rec.get("edition") or "") == ed)


def main() -> None:
    ce = _load("corpus_editions.json") or {}
    cgpg = {w["urn"]: w for w in (_load("cgpg_works.json") or [])}
    ocr = {w["urn"]: w for w in (_load("ocr_works.json") or [])}
    srcs = _load("inventory/ocr_edition_sources.json") or {}
    prov_recs = _load_provenance()
    prov = _load("corrections_log/provenance.json") or {}
    corrected = set(prov.get("corrected_works", []))
    auto_corrected = set(prov.get("auto_corrected_works", []))
    # Authoritative edit status comes from the rows' own `corrections` stamps
    # (every edit method - confusion, dehyphenation, freq, ... - stamps the row),
    # so a work edited by a tool that bypassed the corrections-log overlay is
    # still marked. Manual methods (llm/agent) promote a work to "manual".
    MANUAL_TAGS = {"llm", "agent", "manual"}
    corpus_dir = DATA / "corpus"
    if corpus_dir.is_dir():
        for fp in corpus_dir.glob("*.jsonl"):
            tags: set = set()
            for line in fp.read_text(encoding="utf-8").splitlines():
                if '"corrections"' in line:
                    tags.update(json.loads(line).get("corrections", []))
            if not tags:
                continue
            urn = fp.stem
            (corrected if tags & MANUAL_TAGS else auto_corrected).add(urn)

    def downloaded_from(urn: str, edition: str, src: str) -> str:
        # a linked source label; drop the domain parentheticals (roger-pearse.com,
        # archive.org) from the visible text but keep the link target
        url = (ocr.get(urn, {}).get("source_url")
               or (srcs.get(edition, {}) if isinstance(srcs.get(edition), dict) else {}).get("url"))
        label = (srcs.get(edition, {}).get("label") if isinstance(srcs.get(edition), dict) else None) \
            or edition
        if not label:
            return "—"
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
            desc = " — ".join(p for p in (w.get("author", ""), w.get("title", "")) if p)
            name = urn
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
        rows.append((name, desc, dl, model, f"{m.get('n_tokens', 0):,}", status))

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
