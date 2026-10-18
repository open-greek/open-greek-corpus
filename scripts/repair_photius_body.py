"""The separately reviewed, bounded missing-body repair for legacy Photius255.6.

This is a source correction, not an apparatus classification. The historical
prefix remains exact; the unprinted loop abstains while two independently
reviewed tail readings retain every disagreement in the ordinary vote network.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from ocr_consensus import merge_witnesses, compact_corpus_consensus

REVIEW = Path("data/ingest_reviews/photius-bekker-body-corrections.json")
LOCUS = "helladius_chrestomathia_photius_bekker_v2_0255.6"
ROW_SHA = "a6b2d707fe79fd4c7c5ffcb1657c735ef82e57df956d75fa6bfebc8635c4f823"
LIBRARY = Path("data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz")
LIBRARY_SHA = "114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291"
LIBRARY_URL = "https://gitlab.lisn.upsaclay.fr/api/v4/projects/1918/packages/generic/corpus/1/works/tlg4040/tlg001/local002.json.gz"
SCHEMA = "source-reviewed-photius-body-correction-v1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def correct(raw, historical, decisions, library_raw, archive):
    from repair_photius_apparatus import SOURCE_SHA, SOURCE_URL, row_sha, encode

    authority = json.loads(raw)
    old = historical[LOCUS]
    scope = authority.get("replacement_scope", {})
    source = authority.get("source", {})
    window = authority.get("source_library_window", {})
    following = authority.get("following_body_anchor", {})
    if (authority.get("schema_version") != 1 or authority.get("work") != "photius.bibliotheca"
            or authority.get("kind") != "source-reviewed-missing-body-candidate"
            or authority.get("locus") != LOCUS or row_sha(old) != ROW_SHA
            or authority.get("original_row") != old or authority.get("row_sha256") != ROW_SHA
            or scope.get("start") != 162 or scope.get("end") != len(old["text"])
            or scope.get("original_text") != old["text"][162:] or not scope.get("policy")
            or decisions[LOCUS][1]["exclusions"] or not authority.get("reviewed_at")
            or not authority.get("source_evidence") or not authority.get("transcription_convention")):
        raise ValueError("Body correction differs from the exact reviewed255.6 historical span")
    if (source != {"url": SOURCE_URL, "sha256": SOURCE_SHA, "scan_page": 255,
                   "printed_page": 520, "region": [.58, .522, .955, .729]}
            or following.get("locus") != "helladius_chrestomathia_photius_bekker_v2_0256.1"
            or row_sha(historical[following["locus"]]) != following.get("row_sha256")
            or not following.get("text_prefix") or not following.get("evidence")
            or not historical[following["locus"]]["text"].startswith(following.get("text_prefix", ""))):
        raise ValueError("Body correction source region or following body boundary changed")
    image = authority.get("source_image", {})
    if (image.get("crop_sha256") != "ed8844d5e319ef12d391f85570d5eefcdcf5fb0739f9bdb80ba15a087ff38cd9"
            or image.get("render_sha256") != "3b45cbd1b2543c4de67e532c252b36c7d071acca2ad943e3ced9dd272949d191"
            or image.get("pixel_bbox") != [2242, 2610, 3692, 3645]):
        raise ValueError("Body correction lacks its exact independently reviewed source image")
    if (sha(library_raw) != LIBRARY_SHA or window.get("path") != LIBRARY.as_posix()
            or window.get("sha256") != LIBRARY_SHA or window.get("section") != "tlg4040-tlg001-local002-s532"
            or window.get("start") != 3640 or window.get("end") != 4189
            or not window.get("page_label_qualification")):
        raise ValueError("Body correction digital source or bounded window changed")
    document = json.loads(gzip.decompress(library_raw))
    section = next(section for section in document["sections"] if section["id"] == window["section"])
    digital_text = "\n".join(block["text"] for block in section["blocks"])
    if digital_text[3640:4189] != window.get("original_text"):
        raise ValueError("Body correction digital reading differs from the pinned source codepoints")
    witnesses = authority.get("witnesses", [])
    if (len(witnesses) != 2 or {w.get("id") for w in witnesses} != {"manual-scan-review", "source-library-local002"}
            or any(w.get("vote_group") != w.get("id") for w in witnesses)):
        raise ValueError("Body correction requires both independent reviewed tail readings")
    by_id = {w["id"]: w for w in witnesses}
    manual, digital = by_id["manual-scan-review"], by_id["source-library-local002"]
    if (not manual.get("text") or not manual.get("evidence")
            or manual.get("artifact_sha256") != sha(manual["text"].encode())
            or manual["artifact_sha256"] != "45f0148593ccc63f0cd2593c2ea5c0e137f86101351b0387a6f626917f74d755"
            or digital.get("text") != window["original_text"] or digital.get("license") != "CC-BY-SA-4.0"
            or digital.get("artifact_sha256") != "4391780ff335f3f6faa7fa7ca4decd0a3e79b9e6da4f9542a980c948709028c9"
            or digital.get("source_url") != LIBRARY_URL or digital.get("source_file_sha256") != LIBRARY_SHA
            or digital.get("source_section") != window["section"]
            or any("voting_segments" in witness or "abstention_audit" in witness for witness in witnesses)):
        raise ValueError("Body correction witness identity, text, or component license changed")
    credit = authority.get("source_library_credit", {})
    if (credit.get("url") != LIBRARY_URL or credit.get("sha256") != LIBRARY_SHA
            or credit.get("license", {}).get("url") != "https://creativecommons.org/licenses/by-sa/4.0/"
            or not credit.get("rights") or credit.get("separate_api_notice", {}).get("tdm_reservation") != 1
            or credit["separate_api_notice"].get("tdm_policy") != "https://sourcelibrary.org/licensing"
            or credit["separate_api_notice"].get("attribution") != "Source Library (https://sourcelibrary.org)"):
        raise ValueError("Body correction must retain the component attribution and separate API reservation")
    pin = {"path": (archive / "body-review.json").as_posix(), "sha256": sha(raw)}
    prefix = old["text"][:162]
    historical_witness = {"id": "historical-prefix", "vote_group": "historical-prefix", "text": old["text"],
        "artifact_sha256": ROW_SHA, "voting_segments": [{"start": 0, "end": 162, "text": prefix}],
        "abstention_audit": {"reviewed_text_sha256": sha(old["text"].encode()), "source_review": pin,
            "excluded_spans": [{"start": 162, "end": len(old["text"]), "text": old["text"][162:],
                "reason": "Source-confirmed unprinted repetition replaces missing body; no omission vote."}]}}
    first = merge_witnesses([historical_witness])
    tail = merge_witnesses(witnesses)
    if tail["ocr_consensus"]["counts"] != {"agreement": 76, "unresolved": 12}:
        raise ValueError("The reviewed bounded source disagreements no longer reproduce")
    # Disjoint physical text ranges are aligned independently. There is no
    # synthetic third vote on the missing tail and no global positional guess.
    slots = copy.deepcopy(first["ocr_consensus"]["slots"] + tail["ocr_consensus"]["slots"])
    for position, slot in enumerate(slots):
        slot["position"] = position
        outside = ([w["id"] for w in witnesses] if position < len(first["ocr_consensus"]["slots"])
                   else [fragment["id"] for fragment in first["ocr_consensus"].get("voting_fragments", [])])
        slot["abstentions"] = sorted(set(slot["abstentions"]) | set(outside))
    network = {"schema_version": 1,
        "policy": "Exact retained historical prefix followed by the independent bounded tail consensus. Disjoint source ranges align separately; the held historical loop abstains. Every tail tie remains visible and lexically ineligible.",
        "witnesses": first["ocr_consensus"]["witnesses"] + tail["ocr_consensus"]["witnesses"],
        "voting_fragments": first["ocr_consensus"].get("voting_fragments", []),
        "slots": slots, "counts": dict(Counter(slot["status"] for slot in slots)),
        "span_networks": {"historical_prefix": first, "replacement_tail": tail}}
    full = {"text": prefix + tail["text"],
            "analysis_text": " ".join(slot["selected"] for slot in slots if slot["lexical_eligible"]),
            "ocr_consensus": network}
    network_path = archive / "body-word-networks.json.gz"
    compact = compact_corpus_consensus(full, {"path": network_path.as_posix(), "key": LOCUS})
    correction = {"schema": SCHEMA, "source_review": pin, "original_text": old["text"],
        "retained_prefix": prefix, "replacement_text": tail["text"], "replaced_span": scope,
        "source": source, "transcription_convention": authority["transcription_convention"],
        "license": "CC-BY-SA-4.0"}
    updated = {**old, **compact, "edition": "bekker1824-independent-ocr-consensus", "source": "reviewed-text-consensus",
               "language": "grc", "physical_refs": source, "license": "CC-BY-SA-4.0", "source_body_correction": correction,
               "component_attribution": [{"id": "reviewed-bekker-scan", "source": source, "license": "PD"},
                                         {"id": "source-library-local002", **credit}]}
    change = {"locus": LOCUS, "original_text": old["text"], "corrected_text": updated["text"],
        "original_row": old, "corrected_row": updated, "original_row_sha256": ROW_SHA,
        "corrected_row_sha256": row_sha(updated), "replacement_scope": scope, "source_review": pin,
        "source": source, "source_image": image, "reviewed_at": authority["reviewed_at"],
        "evidence": authority["source_evidence"], "following_body_anchor": following,
        "held_original_reading": historical_witness, "transcription_convention": authority["transcription_convention"]}
    return updated, {"source_review": pin, "license": "CC-BY-SA-4.0", "source_library": credit,
        "network": {"path": network_path.as_posix(), "sha256": sha(gzip.compress(encode({LOCUS: full}), mtime=0))},
        "counts": {"corrected_rows": 1, "retained_prefix_characters": 162, "held_loop_characters": 32,
                   "replacement_agreement_slots": tail["ocr_consensus"]["counts"].get("agreement", 0),
                   "replacement_unresolved_slots": tail["ocr_consensus"]["counts"].get("unresolved", 0)},
        "changes": [change]}, {network_path: gzip.compress(encode({LOCUS: full}), mtime=0)}


def validate_projection(row):
    layer = row["source_body_correction"]
    slots = row["ocr_consensus"]["slots"]
    if (layer.get("schema") != SCHEMA or row.get("locus") != LOCUS
            or layer.get("retained_prefix") != layer.get("original_text", "")[:162]
            or row.get("text") != layer["retained_prefix"] + layer["replacement_text"]
            or row.get("analysis_text") != " ".join(slot["selected"] for slot in slots if slot["lexical_eligible"])):
        raise ValueError("Body correction lexical projection differs from its retained prefix and checked slots")
