#!/usr/bin/env python3
"""
Fetch author portraits (Wikidata P18) + short bios for the Open Greek Corpus
reader's author panel. Reproducible, offline-cacheable, and audit-trailed:
every stored portrait carries its Commons file page (source_url), license,
and artist/credit, and every bio carries its Wikipedia source URL + retrieval
date, so any image or bio can be traced, re-derived, or removed by source.

Committed deliverables (small, plain git objects - no LFS):
  data/media/author_portraits/<qid>.jpg   thumbnailed portraits (<=600px longest side)
  data/author_portraits.json               qid -> {file, credit, artist, license,
                                                    license_url, source_url, retrieved}
  data/author_bios.json                    qid -> {bio, source, source_url, retrieved}

Author QIDs are the same superset the Rails importer resolves against: every
Wikidata id in data/author_authority.json plus data/source_registry.json
(mirrors Corpus::AuthorNames.collect_qids), so the manifests survive future
work additions.

Sources:
  - Wikidata SPARQL: P18 image + English description + enwiki sitelink, by QID.
  - Wikimedia Commons API (imageinfo/extmetadata): license, artist, credit,
    file-page URL, and a width-capped thumbnail.
  - Wikipedia extracts API: a one-or-two sentence lead for the bio.

Only images with a clearly public-domain or CC-reusable license are kept;
anything non-free / fair-use / unlabeled is skipped (reported, not stored).

Usage:
  python3 scripts/fetch_author_media.py --meta     # SPARQL -> cache; report P18 coverage
  python3 scripts/fetch_author_media.py --images   # download + thumbnail + license manifest
  python3 scripts/fetch_author_media.py --bios      # bios manifest
  python3 scripts/fetch_author_media.py --all
"""

import argparse
import datetime
import io
import json
import os
import re
import sys
import time
import urllib.parse
from html import unescape

import requests
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CACHE_DIR = os.path.join(DATA, "cache")  # gitignored intermediates
MEDIA_DIR = os.path.join(DATA, "media", "author_portraits")
META_CACHE = os.path.join(CACHE_DIR, "author_media_meta.json")
PORTRAITS_MANIFEST = os.path.join(DATA, "author_portraits.json")
BIOS_MANIFEST = os.path.join(DATA, "author_bios.json")

UA = "OpenGreekCorpus-authormedia/1.0 (https://opengreek.org; cisco.riordan@gmail.com)"
SPARQL = "https://query.wikidata.org/sparql"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKI_API = "https://en.wikipedia.org/w/api.php"

THUMB_MAX = 600          # longest side, px
JPEG_QUALITY = 82
SPARQL_CHUNK = 180
COMMONS_CHUNK = 50
EXTRACT_CHUNK = 20

SESSION = requests.Session()
SESSION.headers["User-Agent"] = UA

# License gate: keep only clearly reusable licenses. Matched case-insensitively
# against the Commons LicenseShortName (and, as a fallback, the machine License
# tag). Anything not matched is skipped and reported.
LICENSE_ALLOW = re.compile(
    r"public domain|^pd\b|\bpd-|cc0|cc[ -]?by|creative commons|"
    r"no restrictions|no known copyright",
    re.IGNORECASE,
)
LICENSE_DENY = re.compile(r"fair use|non[- ]?free|all rights reserved", re.IGNORECASE)


def today():
    return datetime.date.today().isoformat()


def collect_qids():
    """Every author QID in the authority + registry files, sorted.

    Mirrors Corpus::AuthorNames.collect_qids so the manifests cover the same
    superset the Rails importer resolves author rows against."""
    qids = set()
    with open(os.path.join(DATA, "author_authority.json")) as fh:
        for row in json.load(fh).values():
            if isinstance(row, dict) and row.get("wikidata"):
                qids.add(row["wikidata"])
    with open(os.path.join(DATA, "source_registry.json")) as fh:
        for row in json.load(fh).get("authors", {}).values():
            qid = (row.get("aliases") or {}).get("wikidata")
            if qid:
                qids.add(qid)
    return sorted(qids)


def sparql(query):
    for attempt in range(4):
        resp = SESSION.get(
            SPARQL, params={"query": query, "format": "json"}, timeout=120
        )
        if resp.status_code == 200:
            return resp.json()["results"]["bindings"]
        time.sleep(2 + attempt * 2)
    resp.raise_for_status()


def fetch_meta():
    """SPARQL P18 + en description + enwiki sitelink for every QID, cached."""
    qids = collect_qids()
    print(f"Collected {len(qids)} author QIDs.")
    meta = {}
    for i in range(0, len(qids), SPARQL_CHUNK):
        chunk = qids[i : i + SPARQL_CHUNK]
        values = " ".join(f"wd:{q}" for q in chunk)
        query = f"""
SELECT ?item ?image ?desc ?article WHERE {{
  VALUES ?item {{ {values} }}
  OPTIONAL {{ ?item wdt:P18 ?image. }}
  OPTIONAL {{ ?item schema:description ?desc. FILTER(LANG(?desc) = "en") }}
  OPTIONAL {{ ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> . }}
}}"""
        rows = sparql(query)
        for r in rows:
            qid = r["item"]["value"].rsplit("/", 1)[-1]
            entry = meta.setdefault(qid, {})
            if "image" in r:
                # P18 value is a Special:FilePath URL; recover the file title.
                fname = urllib.parse.unquote(r["image"]["value"].rsplit("/", 1)[-1])
                entry["image_file"] = fname
            if "desc" in r:
                entry["description"] = r["desc"]["value"]
            if "article" in r:
                title = urllib.parse.unquote(r["article"]["value"].rsplit("/", 1)[-1])
                entry["enwiki_title"] = title.replace("_", " ")
        print(f"  sparql {i + len(chunk)}/{len(qids)}  (with-image so far: "
              f"{sum(1 for v in meta.values() if v.get('image_file'))})")
        time.sleep(1)

    os.makedirs(CACHE_DIR, exist_ok=True)
    payload = {"_retrieved": today(), "qids": len(qids), "meta": meta}
    with open(META_CACHE, "w") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    with_img = sum(1 for v in meta.values() if v.get("image_file"))
    with_art = sum(1 for v in meta.values() if v.get("enwiki_title"))
    with_desc = sum(1 for v in meta.values() if v.get("description"))
    print(f"\nP18 coverage: {with_img}/{len(qids)} author QIDs have a Wikidata image.")
    print(f"enwiki article: {with_art}/{len(qids)};  en description: {with_desc}/{len(qids)}.")
    print(f"Cached -> {META_CACHE}")


def load_meta():
    with open(META_CACHE) as fh:
        return json.load(fh)["meta"]


def html_to_text(html):
    if not html:
        return None
    text = re.sub(r"<[^>]+>", "", html)
    text = unescape(text).strip()
    text = re.sub(r"\s+", " ", text)
    return text or None


def commons_imageinfo(file_titles):
    """Batch imageinfo (url + extmetadata + a width-capped thumbnail)."""
    out = {}
    for i in range(0, len(file_titles), COMMONS_CHUNK):
        chunk = file_titles[i : i + COMMONS_CHUNK]
        titles = "|".join(f"File:{t}" for t in chunk)
        params = {
            "action": "query", "titles": titles, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": THUMB_MAX,
            "iiextmetadatafilter": "LicenseShortName|License|LicenseUrl|Artist|Credit|Attribution",
            "format": "json", "formatversion": "2",
        }
        for attempt in range(4):
            resp = SESSION.get(COMMONS_API, params=params, timeout=60)
            if resp.status_code == 200:
                break
            time.sleep(2 + attempt)
        norm = {}  # normalized title -> requested filename
        data = resp.json()
        for pg in data.get("query", {}).get("pages", []):
            title = pg.get("title", "")
            fname = title.split("File:", 1)[-1]
            ii = (pg.get("imageinfo") or [None])[0]
            if ii:
                out[fname] = ii
        # handle title normalization (spaces/underscores)
        for n in data.get("query", {}).get("normalized", []):
            norm[n["to"].split("File:", 1)[-1]] = n["from"].split("File:", 1)[-1]
        for to_name, from_name in norm.items():
            if to_name in out and from_name not in out:
                out[from_name] = out[to_name]
        print(f"  commons {i + len(chunk)}/{len(file_titles)}")
        time.sleep(0.5)
    return out


def license_ok(short, machine):
    text = f"{short or ''} {machine or ''}"
    if LICENSE_DENY.search(text):
        return False
    return bool(LICENSE_ALLOW.search(text))


def download_thumb(url):
    """Fetch a thumbnail with backoff (upload.wikimedia.org throttles bulk
    pulls with 429s); return re-compressed JPEG bytes, or None on failure."""
    if not url:
        return None
    for attempt in range(5):
        try:
            resp = SESSION.get(url, timeout=90)
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(3 + attempt * 3)
                continue
            resp.raise_for_status()
            return thumbnail_to_jpeg(resp.content)
        except Exception as exc:  # noqa: BLE001
            if attempt == 4:
                print(f"    ! {exc}")
                return None
            time.sleep(2 + attempt * 2)
    return None


def thumbnail_to_jpeg(raw_bytes):
    img = Image.open(io.BytesIO(raw_bytes))
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    img.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return buf.getvalue()


def fetch_images():
    meta = load_meta()
    with_img = {q: v["image_file"] for q, v in meta.items() if v.get("image_file")}
    print(f"{len(with_img)} QIDs have a P18 image; fetching license + thumbnails.")
    info = commons_imageinfo(sorted(set(with_img.values())))

    os.makedirs(MEDIA_DIR, exist_ok=True)
    manifest = {}
    skipped = []
    for qid in sorted(with_img):
        fname = with_img[qid]
        ii = info.get(fname)
        if not ii:
            skipped.append((qid, fname, "no imageinfo"))
            continue
        ext = ii.get("extmetadata", {})
        short = (ext.get("LicenseShortName") or {}).get("value")
        machine = (ext.get("License") or {}).get("value")
        if not license_ok(short, machine):
            skipped.append((qid, fname, f"license={short or machine!r}"))
            continue
        thumburl = ii.get("thumburl") or ii.get("url")
        jpeg = download_thumb(thumburl)
        if jpeg is None:
            skipped.append((qid, fname, "download/convert failed"))
            continue
        out_path = os.path.join(MEDIA_DIR, f"{qid}.jpg")
        with open(out_path, "wb") as fh:
            fh.write(jpeg)
        artist = html_to_text((ext.get("Artist") or {}).get("value"))
        credit = html_to_text((ext.get("Credit") or {}).get("value"))
        manifest[qid] = {
            "file": f"media/author_portraits/{qid}.jpg",
            "artist": artist,
            "credit": credit,
            "license": short or machine,
            "license_url": (ext.get("LicenseUrl") or {}).get("value"),
            "source_url": ii.get("descriptionurl"),
            "commons_file": fname,
            "retrieved": today(),
        }
        print(f"  saved {qid} ({len(jpeg) // 1024} KB) [{short or machine}]")
        time.sleep(0.2)

    with open(PORTRAITS_MANIFEST, "w") as fh:
        json.dump(dict(sorted(manifest.items())), fh, ensure_ascii=False, indent=1)
    print(f"\nWrote {len(manifest)} portraits -> {PORTRAITS_MANIFEST}")
    print(f"Skipped {len(skipped)} (no info / non-free / failed):")
    lic = {}
    for _q, _f, reason in skipped:
        key = reason.split(":", 1)[0]
        lic[key] = lic.get(key, 0) + 1
    for k, v in sorted(lic.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")


# Etymology/pronunciation parenthetical right after the subject: a (...) group
# carrying Greek script, "Greek:", IPA stress marks, or a semicolon list. The
# panel already shows the Greek name and dates separately, so this is noise.
PRONUN_PAREN = re.compile(r"\s*\([^()]*(?:Greek|Latin|[Ͱ-Ͽἀ-῿]|[ˈˌ]|;)[^()]*\)")


def clean_bio(text):
    """Trim pronunciation/etymology cruft and match the reader's era style
    (BCE/CE, plain hyphens) so the bio reads like the rest of the app."""
    if not text:
        return text
    text = PRONUN_PAREN.sub("", text)
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\bBC\b", "BCE", text)
    text = re.sub(r"\bAD\b", "CE", text)
    text = re.sub(r"\s+([,.;])", r"\1", text)  # tidy space before punctuation
    return re.sub(r"\s+", " ", text).strip()


def first_sentences(text, max_chars=280):
    text = clean_bio(re.sub(r"\s+", " ", (text or "").strip()))
    if len(text) <= max_chars:
        return text or None
    cut = text[:max_chars]
    dot = max(cut.rfind(". "), cut.rfind("; "))
    if dot > 80:
        return cut[: dot + 1].strip()
    return cut.rsplit(" ", 1)[0].strip() + "…"


def wiki_extracts(titles):
    """Batch two-sentence plain-text lead extracts, title -> extract."""
    out = {}
    for i in range(0, len(titles), EXTRACT_CHUNK):
        chunk = titles[i : i + EXTRACT_CHUNK]
        params = {
            "action": "query", "prop": "extracts",
            "exintro": "1", "explaintext": "1", "exsentences": "2",
            "redirects": "1", "titles": "|".join(chunk),
            "format": "json", "formatversion": "2",
        }
        for attempt in range(4):
            resp = SESSION.get(WIKI_API, params=params, timeout=60)
            if resp.status_code == 200:
                break
            time.sleep(2 + attempt)
        data = resp.json()
        redir = {r["from"]: r["to"] for r in data.get("query", {}).get("redirects", [])}
        norm = {n["from"]: n["to"] for n in data.get("query", {}).get("normalized", [])}
        by_title = {pg["title"]: pg.get("extract", "") for pg in data.get("query", {}).get("pages", [])}
        for t in chunk:
            resolved = norm.get(t, t)
            resolved = redir.get(resolved, resolved)
            out[t] = by_title.get(resolved, "")
        print(f"  extracts {i + len(chunk)}/{len(titles)}")
        time.sleep(0.3)
    return out


def fetch_bios():
    meta = load_meta()
    titles = {q: v["enwiki_title"] for q, v in meta.items() if v.get("enwiki_title")}
    print(f"{len(titles)} QIDs have an enwiki article; fetching lead extracts.")
    extracts = wiki_extracts(sorted(set(titles.values())))

    manifest = {}
    for qid in sorted(meta):
        m = meta[qid]
        title = m.get("enwiki_title")
        bio = first_sentences(extracts.get(title, "")) if title else None
        if not bio:
            # fall back to the Wikidata one-line description
            bio = first_sentences(m.get("description"))
            source = "Wikidata"
            source_url = f"https://www.wikidata.org/wiki/{qid}" if bio else None
        else:
            source = "Wikipedia"
            source_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
        if not bio:
            continue
        manifest[qid] = {
            "bio": bio,
            "source": source,
            "source_url": source_url,
            "retrieved": today(),
        }
    with open(BIOS_MANIFEST, "w") as fh:
        json.dump(dict(sorted(manifest.items())), fh, ensure_ascii=False, indent=1)
    wp = sum(1 for v in manifest.values() if v["source"] == "Wikipedia")
    print(f"\nWrote {len(manifest)} bios -> {BIOS_MANIFEST} "
          f"({wp} from Wikipedia, {len(manifest) - wp} from Wikidata descriptions).")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--meta", action="store_true")
    ap.add_argument("--images", action="store_true")
    ap.add_argument("--bios", action="store_true")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()
    if not any([args.meta, args.images, args.bios, args.all]):
        ap.print_help()
        sys.exit(1)
    if args.meta or args.all:
        fetch_meta()
    if args.images or args.all:
        fetch_images()
    if args.bios or args.all:
        fetch_bios()


if __name__ == "__main__":
    main()
