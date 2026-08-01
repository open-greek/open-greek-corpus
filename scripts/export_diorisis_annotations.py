#!/usr/bin/env python3
"""Export the Diorisis corpus as cog's standardized annotation export (queue item 1e, Diorisis half).

This produces the annotation export defined by docs/annotation-export-contract.md:
per-work, CTS-URN-keyed streams of token records, with cog-owned encoding
normalization and the source-native Diorisis lemma lexicon and morphological
descriptors preserved verbatim. dilemma and other consumers pin this by
"cog export <release_id>, hash <content_hash>".

Source: The Diorisis Ancient Greek Corpus (Vatri & McGillivray 2018), figshare
article 6187256, version 1 (version DOI 10.6084/m9.figshare.6187256.v1; the
concept DOI floats and is never the pin). 820 TEI XML texts, 10,206,421 word
tokens of literary Ancient Greek (Homer to the fifth century CE), sourced from
Perseus canonical-greekLit (752 files), Bibliotheca Augustana (60), and The
Little Sailing (8). The retained copy is ~/Documents/diorisis (Diorisis.zip,
pinned by sha256, plus extracted/); the run aborts if the zip hash drifts from
the pin (docs/pinning-discipline.md).

Annotation shape: lemma plus POS/morphology only; Diorisis has NO dependency
syntax, so token records carry no head/deprel at all (the contract says a
morphology-only source omits them; empty fields are not emitted). Each <word>
carries exactly one <lemma> (the corpus's chosen lemma after disambiguation)
with the Diorisis lexicon id, the headword ('entry'), a coarse POS, and zero or
more <analysis morph="..."> readings from Morpheus. Where several morphological
readings survive, `morph` is the full list, verbatim and in source order
(multiple readings are stored, never arbitrarily collapsed); where the corpus
could not analyze a word (lemma id 'unknown'), lemma/pos/morph are null.

Provenance / policy (docs/source-policy.md):
  - The whole annotation layer is automatic (Morpheus morphological analysis;
    lemma disambiguation by frequency and by a TreeTagger POS tagger where
    needed). Every sentence is analysis='auto', provenance_tag='diorisis'.
    Tier 3 under source-policy.md: non-PROIEL automatic annotation, no PROIEL
    data and no PROIEL-trained models anywhere in the pipeline.
  - Licensing is re-derived from every file's TEI header at run time: a file
    whose <licence> is NonCommercial/NoDerivatives is EXCLUDED, and one that is
    neither NC nor on the open allowlist (creativecommons.org /by/ or /by-sa/,
    any version) is EXCLUDED as unclear; both land in the scope audit. In the
    pinned corpus all 820 files carry CC BY-SA 3.0 US, so both sets are empty,
    but the screen runs every time so a drifted input cannot silently ship.
    The figshare record's aggregate license is CC BY 4.0.

Work identity: every file's TEI header carries tlgAuthor/tlgId, and these are
the Perseus greekLit CTS ids (verified against the header's own Perseus ref
path for the 752 Perseus files; for Euripides this numbering differs from the
TLG-E canon on purpose, e.g. Hecuba is greekLit tlg0006.tlg007, and it is what
glaux-v1 and cog's crosswalk use). Letter-suffixed work ids (Plutarch tlg051a
and friends) are merged into their base CTS work in letter order, exactly like
glaux-v1's letter-suffix merge; several files sharing one work id (Diodorus'
three Bibliotheca Historica volumes, Aristotle's two Oeconomica files) merge
into one work in (work id, filename) order. Every token's `doc` field records
the Diorisis file stem, and (doc, sentence_id) is the unique sentence key.
Files whose header ids do not fit tlgAuthor=NNNN / tlgId=NNN[a-z] would be
excluded and reported in the audit, never guessed (none in the pinned corpus).

Locus: Diorisis cites at SENTENCE granularity: each <sentence> has a location
attribute already composed per the work's own citation scheme (book.chapter.
section for most prose, line numbers for drama, Stephanus pages like '17a',
named parts like 'Proof.4', ...). The locus is that string verbatim, shared by
the sentence's tokens; empty locations stay null (faithfully sparse, 33,745
sentences in the pinned corpus). Standalone <punct> marks are not tokens in
Diorisis (no id, no annotation) and are not exported; per-work counts are kept
in the manifest.

cog owns encoding normalization: Diorisis stores surface forms in Beta Code,
which is converted to Unicode Greek by the audited table below (unknown Beta
Code characters abort the run), then normalized like every other exporter (NFC;
elision apostrophes -> U+2019; standard final/medial sigma). Lemma entries are
already Unicode and get the same normalization. cog does NOT normalize lemma
conventions: Diorisis headwords are preserved verbatim, and the Diorisis
lexicon id (`lemma_id`) carries homograph identity (no trailing digits in the
headwords themselves; 'nlsjNNN' ids mark lemmas outside LSJ).

The export is deterministic: gzip is written with mtime=0, works are emitted in
sorted order, the manifest timestamp is a constant (no wall clock anywhere),
and the content hash is computed over the uncompressed per-work payloads, so
re-running on unchanged input reproduces byte-identical files.

Storage (docs/annotation-export-contract.md, "Storage"): the payload this
writes is NOT committed to git. It is uploaded to the Hugging Face dataset repo
with scripts/upload_annotation_export.py; git tracks this exporter plus the
pointer stub written next to the release dir
(data/annotations/diorisis/<release_id>.json).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Shared cog encoding normalization (NFC + apostrophes -> U+2019 + per-word
# final/medial sigma); one implementation for every exporter so they cannot
# drift (see scripts/annotation_encoding.py).
from annotation_encoding import normalize

# The HF dataset repo that holds export payloads (docs/annotation-export-contract.md,
# "Storage"); the release id is the path in the repo. upload_annotation_export.py
# shares this default.
HF_EXPORTS_REPO = "ciscoriordan/open-greek-corpus-annotation-exports"

# The upstream pin (docs/pinning-discipline.md): the figshare VERSION DOI (the
# concept DOI 10.6084/m9.figshare.6187256 floats to latest and is not a pin)
# plus the exact bytes of the one published file, verified at run time against
# the retained copy.
UPSTREAM_NAME = "The Diorisis Ancient Greek Corpus"
UPSTREAM_ARTICLE = "https://figshare.com/articles/dataset/The_Diorisis_Ancient_Greek_Corpus/6187256"
UPSTREAM_VERSION_DOI = "10.6084/m9.figshare.6187256.v1"
UPSTREAM_DOWNLOAD_URL = "https://ndownloader.figshare.com/files/11296247"
UPSTREAM_ZIP_NAME = "Diorisis.zip"
UPSTREAM_ZIP_BYTES = 194443428
UPSTREAM_ZIP_MD5 = "f3a26efa7e7d2b93d1bcca26900d180a"    # figshare supplied_md5, re-verified locally
UPSTREAM_ZIP_SHA256 = "fb32b7ff4bcfc433f1234aff8134096f524c9a32accbfdf0a072df4a5f019b65"
EXPECTED_FILES = 820

# Determinism: no wall clock anywhere in the output. This constant is the only
# timestamp; bump it deliberately when (and only when) minting a new release.
GENERATED_AT = "2026-07-31T00:00:00Z"

_TLG_AUTHOR_RE = re.compile(r"^\d{4}$")
_TLG_WORK_RE = re.compile(r"^(\d{3})([a-z]?)$")
_PERSEUS_REF_RE = re.compile(r"canonical-greekLit/tree/master/data/tlg(\d{4})/tlg(\d{3}[a-z]?)/")


def _tilde(path):
    """Home-relativize a path (~/...) so published manifests carry no personal
    absolute path (matches the other exporters' retained_clone convention)."""
    p = str(path)
    home = os.path.expanduser("~")
    return "~" + p[len(home):] if p.startswith(home) else p


# --- License classification (run-time, from each file's TEI <licence>) ------

def is_noncommercial(license_target: str) -> bool:
    """True when a licence URL/text carries an NC or ND clause. Same detector
    policy as the OGA and GLAUx exporters."""
    t = (license_target or "").lower()
    return ("by-nc" in t) or ("-nc-" in t) or ("by-nd" in t) or ("-nd-" in t) or ("noncommercial" in t)


# Open allowlist: Creative Commons BY or BY-SA, any version, any jurisdiction
# suffix (the pinned corpus is uniformly /by-sa/3.0/us/). Anything neither NC
# nor allowlisted is excluded as unclear rather than served, matching glaux-v1.
_OPEN_LICENSE_RE = re.compile(r"^https?://creativecommons\.org/licenses/by(-sa)?/[0-9]\.[0-9](/[a-z]+)?/?$")


def license_class(license_target: str) -> str:
    """'open' | 'noncommercial' | 'unclear' for a TEI licence ref target."""
    s = (license_target or "").strip()
    if is_noncommercial(s):
        return "noncommercial"
    if _OPEN_LICENSE_RE.match(s):
        return "open"
    return "unclear"


# --- Beta Code -> Unicode Greek --------------------------------------------

# The complete character inventory of the pinned corpus's form attributes is
# 34 characters: the 25 letters below (no 'j'), 7 diacritics, apostrophe, and
# '*' (capitalization). Anything outside the table aborts the run (report,
# don't guess). 'v' is TLG Beta Code digamma; the pinned corpus uses it both
# genuinely (Dionysius of Halicarnassus' digamma discussion: va/nac) and in a
# handful of upstream typos, all converted faithfully.
BETA_LETTERS = {
    "a": "α", "b": "β", "g": "γ", "d": "δ", "e": "ε", "z": "ζ", "h": "η",
    "q": "θ", "i": "ι", "k": "κ", "l": "λ", "m": "μ", "n": "ν", "c": "ξ",
    "o": "ο", "p": "π", "r": "ρ", "s": "σ", "t": "τ", "u": "υ", "f": "φ",
    "x": "χ", "y": "ψ", "w": "ω", "v": "ϝ",
}
BETA_DIACRITICS = {
    ")": "̓",   # smooth breathing
    "(": "̔",   # rough breathing
    "/": "́",   # acute
    "\\": "̀",  # grave
    "=": "͂",   # circumflex (perispomeni)
    "+": "̈",   # diaeresis
    "|": "ͅ",   # iota subscript (ypogegrammeni)
}


def beta_to_unicode(beta: str, where: str) -> str:
    """Convert one Beta Code token to a Unicode Greek combining sequence.

    '*' capitalizes the next letter; diacritics between '*' and the letter
    (Beta Code writes capitals' breathings first: *)a = smooth-breathing alpha)
    are re-attached AFTER the letter so the combining sequence is well formed.
    Diacritics keep their source order otherwise (breathing before accent, as
    Beta Code writes them), which is the canonical order NFC expects. The
    apostrophe (elision) passes through for normalize() to unify to U+2019.
    Final/medial sigma is enforced afterward by normalize(); the source never
    marks it (no digits occur in any form).
    """
    out = []
    caps = False
    stash = ""  # diacritics seen between '*' and its letter
    for ch in beta:
        if ch == "*":
            caps = True
            stash = ""
        elif ch in BETA_DIACRITICS:
            if caps:
                stash += BETA_DIACRITICS[ch]
            else:
                out.append(BETA_DIACRITICS[ch])
        elif ch in BETA_LETTERS:
            if caps:
                out.append(BETA_LETTERS[ch].upper())
                out.append(stash)
                caps = False
                stash = ""
            else:
                out.append(BETA_LETTERS[ch])
        elif ch == "'":
            out.append(ch)
        else:
            sys.exit(f"[diorisis-export] ABORT: unknown Beta Code character {ch!r} "
                     f"in form {beta!r} ({where}); extend BETA_LETTERS/BETA_DIACRITICS deliberately")
    if caps:  # trailing bare '*' (does not occur in the pinned corpus)
        out.append(stash)
    return "".join(out)


def convert_form(beta: str, where: str) -> str:
    """Beta Code -> Unicode, then the shared cog normalization (NFC,
    apostrophes -> U+2019, final/medial sigma)."""
    return normalize(beta_to_unicode(beta, where))


# --- Token record ----------------------------------------------------------

# head/deprel are deliberately absent: Diorisis has no dependency syntax, and
# the contract omits the fields entirely for a morphology-only source.
TOKEN_FIELD_ORDER = [
    "id", "form", "lemma", "lemma_id", "pos", "morph",
    "locus", "sentence_id", "doc",
    "analysis", "provenance_tag",
    "treetagger", "disambiguated", "isquote", "lacuna",
]

_FLAG_VALUES = {None, "true"}


def build_token_record(w, lm, analyses, locus, sentence_id: int, doc: str, where: str):
    form = w.get("form")
    if not form:
        sys.exit(f"[diorisis-export] ABORT: word without form ({where})")
    isquote = w.get("isquote")
    lacuna = w.get("lacuna")
    if isquote not in _FLAG_VALUES or lacuna not in _FLAG_VALUES:
        sys.exit(f"[diorisis-export] ABORT: unexpected isquote={isquote!r} / lacuna={lacuna!r} ({where})")
    tt = lm.get("TreeTagger")
    if tt not in ("true", "false"):
        sys.exit(f"[diorisis-export] ABORT: unexpected TreeTagger={tt!r} ({where})")
    entry = lm.get("entry")
    return {
        "id": int(w.get("id")),
        "form": convert_form(form, where),
        "lemma": normalize(entry) if entry is not None else None,
        "lemma_id": lm.get("id"),
        "pos": lm.get("POS"),
        "morph": analyses if analyses else None,
        "locus": locus,
        "sentence_id": sentence_id,
        "doc": doc,
        "analysis": "auto",
        "provenance_tag": "diorisis",
        "treetagger": tt == "true",
        "disambiguated": lm.get("disambiguated"),
        "isquote": True if isquote == "true" else None,
        "lacuna": True if lacuna == "true" else None,
    }


# --- Per-file parsing -------------------------------------------------------

class DiorisisFile:
    """One Diorisis TEI XML file: header identity plus the sentence stream.

    Only the teiHeader is parsed and held up front (the classification pass
    touches all 820 files); the sentence stream is re-read with iterparse at
    write time, one file at a time, so the whole corpus is never in memory.
    """

    def __init__(self, path: Path):
        self.path = path
        self.stem = path.stem  # the native document id, e.g. "Plutarch (0007) - Agis (051a)"
        header = None
        for i, (ev, el) in enumerate(ET.iterparse(str(path), events=("start", "end"))):
            if i == 0:
                if not (ev == "start" and el.tag == "TEI.2"):
                    sys.exit(f"[diorisis-export] ABORT: {self.stem}: root tag {el.tag!r}, expected TEI.2")
            elif ev == "end" and el.tag == "teiHeader":
                header = el
                break
        if header is None:
            sys.exit(f"[diorisis-export] ABORT: {self.stem}: no teiHeader")
        ts = header.find("fileDesc/titleStmt")
        self.title = (ts.findtext("title") or "").strip()
        self.author = (ts.findtext("author") or "").strip()
        self.tlg_author = (ts.findtext("tlgAuthor") or "").strip()
        self.tlg_work = (ts.findtext("tlgId") or "").strip()
        src_ref = header.find("fileDesc/sourceDesc/ref")
        self.source_ref = src_ref.get("target") if src_ref is not None else None
        self.source_name = (src_ref.text or "").strip() if src_ref is not None else None
        lic = header.find("fileDesc/publicationStmt/licence/ref")
        self.license_target = lic.get("target") if lic is not None else None
        self.genre = (header.findtext("xenoData/genre") or "").strip() or None
        self.subgenre = (header.findtext("xenoData/subgenre") or "").strip() or None
        self.creation_date = (header.findtext("profileDesc/creation/date") or "").strip() or None

    def id_ok(self) -> bool:
        return bool(_TLG_AUTHOR_RE.match(self.tlg_author) and _TLG_WORK_RE.match(self.tlg_work))

    def work_key(self) -> str:
        m = _TLG_WORK_RE.match(self.tlg_work)
        return f"tlg{self.tlg_author}.tlg{m.group(1)}"

    def check_perseus_ref(self):
        """Perseus-sourced files embed their greekLit path in the source ref;
        the header ids must match it. Returns True when the check applied."""
        m = _PERSEUS_REF_RE.search(self.source_ref or "")
        if not m:
            return False
        if (m.group(1), m.group(2)) != (self.tlg_author, self.tlg_work):
            sys.exit(f"[diorisis-export] ABORT: {self.stem}: header ids "
                     f"{self.tlg_author}/{self.tlg_work} disagree with Perseus ref {self.source_ref}")
        return True

    def sentences(self):
        """Yield (sentence_id, locus, punct_count, [(word, lemma, [morphs]), ...])
        in document order, streaming (each sentence is freed after the consumer
        moves on)."""
        for _ev, s in ET.iterparse(str(self.path), events=("end",)):
            if s.tag != "sentence":
                continue
            sid = int(s.get("id"))
            loc = s.get("location")
            if loc is None:
                sys.exit(f"[diorisis-export] ABORT: {self.stem} sentence {sid} has no location attribute")
            locus = loc if loc != "" else None
            words = []
            for w in s.findall("word"):
                lemmas = w.findall("lemma")
                if len(lemmas) != 1:
                    sys.exit(f"[diorisis-export] ABORT: {self.stem} sentence {sid} word "
                             f"{w.get('id')} has {len(lemmas)} <lemma> elements, expected 1")
                lm = lemmas[0]
                morphs = [a.get("morph") for a in lm.findall("analysis")]
                if any(m is None for m in morphs):
                    sys.exit(f"[diorisis-export] ABORT: {self.stem} sentence {sid} word "
                             f"{w.get('id')}: <analysis> without morph")
                words.append((w, lm, morphs))
            yield sid, locus, len(s.findall("punct")), words
            s.clear()


# --- Per-work export -------------------------------------------------------

class WorkExport:
    """One CTS work = one or more Diorisis files (letter-suffix ids and
    same-id volume splits merged, in (work id, filename) order)."""

    def __init__(self, work_key: str, files: list[DiorisisFile]):
        self.work_key = work_key
        self.cts_urn = f"urn:cts:greekLit:{work_key}"
        self.files = files

    def write(self, out_dir: Path):
        buf = io.StringIO()
        n_tokens = n_sentences = n_punct = 0
        n_unknown = n_nomorph = n_multi = 0
        n_sent_noloc = n_sent_notok = 0
        doc_stats = []
        for df in self.files:
            doc = df.stem
            d_tokens = d_sentences = 0
            for sid, locus, punct, words in df.sentences():
                n_sentences += 1
                d_sentences += 1
                n_punct += punct
                if locus is None:
                    n_sent_noloc += 1
                if not words:
                    # A word-less source sentence (punctuation only, e.g.
                    # Athenaeus' Roman-numeral headings): counted as a sentence
                    # (it is a source annotation unit) but contributes no token
                    # records, so distinct (doc, sentence_id) keys in the token
                    # stream fall short of `sentences` by this amount.
                    n_sent_notok += 1
                for w, lm, morphs in words:
                    where = f"{doc} s{sid} w{w.get('id')}"
                    rec = build_token_record(w, lm, morphs, locus, sid, doc, where)
                    if rec["lemma"] is None:
                        n_unknown += 1
                    if not morphs:
                        n_nomorph += 1
                    elif len(morphs) > 1:
                        n_multi += 1
                    buf.write(json.dumps({k: rec[k] for k in TOKEN_FIELD_ORDER}, ensure_ascii=False))
                    buf.write("\n")
                    n_tokens += 1
                    d_tokens += 1
            doc_stats.append((df, d_tokens, d_sentences))
        payload = buf.getvalue().encode("utf-8")
        sha = hashlib.sha256(payload).hexdigest()
        out_path = out_dir / "works" / f"{self.work_key}.jsonl.gz"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
                gz.write(payload)

        first = self.files[0]
        entry = {
            "work_key": self.work_key,
            "cts_urn": self.cts_urn,
            "diorisis_files": [df.stem for df in self.files],
            "file": out_path.name,
            "author": first.author,
            "title": first.title,
            "genre": first.genre,
            "subgenre": first.subgenre,
            "creation_date": first.creation_date,
            "tokens": n_tokens,
            "sentences": n_sentences,
            "tokens_unknown_lemma": n_unknown,
            "tokens_without_morph": n_nomorph,
            "tokens_multiple_morph": n_multi,
            "sentences_without_locus": n_sent_noloc,
            "sentences_without_tokens": n_sent_notok,
            "punct_marks_not_exported": n_punct,
            "source_refs": sorted({df.source_ref for df in self.files if df.source_ref}),
            "license": sorted({df.license_target for df in self.files if df.license_target}),
            "sha256": sha,
        }
        if len(self.files) > 1:
            entry["docs"] = [
                {"diorisis_file": df.stem, "tlg_header_id": f"{df.tlg_author}.{df.tlg_work}",
                 "title": df.title, "source_ref": df.source_ref,
                 "tokens": t, "sentences": s}
                for df, t, s in doc_stats
            ]
        return entry


# --- Scope / classification -------------------------------------------------

def audit_row(df: DiorisisFile, reason: str) -> dict:
    return {
        "diorisis_file": df.stem,
        "tlg_header_ids": f"{df.tlg_author}.{df.tlg_work}" if (df.tlg_author or df.tlg_work) else None,
        "author": df.author,
        "title": df.title,
        "license": df.license_target,
        "source_ref": df.source_ref,
        "reason": reason,
    }


def classify_files(files: list[DiorisisFile]):
    """Apply the license screen and the CTS mapping. Returns (kept, excluded_nc,
    excluded_unclear, unmapped, perseus_confirmed); kept maps work_key ->
    [DiorisisFile] in (work id, filename) order."""
    nc, unclear, unmapped = [], [], []
    perseus_confirmed = 0
    kept: dict[str, list[DiorisisFile]] = {}
    for df in files:
        lclass = license_class(df.license_target)
        if lclass == "noncommercial":
            nc.append(df)
            continue
        if lclass == "unclear":
            unclear.append(df)
            continue
        if not df.id_ok():
            unmapped.append(df)
            continue
        if df.check_perseus_ref():
            perseus_confirmed += 1
        kept.setdefault(df.work_key(), []).append(df)
    for work_key, group in kept.items():
        # (work id incl. letter suffix, then filename): letter parts in letter
        # order like glaux-v1 (051a Agis before 051b Cleomenes; 052a Tiberius
        # before 052b Caius), and same-id volume splits in filename order
        # (Diodorus Books I-V / XI-XVII / XVIII-XX; Aristotle Economics before
        # the Augustana Oeconomica II).
        group.sort(key=lambda d: (d.tlg_work, d.stem))
    return kept, nc, unclear, unmapped, perseus_confirmed


# --- Pointer stub ----------------------------------------------------------

def make_pointer_stub(manifest: dict, hf_repo: str) -> dict:
    exp = manifest["export"]
    release_id = exp["release_id"]
    src = manifest["source"]
    return {
        "release_id": release_id,
        "content_hash": exp["content_hash"],
        "pin_line": exp["pin_line"],
        "storage": {
            "hf_dataset_repo": hf_repo,
            "repo_type": "dataset",
            "path_in_repo": f"{release_id}/",
            "url": f"https://huggingface.co/datasets/{hf_repo}/tree/main/{release_id}",
            "payload": ("works/<work_key>.jsonl.gz per exported work, plus "
                        "manifest.json and diorisis_scope_audit.json"),
            "note": ("docs/annotation-export-contract.md, 'Storage': export payloads "
                     "live on the Hub; git tracks the exporter script and this pointer "
                     "stub only. Regenerate locally with "
                     "scripts/export_diorisis_annotations.py, publish with "
                     "scripts/upload_annotation_export.py."),
        },
        "counts": exp["counts"],
        "generated_by": exp["generated_by"],
        "generated_at": exp["generated_at"],
        "contract": exp["contract"],
        "upstream_pin": {
            "source": f"{src['name']} (figshare article 6187256, version 1)",
            "version_doi": src["version_doi"],
            "figshare_article": src["figshare_article"],
            "download_url": src["download_url"],
            "file": src["file"],
            "retained_copy": src["retained_copy"],
            "license": src["license_upstream"],
            "note": "cog pins the upstream; consumers pin only pin_line (docs/pinning-discipline.md)",
        },
    }


# --- Main ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--diorisis-root",
                    default=os.environ.get("DIORISIS_DIR", os.path.expanduser("~/Documents/diorisis")),
                    help="retained Diorisis copy (default $DIORISIS_DIR or ~/Documents/diorisis)")
    ap.add_argument("--out-dir", default=None,
                    help="output release dir (default <repo>/data/annotations/diorisis/<release_id>)")
    ap.add_argument("--release-id", default="diorisis-v1", help="cog export release id (default diorisis-v1)")
    ap.add_argument("--limit", type=int, default=None, help="export only the first N works (smoke test)")
    ap.add_argument("--works", nargs="*", default=None,
                    help="export only these works, by work_key (smoke test)")
    ap.add_argument("--skip-zip-check", action="store_true",
                    help="skip the retained-zip sha256 verification (smoke test only)")
    ap.add_argument("--hf-repo", default=HF_EXPORTS_REPO,
                    help="HF dataset repo the pointer stub records as the payload home")
    args = ap.parse_args()

    root = Path(args.diorisis_root)
    zip_path = root / UPSTREAM_ZIP_NAME
    xml_dir = root / "extracted"
    if not xml_dir.is_dir():
        sys.exit(f"[diorisis-export] ABORT: {xml_dir} not found; unzip {UPSTREAM_ZIP_NAME} there")
    repo_root = Path(__file__).resolve().parent.parent
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "data" / "annotations" / "diorisis" / args.release_id

    # Verify the retained copy is at the pin (docs/pinning-discipline.md).
    if not args.skip_zip_check:
        if not zip_path.is_file() or zip_path.stat().st_size != UPSTREAM_ZIP_BYTES:
            sys.exit(f"[diorisis-export] ABORT: {zip_path} missing or not {UPSTREAM_ZIP_BYTES} bytes")
        h = hashlib.sha256()
        with open(zip_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != UPSTREAM_ZIP_SHA256:
            sys.exit(f"[diorisis-export] ABORT: {zip_path} sha256 {h.hexdigest()} != pinned "
                     f"{UPSTREAM_ZIP_SHA256}; update the pin constants deliberately if the "
                     f"upstream pin is meant to move")

    xml_paths = sorted(xml_dir.glob("*.xml"))
    if len(xml_paths) != EXPECTED_FILES:
        sys.exit(f"[diorisis-export] ABORT: {len(xml_paths)} xml files in {xml_dir}, "
                 f"expected {EXPECTED_FILES}")

    print(f"[diorisis-export] parsing {len(xml_paths)} files ...", flush=True)
    files = [DiorisisFile(p) for p in xml_paths]
    kept, nc, unclear, unmapped, perseus_confirmed = classify_files(files)
    non_perseus = [df for df in files if not _PERSEUS_REF_RE.search(df.source_ref or "")]
    print(f"[diorisis-export] policy: {len(nc)} NonCommercial excluded, {len(unclear)} "
          f"unclear-license excluded, {len(unmapped)} unmapped; {perseus_confirmed} header ids "
          f"confirmed against Perseus refs, {len(non_perseus)} non-Perseus files "
          f"(header ids only)", flush=True)
    if unmapped:
        print(f"[diorisis-export] WARNING: files with non-TLG header ids excluded "
              f"(report, don't guess): {[df.stem for df in unmapped]}", flush=True)

    work_keys = sorted(kept)
    if args.works:
        wanted = set(args.works)
        work_keys = [k for k in work_keys if k in wanted]
    if args.limit:
        work_keys = work_keys[: args.limit]

    works: list[dict] = []
    totals = {"tokens": 0, "sentences": 0, "unknown": 0, "nomorph": 0, "multi": 0,
              "sent_noloc": 0, "sent_notok": 0, "punct": 0}
    for i, work_key in enumerate(work_keys, 1):
        we = WorkExport(work_key, kept[work_key])
        entry = we.write(out_dir)
        works.append(entry)
        totals["tokens"] += entry["tokens"]
        totals["sentences"] += entry["sentences"]
        totals["unknown"] += entry["tokens_unknown_lemma"]
        totals["nomorph"] += entry["tokens_without_morph"]
        totals["multi"] += entry["tokens_multiple_morph"]
        totals["sent_noloc"] += entry["sentences_without_locus"]
        totals["sent_notok"] += entry["sentences_without_tokens"]
        totals["punct"] += entry["punct_marks_not_exported"]
        if i % 100 == 0 or i == len(work_keys):
            print(f"[diorisis-export] {i}/{len(work_keys)} works ... {totals['tokens']:,} tokens", flush=True)

    # Deterministic content hash over the uncompressed per-work payloads
    # (same method as every other cog export).
    hasher = hashlib.sha256()
    for w in sorted(works, key=lambda x: x["work_key"]):
        hasher.update(f"{w['work_key']}:{w['sha256']}\n".encode("utf-8"))
    content_hash = "sha256:" + hasher.hexdigest()

    license_tally: dict[str, int] = {}
    for df in files:
        key = df.license_target or "(none)"
        license_tally[key] = license_tally.get(key, 0) + 1
    source_tally: dict[str, int] = {}
    for df in files:
        key = df.source_name or "(none)"
        source_tally[key] = source_tally.get(key, 0) + 1

    file_pin = {
        "name": UPSTREAM_ZIP_NAME,
        "bytes": UPSTREAM_ZIP_BYTES,
        "md5": UPSTREAM_ZIP_MD5,
        "sha256": UPSTREAM_ZIP_SHA256,
    }

    scope_audit = {
        "source": {
            "name": UPSTREAM_NAME,
            "figshare_article": UPSTREAM_ARTICLE,
            "version_doi": UPSTREAM_VERSION_DOI,
            "download_url": UPSTREAM_DOWNLOAD_URL,
            "file": file_pin,
            "retained_copy": _tilde(root),
            "files_in_corpus": len(files),
        },
        "license_screen": {
            "rule": ("docs/source-policy.md: any NonCommercial (or NoDerivatives) clause is banned "
                     "in every role, and licenses neither NC nor on the open allowlist "
                     "(creativecommons.org /by/ or /by-sa/, any version) are excluded as unclear "
                     "rather than served. Re-derived from every file's TEI <licence> at run time. "
                     "In the pinned corpus all 820 files carry CC BY-SA 3.0 US; the figshare "
                     "record's aggregate license is CC BY 4.0."),
            "noncommercial_excluded": {
                "files": len(nc),
                "detail": sorted((audit_row(df, "NonCommercial licence") for df in nc),
                                 key=lambda d: d["diorisis_file"]),
            },
            "unclear_license_excluded": {
                "files": len(unclear),
                "detail": sorted((audit_row(df, "licence not on the open allowlist (unclear)")
                                  for df in unclear), key=lambda d: d["diorisis_file"]),
            },
            "license_tally": dict(sorted(license_tally.items())),
        },
        "work_identity": {
            "rule": ("Every file's TEI header carries tlgAuthor/tlgId, which are the Perseus "
                     "greekLit CTS ids (for Euripides this differs from the TLG-E canon on "
                     "purpose: greekLit tlg0006.tlg007 is Hecuba). For Perseus-sourced files the "
                     "header ids are verified against the greekLit path embedded in the file's "
                     "own source ref; a mismatch aborts. Letter-suffixed ids merge into the base "
                     "CTS work in letter order and same-id volume splits merge in filename order, "
                     "with the Diorisis file stem in each token's `doc`. Files with non-TLG "
                     "header ids would be excluded and listed here, never guessed."),
            "header_ids_confirmed_against_perseus_ref": perseus_confirmed,
            "non_perseus_files": sorted(
                ({"diorisis_file": df.stem, "tlg_header_ids": f"{df.tlg_author}.{df.tlg_work}",
                  "source_name": df.source_name, "source_ref": df.source_ref}
                 for df in non_perseus if df.id_ok()),
                key=lambda d: d["diorisis_file"]),
            "unmapped_files": [audit_row(df, "header ids do not fit tlgAuthor=NNNN / tlgId=NNN[a-z]; "
                                             "excluded, not guessed") for df in unmapped],
            "merged_works": sorted(
                ({"work_key": k, "diorisis_files": [df.stem for df in g]}
                 for k, g in kept.items() if len(g) > 1),
                key=lambda d: d["work_key"]),
        },
        "source_tally": dict(sorted(source_tally.items())),
    }

    manifest = {
        "export": {
            "release_id": args.release_id,
            "contract": "docs/annotation-export-contract.md",
            "generated_by": "scripts/export_diorisis_annotations.py",
            "generated_at": GENERATED_AT,
            "content_hash": content_hash,
            "content_hash_method": (
                "sha256 over the newline-joined '<work_key>:<sha256-of-uncompressed-jsonl>' lines, "
                "work_key-sorted; excludes gzip framing so it is reproducible on unchanged input "
                "(generated_at is itself a constant: the export uses no wall clock)"
            ),
            "pin_line": f"cog export {args.release_id}, {content_hash}",
            "record_layout": (
                "per-work JSONL under works/<work_key>.jsonl.gz (gzip mtime=0, deterministic); one token "
                "record per line. work_key is the greekLit CTS work id (tlgNNNN.tlgNNN) from each file's "
                "TEI header tlgAuthor/tlgId; letter-suffixed ids (Plutarch tlg051a and friends) and "
                "same-id volume splits (Diodorus, Aristotle Oeconomica) are merged into the base work's "
                "stream, with the Diorisis file stem in each token's `doc` and (doc, sentence_id) as the "
                "unique sentence key. head/deprel are omitted entirely: Diorisis has no dependency syntax"
            ),
            "token_fields": {
                "id": "Diorisis native word id (integer), numbered per sentence",
                "form": "surface form, converted from the source's Beta Code to Unicode Greek and cog-normalized (see source.encoding_normalization)",
                "lemma": "Diorisis lexicon headword ('entry'), verbatim except cog encoding normalization; null where the corpus could not lemmatize (lemma_id='unknown')",
                "lemma_id": "Diorisis lexicon id, verbatim: numeric for LSJ-backed lemmas, 'nlsjNNN' for lemmas outside LSJ, 'unknown' for unanalyzed words; carries homograph identity (headwords have no disambiguation digits)",
                "pos": "Diorisis native coarse part of speech (verb/noun/article/adjective/conjunction/pronoun/particle/preposition/adverb/proper/interjection); null on unanalyzed words",
                "morph": "the source's surviving morphological readings for the chosen lemma: a list of Morpheus descriptor strings (e.g. 'fem nom/voc sg'), verbatim and in source order, duplicates included; null when the source gives none. Multiple readings are stored as-is, never collapsed to one",
                "locus": "the sentence's location attribute verbatim: the work's own citation scheme at sentence granularity (book.chapter.section, line, Stephanus page, named parts); null where the source leaves it empty",
                "sentence_id": "Diorisis native per-file sentence id (integer, the annotation unit); unique within the work stream together with `doc`. Word-less source sentences (punctuation only) are counted in `sentences` but contribute no token records (see counts.sentences_without_tokens)",
                "doc": "the Diorisis file stem (e.g. 'Plutarch (0007) - Agis (051a)'); distinguishes merged parts and volume splits",
                "analysis": "'auto' on every sentence: the whole Diorisis annotation layer is automatic",
                "provenance_tag": "'diorisis' on every token",
                "treetagger": "Diorisis native TreeTagger attribute as a boolean: true when the lemma was chosen by the TreeTagger POS tagger, false otherwise",
                "disambiguated": "Diorisis native disambiguated attribute verbatim: 'n/a' when no lemma disambiguation was needed, else the disambiguation score as the source's decimal string (e.g. '0.5')",
                "isquote": "true on words inside quotations (Diorisis native flag); null otherwise",
                "lacuna": "true on words adjacent to a lacuna (Diorisis native flag); null otherwise",
            },
            "counts": {
                "works_exported": len(works),
                "diorisis_files_exported": sum(len(w["diorisis_files"]) for w in works),
                "tokens": totals["tokens"],
                "sentences": totals["sentences"],
                "sentences_by_analysis": {"auto": totals["sentences"]},
                "tokens_by_analysis": {"auto": totals["tokens"]},
                "provenance_sentences": {"diorisis": totals["sentences"]},
                "provenance_tokens": {"diorisis": totals["tokens"]},
                "tokens_unknown_lemma": totals["unknown"],
                "tokens_without_morph": totals["nomorph"],
                "tokens_multiple_morph": totals["multi"],
                "sentences_without_locus": totals["sent_noloc"],
                "sentences_without_tokens": totals["sent_notok"],
                "punct_marks_not_exported": totals["punct"],
                "files_excluded_noncommercial": len(nc),
                "files_excluded_unclear_license": len(unclear),
                "files_unmapped": len(unmapped),
            },
        },
        "source": {
            "name": UPSTREAM_NAME,
            "figshare_article": UPSTREAM_ARTICLE,
            "version_doi": UPSTREAM_VERSION_DOI,
            "download_url": UPSTREAM_DOWNLOAD_URL,
            "file": file_pin,
            "retained_copy": _tilde(root),
            "license_upstream": (
                "CC BY 4.0 (the figshare record's aggregate license); every file's own TEI header "
                "carries CC BY-SA 3.0 US. Text sources: Perseus canonical-greekLit (752 files), "
                "Bibliotheca Augustana (60), The Little Sailing (8), per each file's source ref"
            ),
            "format": ("per-work TEI XML ('Author (NNNN) - Title (NNN).xml'): <sentence id location> "
                       "of <word form id> elements, each with one <lemma> (id/entry/POS/TreeTagger/"
                       "disambiguated) holding zero or more <analysis morph>; standalone <punct> "
                       "marks are not tokens and are not exported (counted per work)"),
            "annotation_method": (
                "Automatic throughout (analysis='auto' on every sentence): morphological analysis "
                "from Morpheus, lemma assignment against a lexicon built from LSJ (plus 'nlsj' "
                "additions), disambiguation by frequency and, where needed, by a TreeTagger POS "
                "tagger (the per-token treetagger/disambiguated fields carry the source's own "
                "marking). No human revision layer exists; where several morphological readings "
                "survive, morph carries them all. Vatri & McGillivray 2018."
            ),
            "provenance_note": (
                "provenance_tag='diorisis' on every token; tier 3 under docs/source-policy.md "
                "(non-PROIEL automatic annotation): no PROIEL data and no PROIEL-trained models "
                "anywhere in the pipeline, so none of the PROIEL screens apply. Not Gorman-derived. "
                "Where a non-PROIEL manual source covers the same work, prefer it; Diorisis is "
                "lemma/morphology only and carries no syntax."
            ),
            "lemma_convention": (
                "Preserved verbatim (cog does not normalize lemma conventions). Diorisis headwords "
                "follow its LSJ-derived lexicon; homograph identity lives in lemma_id (numeric LSJ-"
                "backed ids, 'nlsjNNN' for non-LSJ lemmas), not in headword digits. Only cog encoding "
                "normalization (NFC, apostrophe, sigma) is applied to the headword string."
            ),
            "locus_note": (
                "Diorisis cites at sentence granularity: each <sentence> carries a location string "
                "already composed per the work's own citation scheme (book.chapter.section for most "
                "prose, bare line numbers for drama and epic, Stephanus pages like '17a' for Plato, "
                "named parts like 'Proof.4' or 'Ath. Pol..3'). The locus is that string verbatim on "
                "each of the sentence's tokens; empty locations stay null (faithfully sparse). "
                "Within a merged multi-part work the locus namespace is per Diorisis file: combine "
                "locus with the token's `doc`."
            ),
            "encoding_normalization": {
                "beta_code": ("the source stores forms in TLG Beta Code (lowercase letters, '*' "
                              "capitals, ()/\\=|+ diacritics, 'v' digamma); converted to Unicode "
                              "Greek by the exporter's audited table, unknown characters abort"),
                "unicode": "NFC",
                "apostrophes_to_U+2019": ["U+02BC", "U+0027", "U+2018", "U+2019"],
                "sigma": "final ς word-finally, medial σ otherwise (applied to form and lemma)",
                "lemma_entries": "already Unicode in the source; same NFC/apostrophe/sigma normalization applied",
            },
            "citation": (
                "Alessandro Vatri and Barbara McGillivray. 2018. The Diorisis Ancient Greek Corpus. "
                "Research Data Journal for the Humanities and Social Sciences 3(1), 55-65. "
                "doi:10.1163/24523666-01000013. Dataset: doi:10.6084/m9.figshare.6187256.v1 (CC BY 4.0)."
            ),
        },
        "policy": {
            "license_screen": {
                "rule": scope_audit["license_screen"]["rule"],
                "noncommercial_excluded_files": len(nc),
                "unclear_license_excluded_files": len(unclear),
                "detail_file": "diorisis_scope_audit.json",
            },
            "proiel": ("tier 3: not PROIEL data and not PROIEL-model output; no PROIEL screen "
                       "applies (docs/source-policy.md)"),
            "gorman": "not Gorman-derived; no Gorman tagging applies",
            "unmapped_files": [df.stem for df in unmapped],
        },
        "consumers": (
            "This is the Diorisis half of annotation-consumption queue item 1e "
            "(docs/annotation-export-contract.md). dilemma pins this export by export.pin_line. "
            "The corpus is lemma/morphology only: consumers needing syntax use the treebank "
            "exports (glaux-v1 and friends)."
        ),
        "works": [dict(w) for w in sorted(works, key=lambda x: x["work_key"])],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")
    with open(out_dir / "diorisis_scope_audit.json", "w", encoding="utf-8") as fh:
        json.dump(scope_audit, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")

    # The git-tracked pointer stub, written next to the (gitignored) release dir.
    # Skipped for smoke tests, whose partial hash must never overwrite the pin.
    if not args.limit and not args.works:
        stub_path = out_dir.parent / f"{args.release_id}.json"
        with open(stub_path, "w", encoding="utf-8") as fh:
            json.dump(make_pointer_stub(manifest, args.hf_repo), fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"[diorisis-export] pointer stub -> {stub_path}", flush=True)

    print(f"[diorisis-export] wrote {len(works)} works, {totals['tokens']:,} tokens "
          f"({totals['sentences']:,} sentences) to {out_dir}", flush=True)
    print(f"[diorisis-export] unknown-lemma tokens {totals['unknown']:,}; multi-reading morph "
          f"{totals['multi']:,}; sentences without locus {totals['sent_noloc']:,}; word-less "
          f"sentences {totals['sent_notok']:,}; punct marks not exported {totals['punct']:,}", flush=True)
    print(f"[diorisis-export] policy: NC excluded {len(nc)} files; unclear-license excluded "
          f"{len(unclear)} files; unmapped {len(unmapped)} files", flush=True)
    print(f"[diorisis-export] pin line: cog export {args.release_id}, {content_hash}", flush=True)


if __name__ == "__main__":
    main()
