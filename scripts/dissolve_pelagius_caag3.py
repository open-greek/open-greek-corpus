#!/usr/bin/env python3
"""Dissolve the pelagius CAAG livraison-3 catch-all into per-work slugs.

Diagnosis (2026-07-10, session e0a83cbd; precedents: greek-ocr dissolve_hgm1.py,
scripts/rescope_cougny_appendix.py, scripts/displace_to_secondary.py)
--------------------------------------------------------------------------------
After the 2026-07-10 double-serve displacement (scan pages 0013-0180 -> zosimus
secondary), pelagius.pelagi-ou-filoso-fou-peri-th-s-qei-as-tau-ths-kai-i-era-s-
te-xnhs still served ALL of Berthelot-Ruelle, Collection des anciens alchimistes
grecs (texte grec, 1888) livraison 3 = printed pp. 253-459 (scan = printed + 42,
scan 0295-0501, 2,500 rows on 204 pages). Only printed 253-261 (scan 0295-0302;
scan 0303 = printed 261 is absent from the corpus) is the real Pelagius treatise
(tlg2019.001, canon 1,834 words). Everything after is CAAG Parts IV.ii-VI:
Ostanes, Joannes Archiereus, ps.-Hermes, ps.-Agathodaemon, the anonymous "vieux
auteurs" fragments, Iamblichus, Comarius, the Chimie de Moise, the Part V
technical recipes, Salmanas, the Philosophus Christianus, the Anepigraphos,
Cosmas Hieromonachus, Hierotheus and Nicephorus Blemmydes.

The TLG canon (~/Documents/tlge-tools/data/tlg_canon.json) cites CAAG vol. 2 by
printed page for every one of these works, giving an authoritative zone map;
every zone boundary below was additionally verified against the corpus rows'
own section heads (quoted in the ZONES table) and, where the older OCR pass is
garbled, against the fresh full-page reads in greek-ocr
runs/editions/berthelot_alchimistes_grec_out (evidence quoted in
scratchpad pelagius_dissolve_report.md).

What this tool does (dry-run default; --apply writes):
  1. keeps pelagius.* primary for its true zone (scan 0295-0302 only);
  2. serves every other zone as a NEW PRIMARY work under its registry slug
     (the registry already mints canon-derived slugs, e.g.
     moses.eu-poi-kai-eu-tuxi-tou-ktisame-nou-kai-e-pituxi-kama-tou-kai);
     the two canon works with empty canon titles (tlg1379.030 / .053) get
     hand-minted slugs in house betacode style (flagged);
  3. EXCEPT the three zones whose works are already served by First1KGreek
     TEI primaries (tlg4086.002 Agathodaemon, tlg2140.001 Iamblichus,
     tlg2632.001 Comarius): open-digital > OCR, so those zones are displaced
     to data/corpus_secondary/<target>.jsonl as edition witnesses, each only
     after char-10-gram containment probes re-verify the coverage here and now;
  4. mid-page boundaries split at the section-head row (asserted at runtime);
     pages the old OCR pass read as interleaved half-columns get explicit
     per-row maps (asserted to exactly partition the page's rows);
  5. crosswalk entries are added ONLY for canon-verified ids (every id is
     asserted against the canon at runtime: title page-range and word count);
     tlg2632.X01 (IV.xxi) is a canon dubium printed as a TITLE-ONLY section
     (Berthelot's note: text = Ostanes IV.ii) - it gets its registry slug and
     canon id but is flagged as a 2-row stub.

Invariants (checked before any write):
  - Greek chars across all planned outputs == 100.0000% of the input (pure
    reassignment: zero rows dropped, zero rows duplicated; >= 99.5% required);
  - every input row lands in exactly one output work; after write, every
    berthelot scan page 0295-0501 is served by exactly one PRIMARY work at
    row level (pages hosting a boundary carry two+ works on disjoint row sets,
    listed in the report);
  - urns only from the TLG canon (asserted); new works are written only to
    slugs with no existing corpus file;
  - per-zone word-count sanity vs the canon (soft flag outside 0.5-2.5x,
    hard problem outside 0.25-4x for zones of >= 300 canon words).

NOT done here (main session runs, once, after review):
  (cog) scripts/rekey_corrections_log.py --write   # audit mirror follows moves
  (cog) scripts/reconcile_corpus_editions.py

  python3 scripts/dissolve_pelagius_caag3.py             # dry-run report
  python3 scripts/dissolve_pelagius_caag3.py --apply
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "corpus"
SECONDARY = REPO / "data" / "corpus_secondary"
CW_PATH = REPO / "data" / "tlg_crosswalk.json"
TSV_PATH = REPO / "data" / "tlg_crosswalk.tsv"
REG_PATH = REPO / "data" / "source_registry.json"
CANON = Path.home() / "Documents/tlge-tools/data/tlg_canon.json"
SCRATCH = Path("/private/tmp/claude-501/-Users-cisco-Documents-greek-ocr/"
               "e0a83cbd-1aed-4a76-a35a-2908a4934e9a/scratchpad")

OLD = "pelagius.pelagi-ou-filoso-fou-peri-th-s-qei-as-tau-ths-kai-i-era-s-te-xnhs"
BASE = "berthelot_alchimistes_grec"
OFF = 42                     # scan page = printed page + 42 (livraison 3)
COVER_TOL = 0.995
GK = re.compile(r"[Ͱ-Ͽἀ-῿]")

SEC_REASON = ("Berthelot-Ruelle CAAG texte grec (1888) edition witness of this "
              "work, carved from the pelagius livraison-3 catch-all (scan "
              "berthelot_alchimistes_grec); primary text is the served "
              "First1KGreek TEI file (dissolve_pelagius_caag3.py 2026-07-10; "
              "section-head + containment evidence in "
              "pelagius_dissolve_report.md / dissolve_pelagius_caag3_report.json)")

# ---------------------------------------------------------------------------
# Zone table. One entry per TLG-canon work printed in CAAG vol. 2 pp. 253-459
# (plus the title-only IV.xxi dubium). Fields:
#   tlg      canon id "tlgAUTHOR.WORK" ("X01" works are canon dubia w/o text)
#   pp       printed page range in the canon (asserted, except X-works)
#   wc       canon word count (asserted; None for X-works)
#   start    (scan_page, row) of the zone's first row (inclusive)
#   head     raw substring expected in the start row (normalized containment,
#            asserted at runtime; observed in the corpus rows on 2026-07-10)
#   act      "keep" | "new" | "sec"; sec_target names the served 1st1K primary
#   slug     None -> resolve from registry by cts alias; str -> minted (flagged)
# Boundaries fall where the canon page map and the observed section heads
# agree; caag notes the printed section number for the report.
# ---------------------------------------------------------------------------
Z = lambda **kw: kw
ZONES = [
    Z(tlg="tlg2019.001", pp=(253, 261), wc=1834, start=(295, 1), act="keep",
      caag="IV.i", head="ΠΕΛΑΓΙΟΥ ΦΙΛΟΣΟΦΟΥ ΠΕΡΙ ΤΗΣ ΘΕΙΑΣ"),
    # scan 0303 (= printed 261, Pelagius explicit + Ostanes head) is absent
    # from the corpus; the Ostanes zone is its printed-262 page only.
    Z(tlg="tlg1016.001", pp=(261, 262), wc=292, start=(304, 1), act="new",
      caag="IV.ii", head="ἀγγείῳ λίτρων μίαν"),
    Z(tlg="tlg4327.001", pp=(263, 267), wc=973, start=(305, 1), act="new",
      caag="IV.iii", head="ΙΩΑΝΝΟΥ ΑΡΧΙΕΡΕΩΣ"),
    Z(tlg="tlg4325.002", pp=(267, 268), wc=59, start=(309, 3), act="new",
      caag="IV.iv", head="ΑΙΝΙΓΜΑ ΤΟΥ ΦΙΛΟΣΟΦΙΚΟΥ"),
    Z(tlg="tlg4086.002", pp=(268, 271), wc=871, start=(310, 3), act="sec",
      caag="IV.v", head="ΑΓΑΘΟΔΑΙΜΩΝ ΕΙΣ ΤΟΝ ΧΡΗΣΜΟΝ",
      sec_target="agathodaemon.agaqodai-mwn-ei-s-n-xrhsmo-n-orfe-ws-sunagwgh-kai"),
    Z(tlg="tlg1379.058", pp=(272, 275), wc=631, start=(314, 1), act="new",
      caag="IV.vi", head="ΟΤΙ ΣΥΝΘΕΤΟΝ ΚΑΙ ΟΥΧ"),
    Z(tlg="tlg1379.059", pp=(275, 277), wc=500, start=(317, 2), act="new",
      caag="IV.vii", head="ΠΟΙΗΣΙΣ ΜΑΛΛΟΝ ΤΟΥ ΠΑΝΤΟΣ"),
    Z(tlg="tlg1379.060", pp=(278, 278), wc=200, start=(320, 1), act="new",
      caag="IV.viii", head="Η ΟΙΚΟΝΟΜΙΑ"),
    Z(tlg="tlg1379.061", pp=(279, 280), wc=210, start=(321, 1), act="new",
      caag="IV.ix", head="ΤΙΣ Η ΤΩΝ ΑΡΧΑΙΩΝ ΑΣΒΕΣΤΟΣ"),
    Z(tlg="tlg1379.062", pp=(280, 280), wc=49, start=(322, 2), act="new",
      caag="IV.x (sine titulo)", head="Τινὲς μὲν οὖν τὸν ἴον"),
    Z(tlg="tlg1379.063", pp=(280, 281), wc=128, start=(322, 3), act="new",
      caag="IV.xi", head="ΟΙΚΟΝΟΜΙΑ ΤΗΣ ΑΣΒΕΣΤΟΥ"),
    Z(tlg="tlg1379.064", pp=(281, 282), wc=121, start=(323, 2), act="new",
      caag="IV.xii", head="ΠΟΙΗΣΙΣ ΑΣΒΕΣΤΟΥ"),
    Z(tlg="tlg1379.065", pp=(282, 282), wc=130, start=(324, 2), act="new",
      caag="IV.xiii (titulus in app.)", head="Τινὲς δὲ τὴν ἀσθεστον"),
    Z(tlg="tlg1379.066", pp=(283, 283), wc=89, start=(325, 2), act="new",
      caag="IV.xiv (sine titulo)", head="Ἕτεροι δὲ τὸν σποδὸν"),
    Z(tlg="tlg1379.067", pp=(283, 283), wc=32, start=(325, 3), act="new",
      caag="IV.xv", head="ΑΛΛΩΣ"),
    Z(tlg="tlg1379.068", pp=(284, 284), wc=35, start=(326, 1), act="new",
      caag="IV.xvi", head="ΕΤΕΡΩΣ. Η ΠΟΙΗΣΙΣ"),
    Z(tlg="tlg1379.069", pp=(284, 284), wc=28, start=(326, 3), act="new",
      caag="IV.xvii", head="ΕΤΕΡΩΣ. Η ΑΓΩΓΗ"),
    Z(tlg="tlg1379.070", pp=(284, 285), wc=66, start=(326, 5), act="new",
      caag="IV.xviii", head="ΣΥΜΠΕΡΑΣΜΑ ΤΗΣ ΠΟΙΗΣΕΩΣ"),
    Z(tlg="tlg2140.001", pp=(285, 289), wc=1055, start=(327, 2), act="sec",
      caag="IV.xix", head="ΙΑΜΒΛΙΧΟΥ ΚΑΤΑΒΑΦΗ",
      sec_target="iamblichus-alchemy.fragmenta-alchemica-e-cod-paris-b-n-gr-"
                 "2327-fol-266r"),
    Z(tlg="tlg2632.001", pp=(289, 299), wc=2355, start=(331, 13), act="sec",
      caag="IV.xx", head="ΚΟΜΑΡΙΟΥ ΦΙΛΟΣΟΦΟ",
      sec_target="comarius.de-lapide-philosophorum-e-cod-paris-b-n-gr-2327-"
                 "fol-74r"),
    # IV.xxi: canon dubium, printed as a TITLE-ONLY section (Berthelot's note:
    # same text as Ostanes IV.ii, given anonymously in ms. A) -> 2-row stub.
    Z(tlg="tlg2632.X01", pp=None, wc=None, start=(341, 15), act="new",
      caag="IV.xxi (title-only)", head="ΠΕΡΙ ΤΗΣ ΘΕΙΑΣ ΚΑΙ ΙΕΡΑΣ"),
    Z(tlg="tlg2181.002", pp=(300, 315), wc=3782, start=(342, 1), act="new",
      caag="IV.xxii", head="ΕΥΗΟΙΑ ΚΑΙ ΕΥΤΥΧΙΑ ΤΟΥ ΚΤΙΣΑΜΕΝΟΥ"),
    Z(tlg="tlg1379.071", pp=(315, 318), wc=533, start=(357, 18), act="new",
      caag="IV.xxiii", head="ΠΕΡΙ ΤΗΣ ΘΕΙΑΣ ΚΑΙ ΙΕΡΑΣ ΤΕΧΝΗΣ ΤΩ"),
    Z(tlg="tlg1379.072", pp=(318, 319), wc=192, start=(360, 2), act="new",
      caag="IV.xxiv", head="ΩΣΤΕ ΛΕΥΚΑΝΑΙ"),
    Z(tlg="tlg1379.026", pp=(321, 337), wc=4348, start=(363, 1), act="new",
      caag="V.i", head="ΠΕΡΙ ΤΗΣ ΤΙΜΙΩΤΑΤΗΣ ΚΑΙ ΠΟΛΥΦΗΜΟΥ"),
    Z(tlg="tlg1379.027", pp=(337, 342), wc=1285, start=(379, 2), act="new",
      caag="V.ii", head="ΑΡΧΗ ΤΗΣ ΚΑΤΑ ΠΛΑΤΟΣ"),
    Z(tlg="tlg1379.028", pp=(342, 345), wc=798, start=(384, 19), act="new",
      caag="V.iii", head="ΠΕΡΙ ΒΑΦΗΣ ΣΙΔΗΡΟΥ"),
    Z(tlg="tlg1379.029", pp=(346, 347), wc=273, start=(388, 1), act="new",
      caag="V.iv", head="ΒΑΦΗ ΤΟΥ ΠΑΡΑ ΠΕΡΣΑΙΣ"),
    Z(tlg="tlg1379.030", pp=(347, 348), wc=202, start=(389, 2), act="new",
      caag="V.v (canon title empty)", head="ΒΑΦΗ ΤΟΥἸΝΔΙΚΟΥ ΣΙΔΗΡΟΥ",
      slug="fragmenta-alchemica.bafh-tou-i-ndikou-sidh-rou-grafei-sa-tw-au-tw-"
           "xro-nw",
      title="Βαφὴ τοῦ Ἰνδικοῦ σιδήρου, γραφεῖσα τῷ αὐτῷ χρόνῳ"),
    Z(tlg="tlg1379.031", pp=(348, 350), wc=359, start=(390, 3), act="new",
      caag="V.vi", head="ΠΟΙΗΣΙΣ ΚΡΥΣΤΑΛΛΙΩΝ"),
    Z(tlg="tlg1379.032", pp=(350, 364), wc=3629, start=(392, 4), act="new",
      caag="V.vii", head="ΚΑΤΑΒΑΦΗ ΑΙΘΩΝ ΚΑΙ ΣΜΑΡΑΓΔΩΝ"),
    Z(tlg="tlg4340.001", pp=(364, 367), wc=945, start=(406, 2), act="new",
      caag="V.viii", head="ΜΕΘΟΔΟΣ ΔΙ ' ΗΣ ΑΠΟΤΕΛΕΙΤΑΙ"),
    Z(tlg="tlg1379.034", pp=(368, 371), wc=941, start=(410, 1), act="new",
      caag="V.ix", head="ΣΜΗΞΙΣ ΚΑΙ ΛΑΜΠΡΥΝΣΙΣ ΜΑΡΓΑΡΩΝ"),
    Z(tlg="tlg1379.035", pp=(372, 372), wc=106, start=(414, 1), act="new",
      caag="V.x", head="ΠΕΡΙ ΖΥΘΩΝ ΠΟΙΗΣΕΩΣ"),
    Z(tlg="tlg1379.036", pp=(372, 373), wc=296, start=(414, 3), act="new",
      caag="V.xi", head="ΣΤΑΚΤΗΣ ΠΟΙΗΣΙΣ"),
    Z(tlg="tlg1379.037", pp=(373, 374), wc=69, start=(415, 4), act="new",
      caag="V.xii", head="ΠΟΣΟΣ Ο ΤΩΝ ΒΑΠΤΟΜΕΝΩΝ"),
    Z(tlg="tlg1379.038", pp=(374, 374), wc=51, start=(416, 6), act="new",
      caag="V.xiii", head="ΤΙΣ Η ΤΟΥ"),
    Z(tlg="tlg1379.039", pp=(374, 374), wc=24, start=(416, 12), act="new",
      caag="V.xiv", head="ΤΙΣ Η"),
    Z(tlg="tlg1379.040", pp=(375, 375), wc=79, start=(417, 1), act="new",
      caag="V.xv", head="ΤΙΣ Η ΜΕΤΑ ΤΗΝ ΙΩΣΙΝ"),
    Z(tlg="tlg1379.041", pp=(375, 377), wc=460, start=(417, 3), act="new",
      caag="V.xvi", head="ΕΙ ΘΕΛΕΙΣ ΠΟΙΗΣΑΙ ΦΟΥΡΜΑΣ"),
    Z(tlg="tlg1379.042", pp=(377, 379), wc=568, start=(419, 2), act="new",
      caag="V.xvii", head="ΔΙΑΦΟΡΑΙ ΜΟΛΙΒΔΟΥ"),
    Z(tlg="tlg1379.043", pp=(380, 380), wc=176, start=(422, 1), act="new",
      caag="V.xviii", head="ΠΕΡΙ ΤΟΥ ΠΟΙΗΣΑΙ ΤΥΡΟΚΟΛΛΑΝ"),
    Z(tlg="tlg1379.044", pp=(380, 381), wc=101, start=(422, 5), act="new",
      caag="V.xix", head="ΠΕΡΙ ΤΟΥ ΠΟΙΗΣΑΙ ΟΞΥΓΓΟΔΑΠΟΥΝΟΝ"),
    Z(tlg="tlg1379.045", pp=(381, 382), wc=116, start=(423, 2), act="new",
      caag="V.xx", head="Ὁ μέλυβδος φύσει"),
    Z(tlg="tlg1379.046", pp=(382, 383), wc=151, start=(424, 2), act="new",
      caag="V.xxi", head="ΧΡΥΣΟΥ ΠΟΙΗΣΙΣ"),
    Z(tlg="tlg1379.047", pp=(383, 383), wc=49, start=(425, 2), act="new",
      caag="V.xxii", head="ΣΚΕΥΑΣΙΑ ΑΦΡΟΝΙΤΡΟΥ"),
    Z(tlg="tlg1379.048", pp=(383, 384), wc=271, start=(425, 4), act="new",
      caag="V.xxiii", head="ΚΙΝΝΑΒΑΡΕΩΣ ΣΚΕΥΑΣΙ"),
    Z(tlg="tlg1379.049", pp=(384, 387), wc=733, start=(426, 21), act="new",
      caag="V.xxiv (sine titulo; explicit at 0429.21)",
      head="Λαβὼν ὀστραχα ὠῶν"),
    Z(tlg="tlg1379.050", pp=(387, 388), wc=172, start=(429, 22), act="new",
      caag="V.xxv", head="ΔΙΑΡΓΑΜΜΑ ΤΗΣ ΜΕΓΑΛΗΣ"),
    Z(tlg="tlg1379.051", pp=(388, 389), wc=178, start=(430, 4), act="new",
      caag="V.xxvi", head="ΕΥΧΗ ΕΙΣ ΤΙ ΜΕΛΙΣΣΙΟΝ"),
    Z(tlg="tlg1379.052", pp=(389, 390), wc=142, start=(431, 11), act="new",
      caag="V.xxvii", head="ΠΟΙΗΣΙΣ ΑΡΓΥΡΟΥ"),
    Z(tlg="tlg1379.053", pp=(390, 390), wc=51, start=(432, 5), act="new",
      caag="V.xxviii (canon title empty)", head="ΠΕΡΙ ΤΟΥ ΟΡΕΙΧΑΛΚΟΥ",
      slug="fragmenta-alchemica.peri-tou-o-reixa-lkou",
      title="Περὶ τοῦ ὀρειχάλκου"),
    Z(tlg="tlg1379.054", pp=(390, 390), wc=69, start=(432, 11), act="new",
      caag="V.xxix", head="ΠΕΡΙ ΤΟΥ ΘΕΙΟΥ ΑΚΑΥΣΤΟΥ"),
    Z(tlg="tlg1379.055", pp=(391, 391), wc=67, start=(433, 1), act="new",
      caag="V.xxx", head="ΛΕΥΚΩΣΙΣ ΥΔΑΤΟΣ"),
    Z(tlg="tlg1379.056", pp=(391, 391), wc=100, start=(433, 10), act="new",
      caag="V.xxxi", head="ΠΕΡΙ ΛΕΥΚΩΣΕΩΣ ΤΟΥ ΑΡΣΕΝΙΚΟΥ"),
    Z(tlg="tlg1379.057", pp=(392, 393), wc=321, start=(434, 1), act="new",
      caag="V.xxxii", head="ΠΕΡΙ ΤΟΥ ΧΡΗΣΩΣΑΙ ΣΙΔΗΡΟΝ"),
    Z(tlg="tlg4328.001", pp=(395, 399), wc=849, start=(437, 1), act="new",
      caag="VI.i", head="ΤΟΥ ΧΡΙΣΤΙΑΝΟΥ ΠΕΡΙ ΕΥΣΤΑΘΕΙΑΣ"),
    Z(tlg="tlg4328.002", pp=(399, 400), wc=137, start=(441, 5), act="new",
      caag="VI.ii", head="ΤΟΥ ΑΥΤΟΥ ΧΡΙΣΤΙΑΝΟΥ ΠΕΡΙ ΤΟΥ ΘΕΙΟΥ"),
    Z(tlg="tlg4328.003", pp=(400, 401), wc=235, start=(442, 9), act="new",
      caag="VI.iii", head="ΤΙΣ Ἡ ΤΩΝ ΑΡΧΑΙΩΝ ΔΙΑΦΩΝΙΑ"),
    Z(tlg="tlg4328.004", pp=(401, 402), wc=40, start=(443, 6), act="new",
      caag="VI.iv", head="ΤΙΣ Η ΚΑΘΟΛΟΥ ΤΟΥ ΥΔΑΤΟΣ"),
    Z(tlg="tlg4328.005", pp=(402, 405), wc=626, start=(444, 3), act="new",
      caag="VI.v", head="Ἡ ΤΟΥ ΜΗΘΙΚΟΥ ΓΔΑΤΟΣ ΠΟΙΗΣΙΣ"),
    Z(tlg="tlg4328.006", pp=(405, 407), wc=375, start=(447, 2), act="new",
      caag="VI.vi", head="ΘΕΣΙΣ ΛΕΓΟΥΣΑ ΟΤΙ ΤΟ ΘΕΙΟΝ"),
    Z(tlg="tlg4328.007", pp=(407, 408), wc=373, start=(449, 2), act="new",
      caag="VI.vii", head="ΑΛΛΗ ΑΠΟΡΙΑ"),
    Z(tlg="tlg4328.008", pp=(409, 409), wc=87, start=(451, 1), act="new",
      caag="VI.viii", head="ΤΟΥ ΧΡΙΣΤΙΑΝΟΥ ΣΥΝΟΨΙΣ"),
    Z(tlg="tlg4328.009", pp=(409, 410), wc=173, start=(451, 4), act="new",
      caag="VI.ix", head="ΤΕΤΡΑΧΩΣ ΔΙΑΙΡΟΥΜΕΝΗΣ"),
    Z(tlg="tlg4328.010", pp=(410, 414), wc=832, start=(452, 16), act="new",
      caag="VI.x", head="ΠΟΣΑΙ ΕΙΣΙΝ ΔΙΑΦΟΡΑΙ"),
    Z(tlg="tlg4328.011", pp=(414, 415), wc=166, start=(456, 2), act="new",
      caag="VI.xi", head="ΠΩΣ ΔΕΙ ΝΟΕΙΝ"),
    Z(tlg="tlg4328.012", pp=(415, 421), wc=1224, start=(457, 2), act="new",
      caag="VI.xii", head="ΤΙΣ Η ΕΝ ΑΠΟΚΡΥΦΟΙΣ"),
    Z(tlg="tlg4329.001", pp=(421, 424), wc=520, start=(463, 2), act="new",
      caag="VI.xiii", head="ΑΝΕΠΙΓΡΑΦΟΥ ΦΙΛΟΣΟΦΟΥ ΠΕΡΙ ΘΕΙΟΥ"),
    Z(tlg="tlg4329.002", pp=(424, 433), wc=1758, start=(466, 3), act="new",
      caag="VI.xiv", head="ΦΙΛΟΣΟΦΟΥ ΚΑΤΑ ΔΚΟ"),
    Z(tlg="tlg4329.003", pp=(433, 441), wc=1711, start=(475, 3), act="new",
      caag="VI.xv", head="Τὸ ὅν τετραμερές ἐστιν"),
    Z(tlg="tlg4330.001", pp=(442, 446), wc=1124, start=(484, 1), act="new",
      caag="VI.xvi", head="ΕΡΜΗΝΕΙΑ ΤΗΣ ΕΠΙΣΤΗΜ"),
    Z(tlg="tlg1379.073", pp=(446, 447), wc=116, start=(488, 15), act="new",
      caag="VI.xvii", head="Ζώσιμος · Κἀγὼ δὲ χά"),
    Z(tlg="tlg1379.074", pp=(447, 450), wc=532, start=(489, 3), act="new",
      caag="VI.xviii", head="ΠΕΡΙ ΤΟΥ ΑΙΘΟΥ ΤΩΝ ΦΙΑ"),
    Z(tlg="tlg4331.001", pp=(450, 451), wc=381, start=(492, 9), act="new",
      caag="VI.xix", head="ΙΕΡΟΘΕΟΥ ΠΕΡΙ ΤΗΣ ΙΕΡ"),
    Z(tlg="tlg4333.001", pp=(452, 457), wc=1269, start=(494, 1), act="new",
      caag="VI.xx", head="ΠΕΡΙ ΤΗΣ ΩΧΡΥΣΟΠΟΗΙΑΣ"),
    Z(tlg="tlg4333.002", pp=(458, 459), wc=177, start=(500, 1), act="new",
      caag="VI appendix", head="ΑΠΕΡ ΧΡΗΖΕΙ Η ΠΑΡΟΥΣΑ"),
]

# ---------------------------------------------------------------------------
# Pages the old OCR pass read as interleaved half-columns (left halves, then
# right halves, then apparatus), or whose bottom apparatus block glosses the
# EARLIER zone: explicit per-row zone maps (tlg key -> row numbers). Asserted
# at runtime to exactly partition the page's present rows. Derivation for
# every page is quoted in scratchpad pelagius_dissolve_report.md.
# ---------------------------------------------------------------------------
def rr(*specs):
    out = set()
    for s in specs:
        out.update(range(s[0], s[1] + 1) if isinstance(s, tuple) else [s])
    return out

SPLIT_PAGES: dict[int, dict[str, set[int]]] = {
    325: {"tlg1379.066": rr(2, 5), "tlg1379.067": rr(3, 4, 6)},
    331: {"tlg2140.001": rr((1, 12), (22, 33), 43),
          "tlg2632.001": rr((13, 21), (34, 42), (44, 47))},
    341: {"tlg2632.001": rr((1, 14), (17, 28), (30, 31)),
          "tlg2632.X01": rr((15, 16))},
    357: {"tlg2181.002": rr((1, 17), (21, 39)),
          "tlg1379.071": rr((18, 20), (40, 43), 45)},
    360: {"tlg1379.071": rr(1, (3, 8), (21, 27)),
          "tlg1379.072": rr(2, (9, 20), (28, 30))},
    384: {"tlg1379.027": rr((1, 18), (21, 30)),
          "tlg1379.028": rr((19, 20))},
    416: {"tlg1379.037": rr((1, 5), (15, 16), (18, 24)),
          "tlg1379.038": rr((6, 11), (25, 30), 34),
          "tlg1379.039": rr((12, 14), (31, 33))},
    426: {"tlg1379.048": rr((1, 20), (23, 24)),
          "tlg1379.049": rr((21, 22))},
    431: {"tlg1379.051": rr((1, 10), 22, (24, 27)),
          "tlg1379.052": rr((11, 21))},
    432: {"tlg1379.052": rr((1, 4)),
          "tlg1379.053": rr((5, 10), (19, 20)),
          "tlg1379.054": rr((11, 18), (21, 22))},
    452: {"tlg4328.009": rr((1, 15), (20, 22), (25, 38), (44, 45), (47, 48)),
          "tlg4328.010": rr((16, 19), (39, 43))},
    457: {"tlg4328.011": rr(1, 4), "tlg4328.012": rr(2, 3)},
    466: {"tlg4329.001": rr((1, 2), (14, 19), (30, 37)),
          "tlg4329.002": rr((3, 13), (20, 29), (38, 43))},
    475: {"tlg4329.002": rr((1, 2), (4, 12), 20),
          "tlg4329.003": rr(3, (13, 19), (21, 25))},
    488: {"tlg4330.001": rr((1, 14), (17, 37)),
          "tlg1379.073": rr((15, 16), (38, 45))},
    489: {"tlg1379.073": rr((1, 2), 5), "tlg1379.074": rr((3, 4))},
    492: {"tlg1379.074": rr((1, 8), (19, 21)),
          "tlg4331.001": rr((9, 18), (23, 24))},
}

PROBE_MIN_PASS, PROBE_MIN_CONT = 2, 0.6   # measured 0.68-0.97 on 2026-07-10


# ------------------------------ helpers -------------------------------------
def locus_key(locus: str) -> tuple[int, int]:
    m = re.match(rf"^{re.escape(BASE)}_(\d+)\.(\d+)$", str(locus))
    if not m:
        raise SystemExit(f"ABORT: row not keyed to {BASE}: {locus!r}")
    return int(m.group(1)), int(m.group(2))


def greek(s: str) -> int:
    return len(GK.findall(s or ""))


def gk_total(rows) -> int:
    return sum(greek(r.get("text", "")) for r in rows)


# OCR mixes visually identical Latin/Greek capitals and Λ/Α; fold onto one form
_FOLD = str.maketrans("ABEZHIKMNOPTYXΛ", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧΑ")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Zα-ωΑ-Ωϲ]", "", s).upper().replace("Ϲ", "Σ")
    return s.translate(_FOLD)


def norm_tok(tok: str) -> str:
    d = unicodedata.normalize("NFD", tok.lower())
    d = "".join(c for c in d if not unicodedata.combining(c))
    d = "".join(c for c in d if GK.match(c))
    return d.replace("ς", "σ")


def chargrams(text: str, n: int = 10) -> set[str]:
    s = " ".join(w for w in (norm_tok(x) for x in text.split()) if w)
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def load(fp: Path) -> list[dict]:
    if not fp.exists():
        return []
    return [json.loads(l) for l in fp.open(encoding="utf-8") if l.strip()]


def dump(fp: Path, rows: list[dict]) -> None:
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                          for r in rows), encoding="utf-8")


# ------------------------------ main -----------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    problems: list[str] = []
    flags: list[str] = []
    report: dict = {}

    # ---- canon verification: every zone id must be a real canon work -------
    canon = json.load(open(CANON))
    cw_key = {}
    for w in canon["works"]:
        cw_key[f"{w['tlg_id']}.{w['work_id']}"] = w
    for z in ZONES:
        w = cw_key.get(z["tlg"])
        if w is None:
            problems.append(f"{z['tlg']}: NOT IN CANON - refusing to mint")
            continue
        if z["pp"] is not None:
            m = re.match(r"(\d+)(?:-(\d+))?$", w.get("pages") or "")
            got = (int(m.group(1)), int(m.group(2) or m.group(1))) if m else None
            if got != z["pp"]:
                problems.append(f"{z['tlg']}: canon pages {got} != table {z['pp']}")
            if w.get("word_count") != z["wc"]:
                problems.append(f"{z['tlg']}: canon wc {w.get('word_count')} "
                                f"!= table {z['wc']}")
        z["canon_title"] = w.get("title") or ""

    # ---- registry slug resolution -------------------------------------------
    reg = json.load(open(REG_PATH))
    cts2slug = {(w.get("aliases") or {}).get("cts"): s
                for s, w in reg["works"].items()
                if (w.get("aliases") or {}).get("cts")}
    for z in ZONES:
        a, wid = z["tlg"].split(".")
        cts = f"urn:cts:greekLit:{a}.tlg{wid}"
        z["cts"] = cts
        if z["act"] == "keep":
            z["slug"] = OLD
        elif z["act"] == "sec":
            z["slug"] = z["sec_target"]
        elif z.get("slug"):
            flags.append(f"{z['tlg']}: minted slug {z['slug']} (no registry "
                         f"entry; canon title empty)")
            if z["slug"] in reg["works"]:
                problems.append(f"minted slug {z['slug']} collides with registry")
        else:
            slug = cts2slug.get(cts)
            if not slug:
                problems.append(f"{z['tlg']}: no registry slug for {cts}")
            z["slug"] = slug
            z.setdefault("title", (reg["works"].get(slug) or {}).get("title", ""))

    # ---- load + order the catch-all rows ------------------------------------
    rows = load(CORPUS / f"{OLD}.jsonl")
    if len(rows) < 2000:
        raise SystemExit(f"ABORT: {OLD} has only {len(rows)} rows - already "
                         f"dissolved?")
    rows.sort(key=lambda r: locus_key(r["locus"]))
    pages = sorted({locus_key(r["locus"])[0] for r in rows})
    if pages[0] != 295 or pages[-1] != 501:
        raise SystemExit(f"ABORT: unexpected page span {pages[0]}-{pages[-1]}")
    missing_pages = sorted(set(range(295, 502)) - set(pages))
    report["missing_scan_pages"] = missing_pages
    if missing_pages != [303, 362, 436]:
        problems.append(f"unexpected missing pages {missing_pages} "
                        f"(expected [303, 362, 436])")
    by_loc = {locus_key(r["locus"]): r for r in rows}
    pre_gk = gk_total(rows)

    # ---- head assertions -----------------------------------------------------
    for z in ZONES:
        r = by_loc.get(tuple(z["start"]))
        if r is None:
            problems.append(f"{z['tlg']}: start row {z['start']} absent")
        elif norm(z["head"]) not in norm(r["text"]):
            problems.append(f"{z['tlg']}: head {z['head']!r} not in start row "
                            f"{z['start']}: {r['text'][:60]!r}")

    # ---- row assignment ------------------------------------------------------
    zone_rows: dict[str, list[dict]] = defaultdict(list)
    starts = [(tuple(z["start"]), z["tlg"]) for z in ZONES]
    if starts != sorted(starts):
        raise SystemExit("ABORT: ZONES not in reading order")
    split_owner = {}                      # (page,row) -> tlg, from SPLIT_PAGES
    for pg, zmap in SPLIT_PAGES.items():
        present = {l for (p, l) in by_loc if p == pg}
        mapped: set[int] = set()
        for tlg, rowset in zmap.items():
            if mapped & rowset:
                problems.append(f"split page {pg:04d}: overlapping row map")
            mapped |= rowset
            for l in rowset:
                split_owner[(pg, l)] = tlg
        if mapped != present:
            problems.append(f"split page {pg:04d}: map rows {sorted(mapped)} "
                            f"!= present rows {sorted(present)}")
    zi = 0
    for r in rows:
        key = locus_key(r["locus"])
        while zi + 1 < len(ZONES) and key >= tuple(ZONES[zi + 1]["start"]):
            zi += 1
        owner = split_owner.get(key, ZONES[zi]["tlg"])
        zone_rows[owner].append(r)

    # ---- per-zone accounting + word-count sanity ----------------------------
    tlg2zone = {z["tlg"]: z for z in ZONES}
    zone_stats = {}
    for tlg, zrows in zone_rows.items():
        z = tlg2zone[tlg]
        zgk = gk_total(zrows)
        est_words = zgk / 5.5
        ratio = round(est_words / z["wc"], 2) if z["wc"] else None
        zone_stats[tlg] = {
            "slug": z["slug"], "act": z["act"], "caag": z["caag"],
            "printed_pp": z["pp"], "start": list(z["start"]),
            "rows": len(zrows), "greek_chars": zgk,
            "est_words": int(est_words), "canon_wc": z["wc"], "ratio": ratio}
        if ratio is not None:
            if not 0.25 <= ratio <= 4 and z["wc"] >= 300:
                problems.append(f"{tlg}: est words {int(est_words)} vs canon "
                                f"{z['wc']} (ratio {ratio}) - zone mis-scoped?")
            elif not 0.5 <= ratio <= 2.5:
                flags.append(f"{tlg}: word-count ratio {ratio} "
                             f"(est {int(est_words)} vs canon {z['wc']})")
    empty = [z["tlg"] for z in ZONES if z["tlg"] not in zone_rows]
    if empty:
        problems.append(f"zones with NO rows: {empty}")

    # ---- probes for the sec zones -------------------------------------------
    probes = {}
    for z in ZONES:
        if z["act"] != "sec":
            continue
        target_rows = load(CORPUS / f"{z['sec_target']}.jsonl")
        if not target_rows:
            problems.append(f"{z['tlg']}: sec target {z['sec_target']} has no "
                            f"corpus file")
            continue
        span_grams = chargrams(" ".join(r["text"] for r in zone_rows[z["tlg"]]))
        target_rows.sort(key=lambda r: -greek(r.get("text", "")))
        conts = []
        for r in target_rows[:5]:
            g = chargrams(r["text"])
            conts.append(round(len(g & span_grams) / len(g), 3) if g else 0.0)
        ok = sum(c >= PROBE_MIN_CONT for c in conts) >= PROBE_MIN_PASS
        probes[z["tlg"]] = {"target": z["sec_target"], "containments": conts,
                            "min": [PROBE_MIN_PASS, PROBE_MIN_CONT], "pass": ok}
        if not ok:
            problems.append(f"{z['tlg']}: containment probes FAILED for "
                            f"{z['sec_target']}: {conts}")

    # ---- guards --------------------------------------------------------------
    for z in ZONES:
        if z["act"] == "new" and (CORPUS / f"{z['slug']}.jsonl").exists():
            problems.append(f"guard: corpus/{z['slug']}.jsonl already exists")
    for fp in CORPUS.glob("*.jsonl"):
        if fp.name == f"{OLD}.jsonl":
            continue
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        if re.search(rf"{BASE}_0(29[5-9]|[34]\d\d|50[01])\.", txt):
            problems.append(f"guard: {fp.name} already serves {BASE} pages "
                            f"in 0295-0501")
    cw = json.loads(CW_PATH.read_text(encoding="utf-8"))
    for z in ZONES:
        if z["act"] == "new" and z["slug"] in cw:
            flags.append(f"crosswalk already has {z['slug']} -> "
                         f"{cw[z['slug']].get('tlg')} (will not overwrite)")

    # ---- Greek conservation ---------------------------------------------------
    post_gk = sum(gk_total(v) for v in zone_rows.values())
    n_out = sum(len(v) for v in zone_rows.values())
    ok = post_gk >= COVER_TOL * pre_gk and n_out == len(rows)
    report["greek_accounting"] = {
        "before": pre_gk, "planned_out": post_gk,
        "rows_in": len(rows), "rows_out": n_out,
        "keep_ratio": round(post_gk / pre_gk, 6), "invariant_ok": ok}
    if not ok:
        problems.append("conservation invariant failed (rows or Greek lost)")

    # ---- multi-owner (boundary) pages, for the report -------------------------
    page_owners = defaultdict(set)
    for tlg, zrows in zone_rows.items():
        for r in zrows:
            page_owners[locus_key(r["locus"])[0]].add(tlg2zone[tlg]["slug"])
    report["boundary_pages"] = {
        f"{p:04d}": sorted(o) for p, o in sorted(page_owners.items())
        if len(o) > 1}
    report["zones"] = zone_stats
    report["probes"] = probes
    report["problems"], report["flags"] = problems, flags

    # ---- print -----------------------------------------------------------------
    print(f"=== {len(rows)} rows / {pre_gk:,} Greek chars -> {len(ZONES)} zones; "
          f"conservation {post_gk / pre_gk:.4%} ok={ok}")
    print(f"=== boundary pages with >1 owner: {len(report['boundary_pages'])}; "
          f"missing scan pages: {missing_pages}")
    for z in ZONES:
        st = zone_stats.get(z["tlg"], {})
        print(f"    {z['act']:4s} {z['caag']:24s} {z['tlg']:13s} "
              f"{st.get('rows', 0):4d} rows {st.get('greek_chars', 0):7,} gk "
              f"ratio={st.get('ratio')} -> {z['slug']}")
    for tlg, pr in probes.items():
        print(f"    probe {'PASS' if pr['pass'] else 'FAIL'} {tlg} "
              f"{pr['containments']} -> {pr['target']}")
    for f in flags:
        print(f"    flag: {f}")
    for p in problems:
        print(f"    !! {p}")
    out = SCRATCH / "dissolve_pelagius_caag3_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"report -> {out}")

    if not args.apply:
        print("DRY RUN - nothing written (use --apply)")
        return
    if problems:
        sys.exit("ABORT: problems listed above; nothing written")

    # ---- writes -----------------------------------------------------------------
    ours = re.compile(rf"^{re.escape(BASE)}_\d+\.\d+$")
    for z in ZONES:
        zrows = zone_rows[z["tlg"]]
        if z["act"] == "keep":
            dump(CORPUS / f"{OLD}.jsonl", zrows)   # urn unchanged
            print(f"    rewrote corpus/{OLD}.jsonl: {len(zrows)} rows (kept zone)")
        elif z["act"] == "new":
            dump(CORPUS / f"{z['slug']}.jsonl",
                 [dict(r, urn=z["slug"]) for r in zrows])
            print(f"    wrote corpus/{z['slug']}.jsonl: {len(zrows)} rows")
        else:                                       # sec: edition witness
            fp = SECONDARY / f"{z['slug']}.jsonl"
            foreign = [r for r in load(fp)
                       if not ours.match(str(r.get("locus", "")))]
            new = [dict(r, urn=z["slug"], rank="secondary",
                        secondary_reason=SEC_REASON) for r in zrows]
            dump(fp, foreign + new)
            print(f"    wrote secondary/{z['slug']}.jsonl: {len(new)} rows"
                  + (f" + {len(foreign)} foreign kept" if foreign else ""))

    # crosswalk: entries for the new primaries (canon-verified ids only)
    added = []
    for z in ZONES:
        if z["act"] != "new" or z["slug"] in cw:
            continue
        entry = {"cts": z["cts"], "tlg": z["cts"].split("greekLit:")[-1],
                 "author_slug": z["slug"].split(".")[0],
                 "title": z.get("title", "")}
        if z["tlg"].endswith(".X01"):
            entry["note"] = ("canon dubium (no TLG digital text); in CAAG a "
                            "title-only section (IV.xxi, printed p. 299): "
                            "Berthelot notes the text = Ostanes IV.ii "
                            "(dissolve_pelagius_caag3.py 2026-07-10)")
        if z.get("slug", "").startswith("fragmenta-alchemica.") and "title" in z \
                and z["tlg"] in ("tlg1379.030", "tlg1379.053"):
            entry["note"] = ("slug minted here (canon title empty); id "
                            "verified by canon page range + word count "
                            "(dissolve_pelagius_caag3.py 2026-07-10)")
        cw[z["slug"]] = entry
        added.append(z["slug"])
    CW_PATH.write_text(json.dumps(cw, ensure_ascii=False, indent=0),
                       encoding="utf-8")
    with TSV_PATH.open("w", encoding="utf-8") as f:
        f.write("slug\tcts_urn\ttlg\n")
        for s, d in sorted(cw.items()):
            if d.get("cts"):
                f.write(f"{s}\t{d['cts']}\t{d['tlg']}\n")
    print(f"    crosswalk: +{len(added)} entries; tsv regenerated")

    # post-write invariant: every served berthelot locus in 0295-0501 has
    # exactly one primary owner
    owners = defaultdict(set)
    for fp in CORPUS.glob("*.jsonl"):
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        if BASE not in txt:
            continue
        for line in txt.splitlines():
            if not line.strip():
                continue
            loc = str(json.loads(line).get("locus", ""))
            if loc.startswith(BASE):
                k = locus_key(loc)
                if 295 <= k[0] <= 501:
                    owners[k].add(fp.name[:-6])
    multi = {f"{p}.{l}": sorted(o) for (p, l), o in owners.items() if len(o) > 1}
    if multi:
        sys.exit(f"INVARIANT VIOLATION - loci with >1 primary owner: "
                 f"{list(multi.items())[:5]}")
    print(f"applied. {len(owners)} loci each have exactly one primary owner.\n"
          f"Now run (main session, after review):\n"
          f"  scripts/rekey_corrections_log.py --write\n"
          f"  scripts/reconcile_corpus_editions.py")


if __name__ == "__main__":
    main()
