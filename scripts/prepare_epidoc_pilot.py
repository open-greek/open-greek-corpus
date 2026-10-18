#!/usr/bin/env python3
"""Prepare a reversible, unserved EpiDoc pilot with line loci and all readings.

The source XML is copied byte-for-byte. Every line retains structured spans,
including branches not selected by the edition's explicit lem/corr reading.
This command never writes data/corpus or assigns a production work identity.
"""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

TEI = "http://www.tei-c.org/ns/1.0"
NS = {"t": TEI}


def tag(node):
    return node.tag.rsplit("}", 1)[-1]


def element(node):
    return {"tag": tag(node), "attributes": dict(node.attrib)}


def display(spans):
    output = []
    previous = []
    for span in spans:
        if not span["selected"]:
            continue
        annotations = [a for a in span["ancestors"] if a["tag"] in ("supplied", "del")]
        common = 0
        while common < min(len(previous), len(annotations)) and previous[common] == annotations[common]:
            common += 1
        for a in reversed(previous[common:]):
            output.append(">" if a["tag"] == "supplied" and a["attributes"].get("reason") == "omitted" else "]")
        for a in annotations[common:]:
            output.append("<" if a["tag"] == "supplied" and a["attributes"].get("reason") == "omitted" else "[")
        previous = annotations
        text = span.get("text", "")
        if span.get("kind") == "gap":
            text = "…"
        if any(a["tag"] == "unclear" for a in span["ancestors"]):
            text = "".join(c + "\u0323" if c.isalpha() else c for c in text)
        output.append(text)
    for a in reversed(previous):
        output.append(">" if a["tag"] == "supplied" and a["attributes"].get("reason") == "omitted" else "]")
    return re.sub(r"\s+", " ", "".join(output)).strip()


def prepare(source, out, *, source_url, revision):
    raw = source.read_bytes()
    root = ET.fromstring(raw)
    edition = root.find(".//t:div[@type='edition']", NS)
    if edition is None:
        raise ValueError("No edition div")
    license_urls = [e.get("target") for e in root.findall(".//t:availability//t:ref[@type='license']", NS)]
    if not any(u and re.search(r"creativecommons.org/licenses/by/3[.]0/?$", u) for u in license_urls):
        raise ValueError("Pilot currently accepts only the verified CC BY 3.0 source license")
    rows = []
    current = None
    seen = set()
    def flush():
        nonlocal current
        if current is not None:
            current["text"] = display(current["spans"])
            if current["locus"] in seen:
                raise ValueError(f"Duplicate line locus: {current['locus']}")
            seen.add(current["locus"])
            rows.append(current)
            current = None
    def add(text, ancestors, selected, kind="text", attributes=None):
        if current is not None and (text or kind != "text"):
            current["spans"].append({"kind": kind, "text": text,
                "ancestors": copy.deepcopy(ancestors), "selected": selected,
                **({"attributes": attributes} if attributes else {})})
    def walk(node, prefix=(), ancestors=(), selected=True):
        nonlocal current
        name = tag(node)
        if name == "div" and node.get("type") == "textpart":
            if not node.get("n"):
                raise ValueError("Unnumbered textpart cannot form a stable locus")
            prefix += (node.get("n"),)
        if name == "head":
            return
        if name == "lb":
            if not selected:
                raise ValueError("Line break inside an alternative reading requires explicit alignment")
            flush()
            if not node.get("n"):
                raise ValueError("Unnumbered line break")
            current = {"locus": ".".join((*prefix, node.get("n"))),
                       "line_attributes": dict(node.attrib), "spans": []}
            return
        path = (*ancestors, element(node))
        if name == "gap":
            add("", path, selected, "gap", dict(node.attrib))
            return
        choice = None
        if name in ("choice", "app"):
            preferred = ("lem",) if name == "app" else ("corr", "reg", "expan")
            for preferred_tag in preferred:
                matches = [child for child in node if tag(child) == preferred_tag]
                if matches:
                    if len(matches) != 1:
                        raise ValueError("Edition does not identify a unique preferred reading")
                    choice = matches[0]
                    break
            if choice is None:
                raise ValueError("Unresolved variant: retain it for editorial review")
        add(node.text or "", path, selected)
        for child in node:
            walk(child, prefix, path, selected and (choice is None or child is choice))
            add(child.tail or "", path, selected)
        if name == "ab":
            flush()
    walk(edition)
    flush()
    expected = len(edition.findall(".//t:lb", NS))
    if len(rows) != expected:
        raise ValueError(f"Lost line boundaries: {len(rows)} != {expected}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "source.xml").write_bytes(raw)
    with (out / "passages.jsonl").open("w") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    manifest = {"schema_version": 1, "status": "unserved-editorial-pilot",
                "source_url": source_url, "revision": revision,
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "source_license": "CC-BY-3.0", "source_license_urls": license_urls,
                "attribution": "Digital Corpus of Literary Papyri and LDAB (Trismegistos)",
                "title": root.findtext(".//t:titleStmt/t:title", namespaces=NS),
                "lines": len(rows), "markup_counts": dict(Counter(tag(e) for e in edition.iter())),
                "policy": "Explicit edition lem/corr readings drive display; all alternative spans and the unchanged source XML are retained. Unclear letters carry underdots; supplied text is bracketed; gaps stay explicit. Line break=no remains metadata. No normalization or text correction is applied to the source.",
                "generated_by": "scripts/prepare_epidoc_pilot.py"}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.out, source_url=args.source_url,
                             revision=args.revision), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
