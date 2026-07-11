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
OCR_MODEL = {"cgpg": "calfa-co", "ocr": "Qwen3.6-27B"}


def _load(name: str):
    fp = DATA / name
    return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else None


def main() -> None:
    ce = _load("corpus_editions.json") or {}
    cgpg = {w["urn"]: w for w in (_load("cgpg_works.json") or [])}
    ocr = {w["urn"]: w for w in (_load("ocr_works.json") or [])}
    srcs = _load("inventory/ocr_edition_sources.json") or {}
    prov = _load("corrections_log/provenance.json") or {}
    corrected = set(prov.get("corrected_works", []))
    auto_corrected = set(prov.get("auto_corrected_works", []))

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
        if src == "ocr" and urn.startswith("ocr."):
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
