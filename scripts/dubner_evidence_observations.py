"""Occurrence decisions from the two pinned Dübner scans, reviewed 2026-10-25.

The later layer does not rewrite the frozen scope or reading reviews. Narrow
duplicate extracts remain literal, attributed evidence outside lexical voting;
they are not additional printed occurrences or independent OCR vote groups.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = "data/corpus_changes/dubner-evidence-review"
PREDECESSOR_AUTHORITY = "384b11420e68a046812aa17cb1f640fc2e1607063d960620afcc9bb2e1288327"
PREDECESSOR_NETWORK = "9fcffbe336778981a50eaddace65de0b4aab6047e597726477c06cc23f5a821e"
CAPTURE_MANIFEST_SHA256 = "e94f026e73ebc730380f299149b8392856a56c3a13bffe1773e7948d85867afb"

# Exact cells in the literal Harvard lanes. Empty cells, delimiters, and line
# endings also survive in the routing record. These are source decisions for
# these three pages, not a heuristic for other delimiter-bearing OCR.
LAYOUTS = {
    "equites:0094": {
        "pages": (94, 95), "lines": 127, "column": "left",
        "duplicate_lines": (54,55,56,57,58,59,61,62,65,66,67,68,69,70,71,
            73,74,75,76,77,79,88,89,90,91,92,93,94,95,96,97,98,99,100,
            101,102,103,104,105,106,107),
        "observation": "Lines 1–53 give the full left column, from the continuation παιστοι to τῇ πτήσει. The left cells in the named later lines repeat clipped ends of that column. The remaining right cells and unmarked lines continue the right column from τουτέστιν εὐμεταβλήτους through Καλλίαν αἰνίττεται. The print contains each column once.",
    },
    "equites:0107": {
        "pages": (107, 108), "lines": 67, "column": "right",
        "duplicate_lines": tuple(range(1,55)),
        "observation": "Left cells 1–54 give the full left column ending Ἀθη-. Unmarked lines 55–67 give the full right column from ναῖοι to the end of scholion 883. Right cells 1–54 are clipped, overlapping extracts of that same right column, not a second passage. Their numeral disagreements and truncated readings remain literal evidence.",
    },
    "aves:0271": {
        "pages": (271, 298), "lines": 57, "column": "right",
        "duplicate_lines": (*range(1,11), *range(12,49), 55, 56),
        "observation": "Left cells 1–54 give the full left column ending αὐτῷ. Unmarked line 57 transcribes the right column from ταῖς εὐωχίαις to the terminal Πει-. The narrow right cells repeat fragments within that column, including reordered pieces of scholion 873. Their readings are preserved outside lexical voting; no source letters or missing left-column words are supplied from them.",
    },
}

# Direct PDF crops, normalized rectangles, with surrounding printed context.
# The full-page captures for the held layouts are retained by the older layer.
CAPTURES = {
    **{f"toronto-{p:04d}-{side}": ("toronto",p,box) for p in (94,107,271)
       for side,box in (("left",(.01,.04,.53,.94)),("right",(.47,.04,.99,.94)))},
    "harvard-0095-right": ("harvard",95,(.44,.04,.97,.94)),
    "harvard-0298-phorbeia": ("harvard",298,(.44,.27,.97,.37)),
    "toronto-0190-phorbeia": ("toronto",190,(.44,.45,.99,.80)),
    "harvard-0199-phorbeia": ("harvard",199,(.43,.45,.97,.80)),
    "toronto-0449-notes": ("toronto",449,(.01,.04,.99,.94)),
    "toronto-0656-corrigenda": ("toronto",656,(.01,.59,.99,.78)),
    "toronto-0767-index": ("toronto",767,(.01,.04,.99,.94)),
}

# (page network, slot after the source layout review, original tied readings,
# corrected printed form, column, additional evidence captures).
# Original votes and every contrary reading remain in each corrected slot.
READINGS = (
    ("equites:0094",3,("μακρόν","μαχρόν"),"μακρόν","left",()),
    ("equites:0094",41,("καθῆκε","καθῆχε"),"καθῆκε","left",()),
    ("equites:0094",218,("Τυρῶ","Τυφῶ"),"Τυφῶ","left",()),
    ("equites:0094",220,("Τυρὼς","Τυφὼς"),"Τυφὼς","left",()),
    ("equites:0094",253,("Τυρὼς","Τυφὼς"),"Τυφὼς","left",()),
    ("equites:0094",257,("πυρός","τυφὼς"),"πυρός","left",()),
    ("equites:0094",293,("Τυρὼς","Τυφὼς"),"Τυφὼς","left",()),
    ("equites:0094",305,("Τυρῶ","Τυφῶ"),"Τυφῶ","left",()),
    ("equites:0094",314,("ὑπερίσταθαι","ὑπερτίθεσθαι"),"ὑπερτίθεσθαι","left",()),
    ("equites:0094",316,("μέλειν","μέλλειν"),"μέλλειν","left",()),
    ("equites:0094",599,("κατακλύσει","καταχλύσει"),"κατακλύσει","right",()),
    ("equites:0094",624,("","ἀρελῶν"),"ἀφελῶν","right",("harvard-0095-right","toronto-0449-notes")),
    ("equites:0094",625,("","πεδίον"),"πεδίων","right",("harvard-0095-right",)),
    ("equites:0094",669,("φόβον","ψόφον"),"ψόφον","right",("harvard-0095-right",)),
    ("equites:0094",698,("","ἀρελέας"),"ἀφελές","right",("harvard-0095-right","toronto-0449-notes")),
    ("equites:0107",21,("θαλαττοκρατεῖν","θαλαττοχρατεῖν"),"θαλαττοκρατεῖν","left",()),
    ("equites:0107",74,("προσδοκᾶτε","προσδοχᾶτε"),"προσδοκᾶτε","left",()),
    ("equites:0107",245,("συμπένθουσιν","συμπνέουσιν"),"συμπνέουσιν","left",()),
    ("equites:0107",252,("συμπένθουσι","συμπνέουσι"),"συμπνέουσι","left",()),
    ("equites:0107",256,("δοτρακινδοῦ","ὀστρακίνδα"),"ὀστρακίνδα","left",()),
    ("equites:0107",259,("ἐξostraχίσαι","ἐξοστρακίσαι"),"ἐξοστρακίσαι","left",()),
    ("equites:0107",272,("ἐξostraχισθῆναι","ἐξοστρακισθῆναι"),"ἐξοστρακισθῆναι","left",()),
    ("equites:0107",278,("ἐξostraχισμοῦ","ἐξοστρακισμοῦ"),"ἐξοστρακισμοῦ","left",()),
    ("equites:0107",322,("ἐκατοσχιλίων","ἐξακισχιλίων"),"ἐξακισχιλίων","left",()),
    ("equites:0107",335,("ἐκατοσχιλία","ἐξακισχίλια"),"ἐξακισχίλια","left",()),
    ("equites:0107",421,("πόρπακας","πόρπαχας"),"πόρπακας","right",()),
    ("equites:0107",429,("πόρπακας","πόρπαχας"),"πόρπακας","right",()),
    ("aves:0271",41,("Περσικόν","Περσιχόν"),"Περσικόν","left",()),
    ("aves:0271",70,("Προσκαλτίσις","Προσπαλτίοις"),"Προσπαλτίοις","left",()),
    ("aves:0271",106,("φυλακῆς","φυλαχῆς"),"φυλακῆς","left",()),
    ("aves:0271",114,("καυδονοφοροῦν","κωδωνοφορῶν"),"κωδωνοφορῶν","left",()),
    ("aves:0271",120,("περισκοποῦντες","περισχοποῦντες"),"περισκοποῦντες","left",()),
    ("aves:0271",125,("κώδυνας","κώδωνας"),"κώδωνας","left",()),
    ("aves:0271",133,("καθεύδοντα","καθυσδόντα"),"καθεύδοντα","left",()),
    ("aves:0271",174,("γέρνιδα","χέρνιδα"),"χέρνιδα","left",()),
    ("aves:0271",181,("γερνίδων","χαρινίδων"),"χερνίδων","left",()),
    ("aves:0271",191,("γέρνιψ","χέρνιφ"),"χέρνιψ","left",()),
    ("aves:0271",282,("προσodia","προσόδια"),"προσόδια","left",()),
    ("aves:0271",296,("προσδία","προσόδια"),"προσόδια","left",()),
    ("aves:0271",411,("ἐκθέσει","ἐχθέσει"),"ἐκθέσει","right",()),
    ("aves:0271",436,("φόρδιον","ὀρβιον"),"φόρβιον","right",("toronto-0767-index",)),
    ("aves:0271",440,("περικεῖμενον","περιχεῖμενον"),"περικεῖμενον","right",()),
    ("aves:0271",452,("ἐμπεφορβοιωμένον","ἐμπεφορδιωμένον"),"ἐμπεφορβειωμένον","right",("harvard-0298-phorbeia",)),
    ("aves:0271",453,("Φορβεία","Φορδειά"),"Φορβειά","right",("harvard-0298-phorbeia","toronto-0767-index")),
    ("aves:0271",467,("φορβεία","φορδειὰ"),"φορβειὰ","right",("harvard-0298-phorbeia","toronto-0767-index")),
    ("aves:0271",471,("διρθόγγου","διφθόγγου"),"διφθόγγου","right",("harvard-0298-phorbeia",)),
    ("aves:0271",474,("δευύνως","ὀξυτόνως"),"ὀξυτόνως","right",("harvard-0298-phorbeia",)),
    ("aves:0271",549,("ἐκθέσει","ἐχθέσει"),"ἐκθέσει","right",()),
    ("vespae:0190",536,("φορβείᾳ","φορβειᾷ"),"φορβειᾷ","right",("toronto-0190-phorbeia","harvard-0199-phorbeia","toronto-0767-index")),
)

NOTE_REVIEW = (
    {"id":"phorbeia-index", "captures":["toronto-0767-index"],
     "observation":"The Greek index, printed page 725, column 2, reads φορβειά Vesp. 582; Av. 861, 15 and φόρβιον Av. 861. Direct body inspection controls the accent and inflection at each occurrence; the index's OCR δ readings are not trusted as transcription."},
    {"id":"apheles-annotation", "captures":["toronto-0449-notes","harvard-0095-right"],
     "observation":"The note on Knights 527 cites Suda Ἀφελῆς and ἀφελῶς. This locates the difficult body passage, whose own scan prints ἀφελῶν and ἀφελές. The variants and additions quoted in the critical note are not inserted into the historical body."},
    {"id":"corrigenda-scope", "captures":["toronto-0656-corrigenda"],
     "observation":"The Corrigenda begin Adnot. ad Nub. and correct annotations, references, and a deletion in the note on Birds Argument II. They provide no blanket body-text replacement rule. No editorial emendation is adopted in this layer."},
)
