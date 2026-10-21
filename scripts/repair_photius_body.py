"""Two separately reviewed, bounded missing-body repairs in legacy Photius.

This is a source correction, not an apparatus classification. The historical
prefix remains exact; the unprinted loop abstains while two independently
reviewed tail readings retain every disagreement in the ordinary vote network.
"""
from __future__ import annotations

from audit_compression import compress_gzip

import copy
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

from ocr_consensus import merge_witnesses, compact_corpus_consensus

REVIEW = Path("data/ingest_reviews/photius-bekker-body-corrections.json")
REVIEW7 = Path("data/ingest_reviews/photius-bekker-body-page0007.json")
LOCUS = "helladius_chrestomathia_photius_bekker_v2_0255.6"
LOCUS7 = "helladius_chrestomathia_photius_bekker_v2_0007.5"
ROW_SHA = "a6b2d707fe79fd4c7c5ffcb1657c735ef82e57df956d75fa6bfebc8635c4f823"
LIBRARY = Path("data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz")
LIBRARY_SHA = "114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291"
LIBRARY_URL = "https://gitlab.lisn.upsaclay.fr/api/v4/projects/1918/packages/generic/corpus/1/works/tlg4040/tlg001/local002.json.gz"
SCHEMA = "source-reviewed-photius-body-correction-v1"
CASES = {
    LOCUS: {"row_sha256": ROW_SHA, "start": 162, "end": 194, "page": 255,
        "region": [.58, .522, .955, .729], "section": "tlg4040-tlg001-local002-s532", "window": [3640, 4189],
        "following": "helladius_chrestomathia_photius_bekker_v2_0256.1",
        "manual_sha256": "45f0148593ccc63f0cd2593c2ea5c0e137f86101351b0387a6f626917f74d755",
        "digital_artifact_sha256": "4391780ff335f3f6faa7fa7ca4decd0a3e79b9e6da4f9542a980c948709028c9",
        "source_image": {"crop_sha256": "ed8844d5e319ef12d391f85570d5eefcdcf5fb0739f9bdb80ba15a087ff38cd9",
            "render_sha256": "3b45cbd1b2543c4de67e532c252b36c7d071acca2ad943e3ced9dd272949d191",
            "pixel_bbox": [2242, 2610, 3692, 3645]},
        "counts": {"agreement": 76, "unresolved": 12}, "review_file": "body-review.json",
        "network_file": "body-word-networks.json.gz"},
    LOCUS7: {"row_sha256": "3622531a16e3d29ec02027c52611d2b0399ff20a159400c4787aaa7f4202dbf5",
        "start": 981, "end": 1030, "page": 7, "region": [.54, .37, .94, .735],
        "section": "tlg4040-tlg001-local002-s284", "window": [3098, 4223],
        "following": "helladius_chrestomathia_photius_bekker_v2_0008.1",
        "manual_sha256": "0268e0e4b40936a81e573f81ad13aa3ddd6dc0387473e881d01d970e279e0cfe",
        "digital_artifact_sha256": "ac3470b2d8a192fecd9fc04693dda62791ca56f52cc4118472b0ce309c938aac",
        "source_image": {"crop_sha256": "518f2a039b7b4e4242aee7f003df56b2da386bb0b3eda8dbbc199d4e3328b79d"},
        "counts": {"agreement": 177, "unresolved": 7}, "review_file": "body-page0007-review.json",
        "network_file": "body-page0007-word-networks.json.gz"},
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def correct(raw, historical, decisions, library_raw, archive):
    from repair_photius_apparatus import SOURCE_SHA, SOURCE_URL, row_sha, encode

    authority = json.loads(raw)
    locus = authority.get("locus")
    if locus not in CASES:
        raise ValueError("Only the two explicitly reviewed historical body corrections are authorized")
    case = CASES[locus]
    start, end = case["start"], case["end"]
    old = historical[locus]
    scope = authority.get("replacement_scope", {})
    source = authority.get("source", {})
    window = authority.get("source_library_window", {})
    following = authority.get("following_body_anchor", {})
    if (authority.get("schema_version") != 1 or authority.get("work") != "photius.bibliotheca"
            or authority.get("kind") != "source-reviewed-missing-body-candidate"
            or row_sha(old) != case["row_sha256"]
            or authority.get("original_row") != old or authority.get("row_sha256") != case["row_sha256"]
            or scope.get("start") != start or scope.get("end") != end or end != len(old["text"])
            or scope.get("original_text") != old["text"][start:] or not scope.get("policy")
            or decisions[locus][1]["exclusions"] or not authority.get("reviewed_at")
            or not authority.get("source_evidence") or not authority.get("transcription_convention")):
        raise ValueError("Body correction differs from its exact reviewed historical span")
    if (source != {"url": SOURCE_URL, "sha256": SOURCE_SHA, "scan_page": case["page"],
                   "printed_page": case["page"] + 265, "region": case["region"]}
            or following.get("locus") != case["following"]
            or row_sha(historical[following["locus"]]) != following.get("row_sha256")
            or not following.get("text_prefix") or not following.get("evidence")
            or not historical[following["locus"]]["text"].startswith(following.get("text_prefix", ""))):
        raise ValueError("Body correction source region or following body boundary changed")
    image = authority.get("source_image", {})
    if any(image.get(key) != value for key, value in case["source_image"].items()):
        raise ValueError("Body correction lacks its exact independently reviewed source image")
    if (sha(library_raw) != LIBRARY_SHA or window.get("path") != LIBRARY.as_posix()
            or window.get("sha256") != LIBRARY_SHA or window.get("section") != case["section"]
            or [window.get("start"), window.get("end")] != case["window"]
            or not window.get("page_label_qualification")):
        raise ValueError("Body correction digital source or bounded window changed")
    document = json.loads(gzip.decompress(library_raw))
    section = next(section for section in document["sections"] if section["id"] == window["section"])
    digital_text = "\n".join(block["text"] for block in section["blocks"])
    if digital_text[window["start"]:window["end"]] != window.get("original_text"):
        raise ValueError("Body correction digital reading differs from the pinned source codepoints")
    witnesses = authority.get("witnesses", [])
    if (len(witnesses) != 2 or {w.get("id") for w in witnesses} != {"manual-scan-review", "source-library-local002"}
            or any(w.get("vote_group") != w.get("id") for w in witnesses)):
        raise ValueError("Body correction requires both independent reviewed tail readings")
    by_id = {w["id"]: w for w in witnesses}
    manual, digital = by_id["manual-scan-review"], by_id["source-library-local002"]
    if (not manual.get("text") or not manual.get("evidence")
            or manual.get("artifact_sha256") != sha(manual["text"].encode())
            or manual["artifact_sha256"] != case["manual_sha256"]
            or digital.get("text") != window["original_text"] or digital.get("license") != "CC-BY-SA-4.0"
            or digital.get("artifact_sha256") != case["digital_artifact_sha256"]
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
    pin = {"path": (archive / case["review_file"]).as_posix(), "sha256": sha(raw)}
    prefix = old["text"][:start]
    historical_witness = {"id": "historical-prefix", "vote_group": "historical-prefix", "text": old["text"],
        "artifact_sha256": case["row_sha256"], "voting_segments": [{"start": 0, "end": start, "text": prefix}],
        "abstention_audit": {"reviewed_text_sha256": sha(old["text"].encode()), "source_review": pin,
            "excluded_spans": [{"start": start, "end": end, "text": old["text"][start:],
                "reason": "Source-confirmed unprinted repetition replaces missing body; no omission vote."}]}}
    first = merge_witnesses([historical_witness])
    tail = merge_witnesses(witnesses)
    if tail["ocr_consensus"]["counts"] != case["counts"]:
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
    network_path = archive / case["network_file"]
    compact = compact_corpus_consensus(full, {"path": network_path.as_posix(), "key": locus})
    correction = {"schema": SCHEMA, "source_review": pin, "original_text": old["text"],
        "retained_prefix": prefix, "replacement_text": tail["text"], "replaced_span": scope,
        "source": source, "transcription_convention": authority["transcription_convention"],
        "license": "CC-BY-SA-4.0"}
    updated = {**old, **compact, "edition": "bekker1824-independent-ocr-consensus", "source": "reviewed-text-consensus",
               "language": "grc", "physical_refs": source, "license": "CC-BY-SA-4.0", "source_body_correction": correction,
               "component_attribution": [{"id": "reviewed-bekker-scan", "source": source, "license": "PD"},
                                         {"id": "source-library-local002", **credit}]}
    change = {"locus": locus, "original_text": old["text"], "corrected_text": updated["text"],
        "original_row": old, "corrected_row": updated, "original_row_sha256": case["row_sha256"],
        "corrected_row_sha256": row_sha(updated), "replacement_scope": scope, "source_review": pin,
        "source": source, "source_image": image, "reviewed_at": authority["reviewed_at"],
        "evidence": authority["source_evidence"], "following_body_anchor": following,
        "held_original_reading": historical_witness, "transcription_convention": authority["transcription_convention"]}
    return updated, {"source_review": pin, "license": "CC-BY-SA-4.0", "source_library": credit,
        "network": {"path": network_path.as_posix(), "sha256": sha(compress_gzip(encode({locus: full})))},
        "counts": {"corrected_rows": 1, "retained_prefix_characters": start, "held_loop_characters": end - start,
                   "replacement_agreement_slots": tail["ocr_consensus"]["counts"].get("agreement", 0),
                   "replacement_unresolved_slots": tail["ocr_consensus"]["counts"].get("unresolved", 0)},
        "changes": [change]}, {network_path: compress_gzip(encode({locus: full}))}


def validate_projection(row):
    if row.get("historical_reading_batches"):
        from repair_photius_historical_batches import restore_before_row
        row = restore_before_row(row)
    layer = row["source_body_correction"]
    slots = row["ocr_consensus"]["slots"]
    case = CASES.get(row.get("locus"))
    if (case is None or layer.get("schema") != SCHEMA
            or layer.get("retained_prefix") != layer.get("original_text", "")[:case["start"]]
            or row.get("text") != layer["retained_prefix"] + layer["replacement_text"]
            or row.get("analysis_text") != " ".join(slot["selected"] for slot in slots if slot["lexical_eligible"])):
        raise ValueError("Body correction lexical projection differs from its retained prefix and checked slots")
