#!/usr/bin/env python3
"""Export UD_Ancient_Greek-PTNK as cog's standardized annotation export.

This produces the annotation export defined by docs/annotation-export-contract.md:
per-work, CTS-URN-keyed streams of token records, with cog-owned encoding
normalization and source-native tagsets/lemmas preserved verbatim. It is item 1b
of the annotation-consumption queue and is what dilemma pins ("cog export
<release_id>, hash <content_hash>").

Source: UD_Ancient_Greek-PTNK (github.com/UniversalDependencies/UD_Ancient_Greek-PTNK),
a manually annotated Universal Dependencies treebank over portions of the
Septuagint (Genesis, Ruth) as transmitted by the Codex Alexandrinus. The text
base is extracted from https://greekdoc.github.io; morphology is John Barach's
manual annotation and the syntax was initialized by cross-lingual projection from
the parallel Ancient Hebrew treebank and then manually corrected. The upstream
machine-readable metadata marks Lemmas, UPOS, Features, and Relations all as
"manual native", so every token is analysis="manual", provenance_tag="ptnk".

Provenance/policy (docs/source-policy.md):
  - Independent manual gold: NOT PROIEL data and NOT the output of a PROIEL-trained
    model (its syntax is projected from the Ancient Hebrew treebank, not PROIEL),
    so it is tier-3 (non-PROIEL) and carries no provenance=gorman or proiel-* tag.
  - License is CC BY-SA 4.0 for the whole treebank (LICENSE.txt and the upstream
    machine-readable metadata). No NonCommercial clause, so nothing is excluded.

Inputs (all from the retained PTNK clone, default ~/Documents/ud_ptnk):
  - grc_ptnk-ud-{train,dev,test}.conllu
      the CoNLL-U annotation (form, lemma, UPOS, FEATS morphology, head, deprel;
      a per-token Ref in MISC giving the book/chapter.verse locus).

The UD train/dev/test split is preserved per token as the `split` field, because
a consumer (dilemma) holds out TEST as eval and only ingests filtered TRAIN. The
split is authoritative per source file; a single work (Genesis) spans all three
splits, so each token records its own split rather than the work choosing one.

cog owns encoding normalization (NFC; elision apostrophes -> U+2019; standard
final/medial sigma), applied to form and lemma. cog does NOT normalize lemma
conventions: PTNK's native dictionary headwords are preserved verbatim.

The export is deterministic: gzip is written with mtime=0 and the content hash is
computed over the uncompressed per-work payloads, so re-running on unchanged input
reproduces byte-identical files and the same content_hash.

Storage (docs/annotation-export-contract.md, "Storage"): the payload this writes
is NOT committed to git. It is uploaded to the Hugging Face dataset repo with
scripts/upload_annotation_export.py; git tracks this exporter plus the pointer
stub written next to the release dir (data/annotations/ptnk/<release_id>.json).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import gzip
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

# The HF dataset repo that holds export payloads (see the module docstring and
# docs/annotation-export-contract.md, "Storage"); the release id is the path in
# the repo. scripts/upload_annotation_export.py shares this default.
HF_EXPORTS_REPO = "ciscoriordan/open-greek-corpus-annotation-exports"

# The retained upstream clone is pinned by commit SHA (docs/pinning-discipline.md).
# The clone at UPSTREAM_COMMIT is the reproducible input; record both.
UPSTREAM_COMMIT = "818fb315ff1f6cd95b6e7fa90f3707488d2b010d"

# UD book name (from sent_id) -> greekLit CTS work id (textgroup.work). Both books
# are Septuagint books under TLG textgroup tlg0527; work numbers are the TLG canon
# ordering (Genesis = tlg001, Ruth = tlg010). The Ref prefix cross-checks the book.
BOOK_TO_WORK = {
    "Genesis": "tlg0527.tlg001",
    "Ruth": "tlg0527.tlg010",
}
REF_PREFIX_TO_BOOK = {
    "GEN": "Genesis",
    "RUTH": "Ruth",
}

# The three UD split files and the split label each carries.
SPLIT_FILES = {
    "train": "grc_ptnk-ud-train.conllu",
    "dev": "grc_ptnk-ud-dev.conllu",
    "test": "grc_ptnk-ud-test.conllu",
}

_SENT_ID_RE = re.compile(r"^Septuagint-([A-Za-z]+)-(.+)-grc$")


def make_pointer_stub(manifest: dict, hf_repo: str) -> dict:
    """The small git-tracked pointer for a release: identity + where the payload
    lives on the Hub. git holds the recipe and this pointer; HF holds the payload."""
    exp = manifest["export"]
    release_id = exp["release_id"]
    return {
        "release_id": release_id,
        "content_hash": exp["content_hash"],
        "pin_line": exp["pin_line"],
        "storage": {
            "hf_dataset_repo": hf_repo,
            "repo_type": "dataset",
            "path_in_repo": f"{release_id}/",
            "url": f"https://huggingface.co/datasets/{hf_repo}/tree/main/{release_id}",
            "payload": "works/<work_id>.jsonl.gz per exported work, plus manifest.json",
            "note": ("docs/annotation-export-contract.md, 'Storage': export payloads live on "
                     "the Hub; git tracks the exporter script and this pointer stub only. "
                     "Regenerate locally with scripts/export_ptnk_annotations.py, publish with "
                     "scripts/upload_annotation_export.py."),
        },
        "counts": exp["counts"],
        "generated_by": exp["generated_by"],
        "generated_at": exp["generated_at"],
        "contract": exp["contract"],
        "upstream_pin": {
            "source": f"{manifest['source']['name']} ({manifest['source']['ud_version']})",
            "github": manifest["source"]["github"],
            "commit": manifest["source"]["commit"],
            "retained_clone": manifest["source"]["retained_clone"],
            "note": "cog pins the upstream; consumers pin only pin_line (docs/pinning-discipline.md)",
        },
    }


# --- cog-owned encoding normalization -------------------------------------
# Identical to scripts/export_oga_annotations.py: encoding is a cog-owned
# guarantee and must be the same across every annotation export.

# Elision / apostrophe characters that are unified to U+2019 (right single
# quotation mark). Deliberately conservative: U+00B4 (acute) and U+2032 (prime)
# are NOT included because they serve as the Greek numeral keraia / prime mark.
_APOSTROPHES = {
    "ʼ",  # MODIFIER LETTER APOSTROPHE
    "'",  # APOSTROPHE
    "‘",  # LEFT SINGLE QUOTATION MARK
    "’",  # RIGHT SINGLE QUOTATION MARK (target)
}
_APOS_TABLE = {ord(c): "’" for c in _APOSTROPHES}


def _normalize_sigma(s: str) -> str:
    """Map lunate sigma to standard sigma and enforce final/medial position."""
    if not any(c in s for c in ("ϲ", "Ϲ", "σ", "ς")):
        return s
    s = s.replace("ϲ", "σ").replace("Ϲ", "Σ")
    if "σ" not in s and "ς" not in s:
        return s
    chars = list(s)
    n = len(chars)
    for i, ch in enumerate(chars):
        if ch in ("σ", "ς"):
            following_letter = any(chars[j].isalpha() for j in range(i + 1, n))
            chars[i] = "σ" if following_letter else "ς"
    return "".join(chars)


def normalize(text):
    """Apply cog's guaranteed encoding normalization to a surface/lemma string."""
    if text is None:
        return None
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_APOS_TABLE)
    text = _normalize_sigma(text)
    # Re-apply NFC in case sigma/apostrophe swaps changed composition.
    return unicodedata.normalize("NFC", text)


# --- CTS helpers ----------------------------------------------------------

def work_cts_urn(work_id: str) -> str:
    """Full greekLit CTS URN for a PTNK work id (textgroup.work)."""
    return f"urn:cts:greekLit:{work_id}"


def parse_sent_id(sent_id: str):
    """('Septuagint-Genesis-1:17-18-grc') -> (book, chapter:int, verse_start:int).

    The verse part may be a single verse ('31:1') or a verse range ('1:17-18');
    chapter and the range's first verse are used for deterministic ordering.
    """
    m = _SENT_ID_RE.match(sent_id)
    if not m:
        raise ValueError(f"unrecognized sent_id: {sent_id!r}")
    book, cv = m.group(1), m.group(2)
    chapter_s, _, verse_s = cv.partition(":")
    verse_start = verse_s.split("-", 1)[0]
    try:
        return book, int(chapter_s), int(verse_start)
    except ValueError:
        # Fall back to sorting such refs last but still deterministically.
        return book, 10**9, 10**9


# --- CoNLL-U parsing ------------------------------------------------------

def parse_conllu(path: str):
    """Yield (meta, rows) per sentence.

    meta is the dict of '# key = value' comment lines; rows is the list of raw
    10-column CoNLL-U field lists (both multiword-range 'n-m' lines and the
    integer-id word lines, in file order).
    """
    meta: dict = {}
    rows: list[list[str]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                if rows:
                    yield meta, rows
                meta, rows = {}, []
                continue
            if line.startswith("#"):
                if "=" in line:
                    k, _, v = line[1:].partition("=")
                    meta[k.strip()] = v.strip()
                continue
            cols = line.split("\t")
            if len(cols) >= 10:
                rows.append(cols)
    if rows:
        yield meta, rows


def _locus_from_misc(misc: str):
    """Extract the CTS locus (chapter.verse) from a MISC 'Ref=GEN_31.1' field."""
    for field in misc.split("|"):
        if field.startswith("Ref="):
            ref = field[len("Ref="):]
            # Ref is <BOOK>_<chapter>.<verse>; the locus is the dotted passage.
            return ref.split("_", 1)[1] if "_" in ref else ref
    return None


# --- Token records --------------------------------------------------------

TOKEN_FIELD_ORDER = [
    "id", "form", "lemma", "pos", "morph", "head", "deprel",
    "locus", "sentence_id", "split", "analysis", "provenance_tag", "parallel_id",
]


def build_token_record(cols, sentence_id, parallel_id, split, locus):
    """One token record from a CoNLL-U line. Multiword-range 'n-m' lines keep a
    string id and carry only the surface form (their component words hold the
    annotation); word lines carry the full manual annotation."""
    tok_id_raw = cols[0]
    try:
        tok_id = int(tok_id_raw)
    except ValueError:
        tok_id = tok_id_raw  # multiword range 'n-m'

    lemma = None if cols[2] == "_" else cols[2]
    upos = None if cols[3] == "_" else cols[3]
    feats = None if cols[5] == "_" else cols[5]
    deprel = None if cols[7] == "_" else cols[7]
    head_raw = cols[6]
    if head_raw == "_":
        head = None
    else:
        try:
            head = int(head_raw)
        except ValueError:
            head = head_raw

    return {
        "id": tok_id,
        "form": normalize(cols[1]),
        "lemma": normalize(lemma) if lemma is not None else None,
        "pos": upos,      # UD UPOS, native (not remapped)
        "morph": feats,   # UD FEATS, native (not remapped)
        "head": head,
        "deprel": deprel,
        "locus": locus,
        "sentence_id": sentence_id,
        "split": split,
        "analysis": "manual",
        "provenance_tag": "ptnk",
        "parallel_id": parallel_id,
    }


def load_split(path: str, split: str):
    """Parse one split file into a list of sentence dicts with their records."""
    sentences = []
    for meta, rows in parse_conllu(path):
        sent_id = meta.get("sent_id")
        if sent_id is None:
            raise ValueError(f"{path}: sentence without a sent_id")
        parallel_id = meta.get("parallel_id")
        book, chapter, verse_start = parse_sent_id(sent_id)

        # Two passes: resolve each row's locus (multiword-range lines have no Ref,
        # so they inherit the locus of the next word line that does).
        loci = [_locus_from_misc(cols[9]) for cols in rows]
        for i in range(len(rows)):
            if loci[i] is None:
                for j in range(i + 1, len(rows)):
                    if loci[j] is not None:
                        loci[i] = loci[j]
                        break

        records = [
            build_token_record(cols, sent_id, parallel_id, split, loci[i])
            for i, cols in enumerate(rows)
        ]
        sentences.append({
            "sent_id": sent_id,
            "book": book,
            "order": (chapter, verse_start, sent_id),
            "records": records,
        })
    return sentences


# --- Export ---------------------------------------------------------------

def export_work(work_id: str, sentences: list, out_path: Path):
    """Write one work's JSONL.gz (deterministic) and return per-work stats."""
    # Deterministic document order: chapter, verse, then unique sent_id.
    sentences = sorted(sentences, key=lambda s: s["order"])
    buf = io.StringIO()
    n_tokens = n_words = n_ranges = n_missing = 0
    split_tokens = {"train": 0, "dev": 0, "test": 0}
    split_sents = {"train": 0, "dev": 0, "test": 0}
    for sent in sentences:
        split_sents[sent["records"][0]["split"]] += 1
        for rec in sent["records"]:
            if isinstance(rec["id"], str):
                n_ranges += 1
            else:
                n_words += 1
            if rec["locus"] is None:
                n_missing += 1
            split_tokens[rec["split"]] += 1
            buf.write(json.dumps({k: rec[k] for k in TOKEN_FIELD_ORDER}, ensure_ascii=False))
            buf.write("\n")
            n_tokens += 1
    payload = buf.getvalue().encode("utf-8")
    sha = hashlib.sha256(payload).hexdigest()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
            gz.write(payload)
    return {
        "work_id": work_id,
        "cts_urn": work_cts_urn(work_id),
        "file": out_path.name,
        "tokens": n_tokens,
        "words": n_words,
        "multiword_ranges": n_ranges,
        "sentences": len(sentences),
        "split_tokens": split_tokens,
        "split_sentences": split_sents,
        "sha256": sha,
        "_missing_locus": n_missing,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ptnk-root", default=os.environ.get("PTNK_ROOT", os.path.expanduser("~/Documents/ud_ptnk")),
                    help="retained PTNK clone (default $PTNK_ROOT or ~/Documents/ud_ptnk)")
    ap.add_argument("--out-dir", default=None,
                    help="output release dir (default <repo>/data/annotations/ptnk/<release_id>)")
    ap.add_argument("--release-id", default="ptnk-v1", help="cog export release id (default ptnk-v1)")
    ap.add_argument("--hf-repo", default=HF_EXPORTS_REPO,
                    help="HF dataset repo the pointer stub records as the payload home")
    args = ap.parse_args()

    ptnk_root = Path(args.ptnk_root)
    repo_root = Path(__file__).resolve().parent.parent
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "data" / "annotations" / "ptnk" / args.release_id

    for label, fname in SPLIT_FILES.items():
        if not (ptnk_root / fname).is_file():
            sys.exit(f"PTNK split file not found: {ptnk_root / fname}")

    # Verify the retained clone is at the pinned commit (best-effort; a bare copy
    # without .git is allowed but then we cannot verify and only warn).
    head = None
    git_head = ptnk_root / ".git" / "HEAD"
    if git_head.is_file():
        import subprocess
        try:
            head = subprocess.check_output(["git", "-C", str(ptnk_root), "rev-parse", "HEAD"],
                                           text=True).strip()
        except Exception:
            head = None
    if head and head != UPSTREAM_COMMIT:
        sys.exit(f"[ptnk-export] ABORT: clone at {head} != pinned {UPSTREAM_COMMIT}; "
                 f"update UPSTREAM_COMMIT deliberately if the upstream pin is meant to move")

    # Load all splits, then group sentences by work (a work spans splits).
    by_work: dict[str, list] = {}
    for split, fname in SPLIT_FILES.items():
        sents = load_split(str(ptnk_root / fname), split)
        for sent in sents:
            book = sent["book"]
            if book not in BOOK_TO_WORK:
                sys.exit(f"[ptnk-export] ABORT: unknown book {book!r} in {fname}; "
                         f"add it to BOOK_TO_WORK with its greekLit work id")
            by_work.setdefault(BOOK_TO_WORK[book], []).append(sent)
        print(f"[ptnk-export] loaded {len(sents)} sentences from {fname} (split={split})", flush=True)

    works: list[dict] = []
    totals = {"tokens": 0, "words": 0, "multiword_ranges": 0, "sentences": 0, "missing_locus": 0}
    split_tokens = {"train": 0, "dev": 0, "test": 0}
    split_sents = {"train": 0, "dev": 0, "test": 0}
    for work_id in sorted(by_work):
        out_path = out_dir / "works" / f"{work_id}.jsonl.gz"
        stats = export_work(work_id, by_work[work_id], out_path)
        totals["tokens"] += stats["tokens"]
        totals["words"] += stats["words"]
        totals["multiword_ranges"] += stats["multiword_ranges"]
        totals["sentences"] += stats["sentences"]
        totals["missing_locus"] += stats.pop("_missing_locus")
        for k in split_tokens:
            split_tokens[k] += stats["split_tokens"][k]
            split_sents[k] += stats["split_sentences"][k]
        works.append(stats)
        print(f"[ptnk-export] wrote {work_id} ({stats['cts_urn']}): "
              f"{stats['tokens']} tokens, {stats['sentences']} sentences", flush=True)

    # Deterministic content hash over the uncompressed per-work payloads.
    hasher = hashlib.sha256()
    for w in sorted(works, key=lambda x: x["work_id"]):
        hasher.update(f"{w['work_id']}:{w['sha256']}\n".encode("utf-8"))
    content_hash = "sha256:" + hasher.hexdigest()

    manifest = {
        "export": {
            "release_id": args.release_id,
            "contract": "docs/annotation-export-contract.md",
            "generated_by": "scripts/export_ptnk_annotations.py",
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content_hash": content_hash,
            "content_hash_method": (
                "sha256 over the newline-joined '<work_id>:<sha256-of-uncompressed-jsonl>' lines, "
                "work_id-sorted; excludes generated_at and gzip framing so it is reproducible on unchanged input"
            ),
            "pin_line": f"cog export {args.release_id}, {content_hash}",
            "record_layout": (
                "per-work JSONL under works/<work_id>.jsonl.gz (gzip mtime=0, deterministic); "
                "one token record per line; the work's CTS URN is the file/work key (see works[].cts_urn); "
                "tokens are ordered by chapter, verse, then sent_id"
            ),
            "token_fields": {
                "id": "UD native token id: an integer word index (head points to it; 0 = root), or a string 'n-m' for a multiword-range (crasis) line",
                "form": "surface form, cog-normalized (see source.encoding_normalization)",
                "lemma": "lemma in PTNK's native convention, verbatim except cog encoding normalization; null on multiword-range lines",
                "pos": "UD UPOS, native (not remapped); null on multiword-range lines",
                "morph": "UD FEATS morphology string, native (not remapped); null where absent",
                "head": "in-sentence id of the governing token (0 = root), scoped by sentence_id; null on multiword-range lines",
                "deprel": "UD dependency relation (incl. subrelations like nmod:poss), native; null on multiword-range lines",
                "locus": "CTS logical passage (chapter.verse) from the token's MISC Ref; combine with works[].cts_urn",
                "sentence_id": "PTNK native sent_id (the annotation unit), e.g. 'Septuagint-Genesis-31:1-grc'",
                "split": "UD split identity: 'train' | 'dev' | 'test'. Authoritative per source file; preserved so a consumer can hold out test and filter train",
                "analysis": "'manual' for all PTNK tokens (manually annotated treebank; see source.annotation_method)",
                "provenance_tag": "'ptnk' for all tokens",
                "parallel_id": "PTNK native parallel_id linking the sentence to the parallel Ancient Hebrew treebank verse (e.g. 'bible/gen-31-1')",
            },
            "counts": {
                "works_exported": len(works),
                "tokens": totals["tokens"],
                "words": totals["words"],
                "multiword_ranges": totals["multiword_ranges"],
                "sentences": totals["sentences"],
                "tokens_missing_locus": totals["missing_locus"],
                "split_tokens": split_tokens,
                "split_sentences": split_sents,
            },
        },
        "source": {
            "name": "UD_Ancient_Greek-PTNK",
            "ud_version": "UD (manual native; MISC Ref present, i.e. >= v2.17)",
            "github": "https://github.com/UniversalDependencies/UD_Ancient_Greek-PTNK",
            "commit": UPSTREAM_COMMIT,
            "retained_clone": "~/Documents/ud_ptnk",
            "license_upstream": "CC BY-SA 4.0 (LICENSE.txt and upstream machine-readable metadata; whole treebank, single license)",
            "text_base": (
                "Septuagint (Genesis, Ruth) per the Codex Alexandrinus; text extracted from "
                "https://greekdoc.github.io. Works are keyed by their greekLit CTS work URN "
                "(Genesis = urn:cts:greekLit:tlg0527.tlg001, Ruth = urn:cts:greekLit:tlg0527.tlg010); "
                "no registered CTS edition exists for the greekdoc Codex Alexandrinus witness, so the "
                "work-level URN is the key and the witness is recorded here."
            ),
            "annotation_method": (
                "Manually annotated treebank. Morphology is John Barach's manual annotation; syntax was "
                "initialized by word-aligning and projecting relations from the parallel Ancient Hebrew "
                "treebank, then manually corrected (Swanson, Bussert & Tyers, LREC-COLING 2024, "
                "aclanthology.org/2024.lrec-main.1145). The upstream metadata marks Lemmas, UPOS, "
                "Features, and Relations all 'manual native', so every token is analysis='manual'."
            ),
            "provenance_note": (
                "provenance_tag='ptnk' for all tokens. Independent manual gold under docs/source-policy.md: "
                "NOT PROIEL data (tier-1) and NOT the output of a PROIEL-trained model (tier-2) - the syntax "
                "is projected from the Ancient Hebrew treebank, not PROIEL - so it is tier-3 (non-PROIEL) and "
                "is NOT Gorman-derived. No tokens are tagged provenance=gorman or proiel-*."
            ),
            "lemma_convention": (
                "Preserved verbatim (cog does not normalize lemma conventions). PTNK lemmas use standard "
                "dictionary headwords (capitalized proper nouns, e.g. 'Ἰακώβ'). Only cog encoding "
                "normalization (NFC, apostrophe, sigma) is applied to the lemma string."
            ),
            "split_note": (
                "The UD train/dev/test split is preserved per token as `split`, authoritative per source "
                "file (grc_ptnk-ud-{train,dev,test}.conllu). Genesis spans all three splits (dev = ch 1-18, "
                "test = ch 19-30, train = ch 31-50); Ruth is entirely train. Because a work spans splits, "
                "the split is a per-token field, not a per-work choice."
            ),
            "sentence_id_note": (
                "PTNK provides an explicit per-sentence identifier (# sent_id); it is used verbatim as "
                "sentence_id. A sentence corresponds to one Septuagint verse or a small verse range."
            ),
            "encoding_normalization": {
                "unicode": "NFC",
                "apostrophes_to_U+2019": ["U+02BC", "U+0027", "U+2018", "U+2019"],
                "sigma": "lunate ϲ/Ϲ -> σ/Σ; final ς word-finally, medial σ otherwise (applied to form and lemma)",
            },
            "citation": (
                "Daniel G. Swanson, Bryce D. Bussert, and Francis Tyers. 2024. Producing a Parallel "
                "Universal Dependencies Treebank of Ancient Hebrew and Ancient Greek via Cross-Lingual "
                "Projection. LREC-COLING 2024, 13074-13078. https://aclanthology.org/2024.lrec-main.1145"
            ),
        },
        "policy": {
            "nc_ban": "docs/source-policy.md: any NonCommercial licence is banned in every role.",
            "license_verdict": "CC BY-SA 4.0 - openly licensed, no NonCommercial clause; ingested in full.",
            "proiel_tier": "tier-3 (non-PROIEL): not PROIEL data and not PROIEL-model output.",
            "gorman": "not Gorman-derived; no provenance=gorman tokens.",
        },
        "consumers": (
            "This is annotation-consumption queue item 1b (docs/annotation-export-contract.md). "
            "dilemma pins this export by export.pin_line, holds out split='test' as eval, and "
            "ingests filtered split='train'."
        ),
        "works": [dict(w) for w in sorted(works, key=lambda x: x["work_id"])],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")

    # The git-tracked pointer stub, written next to the (gitignored) release dir.
    stub_path = out_dir.parent / f"{args.release_id}.json"
    with open(stub_path, "w", encoding="utf-8") as fh:
        json.dump(make_pointer_stub(manifest, args.hf_repo), fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"[ptnk-export] pointer stub -> {stub_path}", flush=True)

    print(f"[ptnk-export] wrote {len(works)} works, {totals['tokens']:,} tokens to {out_dir}", flush=True)
    print(f"[ptnk-export] split tokens: {split_tokens}", flush=True)
    if totals["missing_locus"]:
        print(f"[ptnk-export] WARNING: {totals['missing_locus']} tokens had no CTS locus", flush=True)
    print(f"[ptnk-export] pin line: cog export {args.release_id}, {content_hash}", flush=True)


if __name__ == "__main__":
    main()
