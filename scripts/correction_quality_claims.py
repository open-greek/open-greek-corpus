"""Current-primary evidence for optional correction-log quality enrichment.

The mirror's work-level list alone cannot establish that a correction survived
a carve or re-keying. A manual claim needs both the recorded method and a whole
corrected reading still standing at its exact current primary locus. Row stamps
remain a separate authority for the consumers of this optional enrichment.
"""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path

from check_corrections_mirror_fresh import MANUAL, standing


def verified_manual_works(data: Path) -> set[str]:
    """Return log claims supported by a current primary row, without guessing loci.

    Missing mirror files supply no enrichment. Retired, re-keyed, and
    secondary-only readings do not establish a current-primary quality claim.
    Matching is literal and uses the mirror checker's Greek-token boundaries.
    """
    data = Path(data)
    provenance = data / "corrections_log/provenance.json"
    applied = data / "corrections_log/applied.jsonl"
    if not provenance.is_file() or not applied.is_file():
        return set()
    claimed = set(json.loads(provenance.read_text(encoding="utf-8")).get("corrected_works", []))
    if not claimed:
        return set()
    candidates = defaultdict(lambda: defaultdict(set))
    with applied.open(encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line)
            slug, locus, corrected = record.get("urn"), record.get("locus"), record.get("corrected")
            if (slug in claimed and record.get("by") in MANUAL and locus is not None
                    and isinstance(corrected, str) and corrected):
                candidates[slug][str(locus)].add(corrected)
    verified = set()
    # The actual primary directory defines the served set. A mirror slug cannot
    # redirect this check to a secondary file or a path outside that directory.
    for primary in (data / "corpus").glob("*.jsonl"):
        loci = candidates.get(primary.stem)
        if not loci:
            continue
        with primary.open(encoding="utf-8") as source:
            for line in source:
                if not line.strip():
                    continue
                row = json.loads(line)
                readings = loci.get(str(row.get("locus")))
                text = row.get("text") or ""
                if readings and any(standing(reading, text) for reading in readings):
                    verified.add(primary.stem)
                    break
    return verified
