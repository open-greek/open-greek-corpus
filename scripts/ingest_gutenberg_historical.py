#!/usr/bin/env python3
"""Pin, compare, and admit historical Greek found in the Gutenberg catalog.

These three catalog discoveries are not rows of the 214-document GlossAPI
artifact. Scope decisions, source snapshots, whole-corpus duplicate evidence,
critical notation, and reversible output hashes remain OGC-owned.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup
from audit_glossapi_gutenberg import book_metadata, quality, sha, source_body
from critical_text import SCHEMA, annotate, finalize_tokens, render_html, validate
from stage_glossapi_ekklisiastika import greek_tokens, _fold_token
from build_source_components import corpus_hash

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
DEPENDENCY_SHA256 = {name: hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
                    for name in ("audit_glossapi_gutenberg.py", "critical_text.py", "stage_glossapi_ekklisiastika.py")}
PIN = ROOT / "data/gutenberg_historical_sources.json"
DEDUP = ROOT / "data/gutenberg_historical_dedup.json"
AUDIT = "data/corpus_changes/gutenberg-historical/changes.json"
CANDIDATES = {
    32549: {"title": "Expositio fidei", "disposition": "approved_subject_to_gates",
            "work": "marcellus-theology.expositio-fidei", "author": "marcellus-theology", "author_name": "Marcellus",
            "cts": "urn:cts:greekLit:tlg2041.tlg004", "edition": "gutenberg-32549-2010",
            "edition_name": "Project Gutenberg 32549 (2010), Greek text; attribution disputed",
            "citation_scheme": "section", "source_editors": ["Michael Gray (digital transcription)"],
            "attribution_status": "disputed",
            "attribution_readings": [
                {"author": "Athanasius", "status": "traditional_source_attribution", "evidence": "Gutenberg 32549 catalog and Greek heading"},
                {"author": "Marcellus of Ancyra", "status": "catalog_attribution_not_adjudicated", "evidence": "CPG 2804, Pinakes and BiblIndex; OGC's existing tlg2041.tlg004 entry"}],
            "identity_evidence": ["https://pinakes.irht.cnrs.fr/notices/oeuvre/id/6423", "https://dapytains.biblindex.org/en/work-edition/7967"],
            "edition_qualification": "The Greek work is CPG 2804. OGC's existing Marcellian work key is retained while both its catalog attribution and Gutenberg's traditional Athanasian attribution remain explicit and disputed. The text source is Gutenberg's 2010 digital edition; the Nordberg 1962 bibliographic record identifies the work, not the transcribed edition."},
    37641: {"title": "In illud: Omnia mihi tradita sunt", "disposition": "approved_subject_to_gates",
            "work": "athanasius-theology.in-illud-omnia-mihi-tradita-sunt",
            "author": "athanasius-theology", "author_name": "Athanasius",
            "cts": "urn:cts:greekLit:tlg2035.tlg039", "edition": "gutenberg-37641-2011",
            "edition_name": "Project Gutenberg 37641 (2011), Greek text",
            "citation_scheme": "section", "source_editors": ["Michael Gray (digital transcription)"],
            "edition_qualification": "The citable edition is the pinned Gutenberg digital transcription, with six native numbered Greek sections. The underlying printed exemplar is not identified by Gutenberg; no claim to a particular Migne impression, page, or column is made."},
    66595: {"title": "Res gestae divi Augusti (Greek version)", "disposition": "approved_subject_to_gates",
            "work": "augustus.res-gestae-divi-augusti", "author": "augustus", "author_name": "Augustus",
            "edition": "gutenberg-fairley-1898-grc", "edition_name": "William Fairley, Monumentum Ancyranum (Philadelphia, 1898), Greek inscription",
            "citation_scheme": "column.line", "source_editors": ["William Fairley"],
            "edition_qualification": "Fairley's title page explicitly identifies the 1898 Philadelphia edition. Only the ancient Greek inscription under H2GREEK is admitted; Latin, modern English, commentary, and apparatus are retained outside lexical text. Augustus is the author of the underlying statement; the ancient Greek translator is unnamed."},
}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def pin_sources():
    if PIN.exists():
        raise ValueError("Refusing to overwrite existing source pins")
    sources = []
    cache = ROOT / "data/cache/glossapi/gutenberg"
    for ident, policy in CANDIDATES.items():
        url = f"https://www.gutenberg.org/ebooks/{ident}"
        catalog = (cache / f"{ident}.catalog.html").read_bytes()
        metadata, text_url = book_metadata(catalog, url)
        raw = (cache / f"{ident}.text.html").read_bytes()
        if metadata.get("Copyright") != ["Public domain in the USA."]:
            raise ValueError("No verified public-domain source declaration")
        source_path = f"data/reference/gutenberg/{ident}/source.html"
        catalog_path = f"data/reference/gutenberg/{ident}/catalog.html"
        for relative, data in ((source_path, raw), (catalog_path, catalog)):
            dest = ROOT / relative
            if dest.exists() and dest.read_bytes() != data:
                raise ValueError("Refusing to replace a retained source snapshot")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        sources.append({**policy, "ebook_id": ident, "url": url, "source_url": text_url,
                        "source_path": source_path, "source_sha256": sha(raw),
                        "catalog_path": catalog_path, "catalog_sha256": sha(catalog),
                        "metadata": metadata, "language": "grc",
                        "license": "PD (ancient Greek text; public-domain Gutenberg edition)",
                        "license_url": "https://www.gutenberg.org/policy/license.html"})
    PIN.write_bytes(encoded({"schema_version": 1, "reviewed_on": "2026-10-20",
                            "discovery": "Official Greek catalog, outside the GlossAPI 214-row artifact",
                            "sources": sources}))


def load_sources():
    doc = json.loads(PIN.read_bytes())
    for source in doc["sources"]:
        for key in ("source", "catalog"):
            if sha((ROOT / source[f"{key}_path"]).read_bytes()) != source[f"{key}_sha256"]:
                raise ValueError("Historical Gutenberg source snapshot changed")
        if {k: source[k] for k in CANDIDATES[source["ebook_id"]]} != CANDIDATES[source["ebook_id"]]:
            raise ValueError("Source scope differs from the reviewed generator policy")
    return doc


def refresh_review():
    """Update reviewed routing while refusing any change to pinned source bytes."""
    doc = json.loads(PIN.read_bytes())
    for source in doc["sources"]:
        for key in ("source", "catalog"):
            if sha((ROOT/source[f"{key}_path"]).read_bytes()) != source[f"{key}_sha256"]:
                raise ValueError("Cannot revise routing for changed source bytes")
        source.pop("reason", None)
        source.update(CANDIDATES[source["ebook_id"]])
    PIN.write_bytes(encoded(doc))


def numbered_greek(raw: bytes, ident: int) -> tuple[list[dict], list[dict]]:
    soup = BeautifulSoup(raw, "html.parser")
    rows, notes = [], []
    active = False
    for p in soup.find_all("p"):
        value = p.get_text(" ", strip=True)
        if re.match(r"1\.\s+(?:Καὶ|Πιστεύομεν)", value):
            active = True
        elif active and re.match(r"1\.\s+[A-Za-z]", value):
            active = False
        if active and re.match(r"\d+\.\s+", value):
            clone = BeautifulSoup(str(p), "html.parser")
            refs = []
            for a in clone.find_all("a"):
                label = a.get_text(" ", strip=True)
                if re.fullmatch(r"[\[(]\d+[\])]", label):
                    refs.append(label)
                    a.decompose()
                else:
                    a.unwrap()
            value = clone.get_text("", strip=False).strip()
            match = re.match(r"(\d+)\.\s+(.+)", value, re.S)
            rows.append({"locus": match[1], "text": " ".join(match[2].split()),
                         "source_note_references": refs})
        if re.match(r"[\[(]\d+[\])]", value):
            notes.append({"locus": f"note.{len(notes)+1}", "text": value})
    expected = 6 if ident == 37641 else 4
    if [r["locus"] for r in rows] != [str(i) for i in range(1, expected + 1)]:
        raise ValueError("Greek sections are missing, reordered, or duplicated")
    return rows, notes


def inscription(raw: bytes) -> tuple[list[dict], list[dict]]:
    soup = BeautifulSoup(raw, "html.parser")
    start = soup.find(id="H2GREEK")
    if not start or not soup.find(id="H2ENGLISH"):
        raise ValueError("Greek inscription boundaries are missing")
    rows, notes, column, chapter, depth, previous_hyphen = [], [], "", None, 0, False
    for element in start.parent.next_siblings:
        if not getattr(element, "name", None):
            continue
        if element.find(id="H2ENGLISH"):
            break
        ps = [element] if element.name == "p" else element.find_all("p")
        for p in ps:
            text = p.get_text("", strip=False).strip()
            if re.fullmatch(r"[IVXLCDM]+\.", text):
                column = text[:-1]
            chapter_match = re.fullmatch(r"c\.\s*(\d+)\.", text)
            if chapter_match:
                chapter = int(chapter_match[1])
            if "inscrip" not in p.get("class", []):
                if "bqp9em" in p.get("class", []):
                    notes.append({"locus": f"apparatus.{len(notes)+1}", "text": " ".join(text.split())})
                continue
            match = re.match(r"(\d+)\s+(.+)", text, re.S)
            if not match or not column:
                raise ValueError("Inscription line lacks a native column/line reference")
            number, text = match[1], " ".join(match[2].split())
            spans, chunk = [], []
            def flush():
                if chunk:
                    ancestors = [{"tag": "supplied", "attributes": {"reason": "lost"}}] if depth else []
                    for part in re.split(r"((?:\.\s*){2,})", "".join(chunk)):
                        if not part:
                            continue
                        if re.fullmatch(r"(?:\.\s*){2,}", part):
                            spans.append({"kind": "gap", "text": "", "selected": True,
                                          "attributes": {"reason": "lost"}, "ancestors": ancestors})
                        else:
                            spans.append({"kind": "text", "text": part, "selected": True,
                                          "ancestors": ancestors})
                    chunk.clear()
            for char in text:
                if char in "[]":
                    flush()
                    depth += 1 if char == "[" else -1
                    if depth not in (0, 1):
                        raise ValueError("Ambiguous nested or unmatched restoration brackets")
                else:
                    chunk.append(char)
            flush()
            parts = [{"tag": "div", "attributes": {"type": "textpart", "subtype": "column", "n": column}}]
            line = {"n": number, **({"break": "no"} if previous_hyphen else {})}
            row = {"locus": f"{column}.{number}", "text": text, "spans": spans,
                   "textparts": parts, "line_attributes": line,
                   "physical_refs": {"textparts": parts, "line_attributes": line},
                   "chapter": chapter, "critical_markup": {"schema": SCHEMA},
                   "gap_boundary_policy": "conservative-across-whitespace",
                   "source_note": "Square brackets are editorial restorations, not attested letters. Spaced dots mark lacunae; neighboring tokens have uncertain word boundaries and remain uncounted."}
            previous_hyphen = text.endswith("-")
            rows.append(annotate(row))
    if depth or len(rows) != 436 or len({r["locus"] for r in rows}) != 436:
        raise ValueError("Inscription brackets or native physical references are incomplete")
    # Three source-printed hyphens continue across column boundaries. Keep
    # those fragments visible and uncounted; never synthesize a complete word.
    finalize_tokens(rows, allow_cross_column_continuations=True)
    for row in rows:
        validate(row)
    return rows, notes


def candidates():
    doc = load_sources()
    result = []
    for source in doc["sources"]:
        raw = (ROOT / source["source_path"]).read_bytes()
        rows, notes = inscription(raw) if source["ebook_id"] == 66595 else numbered_greek(raw, source["ebook_id"])
        for row in rows:
            row.update({"urn": source.get("work", f"quarantine.gutenberg-{source['ebook_id']}"),
                        "edition": source.get("edition"), "source": "gutenberg", "license": source["license"],
                        "language": "grc", "provenance": {
                            "url": source["source_url"], "ebook_id": source["ebook_id"],
                            "source_sha256": source["source_sha256"], "source_path": source["source_path"],
                            "edition_qualification": source.get("edition_qualification", source.get("reason")),
                            **({"attribution_status": source["attribution_status"],
                                "attribution_readings": source["attribution_readings"],
                                "identity_evidence": source["identity_evidence"]} if source.get("attribution_readings") else {})}})
        result.append((source, rows, notes))
    return result


def upstream_corrections(source):
    """Retain the publisher's reported variants without applying new edits."""
    soup = BeautifulSoup((ROOT / source["source_path"]).read_bytes(), "html.parser")
    text = soup.get_text(" ", strip=True)
    start = text.find("Typographical errors in the Greek (All corrected).")
    if start < 0:
        return []
    end = text.find("Typographical errors in the Latin", start)
    section = text[start:end if end >= 0 else None]
    return [{"original": before, "corrected": after, "printed_page": page,
             "source_url": source["source_url"], "source_sha256": source["source_sha256"],
             "recorded_on": "2026-10-20", "scope": "Gutenberg transcriber's report; no correction applied by OGC"}
            for page,before,after in re.findall(r"Page\s+(\d+)\s+(\S+)\s+changed to read\s+(\S+)", section)]


def baseline_files():
    outputs = {s["work"] + ".jsonl" for s in CANDIDATES.values() if s.get("work")}
    return [p for p in sorted((ROOT / "data/corpus").glob("*.jsonl")) if p.name not in outputs]


def dedup_queries(groups):
    queries = {}
    for source, rows, _ in groups:
        # The physical inscription is compared in whole-column units, retaining
        # boundaries separately in the eventual corpus and reader.
        units = defaultdict(list)
        for row in rows:
            key = row["locus"].split(".")[0] if source["ebook_id"] == 66595 else row["locus"]
            units[key].append(row.get("reading_text", row["text"]))
        for unit, parts in units.items():
            key = f"{source['ebook_id']}:{unit}"
            ts = [_fold_token(t) for t in greek_tokens(" ".join(parts))]
            queries[key] = ts
    return queries


def scan_corpus(groups):
    queries, windows = dedup_queries(groups), defaultdict(list)
    for key, ts in queries.items():
        for index in range(len(ts) - 7):
            windows[tuple(ts[index:index+8])].append((key, index))
    coverage, witnesses, pins = {}, defaultdict(dict), {}
    paths = baseline_files()
    for index, path in enumerate(paths, 1):
        raw = path.read_bytes()
        pins[path.name] = sha(raw)
        for line in raw.splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            ts = [_fold_token(t) for t in greek_tokens(row.get("text", ""))]
            hit_queries = set()
            for position in range(len(ts) - 7):
                for key, offset in windows.get(tuple(ts[position:position+8]), ()):
                    pair = key, path.stem
                    if pair not in coverage:
                        coverage[pair] = bytearray(len(queries[key]))
                    coverage[pair][offset:offset+8] = b"\x01" * 8
                    hit_queries.add(key)
            for key in hit_queries:
                evidence = witnesses[key].setdefault(path.stem, [])
                if len(evidence) < 12:
                    evidence.append({k: row.get(k) for k in ("urn", "locus", "edition", "source")})
        if index % 500 == 0:
            print(f"Compared {index}/{len(paths)} corpus files", flush=True)
    matches = {}
    for (key, work), covered in coverage.items():
        count = sum(covered)
        if count >= 24:
            matches.setdefault(key, []).append({"work": work, "covered_tokens": count,
                "candidate_tokens": len(queries[key]), "coverage": count / len(queries[key]),
                "passages": witnesses[key][work]})
    report = {"schema_version": 1, "source_manifest_sha256": sha(PIN.read_bytes()),
              "method": "Exact accent-folded eight-word contexts at every source and corpus token position; overlap is evidence, never automatic deletion of a cross-work quotation.",
              "file_sha256": pins, "corpus_sha256": corpus_hash(pins),
              "files": len(pins), "excluded_admission_outputs": sorted({s["work"] for s in CANDIDATES.values() if s.get("work")}),
              "candidate_token_counts": {key: len(value) for key, value in queries.items()},
              "candidate_sha256": {key: sha(" ".join(value).encode()) for key, value in queries.items()},
              "matches": {k: sorted(v, key=lambda x: (-x["coverage"], x["work"])) for k,v in sorted(matches.items())}}
    DEDUP.write_bytes(encoded(report))
    return report


def generate(groups):
    report = json.loads(DEDUP.read_bytes())
    if report["source_manifest_sha256"] != sha(PIN.read_bytes()):
        raise ValueError("Duplicate audit has different source pins")
    expected_queries = {key: sha(" ".join(value).encode()) for key,value in dedup_queries(groups).items()}
    if expected_queries != report.get("candidate_sha256"):
        raise ValueError("Duplicate audit has different extracted candidate readings")
    actual = {p.name: sha(p.read_bytes()) for p in baseline_files()}
    if actual != report["file_sha256"]:
        raise ValueError("Duplicate audit is stale for the served corpus")
    artifacts, admitted, held = {}, [], []
    for source, rows, notes in groups:
        if source["disposition"] != "approved_subject_to_gates":
            held.append({"ebook_id": source["ebook_id"], "reason": source["reason"]})
            continue
        qs = [q for q in report["candidate_token_counts"] if q.startswith(str(source["ebook_id"])+":")]
        if qs and all(any(m["coverage"] >= .95 for m in report["matches"].get(q, [])) for q in qs):
            raise ValueError("Candidate is already represented by existing corpus witnesses")
        for row in rows:
            check_row_quality(row)
        payload = b"".join(json.dumps(row, ensure_ascii=False).encode() + b"\n" for row in rows)
        corpus_path = f"data/corpus/{source['work']}.jsonl"
        artifacts[corpus_path] = payload
        note_path = f"data/paratext/gutenberg/{source['ebook_id']}.jsonl"
        artifacts[note_path] = b"".join(json.dumps({**note, "source": "gutenberg", "source_sha256": source["source_sha256"]}, ensure_ascii=False).encode()+b"\n" for note in notes)
        if source["ebook_id"] == 66595:
            base = "data/critical_editions/gutenberg-66595"
            manifest = {"schema_version": 2, "status": "served-critical-edition", "work": source["work"],
                "edition": source["edition"], "author": source["author"], "author_name": source["author_name"],
                "title": source["title"], "edition_name": source["edition_name"], "provider": "gutenberg",
                "edition_identifiers": {"gutenberg": str(source["ebook_id"])}, "source_url": source["source_url"],
                "source_path": source["source_path"], "source_sha256": source["source_sha256"],
                "source_license": source["license"], "source_editors": source["source_editors"],
                "attribution": "William Fairley, Monumentum Ancyranum (Philadelphia, 1898); Project Gutenberg 66595 (2021).",
                "physical_citation_scheme": "column.line", "language": "grc", "critical_markup_schema": SCHEMA,
                "corpus_path": corpus_path, "corpus_sha256": sha(payload), "reader_path": base+"/reader.html",
                "counts": {"lines": len(rows), "surface_tokens": sum(len(r["tokens"]) for r in rows),
                    "lexical_tokens": sum(sum(t["lexical_eligible"] for t in r["tokens"]) for r in rows)},
                "token_policy": "Printed restored letters and line fragments remain visible and uncounted. Every alternative note is retained separately. No restoration is promoted to an attested word, and no source reading is corrected.",
                "apparatus_path": note_path,
                "policy": source["edition_qualification"], "generated_by": "scripts/ingest_gutenberg_historical.py"}
            artifacts[base+"/manifest.json"] = encoded(manifest)
            artifacts[base+"/reader.html"] = render_html(rows, manifest).encode()
        admitted.append({**source, "corpus_path": corpus_path, "corpus_sha256": sha(payload),
                         "passages": len(rows), "notes_path": note_path})
    audit = {"schema_version": 1, "operation": "admit-historical-gutenberg", "date": "2026-10-20",
             "source_manifest_sha256": sha(PIN.read_bytes()), "dedup_report_sha256": sha(DEDUP.read_bytes()),
             "generator_sha256": GENERATOR_SHA256, "admitted": admitted, "quarantined": held,
             "dependency_sha256": DEPENDENCY_SHA256,
             "text_corrections": [],
             "upstream_reported_corrections": [c for source,_,_ in groups for c in upstream_corrections(source)],
             "output_sha256": {k: sha(v) for k,v in artifacts.items()},
             "reversal": "Run scripts/ingest_gutenberg_historical.py --undo, then rebuild the shared corpus metadata. Retained source snapshots and this audit are not removed."}
    artifacts[AUDIT] = encoded(audit)
    return artifacts


def check_row_quality(row):
    # A lexical projection may omit a damaged character. Reader text must pass
    # the same hard quality gate, rather than hiding it through that omission.
    for text in {row["text"], row.get("analysis_text", row["text"])}:
        metric = quality(text)
        if metric["replacement_characters"] or metric["mixed_script_tokens"] or metric["case_join_tokens"]:
            raise ValueError(f"Unresolved text-quality defect at {row['urn']}:{row['locus']}: {metric}")


def apply(artifacts, *, undo=False):
    targets = {k:v for k,v in artifacts.items() if not (undo and k == AUDIT)}
    for name, raw in targets.items():
        path = ROOT / name
        if path.exists() and path.read_bytes() != raw:
            if name == AUDIT and not undo:
                # A regenerated audit may add provenance while every admitted
                # output remains byte-identical. Validate that before replacing.
                old = json.loads(path.read_bytes())
                if (all(not (ROOT/p).exists() for p in old["output_sha256"]) or
                        all((ROOT/p).is_file() and sha((ROOT/p).read_bytes())==digest
                            for p,digest in old["output_sha256"].items())):
                    continue
            raise ValueError(f"Refusing to replace or undo independently modified output: {name}")
    for name, raw in targets.items():
        path = ROOT / name
        if undo:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)


def undo_admission():
    """Reverse the recorded admission even if its source was invalidated."""
    audit = json.loads((ROOT / AUDIT).read_bytes())
    paths = []
    for name, digest in audit["output_sha256"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or relative.parts[0] != "data":
            raise ValueError("Admission output must be repository-relative data")
        path = ROOT / relative
        if path.exists() and sha(path.read_bytes()) != digest:
            raise ValueError(f"Refusing to undo independently modified output: {name}")
        paths.append(path)
    for path in paths:
        path.unlink(missing_ok=True)
    return len(paths)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pin",action="store_true")
    p.add_argument("--refresh-review",action="store_true",help="Apply reviewed scope changes with unchanged source checksums")
    p.add_argument("--scan-corpus",action="store_true")
    action=p.add_mutually_exclusive_group()
    action.add_argument("--apply",action="store_true")
    action.add_argument("--check",action="store_true")
    action.add_argument("--undo",action="store_true")
    args=p.parse_args()
    if args.undo:
        print(json.dumps({"undone_outputs": undo_admission(), "audit_retained": True}))
        return
    if args.pin: pin_sources()
    if args.refresh_review: refresh_review()
    groups=candidates()
    if args.scan_corpus: scan_corpus(groups)
    if not DEDUP.exists():
        print("Pinned and extracted candidates; run --scan-corpus before admission.")
        return
    artifacts=generate(groups)
    if args.apply: apply(artifacts)
    if args.check:
        changed=[name for name,raw in artifacts.items() if not (ROOT/name).exists() or (ROOT/name).read_bytes()!=raw]
        if changed: raise ValueError(f"Generated Gutenberg admission differs: {changed}")
    print(json.dumps({"outputs":len(artifacts),"admitted":[s['work'] for s,_,_ in groups if s['disposition']=='approved_subject_to_gates']},ensure_ascii=False))


if __name__ == "__main__":
    main()
