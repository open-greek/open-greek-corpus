"""Load reviewed scan additions without losing them on a TEI rebuild."""
import hashlib
import json
from pathlib import Path
from collections import Counter


def reading_digest(rows):
    selected = [{key: row.get(key) for key in ("locus", "text", "source", "edition")}
                for row in rows]
    return hashlib.sha256(json.dumps(selected, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def combine_rows(work, base, extensions):
    """Keep each old book's order while inserting newly supplied books before it."""
    def key(pair):
        position, row = pair
        if work == "cassius-dio.historiae-romanae":
            if row["locus"].startswith("cary-v"):
                volume = int(row["locus"].split("-")[1][1:])
                return (0 if volume < 3 else 2, volume, row["printed_page"], position)
            return (1, 0, 0, position)
        book = int(row["locus"].split(".")[0])
        return (book, 0, row.get("printed_page", 0), position)
    return [row for position, row in sorted(enumerate(base + extensions), key=key)]


def load_extensions(root: Path, work: str, existing_loci=(), base_rows=None):
    index = root / "data/corpus_extension_index.json"
    if not index.exists():
        return []
    entry = json.loads(index.read_text()).get("works", {}).get(work)
    if not entry:
        return []
    if entry.get("base_readings_sha256") and (base_rows is None or
            reading_digest(base_rows) != entry["base_readings_sha256"]):
        raise ValueError("The base edition changed; review coverage overlap before rebuilding")
    path = Path(entry["path"])
    if path.is_absolute() or ".." in path.parts or path.parts[:2] != ("data", "corpus_extensions"):
        raise ValueError("Unsafe scan extension path")
    raw = (root / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise ValueError("Scan extension changed outside its reviewed importer")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    loci = set(existing_loci)
    for row in rows:
        if row["urn"] != work or row["locus"] in loci:
            raise ValueError("Scan extension has a wrong work or repeated citation")
        loci.add(row["locus"])
    return rows


def coverage_scope(root: Path, work: str):
    """Describe the served manifestation without shrinking the Work identity.

    Planned scan pages never count as admitted. Callers can attach this block to
    both the public Work index and the source registry's manifestation metadata.
    The exact OCR word networks and the comparison panels remain separate data.
    """
    directory = root / "data/ingest_reviews/coverage"
    qualifications = {
        "pappus-mathematics.synagoge": {
            "work_identity": "Pappus, Synagoge (Collection)",
            "base_scope": "Hultsch volume I, surviving Greek material of Books II–V",
            "addition_scope": "Hultsch volumes II–III, Books VI–VIII, including the Heron quotation at the end of Book VIII",
            "transmission_limit": "Book I is lost and only the latter part of Book II survives. Hultsch edits the surviving remains of Books II–VIII; the selected Greek body does not reconstruct those losses or claim an intact eight-book text.",
            "transmission_reference": {"citation": "The manuscript tradition of the Collectio Mathematica, Scriptorium 11.2 (1957), opening description of the extant text", "url": "https://www.persee.fr/doc/scrip_0036-9772_1957_num_11_2_2937"},
            "excluded_material": "Facing Latin translation, diagrams and their labels, critical apparatus, later anonymous supplements, scholia and indexes",
            "historical_citation_scheme": "pappus-first1k-book-attributes",
            "scan_citation_scheme": "Book plus Hultsch printed page",
            "manifest": "mathematical-ocr-jobs.json",
        },
        "apollonius-geom.conica": {
            "work_identity": "Apollonius of Perga, Conica",
            "base_scope": "Heiberg volume II, Greek Book IV",
            "addition_scope": "Heiberg volume I, Greek Books I–III, including epistolary prefaces",
            "transmission_limit": "The Greek manifestation covers Books I–IV. Books V–VII survive only in Arabic translation, and Book VIII is lost; none is reconstructed as Greek reading text.",
            "transmission_reference": {"citation": "Cambridge Library Collection description of Heiberg's Apollonii Pergaei quae Graece exstant cum commentariis antiquis, volume II", "url": "https://www.cambridge.org/core/books/apollonii-pergaei-quae-graece-exstant-cum-commentariis-antiquis/5D8CEEC494A099E165426D0D05022E27"},
            "excluded_material": "Facing Latin translation, diagrams and their labels, critical apparatus and indexes",
            "historical_citation_scheme": "apollonius-first1k-unqualified-sections",
            "scan_citation_scheme": "Book plus Heiberg printed page",
            "manifest": "mathematical-ocr-jobs.json",
        },
        "cassius-dio.historiae-romanae": {
            "work_identity": "Cassius Dio, Historiae Romanae (Roman History), the ancient eighty-book work",
            "base_scope": "Perseus Cary volumes III–VI, encoded Books 36–55, ending mid-sentence at 55.9.4",
            "addition_scope": "Cary volumes I–II fragments and volumes VI–IX remaining Greek direct text, excerpts and epitomes",
            "transmission_limit": "This is mixed ancient transmission, not an intact eighty-book direct text. Fragment quotations, direct text, excerpted lacunae and epitomes retain distinct transmission labels. The ancient direct-text gap after the last words at 55.9.4 is not repaired as newly surviving direct text. Early fragments of uncertain reference remain unassigned to a book.",
            "direct_text_lacuna_evidence": "Cary volume VI, printed page 402 (PDF 206), footnote 4: two folios are lost in M between τρόπον at 55.9.4 and (Ἄ)ρει at 55.10.2; the printed continuation combines Zonaras, Xiphilinus and Excerpta Valesiana. This qualification applies to that gap, not all later direct text.",
            "excluded_material": "English translation, critical apparatus and indexes; comparative quotations from Zonaras and other authors are retained as separate paratext rather than counted as direct Dio text",
            "scan_citation_scheme": "Cary volume plus printed page and fragment/comparison panel when needed; conflicting display and marginal book numbers are retained as source references without a blanket offset",
            "manifest": "cassius-dio-ocr-jobs.json",
        },
    }
    if work not in qualifications:
        return None
    description = dict(qualifications[work])
    filename = description.pop("manifest")
    manifest_path = directory / filename
    if not manifest_path.exists():
        return None
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    selected = [page for page in manifest["pages"] if page["work"] == work]
    primary = [page for page in selected if page.get("admission") != "comparative-paratext"]
    expected = {page["id"] for page in primary}
    index_path = root / "data/corpus_extension_index.json"
    entry = json.loads(index_path.read_text()).get("works", {}).get(work) if index_path.exists() else None
    rows = []
    if entry:
        extension = root / entry["path"]
        data = extension.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Scan extension changed outside its reviewed importer")
        rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    admitted = {row.get("scan_region_id") for row in rows}
    if admitted - expected:
        raise ValueError("Coverage metadata found a scan region outside its reviewed manifestation")
    sources = sorted({page["source"] for page in selected})
    return {**description,
        "status": "reviewed-primary-regions-admitted" if admitted == expected else "reviewed-scan-additions-pending",
        "reviewed_primary_regions": len(expected), "admitted_primary_regions": len(admitted),
        "remaining_reviewed_primary_regions": len(expected - admitted),
        "reviewed_comparative_regions": len(selected) - len(primary),
        "admitted_transmission_counts": dict(sorted(Counter(row["transmission"] for row in rows).items())),
        "scan_manifest": str(manifest_path.relative_to(root)),
        "scan_manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "scan_sources": [{"id": source, **manifest["sources"][source]} for source in sources],
        "admission_audit": entry.get("audit") if entry else None,
        "digital_components": entry.get("digital_components", []) if entry else [],
        "frequency_policy": "Resolved Greek word votes only; all unresolved and mixed-script readings remain visible with original witnesses in the audit"}
