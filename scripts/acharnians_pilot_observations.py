"""Scan observations for a frozen, purposive ten-page source audit.

These are observations and proposed readings, not admitted text corrections.
Every original reading remains served unchanged. Source regions are provisional
page-level measurements and do not supply a work carve or lexical eligibility.
"""

PAGES = (
    (9, "edition_title", "Title identifies Dübner, Firmin-Didot, Paris, 1855; the volume includes scholia, critical notes, and indexes."),
    (43, "acharnians_start", "Printed page 1: ΑΧΑΡΝΗΣ, two hypotheses, then SCHOLIA IN ACHARNENSES; the right column continues the first hypothesis before the second begins."),
    (58, "acharnians_midpoint", "Printed page 16: scholia 507–542, with quoted verse, manuscript sigla, and retained print hyphenation; no separate lower apparatus block."),
    (73, "acharnians_end", "Printed page 31 ends the Acharnians scholia at verse 1232; verse 1230 prints τήνελλα as one word."),
    (74, "next_play_start", "Printed page 32 starts ΙΠΠΗΣ and its hypotheses. This is Knights material, not Acharnians."),
    (251, "later_plays_midpoint", "Printed page 209 starts ΟΡΝΙΘΕΣ and its hypotheses. This is Birds material, not Acharnians."),
    (431, "annotation_start", "Printed page 389: ADNOTATIO IN SCHOLIASTAS ARISTOPHANIS, ACHARNENSES; mixed Latin discussion and Greek variants belong to the editor's critical annotation."),
    (543, "annotation_midpoint", "Printed page 501: LYSISTRATAE, mixed Latin critical discussion and Greek variant readings. Several displayed source notes are absent from the served extraction."),
    (657, "index_title", "Printed page 615 identifies INDEX NOMINUM ET RERUM, INDEX AUCTORUM, and INDEX GRAECUS; this is an editorial index section."),
    (768, "last_served_page", "Printed page 726: INDEX GRAECUS, three columns of words, explanations, and references to multiple plays; the two-column OCR provenance does not describe this layout."),
)

SELECTION = (
    "Purposive source-role sample fixed before compiling metrics, not a random "
    "OCR accuracy sample: edition title; first, midpoint, and last Acharnians "
    "pages (43, (43+73)//2, 73); first subsequent play; midpoint of the later "
    "play block (74+429)//2; first and midpoint of the critical annotation "
    "(431, (431+656)//2); index title; last served page."
)

# Whole-page regions are an assessment scaffold only. A future work/role split
# must review every boundary and intra-page role and preserve historical loci.
REGIONS = (
    (1, 42, "front_matter", "Front matter and grammatical prolegomena"),
    (43, 73, "acharnians", "Acharnians hypotheses and scholia"),
    (74, 430, "other_plays", "Subsequent plays' hypotheses and scholia"),
    (431, 656, "critical_annotation", "Dübner's critical annotation"),
    (657, 776, "indexes", "Editorial indexes"),
)

OBSERVATIONS = (
    {"id": "truncated-play-heading", "page": 43, "locus": "scholia_aristoph_dubner_0043.1",
     "original": "ΑΧΑΡ", "proposed": "ΑΧΑΡΝΗΣ", "kind": "heading_truncation",
     "evidence": "The complete centered heading on the pinned scan reads ΑΧΑΡΝΗΣ. A heading is not continuous scholion text."},
    {"id": "missing-eta", "page": 43, "locus": "scholia_aristoph_dubner_0043.6",
     "original": "Ἀθναίοις", "proposed": "Ἀθηναίοις", "kind": "omitted_letter",
     "evidence": "Right column, continuation of hypothesis I, prints ἐν Ἀθηναίοις διὰ Καλλιστράτου."},
    {"id": "mixed-alphabet", "page": 58, "locus": "scholia_aristoph_dubner_0058.9",
     "original": "σίχuos", "proposed": None, "kind": "mixed_greek_latin",
     "evidence": "The scholion on verse 520 is wholly Greek at this position; Latin u/o/s in the extraction cannot be a diplomatic transcription. Exact accents and letters require occurrence review before correction."},
    {"id": "fragmented-interjection", "page": 73, "locus": "scholia_aristoph_dubner_0073.9",
     "original": "τὴν ελλα", "proposed": "τήνελλα", "occurrences": 3, "kind": "false_word_split",
     "evidence": "Verse 1230 prints τήνελλα three times, as lemma, explanation, and quoted Archilochus. The independent OCR pass embedded in the same PDF also retains the single word."},
    {"id": "knights-misattribution", "page": 74, "locus": "scholia_aristoph_dubner_0074.2",
     "original": "Τὸ δράμα τοῦτο ποιεῖται εἰς Κλέωνα", "proposed": None, "kind": "wrong_work_scope",
     "evidence": "The page heading ΙΠΠΗΣ establishes the Knights hypothesis. This is legitimate historical Greek assigned to the wrong work, not OCR noise."},
    {"id": "editorial-variants", "page": 431, "locus": "scholia_aristoph_dubner_0431.1",
     "original": "ἐφέστηχεν Reg.", "proposed": None, "kind": "editorial_apparatus",
     "evidence": "ADNOTATIO begins here; Reg., Ald., om., transponi mavult, and the manuscript variants belong to the critical annotation and must remain attributed variants."},
    {"id": "missing-editorial-note", "page": 543, "locus": "scholia_aristoph_dubner_0543.4",
     "original": "439, 12 καὶ Ἄγραυλος Brunckius. δὲ ἡ Ἄθ. Put.", "proposed": None, "kind": "omitted_source_note",
     "evidence": "Immediately after this note, the scan has the separate note beginning 443. Hoc scholion cum additamento Raven- and ending et schol. 447 omittit. It is absent between current rows .4 and .5. This matters for evidence preservation, not admission as scholion text."},
    {"id": "attached-numbers", "page": 543, "locus": "scholia_aristoph_dubner_0543.20",
     "original": "ἄλλοις11", "proposed": None, "kind": "numeric_suffix_noise",
     "evidence": "The source note on verse 513 reads παρὰ τοῖς ἄλλοις; 11 is not printed after this word. Similar attached numbers need geometric source review, not a blanket digit deletion."},
    {"id": "index-counted-as-text", "page": 768, "locus": "scholia_aristoph_dubner_0768.1",
     "original": "Χολαργεῖς Ἀχαμαντίδος φυλῆς Ach. 855.", "proposed": None, "kind": "editorial_index",
     "evidence": "The INDEX GRAECUS page is a three-column editorial index. Its Greek headwords duplicate and point into multiple plays; they are not a new continuous Acharnians witness."},
)
