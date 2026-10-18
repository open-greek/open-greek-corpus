"""Reproducible word voting with explicit ties and reversible OCR witnesses.

Alignment ignores accents and case only to locate candidate positions. Votes
remain accent- and case-exact. No witness wins a tied reading; original text,
surface punctuation, support, omissions, and abstentions remain inspectable.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import difflib
import hashlib
import re
import unicodedata

GREEK = r"Ͱ-Ͽἀ-῿̀-ͯ"
WORD = re.compile(r"[([«“‘]*(?:[" + GREEK + r"])+(?:['’ʼ᾽])?[)\]»”’.,;··:!?…]*")
CORE = re.compile(r"[" + GREEK + r"]+(?:['’ʼ᾽])?")


def tokenize(text):
    text = re.sub(r"([" + GREEK + r"])[-‐]\s*\n\s*([" + GREEK + r"])", r"\1\2", text)
    words = []
    for match in WORD.finditer(text):
        key = unicodedata.normalize("NFC", CORE.search(match[0])[0])
        words.append((key, unicodedata.normalize("NFC", match[0])))
    return words


def alignment_key(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold())
        if not unicodedata.combining(c)).replace("ς", "σ").rstrip("'’ʼ᾽")


def word_cost(slot, word):
    key = alignment_key(word)
    keys = [alignment_key(k) for k in slot]
    if key in keys:
        return 0
    similarity = max((difflib.SequenceMatcher(None, key, k, autojunk=False).ratio()
        for k in keys), default=0)
    return .45 if similarity >= .6 else 1.1


def align(slots, words):
    """Minimum-cost word/profile alignment; return profile and input indexes."""
    n, m = len(slots), len(words)
    previous = list(range(m + 1))
    directions = [bytearray([2] * (m + 1))]
    for i, slot in enumerate(slots, 1):
        row = [float(i)] + [0.] * m
        direction = bytearray(m + 1)
        direction[0] = 1
        for j, (word, surface) in enumerate(words, 1):
            choices = (previous[j - 1] + word_cost(slot, word), previous[j] + 1, row[j - 1] + 1)
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
        if status == "unresolved":
            display.append("⟦" + " ∥ ".join(key or "∅" for key in winners) + "⟧")
        elif status != "omission":
            key = winners[0]
            surfaces = Counter(slot[key].values())
            best = max(surfaces.values())
            surface_winners = sorted(s for s, count in surfaces.items() if count == best)
            display.append(surface_winners[0] if len(surface_winners) == 1
                else "⟦" + " ∥ ".join(surface_winners) + "⟧")
            lexical.append(key)
        stats[status] += 1
        records.append({"position": i, "readings": readings,
            "omission_support": gaps, "abstentions": abstentions,
            "omission_groups": omission_groups,
            "status": status, "selected": winners[0] if len(winners) == 1 else None,
            "tied_readings": winners if len(winners) > 1 else []})
    return {"text": " ".join(display), "analysis_text": " ".join(lexical),
        "ocr_consensus": {"schema_version": 1,
            "policy": "Exact word votes after accent-insensitive positional alignment. Preserve tied readings; omissions vote only inside each witness's observed span. Original raw text remains reversible.",
            "witnesses": [{**w, "text_sha256": hashlib.sha256(w["text"].encode()).hexdigest()}
                for w in witnesses], "slots": records, "counts": dict(stats)}}
