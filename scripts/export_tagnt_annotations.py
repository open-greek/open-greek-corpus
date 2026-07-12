#!/usr/bin/env python3
"""Export STEPBible TAGNT as cog's standardized annotation export (queue item 1d).

TAGNT (Translators Amalgamated Greek New Testament, www.STEPBible.org, Tyndale
House Cambridge) is the Greek New Testament amalgamated across the major editions
(NA27/NA28, TR, SBL, WH, Treg, Byz, Tyn=THGNT), word by word, with per-word
edition flags, positional and meaning variants, disambiguated-Strongs lexical
tags, and Robinson (Tauber) morphology. This produces the annotation export
defined by docs/annotation-export-contract.md: per-work (per NT book),
CTS-URN-keyed streams of token records, with cog-owned encoding normalization and
source-native tagsets/lemmas preserved verbatim. dilemma and other consumers pin
this by "cog export <release_id>, hash <content_hash>".

Input (the retained STEPBible-Data clone, default ~/Documents/STEPBible-Data):
  Translators Amalgamated OT+NT/
    TAGNT Mat-Jhn ... .txt   (Matthew..John)
    TAGNT Act-Rev ... .txt   (Acts..Revelation)
  Each data row is one amalgamated word:
    <Book.Ch.Vs>#<n>=<WordType> \t <Greek (translit)> \t <English> \t
      <dStrong>=<Robinson-morph> \t <TBESG-lemma>=<gloss> \t <editions> \t
      <meaning variants> \t <spelling variants> \t <Spanish> \t <sub-meaning> \t
      <conjoin> \t <sStrong+instance> \t <alt Strongs> \t <variant note>
  The '#'-prefixed lines between the word blocks are TAGNT's continuous
  running-text summary of the verse; this exporter never reads them (see the
  NA27/28 copyright note below). Only the per-word data rows are exported.

What each token record carries (docs/annotation-export-contract.md schema plus
TAGNT-native fields; the edition/variant layer is TAGNT's distinctive value over
any single edition):
  form / lemma / pos / morph   surface form; TBESG dictionary form (lemma) kept
                               VERBATIM in TAGNT's convention; Robinson morphology
                               kept in its NATIVE tagset, not remapped (pos is the
                               native category prefix of the Robinson code).
  dstrong / sstrong /          disambiguated Strongs, simple Strongs+instance, and
  alt_strongs / gloss          alternate Strongs; TBESG brief gloss.
  word_type                    TAGNT's manuscript-tradition presence code (NKO,
                               N(k)O, K, O, ...), verbatim.
  editions                     the edition FLAGS: which editions carry this word,
                               verbatim tokens (may carry a THGNT-style word-order
                               displacement suffix, e.g. 'TR»1'/'Byz«3', and extra
                               witnesses such as KJV, manuscript sigla, versions).
  meaning_variants /           the alternate readings: each with its own form,
  spelling_variants            translit, gloss, Strongs+morph, and the editions
                               that carry it (meaning), or per-edition spellings.
  variant_note                 TAGNT's significant-variant note (^ extra text / v
                               variant reading), text only.
  locus                        the CTS logical passage of the word within the book:
                               "chapter.verse.word" (NRSV versification). When the
                               reference carries a bracketed alternate versification
                               (KJV [ ], NA ( ), other { }) it is kept in
                               alt_versification, never in the locus.
  analysis                     "manual" for every token: TAGNT is human-tagged
                               (Tyndale scholars over Tauber morphology + TBESG).
  provenance_tag               "tagnt".

NA27/28 copyright (docs/source-policy.md; the export shape honors it): the NA27
and NA28 readings are a copyright-flagged (DBG) reconstruction. This export emits
per-word tokens with NA27/NA28 as edition FLAGS only; it never emits or
reconstructs a continuous NA27/28 running text. The other editions carried
(Tyn/SBL/WH/Treg/TR/Byz) are themselves openly licensed. Structurally: only the
discrete per-word rows are read, never TAGNT's '#'-prefixed running-text lines,
and tokens are written as independent records, not as a rebuilt continuous text.

Licensing (docs/source-policy.md): STEPBible-Data is CC BY 4.0 (verified in the
repository README and in each TAGNT file header); no NonCommercial clause, so it
is ingested. Attribution is recorded as "STEP Bible" -> https://www.STEPBible.org.

cog owns encoding normalization (NFC; apostrophes -> U+2019; standard final/medial
sigma), applied to Greek form/lemma strings. cog does NOT normalize the lemma
convention (TBESG multi-form headwords like "Δαυείδ, Δαυίδ, Δαβίδ" and Koine
headword choices are preserved) nor the Robinson morphology.

The export is deterministic: gzip is written with mtime=0 and the content hash is
computed over the uncompressed per-work payloads, so re-running on unchanged input
reproduces byte-identical files and the same content_hash.

Storage (docs/annotation-export-contract.md, "Storage"): the payload this writes
is NOT committed to git. It is uploaded to the Hugging Face dataset repo with
scripts/upload_annotation_export.py; git tracks this exporter plus the pointer
stub written next to the release dir (data/annotations/tagnt/<release_id>.json).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import gzip
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

# The HF dataset repo that holds export payloads (docs/annotation-export-contract.md,
# "Storage"); the release id is the path in the repo. upload_annotation_export.py
# shares this default.
HF_EXPORTS_REPO = "ciscoriordan/open-greek-corpus-annotation-exports"

# STEPBible upstream pin (docs/pinning-discipline.md: git SHA + retained clone).
UPSTREAM = {
    "name": "STEPBible TAGNT (Translators Amalgamated Greek New Testament)",
    "publisher": "STEP Bible / Tyndale House Cambridge",
    "attribution": 'STEP Bible -> https://www.STEPBible.org',
    "github": "https://github.com/STEPBible/STEPBible-Data",
    "git_commit": "b86d26cdb1f51729e73b5b4eb7f7ccadc5dfba39",
    "commit_date": "2026-06-09",
    "license_upstream": "CC BY 4.0",
    "retained_clone": "~/Documents/STEPBible-Data",
}

# New Testament book abbreviation -> TLG work number (tlg0031 is the NT textgroup;
# .tlg001..tlg027 are the 27 books in canonical order, matching cog's existing
# tlg0031.tlgNNN convention, e.g. data/oga_dating.json). TAGNT is a distinct
# amalgamated edition, so it takes its own CTS edition id (stepbible-grc1).
NT_WORK_NUM = {
    "Mat": "001", "Mrk": "002", "Luk": "003", "Jhn": "004", "Act": "005",
    "Rom": "006", "1Co": "007", "2Co": "008", "Gal": "009", "Eph": "010",
    "Php": "011", "Col": "012", "1Th": "013", "2Th": "014", "1Ti": "015",
    "2Ti": "016", "Tit": "017", "Phm": "018", "Heb": "019", "Jas": "020",
    "1Pe": "021", "2Pe": "022", "1Jn": "023", "2Jn": "024", "3Jn": "025",
    "Jud": "026", "Rev": "027",
}
EDITION_ID = "stepbible-grc1"

BOOK_TITLE = {
    "Mat": "Matthew", "Mrk": "Mark", "Luk": "Luke", "Jhn": "John", "Act": "Acts",
    "Rom": "Romans", "1Co": "1 Corinthians", "2Co": "2 Corinthians",
    "Gal": "Galatians", "Eph": "Ephesians", "Php": "Philippians",
    "Col": "Colossians", "1Th": "1 Thessalonians", "2Th": "2 Thessalonians",
    "1Ti": "1 Timothy", "2Ti": "2 Timothy", "Tit": "Titus", "Phm": "Philemon",
    "Heb": "Hebrews", "Jas": "James", "1Pe": "1 Peter", "2Pe": "2 Peter",
    "1Jn": "1 John", "2Jn": "2 John", "3Jn": "3 John", "Jud": "Jude",
    "Rev": "Revelation",
}


def work_id_for(book: str) -> str:
    return f"tlg0031.tlg{NT_WORK_NUM[book]}.{EDITION_ID}"


def work_cts_urn(book: str) -> str:
    return f"urn:cts:greekLit:{work_id_for(book)}"


# --- cog-owned encoding normalization (identical policy to the OGA exporter) ---

# Apostrophe characters unified to U+2019 (right single quotation mark). Kept
# conservative: only true apostrophe/elision marks, applied to Greek form/lemma
# strings, not to incidental text fields.
_APOSTROPHES = {"ʼ", "'", "‘", "’"}
_APOS_TABLE = {ord(c): "’" for c in _APOSTROPHES}


# Canonical sigma normalization is shared across all exporters (see
# scripts/annotation_encoding.py). Import it so every exporter stays in sync.
from annotation_encoding import normalize_sigma as _normalize_sigma


def norm_form(text):
    """Full cog encoding normalization for a Greek surface/lemma/variant form."""
    if text is None:
        return None
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_APOS_TABLE)
    text = _normalize_sigma(text)
    return unicodedata.normalize("NFC", text)


def nfc(text):
    """NFC only, for incidental text fields (translit, gloss, notes)."""
    if text is None:
        return None
    return unicodedata.normalize("NFC", text)


# --- TAGNT row parsing ----------------------------------------------------

# A data row: Book.Ch.Vs#<n>=<WordType> \t ... ; the running-text summary lines
# ('# Ref ...', '#_Translation', '#_Word=Grammar') never match (they lack '#<n>=').
_ROW_RE = re.compile(
    r"^(?P<book>[A-Za-z0-9]+)\.(?P<ch>\d+)\.(?P<vs>[^#\t]+)#(?P<wn>\d+)=(?P<wtype>\S+)$"
)
_LEAD_INT = re.compile(r"^(\d+)")

# One meaning-variant unit: "<form> (<marker>=<translit>) <gloss> - <tags> in: <eds>"
_MV_UNIT = re.compile(r"^(?P<form>.+?) \((?P<marker>[A-Za-z])=(?P<translit>[^)]*)\) (?P<mid>.*)$")
_MV_TAGS = re.compile(
    r"^(?P<gloss>.*) - (?P<tags>[GH]\d+[A-Za-z]?=\S+(?: \+ [GH]\d+[A-Za-z]?=\S+)*)$"
)
_ITALIC_RE = re.compile(r"</?i>")


def split_field(value, sep="="):
    """Split 'A=B' into (A, B) on the FIRST sep; ('', None) handling for blanks."""
    value = value.strip()
    if not value:
        return None, None
    if sep in value:
        a, b = value.split(sep, 1)
        return a.strip(), b.strip()
    return value, None


def parse_meaning_variants(cell):
    """Parse the meaning-variants cell into structured alternate readings."""
    cell = cell.strip()
    if not cell:
        return []
    out = []
    for unit in cell.split(" ¦ "):  # U+00A6 broken bar separates variants
        unit = unit.strip()
        if not unit:
            continue
        left, sep, eds = unit.rpartition(" in: ")
        m = _MV_UNIT.match(left if sep else unit)
        if not m:
            out.append({"raw": nfc(unit)})
            continue
        mid = m.group("mid")
        tm = _MV_TAGS.match(mid)
        if tm:
            gloss = tm.group("gloss").strip()
            tags = [{"dstrong": t.split("=", 1)[0], "morph": t.split("=", 1)[1]}
                    for t in tm.group("tags").split(" + ")]
        else:
            gloss, tags = mid.strip(), []
        out.append({
            "form": norm_form(m.group("form")),
            "marker": m.group("marker"),
            "translit": m.group("translit"),
            "gloss": gloss or None,
            "tags": tags,
            "editions": [e for e in eds.split("+") if e] if sep else [],
        })
    return out


def parse_spelling_variants(cell):
    """Parse the spelling-variants cell into per-edition alternate spellings."""
    cell = cell.strip()
    if not cell:
        return []
    out = []
    for chunk in cell.split(";"):
        chunk = chunk.strip()
        if not chunk or ":" not in chunk:
            continue
        eds, form = chunk.split(":", 1)
        eds = [e for e in eds.strip().lstrip("+").split("+") if e]
        out.append({"editions": eds, "form": norm_form(form.strip())})
    return out


def parse_greek_translit(cell):
    """'Βίβλος (Biblos)' -> ('Βίβλος', 'Biblos'); tolerant of a missing translit."""
    cell = cell.strip()
    m = re.match(r"^(?P<g>.*?)\s*\((?P<t>[^()]*)\)\s*$", cell)
    if m:
        return norm_form(m.group("g")), m.group("t") or None
    return norm_form(cell), None


def parse_row(cols):
    """Build a token record from a 14+-column data row, or None if not a data row."""
    m = _ROW_RE.match(cols[0])
    if not m:
        return None
    book = m.group("book")
    if book not in NT_WORK_NUM:
        return None
    ch = m.group("ch")
    vs_raw = m.group("vs").strip()
    vm = _LEAD_INT.match(vs_raw)
    if not vm:
        return None
    verse = vm.group(1)
    alt_versification = vs_raw[vm.end():].strip() or None
    word_num = int(m.group("wn"))

    def col(i):
        return cols[i] if i < len(cols) else ""

    form, translit = parse_greek_translit(col(1))
    # TAGNT marks a paragraph break (per THGNT) with a trailing pilcrow on the last
    # word of the paragraph; it is not part of the Greek surface, so lift it into a
    # flag and keep the form clean.
    paragraph_break = form is not None and "¶" in form
    if paragraph_break:
        form = form.replace("¶", "").rstrip()
    dstrong, morph = split_field(col(3))
    lemma, gloss = split_field(col(4))
    pos = morph.split("-", 1)[0] if morph else None
    editions = [e for e in col(5).split("+") if e.strip()]
    alt_strongs = [a for a in re.split(r"[\s,]+", col(12).strip()) if a]
    variant_note = col(13).strip()
    variant_note = nfc(_ITALIC_RE.sub("", variant_note)).strip() or None if variant_note else None

    return {
        "book": book,
        "record": {
            "word_num": word_num,
            "form": form,
            "translit": translit,
            "lemma": norm_form(lemma) if lemma else None,
            "pos": pos,
            "morph": morph,
            "dstrong": dstrong,
            "sstrong": col(11).strip() or None,
            "alt_strongs": alt_strongs,
            "gloss": nfc(gloss) if gloss else None,
            "word_type": m.group("wtype"),
            "editions": editions,
            "meaning_variants": parse_meaning_variants(col(6)),
            "spelling_variants": parse_spelling_variants(col(7)),
            "variant_note": variant_note,
            "paragraph_break": paragraph_break,
            "locus": f"{ch}.{verse}.{word_num}",
            "alt_versification": alt_versification,
            "sentence_id": None,
            "analysis": "manual",
            "provenance_tag": "tagnt",
        },
    }


RECORD_FIELD_ORDER = [
    "word_num", "form", "translit", "lemma", "pos", "morph",
    "dstrong", "sstrong", "alt_strongs", "gloss",
    "word_type", "editions", "meaning_variants", "spelling_variants",
    "variant_note", "paragraph_break", "locus", "alt_versification",
    "sentence_id", "analysis", "provenance_tag",
]


def iter_data_rows(path):
    """Yield (book, record) for every per-word data row in a TAGNT file."""
    with open(path, encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or "#" not in line.split("\t", 1)[0]:
                continue
            cols = line.split("\t")
            parsed = parse_row(cols)
            if parsed is not None:
                yield parsed["book"], parsed["record"]


def export_book(records, book, out_path):
    """Write one book's JSONL.gz (deterministic) and return per-work stats."""
    buf = io.StringIO()
    n_tokens = n_mv = n_sv = 0
    for rec in records:
        if rec["meaning_variants"]:
            n_mv += 1
        if rec["spelling_variants"]:
            n_sv += 1
        buf.write(json.dumps({k: rec[k] for k in RECORD_FIELD_ORDER}, ensure_ascii=False))
        buf.write("\n")
        n_tokens += 1
    payload = buf.getvalue().encode("utf-8")
    sha = hashlib.sha256(payload).hexdigest()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
            gz.write(payload)
    return {
        "work_id": work_id_for(book),
        "cts_urn": work_cts_urn(book),
        "book": book,
        "title": BOOK_TITLE[book],
        "file": out_path.name,
        "tokens": n_tokens,
        "tokens_with_meaning_variants": n_mv,
        "tokens_with_spelling_variants": n_sv,
        "sha256": sha,
    }


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return {"sha256": h.hexdigest(), "bytes": os.path.getsize(path)}


def find_tagnt_files(step_root: Path):
    d = step_root / "Translators Amalgamated OT+NT"
    files = sorted(glob.glob(str(d / "TAGNT *.txt")))
    if not files:
        sys.exit(f"no 'TAGNT *.txt' files under {d}")
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--step-root",
                    default=os.environ.get("STEPBIBLE_ROOT", os.path.expanduser("~/Documents/STEPBible-Data")),
                    help="retained STEPBible-Data clone (default $STEPBIBLE_ROOT or ~/Documents/STEPBible-Data)")
    ap.add_argument("--out-dir", default=None,
                    help="output release dir (default <repo>/data/annotations/tagnt/<release_id>)")
    ap.add_argument("--release-id", default="tagnt-v1", help="cog export release id (default tagnt-v1)")
    ap.add_argument("--books", nargs="*", default=None, help="export only these book abbreviations (smoke test)")
    ap.add_argument("--hf-repo", default=HF_EXPORTS_REPO,
                    help="HF dataset repo the pointer stub records as the payload home")
    args = ap.parse_args()

    step_root = Path(args.step_root)
    repo_root = Path(__file__).resolve().parent.parent
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "data" / "annotations" / "tagnt" / args.release_id

    files = find_tagnt_files(step_root)
    print(f"[tagnt-export] input files: {[os.path.basename(f) for f in files]}", flush=True)

    # License guard: every TAGNT file must self-declare CC BY. Do not ship if not.
    for f in files:
        with open(f, encoding="utf-8-sig") as fh:
            header = fh.read(4096)
        if "CC BY" not in header:
            sys.exit(f"[tagnt-export] ABORT: '{os.path.basename(f)}' header does not declare CC BY licensing")

    # Read all rows, grouped by book in canonical (file) order.
    from collections import OrderedDict
    by_book = OrderedDict()
    input_artifacts = {}
    for f in files:
        input_artifacts[os.path.basename(f)] = sha256_file(f)
        for book, rec in iter_data_rows(f):
            by_book.setdefault(book, []).append(rec)

    wanted = set(args.books) if args.books else None
    works = []
    total_tokens = total_mv = total_sv = 0
    for book in NT_WORK_NUM:  # canonical order
        if book not in by_book:
            continue
        if wanted and book not in wanted:
            continue
        out_path = out_dir / "works" / f"{work_id_for(book)}.jsonl.gz"
        stats = export_book(by_book[book], book, out_path)
        works.append(stats)
        total_tokens += stats["tokens"]
        total_mv += stats["tokens_with_meaning_variants"]
        total_sv += stats["tokens_with_spelling_variants"]
        print(f"[tagnt-export] {book} ({stats['work_id']}): {stats['tokens']:,} tokens", flush=True)

    # Deterministic content hash over the uncompressed per-work payloads.
    hasher = hashlib.sha256()
    for w in sorted(works, key=lambda x: x["work_id"]):
        hasher.update(f"{w['work_id']}:{w['sha256']}\n".encode("utf-8"))
    content_hash = "sha256:" + hasher.hexdigest()

    manifest = {
        "export": {
            "release_id": args.release_id,
            "contract": "docs/annotation-export-contract.md",
            "generated_by": "scripts/export_tagnt_annotations.py",
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content_hash": content_hash,
            "content_hash_method": (
                "sha256 over the newline-joined '<work_id>:<sha256-of-uncompressed-jsonl>' lines, "
                "work_id-sorted; excludes generated_at and gzip framing so it is reproducible on unchanged input"
            ),
            "pin_line": f"cog export {args.release_id}, {content_hash}",
            "record_layout": (
                "per-work JSONL under works/<work_id>.jsonl.gz (gzip mtime=0, deterministic); "
                "one token record per line; one work per NT book; the work's CTS URN is the file/work "
                "key (see works[].cts_urn)"
            ),
            "token_fields": {
                "word_num": "TAGNT native 1-based word index within the verse",
                "form": "surface Greek form, cog-normalized (may carry attached THGNT punctuation)",
                "translit": "TAGNT transliteration of the form (Latin), NFC only",
                "lemma": "TBESG dictionary form (lemma), TAGNT convention preserved verbatim (multi-form "
                          "headwords kept, e.g. 'Δαυείδ, Δαυίδ, Δαβίδ'); only cog encoding normalization applied",
                "pos": "native category prefix of the Robinson morph code (e.g. N, V, A, CONJ); not remapped",
                "morph": "Robinson (Tauber) morphology code in TAGNT's native tagset; not remapped",
                "dstrong": "disambiguated Strongs (STEPBible dStrong, LSJ-linked), verbatim",
                "sstrong": "simple Strongs + in-verse instance suffix (e.g. G5207_A; lowercase = may be absent "
                           "from some tagged Bibles), verbatim",
                "alt_strongs": "alternate Strongs tags for the same word, verbatim",
                "gloss": "TBESG brief English gloss",
                "word_type": "TAGNT manuscript-tradition presence code (NKO, N(k)O, K, O, ...), verbatim",
                "editions": "edition FLAGS carrying this word, verbatim tokens; may carry a THGNT-style word-order "
                            "displacement suffix (»N forward / «N back) and non-edition witnesses (KJV, manuscript "
                            "sigla, versions). NA27/NA28 appear here as flags only (see na_copyright)",
                "meaning_variants": "alternate readings that affect translation; each has form, marker (t/o/T/O), "
                                    "translit, gloss, tags (Strongs+morph), and the editions carrying it",
                "spelling_variants": "per-edition alternate spellings (do not affect translation); each has editions + form",
                "variant_note": "TAGNT significant-variant note (^ extra text / v variant reading), text only",
                "paragraph_break": "true when TAGNT marks a paragraph break (THGNT) at this word; the pilcrow is "
                                   "lifted out of the surface form into this flag",
                "locus": "CTS logical passage of the word within the book: 'chapter.verse.word' (NRSV versification); "
                         "combine with works[].cts_urn",
                "alt_versification": "bracketed alternate versification of the verse when present (KJV [ ], NA ( ), "
                                     "other { }); kept out of the locus",
                "sentence_id": "null: TAGNT has no sentence segmentation (the word within the verse is the unit)",
                "analysis": "'manual' for all tokens (see source.annotation_method)",
                "provenance_tag": "'tagnt' for all tokens",
            },
            "counts": {
                "works_exported": len(works),
                "tokens": total_tokens,
                "tokens_with_meaning_variants": total_mv,
                "tokens_with_spelling_variants": total_sv,
            },
        },
        "source": {
            "name": UPSTREAM["name"],
            "publisher": UPSTREAM["publisher"],
            "attribution": UPSTREAM["attribution"],
            "github": UPSTREAM["github"],
            "git_commit": UPSTREAM["git_commit"],
            "commit_date": UPSTREAM["commit_date"],
            "retained_clone": UPSTREAM["retained_clone"],
            "pin_note": (
                "docs/pinning-discipline.md: git sources are pinned by commit SHA plus a retained local clone "
                "(the SHA pins bytes, the clone pins availability). There is no DOI for STEPBible-Data."
            ),
            "input_artifacts": input_artifacts,
            "license_upstream": UPSTREAM["license_upstream"],
            "annotation_method": (
                "Human-tagged: Robinson morphology (from James Tauber) with manual additions/corrections by "
                "Tyndale House scholars, disambiguated Strongs (dStrong) and TBESG lemmas curated by hand, and "
                "per-word edition/variant collation. Every token is analysis='manual'."
            ),
            "provenance_note": (
                "provenance_tag='tagnt' for all tokens. TAGNT is an independent scholarly amalgamation; it is not "
                "PROIEL data, not the output of a PROIEL-trained model, and not Gorman-derived, so no tokens are "
                "tagged provenance=gorman or proiel-* (docs/source-policy.md)."
            ),
            "lemma_convention": (
                "Preserved verbatim (cog does not normalize lemma conventions). TAGNT lemmas are TBESG dictionary "
                "headwords and may list several spellings for one headword (e.g. 'Δαυείδ, Δαυίδ, Δαβίδ'); only cog "
                "encoding normalization (NFC, apostrophe, sigma) is applied to the lemma string."
            ),
            "morph_convention": (
                "Robinson (Tauber) morphology codes, preserved verbatim in TAGNT's native tagset; not remapped to any "
                "common scheme. 'pos' is the native category prefix of the code, split out for convenience."
            ),
            "sentence_id_note": (
                "TAGNT provides no sentence segmentation; the annotation unit is the word within the verse, so "
                "sentence_id is null for every token."
            ),
            "encoding_normalization": {
                "unicode": "NFC",
                "apostrophes_to_U+2019": ["U+02BC", "U+0027", "U+2018", "U+2019"],
                "sigma": "lunate ϲ/Ϲ -> σ/Σ; final ς word-finally, medial σ otherwise (applied to Greek form and lemma)",
                "scope": "full form normalization on form/lemma and variant forms; NFC only on translit/gloss/notes",
            },
            "citation": (
                "STEP Bible (Tyndale House Cambridge). Translators Amalgamated Greek New Testament (TAGNT). "
                "CC BY 4.0. https://www.STEPBible.org ; https://github.com/STEPBible/STEPBible-Data"
            ),
        },
        "policy": {
            "license_verdict": (
                "CC BY 4.0 (verified in the repository README and each TAGNT file header): openly licensed, no "
                "NonCommercial clause, so ingested and re-exported under docs/source-policy.md."
            ),
            "na_copyright": (
                "The NA27/NA28 reading is a copyright-flagged (DBG) reconstruction. This export emits per-word tokens "
                "with NA27/NA28 as edition FLAGS only in the 'editions' field; it does NOT emit or reconstruct a "
                "continuous NA27/28 running text. Only TAGNT's discrete per-word rows are read (never its "
                "'#'-prefixed running-text lines), and tokens are written as independent records. Tyn/SBL/WH/Treg/"
                "TR/Byz are themselves openly licensed."
            ),
        },
        "consumers": (
            "This is annotation-consumption queue item 1d (docs/annotation-export-contract.md). "
            "Consumers pin this export by export.pin_line."
        ),
        "works": [dict(w) for w in sorted(works, key=lambda x: x["work_id"])],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")

    # The git-tracked pointer stub, written next to the (gitignored) release dir.
    # Skipped for partial smoke tests, whose hash must never overwrite the pin.
    if not args.books:
        stub = {
            "release_id": args.release_id,
            "content_hash": content_hash,
            "pin_line": manifest["export"]["pin_line"],
            "storage": {
                "hf_dataset_repo": args.hf_repo,
                "repo_type": "dataset",
                "path_in_repo": f"{args.release_id}/",
                "url": f"https://huggingface.co/datasets/{args.hf_repo}/tree/main/{args.release_id}",
                "payload": "works/<work_id>.jsonl.gz per exported NT book, plus manifest.json",
                "note": ("docs/annotation-export-contract.md, 'Storage': export payloads live on the Hub; git tracks "
                         "the exporter script and this pointer stub only. Regenerate locally with "
                         "scripts/export_tagnt_annotations.py, publish with scripts/upload_annotation_export.py."),
            },
            "counts": manifest["export"]["counts"],
            "generated_by": manifest["export"]["generated_by"],
            "generated_at": manifest["export"]["generated_at"],
            "contract": "docs/annotation-export-contract.md",
            "attribution": UPSTREAM["attribution"],
            "upstream_pin": {
                "source": UPSTREAM["name"],
                "github": UPSTREAM["github"],
                "git_commit": UPSTREAM["git_commit"],
                "commit_date": UPSTREAM["commit_date"],
                "retained_clone": UPSTREAM["retained_clone"],
                "license_upstream": UPSTREAM["license_upstream"],
                "note": "cog pins the upstream (git SHA + retained clone); consumers pin only pin_line (docs/pinning-discipline.md)",
            },
        }
        stub_path = out_dir.parent / f"{args.release_id}.json"
        with open(stub_path, "w", encoding="utf-8") as fh:
            json.dump(stub, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"[tagnt-export] pointer stub -> {stub_path}", flush=True)

    print(f"[tagnt-export] wrote {len(works)} works, {total_tokens:,} tokens to {out_dir}", flush=True)
    print(f"[tagnt-export] content_hash = {content_hash}", flush=True)
    print(f"[tagnt-export] pin line: cog export {args.release_id}, {content_hash}", flush=True)


if __name__ == "__main__":
    main()
