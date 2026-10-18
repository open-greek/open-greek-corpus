"""Reproducible word voting with explicit ties and reversible OCR witnesses.

Alignment ignores accents and case only to locate candidate positions. Votes
remain accent- and case-exact. No witness wins a tied reading; original text,
surface punctuation, support, omissions, and abstentions remain inspectable.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import difflib
from functools import lru_cache
import hashlib
import json
from pathlib import PurePosixPath
import re
import unicodedata

GREEK = r"Ͱ-Ͽἀ-῿̀-ͯ"
APOSTROPHES = frozenset("'’ʼ᾽")


def _network_sha256(result):
    raw = json.dumps(result, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def compact_corpus_consensus(result, network_reference):
    """Keep countable slot boundaries and link the complete archived vote network.

    Archive the original merge result under the supplied key before publishing
    the compact projection. Every raw witness remains directly available in the
    corpus, while losing readings, support, surfaces and abstentions remain in
    the hash-checked compressed archive. No slot is removed, including omissions,
    damaged words and unresolved readings that must break lexical adjacency.
    """
    path, key = network_reference["path"], network_reference["key"]
    if (not isinstance(path, str) or not path or "\\" in path or ":" in path
            or PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts
            or not isinstance(key, str) or not key):
        raise ValueError("A full vote network needs a relative archive path and nonempty string key")
    network = result["ocr_consensus"]
    if "full_network" in network:
        raise ValueError("Archive the complete vote network before compacting it")
    fields = ("position", "selected", "status", "lexical_eligible", "tied_readings")
    slots = []
    for position, slot in enumerate(network["slots"]):
        if slot["position"] != position or not all(field in slot for field in fields):
            raise ValueError("The complete vote network has missing or unordered slots")
        slots.append({field: deepcopy(slot[field]) for field in fields})
    return {**deepcopy({k: v for k, v in result.items() if k != "ocr_consensus"}),
        "ocr_consensus": {**deepcopy({k: v for k, v in network.items() if k != "slots"}),
            "slots": slots, "storage": "compact-slots-v1",
            "full_network": {"path": path, "key": key, "sha256": _network_sha256(result)}}}


def restore_corpus_consensus(compact, archived_result):
    """Verify an archive entry and reconstruct the exact original merge result."""
    reference = compact["ocr_consensus"]["full_network"]
    if _network_sha256(archived_result) != reference["sha256"]:
        raise ValueError("The archived full vote network changed")
    if compact_corpus_consensus(archived_result, reference) != compact:
        raise ValueError("The corpus projection differs from its full vote network")
    return deepcopy(archived_result)


def greek_letter(char):
    return unicodedata.category(char).startswith("L") and "GREEK" in unicodedata.name(char, "")


def lexical_eligible(word):
    letters = [char for char in word if unicodedata.category(char).startswith("L")]
    return bool(letters) and all(greek_letter(char) for char in letters)


def tokenize(text):
    text = re.sub(r"([" + GREEK + r"])[-‐]\s*\n\s*([" + GREEK + r"])", r"\1\2", text)
    words = []
    index = 0
    while index < len(text):
        if not unicodedata.category(text[index]).startswith(("L", "M")):
            index += 1
            continue
        start = index
        while index < len(text) and (unicodedata.category(text[index]).startswith(("L", "M")) or text[index] in APOSTROPHES):
            index += 1
        raw = text[start:index]
        if not any(greek_letter(char) for char in raw):
            continue
        left, right = start, index
        while left and text[left - 1] in "([«“‘":
            left -= 1
        while right < len(text) and text[right] in ")]»”’.,;··:!?…":
            right += 1
        if index < len(text) and text[index] in "-‐" and not text[index + 1:].strip():
            right = index + 1  # retain a printed word continued on another page
        words.append((unicodedata.normalize("NFC", raw),
            unicodedata.normalize("NFC", text[left:right])))
    return words


def alignment_key(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold())
        if not unicodedata.combining(c)).replace("ς", "σ").rstrip("'’ʼ᾽")


@lru_cache(maxsize=200000)
def _word_cost(keys, key):
    if key in keys:
        return 0
    for other in keys:
        if min(len(key), len(other)) / max(1, len(key), len(other)) < .43:
            continue
        matcher = difflib.SequenceMatcher(None, key, other, autojunk=False)
        if matcher.quick_ratio() >= .6 and matcher.ratio() >= .6:
            return .45
    return 1.1


def _align_dp(slots, words):
    """Minimum-cost alignment inside one interval between shared anchors."""
    n, m = len(slots), len(words)
    slot_keys = [tuple(sorted({alignment_key(k) for k in slot})) for slot in slots]
    word_keys = [alignment_key(k) for k, surface in words]
    previous = list(range(m + 1))
    directions = [bytearray([2] * (m + 1))]
    for i, keys in enumerate(slot_keys, 1):
        row = [float(i)] + [0.] * m
        direction = bytearray(m + 1)
        direction[0] = 1
        for j, key in enumerate(word_keys, 1):
            choices = (previous[j - 1] + _word_cost(keys, key), previous[j] + 1, row[j - 1] + 1)
            step = min(range(3), key=choices.__getitem__)
            row[j], direction[j] = choices[step], step
        previous = row
        directions.append(direction)
    operations = []
    i, j = n, m
    while i or j:
        step = directions[i][j]
        if i and j and step == 0:
            i -= 1
            j -= 1
            operations.append((i, j))
        elif i and (not j or step == 1):
            i -= 1
            operations.append((i, None))
        else:
            j -= 1
            operations.append((None, j))
    return list(reversed(operations))


def align(slots, words):
    """Align exact shared runs first, then vote all readings between them.

    The anchors are positional scaffolding, never a selected reading. A page
    with 1,500 words ordinarily becomes many small intervals rather than a
    quadratic profile comparison. Accent/case differences remain exact-vote
    alternatives after either alignment path.
    """
    if len(slots) * len(words) < 4096:
        return _align_dp(slots, words)
    profile = [alignment_key(max(slot, key=lambda key: (len(slot[key]), key))) for slot in slots]
    incoming = [alignment_key(key) for key, surface in words]
    anchors = [block for block in difflib.SequenceMatcher(None, profile, incoming,
        autojunk=False).get_matching_blocks() if block.size >= 4]
    if not anchors:
        return _align_dp(slots, words)
    operations, left, right = [], 0, 0
    for anchor in [*anchors, difflib.Match(len(slots), len(words), 0)]:
        for i, j in _align_dp(slots[left:anchor.a], words[right:anchor.b]):
            operations.append((None if i is None else i + left, None if j is None else j + right))
        operations.extend((anchor.a + offset, anchor.b + offset) for offset in range(anchor.size))
        left, right = anchor.a + anchor.size, anchor.b + anchor.size
    return operations


def merge_witnesses(witnesses):
    """Merge one physical page; duplicate raw artifacts contribute one vote."""
    unique = {}
    for witness in witnesses:
        identity = witness["artifact_sha256"]
        if identity in unique:
            if unique[identity]["text"] != witness["text"]:
                raise ValueError("One raw OCR artifact was supplied with conflicting text")
            continue
        unique[identity] = witness
    witnesses = sorted(unique.values(), key=lambda w: w["id"])
    if not witnesses:
        raise ValueError("A consensus needs at least one original OCR witness")
    if len({w["id"] for w in witnesses}) != len(witnesses):
        raise ValueError("OCR witness identifiers must be unique")
    tokens = {w["id"]: tokenize(w["text"]) for w in witnesses}
    vote_group = {w["id"]: w.get("vote_group", w["id"]) for w in witnesses}
    # Centrality chooses an alignment scaffold, never a winning reading. The
    # final vote still considers every original artifact and retains ties.
    centrality = {}
    for witness in witnesses:
        a = [alignment_key(k) for k, surface in tokens[witness["id"]]]
        centrality[witness["id"]] = sum(difflib.SequenceMatcher(None, a,
            [alignment_key(k) for k, surface in tokens[other["id"]]], autojunk=False).ratio()
            for other in witnesses)
    order = sorted(witnesses, key=lambda w: (-centrality[w["id"]], w["id"]))
    slots = []
    for witness in order:
        identifier = witness["id"]
        words = tokens[identifier]
        if not slots:
            slots = [{key: {identifier: surface}} for key, surface in words]
            continue
        merged = []
        for old, new in align(slots, words):
            slot = {} if old is None else slots[old]
            if new is not None:
                key, surface = words[new]
                slot.setdefault(key, {})[identifier] = surface
            merged.append(slot)
        slots = merged
    coverage = {}
    for witness in witnesses:
        identifier = witness["id"]
        positions = [i for i, slot in enumerate(slots)
            if any(identifier in sources for sources in slot.values())]
        coverage[identifier] = (min(positions), max(positions)) if positions else None
    display, lexical, records = [], [], []
    stats = Counter()
    for i, slot in enumerate(slots):
        present = {source for sources in slot.values() for source in sources}
        gaps = [identifier for identifier, bounds in coverage.items()
            if identifier not in present and bounds is not None and bounds[0] < i < bounds[1]]
        abstentions = [w["id"] for w in witnesses if w["id"] not in present and w["id"] not in gaps]
        readings = [{"text": key, "support": sorted(sources),
            "support_groups": sorted({vote_group[source] for source in sources}),
            "surfaces": dict(sorted(sources.items()))} for key, sources in sorted(slot.items())]
        counts = {key: len({vote_group[source] for source in sources}) for key, sources in slot.items()}
        present_groups = {vote_group[source] for source in present}
        omission_groups = sorted({vote_group[source] for source in gaps} - present_groups)
        counts[""] = len(omission_groups)
        maximum = max(counts.values())
        winners = sorted(key for key, count in counts.items() if count == maximum)
        status = "unresolved" if len(winners) > 1 else "omission" if winners == [""] else "agreement" if maximum > 1 else "single-witness"
        vote_status = status
        fragment_support = sorted(source for sources in slot.values()
                                  for source, surface in sources.items()
                                  if surface.endswith(("-", "‐")))
        incomplete = (len(winners) == 1 and bool(winners[0]) and
                      any(surface.endswith(("-", "‐")) for surface in slot[winners[0]].values()))
        eligible = len(winners) == 1 and bool(winners[0]) and lexical_eligible(winners[0]) and not incomplete
        if incomplete:
            status = "incomplete-reading"
        elif len(winners) == 1 and winners[0] and not eligible:
            status = "damaged-reading"
        if status == "unresolved":
            display.append("⟦" + " ∥ ".join(key or "∅" for key in winners) + "⟧")
        elif status != "omission":
            key = winners[0]
            surfaces = Counter(slot[key].values())
            best = max(surfaces.values())
            surface_winners = sorted(s for s, count in surfaces.items() if count == best)
            display.append(surface_winners[0] if len(surface_winners) == 1
                else "⟦" + " ∥ ".join(surface_winners) + "⟧")
            if eligible:
                lexical.append(key)
        stats[status] += 1
        records.append({"position": i, "readings": readings,
            "omission_support": gaps, "abstentions": abstentions,
            "omission_groups": omission_groups,
            "status": status, "vote_status": vote_status, "lexical_eligible": eligible,
            "lexical_exclusion": ("source-page-end-fragment" if incomplete else
                                  "mixed-script-token" if status == "damaged-reading" else None),
            "terminal_fragment_support": fragment_support,
            "selected": winners[0] if len(winners) == 1 else None,
            "tied_readings": winners if len(winners) > 1 else []})
    return {"text": " ".join(display), "analysis_text": " ".join(lexical),
        "ocr_consensus": {"schema_version": 1,
            "policy": "Exact word votes after accent-insensitive positional alignment. Preserve tied readings; omissions vote only inside each witness's observed span. Original raw text remains reversible.",
            "witnesses": [{**w, "text_sha256": hashlib.sha256(w["text"].encode()).hexdigest()}
                for w in witnesses], "slots": records, "counts": dict(stats)}}
