"""Resolve a TLG/CTS id to its corpus author.work slug.

The slug is the primary id for every corpus work; the TLG number is a crosswalk
only (see data/tlg_crosswalk.tsv). Ingesters that receive a source's TLG/CTS id
call slug_for() to learn the slug they must write, so a rebuild never reintroduces
tlg-named files. Join scripts that read the vendored tlg-keyed CSVs call it to
match the now-slug corpus keys.

Resolution order: the crosswalk (the 2.5k corpus works, incl. minted off-canon)
then the full registry (~7.4k works). An unresolved id returns unchanged and is
reported, so a genuinely new work surfaces instead of silently keying by tlg.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_MAP: dict[str, str] | None = None


def _load() -> dict[str, str]:
    global _MAP
    if _MAP is not None:
        return _MAP
    m: dict[str, str] = {}
    reg = REPO / "data" / "source_registry.json"
    if reg.exists():
        for slug, w in json.loads(reg.read_text(encoding="utf-8"))["works"].items():
            cts = (w.get("aliases") or {}).get("cts")
            if cts:
                m.setdefault(cts, slug)
    cw = REPO / "data" / "tlg_crosswalk.json"
    if cw.exists():
        for slug, d in json.loads(cw.read_text(encoding="utf-8")).items():
            if d.get("cts"):
                m[d["cts"]] = slug          # crosswalk wins (it reflects the delivered corpus)
            if d.get("pta"):                # PTA alias (see build_pta_crosswalk.py)
                m[f"urn:cts:pta:{d['pta']}"] = slug
    _MAP = m
    return m


def _to_cts(x: str) -> str:
    x = (x or "").strip()
    if x.startswith("urn:cts:"):
        return x
    if re.match(r"tlg\d+\.tlg[X0-9]+[a-z]?$", x):
        return f"urn:cts:greekLit:{x}"
    if re.match(r"pta\d+\.pta\d+$", x):
        return f"urn:cts:pta:{x}"
    return x


def slug_for(tlg_or_cts: str, default: str | None = None, warn: bool = True) -> str:
    """Slug for a TLG stem ('tlg0012.tlg001'), a CTS urn, or (already) a slug.
    Returns `default` (or the input unchanged) if unresolved."""
    m = _load()
    cts = _to_cts(tlg_or_cts)
    slug = m.get(cts)
    if slug:
        return slug
    if warn and cts.startswith("urn:cts:"):
        print(f"crosswalk: no slug for {tlg_or_cts} - keying by tlg (re-run build_id_crosswalk.py)",
              file=sys.stderr)
    return default if default is not None else tlg_or_cts
