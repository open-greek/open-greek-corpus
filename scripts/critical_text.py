"""Lossless critical-edition spans, conservative token offsets, and HTML export.

Offsets address Unicode code points in ``reading_text``, never HTML or a
normalized transcription. Morphology and lemmas are deliberately unattested.
"""
from __future__ import annotations

import html
import hashlib
import json
from pathlib import Path
import re
import unicodedata

SCHEMA = "epidoc-spans-v1"
EDITORIAL_TAGS = {"unclear", "supplied", "corr", "sic", "lem", "rdg", "del", "note"}


def load_critical_editions(data):
    """Reader-facing manifests are checked against the exact source and corpus."""
    data = Path(data)
    result = {}
    for path in sorted((data / "critical_editions").glob("*/manifest.json")):
        manifest = json.loads(path.read_text())
        if manifest.get("status") != "served-critical-edition" or manifest.get("critical_markup_schema") != SCHEMA:
            raise ValueError(f"Unsupported critical edition: {path.name}")
        for field, digest_field in (("source_path", "source_sha256"), ("corpus_path", "corpus_sha256")):
            relative = Path(manifest[field])
            if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "data":
                raise ValueError("Critical edition path must be repository-relative")
            if hashlib.sha256((data.parent / relative).read_bytes()).hexdigest() != manifest[digest_field]:
                raise ValueError("Critical edition source or corpus checksum changed")
        if manifest["work"] in result:
            raise ValueError("Duplicate critical edition work")
        result[manifest["work"]] = {**manifest, "manifest_path": path.relative_to(data.parent).as_posix()}
    return result


def register_critical_editions(registry, manifests):
    """Register the physical edition directly instead of guessing a Canon work."""
    for slug, manifest in manifests.items():
        author = registry.mint_author(manifest["author_name"], slug=manifest["author"])
        work = registry.mint_work(author, manifest["title"], slug=slug,
                                  aliases={"cts": f"urn:cts:cogGreek:{slug}"})
        registry.works[work].best_source = "open_corpus"
        registry.mint_edition(work, manifest["edition"], manifest["edition_name"],
                              provider=manifest["provider"], scheme=manifest["physical_citation_scheme"],
                              editor="; ".join(manifest["source_editors"]),
                              source=manifest["source_url"], license=manifest["source_license"],
                              servable=True, make_default=True,
                              aliases=manifest["edition_identifiers"])
        registry.add_tag(work, "language", manifest["language"])


def index_metadata(manifest):
    """Attach this block to a work_index work's ``critical_edition`` field."""
    fields = ("critical_markup_schema", "physical_citation_scheme", "manifest_path", "reader_path",
              "source_path", "source_url", "source_sha256", "source_license", "attribution",
              "source_editors", "counts", "token_policy")
    return {field: manifest[field] for field in fields}


def lexical_text(record):
    """Critical editions contribute only validated complete, certain tokens."""
    if "analysis_text" in record:
        if not isinstance(record["analysis_text"], str):
            raise ValueError("Lexical projection must be a string")
        return record["analysis_text"]
    if "critical_markup" in record:
        if record["critical_markup"].get("schema") != SCHEMA:
            raise ValueError("Unsupported critical-markup schema")
        raise ValueError("Critical text needs an explicit lexical projection")
    return record.get("text", "")


def _statuses(span):
    result = []
    for ancestor in span["ancestors"]:
        name, attributes = ancestor["tag"], ancestor["attributes"]
        if name == "unclear":
            result.append("unclear")
        elif name == "supplied":
            result.append("apograph" if attributes.get("evidence") == "apograph" else "supplied")
        elif name == "corr":
            result.append("corrected")
        elif name in ("lem", "rdg"):
            result.append("variant")
        elif name in ("del", "note"):
            result.append(name)
    return sorted(set(result))


def annotate(row):
    """Retain every branch and annotate selected surface fragments without guesses."""
    spans = row["spans"]
    chars, owners, statuses = [], [], []
    for index, span in enumerate(spans):
        span["id"] = f"{row['locus']}.s{index + 1}"
        if not span["selected"] or span["kind"] == "milestone":
            continue
        text = "…" if span["kind"] == "gap" else span["text"]
        state = _statuses(span)
        for char in text:
            # Collapse source indentation, keeping exact letters and diacritics.
            if char.isspace():
                char = " "
                if not chars or chars[-1] == " ":
                    continue
            chars.append(char)
            owners.append(span["id"])
            statuses.append(state)
    if chars and chars[-1] == " ":
        chars.pop(); owners.pop(); statuses.pop()
    reading = "".join(chars)
    tokens = []
    start = None
    for index in range(len(reading) + 1):
        char = reading[index] if index < len(reading) else " "
        is_letter = unicodedata.category(char)[0] in ("L", "M")
        is_elision = char in "’ʼ'" and start is not None
        if is_letter or is_elision:
            if start is None:
                start = index
            continue
        if start is None:
            continue
        state = sorted({s for group in statuses[start:index] for s in group})
        if (start and reading[start - 1] == "…") or (index < len(reading) and reading[index] == "…"):
            state.append("fragment")
        tokens.append({"id": f"{row['locus']}.t{len(tokens) + 1}",
                       "form": reading[start:index], "start": start, "end": index,
                       "span_ids": list(dict.fromkeys(owners[start:index])),
                       "status": sorted(state) or ["extant"], "lexical_eligible": not state,
                       "lemma": None, "analysis": None})
        start = None
    row["reading_text"] = reading
    row["tokens"] = tokens
    return row


def finalize_tokens(rows):
    """A break=no continuation is retained, never promoted as two complete words."""
    for index, row in enumerate(rows):
        row["word_continuations"] = {
            "from_previous_line": row["line_attributes"].get("break") == "no",
            "to_next_line": index + 1 < len(rows) and rows[index + 1]["line_attributes"].get("break") == "no"}
    for index, row in enumerate(rows):
        if row["line_attributes"].get("break") == "no":
            targets = [row["tokens"][:1]]
            if index:
                if rows[index - 1]["locus"].rsplit(".", 1)[0] != row["locus"].rsplit(".", 1)[0]:
                    raise ValueError("Word continuation crosses a column boundary")
                targets.append(rows[index - 1]["tokens"][-1:])
            for group in targets:
                for token in group:
                    token["status"] = sorted((set(token["status"]) - {"extant"}) | {"line_fragment"})
                    token["lexical_eligible"] = False
    for row in rows:
        row["analysis_text"] = " ".join(t["form"] for t in row["tokens"] if t["lexical_eligible"])
        validate(row)


def validate(row):
    """Check offsets, branch ownership, eligibility, and physical line identity."""
    if row.get("critical_markup", {}).get("schema", SCHEMA) != SCHEMA:
        raise ValueError("Unsupported critical-markup schema")
    expected_locus = ".".join([part["attributes"]["n"] for part in row["textparts"]] + [row["line_attributes"]["n"]])
    if row["locus"] != expected_locus:
        raise ValueError("Passage locus differs from physical column/line references")
    by_id = {s["id"]: s for s in row["spans"]}
    if len(by_id) != len(row["spans"]):
        raise ValueError("Duplicate span ID")
    if len({t["id"] for t in row["tokens"]}) != len(row["tokens"]):
        raise ValueError("Duplicate token ID")
    previous = 0
    for index, token in enumerate(row["tokens"]):
        a, b = token["start"], token["end"]
        if not (previous <= a < b <= len(row["reading_text"])) or row["reading_text"][a:b] != token["form"]:
            raise ValueError("Token offsets do not match the selected reading")
        if not token["span_ids"] or any(s not in by_id or not by_id[s]["selected"] or by_id[s]["kind"] != "text" for s in token["span_ids"]):
            raise ValueError("Token refers to a gap or an unselected reading")
        expected_status = {state for s in token["span_ids"] for state in _statuses(by_id[s])}
        reading = row["reading_text"]
        if (a and reading[a - 1] == "…") or (b < len(reading) and reading[b] == "…"):
            expected_status.add("fragment")
        continuation = row["word_continuations"]
        if ((index == 0 and continuation["from_previous_line"]) or
                (index == len(row["tokens"]) - 1 and continuation["to_next_line"])):
            expected_status.add("line_fragment")
        if token["status"] != (sorted(expected_status) or ["extant"]):
            raise ValueError("Token status differs from source markup or physical boundary")
        if token["lexical_eligible"] != (token["status"] == ["extant"]):
            raise ValueError("Uncertain or restored token entered lexical projection")
        if token["lemma"] is not None or token["analysis"] is not None:
            raise ValueError("This edition does not provide linguistic analyses")
        previous = b
    expected = " ".join(t["form"] for t in row["tokens"] if t["lexical_eligible"])
    if row["analysis_text"] != expected:
        raise ValueError("Lexical projection differs from validated tokens")
    return True


def _span_html(span):
    attrs = [a for a in span["ancestors"] if a["tag"] in EDITORIAL_TAGS]
    details = "; ".join(a["tag"] + ": " + json.dumps(a["attributes"], ensure_ascii=False) for a in attrs)
    if span["kind"] == "gap":
        detail = "gap: " + json.dumps(span.get("attributes", {}), ensure_ascii=False)
        text = "[…]" if span.get("attributes", {}).get("reason") == "lost" else "…"
        return f'<span class="gap" title="{html.escape(detail, quote=True)}">{text}</span>'
    if span["kind"] == "milestone":
        return '<span class="milestone" title="' + html.escape(json.dumps(span.get("attributes", {})), quote=True) + '">¶</span>'
    text = html.escape(span["text"])
    for annotation in reversed(attrs):
        name, a = annotation["tag"], annotation["attributes"]
        if name == "supplied":
            opening, closing = ("⸢", "⸣") if a.get("evidence") == "apograph" else (("&lt;", "&gt;") if a.get("reason") == "omitted" else ("[", "]"))
            text = opening + text + closing
    classes = " ".join(_statuses(span))
    return f'<span class="{classes}" title="{html.escape(details, quote=True)}">{text}</span>'


def render_html(rows, manifest):
    """Standalone reader: visible damage, alternate readings, and token inspection."""
    body = []
    for row in rows:
        validate(row)
        selected = "".join(_span_html(s) for s in row["spans"] if s["selected"])
        alternatives = [s for s in row["spans"] if not s["selected"] and s.get("text", "").strip()]
        refs = row["physical_refs"]
        textparts = " / ".join(f"{p['attributes'].get('subtype', 'part')} {p['attributes'].get('n', '')}" for p in refs["textparts"])
        continuation = " · continues preceding word" if refs["line_attributes"].get("break") == "no" else ""
        entries = "".join('<li>' + _span_html(s) + '</li>' for s in alternatives)
        detail = (f'<details><summary>Alternative readings ({len(alternatives)})</summary><ul>{entries}</ul></details>' if entries else "")
        physical = html.escape(json.dumps(refs, ensure_ascii=False, indent=2))
        tokens = html.escape(json.dumps(row["tokens"], ensure_ascii=False, indent=2))
        anchor = html.escape(row["locus"], quote=True)
        body.append(f'<article id="line-{anchor}"><a class="locus" href="#line-{anchor}">{html.escape(textparts)} · line {html.escape(refs["line_attributes"]["n"])}{continuation}</a><p class="reading" lang="grc">{selected}</p>{detail}<details><summary>Token annotations and physical references</summary><pre>{tokens}</pre><pre>{physical}</pre></details></article>')
    attribution = html.escape(manifest["attribution"])
    title = html.escape(manifest["title"])
    source_url = html.escape(manifest["source_url"], quote=True)
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{title}</title>
<style>body{{font:18px/1.6 Georgia,serif;max-width:64rem;margin:2rem auto;padding:0 1rem;color:#24231f;background:#fbf9f2}}h1{{font-size:1.6rem}}a{{color:#754421}}article{{border-top:1px solid #c9c2af;padding:1rem 0}}.locus,summary{{font-size:.85rem}}.reading{{font-size:1.4rem;white-space:pre-wrap;margin:.5rem 0}}.unclear{{text-decoration:underline dotted;text-underline-offset:.2em}}.supplied{{color:#71452e}}.apograph{{color:#286353}}.corrected,.variant{{border-bottom:1px solid #8a6030}}.gap{{color:#635c50;letter-spacing:.1em}}pre{{white-space:pre-wrap;font-size:.75rem;overflow-wrap:anywhere}}details{{margin:.4rem 0}}label{{margin-right:1.2rem}}.hide-uncertain .unclear{{color:#68645b}}.hide-restored .supplied,.hide-restored .apograph{{opacity:.4}}</style>
<h1>{title}</h1><p>P.Herc. 1026 · DCLP 63141 · {attribution} · <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>. <a href="{source_url}">Pinned source EpiDoc</a>.</p>
<p>Unclear letters have dotted underlining; [restored letters], &lt;omitted letters&gt;, ⸢letters surviving only in apographs⸣, and gaps retain their editorial status. Select any marked span for its source attributes. Alternatives and original corrections are available at each line. Tokens with damage or editorial intervention are excluded from the lexical projection; no lemma or morphology is inferred.</p>
<label><input type="checkbox" id="restorations" checked>Emphasize supplied text</label><label><input type="checkbox" id="uncertainty" checked>Emphasize unclear text</label>
{''.join(body)}<script>document.getElementById('restorations').addEventListener('change',e=>document.body.classList.toggle('hide-restored',!e.target.checked));document.getElementById('uncertainty').addEventListener('change',e=>document.body.classList.toggle('hide-uncertain',!e.target.checked));</script></html>'''
