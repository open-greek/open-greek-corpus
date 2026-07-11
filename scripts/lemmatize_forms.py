#!/usr/bin/env python3
"""Lemmatize a plain list of Greek surface forms with Dilemma -> form/lemma TSV.

The remote half of build_work_lemma_counts.py's split lemmatization: run this
on a GPU box against the --emit-missing list, ship the map back, and rerun the
builder with --lemma-map. Self-contained on purpose (stdlib + dilemma only) so
it can be scp'd to a fresh instance.

Setup on a fresh CUDA box (pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel):
  git clone https://github.com/open-greek/dilemma && pip install -e dilemma
  cd dilemma && python -m dilemma download    # lookup.db + models
  rm -f model/*/encoder.onnx                  # force the torch (CUDA) backend

  python lemmatize_forms.py missing.tsv lemma_map.tsv [--device cuda]

Unresolved forms are omitted from the output (the builder retries them on a
later run). Appends as it goes, flushing every chunk, so a killed run loses at
most one chunk; rerunning with the same output file resumes past the forms
already mapped.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("forms", type=Path, help="input: one form per line")
    ap.add_argument("out", type=Path, help="output: form<TAB>lemma TSV")
    ap.add_argument("--device", default=None,
                    help='"cuda" / "cpu"; Dilemma auto-detects if omitted')
    ap.add_argument("--chunk", type=int, default=50000)
    args = ap.parse_args()

    forms = [f for f in args.forms.read_text(encoding="utf-8").splitlines() if f]
    done: set[str] = set()
    if args.out.exists():
        for line in args.out.read_text(encoding="utf-8").splitlines():
            form, _, _ = line.partition("\t")
            done.add(form)
        print(f"resuming: {len(done):,} forms already mapped in {args.out}",
              file=sys.stderr)
    todo = [f for f in forms if f not in done]
    print(f"lemmatizing {len(todo):,} of {len(forms):,} forms ...",
          file=sys.stderr)

    from dilemma import Dilemma  # noqa: PLC0415
    d = Dilemma(lang="grc", device=args.device)

    n_out = 0
    with args.out.open("a", encoding="utf-8") as sink:
        for i in range(0, len(todo), args.chunk):
            chunk = todo[i:i + args.chunk]
            for form, lemma in zip(chunk, d.lemmatize_batch(chunk)):
                lem = (lemma or "").strip()
                if lem:
                    sink.write(f"{form}\t{lem}\n")
                    n_out += 1
            sink.flush()
            print(f"  {min(i + args.chunk, len(todo)):,}/{len(todo):,}",
                  file=sys.stderr)
    print(f"wrote {n_out:,} mappings to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
