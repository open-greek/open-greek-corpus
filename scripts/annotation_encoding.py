#!/usr/bin/env python3
"""Shared encoding normalization for cog's annotation exporters.

cog owns ENCODING normalization (per docs/annotation-export-contract.md): every
scripts/export_*.py applies the SAME canonical form/lemma normalization so
downstream consumers get one consistent encoding. Keeping the one implementation
here, imported by every exporter, stops the per-exporter copies from drifting:
an early copy carried a sigma bug (a whole-string look-ahead that medialized a
word-final sigma inside a multi-word lemma string, e.g. "Ζεύς, Δίς" -> "Ζεύσ, Δίς").

Normalization applied to a Greek surface/lemma form:
  - NFC
  - apostrophe / elision marks unified to U+2019
  - lunate sigma -> standard sigma, with final/medial position enforced PER WORD

Lemma CONVENTIONS (homograph digits, Koine headword choices, ...) are preserved
verbatim: this module normalizes ENCODING only, never conventions.
"""

from __future__ import annotations

import unicodedata

# Apostrophe / elision marks unified to U+2019. Conservative: only true
# apostrophe marks, applied to Greek form/lemma strings, never to incidental text.
_APOSTROPHES = {
    "ʼ",  # MODIFIER LETTER APOSTROPHE (a common elision mark, e.g. par')
    "'",       # APOSTROPHE
    "‘",  # LEFT SINGLE QUOTATION MARK
    "’",  # RIGHT SINGLE QUOTATION MARK (target)
}
_APOS_TABLE = {ord(c): "’" for c in _APOSTROPHES}


def normalize_sigma(s: str) -> str:
    """Lunate sigma -> standard sigma, then enforce final/medial position PER WORD.

    A sigma is final (ς) when it ends a word (nothing, or a non-letter, follows it
    directly) and medial (σ) when a letter follows directly. The look-ahead is
    LOCAL (the next character only), so multi-word / multi-form strings such as
    "Ζεύς, Δίς" or "δέκα καὶ ὀκτὼ" keep each word's word-final sigma; a whole-string
    "any following letter" test wrongly medializes the final ς of an earlier word.
    """
    if not any(c in s for c in ("ϲ", "Ϲ", "σ", "ς")):
        return s
    s = s.replace("ϲ", "σ").replace("Ϲ", "Σ")
    if "σ" not in s and "ς" not in s:
        return s
    chars = list(s)
    n = len(chars)
    for i, ch in enumerate(chars):
        if ch in ("σ", "ς"):
            following_letter = (i + 1 < n) and chars[i + 1].isalpha()
            chars[i] = "σ" if following_letter else "ς"
    return "".join(chars)


def normalize(text):
    """Full cog encoding normalization for a Greek surface/lemma/variant form."""
    if text is None:
        return None
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_APOS_TABLE)
    text = normalize_sigma(text)
    return unicodedata.normalize("NFC", text)


# Some exporters imported this under the name norm_form.
norm_form = normalize


def nfc(text):
    """NFC only, for incidental text fields (translit, gloss, notes)."""
    if text is None:
        return None
    return unicodedata.normalize("NFC", text)
