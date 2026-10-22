"""Source-pinned edition sections retained outside authorial corpus totals.

These decisions classify the five sections of one reviewed First1K edition.
They do not turn section names into a corpus-wide rule: another work's
``commentary`` or ``testimonium`` can be its own authorial text.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path


HIPPONAX_WORK = "hipponax.fragmenta"
HIPPONAX_EDITION = "1st1K-grc1"
HIPPONAX_PARATEXT = "data/paratext/hipponax-brandt1888.jsonl"
ROLE_AUTHORITY = "data/corpus_changes/editorial-role-review/changes.json"
HIPPONAX_SOURCE = {
    "source": "first1k",
    "edition": HIPPONAX_EDITION,
    "source_path": "sources/first1k/data/tlg0233/tlg001/tlg0233.tlg001.1st1K-grc1.xml",
    "sha256": "82415a5b06330fc223aa5d15080b078637ff6eb354efeef2ec7b85019be090b7",
    "revision": "4c9c843d80ee94b4371f52add5f7d68bbfe7ba4c",
    "repository": "https://github.com/OpenGreekAndLatin/First1KGreek",
    "url": "https://github.com/OpenGreekAndLatin/First1KGreek/blob/4c9c843d80ee94b4371f52add5f7d68bbfe7ba4c/data/tlg0233/tlg001/tlg0233.tlg001.1st1K-grc1.xml",
    "title": "Corpusculum Poesis Epicae Graecae Ludibundae, volume 1: Fragmentum (128)",
    "editor": "Brandt, Paul",
    "year": 1888,
    "license": "CC-BY-SA-4.0",
}

HIPPONAX_ROLES = {
    "similes": {
        "editorial_role": "homeric-comparanda",
        "lang": "grc",
        "heading": "HOMERI LOCI SIMILES",
        "source_citations": ["α 1", "υ 181", "Γ 417", "ρ 217", "Α 316"],
        "why_not_served": "Brandt's Homeric parallels compare verses of the fragment with Homer; these quotations are not additional Hipponax verses.",
    },
    "testimonium": {
        "editorial_role": "external-testimonium",
        "lang": "grc",
        "heading": "TESTIMONIVM",
        "source_citations": ["Ath. XV 698b"],
        "why_not_served": "Athenaeus's report quoting Polemon introduces the Hipponax fragment; the external testimony and abbreviated quotation are retained apart from Hipponax's authorial text.",
    },
    "variants": {
        "editorial_role": "critical-apparatus",
        "lang": "mul",
        "heading": "VARIETAS LECTIONIS",
        "source_citations": [],
        "why_not_served": "Brandt's critical apparatus records manuscript and editorial variants with their attributions; every variant remains in the retained section rather than being counted as another Hipponax reading.",
    },
    "commentary": {
        "editorial_role": "editorial-commentary",
        "lang": "mul",
        "heading": "COMMENTARIVS",
        "source_citations": [],
        "why_not_served": "Brandt's Latin commentary and its Greek examples discuss the fragment and quote other authors; they are edition commentary rather than additional Hipponax verses.",
    },
}


def validate_source(work, edition, source, path):
    """Reject source drift before applying the reviewed Hipponax partition."""
    if work != HIPPONAX_WORK:
        return
    if edition != HIPPONAX_EDITION or source != HIPPONAX_SOURCE["source"]:
        raise ValueError("Hipponax editorial roles require the reviewed First1K edition")
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != HIPPONAX_SOURCE["sha256"]:
        raise ValueError("Hipponax editorial-role source checksum changed; review the revised edition before rebuilding")


def partition_editorial_rows(work, rows):
    """Return unchanged primary rows and losslessly attributed paratext rows.

    The exact five section identities are required for the reviewed edition.
    Unknown, repeated, or missing sections fail closed, since accepting a new
    section without reviewing its role could restore the original defect.
    """
    rows = list(rows)
    if work != HIPPONAX_WORK:
        return rows, []
    if (len(rows) != 5 or {row.get("locus") for row in rows}
            != {"frag128", *HIPPONAX_ROLES}):
        raise ValueError("Hipponax editorial roles require exactly the five reviewed source sections")
    primary, retained = [], []
    for row in rows:
        if (row.get("urn") != work or row.get("edition") != HIPPONAX_EDITION
                or row.get("source") != HIPPONAX_SOURCE["source"]):
            raise ValueError("Hipponax editorial-role row differs from the reviewed work, edition, or source")
        if row["locus"] == "frag128":
            primary.append(row)
            continue
        role = HIPPONAX_ROLES[row["locus"]]
        attributed = deepcopy(row)
        attributed.update({
            "class": "edition_apparatus",
            "lang": role["lang"],
            "editorial_role": role["editorial_role"],
            "why_not_served": role["why_not_served"],
            "editorial_role_authority": {
                "source_sha256": HIPPONAX_SOURCE["sha256"],
                "source_revision": HIPPONAX_SOURCE["revision"],
                "source_url": HIPPONAX_SOURCE["url"],
                "tei_section_n": row["locus"],
                "tei_heading": role["heading"],
                "source_citations": deepcopy(role["source_citations"]),
            },
            "editorial_role_review": {
                "schema_version": 1, "authority": ROLE_AUTHORITY, "work": work,
            },
        })
        retained.append(attributed)
    return primary, retained


def paratext_path(work):
    """The dedicated sidecar for this reviewed edition, never a shared file."""
    return HIPPONAX_PARATEXT if work == HIPPONAX_WORK else None
