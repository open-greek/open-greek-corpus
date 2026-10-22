#!/usr/bin/env python3
"""Scan-verified body inventory for the Headlam–Knox Herodas recovery.

Regions are normalized (left, top, right, bottom) coordinates in the pinned
542-page PDF. They locate printed material; they do not authorize admitting all
Greek inside a region. Speaker labels and the IXa/IXb reference headings still
require role separation. The edition's verse numbers count metrical verses,
including verses split between speakers or across physical pages.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path


SOURCE_SHA256 = "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a"
SOURCE = {
    "title": "Herodas: The Mimes and fragments",
    "editor": ["Walter Headlam (notes)", "A. D. Knox (editor)"],
    "year": 1922,
    "publisher": "Cambridge University Press",
    "url": "https://archive.org/details/mimesfragments00hero",
    "download_url": "https://archive.org/download/mimesfragments00hero/mimesfragments00hero.pdf",
    "sha256": SOURCE_SHA256,
    "bytes": 35869325,
    "pdf_pages": 542,
    "audit_path": "data/corpus_changes/editorial-role-review/source-herodas.pdf",
}

EXISTING_BODY_PAGES = (72, 74, 132, 180, 182, 236, 238, 290, 292, 294, 344, 346, 472)

QUALIFICATION = (
    "This inventory covers the Greek authorial body printed in the pinned 1922 "
    "edition: Mimes I–VIII, IX with IXa/IXb, X, and XI. It is not a claim that "
    "the ancient works survive complete. The 62 existing primary rows on 13 "
    "pages already represent those pages' complete printed authorial blocks; "
    "their identities and literal readings are preserved. Recovery concerns 22 "
    "source-disjoint missing body pages. Existing OCR spelling defects, critical "
    "restorations, dialogue distributions, and attribution variants are not "
    "silently resolved. VIII's printed lacunae and incomplete words remain "
    "lacunae and incomplete words. Anchors identify printed boundaries and are "
    "not replacement transcriptions or requirements that an OCR witness agree "
    "in spelling. Modern Greek renderings of Latin Mattius, anonymous or "
    "conjecturally attributed quotations, and the unplaced two-letter papyrus "
    "remain separately identified below. Facing English and scholarly notes "
    "are outside the authorial body."
)


def _page(scan_page, mime, verses, region, first_body, last_body, evidence="", ocr_region=None):
    result = {
        "scan_page": scan_page,
        "printed_page": scan_page - 70,
        "mime": mime,
        "verses": verses,
        "region": list(region),
        "first_body": first_body,
        "last_body": last_body,
        "already_present": scan_page in EXISTING_BODY_PAGES,
        "confidence": "scan-verified",
        "evidence": (
            f"Pinned scan, PDF page {scan_page}, printed page {scan_page - 70}: "
            "main Greek verse block; crop excludes the running heading, facing "
            "translation, and smaller-type apparatus. " + evidence
        ).rstrip(),
    }
    if ocr_region is not None:
        result["ocr_region"] = list(ocr_region)
    return result


# Top/bottom cuts were checked on rendered pages. Horizontal cuts retain the
# full verse width; some margin numerals remain and are not authorial words.
# The suffixes a/b below identify a physical-page division of one verse, not
# an additional metrical verse. Printed speaker labels remain inside crops.
BODY_PAGES = [
    _page(72, "I", "1–16", (.20, .210, .96, .880),
          "ἀράσσει τὴν θύρην", "σκιὴ παρέστηκεν"),
    _page(74, "I", "17–44", (.20, .082, .96, .740),
          "σιγῇ τε καὶ μὴ", "ἄγριος χειμών"),
    _page(76, "I", "45–74", (.20, .082, .90, .790),
          "καταιγίσας ἔπνευσε", "μῦθον ὃς μὲν γρήαισι"),
    _page(78, "I", "75–90", (.20, .082, .90, .545),
          "πρέπει γυναιξὶ ταῖς νέαις", "νέαι μένοιεν"),
    _page(132, "II", "1–23", (.15, .235, .96, .718),
          "ἄνδρες δικασταί", "ἀσκέρας σαπρὰς"),
    _page(134, "II", "24–59", (.17, .082, .96, .880),
          "ἄξει τῶν ἐμῶν", "ἐς Φασηλίδα πλώσῃ"),
    _page(136, "II", "60–94", (.17, .082, .96, .780),
          "ἐγὼ δ’ ὅκως", "τὴν πόλιν ξείνοις"),
    _page(138, "II", "95–102", (.17, .082, .96, .270),
          "νῦν δείξεθ’", "ἡ παροιμίη βάζει"),
    _page(180, "III", "1–27", (.17, .265, .96, .830),
          "αἱ φίλαι Μοῦσαι", "οὐκ ὄνους βόσκειν"),
    _page(182, "III", "28–59", (.16, .082, .96, .780),
          "αὐτὸν διδάσκω", "Εὐθίης κοῦ μοι"),
    _page(184, "III", "60–81a", (.16, .082, .96, .780),
          "κοῦ Κόκκαλος, κοῦ Φίλλος", "ἱκαναί, Λαμπρίσκε",
          "Verse 81 continues on PDF page 186 after a change of speaker."),
    _page(186, "III", "81b–97", (.15, .082, .96, .790),
          "καὶ σὺ δὴ παῦσαι", "αἱ πότνιαι βλέπωσιν",
          "The opening words complete verse 81 begun on PDF page 184; "
          "verse 82 begins with κάκ’ ἔργα πρήσσων."),
    _page(236, "IV", "1–25a", (.16, .226, .96, .830),
          "Χαίροις, ἄναξ Παίηον", "ἔστησεν ὁ Πρήξωνος",
          "Verse 25 continues on PDF page 238 after a change of speaker."),
    _page(238, "IV", "25b–53", (.15, .082, .96, .750),
          "ἵλεως εἴη", "ὦτα νωθρίη θλίβει",
          "The opening words complete verse 25 begun on PDF page 236."),
    _page(240, "IV", "54–80", (.15, .082, .96, .745),
          "ἀλλ’ ἡμέρη", "μεζόνως οὖτις"),
    _page(242, "IV", "81–95", (.15, .082, .96, .470),
          "ἠρέσατο τὸν Παίηον", "τῆς μοίρης"),
    _page(290, "V", "1–18", (.19, .250, .96, .880),
          "Λέγε μοι σύ, Γάστρων", "τὴν ἁπληγίδ’ ἐκδύσας"),
    _page(292, "V", "19–41", (.19, .082, .96, .880),
          "Βίτιννα, τῶν σε γουνάτων", "τὸ ῥύγχος"),
    _page(294, "V", "42–73a", (.20, .082, .96, .805),
          "τοῦ παντοέρκτεω τοῦδε", "ἁμαρτίην",
          "Verse 73 continues on PDF page 296 after a change of speaker."),
    _page(296, "V", "73b–85", (.20, .082, .96, .450),
          "Κύδιλλα, μή με λυπεῖτε", "ὁρτὴν ἐξ ὁρτῆς",
          "The opening words complete verse 73 begun on PDF page 294."),
    _page(344, "VI", "1–20a", (.19, .235, .96, .875),
          "Κάθησο, Μητροῖ", "Μητροῖ, σὺ κεῖνον",
          "Verse 20 continues on PDF page 346 after a change of speaker."),
    _page(346, "VI", "20b–47a", (.19, .082, .96, .885),
          "Νοσσὶς εἶχεν ἡρίννης", "ἀλλ’ εἰπὲ τὸν ῥάψαντα",
          "The first words complete verse 20; the final words begin verse 47, "
          "continued on PDF page 348 after a change of speaker."),
    _page(348, "VI", "47b–78", (.17, .082, .96, .890),
          "τί μοι ἐνεύχῃ", "δοῦσα χρήσασθαι",
          "The opening reply completes verse 47 begun on PDF page 346."),
    _page(350, "VI", "79–102", (.15, .082, .96, .795),
          "ἀλλ’ εἴ σε καὶ τοῦτ’", "ἐν κόλπῳ"),
    _page(388, "VII", "1–22", (.19, .207, .96, .725),
          "Κέρδων, ἄγω σοι", "σάφ’ ἡνίσκοις"),
    _page(390, "VII", "23–49", (.19, .082, .96, .635),
          "ἐξηρτίωται πᾶσα", "ἡ ἀγορὴ δεῖται"),
    _page(392, "VII", "50–78", (.20, .082, .96, .742),
          "χαλκῶν δέ", "ἐξεδίφησας"),
    _page(394, "VII", "79–105", (.20, .082, .96, .830),
          "γύναι, μιῆς μνῆς", "ὄναρ δοῦναι"),
    _page(396, "VII", "106–129", (.19, .082, .96, .580),
          "καὶ ταῦτα καὶ ταῦτα", "τὸν φρονοῦντα δεῖ ῥάπτειν"),
    _page(440, "VIII", "1–23", (.20, .231, .96, .700),
          "δούλη Ψύλλα", "γεύεται τρώγων"),
    _page(442, "VIII", "24–54", (.20, .082, .96, .720),
          "οἱ δ’ ἀμφί", "ῥυπ(αρὸς)",
          "Verses 49–53 contain incomplete readings; verse 54 is a dotted "
          "loss. The final anchor is the last word-shaped fragment, not the "
          "bottom of the block: two isolated initial letters and dotted "
          "lacunae follow it and must not be dropped."),
    _page(444, "VIII", "55–79", (.15, .082, .96, .595),
          "τὰ δεινὰ πνεῦσαι", "Ξουθίδαις ἐπίουσιν",
          "The first three printed lines (55–57) are dotted losses; first "
          "readable Greek is verse 58. The crop preserves those initial losses."),
    _page(472, "IX; IXa; IXb", "IX 1–13; IXa 1–3; IXb 1–3", (.20, .205, .96, .810),
          "ἔζεσθε πᾶσαι", "τοῦ ἑτέρου δόκει πρήσσειν",
          "Includes three separately headed body fragments and printed losses. "
          "The IXa/IXb reference headings are not authorial. The small-type "
          "IXc attribution note below the crop remains excluded."),
    _page(480, "X", "1–4", (.20, .328, .96, .420),
          "Ἐπὴν τὸν ἑξηκοστὸν", "τῆς ζοῆς ἀπήμβλυνται",
          "Only four Greek verses at PDF y=204.1–251.4 points. Title, English "
          "translation, and apparatus are excluded. The apparatus attributes "
          "the quotations to Herodas through Stobaeus, Florilegium 116.21; "
          "their combination and readings involve named editorial changes."),
    _page(486, "XI", "1", (.20, .304, .96, .360),
          "προσφὺς ὅκως", "χοιράδων ἀνηρίτης",
          "The single Greek XI verse at PDF y=189.6–201.2 points and its "
          "following eight-dot loss row near y=212 points. "
          "Athenaeus 86b explicitly names Herodas and Synergazomenai. The "
          "following XIa heading and its two verses are outside the body region "
          "and held separately because their Herodas attribution is conjectural. "
          "The separately recorded original OCR region ends before the dotted "
          "loss: the in-progress pinned request recognized the verse only; the "
          "full scan review retains the loss without changing that request.",
          ocr_region=(.20, .304, .96, .344)),
]

HOLDS = [
    {"scan_page": 472, "printed_page": 402, "label": "IXc source note",
     "status": "attribution-hold", "region": [.15, .820, .99, .880],
     "evidence": "Small-type Zenobius 6.47 note attributes a statement to "
         "Herodotus; Bergk assigned it to Herodas because it does not appear "
         "in Herodotus. It is not a printed authorial body fragment and was "
         "already retained as an editorial source note by the role review."},
    {"scan_page": 482, "printed_page": 412, "label": "Xa; Xb beginning",
     "status": "attribution-hold", "region": [.12, .700, .97, .820],
     "evidence": "Commentary introduces a corrupt proverb as possibly "
         "choliambic (Xa, Crusius 70), then calls the following proposal Xb "
         "a still longer venture. The discussion continues on PDF page 483."},
    {"scan_page": 483, "printed_page": 413, "label": "Xb; other doubtful quotations",
     "status": "attribution-hold", "region": [.05, .085, .89, .370],
     "evidence": "Commentary says Herodas is only one of many choliambic "
         "writers, identifies Crusius 66 with Phoenix and 65 with Callimachus, "
         "and discusses other uncertain fragments. Its Greek quotations are "
         "not wholesale Herodas authorial text."},
    {"scan_page": 486, "printed_page": 416, "label": "XIa",
     "status": "attribution-hold", "region": [.20, .380, .96, .435],
     "evidence": "The two Greek lines at PDF y=238.1–260.2 are anonymous "
         "courtesan speech quoted from Strabo 371. The commentary on printed "
         "page 417 says the subject may have been such a discussion and I "
         "would refer the fragment XIa here: this is conjectural attribution."},
    {"scan_page": 487, "printed_page": 417, "label": "XIb",
     "status": "attribution-hold", "region": [.02, .600, .85, .680],
     "evidence": "Commentary describes the quotation from Herodian through "
         "Etymologicum Magnum page 19 as anonymous, saying here too may "
         "belong (XIb, Crusius 69). No secure Herodas attribution is supplied."},
    {"scan_page": 490, "printed_page": 420, "label": "XII: modern Greek renderings of Mattius",
     "status": "excluded-modern-rendering", "region": [.28, .275, .99, .690],
     "evidence": "Printed page 419/PDF 489 explicitly identifies these "
         "Greek lines as renderings by Headlam with additional renderings "
         "by Knox of Latin Mattius. It says their status as translations is "
         "uncertain and their dependence on Herodas doubly uncertain. Greek "
         "language and body-sized type do not make these ancient Herodas."},
    {"scan_page": 493, "printed_page": 423, "label": "unplaced papyrus (under XIII, XIV, XV)",
     "status": "unplaced-nonlexical-fragment", "region": [.40, .420, .50, .450],
     "evidence": "The edition calls the papyrus unplaced and prints only ξυ "
         "with faint remains of letters below. It supplies neither a word "
         "nor a verse location. Its note maps the older XIV and XV numbers "
         "to IXa and IXb, which are already represented on PDF page 472."},
]


def verify_source_pdf(path: str | Path) -> None:
    raw = Path(path).read_bytes()
    if len(raw) != SOURCE["bytes"] or hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Headlam–Knox body inventory source scan changed")


def build_inventory(source_pdf: str | Path | None = None) -> dict:
    """Return a detached source inventory; optionally verify the source bytes."""
    if source_pdf is not None:
        verify_source_pdf(source_pdf)
    pages = [row["scan_page"] for row in BODY_PAGES]
    if len(pages) != 35 or pages != sorted(set(pages)):
        raise ValueError("Herodas body page inventory changed")
    if tuple(row["scan_page"] for row in BODY_PAGES if row["already_present"]) != EXISTING_BODY_PAGES:
        raise ValueError("Herodas existing-page boundary changed")
    for row in BODY_PAGES + HOLDS:
        left, top, right, bottom = row["region"]
        if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
            raise ValueError("Invalid Herodas source crop")
    return deepcopy({
        "schema_version": 1,
        "source": SOURCE,
        "qualification": QUALIFICATION,
        "body_pages": BODY_PAGES,
        "holds": HOLDS,
        "accounting": {"body_pages": 35, "already_present_pages": 13,
                       "missing_body_pages": 22, "preserved_primary_rows": 62},
    })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdf", type=Path)
    args = parser.parse_args()
    print(json.dumps(build_inventory(args.source_pdf), ensure_ascii=False, indent=2))
