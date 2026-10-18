#!/usr/bin/env python3
"""Pin source-reviewed strips for particular failed Photius checkpoints."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_photius_coverage import ROOT, build, build_later_gap, build_page13_retry

CHECKPOINT38 = {"model": "Qwen/Qwen3.8-27B-FP8", "revision": "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"}
CHECKPOINT36 = {"model": "Qwen/Qwen3.6-27B", "revision": "6a9e13bd6fc8f0983b9b99948120bc37f49c13e9"}


def column_strips(top, bottom, left_cuts, right_cuts):
    result = []
    for side, x0, x1, cuts in (("left", .045, .495, left_cuts), ("right", .505, .97, right_cuts)):
        limits = [top, *cuts, bottom]
        result.extend((f"{side}-{name}", [x0, low, x1, high])
                      for name, low, high in zip(("upper", "middle", "lower"), limits, limits[1:]))
    return result


def body_columns(top, bottom):
    return [("left-body", [.045, top, .495, bottom]),
            ("right-body", [.505, top, .975, bottom])]


REVIEWS = {
    41: {"strips": body_columns(.060, .839), "checkpoints": [CHECKPOINT36],
         "evidence": "Printed page29 continues the Procopius narrative. The original Qwen3.6 includes small numbered variants, including στρατείας mg and στρατείας s, after the large body. Enlarged source inspection places the last body lines above.839 and the apparatus below.850. The two column crops retain every large body line and exclude the running header and smaller notes.",
         "failure": "The stop-terminated Qwen3.6 original includes critical apparatus. Preserve that original as evidence and retain the independent Qwen3.8 whole-page reading."},
    27: {"strips": [("left-upper", [.035, .055, .49, .318]),
                    ("left-middle", [.035, .318, .49, .574]),
                    ("left-lower", [.035, .574, .49, .848]),
                    ("right-upper", [.495, .055, .975, .295]),
                    ("right-middle", [.495, .295, .975, .5895]),
                    ("right-lower", [.495, .5895, .975, .848])],
         "evidence": "Printed page15 continues codex54, then contains codices55–57. The sentence ἔσφαγη, ἢ ὡς ἄλλοι φασίν, ἠφανίσθη occurs once in codex57; the source then continues its account of the later Roman kings. The original Qwen3.8 instead repeats that sentence and the following phrase122 times despite stop termination. Enlarged interline checks preserve every body line and heading in these six strips; the lower boundary excludes smaller apparatus.",
         "failure": "A stop-terminated Qwen3.8 original contains a source-confirmed repetition loop. The independent Qwen3.6 whole-page reading remains its vote."},
    47: {"cut": .458, "top": .065, "bottom": .848,
         "evidence": "Printed page 35 begins codex 70, continues codex 71 from the left-column foot into the right-column top, then begins codex 72. The four crop boundaries retain complete authorial lines and stop above the smaller apparatus. The horizontal split at .458 lies in a blank interline gap in both columns.",
         "failure": "Qwen3.8 repeats Greek function words and reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
    49: {"strips": body_columns(.058, .817), "checkpoints": [CHECKPOINT36],
         "evidence": "Printed page37 continues the Persian narrative. The original Qwen3.6 appends the smaller numbered apparatus, including add and post ἐπτακισχίλιοι cum A omisi δύο. Source inspection places both body-column feet above.817 and the apparatus below.828. The two enlarged columns preserve every large body line and exclude the running header and small notes.",
         "failure": "The stop-terminated Qwen3.6 original leaks printed critical apparatus into its body reading. Retain it as evidence; the independent Qwen3.8 whole-page reading stays intact."},
    50: {"cut": .456, "top": .062, "bottom": .835,
         "evidence": "Printed page 38 continues codex 72 in two columns. The four crops include every large Greek body line; the last right-column line ends with the opening of Xerxes' campaign against the Greeks. The horizontal split at .456 lies between complete lines; the lower boundary excludes the smaller apparatus.",
         "failure": "Qwen3.8 repeats καὶ and reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
    87: {"strips": [("left-upper", [.045, .061, .495, .318]),
                    ("left-middle", [.045, .318, .495, .580]),
                    ("left-lower", [.045, .580, .495, .840]),
                    ("right-upper", [.505, .061, .97, .318]),
                    ("right-middle", [.505, .318, .97, .580]),
                    ("right-lower", [.505, .580, .97, .840])],
         "evidence": "Printed page75 continues the dramatic narrative in two columns. The six strips retain every large Greek body line, including the lower right paragraph beginning Ἀλλ’ ὅ γε Τύρος καὶ Εὐφράτης. Both horizontal boundaries lie between complete lines; the bottom at.840 stops above the smaller apparatus beginning at.850. Reading order is the entire left column followed by the entire right column.",
         "failure": "The original Qwen3.8 page attempt reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
    83: {"strips": body_columns(.067, .838), "checkpoints": [CHECKPOINT36],
         "evidence": "Printed page71 continues the post-Alexander narrative. Qwen3.6 appends the smaller numbered apparatus, including τὸ add A and malim δορῶν with a Bast palaeography reference. Source inspection confirms the last large body lines above.838 and the small notes below.847. The two enlarged crops include complete body columns while excluding the running header and apparatus.",
         "failure": "The stop-terminated Qwen3.6 original leaks critical notes. Retain every original reading; the independent Qwen3.8 whole-page reading stays intact."},
    105: {"strips": column_strips(.061, .840, [.340, .601], [.322, .620]),
          "evidence": "Printed page93 contains the continuation of the Origen-related notice, codex119 on Pierius, and the opening of codex120 on Epiphanius. The six strips retain the complete large body in column order. Left boundaries fall before a new paragraph and the119 heading; the lower right boundary falls before the120 heading. Enlarged boundary checks include descenders and exclude the smaller apparatus below.840.",
          "failure": "The original Qwen3.8 page attempt reaches its output limit. The successful Qwen3.6 whole-page reading remains its vote."},
    109: {"strips": column_strips(.070, .850, [.383, .588], [.387, .611]),
          "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page97 includes codex131, the grouped132–135 notices, codices136/137 at the left foot, and codex138 on Eunomius in the right column. The enlarged boundary review preserves every large Greek line and heading, including descenders. Left splits fall between paragraphs and before the136 heading. The bottom at.850 falls between the last body line and smaller apparatus; column order is unchanged.",
          "failure": "The original Qwen3.6 page attempt reaches its output limit. The successful Qwen3.8 whole-page reading remains its vote."},
    112: {"strips": column_strips(.063, .844, [.285, .587], [.3425, .605]),
          "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page100 continues the lexicon notices153–158. The left splits precede the154 and157 headings. The right splits lie between complete body lines, checked with enlarged source crops to preserve descenders. The bottom at.844 retains the final body lines in both columns and stops above the smaller apparatus. Every authorial line remains in left-then-right column order.",
          "failure": "The original Qwen3.6 page attempt reaches its output limit. The successful Qwen3.8 whole-page reading remains its vote."},
    113: {"strips": [("left-first", [.045, .065, .495, .251]),
                     ("left-second", [.045, .251, .495, .454]),
                     ("left-third", [.045, .454, .495, .6575]),
                     ("left-fourth", [.045, .6575, .495, .813]),
                     ("right-first", [.505, .065, .97, .253]),
                     ("right-second", [.505, .253, .97, .490]),
                     ("right-third", [.505, .490, .97, .640]),
                     ("right-fourth", [.505, .640, .97, .813])],
          "evidence": "Printed page101 continues codex158 on Phrynichus and opens codex159 on Isocrates. The right column is especially faint. Eight shorter strips preserve each complete large Greek line in column order; the final right split precedes the159 heading. Enlarged boundary checks preserve descenders and the breathing marks above the following lines. The bottom at.813 excludes the smaller critical apparatus. The body contains no long dotted lacuna requiring a special ellipsis instruction.",
          "failure": "The original Qwen3.8 attempt reaches its output limit and triggers the frozen mark-loss screen. The Qwen3.6 whole-page reading remains its independent vote; the retry still requires completed source and mark review."},
    119: {"strips": body_columns(.068, .853), "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page107 contains the rhetorical notices. Qwen3.6 appends small numbered variants including ὧν add A and κεχρημένος om pr C. Source inspection confirms that.853 preserves the full-size body in both columns and excludes the apparatus beginning below.865; the upper boundary excludes the running header without cutting the first body line.",
          "failure": "The stop-terminated Qwen3.6 original includes critical apparatus. Its raw text remains held evidence; the independent Qwen3.8 whole-page reading stays intact."},
    147: {"strips": body_columns(.063, .852), "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page135 continues the mythographic narrative. Qwen3.6 appends smaller numbered variants and Ruhnken/Velleius references. The full-size left and right body feet remain above.852; apparatus starts below.860. Source-checked full-column crops preserve the body and exclude both running header and critical notes.",
          "failure": "The stop-terminated Qwen3.6 original leaks small-type critical notes. Preserve that attempt without another vote; the Qwen3.8 whole-page reading stays intact."},
    181: {"strips": body_columns(.056, .841), "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page169 contains the medical discussion. Qwen3.6 appends the smaller apparatus, including διὰ om A and the parenthetical Latin littera o a correctore posita. The two body columns end above.841; notes begin below.848. Source-checked crops preserve the last large Greek line in each column and exclude all smaller notes.",
          "failure": "The stop-terminated Qwen3.6 original includes apparatus. Preserve the full original as evidence; the Qwen3.8 whole-page reading stays intact."},
    188: {"strips": body_columns(.056, .843), "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page176 continues the scientific notices. Qwen3.6 appends the smaller critical apparatus, including Rothomagensis, libri scripti, and post εὐπόρισα in A vacui. The large body feet end above.843 and notes begin below.851. Source-checked full-column crops preserve all body lines while excluding the running header and apparatus.",
          "failure": "The stop-terminated Qwen3.6 original includes small-type critical notes. Keep that attempt and every variant; the Qwen3.8 whole-page reading stays intact."},
    192: {"strips": body_columns(.062, .864), "checkpoints": [CHECKPOINT38],
          "evidence": "Printed page180 continues codex221 on Aetius. The Qwen3.8 original skips most of the left column after its opening paragraph, jumps to ἐν δὲ τῷ τελευταίῳ in the right column, reorders right-column passages, and appends the smaller apparatus beginning a.2 libri μέτρου. Source-checked two-column crops retain every large Greek body line in left-then-right order. The body foot remains above.864 and the smaller notes below.874; the top excludes the running header.",
          "failure": "The stop-terminated Qwen3.8 original omits and reorders body passages and leaks apparatus. Preserve it as evidence, require complete source coverage of each retry column, and retain the independent Qwen3.6 whole-page reading."},
    207: {"strips": body_columns(.058, .794), "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page195 contains large Greek body above a substantial small-type apparatus with Greek quotations and Latin citations. The original Qwen3.6 includes the apparatus, including post and malim readings. Enlarged source inspection places the full-size body foot above.794 and the first smaller note below.805. The two column crops preserve all large body lines while excluding the notes and running header.",
          "failure": "The stop-terminated Qwen3.6 original includes critical apparatus. Preserve that attempt and all source readings; the independent Qwen3.8 whole-page reading remains intact."},
    232: {"strips": column_strips(.064, .848, [.32855, .58702], [.32895, .58861]), "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page220 continues codex223 on Diodorus. Six source-checked strips preserve both complete large Greek columns in left-then-right order. Enlarged interline checks place each split between full lines without clipping breathings or descenders. The top excludes the running header; the bottom at.848 lies below the final body lines and above the smaller apparatus. The original Qwen3.6's repeated function words are absent from the source.",
          "failure": "The original Qwen3.6 reaches its output limit during a repetition loop. Preserve it as evidence and retain the independent Qwen3.8 whole-page reading."},
    233: {"strips": column_strips(.064, .849, [.33294, .59026], [.33373, .59105]),
          "evidence": "Printed page221 continues codex223 on Diodorus and fate. Six source-checked strips retain both complete large Greek columns in reading order. Enlarged interline checks preserve every line, breathing, accent, and descender at the cuts. The upper boundary excludes the running header; the lower boundary at.849 lies below both body feet and above the smaller apparatus. The original Qwen3.8's repeated text does not occur in the scan.",
          "failure": "The original Qwen3.8 reaches its output limit while repeating text. Preserve that original as evidence and retain the independent Qwen3.6 whole-page reading."},
    234: {"strips": column_strips(.065, .869, [.31382, .59100], [.31223, .58941]), "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page222 finishes codex223 and begins codex224 on Memnon in the right column. The faint page retains complete large Greek columns and the224 heading inside six reviewed strips. Enlarged interline checks preserve accents, breathings, and descenders at each split. The bottom at.869 lies between the last body lines and smaller apparatus; the top excludes the running header.",
          "failure": "The original Qwen3.6 reaches its output limit while repeating text. Preserve it as evidence and retain the independent Qwen3.8 whole-page reading."},
    239: {"strips": body_columns(.054, .838), "checkpoints": [CHECKPOINT38],
          "evidence": "Printed page227 continues codex224 on Memnon and the Heraclea narrative. The Qwen3.8 original appends the smaller apparatus, including addendus articulus, after the body. Source-checked full-column crops preserve every large Greek line. The upper boundary at.054 lies below the running header and above the first line's breathings; the lower boundary at.838 lies below both body feet and above the smaller notes.",
          "failure": "The stop-terminated Qwen3.8 original leaks critical apparatus into its body reading. Keep that original as evidence and retain the independent Qwen3.6 whole-page reading."},
    242: {"strips": column_strips(.060, .847, [.25249, .60613], [.32497, .60295]), "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page230 continues codex224 on Memnon, with the Heraclea narrative in the left column and Mithridates in the right. Six enlarged source-checked strips retain every large Greek body line. The first left split lies between paragraphs before the Pontus narrative; other interline splits preserve accents, breathings, and descenders. The top excludes the running header and the bottom at.847 lies above the smaller apparatus.",
          "failure": "The original Qwen3.6 reaches its output limit during a repetition loop. Preserve it as evidence and retain the independent Qwen3.8 whole-page reading."},
    381: {"strips": column_strips(.057, .818, [.31504, .58945], [.33096, .60530]),
          "evidence": "Printed page369 contains Himerius excerpts and their preface headings in two columns. The original Qwen3.8 repeats ὅτι in a stop-terminated loop absent from the scan. Enlarged interline checks preserve all large Greek lines and headings in six consecutive column strips. The lower boundary at.818 lies above the smaller apparatus; the first left split follows a preface heading and the right splits lie between complete lines.",
          "failure": "The stop-terminated Qwen3.8 original contains a source-confirmed repetition loop. Retain that original and the independent Qwen3.6 whole-page reading."},
    384: {"strips": column_strips(.055, .825, [.41476, .63303], [.26447, .50186]),
          "evidence": "Printed page372 continues the Himerius excerpts in codex243. Six source-checked strips preserve every large Greek line and preface heading. The left upper split precedes τὸ προοίμιον; the right lower split precedes the Cappadocian proconsul heading. Enlarged boundaries preserve descenders and breathings. The bottom at.825 lies between the body foot and smaller apparatus.",
          "failure": "The original Qwen3.8 attempt reaches its output limit. Preserve that attempt; the independent Qwen3.6 whole-page reading remains intact."},
    385: {"strips": column_strips(.057, .815, [.31552, .58907], [.31473, .60570]), "checkpoints": [CHECKPOINT36],
          "evidence": "Printed page373 continues the Himerius excerpts, including the prefaces addressed to Julius, Plotius, and Salvius. Six enlarged strips preserve every large Greek body line and heading in left-then-right column order. Source-checked interline boundaries retain accents, breathings, and descenders. The top excludes the running header; the bottom at.815 lies between the final body lines and smaller apparatus. The original Qwen3.6's repeated function-word run is absent from the scan.",
          "failure": "The original Qwen3.6 reaches its output limit and triggers the frozen mark-loss screen while repeating text. Retain it as evidence, require completed source and mark review of the retry, and keep the independent Qwen3.8 whole-page reading."},
    388: {"strips": column_strips(.060, .811, [.43767, .72703], [.30271, .56033]),
          "evidence": "Printed page376 continues the Himerius excerpts with a particularly faint left column. Six source-checked strips preserve every large Greek line and heading, including the preface heading below the first left split and the next excerpt below the second. Enlarged interline checks preserve accents, breathings, and descenders. The lower boundary at.811 excludes the small apparatus beneath the body.",
          "failure": "The original Qwen3.8 attempt reaches its output limit. Preserve that attempt and the independent Qwen3.6 whole-page reading."},
    397: {"strips": column_strips(.060, .839, [.32507, .58100], [.32507, .58100]),
          "evidence": "Printed page385 continues the two-column narrative. The original Qwen3.8 ends with repeated τὸν sequences absent from the scan, although it reports stop termination. Six source-checked strips retain the complete large Greek body; enlarged interline checks preserve every line, breathing, and descender in both faint columns. The bottom at.839 lies above the smaller apparatus.",
          "failure": "The stop-terminated Qwen3.8 original contains a source-confirmed repetition loop. Preserve that attempt and retain the independent Qwen3.6 whole-page reading."},
    396: {"strips": column_strips(.057, .814, [.33413, .58980], [.31621, .58980]),
          "evidence": "Printed page384 continues codex244 on Diodorus. Six enlarged strips retain the full large Greek body in column order. The second left split precedes the centered Ἐκ τοῦ λδ heading; enlarged interline checks preserve every accent, breathing, and descender. The bottom at.814 lies below the final body lines and above the small apparatus. The original Qwen3.8's repeated function words are absent from the source.",
          "failure": "The original Qwen3.8 reaches its output limit and triggers the frozen mark-loss screen during a repetition loop. Preserve that attempt; completed source and mark review is required before this assembly can replace its single vote."},
}

# New checkpoint-specific requests never alter a previously queued manifest.
EXTRA_REVIEWS = {
    "0047-qwen36": {"page": 47, "checkpoints": [CHECKPOINT36],
                    "failure": "The stop-terminated Qwen3.6 original ends codex72 with an unprinted repeated ἢ sequence. Source inspection confirms further body text after that point. Use the same reviewed four strip boundaries in this separately pinned checkpoint request; retain the original and the independent Qwen3.8 retry assembly."},
}

SUPPLEMENT_REVIEWS = {
    (397, "right-lower"): {
        "cuts": [.581, .67023, .76089, .839],
        "evidence": "The completed provider-policy Qwen3.8 right-lower retry on printed page385 retains only1 breathing among525 Greek letters, although multiple initial-vowel breathings remain visible in the source. The frozen rule flags this systematic loss while accents remain. Three shorter crops exactly partition that lower-right strip at source-checked blank interline gaps, retaining every complete body line and excluding apparatus. Keep the stripped attempt and all five successful siblings within one model-family assembly.",
        "replacement_condition": {"kind": "source-confirmed-polytonic-mark-stripping",
            "raw_file_sha256": "92ba3d00f4cba3c891f88e933ae523cfd54d98f9285a7263faf0e556c4da3342",
            "prediction_record_sha256": "3c8546d2a4e4b1e9bbd9c30aa86a454a37220a88d143a7068b8693155eb99bc6",
            "raw_prediction_sha256": "f72f1a8af12e24a51d0c5b80033bef9b8f31a4e85d68653c9e5cc8f98e42f286",
            "finish_reason": "stop", "greek_letters": 525, "breathing_letters": 1,
            "frozen_policy_sha256": "36b6a22f5889bf6e92e2e821f4e9a1e82826192b623e20e92efd6af7638ad0b9"},
        "prompt_suffix": "Transcribe each complete Greek line exactly once. Retain every printed polytonic breathing and accent. Do not strip breathings, normalize orthography, repeat text, or continue beyond this crop.",
    },
    (381, "right-middle-part01"): {
        "parent_supplement": "right-middle", "cuts": [.33096, .38638, .44141],
        "evidence": "The first shorter Qwen3.8 right-middle part on printed page369 still has only1 breathing among235 Greek letters despite multiple source-visible breathings. Its two sibling parts retain marks and stay selected. Two yet shorter crops exactly partition only this first part at a source-checked blank interline gap, preserving all six complete printed lines. Keep both degraded attempts, every successful sibling, and one assembled vote for this model family.",
        "replacement_condition": {"kind": "source-confirmed-polytonic-mark-stripping",
            "raw_file_sha256": "0af4e35f1b5e867dd909f5e937bea9d45e9fe1530b7ed9d7d1f7abc2aaf5558a",
            "prediction_record_sha256": "4fc7c0a49a5573536f6d134e5540ad42bb529cd687a054d1c65800a8f11238e7",
            "raw_prediction_sha256": "d84d5926406b9f5c11960a530f29e64441f6c16f2316e09405130cf8f0e62f11",
            "finish_reason": "stop", "greek_letters": 235, "breathing_letters": 1,
            "frozen_policy_sha256": "36b6a22f5889bf6e92e2e821f4e9a1e82826192b623e20e92efd6af7638ad0b9"},
        "prompt_suffix": "Transcribe each of the three complete Greek lines exactly once. Retain every printed polytonic breathing and accent, especially on initial vowels. Do not strip breathings, normalize orthography, repeat text, or continue beyond this crop.",
    },
    (381, "right-middle"): {
        "cuts": [.33096, .44141, .53246, .60530], "checkpoints": [CHECKPOINT38],
        "evidence": "The completed provider-policy Qwen3.8 right-middle retry on printed page369 strips every breathing from576 Greek letters despite clearly printed breathings, including ἡ and ὑπ’. Its accent rate remains.0972, so the frozen breathing rule identifies this specific loss. Three shorter source-checked crops exactly partition that strip at blank interline gaps, preserving all full Greek lines and marks. Retain the stripped attempt and the other five successful retry strips, with one assembled vote for this checkpoint.",
        "replacement_condition": {"kind": "source-confirmed-polytonic-mark-stripping",
            "raw_file_sha256": "5683e79ee59c21dea26865045cd5096691c85eafd6db164c4a04d50ccc16833d",
            "prediction_record_sha256": "6ce30962a50d35844682cd261df919fd4ab61741ac0dc1fbe19dfa3217e5c2d0",
            "raw_prediction_sha256": "869df708a58c398e1dee66c59ca6365035ae44d770ae29fc898797923a5a6d39",
            "finish_reason": "stop", "greek_letters": 576, "breathing_letters": 0,
            "frozen_policy_sha256": "36b6a22f5889bf6e92e2e821f4e9a1e82826192b623e20e92efd6af7638ad0b9"},
        "prompt_suffix": "Transcribe each complete Greek line exactly once, retaining every printed polytonic breathing and accent. Do not strip breathings, normalize orthography, repeat text, or continue beyond this crop.",
    },
    (13, "upper-preface"): {
        "cuts": [.05, .235, .310, .441], "checkpoints": [CHECKPOINT38],
        "evidence": "The completed Qwen3.8 upper-preface retry systematically strips breathings from the lowercase letter on scan13, although they are visible in the source address and in Ἐπειδὴ, Ἀσσυρίας, and ὑποθέσεις. Its919 Greek letters include0 breathing marks; the frozen detector flags low breathing rate. The three shorter crops exactly partition the original upper-preface region: the first includes the deliberately unaccented capital title; the second begins with the letter address; the.310 boundary lies between complete letter lines. Retain the stripped successful attempt, all other good strips, and the unchanged Qwen3.6 reading.",
        "replacement_condition": {"kind": "source-confirmed-polytonic-mark-stripping",
            "raw_file_sha256": "522747b6c319016ebb49637e6e2b58677337dff54239bb6a586b0a8a05becfcb",
            "prediction_record_sha256": "da0c78540950ba3de05acc37a714b6447ec2e5f94b9b4b4c7007a30c182f981e",
            "raw_prediction_sha256": "9b8677b6a1a08b20b15dcb47b76c031b95ab367690169468456a2d58e8fd6dd1",
            "finish_reason": "stop", "greek_letters": 919, "breathing_letters": 0,
            "frozen_policy_sha256": "36b6a22f5889bf6e92e2e821f4e9a1e82826192b623e20e92efd6af7638ad0b9"},
        "prompt_suffix": "Transcribe each complete Greek line exactly once, retaining every printed polytonic breathing and accent on lowercase letters. Preserve the unaccented capital title as printed. Do not strip breathings, normalize orthography, repeat text, or continue beyond this crop.",
    },
    (50, "left-lower"): {
        "cuts": [.456, .583, .712, .835],
        "evidence": "The lower left body on printed page38 is faint. Its first enlarged retry still repeats text and reaches the output limit. Three shorter strips retain the same complete source lines: the.583 boundary falls after the line ending τὴν, and the.712 boundary follows the line ending ἐκκαίει. The final strip includes the paragraph beginning Δαρεῖος νοσήσας through the left-column foot. The union is exactly the reviewed failed lower-left crop; all other successful retry strips remain unchanged.",
    },
    (87, "right-middle"): {
        "cuts": [.318, .412, .505, .580],
        "evidence": "The first enlarged Qwen3.8 right-middle retry on printed page75 reaches its output limit. Three shorter strips exactly partition that crop. Enlarged source checks put both internal boundaries between complete Greek lines, preserving descenders and following breathing marks. These parts are entirely inside the large authorial body; the other five successful retry strips remain unchanged and the failed base strip remains evidence.",
    },
    (113, "right-first"): {
        "cuts": [.065, .126, .195, .253],
        "evidence": "The completed Qwen3.8 right-first retry on printed page101 contains a stop-terminated loop: a line and its eight-word windows recur241 times. The source crop contains only the short continued lexical notice, with different following lines; it has no corresponding printed repetition. Three shorter crops exactly partition that right-first region. Enlarged source checks place both internal boundaries between complete lines, preserving accents and breathings. Keep the looping attempt and the other seven successful retry strips.",
        "replacement_condition": {"kind": "source-confirmed-repetition-loop",
            "raw_file_sha256": "b8341a14012e4fb47a00665f6540544cd5374b88e0912162abb47889e2186788",
            "prediction_record_sha256": "ce0d67053fec9a4c191e4d996cb1b19aac1887328da6b3f8dd2baeb844e198a0",
            "raw_prediction_sha256": "2a5a42ee32fd8efecba4aad046d7ce984c7688c8dd0d787269c720b1481084ee",
            "finish_reason": "stop", "greek_word_runs": 1243,
            "most_repeated_phrase_occurrences": 241, "most_repeated_line_occurrences": 241,
            "repetition_policy_sha256": "5c6cdf1c4f971f5ed7e650ad7f1699e5e437e039e52ec38bfba2427a3ee00c94"},
    },
    (113, "right-first-part02"): {
        "parent_supplement": "right-first", "cuts": [.126, .16042, .195],
        "evidence": "The Qwen3.8 second part of the right-first supplement on printed page101 still repeats ἡ δὲ ἡδὺς καὶ ἡδύποτος in an unprinted stop-terminated loop. Its eight-word window repeats8 times. The printed crop instead has distinct faint lexical lines. Two shorter crops exactly partition only that second part; the.16042 boundary falls in a source-checked blank interline gap. Preserve the failed original, both looping retry attempts, the two successful sibling supplement parts, and all other successful base strips; assemble one model-family vote.",
        "replacement_condition": {"kind": "source-confirmed-repetition-loop",
            "raw_file_sha256": "1e36e19d1360b9ac0040993520e33e0f93f075e4f20a5f0dccc7f2af5d8066d2",
            "prediction_record_sha256": "3b1dcd5f8a3fe3e60f35069fe9feb816d64dfcc004bcb0581e3775bb88b3f72d",
            "raw_prediction_sha256": "1920868a60de5eeead0af96734f3021d0061995e72d2ad8e954df259301a303c",
            "finish_reason": "stop", "greek_word_runs": 43,
            "most_repeated_phrase_occurrences": 8, "most_repeated_line_occurrences": 3,
            "repetition_policy_sha256": "5c6cdf1c4f971f5ed7e650ad7f1699e5e437e039e52ec38bfba2427a3ee00c94"},
    },
}


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def build_retry(page):
    review = REVIEWS[page]
    original = build() if page <= 279 else build_later_gap()
    source_page = next(p for p in original["pages"] if p["scan_page"] == page)
    strips = review.get("strips")
    if strips is None:
        cut, top, bottom = review["cut"], review["top"], review["bottom"]
        strips = [("left-upper", [.045, top, .495, cut]),
                  ("left-lower", [.045, cut, .495, bottom]),
                  ("right-upper", [.505, top, .97, cut]),
                  ("right-lower", [.505, cut, .97, bottom])]
    return {"schema_version": 1, "work": "photius.bibliotheca", "review_date": "2026-10-18",
            "purpose": "Replace only a failed checkpoint's whole-page attempt with a separately reviewed strip assembly; retain successful checkpoint readings and all failed originals.",
            "retry_of": {"path": "data/ocr_requests/photius-bekker-first-volume.json" if page <= 279 else "data/ocr_requests/photius-bekker-later-gap.json",
                         "sha256": hashlib.sha256(encode(original)).hexdigest(), "page_id": source_page["id"]},
            "checkpoints": review.get("checkpoints", [CHECKPOINT38]), "sources": original["sources"], "prompt": original["prompt"],
            "review": {"checked_scan_pages": [page], "accepted_for_primary_ingest": False,
                       "evidence": review["evidence"], "failure": review["failure"],
                       "admission_policy": "Only the listed checkpoint receives an assembled replacement vote after a completed output-to-scan review. Keep every original and retry prediction; no extra votes or arbitrary choice."},
            "pages": [{"id": source_page["id"] + "-" + name, "source": source_page["source"],
                       "scan_page": page, "printed_page": source_page["printed_page"], "region": region,
                       "max_side": 3600, "role": "reviewed-page-retry", "reading_order": order,
                       "prompt_suffix": "This crop contains one complete part of a single Greek body column. Read every complete line from left to right, then down. Preserve any codex heading; do not repeat words or complete text beyond the crop."}
                      for order, (name, region) in enumerate(strips)]}


def manifest_path(page):
    return Path(f"data/ocr_requests/photius-bekker-page{page:04d}-retry.json")


def variant_path(name):
    return Path(f"data/ocr_requests/photius-bekker-page{name}-retry.json")


def build_variant(name):
    import copy
    review = EXTRA_REVIEWS[name]
    manifest = copy.deepcopy(build_retry(review["page"]))
    manifest["checkpoints"] = review["checkpoints"]
    manifest["review"]["failure"] = review["failure"]
    return manifest


def supplement_path(page, name):
    return Path(f"data/ocr_requests/photius-bekker-page{page:04d}-{name}-supplement.json")


def build_supplement(page, name):
    review = SUPPLEMENT_REVIEWS[(page, name)]
    parent_name = review.get("parent_supplement")
    parent = (build_supplement(page, parent_name) if parent_name else
              build_page13_retry() if page == 13 else build_retry(page))
    target = next(p for p in parent["pages"] if p["id"].endswith("-" + name))
    x0, y0, x1, y1 = target["region"]
    cuts = review["cuts"]
    if cuts[0] != y0 or cuts[-1] != y1 or cuts != sorted(set(cuts)):
        raise ValueError("Supplement must partition the exact reviewed parent strip")
    result = {"schema_version": 1, "work": parent["work"], "review_date": parent["review_date"],
            "purpose": "Replace only a failed retry strip within one model-family assembly; preserve all original and retry attempts and all successful sibling strips.",
            "supplements": {"manifest_path": (supplement_path(page, parent_name) if parent_name else manifest_path(page)).as_posix(),
                            "manifest_sha256": hashlib.sha256(encode(parent)).hexdigest(),
                            "replaces_region": target["id"], "page_id": parent.get("retry_of", parent.get("supplements"))["page_id"]},
            "checkpoints": review.get("checkpoints", parent.get("checkpoints")), "sources": parent["sources"], "prompt": parent["prompt"],
            "review": {"checked_scan_pages": [page], "accepted_for_primary_ingest": False,
                       "evidence": review["evidence"],
                       "admission_policy": "Require exact failed parent-strip evidence and completed output-to-scan review. Assemble these parts once in place of that strip; retain successful siblings and one vote per model family."},
            "pages": [{**target, "id": target["id"] + f"-part{order+1:02d}",
                       "region": [x0, low, x1, high], "reading_order": order,
                       "role": "reviewed-failed-strip-supplement",
                       "prompt_suffix": review.get("prompt_suffix", "This crop contains a short consecutive part of one Greek body column. Transcribe each complete line exactly once from left to right, then down. Do not repeat words, reconstruct missing text, or continue beyond the crop.")}
                      for order, (low, high) in enumerate(zip(cuts, cuts[1:]))]}
    if "replacement_condition" in review:
        result["replacement_condition"] = review["replacement_condition"]
        result["purpose"] = "Replace only an exactly pinned source-confirmed mark-stripped successful retry strip; retain every original and one vote per model family."
        result["review"]["admission_policy"] = "This explicit source-confirmed mark-stripping exception applies only to the pinned checkpoint, parent strip, raw file, and prediction record. All other successful strips remain protected from replacement. Require a completed source mark review of the shorter parts before admission."
        if review["replacement_condition"]["kind"] == "source-confirmed-repetition-loop":
            result["purpose"] = "Replace only an exactly pinned source-confirmed stop-terminated repetition loop; retain every original and one vote per model family."
            result["review"]["admission_policy"] = "This explicit source-confirmed repetition exception applies only to the pinned checkpoint, parent strip, raw file, and prediction record. All other successful strips remain protected from replacement. Require a completed source line-coverage review of the shorter parts before admission."
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=int, action="append", choices=sorted(set(REVIEWS) | {p for p, _ in SUPPLEMENT_REVIEWS}))
    parser.add_argument("--variant", action="append", choices=sorted(EXTRA_REVIEWS))
    args = parser.parse_args()
    for page in args.page or ([] if args.variant else sorted(REVIEWS)):
        if page not in REVIEWS:
            continue
        path = ROOT / manifest_path(page)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode(build_retry(page)))
        print(f"Pinned scan {page}: {len(build_retry(page)['pages'])} strips, listed checkpoint only")
    for page, name in sorted(SUPPLEMENT_REVIEWS):
        if args.variant or args.page and page not in args.page:
            continue
        path = ROOT / supplement_path(page, name)
        path.write_bytes(encode(build_supplement(page, name)))
        print(f"Pinned scan {page}: shorter {name} supplement")
    for name in args.variant or ([] if args.page else sorted(EXTRA_REVIEWS)):
        path = ROOT / variant_path(name)
        path.write_bytes(encode(build_variant(name)))
        print(f"Pinned checkpoint-specific variant {name}")
