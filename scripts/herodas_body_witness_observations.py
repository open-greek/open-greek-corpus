"""Scan-reviewed roles in existing Qwen3.6 predictions of missing Herodas pages.

Offsets address each exact raw Greek-only prediction, including every newline.
The projection identifies printed body versus labels, numbers, and apparatus;
it makes no spelling corrections and does not certify extant or certain words.
The complete failed page 444 prediction is retained but contributes no vote.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path


REVIEWED_AT = "2026-10-22T17:32:08Z"
SOURCE = {
    "id": "headlam-knox-1922",
    "path": "data/corpus_changes/editorial-role-review/source-herodas.pdf",
    "sha256": "6568f0c8efb9f8efce1ea9917da2b30dbe16cf8a1147ea2503a6dd0280a8fa1a",
    "url": "https://archive.org/details/mimesfragments00hero",
    "year": 1922,
}
MISSING_PAGES = (76, 78, 134, 136, 138, 184, 186, 240, 242, 296, 348, 350,
                 388, 390, 392, 394, 396, 440, 442, 444, 480, 486)
RAW_SHA256 = {
    76: "d9d2e9a496e8eea8bc96cfe3876ca4fb137ff7eeff6ccaef623a78697be6f73f",
    78: "10a314a02e0013e2742c8b61806212974a07b66ae0f633ac8e22f0d0f098232e",
    134: "f10fcdf171f0132047f84fd8d49d4dfdf3ebaf1fbfff08eaa3d4252045f34dbd",
    136: "700a9f36bd7add1729bdfa44a3c72219bb77d4f7e8cb0fc6c9dcb35121318401",
    138: "323deb8501422c5c5bb33dfdf19c9727a0faa20348845dc3fd286e40b8173370",
    184: "eb4104087bf89f14e770dc45759056f1e0fd492aa16f2614c48e6187231a4e8b",
    186: "3ea12d3cda96ee54b64f16f354f23425bd83fa1ef9af4735f083a237b95a9e53",
    240: "546a05f318b8f78e22cd5f4f4fd1276f7a4999f713e4137bcac27cefdf4633cb",
    242: "7414eaa229b8bfd69ffdddab3e40e94af749d1ac458c2119ddbcc656b29ed4f1",
    296: "fb258d06eaba7f3d60fa6b4c38b07365f4e66b5614376044b451f127188746ef",
    348: "73de21cf634522eac07aaa4700ed3248e978bc9d03f1ca26091ffe9c39cad36a",
    350: "bcd156b81596eddf670b9e79c431bbe5b37c339770cb6c43bb747d36c540be85",
    388: "50cbd922170809d601061167f641ef4a324e4cd4b5d8bdd8ac11beec3d63c7ef",
    390: "63e07a20bc5d8db33b5790deb8e869661c6438aafd301f31e5016b04edb86399",
    392: "fc7608eeb3b3f91b1c1c6ff4a0951b517d401582a85f7a49273d79bd3361ba83",
    394: "97a5b19c1ee478b09a90f0fa87f012b7d18d8f890055dda9a2e03497cf3b0624",
    396: "343e9e0c3e04f9b0d7516f9fb112bf668a690053a36459145d281118ce668b56",
    440: "882a7a47252622d3949bfd34c6a09c4a19a1a95c34a8b4f2f982d06ec7a1b056",
    442: "fe5f92936ab2c389247aa817657c0f7a30e65a761d2a1607a9a2fa9b8d69a0db",
    444: "b5abfdf22f21cf2f62b1d2373d9d9bbde797645f30875950ffc371c26a7bcc86",
    480: "44b2eac5f939eb09688ea5a463c81d1d91a912b272491e2bd0a5b550d3328238",
    486: "1530d05c4e6cb6352e6afb79ad9f5f29929164d27229a7a5462fccb1615ba130",
}
# Zero-based raw-line indices, fixed only after visual inspection of the scan.
# A misrecognized speaker name remains the literal raw reading of a label.
SPEAKER_LINES = {
    76: [4, 6, 26], 78: [8, 12, 15], 134: [22, 26],
    184: [11, 15, 19, 22, 24, 26, 29],
    186: [0, 3, 6, 9, 11, 13, 18, 20, 23, 25],
    240: [0, 4, 21, 29], 242: [5, 14],
    348: [0, 3, 13, 31, 33], 350: [0, 2, 8, 11, 14, 19, 22, 27],
    388: [1], 392: [14, 18, 29], 394: [0, 5, 14, 17, 25],
}
HEADER_LINES = {296: [0], 442: [0]}
TITLE_LINES = {480: [0]}
LINE_NUMBER_PREFIXES = {
    136: {0: "60 ", 5: "65 ", 10: "70 ", 15: "75 ", 20: "80 ", 25: "85 ", 30: "90 "},
    184: {0: "60 ", 5: "65 ", 10: "70 ", 17: "75 ", 28: "80 "},
    186: {8: "85 ", 17: "90 ", 27: "95 "},
    240: {1: "55 ", 9: "60 ", 14: "65 ", 19: "70 ", 22: "75 ", 30: "80 "},
    242: {line: ("85 " if line < 10 else "90 " if line < 14 else "95 ")
          for line in [0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17]},
    392: {0: "50 ", 5: "55 ", 10: "60 ", 16: "65 ", 22: "70 ", 27: "75 "},
    396: {3: "110 ", 8: "115 ", 13: "120 ", 18: "125 "},
}
# Everything beginning at these literal raw lines is below the printed body.
APPARATUS_START = {184: 31, 240: 32, 388: 3, 396: 23, 442: 31}
PRINTED_SCOPE = {
    76: "I.45–74", 78: "I.75–90", 134: "II.24–59", 136: "II.60–94", 138: "II.95–102",
    184: "III.60–81a", 186: "III.81b–97", 240: "IV.54–80", 242: "IV.81–95", 296: "V.73b–85",
    348: "VI.47b–78", 350: "VI.79–102", 388: "VII.1–22", 390: "VII.23–49",
    392: "VII.50–78", 394: "VII.79–105", 396: "VII.106–129", 440: "VIII.1–23",
    442: "VIII.24–54, including printed gaps and fragments", 444: "VIII.55–79, failed comparison prediction; verses 55–57 are dotted losses",
    480: "X.1–4 only", 486: "XI.1 only; XIa held separately",
}
REASONS = {
    "speaker-label": "Separately typeset speaker name in the pinned printed dialogue, not spoken verse; retain its literal OCR spelling only outside the body projection.",
    "running-header": "Running work/mime header above the Greek text, not authorial verse.",
    "title": "Separately typeset mime title; the four Greek verses below it are the admitted comparison scope.",
    "line-number": "Marginal verse number emitted inside the OCR line; even a repeated or misrecognized numeral is source numbering, not Greek body text.",
    "apparatus": "Small-type textual notes below the Greek body, containing sigla, variant quotations, and named conjectures; the whole literal tail remains archived.",
    "unadmitted-XIa": "Two separately printed XIa verses are attributed only through an anonymous speech in Strabo; their uncertain Herodas association is outside this XI-only admission.",
    "failed-recognition": "The Qwen3.6 prediction truncates nearly every printed verse at its right edge, often within a word. The existing loop-recovery text is byte-identical and its manifest records truncated=true; it is not independent corroboration. Retain the entire failed prediction without a counted body vote.",
}
QUALIFICATION = (
    "Roles only: literal OCR spellings, accents, punctuation, fragments, and bracketed readings remain unchanged. "
    "A body span is eligible for comparison with a new independent recognition and the printed scan; it is not "
    "a claim of certain transmission or automatic lexical eligibility. No missing letters or verses are supplied."
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_source_pdf(path):
    if sha(Path(path).read_bytes()) != SOURCE["sha256"]:
        raise ValueError("Herodas witness observation source scan changed")


def project_qwen36(page: int, text: str) -> dict:
    """Partition every raw code point, retaining source-confirmed body spans.

    The returned ``spans`` cover the complete raw input in order. The separate
    ``authorial_spans`` and ``excluded_spans`` are subsets of that same partition.
    Source-role decisions never normalize or correct any span's text.
    """
    if type(page) is not int or page not in RAW_SHA256:
        raise ValueError("No reviewed Qwen3.6 source-role observations for this page")
    if not isinstance(text, str) or sha(text.encode("utf-8")) != RAW_SHA256[page]:
        raise ValueError("Herodas Qwen3.6 raw prediction checksum changed")
    lines = text.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    excluded = []

    def exclude(start, end, role):
        if not 0 <= start < end <= len(text):
            raise ValueError("Reviewed Qwen3.6 exclusion is outside its raw prediction")
        excluded.append({"start": start, "end": end, "role": role,
                         "reason": REASONS[role]})

    if page == 444:
        exclude(0, len(text), "failed-recognition")
    else:
        for mapping, role in ((SPEAKER_LINES, "speaker-label"), (HEADER_LINES, "running-header"),
                              (TITLE_LINES, "title")):
            for line in mapping.get(page, []):
                exclude(starts[line], starts[line + 1], role)
        for line, prefix in LINE_NUMBER_PREFIXES.get(page, {}).items():
            if not lines[line].startswith(prefix):
                raise ValueError("Reviewed marginal-number preimage changed")
            exclude(starts[line], starts[line] + len(prefix), "line-number")
        if page in APPARATUS_START:
            exclude(starts[APPARATUS_START[page]], len(text), "apparatus")
        if page == 486:
            exclude(starts[1], starts[3], "unadmitted-XIa")
            exclude(starts[3], len(text), "apparatus")
    spans, cursor = [], 0

    def append(start, end, role, reason=None):
        span = {"start": start, "end": end, "text": text[start:end], "role": role,
                "eligible_for_comparison": role == "authorial",
                "evidence": f"Visual inspection of Headlam–Knox 1922, PDF page {page}, printed page {page - 70}; {PRINTED_SCOPE[page]}"}
        if reason is not None:
            span["reason"] = reason
        spans.append(span)

    for exclusion in sorted(excluded, key=lambda item: item["start"]):
        if exclusion["start"] < cursor:
            raise ValueError("Reviewed source-role exclusions overlap")
        if exclusion["start"] > cursor:
            append(cursor, exclusion["start"], "authorial")
        append(exclusion["start"], exclusion["end"], exclusion["role"], exclusion["reason"])
        cursor = exclusion["end"]
    if cursor < len(text):
        append(cursor, len(text), "authorial")
    if "".join(span["text"] for span in spans) != text:
        raise ValueError("Herodas witness projection lost literal source characters")
    return {"page": page, "raw_sha256": RAW_SHA256[page], "reviewed_at": REVIEWED_AT,
            "source": deepcopy(SOURCE), "printed_scope": PRINTED_SCOPE[page], "spans": spans,
            "authorial_spans": [deepcopy(span) for span in spans if span["role"] == "authorial"],
            "excluded_spans": [deepcopy(span) for span in spans if span["role"] != "authorial"],
            "eligible_for_comparison": page != 444, "qualification": QUALIFICATION}


def build_observations(packet: dict, *, source_pdf=None) -> dict:
    """Compile all 22 page observations from the checked historical archive."""
    from herodas_body_witnesses import validate_packet
    validate_packet(packet)
    if source_pdf is not None:
        verify_source_pdf(source_pdf)
    if not set(MISSING_PAGES) <= set(packet["selected_pages"]):
        raise ValueError("Historical archive lacks a reviewed missing body page")
    return {"schema_version": 1, "generator": "scripts/herodas_body_witness_observations.py",
            "reviewed_at": REVIEWED_AT, "source": deepcopy(SOURCE),
            "pages": [project_qwen36(page, packet["pages"][str(page)]["qwen36"]["files"]["grc"]["text"])
                      for page in MISSING_PAGES],
            "qualification": QUALIFICATION}
