"""Scan-reviewed boundaries and readings of Crusius's Phoenix appendix.

The supplied scan is a complete Herodas volume, not a Phoenix collected works
edition.  Its Phoenix appendix is the twenty-one verses of Coronistae on
printed pages 83–84.  This module records source observations; it never edits
corpus rows.  Printed conjectural supplies remain visibly bracketed and carry
whole-token lexical exclusions, including the partially supplied <τού>τῳ.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata


REVIEWED_AT = "2026-10-22T03:40:59Z"
WORK = "phoenix.fragmenta"
EDITION = "qwen36-phoenix_choliambi_crusius"
LOCUS_PREFIX = "phoenix_choliambi_crusius_"
ORIGINAL_CORPUS_SHA256 = "9015e9406b4c768489e014c1874c064c3913738aa4954433b7932ea3ee914ce9"
SOURCE = {
    "id": "crusius-1894-phoenix-coronistae",
    "title": "Herondae Mimiambi. Accedunt Phoenicis Coronistae, Mattii Mimiamborum fragmenta",
    "editor": "Crusius, Otto",
    "year": 1894,
    "edition_statement": "Iterum edidit",
    "publisher": "B. G. Teubner, Leipzig",
    "catalog_url": "https://archive.org/details/herondaemimiamb01hero",
    "url": "https://archive.org/download/herondaemimiamb01hero/herondaemimiamb01hero.pdf",
    "download_url": "https://archive.org/download/herondaemimiamb01hero/herondaemimiamb01hero.pdf",
    "archive_id": "herondaemimiamb01hero",
    "contributor": "Columbia University Libraries",
    "scan_sha256": "999122f204d54ec0071749c354598adef4203ea6fc61b53e4a6b0f5df92aade1",
    "sha256": "999122f204d54ec0071749c354598adef4203ea6fc61b53e4a6b0f5df92aade1",
    "scan_bytes": 10963170,
    "physical_pages": 107,
    "title_physical_page": 9,
    "phoenix_physical_pages": [68, 69],
    "phoenix_printed_pages": [83, 84],
    "coverage": "Coronistae, verses 1–21 only; not Phoenix's collected fragments",
    "license_basis": "Public domain edition published in 1894",
    "transcription_convention": "Unicode NFC; printed apostrophes rendered as U+2019; printed angle supplies rendered as ASCII < and >; running titles, line numbers, apparatus, and omission ornaments are separate source roles",
}

# Exact currently served preimages and directly inspected printed readings.
# The source's final sigma and diacritics are transcribed, not modernized.
_READINGS = [
    (68, 3, "Ἔσθλοῖ, κορώνη χεῖρα πρόσδοτε κριθέων,", "Ἐσθλοί, κορώνῃ χεῖρα πρόσδοτε κριθέων,"),
    (68, 4, "τῇ παιδὶ τοῦ Ἀπόλλωνος, ἥ λέχος πυράων", "τῇ παιδὶ τοῦ Ἀπόλλωνος, ἢ λέκος πυρῶν"),
    (68, 5, "ἢ <τ'> ἄρτον ἢ <τ'> ἡμαῖθον, ἥ ὅτι τις χρήζει.", "ἢ <τ’> ἄρτον ἢ <τ’> ἤμαιθον, ἢ ὅτι τις χρῄζει."),
    (68, 6, "δότ', ὦγαθοί,  τῶν ἕκαστος ἐν χερσὶν", "δότ’, ὦγαθοί, <τι> τῶν ἕκαστος ἐν χερσὶν"),
    (68, 7, "ἔχει κορώνη· χέλα λήψεται χόνδρον·", "ἔχει κορώνῃ· χἄλα λήψεται χόνδρον·"),
    (68, 8, "φιλεῖ γὰρ αὐτὴ πάγχυ ταῦτα δαίνυσθαι·", "φιλεῖ γὰρ αὕτη πάγχυ ταῦτα δαίνυσθαι·"),
    (68, 9, "ὁ νῦν ἄλας δοὺς αὐθὶ κηρίον δώσει.", "ὁ νῦν ἅλας δοὺς αὖθι κηρίον δώσει."),
    (68, 10, "ὦ παῖ, θύρην ἄγκλινε — Πλοῦτος ἤκουσε,", "ὦ παῖ, θύρην ἄγκλινε — Πλοῦτος ἤκουσε,"),
    (68, 11, "καὶ τῇ κορώνῃ παρθένος φέρει σῦκα.", "καὶ τῇ κορώνῃ παρθένος φέρει σῦκα."),
    (68, 12, "θεοί, γένοιτο πάντ' ἄμεμπτος ἡ κοῦρη", "θεοί, γένοιτο πάντ’ ἄμεμπτος ἡ κούρη"),
    (68, 13, "κάρνειόν ἄνδρα κόνωμαστὸν ἐξεύροι,", "κἀφνειὸν ἄνδρα κὠνομαστὸν ἐξεύροι,"),
    (68, 14, "καὶ τῷ γέροντι πατρὶ κοῦρον εἰς χεῖρας", "καὶ τῷ γέροντι πατρὶ κοῦρον εἰς χεῖρας"),
    (68, 15, "καὶ μητρὶ κοῦρην εἰς τὰ γόνα κατθεῖη,", "καὶ μητρὶ κούρην εἰς τὰ γοῦνα κατθείη,"),
    (68, 16, "θάλας τρέφειν γυναῖκα τοῖς κασιγνήτοις.", "θάλος τρέφειν γυναῖκα τοῖς κασιγνήτοις."),
    (68, 17, "ἐγὼ δ', ὅκον πόδες φέρουσι, ὀφθαλμοὺς", "ἐγὼ δ’, ὅκου πόδες φέρουσιν, ὀφθαλμοὺς"),
    (69, 1, "ἀμείβομαι, Μοῦσαισι πρὸς θύρας ἄδων", "ἀμείβομαι, Μούσαισι πρὸς θύραις ᾄδων"),
    (69, 2, "καὶ δόντι καὶ μὴ δόντι — πλεῖονα τῷ γε.", "καὶ δόντι καὶ μὴ δόντι — πλέονα <τού>τῳ γε."),
    (69, 3, "ἀλλ', ὦραθοί, ἐπορέξαθ' ὧν μυχὸς πλουτεῖ.", "ἀλλ’, ὦγαθοί, ἐπορέξαθ’ ὧν μυχὸς πλουτεῖ."),
    (69, 4, "δός, ὦ ἄναξ, δός καὶ σὺ πολλά μοι νύμφη·", "δός, ὦ ἄναξ, δὸς καὶ σὺ πολλά μοι νύμφη·"),
    (69, 5, "νόμος κορώνη χεῖρα δοῦν ἀπαιτούση.", "νόμος κορώνῃ χεῖρα δοῦν ἀπαιτούσῃ."),
    (69, 6, "τοσαύτ' ἀείδω· δός τι, καὶ καταχρήσει.", "τοσαῦτ’ ἀείδω· δός τι, καὶ καταχρήσει."),
]


def _supplies(text: str) -> list[dict]:
    """Keep each entire supplied token outside lexical projection."""
    ranges = []
    for match in re.finditer(r"<[^<>]+>[^\s,.;·—]*", text):
        ranges.append({
            "start": match.start(), "end": match.end(),
            "text": match.group(), "text_role": "editorial-supply",
            "lexical_eligible": False,
            "reason": "Printed angle brackets mark an editorial supply; exclude the complete token, including any unsupplied continuation",
        })
    return ranges


SPECS = [
    {
        "id": f"phoenix-crusius-1894-verse-{verse:02}",
        "locus": f"{LOCUS_PREFIX}{physical:04}.{line}",
        "verse": verse,
        "scan_page": physical,
        "printed_page": 83 if physical == 68 else 84,
        "original_text": original,
        "corrected_text": corrected,
        "original_text_sha256": hashlib.sha256(original.encode()).hexdigest(),
        "disposition": "correct-scan-reading" if original != corrected else "retain-scan-reading",
        "text_role": "authorial-body",
        "lexical_eligible": True,
        "editorial_supplies": _supplies(corrected),
        "gap_after": {"kind": "printed-omission-divider", "marker": "***",
                      "source_id": SOURCE["id"], "physical_page": 69,
                      "printed_page": 84,
                      "qualification": "Crusius separates verses 17 and 18 with three asterisk ornaments; the extent of intervening omitted material is unspecified"} if verse == 17 else None,
        "scan": {
            "physical_page": physical,
            "printed_page": 83 if physical == 68 else 84,
            "side": "right" if physical == 68 else "left",
            "region": [.52, .28, .92, .66] if physical == 68 else [.15, .10, .49, .30],
            "source_id": SOURCE["id"],
            "sha256": SOURCE["scan_sha256"],
        },
        "evidence": f"Direct visual inspection of Crusius 1894, printed page {83 if physical == 68 else 84}, Coronistae verse {verse}; the body is separated from apparatus by a horizontal rule",
    }
    for verse, (physical, line, original, corrected) in enumerate(_READINGS, 1)
]

BODY_LOCI = frozenset(spec["locus"] for spec in SPECS)
BOUNDARY_OBSERVATIONS = [
    {
        "physical_page": 9,
        "observed": "Title page names Herondae Mimiambi, with Phoenicis Coronistae and Mattii Mimiamborum fragmenta as appendices; Iterum edidit Otto Crusius; Leipzig, Teubner, MDCCCXCIV",
        "disposition": "identify-volume-and-edition",
    },
    {
        "physical_page": 68,
        "printed_pages": [82, 83],
        "observed": "Left page is Herodas's disputed material, including item 28 and the quotation γῆρας καὶ πενία; right page starts PHOENIX COLOPHONIVS / ΚΟΡΩΝΙΣΤΑΙ and verses 1–15",
        "disposition": "split-author-boundary-within-one-scan-image",
        "exclude_loci": [f"{LOCUS_PREFIX}0068.1", f"{LOCUS_PREFIX}0068.2"],
    },
    {
        "physical_page": 69,
        "printed_pages": [84, 85],
        "observed": "Left page concludes Phoenix's verses 16–21 above the apparatus rule. Three asterisk ornaments separate verses 17 and 18. Right page begins CN. MATTIVS / MIMIAMBORVM FRAGMENTA",
        "disposition": "stop-phoenix-before-mattius-and-preserve-omission-marker",
        "omission_after_verse": 17,
        "omission_before_verse": 18,
        "omission_marker": "***",
        "qualification": "The printed divider marks omitted intervening material; its extent is not inferred and the poem is not represented as continuous across that divider",
    },
]


def classify_locus(locus: str) -> dict:
    """Classify attribution of an original row, without guessing its text."""
    match = re.fullmatch(re.escape(LOCUS_PREFIX) + r"(\d{4})\.(\d+)", locus)
    if not match:
        raise ValueError(f"Unexpected Phoenix source locus: {locus}")
    page, line = map(int, match.groups())
    if not 1 <= page <= SOURCE["physical_pages"] or line < 1:
        raise ValueError(f"Locus falls outside the pinned scan: {locus}")
    if locus in BODY_LOCI:
        return {"text_role": "authorial-body", "lexical_eligible": True,
                "disposition": "retain-phoenix-body"}
    if page == 68 and line == 2:
        return {"text_role": "work-title", "lexical_eligible": False,
                "disposition": "retain-phoenix-title-as-metadata"}
    if page == 68 and line == 1:
        role = "other-work-quotation"
        evidence = "Printed page 82, item 28, is the final Herodas section on the left side of the image; Phoenix starts on the right page 83"
    elif page < 28:
        role = "volume-front-matter"
        evidence = "Source images before Herodas's text contain the volume's title, Latin prefaces, bibliographic material, and quoted Greek examples"
    elif page < 68:
        role = "other-work-material"
        evidence = "Herodas testimonia, mimiambs, fragments, and commentary precede the explicit Phoenix heading on printed page 83"
    elif page == 69:
        role = "other-work-or-apparatus"
        evidence = "Only the six registered body rows on the left page 84 belong to Phoenix; the remaining image contains apparatus and Mattius on printed page 85"
    elif page < 72:
        role = "other-work-material"
        evidence = "Mattius's appendix follows the Phoenix conclusion and precedes the volume's indices"
    elif page == 72:
        role = "other-work-or-index"
        evidence = "This spread contains the end of the preceding appendix and the beginning of INDICES / NOMINA PROPRIA on printed page 91"
    else:
        role = "volume-index"
        evidence = "The volume's indices follow the INDICES heading on printed page 91 and contain Herodas references and repeated quotations, not additional Phoenix fragments"
    return {"text_role": role, "lexical_eligible": False,
            "disposition": "quarantine-misattributed-volume-material", "evidence": evidence}


def build_source_review(rows, *, reviewed_at: str = REVIEWED_AT) -> dict:
    """Compile fixed observations only after validating all exact preimages."""
    instant = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    if instant.tzinfo is None or instant.utcoffset() != timezone.utc.utcoffset(instant):
        raise ValueError("Review timestamp must include UTC")
    if isinstance(rows, dict):
        indexed = rows
    else:
        indexed = {}
        for row in rows:
            if row["locus"] in indexed:
                raise ValueError(f"Duplicate source locus: {row['locus']}")
            indexed[row["locus"]] = row
    records = deepcopy(SPECS)
    for spec in records:
        locus = spec["locus"]
        row = indexed.get(locus)
        if row is None:
            raise ValueError(f"Missing reviewed Phoenix verse: {locus}")
        if row.get("urn") != WORK or row.get("edition") != EDITION:
            raise ValueError(f"Reviewed row has different work or edition: {locus}")
        if row.get("text") != spec["original_text"]:
            raise ValueError(f"Reviewed preimage differs: {locus}")
        if unicodedata.normalize("NFC", spec["corrected_text"]) != spec["corrected_text"]:
            raise ValueError(f"Non-NFC source transcription: {locus}")
        spec["reviewed_at"] = reviewed_at
        spec["original_row_sha256"] = hashlib.sha256(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    roles = []
    for locus in sorted(indexed):
        row = indexed[locus]
        if row.get("urn") != WORK or row.get("edition") != EDITION:
            raise ValueError(f"Unexpected row in Phoenix source: {locus}")
        roles.append({"locus": locus, **classify_locus(locus)})
    return {
        "schema_version": 1,
        "work": WORK, "edition": EDITION, "reviewed_at": reviewed_at,
        "source": deepcopy(SOURCE),
        "source_observations": deepcopy(BOUNDARY_OBSERVATIONS),
        "approved_primary_loci": [spec["locus"] for spec in records],
        "scope": "Phoenix Coronistae, 21 verses",
        "verses": records, "row_roles": roles,
        "scope_accounting": {"body_verses": 21, "body_loci": len(BODY_LOCI),
                  "original_rows": len(indexed),
                  "complete_collected_fragments": False},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--reviewed-at", default=REVIEWED_AT)
    args = parser.parse_args()
    raw = args.corpus.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_CORPUS_SHA256:
        raise SystemExit("Original Phoenix corpus checksum does not match the reviewed preimage")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    print(json.dumps(build_source_review(rows, reviewed_at=args.reviewed_at), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
