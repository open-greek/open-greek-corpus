"""Bounded scan readings for the frozen ten-page Dübner pilot.

These observations identify printed occurrences in the literal pre-split OCR.
They do not change corpus text, count words, add a voter, or claim exhaustive
proofreading. All offsets are Unicode code points in the unnormalized raw row.
Both scans reproduce the same 1855 edition and are not independent editions.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

REVIEWED_AT = "2026-10-24T14:18:29Z"
OUTPUT = "data/corpus_changes/dubner-reading-review"
REVIEW_PATH = OUTPUT + "/source-review.json"
CAPTURE_PATH = OUTPUT + "/capture.json"
RENDERER_VERSION = "1.28.2"
RENDER_DPI = 240
SOURCE_PDFS = {
    "toronto": {"sha256": "9d960c70b833f73b3871701775c557a6db1472cc95a04bea8f35054922715c07",
        "pages": 776, "url": "https://archive.org/download/scholiagraecaina00dbuoft/scholiagraecaina00dbuoft.pdf"},
    "harvard": {"sha256": "61c07b9dbde80569c6e54238f2cbb0897d8bb33386a9ecad389836bd67e0c600",
        "pages": 801, "url": "https://archive.org/download/scholiagraecain01dbgoog/scholiagraecain01dbgoog.pdf"},
}
# Normalized PDF rectangles, rendered directly from the source PDF. The broad
# context remains visible around every letter; crops are not retouched images.
CROPS = {
    "toronto-0043-heading": ("toronto", 43, (.18, .03, .86, .18)),
    "harvard-0044-heading": ("harvard", 44, (.15, .03, .92, .19)),
    "toronto-0043-right": ("toronto", 43, (.48, .12, .99, .91)),
    "harvard-0044-right": ("harvard", 44, (.43, .12, .94, .90)),
    "toronto-0043-left": ("toronto", 43, (.01, .12, .53, .94)),
    "toronto-0058-left": ("toronto", 58, (.01, .05, .56, .97)),
    "toronto-0058-right": ("toronto", 58, (.51, .05, .99, .97)),
    "harvard-0059-left": ("harvard", 59, (.01, .45, .54, .82)),
    "toronto-0073-left": ("toronto", 73, (.01, .04, .53, .44)),
    "toronto-0073-right": ("toronto", 73, (.50, .04, .99, .45)),
    "harvard-0074-right": ("harvard", 74, (.43, .04, .94, .46)),
    "toronto-0074-body": ("toronto", 74, (.01, .15, .99, .95)),
    "harvard-0075-body": ("harvard", 75, (.01, .15, .94, .95)),
    "toronto-0251-body": ("toronto", 251, (.01, .14, .99, .97)),
    "harvard-0278-body": ("harvard", 278, (.01, .14, .94, .97)),
    "toronto-0431-argument": ("toronto", 431, (.02, .29, .53, .49)),
    "toronto-0543-note513": ("toronto", 543, (.46, .17, .99, .45)),
    "toronto-0768-index": ("toronto", 768, (.04, .05, .39, .22)),
}
# Filled from the reviewed renderer output, not from OCR or a language model.
CROP_SHA256 = {'harvard-0044-heading': '7904ba7c453ea75f1338dc4bb6935e69135e591ae881c80d826970b7de933950',
 'harvard-0044-right': '3334a36df7c6a86a16e3bde80fffe118845067e8893dcb88b717837f8d993d2d',
 'harvard-0059-left': '212a200122cfc08c226f81deb72beb61434e676b41014609b3540ff529768b10',
 'harvard-0074-right': 'cbc22b5c23311baba45ad89b677db6018bf89ea64ab79d75d8562805699b237d',
 'harvard-0075-body': 'bfac37c896bf230a2e7df21fdfe0073e765bad9ba175a786584e1d1388dd0a07',
 'harvard-0278-body': '86d115e548cc1b073b9d17534921265acc22113b6fcd8c45d1a5a45e6b279242',
 'toronto-0043-heading': 'f6563927c7a7d860f2cdc12e0bdec16c3e119bbf6818deded49813af127a3126',
 'toronto-0043-left': '5108f884ceed6aec376e78b782d05eb9d4047b727bb3059ceb8ea52d41afe4cf',
 'toronto-0043-right': 'eab942ad7195b6c49e15ce0d695a9c5cf1d114ec6aaf5257b8b1bbe1a40a26fb',
 'toronto-0058-left': '5c1a5978fa3a5a4f814ea6ac9211772c47789e4e4db6ac9ad6db29b9e8243a61',
 'toronto-0058-right': '5b58bd7b90aecf94c58dab6f0869d831b8cd5c3e46230afd876b57a9a06cb861',
 'toronto-0073-left': '7c2cfe1d91150622845d5b81236c4a9eb37b24887dd803a170e419eecc46d033',
 'toronto-0073-right': '7fe87c01460d32a206be3f1abf9f66a9b4df492e3619ff9bb7b3e3e4a1605e4c',
 'toronto-0074-body': '6f216c29037dac58d2233ee3f120aab97f425cfb47fb7f73ff852877c3711311',
 'toronto-0251-body': '9a834c51be7a3d3e2071481a6f2cc6ed219f8d9cb0c8c59fb8d9c7c0a621c57d',
 'toronto-0431-argument': 'bad2e9b0da3bcb4b4107527f86faf381dcd4bbf5b153b3117f6f0f9460d21dcb',
 'toronto-0543-note513': 'fabe232676bce25f4404328feb0d0eb44b1345508972ccdc2a868d766c85c626',
 'toronto-0768-index': '117a7dd919f2ec816370ef8918e8570a71a2d95f79483712edb0b5be277dae5a'}

PAGE_REVIEWS = (
    (9, "edition-title", "No historical occurrence correction; bibliographic page."),
    (43, "acharnians-hypotheses", "Bounded letter-confusion and pilot omission review; many other OCR readings remain unassessed."),
    (58, "acharnians-scholia", "Bounded mixed-script and letter-confusion review; variant sigla remain intact."),
    (73, "acharnians-final-scholia", "All three printed τήνελλα occurrences and nearby consonant confusions reviewed."),
    (74, "knights-hypotheses", "Bounded κ/χ and consonant-confusion review; source role already established by the scope repair."),
    (251, "birds-hypotheses", "Bounded consonant-confusion review; no historical chronology or proper-name normalization inferred."),
    (431, "editorial-annotation", "Printed variant remains editorial evidence; correcting an OCR letter does not admit it as a historical occurrence."),
    (543, "editorial-annotation", "The attached 11 is absent after ἄλλοις. The longer omitted Latin note remains a deferred source omission."),
    (657, "index-title", "No historical occurrence correction; the three index classes are editorial."),
    (768, "editorial-index", "One bounded index-name transcription correction; no new historical attestation."),
)


def anchor(group, page, row, original, corrected, count=1):
    return {"group": group, "page": page, "row": row,
            "original": original, "corrected": corrected, "count": count}


def claim(identifier, page, scope, evidence, crops, *anchors, **metadata):
    return {"id": identifier, "toronto_page": page, "scope": scope,
            "evidence": evidence, "crops": list(crops), "anchors": list(anchors), **metadata}


CLAIMS = (
    claim("lenaiois-source-reading", 43, "historical",
        "Hypothesis I, upper right column, prints ἐν Ληναίοις διὰ Καλλιστράτου. The first letter is capital lambda followed by eta; the frozen preliminary pilot mistakenly proposed Ἀθηναίοις. Both retained OCR extractions have a different corrupted reading.",
        ("toronto-0043-right", "harvard-0044-right"),
        anchor("toronto", 43, 6, "Ἀθναίοις", "Ληναίοις"),
        anchor("harvard", 44, 3, "Ἀγναίοις", "Ληναίοις"),
        supersedes={"path": "data/audits/acharnians-source-pilot/report.json",
            "observation_id": "missing-eta", "proposed_reading": "Ἀθηναίοις",
            "reason": "Both pinned scans print Ληναίοις; the frozen pilot proposal is retained as a historical observation but is not admitted."}),
    claim("acharnians-lakosin-kappa", 43, "historical",
        "Hypothesis I, left column, prints τοῖς Λάκωσιν. The printed consonant is κ, not χ; retain the source's remaining spelling.",
        ("toronto-0043-left",), anchor("toronto", 43, 3, "Λάχωσιν", "Λάκωσιν")),
    claim("sikuon-lemma", 58, "historical",
        "The scholion numbered520 prints σίκυον. Both scans show κ followed by υ and ο, without replacing the source spelling from a dictionary.",
        ("toronto-0058-left", "harvard-0059-left"),
        anchor("toronto", 58, 9, "σίχουν", "σίκυον"), anchor("harvard", 59, 13, "σίκων", "σίκυον")),
    claim("sikuos-article", 58, "historical",
        "The same short scholion prints τῆς ὁ σίκυος. The OCR δ at this occurrence is the printed article ὁ; the unusual surrounding wording is preserved.",
        ("toronto-0058-left", "harvard-0059-left"), anchor("toronto", 58, 9, "δ", "ὁ")),
    claim("sikuos-mixed-alphabet", 58, "historical",
        "The nominative in scholion 520 is σίκυος in both scans. The Latin u/o/s in the Toronto extraction and missing υ in the Harvard extraction are OCR defects.",
        ("toronto-0058-left", "harvard-0059-left"),
        anchor("toronto", 58, 9, "σίχuos", "σίκυος"), anchor("harvard", 59, 13, "σίκος", "σίκυος")),
    claim("laikastrion-kappa", 58, "historical", "Scholion 529 prints λαικαστριῶν, with κ rather than χ.",
        ("toronto-0058-right",), anchor("toronto", 58, 18, "λαιχαστριῶν", "λαικαστριῶν")),
    claim("kratistos-kappa", 58, "historical", "The quoted verse below scholion 530 begins κράτιστος; the printed initial is κ.",
        ("toronto-0058-right",), anchor("toronto", 58, 20, "χράτιστος", "κράτιστος")),
    claim("egkatelipe-kappa", 58, "historical", "The last line of the same quotation prints ἐγκατέλιπε, with κ.",
        ("toronto-0058-right",), anchor("toronto", 58, 26, "ἐγχατέλιπε", "ἐγκατέλιπε")),
    claim("akroomenois-vowels", 58, "historical", "The end of that quoted line prints τοῖς ἀκροωμένοις; the scan shows κ and ο after ρ.",
        ("toronto-0058-right",), anchor("toronto", 58, 26, "ἀχρωωμένοις", "ἀκροωμένοις"), anchor("harvard", 59, 20, "ἀκροαμένους", "ἀκροωμένοις")),
    claim("askon-kappa", 58, "historical", "Scholion 526, lower left column, prints τῶν τὸν ἄνεμον δεχομένων ἀσκῶν. Only this occurrence's χ is corrected to the printed κ.",
        ("toronto-0058-left",), anchor("toronto", 58, 14, "ἀσχῶν", "ἀσκῶν"), anchor("harvard", 59, 18, "ἀσπῶν", "ἀσκῶν")),
    claim("tenella-unsplit", 73, "historical",
        "Scholion 1230 prints τήνελλα as one word three times: lemma, explanation, and the quoted Archilochus verse. Both scans agree; the Toronto split and Harvard σ are contrary OCR readings, not printed alternatives.",
        ("toronto-0073-right", "harvard-0074-right"),
        anchor("toronto", 73, 9, "τὴν ελλα", "τήνελλα", 3), anchor("harvard", 74, 9, "σήνελλα", "τήνελλα", 3)),
    claim("kallinike-kappa", 73, "historical", "The same quotation prints ὦ καλλίνικε, with κ.",
        ("toronto-0073-right", "harvard-0074-right"), anchor("toronto", 73, 9, "χαλλίνικε", "καλλίνικε")),
    claim("heraklees-reading", 73, "historical", "The printed vocative is Ἡράκλεες, with acute on α and κ. Harvard's retained OCR also has this reading; Toronto's Ἥραχλεες is not the print.",
        ("toronto-0073-right", "harvard-0074-right"), anchor("toronto", 73, 9, "Ἥραχλεες", "Ἡράκλεες")),
    claim("aichmeta-chi", 73, "historical", "The quoted line ends αἰχμητὰ δύο. The letter before μ is χ, not γ.",
        ("toronto-0073-right", "harvard-0074-right"), anchor("toronto", 73, 9, "αἰγμητὰ", "αἰχμητὰ")),
    claim("eisthesei-reading", 73, "historical", "After the quotation the print reads ἐν εἰσθέσει, divided εἰ-/σθέσει at the printed line. Harvard also retains εἰσθέσει; Toronto's inserted όδ is not printed.",
        ("toronto-0073-right", "harvard-0074-right"), anchor("toronto", 73, 9, "εἰσόδεσει", "εἰσθέσει")),
    claim("presbu-beta", 73, "historical", "Scholion 1228 prints ὦ πρέσβυ, with β rather than δ.",
        ("toronto-0073-right", "harvard-0074-right"), anchor("toronto", 73, 7, "πρέσδυ :", "πρέσβυ :")),
    claim("presbun-beta", 73, "historical", "The following explanation prints πρέσβυν, with β rather than δ.",
        ("toronto-0073-right", "harvard-0074-right"), anchor("toronto", 73, 7, "πρέσδυν", "πρέσβυν")),
    claim("thrakike-kappa", 73, "historical", "Scholion 1226 prints Θρακική, with κ in its final syllable. No dialect or lemma normalization is inferred.",
        ("toronto-0073-right", "harvard-0074-right"), anchor("toronto", 73, 6, "Θρακιχή", "Θρακική"), anchor("harvard", 74, 6, "Ὀρακινη", "Θρακική")),
    claim("askon-scholion1224", 73, "historical", "The end of the prize explanation in scholion 1224 prints τὸν ἀσκόν. The initial α has smooth breathing and the consonant is κ.",
        ("toronto-0073-left",), anchor("toronto", 73, 4, "ἄσχόν", "ἀσκόν")),
    claim("askon-scholion1225", 73, "historical", "The first two bag references in scholion 1225 print ἀσκόν, followed by the grave-accented ἀσκὸν before δείκνυσι. Each occurrence retains its printed accent.",
        ("toronto-0073-left",), anchor("toronto", 73, 5, "ἄσχόν", ("ἀσκόν", "ἀσκόν", "ἀσκὸν"), 3)),
    claim("deiknusi-kappa", 73, "historical", "The same scholion prints δείκνυσι, with κ rather than χ.",
        ("toronto-0073-left",), anchor("toronto", 73, 5, "δείχνυσι", "δείκνυσι")),
    claim("kathelein-kappa", 74, "historical", "Knights hypothesisII, lower left column, prints καθελεῖν Κλέωνα, with initial κ.",
        ("toronto-0074-body", "harvard-0075-body"), anchor("toronto", 74, 4, "χαθελεῖν", "καθελεῖν")),
    claim("bursopoles-rho", 74, "historical", "The following phrase prints βυρσοπώλης, with ρσ rather than σσ. The same letter group is visible elsewhere on the page.",
        ("toronto-0074-body", "harvard-0075-body"), anchor("toronto", 74, 4, "βυσσοπώλης", "βυρσοπώλης")),
    claim("pikrotata-kappa", 74, "historical", "The verse hypothesis at the bottom of the right column prints πικρότατα, with κ.",
        ("toronto-0074-body",), anchor("toronto", 74, 11, "πιχρότατα", "πικρότατα")),
    claim("skatophagon-kappa", 74, "historical", "The last printed line reads εὐθέως τε σκατοφάγον, with κ after σ.",
        ("toronto-0074-body",), anchor("toronto", 74, 11, "σχατοφάγον", "σκατοφάγον")),
    claim("kleros-kappa", 251, "historical", "Birds hypothesisII prints τὸ μέγιστον ἦν κλῆρος. Only the source's κ is restored; the historical account is not factually revised.",
        ("toronto-0251-body", "harvard-0278-body"), anchor("toronto", 251, 4, "χλῆρος", "κλῆρος"), anchor("harvard", 278, 4, "κλῆς", "κλῆρος")),
    claim("sukophantein-kappa", 251, "historical", "The end of Birds hypothesisI prints καὶ συκοφαντεῖν, not the OCR χ.",
        ("toronto-0251-body",), anchor("toronto", 251, 3, "συχοφαντεῖν", "συκοφαντεῖν"), anchor("harvard", 278, 3, "συχορρατεῖν", "συκοφαντεῖν")),
    claim("alkibiaden-consonants", 251, "historical", "The Salaminia paragraph prints τὸν Ἀλκιβιάδην. The visible consonants are κ and β, rather than χ and δ.",
        ("toronto-0251-body", "harvard-0278-body"), anchor("toronto", 251, 7, "Ἀλχιδιάδην", "Ἀλκιβιάδην")),
    claim("ornisin-nu", 251, "historical", "Near the end of hypothesisII the print reads ὄρνισιν ἔδωκε. The word has ν rather than γ, with the visible initial accent retained.",
        ("toronto-0251-body",), anchor("toronto", 251, 6, "ὀργισιν", "ὄρνισιν"), anchor("harvard", 278, 4, "ὀρνίσιν", "ὄρνισιν")),
    claim("acharnians-heading", 43, "heading", "The centered play heading is ΑΧΑΡΝΗΣ. This correction remains a heading and supplies no lexical occurrence.",
        ("toronto-0043-heading", "harvard-0044-heading"), anchor("toronto", 43, 1, "ΑΧΑΡ", "ΑΧΑΡΝΗΣ")),
    claim("editorial-ephesteken-kappa", 431, "paratext", "The first variant in the ADNOTATIO prints ἐφέστηκεν Reg. The variant and its attribution remain editorial evidence, outside historical word counts.",
        ("toronto-0431-argument",), anchor("toronto", 431, 1, "ἐφέστηχεν", "ἐφέστηκεν")),
    claim("editorial-allois-number", 543, "paratext", "The note on513 prints παρὰ τοῖς ἄλλοις with no 11 following the word. This single attached extraction number is removed; manuscript variants and real printed reference numbers remain intact.",
        ("toronto-0543-note513",), anchor("toronto", 543, 20, "ἄλλοις11", "ἄλλοις")),
    claim("index-akamantidos-kappa", 768, "paratext", "The first index entry prints Ἀκαμαντίδος φυλῆς. The editorial index stays outside historical counts.",
        ("toronto-0768-index",), anchor("toronto", 768, 1, "Ἀχαμαντίδος", "Ἀκαμαντίδος")),
)

DEFERRED = (
    {"id": "archilochus-kiolaos-crasis", "page": 73,
     "reason": "The precise case, accent, and crasis of the κἸόλαος/κιόλαος sequence were not adjudicated. Retain all observed readings."},
    {"id": "missing-editorial-note443", "page": 543,
     "reason": "The separate Latin note beginning 443. Hoc scholion is omitted in both retained extractions. No insertion or newly invented text is authorized by this bounded spelling review."},
    {"id": "birds-historical-account", "page": 251,
     "reason": "The source's historical chronology and proper-name variants are not corrected from external knowledge."},
)


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build(root: Path) -> dict:
    """Expand authored claims against checked literal original inputs."""
    from repair_dubner_scholias import archived_inputs, source_records
    records = source_records(Path(root), archived_inputs(Path(root)))
    literal = {record["row"]["locus"]: record for record in records if not record["derived"]}
    claims, observations = [], []
    for spec in CLAIMS:
        current = {key: value for key, value in spec.items() if key != "anchors"}
        current.update(reviewed_at=REVIEWED_AT, printed_alternatives=[],
            decision="source-adjudicated-reading", independent_edition=False,
            contrary_readings=sorted({a["original"] for a in spec["anchors"]}), occurrences=[])
        for entry in spec["anchors"]:
            prefix = "scholia_aristoph_dubner" if entry["group"] == "toronto" else "platonius_duebner_scholaristoph1"
            locus = f"{prefix}_{entry['page']:04d}.{entry['row']}"
            record = literal[locus]
            row = record["row"]
            if record["source_page"] != entry["page"] or record["toronto_page"] != spec["toronto_page"]:
                raise ValueError("Reading observation has a different source page: " + locus)
            text = row["text"]
            if text.count(entry["original"]) != entry["count"]:
                raise ValueError("Changed or ambiguous reading preimage: " + locus)
            start = 0
            for ordinal in range(entry["count"]):
                start = text.index(entry["original"], start)
                end = start + len(entry["original"])
                observation = {
                    "id": f"{spec['id']}:{entry['group']}:{ordinal + 1}",
                    "claim_id": spec["id"], "path": record["path"],
                    "input_sha256": record["sha256"], "locus": locus,
                    "row_sha256": _sha(text), "start": start, "end": end,
                    "original": text[start:end], "corrected": entry["corrected"][ordinal] if isinstance(entry["corrected"], tuple) else entry["corrected"],
                    "original_text": text[start:end], "corrected_text": entry["corrected"][ordinal] if isinstance(entry["corrected"], tuple) else entry["corrected"],
                    "group": record["group"], "source_pdf": entry["group"],
                    "source_pdf_sha256": SOURCE_PDFS[entry["group"]]["sha256"],
                    "source_pdf_page": entry["page"], "toronto_page": spec["toronto_page"],
                    "scope": spec["scope"], "reviewed_at": REVIEWED_AT,
                    "evidence": spec["evidence"], "evidence_crops": spec["crops"],
                    "allowed_observed_readings": current["contrary_readings"],
                    "context_before": text[max(0, start - 35):start],
                    "context_after": text[end:end + 35],
                }
                observations.append(observation)
                current["occurrences"].append(observation["id"])
                start = end
        claims.append(current)
    identities = [item["id"] for item in observations]
    if len(identities) != len(set(identities)):
        raise ValueError("Repeated reading observation identity")
    per_row = {}
    for item in observations:
        key = (item["path"], item["locus"])
        per_row.setdefault(key, []).append(item)
    for values in per_row.values():
        previous = 0
        for item in sorted(values, key=lambda value: value["start"]):
            if item["start"] < previous:
                raise ValueError("Overlapping source reading corrections")
            previous = item["end"]
    return {
        "schema_version": 1, "reviewed_at": REVIEWED_AT,
        "qualification": "Bounded occurrence review of a frozen purposive ten-page sample, not exhaustive proofreading or a random OCR accuracy estimate. Source readings refer to two scans of one 1855 edition. Contrary OCR readings remain recoverable; no global character replacement is authorized.",
        "sources": SOURCE_PDFS,
        "page_reviews": [{"toronto_page": page, "role": role, "assessment": assessment}
                         for page, role, assessment in PAGE_REVIEWS],
        "claims": claims, "observations": observations, "deferred": list(DEFERRED),
        "inputs": dict(sorted({record["path"]: record["sha256"] for record in records if not record["derived"]}.items())),
    }
