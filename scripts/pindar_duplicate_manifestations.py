"""Register the four served First1K Pindar units from their checked TEI headers.

The existing collective catalog author is an attribution label. Neither that
label nor Pindar's date establishes when these biographies were composed.
"""
from __future__ import annotations

from copy import deepcopy
import gzip
from pathlib import Path
import xml.etree.ElementTree as ET

import repair_pindar_duplicate_primaries as repair

ROOT = Path(__file__).resolve().parents[1]
AUTHOR = "vitae-pindari-et-varia-de-pindaro"
NS = {"t": "http://www.tei-c.org/ns/1.0"}
ATTRIBUTION = (
    "The First1K collective catalog attribution is retained. The biography "
    "subject and collective author label do not establish the composition "
    "date or individual authorship of these separate units."
)


def _text(element):
    return " ".join("".join(element.itertext()).split()) if element is not None else ""


def identity_metadata(root=ROOT):
    root = Path(root)
    if not repair.active(root):
        return {}
    audit, before = repair.verify(root)
    result = {}
    for pair in repair.PAIRS:
        raw = before[repair.source_path(pair)]
        archived = root / repair.AUDIT / "sources" / (pair["old"] + ".xml.gz")
        if gzip.decompress(archived.read_bytes()) != raw:
            raise ValueError("Pindar archived TEI header differs from its pinned input")
        tree = ET.fromstring(raw)
        statement = tree.find("t:teiHeader/t:fileDesc/t:titleStmt", NS)
        title = _text(statement.find("t:title", NS))
        author_name = _text(statement.find("t:author", NS))
        source = repair.source_metadata(pair)
        edition_urn = source["cts"] + ".1st1K-grc1"
        editions = tree.findall(".//t:div[@type='edition']", NS)
        if (not title or not author_name or not editions
                or any(element.get("n") != edition_urn for element in editions)):
            raise ValueError("Pindar TEI header has no checked title, author label, or edition identity")
        source["title"] = title
        result[pair["canonical"]] = {
            "author": AUTHOR, "author_name": author_name, "title": title,
            "aliases": {"cts": source["cts"]}, "edition": "1st1K-grc1",
            "edition_urn": edition_urn, "source": source,
            "counts": deepcopy(audit["works"][pair["canonical"]]),
            "canonical_id": pair["canonical_id"], "retired_source": pair["old"],
            "retired_source_id": pair["old_id"],
            "attribution_qualification": ATTRIBUTION,
            "authority": {"path": repair.AUDIT + "/changes.json",
                "sha256": repair.sha((root / repair.AUDIT / "changes.json").read_bytes())}}
    return result


def register_identities(registry, root=ROOT, *, identities=None):
    identities = identity_metadata(root) if identities is None else identities
    for slug, value in identities.items():
        registry.mint_author(value["author_name"], slug=AUTHOR)
        registry.mint_work(AUTHOR, value["title"], slug=slug, aliases=value["aliases"])
        work = registry.works[slug]
        work.author, work.title, work.best_source = AUTHOR, value["title"], "open_corpus"
    return identities


def qualify_oga_date(registry, urn, upstream):
    """Retain collective OGA chronology without dating a separate biography."""
    pair = next((pair for pair in repair.PAIRS if pair["old"] == urn), None)
    if pair is None or pair["canonical"] not in registry.works:
        return None
    work = registry.works[pair["canonical"]]
    review = work.coverage_composition.get("pindar_duplicate_review", {})
    if review.get("manifest") != repair.AUDIT + "/changes.json":
        return None
    reading = {"urn": urn, "slug": pair["canonical"],
        "source": "Opera Graeca Adnotata v0.2.0", "upstream_record": deepcopy(upstream),
        "status": "unverified-unit-composition-date", "applied_to_unit": False,
        "qualification": (
            "The upstream interval is supplied for the collective Pindar "
            "biography catalog and cites an article on Pindar. It is not "
            "independent evidence for this separate unit's composition date; "
            "the same interval also occurs on the explicitly Thomana unit. "
            "Keep the source reading without adding a century or era tag.")}
    review["upstream_date_readings"] = [deepcopy(reading)]
    return reading


def register(registry, root=ROOT):
    root = Path(root)
    identities = register_identities(registry, root)
    if not identities:
        return identities
    audit, _ = repair.verify(root)
    for slug, value in identities.items():
        work = registry.works[slug]
        previous = work.default_edition
        old_default = work.editions.get(previous)
        preserve_default = old_default is not None and old_default.servable and old_default.storage == "primary"
        source = value["source"]
        primary_key = registry.mint_edition(slug, value["edition"],
            value["title"] + " (First1KGreek, Drachmann 1903)",
            aliases={"cts": value["edition_urn"]})
        primary = work.editions[primary_key]
        primary.provider, primary.license, primary.source = "first1k", repair.LICENSE, source["url"]
        primary.editor, primary.year = source["editor"], source["year"]
        primary.scheme, primary.storage, primary.servable = "section", "primary", True
        primary.note = "Retained byte-identical First1K primary. " + ATTRIBUTION
        secondary_key = registry.mint_edition(slug, repair.SECONDARY_EDITION,
            "First1KGreek, retained former TLG-keyed duplicate serialization")
        secondary = work.editions[secondary_key]
        secondary.provider, secondary.license, secondary.source = "first1k", repair.LICENSE, source["url"]
        secondary.editor, secondary.year = source["editor"], source["year"]
        secondary.scheme, secondary.storage, secondary.servable = "former-work.source-section", "secondary", True
        secondary.note = (
            "Literal former primary rows of the same digital edition, with "
            "original citations and opaque identifier preserved. This is not "
            "an independent textual witness. " + repair.QUALIFICATION)
        work.default_edition = previous if preserve_default else primary_key
        path = repair.primary(slug)
        literal = value["counts"]["secondary_path"]
        review = {"policy": "exact-same-edition-duplicate-primary-consolidation",
            "manifest": value["authority"]["path"], "manifest_sha256": value["authority"]["sha256"],
            "canonical_id": value["canonical_id"], "retired_source": value["retired_source"],
            "retired_source_id": value["retired_source_id"],
            "attribution_qualification": ATTRIBUTION, "qualification": repair.QUALIFICATION,
            "source_editions": [deepcopy(source)],
            "counts": {name: value["counts"][name] for name in
                ("primary_rows", "secondary_rows", "analysis_tokens")},
            "components": [
                {"edition": primary_key, "role": "retained-primary", "provider": "first1k",
                 "license": repair.LICENSE, "source": source["url"], "storage": "primary",
                 "path": path, "sha256": audit["outputs"][path],
                 "passages": value["counts"]["primary_rows"], "analysis_tokens": value["counts"]["analysis_tokens"]},
                {"edition": secondary_key, "role": "literal-duplicate-serialization", "provider": "first1k",
                 "license": repair.LICENSE, "source": source["url"], "storage": "secondary",
                 "path": literal, "sha256": audit["outputs"][literal],
                 "passages": value["counts"]["secondary_rows"], "independent_witness": False,
                 "counts_toward_primary_frequency": False}]}
        earlier = work.coverage_composition.get("pindar_duplicate_review", {})
        if "upstream_date_readings" in earlier:
            review["upstream_date_readings"] = deepcopy(earlier["upstream_date_readings"])
        work.coverage_composition = {**work.coverage_composition, "pindar_duplicate_review": review}
    return identities
