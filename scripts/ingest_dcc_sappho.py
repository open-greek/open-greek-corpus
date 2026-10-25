#!/usr/bin/env python3
"""Replace the apparatus-heavy Sappho OCR with DCC's readable Greek text.

Dickinson College Commentaries publishes a peer-reviewed teaching text of the
extant fragments under CC BY-SA 4.0.  Each poem page keeps the Greek reading
text in the article's body field and puts commentary, vocabulary, and
translation in separate fields.  This importer takes only that reading-text
field, removes inline footnotes and display line numbers, and preserves its
physical lines in ``text_lines``.

The source is not silently overwritten.  On the first ``--apply`` the exact
135-row Bergk OCR file is archived under ``data/corpus_changes``.  The audit
record and a per-page SHA-256 manifest make the source swap reversible and
show precisely which DCC representation produced every row.

  python3 scripts/ingest_dcc_sappho.py --fetch
  python3 scripts/ingest_dcc_sappho.py                 # dry run
  python3 scripts/ingest_dcc_sappho.py --apply
  python3 scripts/reconcile_corpus_editions.py
  python3 scripts/build_registry.py
  python3 scripts/build_work_index.py
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import urllib.request
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from lxml import html

REPO = Path(__file__).resolve().parent.parent
CACHE = REPO / "data" / "cache" / "dcc" / "sappho"
CORPUS = REPO / "data" / "corpus"
CHANGES = REPO / "data" / "corpus_changes"

BASE_URL = "https://dcc.dickinson.edu"
INDEX_PATH = "/sappho/frag-1"
ABOUT_URL = "https://dcc.dickinson.edu/about-dcc"
SLUG = "sappho.fragmenta"
EDITION = "dcc-sappho"
SOURCE = "dcc"
LICENSE = "CC-BY-SA-4.0"
OLD_EDITION = "bergk-plg3-ocr-frag"
OLD_SHA256 = "14f9754bee6595573fd9fbbcacfbf4f35df2ae9f97b87d97bc4e7a828f7a2861"
ARCHIVE = CHANGES / f"{SLUG}.pre-dcc-ocr.jsonl"
AUDIT = CHANGES / "sappho-fragmenta-dcc-replacement.json"
MANIFEST = CHANGES / "sappho-fragmenta-dcc-sources.json"

GREEK_RE = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")
PAGE_RE = re.compile(r"/sappho/(?:brothers-poem|frag-[0-9-]+)\Z")
SIMPLE_HEADING_RE = re.compile(r"\s*(\d+[A-Za-z]?)\s*\Z")
FRAGMENT_HEADING_RE = re.compile(r"\s*Fragment\s+(\d+[A-Za-z]?)\b", re.I)
USER_AGENT = "open-greek-corpus/ingest (https://github.com/open-greek/open-greek-corpus)"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def cache_path(page_path: str) -> Path:
    return CACHE / f"{page_path.rsplit('/', 1)[-1]}.html"


def request(page_path: str) -> bytes:
    req = urllib.request.Request(BASE_URL + page_path,
                                 headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def discover_page_paths(page: bytes) -> list[str]:
    doc = html.fromstring(page.decode("utf-8"))
    paths: list[str] = []
    for link in doc.xpath("//a[@href]"):
        path = link.get("href", "")
        if PAGE_RE.fullmatch(path) and path not in paths:
            paths.append(path)
    if INDEX_PATH not in paths or len(paths) < 90:
        raise SystemExit(f"ABORT: DCC Sappho menu yielded only {len(paths)} poem pages")
    return paths


def fetch() -> list[str]:
    CACHE.mkdir(parents=True, exist_ok=True)
    index = request(INDEX_PATH)
    paths = discover_page_paths(index)

    def download(path: str) -> tuple[str, bytes]:
        return path, index if path == INDEX_PATH else request(path)

    with ThreadPoolExecutor(max_workers=10) as pool:
        pages = list(pool.map(download, paths))
    for path, body in pages:
        cache_path(path).write_bytes(body)
    print(f"fetched {len(pages)} DCC Sappho pages -> {CACHE.relative_to(REPO)}")
    return paths


def cached_page_paths() -> list[str]:
    index = cache_path(INDEX_PATH)
    if not index.exists():
        raise SystemExit(f"ABORT: {index.relative_to(REPO)} missing; run --fetch")
    paths = discover_page_paths(index.read_bytes())
    missing = [path for path in paths if not cache_path(path).exists()]
    if missing:
        raise SystemExit(f"ABORT: {len(missing)} cached DCC pages missing; run --fetch")
    return paths


def base_locus(page_path: str) -> str:
    name = page_path.rsplit("/", 1)[-1]
    if name == "brothers-poem":
        return "Brothers"
    return name.removeprefix("frag-").split("-", 1)[0]


def heading_locus(text: str) -> str | None:
    match = SIMPLE_HEADING_RE.fullmatch(text)
    if match:
        return match.group(1)
    match = FRAGMENT_HEADING_RE.match(text)
    return match.group(1) if match else None


def clean_text(element) -> str:
    node = copy.deepcopy(element)
    for unwanted in node.xpath(
        ".//fn | .//*[contains(concat(' ', normalize-space(@class), ' '), ' line-number ')]"
    ):
        unwanted.drop_tree()
    return " ".join(node.text_content().split())


def is_reading_text(text: str) -> bool:
    greek = len(GREEK_RE.findall(text))
    latin = len(re.findall(r"[A-Za-z]", text))
    return greek > 0 and latin <= greek


def extract_page(page_path: str, page: bytes) -> list[dict]:
    doc = html.fromstring(page.decode("utf-8"))
    fields = doc.xpath(
        "//article//*[contains(concat(' ', normalize-space(@class), ' '), ' field--name-body ')]"
    )
    if len(fields) != 1:
        raise ValueError(f"{page_path}: expected one article body, found {len(fields)}")

    current = base_locus(page_path)
    lines_by_locus: OrderedDict[str, list[str]] = OrderedDict()
    lines_by_locus[current] = []

    for element in fields[0]:
        tag = element.tag.lower() if isinstance(element.tag, str) else ""
        raw = " ".join(element.text_content().split())
        if tag == "h4":
            locus = heading_locus(raw)
            if locus:
                current = locus
                lines_by_locus.setdefault(current, [])
            continue
        if tag == "p" and element.xpath("./strong"):
            locus = heading_locus(raw.split(" ", 1)[0])
            if locus and not GREEK_RE.search(raw):
                current = locus
                lines_by_locus.setdefault(current, [])
                continue
        if tag != "p" and not (tag == "div" and element.get("lang") == "grc"):
            continue
        text = clean_text(element)
        if is_reading_text(text):
            lines_by_locus.setdefault(current, []).append(text)

    digest = sha256_bytes(page)
    url = BASE_URL + page_path
    records = []
    for locus, lines in lines_by_locus.items():
        if not lines:
            continue
        records.append({
            "urn": SLUG,
            "edition": EDITION,
            "locus": locus,
            "source": SOURCE,
            "license": LICENSE,
            "text": " ".join(lines),
            "text_lines": lines,
            "provenance": {
                "url": url,
                "page_sha256": digest,
                "license_url": ABOUT_URL,
                "method": "DCC article reading-text field; footnotes and display line numbers removed",
            },
        })
    return records


def build() -> tuple[list[dict], list[dict]]:
    records: list[dict] = []
    sources = []
    seen_loci: set[str] = set()
    for path in cached_page_paths():
        page_file = cache_path(path)
        page = page_file.read_bytes()
        page_records = extract_page(path, page)
        if not page_records:
            raise SystemExit(f"ABORT: {path} yielded no Greek reading text")
        for record in page_records:
            locus = record["locus"]
            if locus in seen_loci:
                raise SystemExit(f"ABORT: duplicate DCC fragment locus {locus}")
            seen_loci.add(locus)
            records.append(record)
        sources.append({
            "url": BASE_URL + path,
            "sha256": sha256_bytes(page),
            "loci": [record["locus"] for record in page_records],
        })

    tokens = sum(1 for record in records for word in record["text"].split()
                 if GREEK_RE.search(word))
    if len(records) < 120 or tokens < 3_500:
        raise SystemExit(f"ABORT: implausibly small DCC extraction ({len(records)} rows, {tokens} tokens)")
    return records, sources


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n"
                            for record in records), encoding="utf-8")


def apply(records: list[dict], sources: list[dict]) -> None:
    dst = CORPUS / f"{SLUG}.jsonl"
    CHANGES.mkdir(parents=True, exist_ok=True)
    old = [json.loads(line) for line in dst.read_text(encoding="utf-8").splitlines()
           if line.strip()]
    old_edition = old[0].get("edition") if old else None
    if old_edition not in {OLD_EDITION, EDITION}:
        raise SystemExit(f"ABORT: refusing to replace unexpected edition {old_edition!r}")

    old_meta = None
    if old_edition == OLD_EDITION:
        digest = sha256_file(dst)
        if digest != OLD_SHA256:
            raise SystemExit(f"ABORT: old Sappho OCR digest changed: {digest}")
        if ARCHIVE.exists() and sha256_file(ARCHIVE) != digest:
            raise SystemExit(f"ABORT: existing archive {ARCHIVE.relative_to(REPO)} differs")
        ARCHIVE.write_bytes(dst.read_bytes())
        old_meta = {
            "edition": OLD_EDITION,
            "rows": len(old),
            "greek_tokens": sum(1 for row in old for word in row["text"].split()
                                if GREEK_RE.search(word)),
            "sha256": digest,
            "archived_to": str(ARCHIVE.relative_to(REPO)),
        }
        print(f"archived {len(old)} OCR rows -> {ARCHIVE.relative_to(REPO)}")

    write_jsonl(dst, records)
    tokens = sum(1 for record in records for word in record["text"].split()
                 if GREEK_RE.search(word))
    today = date.today().isoformat()
    MANIFEST.write_text(json.dumps({
        "_meta": {
            "work": SLUG,
            "source": "Dickinson College Commentaries: Sappho",
            "license": LICENSE,
            "license_url": ABOUT_URL,
            "retrieved": today,
            "generated_by": "scripts/ingest_dcc_sappho.py",
        },
        "pages": sources,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    AUDIT.write_text(json.dumps({
        "_meta": {
            "change": "replace served text (apparatus-heavy OCR -> DCC Greek reading text)",
            "work": SLUG,
            "tlg": "tlg0009.tlg001",
            "applied_by": "scripts/ingest_dcc_sappho.py",
            "date": today,
            "reversible": (
                f"restore {ARCHIVE.relative_to(REPO)} verbatim to {dst.relative_to(REPO)}, "
                "then rerun reconcile_corpus_editions.py, build_registry.py, and build_work_index.py"
            ),
        },
        "old": old_meta or {
            "edition": OLD_EDITION,
            "sha256": OLD_SHA256,
            "note": "already replaced; exact prior text remains in the named archive",
        },
        "new": {
            "edition": EDITION,
            "source": SOURCE,
            "license": LICENSE,
            "rows": len(records),
            "greek_tokens": tokens,
            "sha256": sha256_file(dst),
            "source_pages": len(sources),
            "source_manifest": str(MANIFEST.relative_to(REPO)),
        },
        "evidence": (
            "The prior Bergk OCR rows intermixed Sappho's Greek with extensive Latin and German "
            "apparatus. DCC supplies the Greek reading text in a distinct article-body field; "
            "commentary, vocabulary, and translations are separate and are not ingested."
        ),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(records)} fragment records ({tokens:,} Greek tokens) -> {dst.relative_to(REPO)}")
    print(f"wrote source manifest -> {MANIFEST.relative_to(REPO)}")
    print(f"wrote reversible audit -> {AUDIT.relative_to(REPO)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true", help="fetch all DCC Sappho poem pages")
    parser.add_argument("--apply", action="store_true", help="replace the served corpus file")
    args = parser.parse_args()
    if args.fetch:
        fetch()
    records, sources = build()
    tokens = sum(1 for record in records for word in record["text"].split()
                 if GREEK_RE.search(word))
    print(f"{'APPLY' if args.apply else 'DRY'} Sappho: {len(sources)} pages -> "
          f"{len(records)} fragment records, {tokens:,} Greek tokens")
    print(f"  loci: {records[0]['locus']} .. {records[-1]['locus']}")
    if args.apply:
        apply(records, sources)
    else:
        print("DRY RUN - nothing written (use --apply)")


if __name__ == "__main__":
    main()
