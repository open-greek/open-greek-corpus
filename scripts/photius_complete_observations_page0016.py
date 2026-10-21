"""Complete direct scan observations on Bekker printed page 281.

The enumerated passages were read in full, including unchanged words. These
observations are review evidence, not authority to replace the corpus with a
digital transcription. The uncertain deictic in passage 1 remains unresolved.
"""
from copy import deepcopy
import hashlib
import json

PAGE = 16
REVIEWED_AT = "2026-10-21T11:59:47Z"
PREFIX = "helladius_chrestomathia_photius_bekker_v2_0016."
LOCI = [1, *range(4, 46)]
REGIONS = {
    "L1": [.05, .09, .44, .33], "L2": [.05, .30, .44, .55],
    "L3": [.05, .52, .44, .76], "R1": [.41, .09, .83, .33],
    "R2": [.41, .30, .83, .55], "R3": [.41, .52, .83, .76],
}

# Exact historical span, direct scan observation, physical crop. The punctuation
# of the retained transcription is preserved unless explicitly listed here.
CHANGES = {
    1: [("φασιν", "φασὶν", "L1"), ("Θεὸς", "θεὸς", "L1"),
        ("λόγος γὰρ", "λόγος γάρ", "L1"),
        ("ἀλλ' ἐπενεγκόντες", "οὐκ ἐπενεγκόντες", "L1"),
        ("660 H. ", "", "L2"), ("673 R. ", "", "L3"),
        ("ἢ ἐπε-", "καὶ ἐπε-", "L3")],
    6: [("οὐδὲ ἔξω", "οὐδ’ ἔξω", "R1")],
    7: [("κἄν", "κἂν", "R1")],
    16: [("κ διὰ", "καὶ διὰ", "R1")],
    17: [("ιν τῶν", "λιν τῶν", "R1")],
    18: [("ἡ λόγῳ φύσις", "ἡ μία τοῦ λόγου φύσις", "R2")],
    19: [("σαρκομένη", "σαρκωμένη", "R2")],
    25: [("πήσαι", "πῆσαι", "R2")],
    27: [("γισάμενος", "γησάμενος", "R2")],
    29: [("ἰδιά-", "ἰδιό-", "R2")],
    30: [(" ὁδὶ Π.", "", "R2")],
    32: [("κ ἑαυτὸν ὁκ εὐαγὲς", "καὶ ἑαυτὸν ἐκ εὐαγοῦς", "R2")],
    36: [("κ τὰς", "καὶ τὰς", "R3")],
    39: [("κἄν", "κἂν", "R3")],
    45: [("σοφόρον", "στοφόρον", "R3")],
}

# These are source-confirmed retained divisions, not completed words. In
# particular, the scan prints πάλ- / λιν; the digital word πάλιν cannot silently
# remove the additional printed lambda.
FRAGMENTS = {
    1: [("ἐπε-", "trailing")], 4: [("νεγκὼν", "leading")],
    6: [("δή-", "trailing")], 7: [("λον", "leading")],
    9: [("δια-", "trailing")], 10: [("φορὰν", "leading")],
    12: [("φύ-", "trailing")], 13: [("σεων", "leading")],
    15: [("φω-", "trailing")],
    16: [("νήν", "leading"), ("πάλ-", "trailing")],
    17: [("λιν", "leading")], 18: [("σε-", "trailing")],
    19: [("σαρκωμένη", "leading")],
    24: [("ἐνανθρω-", "trailing")], 25: [("πῆσαι", "leading")],
    26: [("ἀπολο-", "trailing")], 27: [("γησάμενος", "leading")],
    29: [("ἰδιό-", "trailing")], 30: [("χειρον", "leading")],
    44: [("Χρι-", "trailing")],
    45: [("στοφόρον", "leading"), ("γρα-", "trailing")],
}

CONVENTION = (
    "Expand the printed καὶ and ου ligatures. Preserve the historical quotation "
    "delimiter convention, apostrophe shape, and paragraph whitespace. Join "
    "printed internal line divisions only where the same retained passage "
    "contains both halves; preserve passage-boundary fragments explicitly. "
    "Marginal references 660 H., 673 R., and 661 H. are not body text."
)


def _sha_row(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def _change(text, replacements):
    for old, new, _ in replacements:
        if text.count(old) != 1:
            raise ValueError(f"The reviewed page 281 source span changed: {old!r}")
        text = text.replace(old, new, 1)
    return text


def _fragments(number, text):
    result = []
    for word, side in FRAGMENTS.get(number, []):
        position = text.find(word) if side == "leading" else text.rfind(word)
        if position < 0:
            raise ValueError("A reviewed printed fragment changed")
        result.append({"start": position, "end": position + len(word), "text": word,
            "side": side, "qualification":
            "The printed word crosses this retained passage boundary. Keep the "
            "visible source fragment and exclude it from lexical counts; do not "
            "invent a completion or an adjacency across the boundary."})
    return sorted(result, key=lambda item: item["start"])


def records(rows, document, crop_png, sections):
    """Compile only the explicitly enumerated completed visual observations."""
    records = []
    for number in LOCI:
        row = rows[PREFIX + str(number)]
        text = row["text"]
        corrected = _change(text, CHANGES.get(number, []))
        crop = "L1" if number == 1 else ("R1" if number <= 17 else "R2" if number <= 32 else "R3")
        # Passage 1 occupies the complete left column; one source rectangle
        # preserves the physical extent of its unchanged and changed words.
        region = [.05, .09, .44, .76] if number == 1 else REGIONS[crop]
        image_sha = hashlib.sha256(crop_png(document, PAGE, region)).hexdigest()
        base = {"review_basis": "direct-scan-inspection", "reviewed_at": REVIEWED_AT,
            "evidence": "Direct inspection of the complete retained passage on "
                "Bekker physical page 16 / printed page 281 in overlapping enlarged "
                "left- or right-column crops, followed by close inspection of "
                "the negative, deictic, proper name, and εὐαγοῦς regions. All "
                "words in this segment were compared, including unchanged text.",
            "transcription_convention": CONVENTION}
        def segment(start, end, original, observed, verification="verified", **extra):
            return {**deepcopy(base), "start": start, "end": end,
                "original_text": original, "corrected_text": observed,
                "verification": verification,
                "scan": {"physical_page": PAGE, "region": region,
                    "image_sha256": image_sha, "observed_text": observed}, **extra}
        if number == 1:
            word = "ἀκὴν"
            start = text.index(word)
            before = _change(text[:start], [c for c in CHANGES[1] if c[0] in text[:start]])
            after = _change(text[start+len(word):], [c for c in CHANGES[1] if c[0] in text[start+len(word):]])
            first = segment(0, start, text[:start], before)
            uncertain = segment(start, start+len(word), word, word, "uncertain",
                uncertainty="The compact printed deictic after ὑποστήσαντες is "
                    "not legible enough to certify its final letters. The digital "
                    "ἐκεῖνον differs from the historical ἀκὴν. Neither reading "
                    "is admitted as a resolved lexical form.")
            uncertain["scan"]["observed_text"] = "ἐκεῖν…"
            digital = sections["tlg4040-tlg001-local002-s293"]
            alternative = "ἐκεῖνον"
            low = digital.index(alternative)
            uncertain["readings"] = [{"kind": "digital", "section": "tlg4040-tlg001-local002-s293",
                "start": low, "end": low + len(alternative), "text": alternative}]
            final = segment(start+len(word), len(text), text[start+len(word):], after)
            final["fragments"] = _fragments(number, after)
            segments, status = [first, uncertain, final], "reviewed-with-uncertainty"
        else:
            whole = segment(0, len(text), text, corrected)
            # Exact source pointers preserve both agreeing observations and
            # the explicitly checked differing readings. They do not cast a
            # vote outside this bounded historical passage.
            digital = sections["tlg4040-tlg001-local002-s293"]
            alternative = {
                6: "ἄσαρκος οὐδὲ ἔξω σώματος, ἀλλ’ ἴδιον ἔχων αὐτό (δῆ",
                17: "ιν τῶν συνελθόντων εἰς ἕνωσιν ἀδιαιρέτως ἑκάτερον,",
                27: "γησάμενος φωνῆς, καὶ τὰ αὐτὰ τὴν ἐν Χαλκηδόνι",
                32: "ἀπαλλάττει δὲ καὶ ἑαυτὸν ἐκ εὐαγὲς ὑπονοίας, ἣν περὶ",
            }.get(number, corrected.rstrip("-"))
            if alternative in digital:
                if digital.count(alternative) != 1:
                    raise ValueError("The reviewed digital window became ambiguous")
                low = digital.index(alternative)
                whole["readings"] = [{"kind": "digital", "section": "tlg4040-tlg001-local002-s293",
                    "start": low, "end": low + len(alternative), "text": alternative}]
            whole["fragments"] = _fragments(number, corrected)
            segments, status = [whole], "reviewed-verified"
        records.append({"locus": row["locus"], "original_row_sha256": _sha_row(row),
                        "status": status, "segments": segments})
    return records
