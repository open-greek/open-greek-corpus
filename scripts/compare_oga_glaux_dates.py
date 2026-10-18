#!/usr/bin/env python3
"""Join Bilby's pinned OGA/GLAUx date pretransforms to the current source dates.

This is a comparison, never an instruction to overwrite dates or merge works.
All CSV rows survive, including repeated CTS keys. Bilby derives from OGA and
GLAUx and is not an independent third dating witness. Run --fetch once to
retrieve the checksum-pinned metadata; --check verifies committed output.
"""
from __future__ import annotations

import argparse
import calendar
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request

from export_glaux_annotations import UPSTREAM_COMMIT as GLAUX_COMMIT

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = Path("data/reference/bilby-oga-glaux-2024")
OUT = Path("data/oga_glaux_date_comparison.json")
MANIFEST = REFERENCE / "manifest.json"
API = "https://zenodo.org/api/records/14254073"
DOI = "10.5281/zenodo.14254073"
TITLE = "OGA v0.2.0 (2024-11-24) and GLAUx v1.0 (2024-04-09) Compared"
GLAUX_URL = f"https://raw.githubusercontent.com/alekkeersmaekers/glaux/{GLAUX_COMMIT}/metadata.txt"
FILES = {
    "oga_unique.csv": {"bytes": 68757, "md5": "90806197c039c9149fc37e01e7dff459",
                       "sha256": "004cfdb1363ff4e4209452437de30eeae3253db927c1f98a8dcc470970997eb4"},
    "glaux_unique.csv": {"bytes": 19060, "md5": "96e235ea720ced2eaaf1e1863490f5b6",
                         "sha256": "f71e707c41a3c05133a1f17491fdd2a43b467c570fc354884c7eb971cffdf38f"},
    "glaux_oga_matches.csv": {"bytes": 99189, "md5": "3fb090e76a76599914a19530034d8af1",
                              "sha256": "974c5394c019588ab078695e998faacdfe66ed0e5c85388c8c108379f26af995"},
    "glaux-metadata.txt": {"bytes": 200187,
                           "sha256": "40ed4a63fb57520ce6bc11823cf805472017495c1e3ad933174bc0291be7345b"}}
_ENDPOINT = re.compile(r"^([+\-—–−]?)(\d{4,})(?:-(\d{2})(?:-(\d{2}))?)?$")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def verify_source(name, raw):
    expected = FILES[name]
    if len(raw) != expected["bytes"] or digest(raw) != expected["sha256"]:
        raise ValueError(f"Pinned source checksum changed: {name}")
    if "md5" in expected and hashlib.md5(raw).hexdigest() != expected["md5"]:
        raise ValueError(f"Zenodo checksum changed: {name}")


def fetch_sources(root=ROOT):
    record = json.load(urllib.request.urlopen(API))
    metadata = record["metadata"]
    if (record["doi"] != DOI or metadata["title"] != TITLE or metadata["version"] != "0.1"
            or metadata["license"]["id"] != "cc-by-sa-4.0"
            or metadata["creators"][0]["name"] != "Bilby, Mark G."):
        raise ValueError("Zenodo identity, version, attribution, or license changed")
    files = {f["key"]: f for f in record["files"]}
    if set(files) != set(FILES) - {"glaux-metadata.txt"}:
        raise ValueError("Zenodo file inventory changed")
    outputs = {}
    for name, expected in FILES.items():
        if name == "glaux-metadata.txt":
            url = GLAUX_URL
        else:
            item = files[name]
            if item["checksum"] != "md5:" + expected["md5"] or item["size"] != expected["bytes"]:
                raise ValueError(f"Zenodo file pin changed: {name}")
            url = item["links"]["self"]
        raw = urllib.request.urlopen(url).read()
        verify_source(name, raw)
        outputs[name] = raw
    destination = root / REFERENCE
    destination.mkdir(parents=True, exist_ok=True)
    for name, raw in outputs.items():
        (destination / name).write_bytes(raw)


def historical_label(year):
    """Convert astronomical numbering to an era label: year zero is 1 BCE."""
    return f"{year} CE" if year > 0 else f"{1 - year} BCE"


def endpoint(value, *, convention, upper=False):
    match = _ENDPOINT.fullmatch(value.strip())
    if not match:
        raise ValueError("unsupported endpoint syntax")
    sign, digits, month, day = match.groups()
    year = int(digits)
    if sign in ("-", "—", "–", "−"):
        if year == 0:
            raise ValueError("negative zero is not a supported year spelling")
        year = -year
    if convention == "historical":
        if year == 0:
            raise ValueError("historical numbering has no year zero")
        year += year < 0
    elif convention != "astronomical":
        raise ValueError("unknown year-numbering convention")
    month_number = int(month) if month else (12 if upper else 1)
    if not 1 <= month_number <= 12:
        raise ValueError("invalid month")
    last_day = calendar.monthrange(year, month_number)[1]
    day_number = int(day) if day else (last_day if upper else 1)
    if not 1 <= day_number <= last_day:
        raise ValueError("invalid day")
    return {"year": year, "month": month_number, "day": day_number,
            "era_label": historical_label(year),
            "precision": "day" if day else "month" if month else "year"}


def interval_key(interval):
    return tuple(interval[side][field] for side in ("start", "end") for field in ("year", "month", "day"))


def normalize_intervals(raw, *, convention="astronomical"):
    """Retain explicit alternatives; never collapse several intervals to a midpoint.

    Semicolons and || delimit explicitly separate alternatives. More than one
    slash within an alternative is ambiguous, not an invitation to guess.
    ``unspecified`` retains both astronomical and historical interpretations.
    """
    values = raw if isinstance(raw, list) else re.split(r"\s*(?:;|\|\|)\s*", raw or "")
    values = [value.strip() for value in values if value.strip()]
    if not values:
        return {"status": "missing", "intervals": [], "issues": []}
    if convention not in ("astronomical", "historical", "unspecified"):
        raise ValueError("unknown year-numbering convention")
    intervals, issues = [], []
    for value in values:
        parts = value.split("/")
        if len(parts) > 2 or any(not part.strip() for part in parts):
            issues.append({"raw": value, "reason": "ambiguous or open interval"})
            continue
        conventions = ["astronomical", "historical"] if convention == "unspecified" else [convention]
        for interpretation in conventions:
            try:
                start = endpoint(parts[0], convention=interpretation)
                end = endpoint(parts[-1], convention=interpretation, upper=True)
                interval = {"start": start, "end": end, "interpretation": interpretation}
                if interval_key(interval)[:3] > interval_key(interval)[3:]:
                    raise ValueError("reversed interval")
                intervals.append(interval)
            except ValueError as error:
                issues.append({"raw": value, "interpretation": interpretation, "reason": str(error)})
    distinct = {interval_key(i) for i in intervals}
    status = ("unresolved" if not intervals else "ambiguous" if issues or
              (convention == "unspecified" and len(distinct) > 1) else "multiple" if len(distinct) > 1 else "valid")
    return {"status": status, "intervals": intervals, "issues": issues,
            "year_numbering": convention,
            "calendar": "proleptic Gregorian; normalized endpoint years use astronomical numbering"}


def cts_key(value):
    """Remove only a full CTS namespace; retain the work's exact letter suffix."""
    value = value.strip()
    if value.startswith("urn:cts:"):
        pieces = value.split(":")
        if len(pieces) != 4:
            raise ValueError("Expected a work-level CTS identifier")
        return pieces[-1]
    return value


def glaux_cts(value):
    match = re.fullmatch(r"(\d{4})-(\d{3})([a-z]?)", value)
    if not match:
        raise ValueError(f"Unmapped GLAUx work identifier: {value}")
    author, work, suffix = match.groups()
    return f"tlg{author}.tlg{work}{suffix}"


def exact_registry_matches(root):
    matches = defaultdict(set)
    registry = json.loads((root / "data/source_registry.json").read_text())["works"]
    crosswalk = json.loads((root / "data/tlg_crosswalk.json").read_text())
    for slug, work in registry.items():
        cts = work.get("aliases", {}).get("cts")
        if cts:
            matches[cts_key(cts)].add(slug)
    for slug, work in crosswalk.items():
        if work.get("cts"):
            matches[cts_key(work["cts"])].add(slug)
    return matches


def read_bilby(reference):
    rows = []
    for name in sorted(set(FILES) - {"glaux-metadata.txt"}):
        raw = (reference / name).read_bytes()
        verify_source(name, raw)
        parsed = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        expected = {"row_number", "formatted_work_date", "cts_urn", "author", "title"}
        if name != "oga_unique.csv":
            expected.add("glaux_text_id")
        if not parsed or set(parsed[0]) != expected:
            raise ValueError("Bilby CSV fields changed")
        seen = set()
        for index, row in enumerate(parsed, 1):
            if row["row_number"] != str(index) or index in seen:
                raise ValueError("CSV row-number identity changed")
            seen.add(index)
            family = ["oga", "glaux"] if name == "glaux_oga_matches.csv" else ["oga" if name == "oga_unique.csv" else "glaux"]
            rows.append({"id": f"bilby:{name}:{index}", "cts": cts_key(row["cts_urn"]),
                         "source": "bilby-0.1", "source_families": family,
                         "source_file": name, "source_row": index, "raw": row,
                         "date": normalize_intervals(row["formatted_work_date"]),
                         "date_attribution": "The matched file exposes one date field and does not distinguish OGA and GLAUx date readings." if len(family) == 2 else "Derived pretransform of " + family[0]})
    return rows


def read_glaux(reference):
    raw = (reference / "glaux-metadata.txt").read_bytes()
    verify_source("glaux-metadata.txt", raw)
    rows = list(csv.DictReader(io.StringIO(raw.decode()), delimiter="\t"))
    fields = ("GLAUX_TEXT_ID", "TLG", "STARTDATE", "ENDDATE", "AUTHOR_STANDARD", "TITLE_STANDARD")
    output = []
    for index, row in enumerate(rows, 1):
        if not all(field in row for field in fields):
            raise ValueError("GLAUx date metadata fields changed")
        dates = []
        for field in ("STARTDATE", "ENDDATE"):
            value = row[field]
            if not re.fullmatch(r"[+-]?\d+", value):
                raise ValueError("Unexpected GLAUx signed-year field")
            numeric = int(value)
            dates.append(("-" if numeric < 0 else "+") + f"{abs(numeric):04d}")
        output.append({"id": f"glaux:{row['GLAUX_TEXT_ID']}", "cts": glaux_cts(row["TLG"]),
                       "source": "glaux-" + GLAUX_COMMIT, "source_families": ["glaux"],
                       "source_row": index, "raw": {field: row[field] for field in fields},
                       "date": normalize_intervals("/".join(dates), convention="unspecified"),
                       "date_attribution": "Signed STARTDATE/ENDDATE are retained. This metadata file does not declare year-zero conventions, so historical and astronomical negative-year interpretations remain available."})
    return output


def compare_readings(readings):
    """Expose disagreement without preferring a source or counting dependent votes."""
    candidates = {}
    for reading in readings:
        for interval in reading["date"]["intervals"]:
            key = interval_key(interval)
            if key not in candidates:
                candidates[key] = {"start": interval["start"], "end": interval["end"], "readings": []}
            candidates[key]["readings"].append({"id": reading["id"], "interpretation": interval["interpretation"]})
    pairwise = []
    for bilby in (r for r in readings if r["source"] == "bilby-0.1"):
        left = {interval_key(i) for i in bilby["date"]["intervals"]}
        for source in (r for r in readings if r["source"] != "bilby-0.1"):
            options = source["date"]["intervals"]
            matching = [i["interpretation"] for i in options if interval_key(i) in left]
            relation = "unresolved" if not left or not options else "equal" if all(interval_key(i) in left for i in options) else "convention-dependent" if matching else "different"
            pairwise.append({"bilby": bilby["id"], "source": source["id"], "relation": relation,
                             "matching_interpretations": matching})
    return {"available_intervals": [candidates[key] for key in sorted(candidates)],
            "bilby_source_comparisons": pairwise,
            "selection": None, "independent_third_vote": False}


def generate(root=ROOT):
    reference = root / REFERENCE
    all_readings = read_bilby(reference) + read_glaux(reference)
    oga_path = root / "data/oga_dating.json"
    oga = json.loads(oga_path.read_text())
    for cts, values in oga["works"].items():
        all_readings.append({"id": "oga:" + cts_key(cts), "cts": cts_key(cts),
                             "source": "oga-v0.2.0", "source_families": ["oga"], "raw": values,
                             "date": normalize_intervals(values["formatted_work_date"]),
                             "date_attribution": "OGA's own formatted field declares ISO 8601; its estimated date, labels, temporary flag, and bibliography remain in raw."})
    works = defaultdict(list)
    for reading in all_readings:
        works[reading["cts"]].append(reading)
    matches = exact_registry_matches(root)
    result = {cts: {"corpus_work_candidates": sorted(matches.get(cts, [])),
                    "readings": sorted(readings, key=lambda r: r["id"]),
                    "comparison": compare_readings(sorted(readings, key=lambda r: r["id"]))}
              for cts, readings in sorted(works.items())}
    relations = Counter(p["relation"] for work in result.values() for p in work["comparison"]["bilby_source_comparisons"])
    by_source = defaultdict(Counter)
    for work in result.values():
        for comparison in work["comparison"]["bilby_source_comparisons"]:
            by_source[comparison["source"].split(":", 1)[0]][comparison["relation"]] += 1
    by_file = Counter(r["source_file"] for r in all_readings if r["source"] == "bilby-0.1")
    counts = {"exact_cts_keys": len(result), "bilby_rows": sum(by_file.values()),
              "bilby_rows_by_file": dict(sorted(by_file.items())),
              "oga_readings": len(oga["works"]), "glaux_readings": sum(r["source"].startswith("glaux-") for r in all_readings),
              "works_with_multiple_available_intervals": sum(len(w["comparison"]["available_intervals"]) > 1 for w in result.values()),
              "bilby_source_comparisons": dict(sorted(relations.items())),
              "bilby_source_comparisons_by_source": {source: dict(sorted(counts.items())) for source, counts in sorted(by_source.items())}}
    manifest = {"schema_version": 1, "title": TITLE, "version": "0.1", "version_doi": DOI,
                "creator": "Mark G. Bilby", "creator_orcid": "0000-0003-0100-6634",
                "publication_date": "2024-12-01", "license": "CC-BY-SA-4.0",
                "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
                "citation": f"Bilby, Mark G. (2024). {TITLE} (0.1). Zenodo. https://doi.org/{DOI}",
                "upstream_corpora": {"oga": "10.5281/zenodo.14206061", "glaux": "10.5281/zenodo.10948375"},
                "derivation": "The three CSVs derive from OGA and GLAUx metadata. They are a finding aid and normalized comparison, not an independent third dating source. Matched rows contain one date field, not separate OGA and GLAUx dates.",
                "files": {name: {**expected, "url": GLAUX_URL if name == "glaux-metadata.txt" else f"{API}/files/{name}/content"} for name, expected in sorted(FILES.items())},
                "current_source_inputs": {"oga": {"path": "data/oga_dating.json", "sha256": digest(oga_path.read_bytes()),
                                                   "version_doi": oga["_meta"]["version_doi"]},
                                          "glaux": {"commit": GLAUX_COMMIT, "path": (REFERENCE / "glaux-metadata.txt").as_posix()}},
                "identity_inputs": {path: digest((root / path).read_bytes()) for path in ("data/source_registry.json", "data/tlg_crosswalk.json")},
                "output": OUT.as_posix(), "counts": counts, "generated_by": "scripts/compare_oga_glaux_dates.py"}
    output = {"schema_version": 1, "provenance": manifest,
              "normalization_policy": "Raw values and all repeated CTS rows are retained. Signed ISO-style fields use astronomical years, where year zero is 1 BCE. GLAUx's unspecified signed-year convention retains both astronomical and historical interpretations; none is selected. Multiple or ambiguous intervals are never collapsed to a midpoint. Exact CTS work suffixes remain distinct. No dates, century tags, identities, or text are overwritten.",
              "works": result}
    return {MANIFEST: encode(manifest), OUT: encode(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.fetch:
        fetch_sources()
    artifacts = generate()
    if args.check:
        drift = [str(path) for path, raw in artifacts.items() if not (ROOT / path).exists() or (ROOT / path).read_bytes() != raw]
        if drift:
            parser.exit(1, "Date comparison drift: " + ", ".join(drift) + "\n")
    else:
        for path, raw in artifacts.items():
            (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / path).write_bytes(raw)
    print(json.dumps(json.loads(artifacts[MANIFEST])["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
