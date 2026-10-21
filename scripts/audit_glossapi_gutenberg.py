#!/usr/bin/env python3
"""Recover and verify Gutenberg witnesses for the pinned GlossAPI collection.

This is discovery and verification, never corpus admission. Cached source bytes
are checked against a separately retained source manifest. --pin creates that
manifest on first discovery; subsequent runs refuse changed or missing pins.
The supplied Greek-variety classifier is recorded but never used as evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
SOURCE_KEY = "glossapi_gutenberg_greek"
CATALOG = "https://www.gutenberg.org/browse/languages/el"
DEFAULT_CACHE = ROOT / "data/cache/glossapi/gutenberg"
DEFAULT_PINS = ROOT / "data/glossapi_gutenberg_sources.json"
DEFAULT_OUTPUT = ROOT / "data/glossapi_gutenberg_identity_report.json"
REVIEWS = ROOT / "data/glossapi_gutenberg_reviews.json"
WORD = re.compile(r"[^\W\d_](?:[^\W\d_]|[\u0300-\u036f])*|\d+", re.UNICODE)
GREEK = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fold(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", value.casefold())
                   if c.isalnum())


def tokens(text: str, *, accents: bool = True) -> list[str]:
    text = unicodedata.normalize("NFC", text).casefold()
    if not accents:
        text = "".join(c for c in unicodedata.normalize("NFD", text)
                       if not unicodedata.combining(c))
    return WORD.findall(text)


def catalog_candidates(raw: bytes) -> dict[str, list[dict]]:
    soup = BeautifulSoup(raw, "html.parser")
    candidates: dict[str, dict[int, dict]] = defaultdict(dict)
    creator = ""
    for element in soup.find_all(["h2", "li"]):
        if element.name == "h2":
            creator = element.get_text(" ", strip=True)
            continue
        for link in element.find_all("a", href=True):
            match = re.fullmatch(r"/ebooks/(\d+)", link["href"])
            if not match:
                continue
            title = link.get_text(" ", strip=True)
            key, ident = fold(title), int(match[1])
            candidate = candidates[key].setdefault(ident, {
                "ebook_id": ident, "title": title, "creators": [],
            })
            if creator not in candidate["creators"]:
                candidate["creators"].append(creator)
    return {key: sorted(value.values(), key=lambda x: x["ebook_id"])
            for key, value in candidates.items()}


def choose_candidate(row: dict, candidates: list[dict]) -> tuple[dict | None, str]:
    author = row.get("Author")
    matching = [c for c in candidates if author and any(
        fold(author) in fold(creator) for creator in c["creators"])]
    if len(matching) == 1:
        return matching[0], "title_and_author"
    if len(candidates) == 1:
        return candidates[0], "unique_title" if not author else "title_only_author_unverified"
    return None, "ambiguous" if candidates else "unmatched"


def book_metadata(raw: bytes, url: str) -> tuple[dict, str]:
    soup = BeautifulSoup(raw, "html.parser")
    metadata: dict[str, list[str]] = defaultdict(list)
    keep = {"Author", "Translator", "Editor", "Title", "Alternate Title",
            "Language", "Release Date", "Copyright", "eBook-No."}
    for row in soup.select("table.bibrec tr"):
        heading, value = row.find("th"), row.find("td")
        if heading and value and heading.get_text(" ", strip=True) in keep:
            metadata[heading.get_text(" ", strip=True)].append(value.get_text(" ", strip=True))
    link = soup.select_one("a.read-online-button[href]")
    if link is None:
        link = soup.find("a", href=True, type=re.compile(r"^text/html"))
    if link is None:
        raise ValueError(f"No HTML reading edition at {url}")
    resolved = urljoin(url, link["href"])
    if urlparse(resolved).hostname != "www.gutenberg.org":
        raise ValueError(f"Unexpected reading-edition host: {resolved}")
    if "eBook-No." not in metadata:
        raise ValueError(f"Not a Gutenberg catalog record: {url}")
    return dict(metadata), resolved


def source_body(raw: bytes) -> str:
    soup = BeautifulSoup(raw, "html.parser")
    for element in soup.select("script, style, #pg-header, #pg-footer, .pg-boilerplate"):
        element.decompose()
    return (soup.body or soup).get_text(" ", strip=True)


def compare_text(row_text: str, source_text: str, *, accents: bool = True) -> dict:
    left, right = tokens(source_text, accents=accents), tokens(row_text, accents=accents)
    if not right:
        return {"dataset_tokens": 0, "matched_tokens": 0, "coverage": None,
                "unmatched_spans": [], "source_token_bounds": None}
    # A whole contiguous match is both faster and stronger than sampled windows.
    haystack, needle = " ".join(left), " ".join(right)
    found = haystack.find(needle)
    if found >= 0 and (found == 0 or haystack[found - 1] == " ") and (
            found + len(needle) == len(haystack) or haystack[found + len(needle)] == " "):
        start = haystack[:found].count(" ")
        return {"dataset_tokens": len(right), "matched_tokens": len(right),
                "coverage": 1.0, "unmatched_spans": [],
                "source_token_bounds": [start, start + len(right)]}
    matcher = SequenceMatcher(None, left, right, autojunk=True)
    blocks = matcher.get_matching_blocks()
    matched = sum(block.size for block in blocks)
    spans = []
    for tag, a, b, c, d in matcher.get_opcodes():
        if tag in {"replace", "insert"}:
            spans.append({"dataset_tokens": [c, d], "source_tokens": [a, b],
                          "dataset_sample": " ".join(right[c:min(d, c + 20)]),
                          "source_sample": " ".join(left[a:min(b, a + 20)])})
    actual = [block for block in blocks if block.size]
    return {"dataset_tokens": len(right), "matched_tokens": matched,
            "coverage": matched / len(right), "unmatched_spans": spans,
            "source_token_bounds": [actual[0].a, actual[-1].a + actual[-1].size] if actual else None}


def quality(text: str) -> dict:
    all_tokens = WORD.findall(text)
    words = [word for word in all_tokens if not word.isdecimal()]
    greek = [word for word in words if GREEK.search(word)]
    mixed = Counter(word for word in greek if any(
        c.isalpha() and not GREEK.fullmatch(c) for c in word))
    joins = Counter(word for word in greek if any(
        GREEK.fullmatch(a) and GREEK.fullmatch(b) and a.islower() and b.isupper()
        for a, b in zip(word, word[1:])))
    return {"lexical_tokens": len(words), "greek_tokens": len(greek),
            "numeric_tokens": len(all_tokens)-len(words),
            "greek_types": len(set(unicodedata.normalize("NFC", w).casefold() for w in greek)),
            "non_nfc_tokens": sum(w != unicodedata.normalize("NFC", w) for w in words),
            "orphan_combining_marks": sum(bool(unicodedata.combining(c)) and
                (i == 0 or not (text[i-1].isalpha() or unicodedata.combining(text[i-1])))
                for i,c in enumerate(text)),
            "replacement_characters": text.count("\ufffd"),
            "mixed_script_tokens": sum(mixed.values()), "mixed_script_forms": dict(mixed.most_common(20)),
            "case_join_tokens": sum(joins.values()), "case_join_forms": dict(joins.most_common(20)),
            "polytonic_characters": sum("\u1f00" <= c <= "\u1fff" for c in text)}


def window_coverage(row_text: str, source_text: str, width: int = 8) -> dict:
    """Exact contextual coverage even when footnotes moved within the book.

    This verifies a witness, not passage order or suitability for admission.
    No missing token is credited just because it has a dictionary spelling.
    """
    left, right = tokens(source_text), tokens(row_text)
    windows = {tuple(left[i:i + width]) for i in range(len(left) - width + 1)}
    covered = bytearray(len(right))
    hits = 0
    for i in range(len(right) - width + 1):
        if tuple(right[i:i + width]) in windows:
            covered[i:i + width] = b"\x01" * width
            hits += 1
    return {"window_words": width, "matched_windows": hits,
            "covered_tokens": sum(covered), "dataset_tokens": len(right),
            "coverage": sum(covered) / len(right) if right else None}


def typographic_coverage(row_text: str, source_text: str, width: int = 32) -> dict:
    """Fingerprint letter-spaced emphasis and relocated notes without editing.

    Word boundaries and numeric note references are ignored only for this
    source-identity check. Token accounting and every original difference stay
    in the word-based comparisons; this is never a lexical normalization rule.
    """
    def stream(text):
        return "".join(c for c in unicodedata.normalize("NFC", text).casefold() if c.isalpha())
    left, right = stream(source_text), stream(row_text)
    windows = {left[i:i+width] for i in range(len(left)-width+1)}
    covered = bytearray(len(right))
    for i in range(len(right)-width+1):
        if right[i:i+width] in windows:
            covered[i:i+width] = b"\x01" * width
    return {"window_letters": width, "covered_letters": sum(covered),
            "dataset_letters": len(right), "coverage": sum(covered)/len(right) if right else None}


def scope_assessment(row: dict, metadata: dict, body: str, reviews: dict) -> dict:
    override = reviews["exceptions"].get(str(row["Text Number"]))
    if override:
        for fragment in override["required_source_fragments"]:
            if fold(fragment) not in fold(body):
                raise ValueError(f"Review evidence missing for row {row['Text Number']}: {fragment}")
        return {**override, "evidence_method": "reviewed_title_page_or_preface",
                "whole_text_eligible": False}
    # A modern editor can publish an unchanged ancient text. Only an author's
    # or translator's chronology supports this whole-document scope decision.
    modern = re.compile(r", (1[7-9]\d{2}|20\d{2})\??(?:[-–]|$)")
    modern_authors = [a for a in metadata.get("Author", []) if modern.search(a)]
    modern_translators = [a for a in metadata.get("Translator", []) if modern.search(a)]
    counts = Counter(tokens(row["Text"]))
    diagnostics = {w: counts[w] for w in ("θα", "δεν", "είναι", "είνε", "ήτο") if counts[w]}
    if modern_authors or modern_translators:
        return {"disposition": "excluded_modern", "kind": "modern_composition_or_translation",
                "language": "el", "whole_text_eligible": False,
                "evidence_method": "reviewed_contributor_chronology_and_running_text",
                "modern_authors": modern_authors, "modern_translators": modern_translators,
                "running_text_diagnostics": diagnostics}
    if metadata.get("Translator") and sum(diagnostics.values()) >= 10:
        return {"disposition": "excluded_modern", "kind": "modern_translation",
                "language": "el", "whole_text_eligible": False,
                "evidence_method": "reviewed_translation_role_and_modern_running_text",
                "translators": metadata["Translator"], "running_text_diagnostics": diagnostics}
    return {"disposition": "quarantined_scope", "whole_text_eligible": False,
            "language": None, "reason": "No independently established historical original; review required"}


class SourceCache:
    def __init__(self, root: Path, pins: dict, fetch: bool, discover: bool):
        self.root, self.pins, self.fetch, self.discover = root, pins, fetch, discover
        self.observed = {}
        self.last_request = 0.0

    def get(self, name: str, url: str) -> bytes:
        expected = self.pins.get(name)
        if not self.discover and (not expected or expected["url"] != url):
            raise ValueError(f"Unpinned source: {name}")
        path = self.root / name
        if name == "greek.catalog.html" and not path.exists():
            retained = ROOT / "data/reference/gutenberg/greek-catalog.html"
            if retained.exists():
                path = retained
        if not path.exists():
            if not self.fetch:
                raise FileNotFoundError(f"Missing source {name}; use --fetch")
            time.sleep(max(0, 1.0 - (time.monotonic() - self.last_request)))
            request = Request(url, headers={"User-Agent": "Open-Greek-Corpus/edition-verification"})
            with urlopen(request, timeout=45) as response:
                if response.headers.get_content_type() != "text/html":
                    raise ValueError(f"Expected HTML at {url}")
                data = response.read()
            self.last_request = time.monotonic()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        raw = path.read_bytes()
        actual = {"url": url, "sha256": sha(raw), "size": len(raw)}
        if expected and actual != {k: expected[k] for k in ("url", "sha256", "size")}:
            raise ValueError(f"Changed pinned source: {name}")
        self.observed[name] = actual
        return raw


def load_rows(input_path: Path | None, fetch: bool) -> tuple[list[dict], dict]:
    import pyarrow.parquet as pq
    decisions = json.loads((ROOT / "data/glossapi_source_decisions.json").read_text())
    source = next(item for item in decisions["sources"] if item["key"] == SOURCE_KEY)
    if input_path is None:
        from huggingface_hub import hf_hub_download
        input_path = Path(hf_hub_download(source["repo"], source["artifact"]["path"],
                         repo_type="dataset", revision=source["revision"], local_files_only=not fetch))
    raw = input_path.read_bytes()
    if len(raw) != source["artifact"]["size"] or sha(raw) != source["artifact"]["sha256"]:
        raise ValueError("GlossAPI artifact does not match the OGC source decision")
    rows = pq.read_table(input_path).to_pylist()
    ids = [r["Text Number"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate dataset Text Number")
    return rows, source


def audit(rows: list[dict], cache: SourceCache, reviews: dict | None = None) -> dict:
    catalog = catalog_candidates(cache.get("greek.catalog.html", CATALOG))
    records = []
    for index, row in enumerate(rows, 1):
        candidates = catalog.get(fold(row["Title"]), [])
        candidate, method = choose_candidate(row, candidates)
        record = {"text_number": row["Text Number"], "title": row["Title"],
                  "dataset_author": row["Author"], "dataset_translator": row["Translator"],
                  "supplied_variety_unverified": row["Variety"],
                  "dataset_text_sha256": sha(row["Text"].encode()),
                  "catalog_candidates": candidates, "candidate_selection": method,
                  "quality": quality(row["Text"])}
        if candidate:
            ident = candidate["ebook_id"]
            url = f"https://www.gutenberg.org/ebooks/{ident}"
            catalog_name = f"{ident}.catalog.html"
            retained_metadata = cache.pins.get(catalog_name, {})
            if "metadata" in retained_metadata:
                metadata, text_url = retained_metadata["metadata"], retained_metadata["text_url"]
            else:
                metadata, text_url = book_metadata(cache.get(catalog_name, url), url)
                # Keep stable bibliographic facts, rather than requiring future
                # readers to reproduce a web page's changing download counts.
                cache.observed[catalog_name].update({"metadata": metadata, "text_url": text_url})
            if metadata["eBook-No."] != [str(ident)]:
                raise ValueError(f"Wrong book returned for {ident}")
            body = source_body(cache.get(f"{ident}.text.html", text_url))
            comparison = compare_text(row["Text"], body)
            ordered = comparison["coverage"] or 0
            folded = compare_text(row["Text"], body, accents=False) if ordered < 0.9999 else None
            contextual = window_coverage(row["Text"], body) if ordered < 0.9999 else None
            coverage = max(ordered, (folded["coverage"] or 0) if folded else 0,
                           (contextual["coverage"] or 0) if contextual else 0)
            typographic = typographic_coverage(row["Text"], body) if coverage < .98 else None
            coverage = max(coverage, (typographic["coverage"] or 0) if typographic else 0)
            record.update({"ebook_id": ident, "url": url, "text_url": text_url,
                           "gutenberg_metadata": metadata, "text_comparison": comparison,
                           "accent_folded_comparison": folded,
                           "exact_contextual_comparison": contextual,
                           "typographic_comparison": typographic,
                           "identity_status": "text_matched" if coverage >= 0.98 else "requires_review",
                           "source_opening": body[:2500] if metadata.get("Copyright") == ["Public domain in the USA."] else None})
            if reviews:
                record["scope_review"] = scope_assessment(row, metadata, body, reviews)
                if metadata.get("Copyright") != ["Public domain in the USA."]:
                    for comparison_result in (comparison, folded):
                        if comparison_result:
                            for span in comparison_result["unmatched_spans"]:
                                span.pop("dataset_sample", None)
                                span.pop("source_sample", None)
        else:
            record["identity_status"] = "unresolved"
        records.append(record)
        print(f"{index}/{len(rows)} row {row['Text Number']}: {record['identity_status']} "
              f"{record.get('text_comparison', {}).get('coverage')}", flush=True)
    return {"schema_version": 1, "source_key": SOURCE_KEY,
            "recipe": {"matching": "Ordered words, exact eight-word contexts for moved notes, and exact 32-letter contexts for typographic letter spacing; original word differences remain visible. NFC casefold, with accent folding reported separately.",
                       "identity_threshold": 0.98, "classifier_used_for_admission": False,
                       "corpus_write_attempted": False},
            "statistics": {"rows": len(records),
                           "identities": dict(Counter(r["identity_status"] for r in records)),
                           "scope_dispositions": dict(Counter(r.get("scope_review", {}).get("disposition", "not_reviewed") for r in records)),
                           "eligible_whole_texts": sum(r.get("scope_review", {}).get("whole_text_eligible", False) for r in records)},
            "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--pins", type=Path, default=DEFAULT_PINS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--pin", action="store_true", help="Create a new source manifest; refuses an existing path")
    parser.add_argument("--row", type=int, action="append", help="Restrict a sanity check to these Text Numbers")
    args = parser.parse_args()
    if args.pin and args.pins.exists():
        parser.error("--pin refuses to overwrite an existing source manifest")
    pins = json.loads(args.pins.read_text())["files"] if args.pins.exists() else {}
    if not pins and not args.pin:
        parser.error("A source manifest is required; use --pin for initial discovery")
    rows, source = load_rows(args.input, args.fetch)
    if args.row:
        selected = set(args.row)
        rows = [r for r in rows if r["Text Number"] in selected]
        if {r["Text Number"] for r in rows} != selected:
            parser.error("Unknown requested Text Number")
    cache = SourceCache(args.cache, pins, args.fetch, args.pin)
    reviews = json.loads(REVIEWS.read_text()) if REVIEWS.exists() else None
    report = audit(rows, cache, reviews)
    if reviews:
        report["reviews_sha256"] = sha(REVIEWS.read_bytes())
    report["generator_sha256"] = GENERATOR_SHA256
    report["source_decisions_sha256"] = sha((ROOT / "data/glossapi_source_decisions.json").read_bytes())
    report["source_artifact_sha256"] = source["artifact"]["sha256"]
    if args.pin:
        retained_catalog = ROOT / "data/reference/gutenberg/greek-catalog.html"
        catalog_bytes = (args.cache / "greek.catalog.html").read_bytes()
        if retained_catalog.exists() and retained_catalog.read_bytes() != catalog_bytes:
            raise ValueError("Retained discovery catalog changed")
        retained_catalog.parent.mkdir(parents=True, exist_ok=True)
        retained_catalog.write_bytes(catalog_bytes)
        args.pins.parent.mkdir(parents=True, exist_ok=True)
        args.pins.write_text(json.dumps({"schema_version": 1, "source_key": SOURCE_KEY,
                            "retrieved_on": datetime.now(timezone.utc).date().isoformat(),
                            "files": dict(sorted(cache.observed.items()))}, ensure_ascii=False, indent=2) + "\n")
    report["source_manifest_sha256"] = sha(args.pins.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report["statistics"], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
