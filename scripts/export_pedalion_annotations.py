#!/usr/bin/env python3
"""Export the Pedalion dependency treebanks as cog's standardized annotation export.

This produces the annotation export defined by docs/annotation-export-contract.md:
per-work, CTS-URN-keyed streams of token records, with cog-owned encoding
normalization and the source-native AGDT/Perseus tagset and lemmas preserved
verbatim. It is item 1c of the annotation-consumption queue.

Source: the Pedalion trees (github.com/perseids-publications/pedalion-trees),
CC BY-SA 4.0 (verified from the repo's TREEBANK_LICENSE at run time). The MIT
LICENSE in the repo covers the site code, not the treebank data. The treebank
data lives in public/xml/*.xml, AGDT ("aldt") format: each <word> carries
form/lemma/postag/relation/head and a `ref` attribute
`PREFIX|DOCUMENT|SENTENCE|TOKEN`, where PREFIX is the per-token provenance
discriminator.

Provenance / policy (docs/source-policy.md) - Pedalion mixes three provenances,
distinguished by the ref PREFIX, and this exporter is the concrete test of both
the PROIEL three-tier rule and the Gorman tag-don't-delete rule:

  - PRO1 / PRO2  -> re-exported PROIEL trees = TIER-1 PROIEL data. DROPPED
    entirely (not emitted). These occur only in the two mixed example-sentence
    files (chilia-sentences.xml, external_examplesentences.xml).
  - GORMAN       -> INCLUDED but tagged provenance_tag="gorman" (tag-don't-delete:
    cog holds Gorman tagged; dilemma filters it at read time; other consumers may
    use it).
  - Leuven / PER / HARR -> INCLUDED, provenance_tag="pedalion", the ref prefix
    carried in ref_provenance so consumers can see the origin.

Provenance is uniform within a sentence (verified: 0 sentences carry more than one
distinct real-token prefix), so PRO1/PRO2 are dropped at the sentence level, which
also drops the sentence's artificial (elliptic) gap nodes.

Scope (per the audit handoff): the literary works Pedalion covers that GLAUx does
NOT already subsume, plus the two mixed example-sentence collections and the
Pedalion example sentences, plus the papyri. GLAUx (item 1e) already ingests 46
Pedalion-derived literary works (its metadata marks them TREEBANK_ANNOTATIONS=
'Pedalion Trees'); re-exporting those from Pedalion would duplicate GLAUx, so this
export carries only the Pedalion literary works GLAUx lacks. That set is verified
reproducibly against a GLAUx metadata.txt checkout at run time (guarded; the run
aborts if the set has drifted). The Menander Dyskolos file is EXCLUDED for
edition-rights safety: its annotation's `form` tokens reconstruct the 1958 Bodmer
text, so emitting the annotation would redistribute that edition's text.

cog owns encoding normalization (NFC; elision apostrophes -> U+2019; standard
final/medial sigma). cog does NOT normalize lemma conventions: Pedalion's
homograph-disambiguation digits (e.g. "ξένος2") are preserved verbatim.

The export is deterministic: gzip is written with mtime=0 and the content hash is
computed over the uncompressed per-work payloads, so re-running on unchanged input
reproduces byte-identical files and the same content_hash.

Storage (docs/annotation-export-contract.md, "Storage"): the payload this writes
is NOT committed to git. It is uploaded to the Hugging Face dataset repo with
scripts/upload_annotation_export.py; git tracks this exporter plus the pointer
stub written next to the release dir (data/annotations/pedalion/<release_id>.json).
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
import xml.etree.ElementTree as ET
from pathlib import Path

# The HF dataset repo that holds export payloads (docs/annotation-export-contract.md,
# "Storage"); the release id is the path in the repo. upload_annotation_export.py
# shares this default.
HF_EXPORTS_REPO = "ciscoriordan/open-greek-corpus-annotation-exports"


def _tilde(path):
    """Home-relativize a path (~/...) so published manifests carry no personal
    absolute path (matches the OGA exporter's retained_clone convention)."""
    p = str(path)
    home = os.path.expanduser("~")
    return "~" + p[len(home):] if p.startswith(home) else p

# --- Scope: file classification and the audited literary crosswalk ---------

# The two mixed example-sentence collections (carry PER/GORMAN/PRO1/PRO2/HARR)
# plus the Pedalion grammar example sentences (all Leuven). Kept as per-file
# collection streams, not split by cited source work: the same source authors
# recur across chilia and external, so a per-source split collides, and these are
# harvested illustrative sentences, not continuous works. Each token still carries
# its cited source (doc + resolved cts_urn + locus).
EXAMPLE_FILES = {
    "example-sentences.xml",
    "chilia-sentences.xml",
    "external_examplesentences.xml",
}
# Documentary papyri: split per Trismegistos document (each TM id is its own work).
PAPYRI_FILES = {"papyri.xml"}

# The Pedalion literary works GLAUx does NOT subsume (audit handoff). The GLAUx
# guard below re-verifies each `tlg` is absent from the live GLAUx metadata and
# aborts on drift; the crosswalk is needed because several Pedalion document_ids
# are non-canonical placeholders (e.g. "0260-x", "Mimn1") that do not machine-map.
# `work` None => the source gives no work number; emit a textgroup-only citation.
LITERARY_WORKS = {
    "chion.xml":      {"tlg": "0041-001", "textgroup": "tlg0041", "work": "tlg001",
                       "author": "Chion Heracleensis", "title": "Epistulae"},
    "epicurus1.xml":  {"tlg": "0537-012", "textgroup": "tlg0537", "work": "tlg012",
                       "author": "Epicurus", "title": "Epistula ad Menoeceum"},
    "ez.xml":         {"tlg": "0343-001", "textgroup": "tlg0343", "work": "tlg001",
                       "author": "Ezechiel Tragicus", "title": "Exagoge"},
    "phlegon.xml":    {"tlg": "0585-001", "textgroup": "tlg0585", "work": "tlg001",
                       "author": "Phlegon Trallianus", "title": "Opera"},
    "sappho.xml":     {"tlg": "0009-001", "textgroup": "tlg0009", "work": "tlg001",
                       "author": "Sappho", "title": "Fragmenta"},
    "sextus.xml":     {"tlg": "0544-002", "textgroup": "tlg0544", "work": "tlg002",
                       "author": "Sextus Empiricus", "title": "Adversus mathematicos"},
    # No canonical work number in the source (document_id is a placeholder); emit a
    # textgroup-only citation (cts_urn=null, textgroup recorded in the manifest).
    "mimn.xml":       {"tlg": "0259-001", "textgroup": "tlg0259", "work": None,
                       "author": "Mimnermus", "title": "Fragmenta"},
    "semonides.xml":  {"tlg": "0260-001", "textgroup": "tlg0260", "work": None,
                       "author": "Semonides", "title": "Fragmenta"},
}
# Not in GLAUx either, but withheld on edition-rights grounds (see module docstring).
MENANDER_FILE = "menander_dyskolos.xml"
MENANDER_TLG = "0541-007"

# The full literary set this scope reasons about = the 8 kept + Menander.
EXPECTED_NOT_IN_GLAUX = set(LITERARY_WORKS) | {MENANDER_FILE}

# A few Pedalion works GLAUx is known to subsume; the guard asserts these ARE in
# GLAUx, so a wrong/empty metadata file cannot silently pass the "absent" checks.
GLAUX_SUBSUMED_SENTINELS = ["0019-001", "0006-003", "0093-009", "0059-003"]

PROVENANCE_PREFIXES = {"Leuven", "PER", "GORMAN", "PRO1", "PRO2", "HARR"}
DROP_PREFIXES = {"PRO1", "PRO2"}


# --- cog-owned encoding normalization (identical policy to the OGA exporter) --

_APOSTROPHES = {
    "ʼ",  # MODIFIER LETTER APOSTROPHE (a common Pedalion elision mark, e.g. δʼ)
    "'",       # APOSTROPHE
    "‘",  # LEFT SINGLE QUOTATION MARK
    "’",  # RIGHT SINGLE QUOTATION MARK (target)
}
_APOS_TABLE = {ord(c): "’" for c in _APOSTROPHES}


# Canonical sigma normalization is shared across all exporters (see
# scripts/annotation_encoding.py). Import it so every exporter stays in sync.
from annotation_encoding import normalize_sigma as _normalize_sigma


def normalize(text):
    """Apply cog's guaranteed encoding normalization to a surface/lemma string."""
    if text is None:
        return None
    text = unicodedata.normalize("NFC", text)
    text = text.translate(_APOS_TABLE)
    text = _normalize_sigma(text)
    return unicodedata.normalize("NFC", text)


# --- CTS / citation helpers ------------------------------------------------

_TLG_DOC_RE = re.compile(r"^(\d{4})-(\d{2,3})[a-z]?$")


def resolve_doc(document_id):
    """Resolve a Pedalion document_id to (work_key, cts_urn, citation_scheme).

    - a canonical TLG id "AAAA-WWW"  -> greekLit CTS work
    - a bare Trismegistos number     -> tm<id>, no CTS
    - anything else (Pedalion labels like "Chilia", "NT")  -> no CTS
    """
    d = (document_id or "").strip()
    m = _TLG_DOC_RE.match(d)
    if m:
        tg, wk = m.group(1), m.group(2)
        return f"tlg{tg}.tlg{wk}", f"urn:cts:greekLit:tlg{tg}.tlg{wk}", "cts"
    if d.isdigit():
        return f"tm{d}", None, "trismegistos"
    return None, None, "pedalion"


def clean_locus(subdoc):
    """A Pedalion subdoc is the passage citation; normalize decimal-comma to dot."""
    s = (subdoc or "").strip()
    if not s:
        return None
    return s.replace(",", ".")


def token_prefix(ref):
    """The provenance discriminator = first '|'-field of ref; '' if unusable."""
    p = (ref or "").split("|")[0]
    if p.endswith("Leuven"):  # heals one corrupted ez.xml ref ("=E1605Leuven|...")
        return "Leuven"
    return p if p in PROVENANCE_PREFIXES else ""


def sentence_provenance(words):
    """The single provenance prefix of a sentence, from its real (non-artificial)
    tokens. Provenance is uniform per sentence; falls back to 'Leuven' when a
    sentence is entirely artificial/blank (only in all-Leuven single-work files)."""
    prefixes = {token_prefix(w.get("ref")) for w in words if not w.get("artificial")}
    prefixes.discard("")
    if len(prefixes) > 1:
        raise ValueError(f"sentence mixes provenances {sorted(prefixes)}")
    return next(iter(prefixes)) if prefixes else "Leuven"


# --- Token record ----------------------------------------------------------

TOKEN_FIELD_ORDER = [
    "id", "form", "lemma", "pos", "morph", "head", "deprel",
    "cts_urn", "locus", "doc", "sentence_id",
    "analysis", "provenance_tag", "ref_provenance",
]


def build_token_record(w, sentence_id, cts_urn, locus, doc, provenance_tag, ref_provenance):
    postag = w.get("postag") or ""
    lemma = w.get("lemma")
    if lemma == "":
        lemma = None
    try:
        head = int(w.get("head"))
    except (TypeError, ValueError):
        head = w.get("head")
    try:
        tok_id = int(w.get("id"))
    except (TypeError, ValueError):
        tok_id = w.get("id")
    return {
        "id": tok_id,
        "form": normalize(w.get("form")),
        "lemma": normalize(lemma) if lemma is not None else None,
        "pos": postag[0] if postag else None,
        "morph": postag or None,
        "head": head,
        "deprel": w.get("relation"),
        "cts_urn": cts_urn,
        "locus": locus,
        "doc": doc,
        "sentence_id": sentence_id,
        "analysis": "manual",
        "provenance_tag": provenance_tag,
        "ref_provenance": ref_provenance,
    }


def provenance_tag_for(prefix):
    return "gorman" if prefix == "GORMAN" else "pedalion"


# --- Per-work stream assembly ----------------------------------------------

class WorkStream:
    def __init__(self, work_key, cts_urn, citation_scheme, source_file, textgroup=None):
        self.work_key = work_key
        self.cts_urn = cts_urn
        self.citation_scheme = citation_scheme
        self.source_file = source_file
        self.textgroup = textgroup
        self.records = []          # list of token dicts
        self.sentences = set()
        self.prov_tokens = {"pedalion": 0, "gorman": 0}
        self.ref_prov_tokens = {}  # Leuven/PER/HARR/GORMAN -> count
        self.artificial = 0
        self.source_docs = {}      # doc_id -> {cts_urn, citation_scheme}

    def add_sentence(self, words, sentence_id, prefix, per_token_citation):
        ptag = provenance_tag_for(prefix)
        for w in words:
            doc = w.get("_doc")
            cts_urn, locus = per_token_citation(w)
            rec = build_token_record(w, sentence_id, cts_urn, locus, doc, ptag, prefix)
            self.records.append(rec)
            self.prov_tokens[ptag] += 1
            self.ref_prov_tokens[prefix] = self.ref_prov_tokens.get(prefix, 0) + 1
            if w.get("artificial"):
                self.artificial += 1
            if doc is not None and doc not in self.source_docs:
                dk, du, ds = resolve_doc(doc)
                self.source_docs[doc] = {"cts_urn": du, "citation_scheme": ds}
        self.sentences.add(sentence_id)

    def write(self, out_dir):
        buf = io.StringIO()
        for rec in self.records:
            buf.write(json.dumps({k: rec[k] for k in TOKEN_FIELD_ORDER}, ensure_ascii=False))
            buf.write("\n")
        payload = buf.getvalue().encode("utf-8")
        sha = hashlib.sha256(payload).hexdigest()
        out_path = out_dir / "works" / f"{self.work_key}.jsonl.gz"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
                gz.write(payload)
        entry = {
            "work_key": self.work_key,
            "cts_urn": self.cts_urn,
            "citation_scheme": self.citation_scheme,
            "source_file": self.source_file,
            "file": out_path.name,
            "tokens": len(self.records),
            "sentences": len(self.sentences),
            "artificial_nodes": self.artificial,
            "provenance_tokens": self.prov_tokens,
            "ref_provenance_tokens": dict(sorted(self.ref_prov_tokens.items())),
            "sha256": sha,
        }
        if self.textgroup:
            entry["textgroup"] = self.textgroup
        if len(self.source_docs) > 1 or self.citation_scheme == "pedalion":
            entry["source_docs"] = dict(sorted(self.source_docs.items()))
        return entry


# --- GLAUx scope verification ----------------------------------------------

def load_glaux_tlg_ids(metadata_path):
    """Return (set of all base TLG ids in GLAUx, count of Pedalion-subsumed rows)."""
    import csv
    base = lambda t: re.sub(r"[a-z]$", "", t.strip())
    all_ids = set()
    subsumed = 0
    with open(metadata_path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            tlg = r.get("TLG", "")
            if tlg and tlg != "NA":
                all_ids.add(base(tlg))
            if "pedalion" in (r.get("ORIGINAL_TREEBANK_LINK") or "").lower():
                subsumed += 1
    return all_ids, subsumed


def verify_glaux_scope(metadata_path):
    """Re-derive and guard the literary scope against a live GLAUx checkout.

    Aborts if any in-scope literary work is now in GLAUx (scope drifted), or if
    the known-subsumed sentinels are missing (wrong/empty metadata file). Returns
    an audit record for the manifest."""
    base = lambda t: re.sub(r"[a-z]$", "", t.strip())
    all_ids, subsumed = load_glaux_tlg_ids(metadata_path)
    now_in_glaux = []
    for stem, meta in LITERARY_WORKS.items():
        if base(meta["tlg"]) in all_ids:
            now_in_glaux.append((stem, meta["tlg"]))
    if now_in_glaux:
        sys.exit(f"[pedalion-export] ABORT: literary works now present in GLAUx "
                 f"(scope drifted, update LITERARY_WORKS): {now_in_glaux}")
    missing = [s for s in GLAUX_SUBSUMED_SENTINELS if base(s) not in all_ids]
    if missing:
        sys.exit(f"[pedalion-export] ABORT: GLAUx metadata missing known-subsumed "
                 f"sentinels {missing}; wrong or empty {metadata_path}?")
    return {
        "glaux_metadata": _tilde(metadata_path),
        "glaux_metadata_sha256": hashlib.sha256(
            Path(metadata_path).read_bytes()).hexdigest(),
        "glaux_texts": len(all_ids),
        "glaux_pedalion_subsumed": subsumed,
        "literary_works_kept_not_in_glaux": sorted(
            m["tlg"] for m in LITERARY_WORKS.values()),
        "menander_tlg_in_glaux": base(MENANDER_TLG) in all_ids,
        "note": ("cog re-verifies this scope against GLAUx at run time; item 1e "
                 "(GLAUx) owns the 46 Pedalion literary works GLAUx subsumes."),
    }


# --- License verification --------------------------------------------------

def verify_license(pedalion_root):
    """Confirm the treebank data is CC BY-SA 4.0 from the repo's TREEBANK_LICENSE."""
    path = Path(pedalion_root) / "TREEBANK_LICENSE"
    if not path.is_file():
        sys.exit(f"[pedalion-export] ABORT: TREEBANK_LICENSE not found at {path}")
    head = path.read_text(encoding="utf-8", errors="replace")[:200]
    if "Attribution-ShareAlike 4.0 International" not in head:
        sys.exit(f"[pedalion-export] ABORT: TREEBANK_LICENSE is not CC BY-SA 4.0: {head!r}")
    return "CC BY-SA 4.0 (Attribution-ShareAlike 4.0 International)"


# --- Main ------------------------------------------------------------------

def iter_sentences(xml_path):
    root = ET.parse(xml_path).getroot()
    for s in root.findall(".//sentence"):
        yield s


def process_literary(stem, meta, xml_path, glaux_all):
    """One in-scope literary file -> one WorkStream (GLAUx-subsumed docs dropped)."""
    base = lambda t: re.sub(r"[a-z]$", "", t.strip())
    work_key = f"{meta['textgroup']}.{meta['work']}" if meta["work"] else f"pedalion-{stem[:-4]}"
    cts_urn = f"urn:cts:greekLit:{work_key}" if meta["work"] else None
    scheme = "cts" if meta["work"] else "pedalion-literary"
    ws = WorkStream(work_key, cts_urn, scheme, stem, textgroup=f"urn:cts:greekLit:{meta['textgroup']}")
    dropped = {"tokens": 0, "sentences": 0}
    for s in iter_sentences(xml_path):
        # Drop any sentence whose document_id is a canonical TLG already in GLAUx
        # (e.g. sappho.xml's 0009-002 Epigrammata, which item 1e owns).
        _, du, dscheme = resolve_doc(s.get("document_id"))
        if dscheme == "cts":
            wk, _, _ = resolve_doc(s.get("document_id"))
            tlg = wk[3:].replace(".tlg", "-")  # tlg0009.tlg002 -> 0009-002
            if base(tlg) in glaux_all:
                dropped["sentences"] += 1
                dropped["tokens"] += len(s.findall("word"))
                continue
        words = s.findall("word")
        prefix = sentence_provenance(words)
        for w in words:
            w.set("_doc", s.get("document_id"))
        locus = clean_locus(s.get("subdoc"))
        ws.add_sentence(words, int(s.get("id")), prefix,
                        per_token_citation=lambda w, cu=cts_urn, lo=locus: (cu, lo))
    return ws, dropped


def process_papyri(stem, xml_path):
    """papyri.xml -> one WorkStream per Trismegistos document (tm<id>)."""
    streams = {}
    for s in iter_sentences(xml_path):
        doc = s.get("document_id")
        work_key, cts_urn, scheme = resolve_doc(doc)
        if work_key is None:  # non-numeric papyri doc (none observed); skip safely
            continue
        if work_key not in streams:
            streams[work_key] = WorkStream(work_key, cts_urn, scheme, stem)
        words = s.findall("word")
        prefix = sentence_provenance(words)
        for w in words:
            w.set("_doc", doc)
        locus = clean_locus(s.get("subdoc"))
        streams[work_key].add_sentence(words, int(s.get("id")), prefix,
                                       per_token_citation=lambda w, lo=locus: (None, lo))
    return list(streams.values())


def process_examples(stem, xml_path, buckets):
    """One example-sentence file -> one collection WorkStream. PRO1/PRO2 sentences
    are dropped; each token keeps its cited source (doc + resolved cts_urn + locus)."""
    work_key = "pedalion-" + stem[:-4].replace("_", "-")
    ws = WorkStream(work_key, None, "pedalion-collection", stem)
    for s in iter_sentences(xml_path):
        words = s.findall("word")
        prefix = sentence_provenance(words)
        n = len(words)
        if prefix in DROP_PREFIXES:
            buckets[prefix]["tokens"] += n
            buckets[prefix]["sentences"] += 1
            continue
        doc = s.get("document_id")
        _, src_urn, _ = resolve_doc(doc)
        locus = clean_locus(s.get("subdoc"))
        for w in words:
            w.set("_doc", doc)
        ws.add_sentence(words, int(s.get("id")), prefix,
                        per_token_citation=lambda w, cu=src_urn, lo=locus: (cu, lo))
    return ws


def make_pointer_stub(manifest, hf_repo):
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
            "payload": ("works/<work_key>.jsonl.gz per exported work, plus "
                        "manifest.json and pedalion_scope_audit.json"),
            "note": ("docs/annotation-export-contract.md, 'Storage': export payloads "
                     "live on the Hub; git tracks the exporter script and this pointer "
                     "stub only. Regenerate locally with "
                     "scripts/export_pedalion_annotations.py, publish with "
                     "scripts/upload_annotation_export.py."),
        },
        "counts": exp["counts"],
        "generated_by": exp["generated_by"],
        "generated_at": exp["generated_at"],
        "contract": exp["contract"],
        "upstream_pin": {
            "source": f"{manifest['source']['name']} @ {manifest['source']['commit']}",
            "repo": manifest["source"]["repo"],
            "commit": manifest["source"]["commit"],
            "note": "cog pins the upstream; consumers pin only pin_line (docs/pinning-discipline.md)",
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pedalion-root",
                    default=os.environ.get("PEDALION_ROOT", os.path.expanduser("~/Documents/pedalion-trees")),
                    help="retained Pedalion clone (default $PEDALION_ROOT or ~/Documents/pedalion-trees)")
    ap.add_argument("--glaux-metadata",
                    default=os.environ.get("GLAUX_METADATA", os.path.expanduser("~/Documents/glaux/metadata.txt")),
                    help="GLAUx metadata.txt, for reproducible literary-scope verification")
    ap.add_argument("--out-dir", default=None,
                    help="output release dir (default <repo>/data/annotations/pedalion/<release_id>)")
    ap.add_argument("--release-id", default="pedalion-v1", help="cog export release id (default pedalion-v1)")
    ap.add_argument("--hf-repo", default=HF_EXPORTS_REPO,
                    help="HF dataset repo the pointer stub records as the payload home")
    args = ap.parse_args()

    ped_root = Path(args.pedalion_root)
    xml_dir = ped_root / "public" / "xml"
    if not xml_dir.is_dir():
        sys.exit(f"Pedalion xml dir not found: {xml_dir}")
    repo_root = Path(__file__).resolve().parent.parent
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "data" / "annotations" / "pedalion" / args.release_id

    # Pin the upstream commit from the retained clone.
    import subprocess
    try:
        commit = subprocess.check_output(["git", "-C", str(ped_root), "rev-parse", "HEAD"],
                                         text=True).strip()
    except Exception:
        commit = "UNKNOWN"

    license_str = verify_license(ped_root)
    print(f"[pedalion-export] license (TREEBANK_LICENSE): {license_str}", flush=True)

    if not Path(args.glaux_metadata).is_file():
        sys.exit(f"[pedalion-export] ABORT: GLAUx metadata not found: {args.glaux_metadata} "
                 f"(needed to verify the literary scope; pass --glaux-metadata)")
    scope_audit = verify_glaux_scope(args.glaux_metadata)
    scope_audit["license"] = license_str
    print(f"[pedalion-export] GLAUx verified: {scope_audit['glaux_texts']} texts, "
          f"{scope_audit['glaux_pedalion_subsumed']} Pedalion-subsumed; "
          f"{len(LITERARY_WORKS)} literary works kept, Menander excluded", flush=True)

    glaux_all, _ = load_glaux_tlg_ids(args.glaux_metadata)

    streams = []
    buckets = {"PRO1": {"tokens": 0, "sentences": 0}, "PRO2": {"tokens": 0, "sentences": 0}}
    literary_subsumed_drop = {"tokens": 0, "sentences": 0}

    # Literary (8 works GLAUx lacks; Menander withheld).
    for stem, meta in LITERARY_WORKS.items():
        ws, dropped = process_literary(stem, meta, xml_dir / stem, glaux_all)
        literary_subsumed_drop["tokens"] += dropped["tokens"]
        literary_subsumed_drop["sentences"] += dropped["sentences"]
        streams.append(ws)

    # Example-sentence collections (PRO1/PRO2 dropped, GORMAN tagged).
    for stem in sorted(EXAMPLE_FILES):
        streams.append(process_examples(stem, xml_dir / stem, buckets))

    # Papyri, per Trismegistos document.
    for stem in sorted(PAPYRI_FILES):
        streams.extend(process_papyri(stem, xml_dir / stem))

    streams = [s for s in streams if s.records]
    streams.sort(key=lambda s: s.work_key)

    works = [ws.write(out_dir) for ws in streams]

    # Aggregate counts / provenance buckets.
    total_tokens = sum(w["tokens"] for w in works)
    total_sentences = sum(w["sentences"] for w in works)
    total_artificial = sum(w["artificial_nodes"] for w in works)
    gorman_tokens = sum(w["provenance_tokens"]["gorman"] for w in works)
    pedalion_tokens = sum(w["provenance_tokens"]["pedalion"] for w in works)
    ref_prov = {}
    for w in works:
        for k, v in w["ref_provenance_tokens"].items():
            ref_prov[k] = ref_prov.get(k, 0) + v

    # Menander (excluded) counts, for the report.
    men_root = ET.parse(xml_dir / MENANDER_FILE).getroot()
    men_sents = men_root.findall(".//sentence")
    men_counts = {"sentences": len(men_sents),
                  "tokens": sum(len(s.findall("word")) for s in men_sents)}

    # Deterministic content hash over the uncompressed per-work payloads.
    hasher = hashlib.sha256()
    for w in sorted(works, key=lambda x: x["work_key"]):
        hasher.update(f"{w['work_key']}:{w['sha256']}\n".encode("utf-8"))
    content_hash = "sha256:" + hasher.hexdigest()

    manifest = {
        "export": {
            "release_id": args.release_id,
            "contract": "docs/annotation-export-contract.md",
            "generated_by": "scripts/export_pedalion_annotations.py",
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content_hash": content_hash,
            "content_hash_method": (
                "sha256 over the newline-joined '<work_key>:<sha256-of-uncompressed-jsonl>' lines, "
                "work_key-sorted; excludes generated_at and gzip framing so it is reproducible on unchanged input"
            ),
            "pin_line": f"cog export {args.release_id}, {content_hash}",
            "record_layout": (
                "per-work JSONL under works/<work_key>.jsonl.gz (gzip mtime=0, deterministic); "
                "one token record per line. work_key is a CTS work id for literary works, tm<id> "
                "for papyri, and pedalion-<collection> for the example-sentence collections; "
                "works[].cts_urn is the work URN where one exists (null for papyri and collections)"
            ),
            "token_fields": {
                "id": "Pedalion native in-sentence token index; the integer 'head' points to (0 = root)",
                "form": "surface form, cog-normalized (see source.encoding_normalization)",
                "lemma": "lemma in Pedalion's native convention, verbatim except cog encoding normalization",
                "pos": "AGDT/Perseus part of speech (first character of the 9-char postag); not remapped",
                "morph": "Pedalion native 9-char AGDT/Perseus positional postag; not remapped",
                "head": "in-sentence id of the governing token (0 = root); scoped by sentence_id",
                "deprel": "AGDT/Perseus dependency relation (the 'relation' attribute); not remapped",
                "cts_urn": "CTS work URN the token's passage cites, where resolvable (null for papyri / Pedalion-internal source docs)",
                "locus": "passage citation within the cited work (Pedalion subdoc, decimal-comma normalized to dot); null where the source gives none",
                "doc": "the Pedalion source document_id (a TLG id, a Trismegistos number, or a Pedalion label); resolve via works[].source_docs",
                "sentence_id": "Pedalion native <sentence> id (the annotation unit), unique within the work stream",
                "analysis": "'manual' for all Pedalion tokens (manually annotated / corrected gold trees)",
                "provenance_tag": "'gorman' for GORMAN-prefix rows (docs/source-policy.md tag-don't-delete); 'pedalion' otherwise",
                "ref_provenance": "the raw Pedalion ref prefix (Leuven / PER / HARR / GORMAN): the sub-provenance of the row",
            },
            "counts": {
                "works_exported": len(works),
                "tokens": total_tokens,
                "sentences": total_sentences,
                "artificial_nodes": total_artificial,
                "provenance_tokens": {"pedalion": pedalion_tokens, "gorman": gorman_tokens},
                "ref_provenance_tokens": dict(sorted(ref_prov.items())),
            },
        },
        "source": {
            "name": "Pedalion Trees",
            "repo": "https://github.com/perseids-publications/pedalion-trees",
            "commit": commit,
            "retained_clone": _tilde(ped_root),
            "license_upstream": license_str,
            "license_note": ("TREEBANK_LICENSE (CC BY-SA 4.0) governs the treebank data; the "
                             "repo's separate MIT LICENSE covers the site code, not the data."),
            "format": "AGDT ('aldt') dependency treebank XML, public/xml/*.xml",
            "annotation_method": (
                "Manually annotated / corrected gold dependency trees (Arethusa/Perseids), following the "
                "Perseus Dependency Treebank guidelines; annotation='manual' for every token."
            ),
            "provenance_note": (
                "Pedalion mixes provenances, discriminated by the per-token ref prefix "
                "(Leuven / PER / GORMAN / PRO1 / PRO2 / HARR). Under docs/source-policy.md: PRO1/PRO2 are "
                "tier-1 PROIEL data (re-exported PROIEL trees) and are DROPPED; GORMAN rows are INCLUDED but "
                "tagged provenance_tag='gorman' (tag-don't-delete); Leuven/PER/HARR are INCLUDED as "
                "provenance_tag='pedalion' with the ref prefix kept in ref_provenance."
            ),
            "lemma_convention": (
                "Preserved verbatim (cog does not normalize lemma conventions). Pedalion lemmas carry "
                "homograph-disambiguation digits (e.g. 'ξένος2'); only cog encoding normalization "
                "(NFC, apostrophe, sigma) is applied to the lemma string."
            ),
            "encoding_normalization": {
                "unicode": "NFC",
                "apostrophes_to_U+2019": ["U+02BC", "U+0027", "U+2018", "U+2019"],
                "sigma": "lunate ϲ/Ϲ -> σ/Σ; final ς word-finally, medial σ otherwise (applied to form and lemma)",
            },
            "citation": ("Toon Van Hal, Alek Keersmaekers et al. Pedalion Trees. Perseids Project. "
                         "https://github.com/perseids-publications/pedalion-trees (CC BY-SA 4.0)."),
        },
        "policy": {
            "proiel_tier1_dropped": {
                "rule": "docs/source-policy.md: PRO1/PRO2 ref prefixes = re-exported PROIEL trees = tier-1 PROIEL data, banned in every role.",
                "pro1_tokens": buckets["PRO1"]["tokens"], "pro1_sentences": buckets["PRO1"]["sentences"],
                "pro2_tokens": buckets["PRO2"]["tokens"], "pro2_sentences": buckets["PRO2"]["sentences"],
                "total_tokens_dropped": buckets["PRO1"]["tokens"] + buckets["PRO2"]["tokens"],
                "located_in": sorted(EXAMPLE_FILES),
            },
            "gorman_tagged": {
                "rule": "docs/source-policy.md: Gorman is included but tagged provenance=gorman (tag-don't-delete).",
                "tokens": gorman_tokens,
            },
            "clean_kept": {
                "rule": "Leuven/PER/HARR rows kept as provenance=pedalion with ref_provenance sub-field.",
                "tokens": pedalion_tokens,
                "by_ref_provenance": {k: v for k, v in sorted(ref_prov.items()) if k != "GORMAN"},
            },
            "menander_excluded": {
                "file": MENANDER_FILE, "tlg": MENANDER_TLG,
                "reason": ("Edition-rights safety: the Menander Dyskolos treebank is based on the 1958 Bodmer "
                           "edition, and the annotation's `form` tokens reconstruct that text, so emitting the "
                           "annotation would redistribute the 1958 edition's text. Default EXCLUDE."),
                "withheld_tokens": men_counts["tokens"], "withheld_sentences": men_counts["sentences"],
            },
            "glaux_dedup": scope_audit,
            "glaux_subsumed_sentences_dropped": literary_subsumed_drop,
            "glaux_subsumed_note": (
                "Within an in-scope literary file, sentences whose document_id is a canonical TLG already in "
                "GLAUx are dropped (only sappho.xml's 0009-002 Epigrammata); item 1e (GLAUx) owns them."
            ),
        },
        "consumers": (
            "This is annotation-consumption queue item 1c (docs/annotation-export-contract.md). "
            "dilemma pins this export by export.pin_line and filters provenance_tag='gorman' at read time."
        ),
        "works": works,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")
    with open(out_dir / "pedalion_scope_audit.json", "w", encoding="utf-8") as fh:
        json.dump({"scope": scope_audit,
                   "literary_works": LITERARY_WORKS,
                   "menander_excluded": manifest["policy"]["menander_excluded"]},
                  fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    stub_path = out_dir.parent / f"{args.release_id}.json"
    with open(stub_path, "w", encoding="utf-8") as fh:
        json.dump(make_pointer_stub(manifest, args.hf_repo), fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"[pedalion-export] pointer stub -> {stub_path}", flush=True)

    print(f"[pedalion-export] wrote {len(works)} works, {total_tokens:,} tokens "
          f"({total_sentences:,} sentences) to {out_dir}", flush=True)
    print(f"[pedalion-export] policy: dropped PRO1={buckets['PRO1']['tokens']} + "
          f"PRO2={buckets['PRO2']['tokens']} tokens; GORMAN tagged={gorman_tokens}; "
          f"clean kept (pedalion)={pedalion_tokens}", flush=True)
    print(f"[pedalion-export] Menander withheld: {men_counts['tokens']} tokens; "
          f"GLAUx-subsumed sappho sentences dropped: {literary_subsumed_drop['tokens']} tokens", flush=True)
    print(f"[pedalion-export] pin line: cog export {args.release_id}, {content_hash}", flush=True)


if __name__ == "__main__":
    main()
