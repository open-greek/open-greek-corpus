"""Load pinned Source Library Cary VII–IX Greek page witnesses and rights."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

LICENSE = "CC-BY-SA-4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"
BASE_URL = "https://gitlab.lisn.upsaclay.fr/api/v4/projects/1918/packages/generic/corpus/1/works/tlg0385/tlg001/"
API_NOTICE = {"spdx": LICENSE, "url": LICENSE_URL,
    "attribution": "Source Library (https://sourcelibrary.org)",
    "terms": "https://sourcelibrary.org/terms", "original_texts": "public-domain",
    "tdm_reservation": 1, "tdm_policy": "https://sourcelibrary.org/licensing",
    "ai_training": "reserved — standard license available, see tdm_policy"}
PINS = {
    "tlg0385.tlg001.local003": {"volume": 7, "book": "6a089bbe2b703903f58e7814",
        "json_sha256": "a44808f87dd70e7f7c6bdf57284b4d9deb249b7b45579320b32db9455d83c216",
        "book_metadata_receipt_sha256": "6e873c915630ca1dad96b270ef49b0023b4225f1959b2c966387f1ca5abc81e5",
        "api_quote_receipt_sha256": "e606d24c2b9611a2ef381f73dff526ae05fc43e219cc4e8e3bda15cf249da2ff"},
    "tlg0385.tlg001.local004": {"volume": 8, "book": "6a089bc42b703903f58e7908",
        "json_sha256": "10ff6a03a62adec5ec9b2a78a564b5c649978226bd5df9acaf01ed609a31906c",
        "book_metadata_receipt_sha256": "038a6b13694d59f6ac9c765ebd71c32f4b0f1fbad3af5a5f05948d6c2ae868cd",
        "api_quote_receipt_sha256": "51b29d1320cfa781a720ee7f213ccf84229cbe8afbd7d6a5fc872494691eab1d"},
    "tlg0385.tlg001.local005": {"volume": 9, "book": "6a089bcb2b703903f58e7a0c",
        "json_sha256": "6acf54dde2b3df539384d3cfad8925d3e0657d299cf64cfb05e57fbec998da67",
        "book_metadata_receipt_sha256": "83ab3e1549ac9d14bb49d6f310e3ff8d77b56be2f5e49981d7c370d55455a2ee",
        "api_quote_receipt_sha256": "e50616d86262e8ed128223c9d8a14ad183f269b4cf84de623ca963a52d1d1e90"},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(paths=(), blobs=None):
    """Return exact original files, licensed component metadata and page texts."""
    inputs = blobs if blobs is not None else [Path(path).read_bytes() for path in paths]
    sources, pages, originals = {}, {}, {}
    for compressed in inputs:
        raw = gzip.decompress(compressed) if compressed.startswith(b"\x1f\x8b") else compressed
        document = json.loads(raw)
        identifier = document["id"]
        if identifier not in PINS or identifier in sources or sha(raw) != PINS[identifier]["json_sha256"]:
            raise ValueError("Unreviewed, repeated or changed Dio digital comparison source")
        pin = PINS[identifier]
        if (document["origin"]["id"] != "source-library" or document["license"]["url"] != LICENSE_URL or
                pin["book"] not in document["sourceCitation"]):
            raise ValueError("Dio comparison identity or license changed")
        metadata = {"id": identifier, "volume": pin["volume"], "json_sha256": sha(raw),
            "url": BASE_URL + identifier.split(".")[-1] + ".json.gz",
            "license": LICENSE, "license_url": LICENSE_URL,
            "attribution": API_NOTICE["attribution"], "source_citation": document["sourceCitation"],
            "source_rights": document["sourceRights"], "upstream_license": document["license"],
            "source_revision_date": document["revisionDate"],
            "api_notice_url": f"https://sourcelibrary.org/api/books/{pin['book']}/quote?page=6",
            "book_metadata_url": f"https://sourcelibrary.org/api/books/{pin['book']}",
            "api_notice_checked_date": "2026-10-18", "separate_api_notice": API_NOTICE,
            "rights_receipts": {key: value for key, value in pin.items() if key.endswith("receipt_sha256")},
            "same_scan_evidence": {"internet_archive_identifier": f"dios-roman-history.-vol.-{pin['volume']}-loeb-{175 if pin['volume'] == 7 else 176 if pin['volume'] == 8 else 177}",
                "api_image_source_license": "http://creativecommons.org/publicdomain/mark/1.0/",
                "review": "Source Library book metadata names the same Internet Archive item as the hash-pinned Cary scan. Greek Library Page sN is that item's physical PDF page N; the body-window anchors independently confirm page identity."},
            "rights_review": "The selected Greek is from the original Cary edition (1924, 1925 or 1927), verified on each scan's impression page. Volume IX's export retains an earlier rights warning based on its 1969 reprint date; the original 1927 Greek print and the current API public-domain image-source statement are separately retained, without deleting that warning."}
        sources[identifier], originals[identifier] = metadata, raw
        for section in document["sections"]:
            match = re.fullmatch(r"Page s(\d+)", section["label"])
            if not match or section.get("children") or any(block["type"] != "paragraph" for block in section["blocks"]):
                raise ValueError("Unreviewed Dio digital comparison page structure")
            page = int(match[1])
            key = (pin["volume"], page)
            if key in pages:
                raise ValueError("Repeated Dio digital comparison physical page")
            text = "\n".join(block["text"] for block in section["blocks"])
            pages[key] = {"id": identifier + ":" + section["id"], "vote_group": "source-library",
                "text": text, "artifact_sha256": sha(json.dumps(section, ensure_ascii=False, sort_keys=True).encode()),
                "source_file_sha256": sha(raw), "source_id": identifier,
                "source_section": section["id"], "source_url": metadata["url"],
                "license": LICENSE, "attribution": metadata["attribution"]}
    return {"sources": sources, "pages": pages, "originals": originals}


def download(directory):
    directory = Path(directory)
    fetched = []
    for identifier in sorted(PINS):
        url = BASE_URL + identifier.split(".")[-1] + ".json.gz"
        raw = urlopen(url, timeout=120).read()
        source = load(blobs=[raw])
        if set(source["sources"]) != {identifier}:
            raise ValueError("Digital comparison download returned another source identity")
        fetched.append((identifier, raw))
    directory.mkdir(parents=True, exist_ok=True)
    for identifier, raw in fetched:
        (directory / (identifier + ".json.gz")).write_bytes(raw)
    return [directory / (identifier + ".json.gz") for identifier, raw in fetched]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", type=Path, required=True)
    args = parser.parse_args()
    for path in download(args.download):
        print(path)
