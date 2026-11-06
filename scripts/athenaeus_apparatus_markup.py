"""Validate and display the printed Athenaeus apparatus without normalizing it."""
from __future__ import annotations

import html
import json
import re
import unicodedata

SCHEMA = "printed-apparatus-v1"


def words(text):
    """Return complete Unicode letter/mark runs and code point offsets."""
    start = None
    for index in range(len(text) + 1):
        letter = index < len(text) and unicodedata.category(text[index])[0] in {"L", "M"}
        if letter and start is None:
            start = index
        elif not letter and start is not None:
            yield start, index, text[start:index]
            start = None


def token_projection(text, readings, numerals=()):
    """Neither uncertain reading nor any fragment of it can enter lexical counts."""
    tokens, runs, run = [], [], []
    for start, end, form in words(text):
        owners = [r["id"] for r in readings if start < r["end"] and end > r["start"]]
        numeric = [r["id"] for r in numerals if start < r["end"] and end > r["start"]]
        eligible = not (owners or numeric)
        token = {"form": form, "start": start, "end": end,
            "status": ["apparatus-variant"] if owners else ["numeral"] if numeric else ["extant"],
            "reading_ids": owners, "lexical_eligible": eligible}
        if numeric:
            token["numeral_ids"] = numeric
        tokens.append(token)
        if eligible:
            run.append(form)
        elif run:
            runs.append(" ".join(run)); run = []
    if run:
        runs.append(" ".join(run))
    return tokens, " ".join(t["form"] for t in tokens if t["lexical_eligible"]), runs


def validate(row):
    """Check diplomatic roles, Unicode offsets, exclusions, and adjacency breaks."""
    markup = row.get("critical_markup", {})
    if markup.get("schema") != SCHEMA:
        raise ValueError("Unsupported printed-apparatus schema")
    if row.get("reading_text") != row.get("text"):
        raise ValueError("Apparatus reading text differs from its diplomatic display")
    readings = markup.get("readings", [])
    if len(readings) != 2 or len({r["id"] for r in readings}) != 2:
        raise ValueError("The apparatus must retain two distinct reading identities")
    previous = 0
    for reading in readings:
        a, b = reading["start"], reading["end"]
        if not previous <= a < b <= len(row["text"]) or row["text"][a:b] != reading["display"]:
            raise ValueError("Apparatus reading offsets do not match its display")
        if ("normalized_reading" not in reading or reading["normalized_reading"] is not None
                or reading["lexical_eligible"] is not False
                or reading["preferred"] is not False):
            raise ValueError("An apparatus variant was promoted to a normalized lexical reading")
        if reading["kind"] == "supralinear-letter":
            anchor = reading["raised_letter"]["anchor"]
            if (reading["baseline_text"] != "ἀρεμβολεῖται"
                    or reading["raised_letter"]["text"] != "θ"
                    or anchor != {"placement": "above", "base_codepoint_index": 1, "base_character": "ρ"}
                    or "linearized_boundary" not in reading["raised_letter"]
                    or reading["raised_letter"]["linearized_boundary"] is not None
                    or reading["display"] != "ἀρᶿεμβολεῖται" or reading["witness"] != "V"):
                raise ValueError("The raised theta lost its source position or gained an inferred insertion order")
        elif reading["kind"] == "adscript-iota":
            if (reading["display"] != "ὧι" or reading["witness"] != "P"
                    or reading["graphemes"] != [
                        {"letter": "ω", "breathing": "rough", "accent": "circumflex"},
                        {"letter": "ι", "placement": "adscript", "baseline": "same"}]):
                raise ValueError("The omega/iota variant lost its breathing or adscript typography")
        else:
            raise ValueError("Unsupported apparatus reading role")
        if not reading["source_regions"]:
            raise ValueError("An apparatus reading lacks its printed source regions")
        for region in reading["source_regions"]:
            if (region["source_id"] not in markup["sources"] or region["printed_page"] != 34
                    or region["apparatus_line"] != 6):
                raise ValueError("An apparatus source region lost its physical identity")
            source = markup["sources"][region["source_id"]]
            x0, y0, x1, y1 = region["box"]
            if not (0 <= x0 < x1 <= source["width"] and 0 <= y0 < y1 <= source["height"]
                    and re.fullmatch(r"[0-9a-f]{64}", source["sha256"])):
                raise ValueError("An apparatus crop is outside its pinned source")
        previous = b
    numerals = markup.get("numerals", [])
    if numerals:
        if len(numerals) != 1:
            raise ValueError("The bounded apparatus review has exactly one verified numeral")
        number = numerals[0]
        a, b = number["start"], number["end"]
        if (number["id"] in {r["id"] for r in readings}
                or number["kind"] != "greek-numeral" or number["display"] != "Γ\u0305"
                or number["base_letter"] != "Γ" or number["value"] != 3
                or number["overbar"] != {"mark": "\u0305", "codepoint": "U+0305", "placement": "above"}
                or not 0 <= a < b <= len(row["text"]) or row["text"][a:b] != number["display"]
                or any(a < r["end"] and b > r["start"] for r in readings)
                or number.get("lexical_eligible") is not False
                or number.get("printed_reading_verified") is not True
                or "normalized_reading" not in number or number["normalized_reading"] is not None
                or "expanded_word" not in number or number["expanded_word"] is not None):
            raise ValueError("The printed numeric Gamma lost its bar, value, or nonlexical role")
        regions = number["source_regions"]
        if {r["source_id"] for r in regions} != {"bsb", "toronto"} or len(regions) != 2:
            raise ValueError("The numeric Gamma needs both independently retained printed copies")
        for region in regions:
            source = markup["sources"][region["source_id"]]
            x0, y0, x1, y1 = region["box"]
            if (region["printed_page"] != 34 or region["apparatus_line"] != "4–5"
                    or region["column"] != "left"
                    or not 0 <= x0 < x1 <= source["width"]
                    or not 0 <= y0 < y1 <= source["height"]
                    or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"])):
                raise ValueError("The numeric Gamma source region changed")
    expected = token_projection(row["text"], readings, numerals)
    if (row.get("tokens"), row.get("analysis_text"), row.get("analysis_segments")) != expected:
        raise ValueError("Apparatus lexical eligibility or contiguous segments changed")
    if row.get("contextual_eligible") is not False:
        raise ValueError("An apparatus variant cannot supply unqualified positional context")
    return True


def render_html(row):
    """Render the raised letter above its printed anchor, without linearizing it."""
    validate(row)
    fragments, previous = [], 0
    numerals = row["critical_markup"].get("numerals", [])
    for reading in sorted([*row["critical_markup"]["readings"], *numerals], key=lambda item: item["start"]):
        fragments.append(html.escape(row["text"][previous:reading["start"]]))
        identity = html.escape(reading["id"], quote=True)
        if reading["kind"] == "supralinear-letter":
            content = 'ἀ<span class="anchor">ρ<span class="above" aria-label="theta printed above rho">θ</span></span>εμβολεῖται'
        elif reading["kind"] == "adscript-iota":
            content = '<span>ὧ</span><span class="adscript">ι</span>'
        else:
            content = html.escape(reading["display"])
        attribute = "data-numeral-id" if reading["kind"] == "greek-numeral" else "data-reading-id"
        style = "numeral" if reading["kind"] == "greek-numeral" else "variant"
        fragments.append(f'<span class="{style}" {attribute}="{identity}">{content}</span>')
        previous = reading["end"]
    fragments.append(html.escape(row["text"][previous:]))
    sources = "".join('<li><a href="' + html.escape(s["url"], quote=True) + '">'
        + html.escape(s["label"]) + '</a>, printed page 34</li>'
        for s in row["critical_markup"]["sources"].values())
    details = html.escape(json.dumps(row["critical_markup"], ensure_ascii=False, indent=2))
    result = ('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>Athenaeus, printed apparatus on page 34</title>
<style>body{font:19px/1.65 Palatino,"Palatino Linotype",serif;max-width:58rem;margin:2rem auto;padding:0 1rem;color:#25211c;background:#faf7ef}h1{font-size:1.5rem}a{color:#754421}.reading{font-size:1.3rem;line-height:2}.variant{border-bottom:1px solid #835d30}.anchor{position:relative;display:inline-block}.above{position:absolute;left:50%;bottom:65%;transform:translateX(-50%);font-size:.78em;line-height:1}.adscript{vertical-align:baseline}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:.8rem}</style>
<h1>Athenaeus, apparatus on printed page 34</h1>
<p>Carle Wescher, <i>Poliorcétique des Grecs</i>, Paris, 1867. The print is in the public domain.</p>
<p>Theta is printed above rho in the V reading. Its ordinary-letter insertion order remains unspecified. P prints omega with rough breathing and circumflex followed by an adscript iota. Both apparatus variants are excluded from lexical counts; no normalized reading is selected.</p>
<p class="reading" lang="grc">''' + "".join(fragments) + '''</p>
<h2>Printed sources</h2><ul>''' + sources + '''</ul>
<details><summary>Source roles and code point offsets</summary><pre>''' + details
        + '</pre></details></html>\n').encode()
    if numerals:
        note = '<p>The overbar above Γ marks a Greek numeral with value 3. Its literal display is retained without expansion into a word, and it is excluded from lexical counts.</p>\n'
        result = result.replace(b'<p class="reading"', note.encode() + b'<p class="reading"', 1)
    return result
