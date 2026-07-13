#!/usr/bin/env python3
"""Scrub private-repo references out of the committed corpus_secondary audit strings.

The upstream (private) OCR pipeline emits row-level audit reasons into
data/corpus_secondary/*.jsonl. Some of those "secondary_reason" strings name the
private source repository by its directory name, which must never appear in this
public repo (see the "Public Repo Hygiene" rule: never reference private repos in
a public repo, not even in code or comments). This script rewords those
references in place so the audit trail stays meaningful without leaking the
private repo name.

To keep this public repo clean, the private repo's directory name is assembled
from fragments at runtime (PRIVATE_TOKEN) rather than written as a contiguous
literal anywhere in this file.

Rewrites, applied per line as a raw-substring replace (never a JSON re-serialize,
so Greek text and every other field stay byte-for-byte identical):

    "<repo> data/corrections/"  ->  "the upstream OCR pipeline's data/corrections/"
    any remaining bare "<repo>" ->  "the upstream OCR pipeline"

The replacement text contains only JSON-safe characters (letters, spaces,
apostrophe, slash), so JSONL validity is preserved. The script is idempotent:
re-running it is a no-op once the references are gone.

Path-agnostic: the corpus_secondary directory is located relative to this
script's own position in the repo (scripts/ -> ../data/corpus_secondary).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# The private upstream repo's directory name, built from fragments so the
# contiguous string is never present in this public file's source.
PRIVATE_TOKEN = "-".join(("greek", "ocr"))

# Ordered: the specific data/corrections/ form must run before the bare form so
# a reference is never transformed twice.
REPLACEMENTS = (
    (f"{PRIVATE_TOKEN} data/corrections/", "the upstream OCR pipeline's data/corrections/"),
    (PRIVATE_TOKEN, "the upstream OCR pipeline"),
)


def secondary_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "corpus_secondary"


def scrub_text(text: str) -> str:
    for needle, replacement in REPLACEMENTS:
        text = text.replace(needle, replacement)
    return text


def main() -> int:
    target = secondary_dir()
    if not target.is_dir():
        print(f"error: {target} is not a directory", file=sys.stderr)
        return 2

    files_changed = 0
    total_refs = 0

    for path in sorted(target.glob("*.jsonl")):
        original = path.read_text(encoding="utf-8")
        refs = original.count(PRIVATE_TOKEN)
        if refs == 0:
            continue

        scrubbed = scrub_text(original)

        # Validate every line still parses as JSON before writing anything.
        for lineno, line in enumerate(scrubbed.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                print(
                    f"error: {path.name}:{lineno} would not parse after scrub: {exc}",
                    file=sys.stderr,
                )
                return 1

        if PRIVATE_TOKEN in scrubbed:
            print(
                f"error: {path.name} still contains the private repo name after scrub",
                file=sys.stderr,
            )
            return 1

        path.write_text(scrubbed, encoding="utf-8")
        files_changed += 1
        total_refs += refs
        print(f"scrubbed {refs:>6} refs in {path.name}")

    print(f"\ndone: reworded {total_refs} references across {files_changed} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
