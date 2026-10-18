"""Audit an unchanged leading fragment without inventing a cross-page word."""
from copy import deepcopy


def exclude_leading_fragment(result, previous_witnesses, current_witnesses, *,
        previous_region, current_region, body_start_evidence, raw_network_reference,
        review_id, reviewed_at, adjacency_evidence):
    """Exclude slot zero only when independent body readings prove continuation.

    Callers must establish consecutive leaves within one reading stream and
    verify that the current witnesses start with body text after any headers.
    The helper independently requires the same two or more vote groups on both
    leaves, a terminal Greek hyphenated token in every preceding witness, and
    matching accent-insensitive terminal/current tokens. Uncertain boundaries
    return the unchanged result and no review. Original spellings stay visible.
    """
    from ocr_consensus import alignment_key, compact_corpus_consensus, lexical_eligible, tokenize
    previous = {value.get("vote_group", value["id"]): value for value in previous_witnesses}
    current = {value.get("vote_group", value["id"]): value for value in current_witnesses}
    if (len(previous) < 2 or len(previous) != len(previous_witnesses) or
            len(current) != len(current_witnesses) or set(previous) != set(current) or not adjacency_evidence or
            not review_id or not reviewed_at or not previous_region or not current_region):
        return result, None, None
    observations = {}
    previous_keys, current_keys = set(), set()
    for group in sorted(previous):
        before, after = previous[group], current[group]
        before_tokens, after_tokens = tokenize(before["text"]), tokenize(after["text"])
        if (not before["text"].rstrip().endswith(("-", "‐")) or not before_tokens or not after_tokens or
                not before_tokens[-1][1].endswith(("-", "‐")) or
                not lexical_eligible(before_tokens[-1][0]) or not lexical_eligible(after_tokens[0][0]) or
                not body_start_evidence.get(after["id"])):
            return result, None, None
        previous_keys.add(alignment_key(before_tokens[-1][0]))
        current_keys.add(alignment_key(after_tokens[0][0]))
        observations[group] = {"previous_witness": before["id"], "current_witness": after["id"],
            "previous_artifact_sha256": before["artifact_sha256"],
            "current_artifact_sha256": after["artifact_sha256"],
            "previous_terminal": before_tokens[-1][1], "current_initial": after_tokens[0][1]}
    slots = result["ocr_consensus"]["slots"]
    if len(previous_keys) != 1 or len(current_keys) != 1 or not slots:
        return result, None, None
    selected = slots[0]["selected"]
    if not selected or alignment_key(selected) not in current_keys:
        return result, None, None
    corrected = deepcopy(result)
    analysis = result["analysis_text"].split()
    if slots[0]["lexical_eligible"]:
        if not analysis or analysis[0] != selected:
            raise ValueError("A boundary fragment differs from its lexical projection")
        analysis = analysis[1:]
    corrected["analysis_text"] = " ".join(analysis)
    raw_reference = compact_corpus_consensus(result, raw_network_reference)["ocr_consensus"]["full_network"]
    audit = {"generator": "scripts/ocr_boundary_fragments.py", "review_id": review_id,
        "date": reviewed_at, "source_kind": "independent-scan-boundary-readings",
        "change_kind": "lexical-eligibility-only", "original_text": result["text"],
        "corrected_text": corrected["text"], "original_analysis_text": result["analysis_text"],
        "corrected_analysis_text": corrected["analysis_text"], "raw_fragment_votes": deepcopy(slots[0]),
        "previous_region": previous_region, "current_region": current_region,
        "boundary_observations": observations, "body_start_evidence": body_start_evidence,
        "evidence": adjacency_evidence,
        "policy": "The preceding body ends with a Greek printed hyphen in every independent witness. The following verified body starts with the same continuation reading. Keep both displayed fragments and every raw vote; exclude the leading continuation as an independent word without supplying a joined spelling.",
        "reversal": {"raw_network_key": raw_network_reference["key"],
            "function": "scripts.ocr_boundary_fragments.unapply_review",
            "policy": "Restore the hash-checked pre-review network; the admission undo operation restores all prior files."}}
    network = corrected["ocr_consensus"]
    old_status = slots[0]["status"]
    network["slots"][0].update(status="continuation-fragment", lexical_eligible=False,
        lexical_exclusion="independently-observed-cross-page-fragment",
        boundary_review={"id": review_id, "raw_status": old_status, "previous_region": previous_region})
    network["counts"][old_status] -= 1
    if network["counts"][old_status] == 0:
        del network["counts"][old_status]
    network["counts"]["continuation-fragment"] = network["counts"].get("continuation-fragment", 0) + 1
    network["raw_ocr_network"] = raw_reference
    network["reviewed_corrections"] = [audit]
    network["policy"] += " A separately audited page-boundary eligibility review preserves the unchanged leading continuation but excludes it as an independent word."
    return corrected, (raw_network_reference["key"], result), audit


def unapply_review(result, archived_raw_result):
    """Recover an exact original network by its retained boundary-review hash."""
    from ocr_consensus import compact_corpus_consensus
    network = result["ocr_consensus"]
    if not any(value.get("generator") == "scripts/ocr_boundary_fragments.py"
               for value in network.get("reviewed_corrections", [])):
        raise ValueError("This result does not carry a boundary-fragment review")
    reference = network["raw_ocr_network"]
    actual = compact_corpus_consensus(archived_raw_result,
        {"path": reference["path"], "key": reference["key"]})["ocr_consensus"]["full_network"]
    if actual != reference:
        raise ValueError("The original network differs from the boundary review's retained evidence")
    return deepcopy(archived_raw_result)
