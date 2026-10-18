"""Bound an unsegmented comparison OCR page by independent body witnesses.

This does not prefer or correct any reading. A third source may contain small
apparatus after its page body; outside another witness's observed span, ROVER
correctly abstains rather than inventing omission votes. Consequently the raw
third source must first have its body window established independently.
"""
from __future__ import annotations

import unicodedata


def _spans(text):
    """Whole letter runs with source offsets, including mixed-script damage."""
    from ocr_consensus import greek_letter
    result, start = [], None
    for index, char in enumerate(text + " "):
        if unicodedata.category(char).startswith(("L", "M")) or char in "'’ʼ᾽":
            if start is None:
                start = index
        elif start is not None:
            word = text[start:index]
            if any(greek_letter(char) for char in word):
                result.append((word, start, index))
            start = None
    return result


def _locations(words, anchor):
    return [index for index in range(len(words) - len(anchor) + 1)
            if words[index:index + len(anchor)] == anchor]


def bound_comparison_witness(fresh_witnesses, comparison_witness, minimum_words=4):
    """Return a bounded source witness and an audit, or hold the whole source.

    Fresh inputs must be body transcriptions from at least two independent vote
    groups. Both boundaries require an identical accent-insensitive phrase of
    at least four pure Greek words that occurs once in every supplied witness.
    Boundary words retain their exact comparison-source readings. No unmatched
    prefix/footer may vote through abstention; all originals remain in audit.
    """
    from ocr_consensus import alignment_key, lexical_eligible
    if minimum_words < 4:
        raise ValueError("Body comparison anchors require at least four words")
    original = comparison_witness["text"]
    normalized = unicodedata.normalize("NFC", original)
    decision = {"generator": "scripts/bound_comparison_witness.py",
        "witness": comparison_witness["id"], "original_text": original,
        "normalization": "NFC for positional matching; no spelling corrections",
        "evidence": "Unique shared Greek body boundaries observed independently in the fresh witnesses; text outside that window is retained for comparison without voting."}
    def hold(reason):
        return None, {**decision, "status": "held-comparison-only", "reason": reason,
                      "corrected_text": None}
    if len({value.get("vote_group", value["id"]) for value in fresh_witnesses}) < 2:
        return hold("Two independent fresh vote groups are required.")
    fresh_spans = [_spans(unicodedata.normalize("NFC", value["text"])) for value in fresh_witnesses]
    source_spans = _spans(normalized)
    if any(len(words) < minimum_words for words in fresh_spans) or len(source_spans) < minimum_words:
        return hold("A body witness is shorter than the required unique anchor.")
    fresh_keys = [[alignment_key(word) for word, start, end in words] for words in fresh_spans]
    source_keys = [alignment_key(word) for word, start, end in source_spans]
    def boundary(at_end):
        for length in range(minimum_words, min(16, *(len(words) for words in fresh_spans)) + 1):
            selected = [words[-length:] if at_end else words[:length] for words in fresh_spans]
            if any(not all(lexical_eligible(word) for word, start, end in words) for words in selected):
                continue
            anchors = [[alignment_key(word) for word, start, end in words] for words in selected]
            anchor = anchors[0]
            if any(other != anchor for other in anchors[1:]):
                continue
            if sum(len(word) for word in anchor) < 16:
                continue
            locations = [_locations(words, anchor) for words in fresh_keys + [source_keys]]
            if not all(len(found) == 1 for found in locations):
                continue
            position = locations[-1][0]
            return position, length, anchor
        return None
    start_anchor, end_anchor = boundary(False), boundary(True)
    if start_anchor is None or end_anchor is None:
        return hold("A unique shared beginning or ending body anchor is missing.")
    first, start_length, first_words = start_anchor
    last, end_length, last_words = end_anchor
    start = source_spans[first][1]
    end = source_spans[last + end_length - 1][2]
    if start >= end or first > last:
        return hold("The source body anchors occur in a different order.")
    while start and normalized[start - 1] in "([«“‘":
        start -= 1
    while end < len(normalized) and normalized[end] in ")]»”’.,;··:!?…-‐":
        end += 1
    text = normalized[start:end]
    bounded = {**comparison_witness, "text": text, "original_text": original,
               "comparison_body_window": {"start": start, "end": end, "normalization": "NFC"}}
    return bounded, {**decision, "status": "bounded-body-voting-witness", "corrected_text": text,
        "start_offset": start, "end_offset": end, "normalized_text": normalized,
        "removed_prefix": normalized[:start], "removed_footer": normalized[end:],
        "start_anchor": {"words": first_words, "length": start_length},
        "end_anchor": {"words": last_words, "length": end_length},
        "fresh_witnesses": [value["id"] for value in fresh_witnesses]}
