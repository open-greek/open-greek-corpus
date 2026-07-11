#!/usr/bin/env python3
"""
Fetch per-work COVER images (the source scan's title page) for the OCR works
of the Open Greek Corpus, for the reader's work landing + work panel.

Real images only: each cover is the title page of the very archive.org scan
we OCR'd, located through the re-OCR provenance. Works whose scan cannot be
resolved, or whose scan is not clearly public domain, get NO cover (the
reader renders nothing, never a placeholder).

Committed deliverables (small, plain git objects - no LFS):
  data/media/work_covers/<work_urn>.jpg   title-page covers (<=600px longest side)
  data/work_covers.json                    urn -> {file, credit, license, source,
                                                   source_url, archive_id, edition,
                                                   publisher, year, retrieved}

Works from the same edition share one scan, so their cover bytes are
identical (git stores the blob once); the manifest still records provenance
per work.

Scan sourcing (mirrors the importer's edition naming):
  - Qwen3.6 re-OCR editions are named "qwen36-<base>", and
    data/inventory/reocr_provenance.json maps each <base> to its archive.org
    source PDF (-> the item identifier).
  - A few other OCR editions have a direct archive.org item URL in
    data/inventory/ocr_edition_sources.json.
Archive.org exposes the title page directly at
  https://archive.org/download/<id>/page/title_w600.jpg
(with services/img as a fallback), and its copyright status via
  https://archive.org/metadata/<id>.

Usage:
  python3 scripts/fetch_work_covers.py            # fetch + write manifest
  python3 scripts/fetch_work_covers.py --dry-run  # resolve + report coverage only
"""

import argparse
import datetime
import io
import json
import os
import re
import sys
import time

import requests
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
INV = os.path.join(DATA, "inventory")
MEDIA_DIR = os.path.join(DATA, "media", "work_covers")
MANIFEST = os.path.join(DATA, "work_covers.json")

UA = "OpenGreekCorpus-covers/1.0 (https://opengreek.org; cisco.riordan@gmail.com)"
THUMB_MAX = 600
JPEG_QUALITY = 82

SESSION = requests.Session()
SESSION.headers["User-Agent"] = UA

# Archive.org copyright statuses we treat as reusable; a pre-1929 scan with
# no explicit status is also accepted (clearly PD by age), everything else
# is skipped.
PD_STATUS = {"NOT_IN_COPYRIGHT", "PUBLIC_DOMAIN", "PUBLIC_DOMAIN_US", "CC0"}


def today():
    return datetime.date.today().isoformat()


def load(name, base=DATA):
    with open(os.path.join(base, name)) as fh:
        return json.load(fh)


def archive_id(url):
    m = re.search(r"/(?:download|details)/([^/]+)", url or "")
    return m.group(1) if m else None


def resolve_targets():
    """work_urn -> {archive_id, source_url, label, edition, route}."""
    ocr = load("ocr_works.json")
    reocr = load("reocr_provenance.json", INV)["editions"]
    srcs = load("ocr_edition_sources.json", INV)

    base2id = {e["base"]: archive_id(e.get("source_url")) for e in reocr}
    es_id = {k: archive_id(v.get("url")) for k, v in srcs.items()}

    targets = {}
    for w in ocr:
        urn, ed = w["urn"], w["edition"]
        aid = label = None
        route = None
        if ed.startswith("qwen36-"):
            base = ed[len("qwen36-"):]
            aid = base2id.get(base)
            label = (srcs.get(ed) or {}).get("label") or base.replace("_", " ")
            route = "reocr"
        if not aid and es_id.get(ed):
            aid = es_id[ed]
            label = (srcs.get(ed) or {}).get("label") or ed
            route = "edition_source"
        if aid:
            targets[urn] = {
                "archive_id": aid,
                "source_url": f"https://archive.org/details/{aid}",
                "label": label,
                "edition": ed,
                "route": route,
            }
    return targets


def get(url, timeout=90):
    for attempt in range(5):
        try:
            r = SESSION.get(url, timeout=timeout)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(3 + attempt * 3)
                continue
            return r
        except Exception:  # noqa: BLE001
            if attempt == 4:
                return None
            time.sleep(2 + attempt * 2)
    return None


def archive_meta(aid):
    r = get(f"https://archive.org/metadata/{aid}", timeout=60)
    if not r or not r.ok:
        return {}
    return r.json().get("metadata", {})


def to_jpeg(img):
    img = img.convert("RGB")
    img.thumbnail((THUMB_MAX, THUMB_MAX), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return buf.getvalue()


def dhash(img, sz=16):
    g = img.convert("L").resize((sz + 1, sz), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for r in range(sz):
        row = px[r * (sz + 1):(r + 1) * (sz + 1)]
        for c in range(sz):
            bits = (bits << 1) | (1 if row[c] < row[c + 1] else 0)
    return bits


def hamming(a, b):
    return bin(a ^ b).count("1")


def fetch_image(url):
    r = get(url)
    if r and r.ok and "image" in r.headers.get("content-type", ""):
        try:
            return Image.open(io.BytesIO(r.content))
        except Exception:  # noqa: BLE001
            return None
    return None


# Google-digitized scans (identifiers ending "goog") open with a standard
# "This is a digital copy ... Google Book Search" notice leaf at n0; on some
# items archive.org's title/cover/thumbnail all resolve to that notice
# instead of the real title page. It is not a genuine cover, so we detect it
# (the candidate is ~identical to the book's own n0) and skip - no cover -
# rather than show the boilerplate.
NOTICE_MAX = 28


def is_google_notice(img, aid):
    if not aid.endswith("goog"):
        return False
    n0 = fetch_image(f"https://archive.org/download/{aid}/page/n0_w{THUMB_MAX}.jpg")
    if n0 is None:
        return False
    return hamming(dhash(img), dhash(n0)) <= NOTICE_MAX


def fetch_cover(aid):
    """The scan's title page as JPEG bytes; services/img as a last resort.
    Returns (jpeg, None) on success or (None, reason) when skipped."""
    for u in (
        f"https://archive.org/download/{aid}/page/title_w{THUMB_MAX}.jpg",
        f"https://archive.org/download/{aid}/page/cover_w{THUMB_MAX}.jpg",
        f"https://archive.org/services/img/{aid}",
    ):
        img = fetch_image(u)
        if img is None:
            continue
        if is_google_notice(img, aid):
            return None, "google notice page (no real title page)"
        return to_jpeg(img), None
    return None, "cover fetch failed"


def pd_ok(meta):
    status = (meta.get("possible-copyright-status") or "").upper()
    if status in PD_STATUS:
        return True, status
    if status:  # an explicit non-PD status -> skip
        return False, status
    # no status: accept only clearly-old scans (pre-1929).
    year = str(meta.get("year") or meta.get("date") or "")
    m = re.search(r"\b(1[5-9]\d\d)\b", year)
    if m and int(m.group(1)) < 1929:
        return True, f"pre-1929 ({m.group(1)})"
    return False, status or "unknown"


def credit_for(meta, label):
    bits = []
    pub = meta.get("publisher")
    year = meta.get("year") or meta.get("date")
    if pub:
        bits.append(re.sub(r"\s+", " ", str(pub)).strip())
    if year:
        bits.append(str(year))
    digitizer = meta.get("sponsor")
    holder = meta.get("contributor")
    tail = []
    if digitizer:
        tail.append(f"digitized by {digitizer}")
    if holder:
        tail.append(f"from {holder}")
    credit = ", ".join(bits)
    if tail:
        credit = (credit + "; " if credit else "") + " ".join(tail)
    return credit or label


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    targets = resolve_targets()
    by_id = {}
    for urn, t in targets.items():
        by_id.setdefault(t["archive_id"], []).append((urn, t))
    print(f"{len(targets)} OCR works resolve to {len(by_id)} distinct archive.org scans.")
    if args.dry_run:
        routes = {}
        for t in targets.values():
            routes[t["route"]] = routes.get(t["route"], 0) + 1
        print("by route:", routes)
        return

    os.makedirs(MEDIA_DIR, exist_ok=True)
    manifest = {}
    skipped = {}
    done_scans = 0
    for aid, items in sorted(by_id.items()):
        meta = archive_meta(aid)
        ok, status = pd_ok(meta)
        if not ok:
            skipped[aid] = f"copyright={status}"
            continue
        jpeg, reason = fetch_cover(aid)
        if not jpeg:
            skipped[aid] = reason
            continue
        credit = credit_for(meta, items[0][1]["label"])
        done_scans += 1
        for urn, t in items:
            path = os.path.join(MEDIA_DIR, f"{urn}.jpg")
            with open(path, "wb") as fh:
                fh.write(jpeg)
            manifest[urn] = {
                "file": f"media/work_covers/{urn}.jpg",
                "credit": credit,
                "license": "Public domain",
                "license_status": status,
                "source": "archive.org",
                "source_url": t["source_url"],
                "archive_id": aid,
                "edition": t["edition"],
                "publisher": (re.sub(r"\s+", " ", str(meta.get("publisher"))).strip()
                              if meta.get("publisher") else None),
                "year": str(meta.get("year") or meta.get("date") or "") or None,
                "retrieved": today(),
            }
        print(f"  {aid}: {len(items)} work(s) [{status}] ({len(jpeg)//1024} KB)")
        time.sleep(0.3)

    with open(MANIFEST, "w") as fh:
        json.dump(dict(sorted(manifest.items())), fh, ensure_ascii=False, indent=1)
    print(f"\nWrote {len(manifest)} work covers from {done_scans} scans -> {MANIFEST}")
    if skipped:
        print(f"Skipped {len(skipped)} scans:")
        for aid, why in sorted(skipped.items()):
            print(f"  {aid}: {why}")


if __name__ == "__main__":
    main()
