#!/usr/bin/env python3
"""Re-key the Justinian Novellae OCR from scan-page loci to novel-number loci.

The served flavius-justinianus-imperator.novellae.jsonl (Schoell-Kroll, Corpus
Iuris Civilis III, Berlin 1895; edition qwen36-justinian_novellae_schoell) was
delivered page-keyed: `justinian_novellae_schoell_<scan>.<seg>`. Every citation
scheme for the Novellae is novel-based (LSJ cites `Nov. 4.2` = novel.chapter),
so the page keys made all of those citations unresolvable. This script re-keys
each passage to its novel:

    <novel>.p<printed>.<seg>     Greek novels 1-168 (printed = Schoell-Kroll
                                 page number; seg = the delivered segment id)
    ed<n>.p<printed>.<seg>       the 13 Edicts printed after the novels
                                 (pp. 759-795, their own Α-ΙΓ numbering)
    app.p<printed>.<seg>         Appendix constitutionum dispersarum (pp. 797-)
    praef.<scan>.<seg>           Latin front matter before printed p. 1
                                 (praefatio + conspectus; roman-paginated in
                                 the print, so the scan leaf number is kept)

TEXT IS NEVER TOUCHED: only the locus field changes, row order is preserved,
and the script asserts per-row text identity plus whitespace-insensitive
equality of the concatenated text before/after. The mapping is reversible by
formula: scan = printed + 30 (novel/ed/app keys) or the literal scan number
(praef keys); seg is carried through unchanged.

Novel boundaries: NOVEL_STARTS below maps each novel/edict to its printed
start page + line + a heading skeleton. It was derived from the per-page
structural headings of the TLG-E digitization of the SAME Schoell-Kroll
edition (TLG 2734.013 is cited by Page.line of this print), with two
mechanical repairs for numerals the digitization dropped (stigma [+6] and
koppa [+90], validated by strict monotonicity), and cross-checked against the
OCR's own bare-numeral heading rows, which agree on a constant scan-printed
offset of 30 across the whole volume (novel 2 through edict 4). The 16 novels
missing from the table (LATIN_ONLY) are the ones Schoell-Kroll transmits in
Latin only; they get no Greek heading, their pages stay keyed to the
preceding novel, and LSJ cites none of them.

Boundary pages (a novel starting mid-page) are split at the detected heading
row (bare Greek-numeral row and/or caps title row matching the heading
skeleton); when no heading row is detectable and the novel starts below the
top of the page, the boundary falls back to the next page and the decision is
logged in the audit record.

The same run also repairs data/ocr_works.json: the upstream OCR pipeline
delivered this batch under the mis-slug flavius-justinianus-imperator.
contra-monophysitas (TLG 2734.001 is Contra monophysitas, which the scan
never contained) and later re-scoped the corpus file to the novellae slug
(see data/work_id_aliases.json) without updating its ocr_works rows; the
stale contra-monophysitas row and the small gap-fill novellae row (the 8
ocr_dpi=400 passages) are merged into one correct novellae row with stats
recomputed from the corpus file.

Audit: data/corpus_changes/flavius-justinianus-imperator.novellae.novel-rekey
.json (old/new sha256, detection + boundary log, per-scan-page novel map, the
replaced ocr_works rows, and the inverse-mapping formula).

Usage:
  python3 scripts/rekey_novellae_by_novel.py            # check only
  python3 scripts/rekey_novellae_by_novel.py --apply    # write files
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import unicodedata
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SLUG = "flavius-justinianus-imperator.novellae"
OLD_SLUG = "flavius-justinianus-imperator.contra-monophysitas"
CTS = "urn:cts:greekLit:tlg2734.tlg013"
EDITION = "qwen36-justinian_novellae_schoell"
RUN_BASE = "justinian_novellae_schoell"
CORPUS = REPO / "data" / "corpus" / f"{SLUG}.jsonl"
CHANGES = REPO / "data" / "corpus_changes"
OCR_WORKS = REPO / "data" / "ocr_works.json"
DATE = "2026-07-31"

OFFSET = 30              # scan page = printed page + 30, constant (verified)
FIRST_PRINTED_SCAN = 31  # scan leaf of printed p. 1; earlier leaves = praef
APPENDIX_PAGE = 797      # Appendix constitutionum dispersarum (pp. 797-798)

OLD_LOCUS = re.compile(rf"^{RUN_BASE}_(\d{{4}})\.(\d+)$")
GREEK = re.compile(r"[Ͱ-Ͽἀ-῿]")

# {novel id: (printed start page, start line on page, heading skeleton)}.
# Novels "1".."168" (Greek collection numbering, the numbering LSJ cites);
# "ed1".."ed13" the Edicts. Derivation: see module docstring.
NOVEL_STARTS: dict[str, tuple[int, int, str]] = {
    "1": (1, 1, "περιτωνκληρονομωνκαιτουφαλκιλιουαυτοκρατ"),
    "2": (10, 4, "περιτουμηεπιλεγεσθαιτασδευτερογαμουσασγυ"),
    "3": (18, 4, "περιτουωρισμενονειναιτοναριθμοντωνκληρικ"),
    "4": (24, 7, "περιτουτουσδανειστασπροτερονχωρεινκατατω"),
    "5": (28, 8, "ηεριμοναστηριωνκαιμοναχωνκαιηγουμενωναυτ"),
    "6": (35, 16, "περιτουπωσδειχειροτονεισθαιτουσεπισκοπου"),
    "7": (48, 5, "περιτουμηεκποιεισθαιηανταλλαττεσθαιταεκκ"),
    "8": (64, 4, "ηδιαταξισπεριτουτουσαρχοντασχωριστησοιασ"),
    "10": (92, 5, "περιτωνρεφερενδαριωναυτοκρατωριουστινιαν"),
    "12": (95, 1, "περιαθεμιτογαμιωναυτοκρατωριουστινιανοσα"),
    "13": (99, 14, "περιτωνπραιτορωντουδημουαυτοκρατωριουστι"),
    "14": (105, 20, "περιτουμηειναιπορνοβοσκουσενμηδενιτοπωιτ"),
    "15": (109, 5, "περιτωνεκδικωνιμπιυστινιανυσαυγιοηαννιππ"),
    "16": (115, 20, "περιτουτουσκληρικουσεξετερασεκκλησιασμετ"),
    "17": (117, 12, "μανδαταπρινξιπισενονοματιτουδεσποτουιησο"),
    "18": (127, 10, "ωστετηννομιμονμοιραντωνπαιδωνειναιειμεχρ"),
    "19": (138, 17, "περιτωνπροτωνπροικωιωνσυμβολαιωντικτομεν"),
    "20": (140, 27, "περιτωνυπηρετουμενωνοφφικιωνεντοισσακροι"),
    "21": (144, 28, "περιαρμενιωνωστεκαιαυτουσενπασιτοισρωμαι"),
    "22": (146, 25, "περιτωνδευτερογαμουντωνοαυτοσβασιλευσιωα"),
    "24": (189, 1, "περιτουπραιτωροσπισιδιασαυτοκρατωριουστι"),
    "25": (195, 28, "περιτουπραιτωροσλυκαονιασαυτοκρατωριουστ"),
    "26": (203, 1, "περιτουπραιτωροσθραικησαυτοκρατωριουστιν"),
    "27": (209, 20, "περιτουκομητοσισαυριασαυτοκρατωριουστινι"),
    "28": (212, 1, "περιτουμοδερατωροσελενοποντουοαυτοσβασιλ"),
    "29": (218, 20, "περιτουπραιτωροσπαφλαγονιασοαυτοσβασιλευ"),
    "30": (223, 27, "περιτουανθυπατουκαππαδοκιασοαυτοσβασιλευ"),
    "31": (235, 14, "περιδιατυπωσεωστωντεσσαρωναρχοντωναρμενι"),
    "32": (239, 25, "περιτουμηδεναδανειζονταγεωργωικρατειντην"),
    "38": (246, 1, "περιβουλευτωνωστεενναουγκιονκαταλιμπανει"),
    "39": (253, 6, "περιαποκαταστασεωσπροικιμαιωνκαιπρογαμια"),
    "40": (258, 14, "περιτουτηνεκκλησιαντησαγιασαναστασεωσεκπ"),
    "41": (262, 5, "ηδιαταξισπροσβονονκοιαιστωραεχερξιτουτατ"),
    "42": (263, 8, "περιτησκαθαιρεσεωσανθιμουκαισεβηρουκαιπε"),
    "43": (269, 5, "περιτωνεργαστηριωνκωνσταντινουπολεωσωστε"),
    "44": (273, 18, "περιτωνσυμβολαιογραφωνκαιπεριτουταπρωτοκ"),
    "45": (277, 14, "περιτουμηελευθερωθηναιβουλευτικηστυχησιο"),
    "46": (280, 1, "περιτηστωνεκκλησιαστικωνακινητωνπραγματω"),
    "47": (283, 1, "περιτουπροταττεσθαιτοτουβασιλεωσονομαεντ"),
    "48": (286, 1, "περιορκουδοθεντοσπαρατουτελευτωντοσενεκε"),
    "49": (288, 1, "περιτωνεισιοντωντηνεκκλητονρεωνκαιπεριιδ"),
    "50": (293, 7, "ηδιαταξισταττειτασεκκλητουσαποτωνπεντεεπ"),
    "51": (295, 1, "περιτουτασεπισκηνησμητεεγγυηνμητεορκοναπ"),
    "52": (297, 1, "περιτουμητεπροσωπουμητεπραγματοσμητεχρυσ"),
    "53": (299, 1, "περιτουτονενεπαρχιαισεισυπερορ ιονδικαστ".replace(" ", ""),),
    "54": (306, 1, "περιτουτηντωνεναπογραφωνδιαταξινχωρανεχε"),
    "55": (308, 19, "περιαμειψεωσπραγματωνεκκλησιαστικωνκαιεμ"),
    "56": (311, 1, "ωστετακαλουμεναεμφανιστικατωνκληρικωνεπι"),
    "57": (312, 14, "περικληρικωναποσταντωντησκαταυτουσεκκλησ"),
    "58": (314, 17, "περιτουενιδιωτικοισοικοισιερανμυσταγωγια"),
    "59": (316, 17, "περιτησοφειλουσησγινεσθαιδαπανησειστασ τω".replace(" ", ""),),
    "60": (325, 1, "περιτουτουστελευτωντασηγουνταλειψανααυτω"),
    "61": (329, 10, "περιτουτηνπρογαμουδωρεανμητευποτιθεσθαιμ"),
    "63": (334, 1, "περικαινοτομιωντησεπιθαλασσαναποψεωσοαυτ"),
    "64": (336, 1, "περιτωνκηπουρωνοαυτοσβασιλευσλογγινωιτωι"),
    "66": (340, 1, "περιτουτασγινομενασνεασδιαταξεισμετατηνε"),
    "67": (344, 1, "περιτουμηδενακτιζεινευκτηριονοικονχωρισγ"),
    "68": (347, 5, "ωστετηνδιαταξιντουευσεβεστατουβασιλεωστη"),
    "69": (349, 1, "περιτουπαντασυπακουειντοισαρχουσιτωνεπαρ"),
    "70": (355, 1, "περιβουλευτωνωστεαυτουστοτετιμησπραεφεξτ"),
    "71": (357, 1, "ωστετουσιλλουστριουσεντοισχρηματικοισδιε"),
    "72": (358, 14, "περικουρατορωνκαικηδεμονωνκαιτηστωννεωνφ"),
    "73": (363, 7, "περιτουπωσχρηεπιτιθεσθαιτοπιστοντοισπαρα"),
    "74": (370, 7, "περιτωνπαιδωνπωσχρηνοεισθαιαυτουσγνησιου"),
    "76": (379, 1, "ηδιαταξισερμηνευειτηνπροτερανδιαταξιντην"),
    "77": (381, 10, "ηδιαταξισπεριτουτουσομνυοντασκατατουθεου"),
    "78": (383, 8, "ωστετουσαπελευθερουστουλοιπουμηδεισθαιδι"),
    "79": (388, 1, "παρατισιχρηδικαζεσθαιμοναχουσκαιασκητρια"),
    "80": (390, 15, "περιτουθυαεσιτοροσοαυτοσβασιλευσιωαννηιτ"),
    "81": (397, 6, "ηδιαταξισηδιατωναξιωματωνκαιτησεπισκοπησ"),
    "82": (400, 9, "περιτωνδικαστωνκαιωστεμεθορκουμηαιρεισθα"),
    "83": (409, 1, "περιτουτουσκληρικουστοισεπισκοποισαποκρι"),
    "84": (411, 10, "περιτωνομοπατριωνκαιομομητριωναδελφωναυτ"),
    "85": (414, 10, "περιτωνοπλωναυτοκρατωριουστινιανοσαυγουσ"),
    "86": (419, 1, "ωστευπερτιθεμενουστουσαρχοντασακουειντων"),
    "87": (423, 8, "περιμορτισκαυσαδωρεασεκβουλευτωνγινομενη"),
    "88": (425, 14, "περιπαρακαταθηκησκαιδιαμαρτυριασενοικωνκ"),
    "89": (428, 14, "περιτωννοθωναυτοκρατωριουστινιανοσαυγουσ"),
    "90": (445, 7, "περιμαρτυρωνιμπιυστινιανυσαιωαννηιτωιενδ"),
    "91": (454, 1, "ωστεαπαιτησεωσουσησπροικοσπρωτηστεκαιδευ"),
    "92": (457, 10, "περιτωνεισπαιδασαμετρωνδωρεωνοαυτοσβασιλ"),
    "93": (459, 1, "περιεφεσεωνωστεεικινουμενησδικησπαραεφετ"),
    "94": (461, 6, "ωστεακωλυτωσεπιτροπευειντασμητερασ τωνπαι".replace(" ", ""),),
    "95": (464, 5, "ωστετουσαρχοντασπεντηκονταημερασμετατηνα"),
    "96": (467, 1, "περιτωνεκβιβαστωνκαιτωναιτιωμενωνκαιαντα"),
    "97": (469, 1, "περιισοτητοσπροικοστεκαιπρογαμουδωρεασεχ"),
    "98": (478, 11, "ηδιαταξισωστεμητετονανδρατοεκτησπροικοσμ"),
    "99": (482, 1, "περιαλληλεγγυωνοαυτοσβασιλευσιωαννηιεπαρ"),
    "100": (484, 1, "περιτουχρονουτησεπιτηιπροικιαναργυριασοα"),
    "101": (487, 17, "περιβουλευτωνεγραφηιωαννηιτωιενδοξοτατωι"),
    "102": (492, 24, "περιτουμοδερατωροσαραβιασοαυτοσβασιλευσι"),
    "103": (496, 1, "περιτουανθυπατουπαλαιστινησεγραφηιωαννηι"),
    "105": (500, 26, "περιτωνυπατωνεγραφηστρατηγιωιτωιενδοξοτα"),
    "106": (507, 27, "περιναυτικωντοκωνοαυτοσβασιλευσιωαννηιεπ"),
    "107": (510, 16, "περιβουλησεωντωνειστουσπαιδασγενομενωνοα"),
    "108": (513, 18, "περιτωναποκαταστασεωνοαυτοσβασιλευσβασσω"),
    "109": (517, 1, "περιαιρετικωντηιπιστειγυναικωνοαυτοσβασι"),
    "110": (520, 10, "περιτωντοκωνοαυτοσβασιλευσιωαννηιεπαρχωι"),
    "111": (521, 6, "ηδιαταξισαναιρουσατηντωνεκατονενιαυτωνπα"),
    "112": (523, 13, "περιτωνλιτιγιοσωνκαιπεριτησοφειλουσησγεν"),
    "113": (529, 5, "ηδιαταξισωστεενμεσωιδικησμηγινεσθαιθειου"),
    "115": (534, 1, "ηδιαταξισεχεικεφαλαιατοπρωτονεντηιεξετασ"),
    "116": (549, 9, "περιστρατιωτωνοαυτοσβασιλευσθεοδοτωιεπαρ"),
    "117": (551, 5, "περιδιαφορωνκεφαλαιωνκαιλυσεωσγαμουοαυτο"),
    "118": (567, 1, "διαταξισαναιρουσατααδγνατικαδικαιακαιτυπ"),
    "119": (573, 1, "ωστετηνδιατουσγαμουσδωρεανιδικονσυναλλαγ"),
    "120": (578, 1, "περιεκποιησεωσκαιεμφυτευσεωσεκκλησιαστικ"),
    "121": (591, 8, "περιτουτασμερικασκαταβολαστωντοκωνειστοδ"),
    "122": (592, 18, "ιδικτονπεριδιατυπωσεωστεχνιτων"),
    "123": (593, 13, "περιεκκλησιαστικωνδιαφορωνκεφαλαιωνοαυτο"),
    "124": (625, 16, "περιτωνδικαζομενωνοαυτοσβασιλευσπετρωιεπ"),
    "125": (630, 1, "περιδικαστωνοαυτοσβασιλευσπετρωιεπαρχωιπ"),
    "126": (631, 11, "ισονθειουνομουπεριεκκλητωνοαυτοσβασιλευσ"),
    "127": (633, 1, "περιαδελφοπαιδωνκληρονομουντωναματοισανι"),
    "128": (636, 9, "περιτηστωνδημοσιωνανυσεωσκαικαταβολησκαι"),
    "129": (647, 1, "περισαμαρειτωνοαυτοσβασιλευσαδδαιωιεπαρχ"),
    "130": (650, 12, "περιπαροδουστρατιωτωνοαυτοσβασιλευσπετρω"),
    "131": (654, 15, "περιεκκλησιαστικωνκανονωνκαιπρονομιωνοαυ"),
    "132": (665, 1, "ιδικτονπεριπιστεωσκωνσταντινουπολιταισ"),
    "133": (666, 7, "περιμοναχωνκαιασκητριωνκαιδιαγωγησαυτωνα"),
    "134": (676, 13, "περιτοποτηρητωνκαιμοιχευομενωνγυναικωνκα"),
    "135": (690, 1, "περιτουμηαναγκαζεσθαιτινασεκστασιωιχρησα"),
    "136": (691, 6, "περιαργυροπρατικωνσυναλλαγματωνοαυτοσβασ"),
    "137": (695, 1, "περιχειροτονιασεπισκοπωνκαικληρικωνενονο"),
    "139": (700, 11, "συγχωρησισποινησπεριτωναθεμιτωνγαμωνενον"),
    "140": (701, 9, "ωστεδυνασθαικατασυναινεσινλυειντονγαμονα"),
    "141": (703, 22, "ιδικτονκωνσταντινουπολιταισιουστινιανουπ"),
    "142": (705, 1, "περιτωνευνουχιζοντωναυτοκρατωριουστινιαν"),
    "144": (709, 1, "περισαμαρειτωναυτοκρατωριουστινοσδιομηδε"),
    "145": (711, 1, "ωστετουλοιπουμηδεμιαναδειανεχειντονδουκα"),
    "146": (714, 6, "περιεβραιωνοαυτοσβασιλευσαρεοβινδωιτωιεν"),
    "147": (718, 6, "ωστετασεποφειλομενασλοιπαδαστοισεπαρχοισ"),
    "148": (722, 1, "περισυγχωρησεωσλοιπαδωνδημοσιωνιουστινοσ"),
    "149": (723, 20, "περιτουπροικατουστωνεπαρχιωναρχοντασγινε"),
    "151": (726, 32, "περιτουμηπαρασταθηναιηδιαχθηναιβουλευτην"),
    "152": (727, 12, "περιτουτουσεπιδημοσιοισπροιοντασθειουστυ"),
    "153": (728, 13, "περιτωνχαμευρετωνβρεφωνοαυτοσβασιλευσηλι"),
    "154": (729, 17, "περιτωνενοσροηνηαθεμιτωσσυναλλαττοντωναυ"),
    "155": (731, 1, "περιτουδειντασμητερασυποκεισθαιεπιτροπικ"),
    "156": (733, 1, "περιτησμεριζομενησγονηστωνγεωργωνοαυτοσβ"),
    "157": (733, 17, "περιτωνεναλλοτριοισχωριοισγαμουντωνγεωργ"),
    "158": (734, 19, "περιτουπαραπεμπεσθαιτοτησδιασκεψεωσδικαι"),
    "159": (736, 1, "ωστετασυποκαταστασεισμεχριενοσβαθμουιστα"),
    "160": (744, 1, "ισονθειουπραγματικουτυπουαυτοκρατωριουστ"),
    "161": (745, 1, "περιτωναρχοντων"),
    "162": (747, 1, "θειοστυποσκαταπεμφθεισδομνικωιτωιενδοξοτ"),
    "163": (749, 16, "περικουφισμουδημοσιων"),
    "164": (751, 15, "περικληρονομιων"),
    "165": (752, 20, "γενικοστυποσπεριαποψεωσθαλασσησγραφεισδο"),
    "166": (753, 1, "περιαπορωνεπιβολησφλαβιοσθεοδωροσπετροσδ"),
    "167": (754, 13, "γενικοσμεγιστοστυποσπεριτουπωσδειστελλεσ"),
    "168": (755, 17, "περιεπιβολων"),
    "ed1": (759, 3, "ιδικτονγραφεντοισαπανταχουγησθεοφιλεστατ"),
    "ed2": (759, 6, "περιτουμηπαρεχειντουσαρχοντασασυλιασλογο"),
    "ed3": (760, 23, "περιτηστωναρμενιωνδιαδοχησοαυτοσβασιλευσ"),
    "ed4": (761, 19, "περιτησαρχησφοινικησλιβανησιασοαυτοσβασι"),
    "ed5": (763, 7, "πδιαταξισαναιρουσατηντωνεκατονενιαυτωνπα"),
    "ed6": (763, 10, "ιδικτοντουευσεβεστατουημωνδεσποτουιουστι"),
    "ed7": (763, 13, "τυποσπραγματικοσπεριαργυροπρατικωνσυναλλ"),
    "ed8": (768, 1, "περιτουβικαριουτησποντικησοαυτοσβασιλευσ"),
    "ed9": (772, 4, "περιαργυροπρατικωνσυναλλαγματωναυτοκρατω"),
    "ed10": (776, 21, "περιταξεωτων"),
    "ed11": (777, 13, "ωστεμηδεμιαναδειανεχειντουσπαραιγυπτιοισ"),
    "ed12": (779, 1, "περιελλησποντου"),
    "ed13": (780, 1, "περιτησαλεξανδρεωνκαιτωναιγυπτιακωνεπαρχ"),
}

# Novels Schoell-Kroll transmits in LATIN only (no Greek heading exists; their
# pages stay with the preceding Greek novel; LSJ cites none of them).
LATIN_ONLY = [9, 11, 23, 33, 34, 35, 36, 37, 62, 65, 75, 104, 114, 138,
              143, 150]

_ONES = {"Α": 1, "Β": 2, "Γ": 3, "Δ": 4, "Ε": 5, "Ϛ": 6, "Ζ": 7, "Η": 8,
         "Θ": 9}
_TENS = {"Ι": 10, "Κ": 20, "Λ": 30, "Μ": 40, "Ν": 50, "Ξ": 60, "Ο": 70,
         "Π": 80, "Ϟ": 90}


def greek_numeral(tok: str) -> int | None:
    """Strict Greek numeral value of a bare token, else None."""
    tok = unicodedata.normalize("NFC", tok.strip().rstrip("."))
    if not tok:
        return None
    v, seen = 0, []
    for ch in tok:
        if ch == "Ρ":
            v += 100
            seen.append(100)
        elif ch in _TENS:
            v += _TENS[ch]
            seen.append(_TENS[ch])
        elif ch in _ONES:
            v += _ONES[ch]
            seen.append(_ONES[ch])
        else:
            return None
    if seen != sorted(seen, reverse=True):
        return None
    return v or None


def numeral_candidates(tok: str) -> set[int]:
    """Values a garbled OCR heading numeral could stand for: as-is and with
    the classic confusions seen in this run (Ρ read as Π; stigma lost)."""
    out: set[int] = set()
    for t in {tok, ("Ρ" + tok[1:]) if tok[:1] == "Π" else tok}:
        v = greek_numeral(t)
        if v:
            out.update((v, v + 6))
    return out


def skel(s: str) -> str:
    """Lowercased, diacritic-free Greek letter skeleton (final sigma folded,
    so caps and lowercase text skeletonize identically)."""
    out = []
    for c in unicodedata.normalize("NFD", s.lower()):
        if unicodedata.category(c).startswith("L") \
                and "GREEK" in unicodedata.name(c, ""):
            out.append(unicodedata.normalize("NFD", c)[0])
    return "".join(out).replace("ς", "σ")


def caps_ratio(s: str) -> float:
    letters = [c for c in s if GREEK.match(c) and c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def title_matches(row_skel: str, title_skel: str) -> bool:
    if len(row_skel) < 6:
        return False
    a, b = row_skel[:16], title_skel[:16]
    if title_skel.startswith(row_skel[:10]) or row_skel.startswith(b[:10]):
        return True
    if difflib.SequenceMatcher(None, a, b).ratio() >= 0.72:
        return True
    # heading rows whose opening words the OCR dropped or garbled (e.g. novel
    # 165's "ΠΕΣ ΑΠΟΤΕΩΣ ΘΑΛΑΣΗΣΗΣ..."): accept a caps row sharing a long
    # contiguous block with the heading skeleton anywhere inside it
    m = difflib.SequenceMatcher(None, row_skel[:48], title_skel)
    return m.find_longest_match().size >= 8


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def greek_chars(s: str) -> int:
    return len(GREEK.findall(s))


def read_rows() -> tuple[list[dict], bytes]:
    raw = CORPUS.read_bytes()
    rows = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l.strip()]
    return rows, raw


def dump_rows(rows: list[dict]) -> bytes:
    return ("\n".join(json.dumps(r, ensure_ascii=False) for r in rows)
            + "\n").encode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="re-key the Novellae by novel")
    ap.add_argument("--apply", action="store_true",
                    help="write files; default is check-only")
    args = ap.parse_args()

    rows, raw = read_rows()
    # Serializer must reproduce the delivered bytes exactly, so that the only
    # diff the re-key introduces is the locus field.
    assert dump_rows(rows) == raw, "serializer does not round-trip the corpus file"

    parsed = []          # (scan_page, seg) per row, in file order
    for r in rows:
        m = OLD_LOCUS.match(r["locus"])
        if not m:
            raise SystemExit(f"unexpected locus (already re-keyed?): {r['locus']}")
        parsed.append((int(m.group(1)), int(m.group(2))))

    by_page: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for (p, s), r in zip(parsed, rows):
        by_page[p].append((s, r["text"]))
    for p in by_page:
        by_page[p].sort()

    # --- 1. offset verification: bare-numeral heading rows in the OCR must
    # agree with NOVEL_STARTS at scan = printed + OFFSET -------------------
    numeral_anchors, title_anchors = [], []
    for nid, (pp, _line, tskel) in NOVEL_STARTS.items():
        scan = pp + OFFSET
        want = int(nid[2:]) if nid.startswith("ed") else int(nid)
        for s, t in by_page.get(scan, []):
            ts = t.strip()
            if len(ts) <= 8 and want in numeral_candidates(ts):
                numeral_anchors.append((nid, scan, s, ts))
                break
        for s, t in by_page.get(scan, []):
            if caps_ratio(t) >= 0.6 and title_matches(skel(t), tskel):
                title_anchors.append((nid, scan, s))
                break
    detected = {a[0] for a in numeral_anchors} | {a[0] for a in title_anchors}
    print(f"concordance: {len(NOVEL_STARTS)} Greek headings "
          f"({len([k for k in NOVEL_STARTS if not k.startswith('ed')])} novels"
          f" + {len([k for k in NOVEL_STARTS if k.startswith('ed')])} edicts);"
          f" {len(LATIN_ONLY)} Latin-only novels have none")
    print(f"in-OCR confirmation at offset {OFFSET}: numeral row {len(numeral_anchors)}, "
          f"caps-title row {len(title_anchors)}, either {len(detected)}")
    if len(detected) < 100:
        raise SystemExit("ABORT: fewer than 100 novel headings confirmed in "
                         "the OCR - not shipping this keying")

    # --- 2. split points: (scan_page, first_seg, segment id) ---------------
    entries: list[tuple[int, int, str]] = [(0, 0, "praef")]
    boundary_log: list[dict] = []
    order = sorted(NOVEL_STARTS, key=lambda k: NOVEL_STARTS[k][:2])
    prev_split: dict[int, int] = {}    # scan page -> seg of last split there
    for nid in order:
        pp, line, tskel = NOVEL_STARTS[nid]
        scan = pp + OFFSET
        segs = by_page.get(scan, [])
        floor = prev_split.get(scan, -1)
        split_seg = None
        how = None
        for s, t in segs:
            if s <= floor:
                continue
            rs = skel(t)
            # caps heading row; or a lowercase-set heading line (some novels
            # open straight into the inscription in lower case), which must
            # share a longer contiguous block with the heading skeleton and
            # must not be an apparatus line quoting the rubric
            is_apparatus = "||" in t or "]" in t or " ind." in t
            hit = (caps_ratio(t) >= 0.6 and title_matches(rs, tskel)) or \
                (not is_apparatus
                 and difflib.SequenceMatcher(None, rs[:60], tskel)
                 .find_longest_match().size >= 12)
            if hit:
                split_seg, how = s, "title-row"
                # a short bare-numeral row just before the title belongs to
                # the heading too
                prevs = [ps for ps, _ in segs if ps < s and ps > floor]
                if prevs:
                    cand = max(prevs)
                    ctext = dict(segs)[cand].strip()
                    if 0 < len(ctext) <= 8 and not any(
                            c.isalpha() and c.islower() for c in ctext):
                        split_seg = cand
                break
        if split_seg is None:
            for s, t in segs:
                if s <= floor:
                    continue
                ts = t.strip()
                want = int(nid[2:]) if nid.startswith("ed") else int(nid)
                if len(ts) <= 8 and want in numeral_candidates(ts):
                    split_seg, how = s, "numeral-row"
                    break
        if split_seg is None:
            if line <= 3:
                nxt = [s for s, _ in segs if s > floor]
                if nxt:
                    split_seg, how = min(nxt), "top-of-page"
        if split_seg is None:
            entries.append((scan + 1, 0, nid))
            boundary_log.append({"segment": nid, "scan_page": scan,
                                 "printed_page": pp, "start_line": line,
                                 "decision": "heading row not detected; "
                                             "segment starts on the next page"})
        else:
            entries.append((scan, split_seg, nid))
            prev_split[scan] = split_seg
            if (scan, split_seg) != (scan, min(s for s, _ in segs)):
                boundary_log.append({"segment": nid, "scan_page": scan,
                                     "printed_page": pp, "split_seg": split_seg,
                                     "how": how})
    entries.append((APPENDIX_PAGE + OFFSET, 0, "app"))
    entries.sort(key=lambda e: (e[0], e[1]))
    keys = [(e[0], e[1]) for e in entries]
    assert keys == sorted(set(keys)), "split points not strictly increasing"

    # --- 3. assign + re-key -----------------------------------------------
    def segment_of(page: int, seg: int) -> str:
        if page < FIRST_PRINTED_SCAN:
            return "praef"
        i = bisect_right(keys, (page, seg)) - 1
        return entries[i][2]

    new_rows = []
    seen = set()
    per_segment: dict[str, int] = defaultdict(int)
    page_map: dict[str, str] = {}
    for (p, s), r in zip(parsed, rows):
        sid = segment_of(p, s)
        per_segment[sid] += 1
        if sid == "praef":
            locus = f"praef.{p}.{s}"
        else:
            locus = f"{sid}.p{p - OFFSET}.{s}"
        assert locus not in seen, f"duplicate new locus {locus}"
        seen.add(locus)
        nr = dict(r)
        nr["locus"] = locus
        new_rows.append(nr)
        page_map.setdefault(str(p), sid)

    # --- 4. text-preservation verification --------------------------------
    assert len(new_rows) == len(rows)
    for a, b in zip(rows, new_rows):
        assert a["text"] == b["text"]
        assert {k: v for k, v in a.items() if k != "locus"} == \
               {k: v for k, v in b.items() if k != "locus"}
    old_concat = "".join("".join(r["text"].split()) for r in rows)
    new_concat = "".join("".join(r["text"].split()) for r in new_rows)
    assert old_concat == new_concat, "text content changed"
    empty = [nid for nid in NOVEL_STARTS if per_segment.get(nid, 0) == 0]
    assert not empty, f"segments with no rows: {empty}"
    new_bytes = dump_rows(new_rows)
    print(f"re-key: {len(rows)} rows -> {len(per_segment)} segments "
          f"(praef {per_segment['praef']}, app {per_segment.get('app', 0)}); "
          f"boundary decisions logged: {len(boundary_log)}")

    # --- 5. ocr_works.json label repair -----------------------------------
    ow_raw = OCR_WORKS.read_text(encoding="utf-8")
    ow = json.loads(ow_raw)
    stale = [w for w in ow if w.get("edition") == EDITION]
    stale_urns = {w["urn"] for w in stale}
    ow_fixed = None
    if stale_urns == {SLUG} and len(stale) == 1 and \
            stale[0]["n_passages"] == len(rows):
        print("ocr_works.json: already merged; no change")
    else:
        assert stale_urns <= {SLUG, OLD_SLUG}, f"unexpected urns {stale_urns}"
        merged = {
            "urn": SLUG,
            "author": "",
            "title": "",
            "edition": EDITION,
            "source": "ocr",
            "license": "PD",
            "pages": len(by_page),
            "pages_skipped_collapsed": 0,
            "n_passages": len(rows),
            "n_tokens": sum(1 for r in rows for t in r["text"].split()
                            if GREEK.search(t)),
            "date": DATE,
        }
        pos = min(i for i, w in enumerate(ow) if w.get("edition") == EDITION)
        ow_fixed = [w for w in ow if w.get("edition") != EDITION]
        ow_fixed.insert(pos, merged)
        print(f"ocr_works.json: merge {len(stale)} rows "
              f"({', '.join(sorted(stale_urns))}) -> 1 x {SLUG} "
              f"({merged['pages']} pages, {merged['n_passages']} passages, "
              f"{merged['n_tokens']} tokens)")

    # --- 6. audit record ---------------------------------------------------
    record = {
        "_meta": {
            "change": "re-key the page-keyed Schoell-Kroll Novellae OCR to "
                      "novel-number loci (<novel>.p<printed>.<seg>, ed<n>./"
                      "app./praef. prefixes); text untouched, row order "
                      "preserved. Same run merges the stale ocr_works.json "
                      "rows left by the upstream contra-monophysitas "
                      "mis-slug rescope.",
            "work": SLUG,
            "cts": CTS,
            "edition": EDITION,
            "applied_by": "scripts/rekey_novellae_by_novel.py",
            "date": DATE,
            "reversible": "old locus = justinian_novellae_schoell_"
                          "<printed+30, zero-padded to 4>.<seg> for novel/ed/"
                          "app keys, and justinian_novellae_schoell_<scan "
                          "zero-padded>.<seg> for praef keys; seg is carried "
                          "through unchanged, so the pre-rekey file is "
                          "byte-reconstructible (or git-restore the parent "
                          "commit). data/corrections_log/applied.jsonl rows "
                          "for this work still cite the pre-rekey loci; the "
                          "same formula joins them to the new keys.",
        },
        "old": {"rows": len(rows), "greek_chars": greek_chars(old_concat),
                "sha256": sha256(raw),
                "locus_scheme": "justinian_novellae_schoell_<scan>.<seg>"},
        "new": {"rows": len(new_rows), "greek_chars": greek_chars(new_concat),
                "sha256": sha256(new_bytes),
                "locus_scheme": "<novel 1-168>.p<printed>.<seg> | "
                                "ed<1-13>.p<printed>.<seg> | "
                                "app.p<printed>.<seg> | praef.<scan>.<seg>"},
        "verification": {
            "per_row_text_identical": True,
            "concat_ws_insensitive_identical": True,
            "concat_sha256": sha256(old_concat.encode("utf-8")),
        },
        "concordance": {
            "derivation": "printed start page+line per novel from the "
                          "per-page structural headings of the TLG-E "
                          "digitization of the same Schoell-Kroll print "
                          "(TLG 2734.013 is keyed Page.line of this "
                          "edition), with mechanical stigma(+6)/koppa(+90) "
                          "numeral repairs under strict monotonicity; "
                          "embedded as NOVEL_STARTS in the script",
            "greek_novel_headings": len([k for k in NOVEL_STARTS
                                         if not k.startswith("ed")]),
            "edict_headings": len([k for k in NOVEL_STARTS
                                   if k.startswith("ed")]),
            "latin_only_novels_no_heading": LATIN_ONLY,
            "scan_printed_offset": OFFSET,
            "ocr_numeral_row_anchors": [
                {"segment": n, "scan_page": sc, "seg": sg, "row_text": t}
                for n, sc, sg, t in numeral_anchors],
            "ocr_heading_confirmed_either_signal": len(detected),
        },
        "boundary_log": boundary_log,
        "scan_page_to_segment": page_map,
        "rows_per_segment": dict(sorted(per_segment.items())),
        "ocr_works_fix": {
            "confusion": "the OCR batch was first delivered under "
                         "flavius-justinianus-imperator.contra-monophysitas "
                         "(tlg2734.tlg001 = Contra monophysitas, which this "
                         "scan never contained); the upstream rescope renamed "
                         "the corpus file to the novellae slug (see "
                         "data/work_id_aliases.json) but left its "
                         "ocr_works.json rows behind: a 14,053-passage row "
                         "under the old slug and an 8-passage ocr_dpi gap-"
                         "fill row under the new one",
            "replaced_rows": stale,
            "action": ("merged into one novellae row with stats recomputed "
                       "from the corpus file" if ow_fixed is not None
                       else "already merged; no change"),
        },
    }

    if args.apply:
        CORPUS.write_bytes(new_bytes)
        if ow_fixed is not None:
            OCR_WORKS.write_text(json.dumps(ow_fixed, ensure_ascii=False,
                                            indent=1), encoding="utf-8")
        CHANGES.mkdir(parents=True, exist_ok=True)
        out = CHANGES / f"{SLUG}.novel-rekey.json"
        out.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
        print(f"APPLIED: corpus re-keyed, audit -> {out.relative_to(REPO)}")
    else:
        print("CHECK ONLY (pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
