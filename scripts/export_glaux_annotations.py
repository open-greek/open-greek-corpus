#!/usr/bin/env python3
"""Export the GLAUx corpus as cog's standardized annotation export (queue item 1e, GLAUx half).

This produces the annotation export defined by docs/annotation-export-contract.md:
per-work, CTS-URN-keyed streams of token records, with cog-owned encoding
normalization and the source-native AGDT/Perseus tagset and lemmas preserved
verbatim. dilemma and other consumers pin this by "cog export <release_id>,
hash <content_hash>".

Source: the GLAUx corpus (github.com/alekkeersmaekers/glaux), ~20M tokens of
Ancient Greek (8th century BCE - roughly 4th century CE) annotated for
morphology, lemmas, and AGDT-style dependency syntax, plus the newer semantic
layers (animacy, WordNet 3.0 senses). The retained clone is pinned by commit
(docs/pinning-discipline.md); the run aborts if the clone is not at the pin.
Each xml/<id>.xml is one document of <sentence analysis="manual|auto"> elements
whose <word> children carry id/form/lemma/postag/head/relation and per-token
citation attributes (div_book / div_section / line and ~50 other genre-specific
div_* attributes).

Provenance / policy (docs/source-policy.md):
  - PROIEL (tier 1, banned in every role): the 25 works whose metadata.txt marks
    TREEBANK_ANNOTATIONS='PROIEL' are DROPPED entirely and recorded in the scope
    audit with their metadata token counts. Re-derived from metadata at run time.
  - NonCommercial: works whose per-work SOURCE_LICENSE carries an NC (or ND)
    clause are EXCLUDED and recorded in the scope audit. Repo policy serves no
    NC-licensed material; oga-v1 set the precedent by excluding its single
    BY-NC-SA file. (scripts/ingest_glaux_pollux.py's case, GLAUx's own CC BY-SA
    corpus license governing a reconstructed public-domain base text, is a
    different question from re-exporting an annotation layer whose per-work
    SOURCE_LICENSE is NC.) Re-derived from metadata at run time, not hardcoded.
  - Unclear licenses: works whose SOURCE_LICENSE is neither NC nor on the open
    allowlist (CC BY / CC BY-SA any version, or 'NA' under the GLAUx corpus's
    own CC BY-SA) are EXCLUDED as unclear and recorded in the scope audit. The
    export is aggregated and published under CC BY-SA: OpenEdition's license is
    not a clean open license, and GPL text under a CC BY-SA label would
    misstate its terms; unknown or unclear licenses are excluded, not served.
    Classified from the license string at run time.
  - Gorman (tag, don't delete): within the 40 works metadata credits to
    "Vanessa Gorman's Ancient Greek Prose Dependency Treebanks", sentences with
    analysis="manual" are tagged provenance_tag='gorman'; auto sentences in
    those works, and every sentence elsewhere, are provenance_tag='glaux'.
    Gorman is dilemma's held-out gold set; dilemma filters provenance_tag=
    'gorman' at read time (the consumer's rule, not cog's).
  - Everything else in GLAUx is either homogenized manual annotation from open
    treebanks (Perseus AGDT / Pedalion / Harrington; analysis="manual") or the
    output of GLAUx's own models (analysis="auto"), which are trained on those
    treebanks plus PROIEL, making the auto layer tier-2 under source-policy.md
    (PROIEL-model output: acceptable, dispreferred), not tier-1 PROIEL data.
    The per-work TREEBANK_ANNOTATIONS credit is carried in the manifest.

Work identity: GLAUx ids "NNNN-NNN" map to greekLit CTS works "tlgNNNN.tlgNNN"
(verified against data/tlg_crosswalk.tsv for known works). 23 documents carry a
letter suffix ("0007-051a"): parts or parallel recensions of one TLG work. Those
are merged into their base CTS work's stream in letter order; every token's
`doc` field records the GLAUx document id, and (doc, sentence_id) is the unique
sentence key. Ids that fit neither shape are excluded and reported, never
guessed.

Locus: GLAUx cites tokens with heterogeneous per-genre citation attributes
(div_book, div_chapter, div_section, line, div_stephanus_section, ...), where a
finer attribute normally embeds its ancestors as a dotted prefix (Thucydides
div_section="1.1.1"). The exporter ranks the attributes finest-first (a fixed,
audited table; unknown attributes abort the run), takes each token's
finest-ranked value as the locus, and per work checks it for ambiguity against
the coarser logical attributes: if the same value occurs under two different
coarser contexts (e.g. the same page number in two volumes), the whole work
switches to composite loci ("volume.page"). Each work's manifest entry records
the citation chain, the mode, and the fallback/missing counts.

cog owns encoding normalization (NFC - the GLAUx corpus is NFD; elision
apostrophes -> U+2019; standard final/medial sigma), applied to form and lemma.
cog does NOT normalize lemma conventions: GLAUx's homogenized AGDT-style
dictionary headwords are preserved verbatim (no homograph digits observed).
form_original, the pre-cleanup source form with its editorial marks, is carried
NFC-only so the marks stay verbatim.

The export is deterministic: gzip is written with mtime=0 and the content hash
is computed over the uncompressed per-work payloads, so re-running on unchanged
input reproduces byte-identical files and the same content_hash.

Storage (docs/annotation-export-contract.md, "Storage"): the payload this writes
is NOT committed to git. It is uploaded to the Hugging Face dataset repo with
scripts/upload_annotation_export.py; git tracks this exporter plus the pointer
stub written next to the release dir (data/annotations/glaux/<release_id>.json).
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
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
from annotation_encoding import nfc, normalize

# The HF dataset repo that holds export payloads (docs/annotation-export-contract.md,
# "Storage"); the release id is the path in the repo. upload_annotation_export.py
# shares this default.
HF_EXPORTS_REPO = "ciscoriordan/open-greek-corpus-annotation-exports"

# The retained upstream clone is pinned by commit SHA (docs/pinning-discipline.md).
UPSTREAM_COMMIT = "b077d8f6ff429a5c7245954bc16bb7d1d7948823"
UPSTREAM_REPO = "https://github.com/alekkeersmaekers/glaux"

# metadata.txt TREEBANK_ANNOTATIONS values that drive the source policy.
PROIEL_CREDIT = "PROIEL"
GORMAN_CREDIT = "Vanessa Gorman's Ancient Greek Prose Dependency Treebanks"

# Policy guards: these must be re-derived from metadata at run time; the
# sentinels below only assert the derivation still finds the known cases, so a
# wrong or drifted metadata file cannot silently ship banned material.
PROIEL_SENTINEL = "0016-001"     # Herodotus, the largest PROIEL-marked work
PROIEL_EXPECTED_COUNT = 25
NC_SENTINEL = "0096-002a"        # Aesop Fabulae, CC BY-NC-ND 3.0, the largest NC work
UNCLEAR_SENTINELS = {"0237-003", "2034-006"}  # OpenEdition Books License; GPL
GORMAN_SENTINEL = "0543-001"     # Polybius
GORMAN_EXPECTED_COUNT = 40

_GLAUX_ID_RE = re.compile(r"^(\d{4})-(\d{3})([a-z]?)$")


def _tilde(path):
    """Home-relativize a path (~/...) so published manifests carry no personal
    absolute path (matches the other exporters' retained_clone convention)."""
    p = str(path)
    home = os.path.expanduser("~")
    return "~" + p[len(home):] if p.startswith(home) else p


# --- License classification (run-time, from SOURCE_LICENSE strings) --------

def is_noncommercial(license_str: str) -> bool:
    """True when a metadata SOURCE_LICENSE carries an NC or ND clause. Same
    detector policy as the OGA exporter's PTA audit. 'NA' (unspecified) is not
    NonCommercial; the GLAUx corpus's own CC BY-SA 4.0 governs those."""
    t = (license_str or "").lower()
    return ("by-nc" in t) or ("-nc-" in t) or ("by-nd" in t) or ("-nd-" in t) or ("noncommercial" in t)


# The allowlist of per-work source licenses this export may aggregate: CC BY /
# CC BY-SA of any version (both 'CC BY-SA 4.0' and 'CC-BY-SA 3.0' spellings
# occur), plus 'NA' (unspecified source; the GLAUx corpus's own CC BY-SA
# governs). Anything neither allowlisted nor NC is excluded as unclear: the
# export is aggregated and published under CC BY-SA, so OpenEdition's license
# (not a clean open license) and GPL-licensed text (whose terms a CC BY-SA
# label would misstate) are excluded rather than served, matching the corpus
# rule that unknown or unclear licenses are excluded.
_OPEN_LICENSE_RE = re.compile(r"^CC[- ]BY([- ]SA)?[- ][0-9]\.[0-9]$")


def license_class(license_str: str) -> str:
    """'open' | 'noncommercial' | 'unclear' for a metadata SOURCE_LICENSE."""
    s = (license_str or "").strip()
    if is_noncommercial(s):
        return "noncommercial"
    if s == "NA" or _OPEN_LICENSE_RE.match(s):
        return "open"
    return "unclear"


# --- Citation attributes / locus construction ------------------------------

# Every citation attribute observed in the pinned GLAUx corpus, ranked finest
# first within three classes. LOGICAL attributes are the text's own citation
# hierarchy (a finer value normally embeds its ancestors as a dotted prefix,
# e.g. div_section="1.1.1" under div_chapter="1.1"); canonical edition schemes
# that standard scholarly citation uses (Stephanus sections for Plato, Stephanus
# pages for Plutarch's Moralia, Bekker pages for Aristotle, Casaubon pages for
# Athenaeus) are ranked inside the logical list at the granularity they
# represent. ALT attributes are alternative numberings; EDITION attributes are
# print-edition page/folio anchors. ALT/EDITION are used for the locus only when
# a work has nothing ranked above them, and never as disambiguation context.
# An attribute not in this table aborts the run (report, don't guess).
LOGICAL_ATTRS = [
    "div_sentence",            # ranked above line: Menander Sententiae's line is a constant 1
    "line",
    "div_subsection", "div_subchapter", "div_subfragment",
    "div_stephanus_section",   # Plato: the canonical '17a' citation
    "div_paragraph", "div_aphorism", "div_number", "div_version",
    "div_section", "div_sententia", "div_entry",
    "div_chapter",
    "div_stephpage",           # Plutarch Moralia: below chapter/section (cog's corpus cites those)
    "div_bekker_page",         # Aristotle: canonical where no chapter exists
    "div_casaubonpage",        # Athenaeus: below div_chapter (Kaibel book.chapter preferred)
    "div_strophe",
    "div_fragment", "div_fable", "div_fabula", "div_oracle",
    "div_ode", "div_psalm", "div_homily", "div_epigram", "div_poem", "div_elegy",
    "div_letter", "div_epistle", "div_oration", "div_exordium", "div_speech",
    "div_tetralogy", "div_column",
    "div_part", "div_book",
]
# Structural containers eligible as composite-locus context (the coarse levels a
# finer numbering can restart under). Canonical page schemes (Stephanus, Bekker,
# Casaubon pages) and verse groupings (strophe/elegy/epigram, whose lines never
# restart) are deliberately NOT context: they anchor editions, they do not scope
# numbering, and they would only pollute composite loci.
CONTEXT_ATTRS = [
    "div_section", "div_sententia", "div_entry", "div_chapter",
    "div_fragment", "div_fable", "div_fabula", "div_oracle",
    "div_ode", "div_psalm", "div_homily", "div_poem",
    "div_letter", "div_epistle", "div_oration", "div_exordium", "div_speech",
    "div_tetralogy", "div_column",
    "div_part", "div_book", "div_work", "div_volume",
]
ALT_ATTRS = ["div_altsection", "div_altchapter", "div_altnumbering", "div_section2"]
EDITION_ATTRS = [
    "div_stephanus_page", "div_perseus_section", "div_jebb_page", "div_page",
    "div_ed1page", "div_ed2page", "div_ed1folio", "div_ms1folio",
    "div_manuscriptpage", "div_reiskpage", "div_olpage", "div_oleariuspage",
    "div_reitz_page", "div_orgpage", "div_mueller", "div_blancard", "div_pat2",
]
# div_volume / div_work are container labels, not citations: they rank below
# even the edition pages (so a PG volume's page numbers, not the constant volume
# number, become the locus) but stay eligible as composite context above.
CONTAINER_ONLY_ATTRS = ["div_volume", "div_work"]
CITATION_RANK = LOGICAL_ATTRS + ALT_ATTRS + EDITION_ATTRS + CONTAINER_ONLY_ATTRS
_RANK_INDEX = {a: i for i, a in enumerate(CITATION_RANK)}
_LOGICAL_SET = set(LOGICAL_ATTRS)

# <word> attributes that are not citation attributes. Anything else that looks
# like a citation attribute (div_* or line) but is missing from CITATION_RANK
# aborts the run. speaker (drama speaker labels), name/namId (two works'
# named-entity marks) are not carried; they remain available upstream.
NON_CITATION_ATTRS = {
    "id", "form", "form_original", "lemma", "postag", "head", "relation",
    "artificial", "animacy", "sense", "speaker", "name", "namId",
}


def token_citation(word_attrib: dict) -> dict:
    """The token's citation attributes {attr: value}; aborts on unknown ones."""
    cite = {}
    for k, v in word_attrib.items():
        if k in NON_CITATION_ATTRS:
            continue
        if k not in _RANK_INDEX:
            sys.exit(f"[glaux-export] ABORT: unknown citation attribute {k!r} "
                     f"(value {v!r}); add it to CITATION_RANK deliberately")
        cite[k] = v
    return cite


def resolve_locus(cite: dict):
    """(attr_used, value) for the finest-ranked citation attribute present, or
    (None, None) when the token carries no citation attribute."""
    best = None
    for a, v in cite.items():
        i = _RANK_INDEX[a]
        if best is None or i < best[0]:
            best = (i, a, v)
    if best is None:
        return None, None
    return best[1], best[2]


def disamb_context(cite: dict, attr_used: str, value: str) -> tuple:
    """The coarse-to-fine tuple of container attribute values (CONTEXT_ATTRS)
    ranked coarser than attr_used that are NOT already embedded in the locus
    value as a dotted prefix. This is the context the ambiguity check compares;
    in composite mode it becomes the locus prefix."""
    used_rank = _RANK_INDEX[attr_used]
    parts: list[str] = []
    # coarse -> fine so a finer context value can refine a coarser one
    for a in reversed(CONTEXT_ATTRS):
        if _RANK_INDEX[a] <= used_rank:
            continue
        c = cite.get(a)
        if c is None:
            continue
        if value == c or value.startswith(c + "."):
            continue  # already embedded in the locus value
        if parts and (c == parts[-1] or c.startswith(parts[-1] + ".")):
            parts[-1] = c  # refines the previous context part
        elif parts and parts[-1].startswith(c + "."):
            continue       # coarser than what we already hold
        else:
            parts.append(c)
    return tuple(parts)


# --- Token record ----------------------------------------------------------

TOKEN_FIELD_ORDER = [
    "id", "form", "lemma", "pos", "morph", "head", "deprel",
    "locus", "sentence_id", "doc",
    "analysis", "provenance_tag",
    "artificial", "form_original", "animacy", "sense",
]


def build_token_record(w: dict, sentence_id: int, doc: str, analysis: str,
                       provenance_tag: str, locus):
    postag = w.get("postag")
    lemma = w.get("lemma")
    head = w.get("head")
    try:
        head = int(head)
    except (TypeError, ValueError):
        pass
    tok_id = w.get("id")
    try:
        tok_id = int(tok_id)
    except (TypeError, ValueError):
        pass
    return {
        "id": tok_id,
        "form": normalize(w.get("form") or ""),
        "lemma": normalize(lemma) if lemma is not None else None,
        "pos": postag[0] if postag else None,
        "morph": postag or None,
        "head": head,
        "deprel": w.get("relation"),
        "locus": locus,
        "sentence_id": sentence_id,
        "doc": doc,
        "analysis": analysis,
        "provenance_tag": provenance_tag,
        "artificial": w.get("artificial"),
        "form_original": nfc(w.get("form_original")),
        "animacy": w.get("animacy"),
        "sense": w.get("sense"),
    }


# --- Per-document parsing --------------------------------------------------

def parse_document(xml_path: Path, doc_id: str):
    """Yield (sentence_id, analysis, [word attrib dicts]) in document order."""
    for _event, el in ET.iterparse(str(xml_path), events=("end",)):
        if el.tag != "sentence":
            continue
        analysis = el.get("analysis")
        if analysis not in ("manual", "auto"):
            sys.exit(f"[glaux-export] ABORT: {doc_id} sentence {el.get('id')} has "
                     f"unexpected analysis={analysis!r}")
        if el.get("document_id") != doc_id:
            sys.exit(f"[glaux-export] ABORT: {xml_path.name} carries document_id="
                     f"{el.get('document_id')!r}, expected {doc_id!r}")
        yield int(el.get("id")), analysis, [dict(w.attrib) for w in el.findall("word")]
        el.clear()


# --- Per-work export -------------------------------------------------------

class WorkExport:
    """One CTS work = one or more GLAUx documents (letter-suffix parts merged
    in letter order). Two passes over the collected sentences: first resolve
    every token's locus and detect ambiguity, then emit."""

    def __init__(self, work_key: str, docs: list[dict]):
        self.work_key = work_key
        self.cts_urn = f"urn:cts:greekLit:{work_key}"
        self.docs = docs  # metadata rows, letter order
        self.sentences = []  # (doc_id, sentence_id, analysis, provenance, words)
        self.chain_attrs = set()

    def load(self, xml_dir: Path, gorman_ids: set):
        for row in self.docs:
            gid = row["TLG"]
            is_gorman = gid in gorman_ids
            for sent_id, analysis, words in parse_document(xml_dir / f"{gid}.xml", gid):
                prov = "gorman" if (is_gorman and analysis == "manual") else "glaux"
                self.sentences.append((gid, sent_id, analysis, prov, words))
                for w in words:
                    self.chain_attrs.update(token_citation(w).keys())

    def write(self, out_dir: Path):
        # Pass 1: resolve loci and detect genuine ambiguity. A locus value is
        # ambiguous within a document when its numbering RESTARTS: it occurs in
        # two or more separate document-order runs AND under differing container
        # contexts (e.g. the same page number in two volumes). A value that
        # merely straddles a container boundary (one contiguous run, two
        # contexts, like a Bekker page crossing a book break) stays unambiguous.
        # Merged letter-suffix documents are checked per document: within a
        # merged work the citation namespace is per doc (the `doc` field).
        primary_rank = min((_RANK_INDEX[a] for a in self.chain_attrs), default=None)
        resolved = []  # per sentence: [(attr_used, value, context), ...]
        seen: dict[tuple, list] = {}  # (doc, value) -> [first_ctx, ctx_differ, runs]
        last_key = None
        composite = False
        for gid, _sid, _analysis, _prov, words in self.sentences:
            row = []
            for w in words:
                cite = token_citation(w)
                attr_used, value = resolve_locus(cite)
                ctx = disamb_context(cite, attr_used, value) if attr_used else ()
                row.append((attr_used, value, ctx))
                if value is not None:
                    key = (gid, value)
                    state = seen.get(key)
                    if state is None:
                        state = seen[key] = [ctx, False, 0]
                    if ctx != state[0]:
                        state[1] = True
                    if key != last_key:
                        state[2] += 1
                    if state[1] and state[2] >= 2:
                        composite = True
                    last_key = key
            resolved.append(row)

        # Pass 2: emit token records deterministically.
        buf = io.StringIO()
        n_tokens = n_artificial = 0
        n_missing = n_fallback = 0
        sent_counts = {"manual": 0, "auto": 0}
        tok_counts = {"manual": 0, "auto": 0}
        prov_tokens = {"glaux": 0, "gorman": 0}
        prov_sents = {"glaux": 0, "gorman": 0}
        for (gid, sid, analysis, prov, words), row in zip(self.sentences, resolved):
            sent_counts[analysis] += 1
            prov_sents[prov] += 1
            for w, (attr_used, value, ctx) in zip(words, row):
                if value is None:
                    locus = None
                    n_missing += 1
                else:
                    locus = ".".join(ctx + (value,)) if composite else value
                    if primary_rank is not None and attr_used and _RANK_INDEX[attr_used] != primary_rank:
                        n_fallback += 1
                rec = build_token_record(w, sid, gid, analysis, prov, locus)
                if rec["artificial"]:
                    n_artificial += 1
                tok_counts[analysis] += 1
                prov_tokens[prov] += 1
                buf.write(json.dumps({k: rec[k] for k in TOKEN_FIELD_ORDER}, ensure_ascii=False))
                buf.write("\n")
                n_tokens += 1
        payload = buf.getvalue().encode("utf-8")
        sha = hashlib.sha256(payload).hexdigest()
        out_path = out_dir / "works" / f"{self.work_key}.jsonl.gz"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as gz:
                gz.write(payload)

        chain = [a for a in CITATION_RANK if a in self.chain_attrs]
        entry = {
            "work_key": self.work_key,
            "cts_urn": self.cts_urn,
            "glaux_ids": [row["TLG"] for row in self.docs],
            "file": out_path.name,
            "author": self.docs[0]["AUTHOR_STANDARD"],
            "title": self.docs[0]["TITLE_STANDARD"],
            "genre": self.docs[0]["GENRE_STANDARD"],
            "tokens": n_tokens,
            "sentences": len(self.sentences),
            "sentences_by_analysis": sent_counts,
            "tokens_by_analysis": tok_counts,
            "provenance_sentences": prov_sents,
            "provenance_tokens": prov_tokens,
            "artificial_nodes": n_artificial,
            "locus_scheme": {
                "citation_attrs": chain,
                "primary": chain[0] if chain else None,
                "mode": ("composite" if composite else ("final" if chain else "none")),
                "fallback_tokens": n_fallback,
                "missing_tokens": n_missing,
            },
            "source": sorted({row["SOURCE"] for row in self.docs}),
            "source_license": sorted({row["SOURCE_LICENSE"] for row in self.docs}),
            "sha256": sha,
        }
        credits = sorted({row["TREEBANK_ANNOTATIONS"] for row in self.docs} - {"NA"})
        if credits:
            entry["treebank_annotations"] = credits
            links = sorted({row["ORIGINAL_TREEBANK_LINK"] for row in self.docs} - {"NA", ""})
            if links:
                entry["original_treebank_link"] = links
        if len(self.docs) > 1:
            entry["docs"] = [
                {"glaux_id": row["TLG"], "title": row["TITLE_STANDARD"],
                 "source_license": row["SOURCE_LICENSE"],
                 "treebank_annotations": row["TREEBANK_ANNOTATIONS"]}
                for row in self.docs
            ]
        return entry


# --- Metadata / scope ------------------------------------------------------

def load_metadata(metadata_path: Path) -> list[dict]:
    with open(metadata_path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows or "TREEBANK_ANNOTATIONS" not in rows[0] or "TLG" not in rows[0]:
        sys.exit(f"[glaux-export] ABORT: {metadata_path} is not the GLAUx metadata.txt")
    return rows


def classify_works(rows: list[dict], xml_dir: Path):
    """Apply the source policy and the CTS mapping. Returns (kept, dropped_proiel,
    excluded_nc, excluded_unclear, unmapped, gorman_ids); kept maps work_key ->
    [metadata rows] in letter order."""
    proiel, nc, unclear, unmapped = [], [], [], []
    gorman_ids = set()
    kept: dict[str, list[dict]] = {}
    for row in rows:
        gid = row["TLG"]
        if not (xml_dir / f"{gid}.xml").is_file():
            sys.exit(f"[glaux-export] ABORT: metadata row {gid} has no xml/{gid}.xml")
        if row["TREEBANK_ANNOTATIONS"] == PROIEL_CREDIT:
            proiel.append(row)
            continue
        lclass = license_class(row["SOURCE_LICENSE"])
        if lclass == "noncommercial":
            nc.append(row)
            continue
        if lclass == "unclear":
            unclear.append(row)
            continue
        m = _GLAUX_ID_RE.match(gid)
        if not m:
            unmapped.append(row)
            continue
        if row["TREEBANK_ANNOTATIONS"] == GORMAN_CREDIT:
            gorman_ids.add(gid)
        work_key = f"tlg{m.group(1)}.tlg{m.group(2)}"
        kept.setdefault(work_key, []).append(row)
    for work_key, group in kept.items():
        # Letter order = document order. A plain id sorts before its letter parts,
        # which matches GLAUx's own sequencing (verified: 0007-082 is Stephanus
        # 208b-236e, 0007-082a is 236f-240b, 0007-082b is 240c-242d; together they
        # are cog's tlg0007.tlg082, 'Apophthegmata Laconica sp. 208b-242d').
        group.sort(key=lambda r: r["TLG"])
    return kept, proiel, nc, unclear, unmapped, gorman_ids


def guard_policy_sets(proiel, nc, unclear, gorman_ids):
    proiel_ids = {r["TLG"] for r in proiel}
    nc_ids = {r["TLG"] for r in nc}
    unclear_ids = {r["TLG"] for r in unclear}
    if PROIEL_SENTINEL not in proiel_ids:
        sys.exit(f"[glaux-export] ABORT: {PROIEL_SENTINEL} (known PROIEL work) not detected")
    if len(proiel_ids) != PROIEL_EXPECTED_COUNT:
        sys.exit(f"[glaux-export] ABORT: PROIEL set drifted: {len(proiel_ids)} works, "
                 f"expected {PROIEL_EXPECTED_COUNT}; review metadata before shipping")
    if NC_SENTINEL not in nc_ids:
        sys.exit(f"[glaux-export] ABORT: {NC_SENTINEL} (known NC work) not detected as NonCommercial")
    if not UNCLEAR_SENTINELS <= unclear_ids:
        sys.exit(f"[glaux-export] ABORT: known unclear-license works {sorted(UNCLEAR_SENTINELS - unclear_ids)} "
                 f"not detected; the license allowlist drifted")
    if GORMAN_SENTINEL not in gorman_ids:
        sys.exit(f"[glaux-export] ABORT: {GORMAN_SENTINEL} (known Gorman work) not detected")
    if len(gorman_ids) != GORMAN_EXPECTED_COUNT:
        sys.exit(f"[glaux-export] ABORT: Gorman set drifted: {len(gorman_ids)} works, "
                 f"expected {GORMAN_EXPECTED_COUNT}; review metadata before shipping")


def policy_row(row: dict, reason: str) -> dict:
    m = _GLAUX_ID_RE.match(row["TLG"])
    return {
        "glaux_id": row["TLG"],
        "cts_urn": f"urn:cts:greekLit:tlg{m.group(1)}.tlg{m.group(2)}" if m else None,
        "author": row["AUTHOR_STANDARD"],
        "title": row["TITLE_STANDARD"],
        "source_license": row["SOURCE_LICENSE"],
        "treebank_annotations": row["TREEBANK_ANNOTATIONS"],
        "tokens_metadata": int(row["TOKENS"]),
        "reason": reason,
    }


# --- Pointer stub ----------------------------------------------------------

def make_pointer_stub(manifest: dict, hf_repo: str) -> dict:
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
                        "manifest.json and glaux_scope_audit.json"),
            "note": ("docs/annotation-export-contract.md, 'Storage': export payloads "
                     "live on the Hub; git tracks the exporter script and this pointer "
                     "stub only. Regenerate locally with "
                     "scripts/export_glaux_annotations.py, publish with "
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
            "retained_clone": manifest["source"]["retained_clone"],
            "note": "cog pins the upstream; consumers pin only pin_line (docs/pinning-discipline.md)",
        },
    }


# --- Main ------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--glaux-root",
                    default=os.environ.get("GLAUX_DIR", os.path.expanduser("~/Documents/glaux")),
                    help="retained GLAUx clone (default $GLAUX_DIR or ~/Documents/glaux)")
    ap.add_argument("--out-dir", default=None,
                    help="output release dir (default <repo>/data/annotations/glaux/<release_id>)")
    ap.add_argument("--release-id", default="glaux-v1", help="cog export release id (default glaux-v1)")
    ap.add_argument("--limit", type=int, default=None, help="export only the first N works (smoke test)")
    ap.add_argument("--works", nargs="*", default=None,
                    help="export only these works, by work_key or GLAUx id (smoke test)")
    ap.add_argument("--hf-repo", default=HF_EXPORTS_REPO,
                    help="HF dataset repo the pointer stub records as the payload home")
    args = ap.parse_args()

    glaux_root = Path(args.glaux_root)
    xml_dir = glaux_root / "xml"
    metadata_path = glaux_root / "metadata.txt"
    if not xml_dir.is_dir() or not metadata_path.is_file():
        sys.exit(f"[glaux-export] ABORT: {glaux_root} is not a GLAUx clone (xml/ + metadata.txt)")
    repo_root = Path(__file__).resolve().parent.parent
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "data" / "annotations" / "glaux" / args.release_id

    # Verify the retained clone is at the pinned commit (docs/pinning-discipline.md).
    head = None
    if (glaux_root / ".git").exists():
        import subprocess
        try:
            head = subprocess.check_output(["git", "-C", str(glaux_root), "rev-parse", "HEAD"],
                                           text=True).strip()
        except Exception:
            head = None
    if head != UPSTREAM_COMMIT:
        sys.exit(f"[glaux-export] ABORT: clone at {head} != pinned {UPSTREAM_COMMIT}; "
                 f"update UPSTREAM_COMMIT deliberately if the upstream pin is meant to move")

    rows = load_metadata(metadata_path)
    kept, proiel, nc, unclear, unmapped, gorman_ids = classify_works(rows, xml_dir)
    guard_policy_sets(proiel, nc, unclear, gorman_ids)
    print(f"[glaux-export] metadata: {len(rows)} documents; policy: "
          f"{len(proiel)} PROIEL dropped, {len(nc)} NonCommercial excluded, "
          f"{len(unclear)} unclear-license excluded, "
          f"{len(gorman_ids)} Gorman-credited, {len(unmapped)} unmapped ids", flush=True)
    if unmapped:
        print(f"[glaux-export] WARNING: ids not matching NNNN-NNN[a-z] excluded "
              f"(report, don't guess): {[r['TLG'] for r in unmapped]}", flush=True)

    work_keys = sorted(kept)
    if args.works:
        wanted = set(args.works)
        work_keys = [k for k in work_keys
                     if k in wanted or any(r["TLG"] in wanted for r in kept[k])]
    if args.limit:
        work_keys = work_keys[: args.limit]

    works: list[dict] = []
    totals = {"tokens": 0, "sentences": 0, "artificial": 0, "missing": 0, "fallback": 0}
    sent_counts = {"manual": 0, "auto": 0}
    tok_counts = {"manual": 0, "auto": 0}
    prov_tokens = {"glaux": 0, "gorman": 0}
    prov_sents = {"glaux": 0, "gorman": 0}
    composite_works = 0
    for i, work_key in enumerate(work_keys, 1):
        we = WorkExport(work_key, kept[work_key])
        we.load(xml_dir, gorman_ids)
        entry = we.write(out_dir)
        works.append(entry)
        totals["tokens"] += entry["tokens"]
        totals["sentences"] += entry["sentences"]
        totals["artificial"] += entry["artificial_nodes"]
        totals["missing"] += entry["locus_scheme"]["missing_tokens"]
        totals["fallback"] += entry["locus_scheme"]["fallback_tokens"]
        for k in ("manual", "auto"):
            sent_counts[k] += entry["sentences_by_analysis"][k]
            tok_counts[k] += entry["tokens_by_analysis"][k]
        for k in ("glaux", "gorman"):
            prov_tokens[k] += entry["provenance_tokens"][k]
            prov_sents[k] += entry["provenance_sentences"][k]
        if entry["locus_scheme"]["mode"] == "composite":
            composite_works += 1
        if i % 100 == 0 or i == len(work_keys):
            print(f"[glaux-export] {i}/{len(work_keys)} works ... {totals['tokens']:,} tokens", flush=True)

    # Deterministic content hash over the uncompressed per-work payloads.
    hasher = hashlib.sha256()
    for w in sorted(works, key=lambda x: x["work_key"]):
        hasher.update(f"{w['work_key']}:{w['sha256']}\n".encode("utf-8"))
    content_hash = "sha256:" + hasher.hexdigest()

    license_tally: dict[str, int] = {}
    for row in rows:
        license_tally[row["SOURCE_LICENSE"]] = license_tally.get(row["SOURCE_LICENSE"], 0) + 1

    UNCLEAR_RULE = (
        "The export is aggregated and published under CC BY-SA, so only works whose per-work "
        "SOURCE_LICENSE is on the open allowlist (CC BY / CC BY-SA any version, or 'NA' with the "
        "GLAUx corpus's own CC BY-SA governing) are served. OpenEdition's license is not a clean "
        "open license, and GPL text in a CC BY-SA-labeled aggregate would misstate its terms; "
        "both are excluded rather than served, matching the corpus rule that unknown or unclear "
        "licenses are excluded. Re-derived from metadata.txt at run time."
    )

    scope_audit = {
        "source": {
            "repo": UPSTREAM_REPO,
            "commit": UPSTREAM_COMMIT,
            "retained_clone": _tilde(glaux_root),
            "metadata_sha256": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
            "documents_in_metadata": len(rows),
        },
        "proiel_dropped": {
            "rule": ("docs/source-policy.md tier 1: works marked TREEBANK_ANNOTATIONS='PROIEL' "
                     "are PROIEL data (re-exported/revised PROIEL trees) and are banned in every "
                     "role. Re-derived from metadata.txt at run time."),
            "works": len(proiel),
            "tokens_metadata": sum(int(r["TOKENS"]) for r in proiel),
            "detail": sorted((policy_row(r, "TREEBANK_ANNOTATIONS='PROIEL' (tier-1 PROIEL data)")
                              for r in proiel), key=lambda d: d["glaux_id"]),
        },
        "noncommercial_excluded": {
            "rule": ("docs/source-policy.md: any NonCommercial clause is banned in every role; "
                     "repo policy serves no NC-licensed material, and oga-v1 set the precedent "
                     "by excluding its one BY-NC-SA file. The per-work SOURCE_LICENSE governs "
                     "this annotation re-export; GLAUx's own CC BY-SA corpus license governing "
                     "a reconstructed public-domain base text (the ingest_glaux_pollux.py case) "
                     "is a different question. Re-derived from metadata.txt at run time."),
            "works": len(nc),
            "tokens_metadata": sum(int(r["TOKENS"]) for r in nc),
            "detail": sorted((policy_row(r, "NonCommercial SOURCE_LICENSE") for r in nc),
                             key=lambda d: d["glaux_id"]),
        },
        "gorman_tagged": {
            "rule": ("docs/source-policy.md: tag, don't delete. In the 40 works credited to "
                     "Vanessa Gorman's treebanks, analysis='manual' sentences are provenance_tag="
                     "'gorman'; auto sentences there, and everything elsewhere, are 'glaux'."),
            "works": len(gorman_ids),
            "gorman_sentences": prov_sents["gorman"],
            "gorman_tokens": prov_tokens["gorman"],
            "work_ids": sorted(gorman_ids),
        },
        "unclear_license_excluded": {
            "rule": UNCLEAR_RULE,
            "works": len(unclear),
            "tokens_metadata": sum(int(r["TOKENS"]) for r in unclear),
            "detail": sorted((policy_row(r, "SOURCE_LICENSE not on the open allowlist (unclear)")
                              for r in unclear), key=lambda d: d["glaux_id"]),
        },
        "unmapped_ids": [policy_row(r, "GLAUx id does not match NNNN-NNN[a-z]; excluded, not guessed")
                         for r in unmapped],
        "license_tally": dict(sorted(license_tally.items())),
    }

    manifest = {
        "export": {
            "release_id": args.release_id,
            "contract": "docs/annotation-export-contract.md",
            "generated_by": "scripts/export_glaux_annotations.py",
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content_hash": content_hash,
            "content_hash_method": (
                "sha256 over the newline-joined '<work_key>:<sha256-of-uncompressed-jsonl>' lines, "
                "work_key-sorted; excludes generated_at and gzip framing so it is reproducible on unchanged input"
            ),
            "pin_line": f"cog export {args.release_id}, {content_hash}",
            "record_layout": (
                "per-work JSONL under works/<work_key>.jsonl.gz (gzip mtime=0, deterministic); one token "
                "record per line. work_key is the greekLit CTS work id (tlgNNNN.tlgNNN) mapped from the "
                "GLAUx id; letter-suffix GLAUx documents (parts/recensions of one TLG work) are merged into "
                "the base work's stream in letter order, with the GLAUx document id in each token's `doc` "
                "and (doc, sentence_id) as the unique sentence key"
            ),
            "token_fields": {
                "id": "GLAUx native corpus-global word id (integer); artificial (elliptic) nodes use a distinct high id range",
                "form": "surface form, cog-normalized (see source.encoding_normalization); empty string for editorially deleted tokens",
                "lemma": "lemma in GLAUx's homogenized convention, verbatim except cog encoding normalization; null where GLAUx gives none",
                "pos": "AGDT/Perseus part of speech (first character of the 9-char postag); not remapped",
                "morph": "GLAUx native 9-char AGDT/Perseus positional postag; not remapped; null on unannotated (deleted-text) tokens",
                "head": "GLAUx global word id of the governing token (0 = sentence root); heads stay within the sentence",
                "deprel": "AGDT/Perseus dependency relation (the 'relation' attribute); not remapped",
                "locus": "citation of the token's passage within the work, built from GLAUx's per-genre citation attributes (see works[].locus_scheme); null where the source gives none",
                "sentence_id": "GLAUx native per-document sentence id (integer, the annotation unit); unique within the work stream together with `doc`",
                "doc": "the GLAUx document id (e.g. '0007-051a'); differs from the work_key only for merged letter-suffix parts",
                "analysis": "GLAUx native per-sentence marking: 'manual' (homogenized human treebank annotation) or 'auto' (GLAUx model output)",
                "provenance_tag": "'gorman' for manual sentences in the 40 Gorman-credited works (docs/source-policy.md tag-don't-delete); 'glaux' otherwise",
                "artificial": "GLAUx native 'elliptic' on artificial (ellipsis) nodes; null on real tokens",
                "form_original": "GLAUx's pre-cleanup source form with editorial marks ({...} deletions, <...> supplements, uncertainty dots), NFC only, otherwise verbatim; null where GLAUx gives none",
                "animacy": "GLAUx semantic layer: animacy class (Zaenen et al. 2004 style), native, where annotated",
                "sense": "GLAUx semantic layer: WordNet 3.0 sense label, native, where annotated",
            },
            "counts": {
                "works_exported": len(works),
                "glaux_documents_exported": sum(len(w["glaux_ids"]) for w in works),
                "tokens": totals["tokens"],
                "sentences": totals["sentences"],
                "sentences_by_analysis": sent_counts,
                "tokens_by_analysis": tok_counts,
                "provenance_sentences": prov_sents,
                "provenance_tokens": prov_tokens,
                "artificial_nodes": totals["artificial"],
                "tokens_missing_locus": totals["missing"],
                "tokens_locus_fallback": totals["fallback"],
                "composite_locus_works": composite_works,
                "works_dropped_proiel": len(proiel),
                "works_excluded_noncommercial": len(nc),
                "works_excluded_unclear_license": len(unclear),
            },
        },
        "source": {
            "name": "GLAUx (the Greek Language Automated)",
            "repo": UPSTREAM_REPO,
            "commit": UPSTREAM_COMMIT,
            "retained_clone": _tilde(glaux_root),
            "license_upstream": (
                "GLAUx corpus CC BY-SA (repo README); per-work SOURCE_LICENSE in metadata.txt "
                "for the underlying text sources (NonCommercial ones excluded, see policy)"
            ),
            "format": "per-document treebank XML (xml/<id>.xml): <sentence analysis=...> of <word> elements",
            "annotation_method": (
                "Mixed, marked per sentence by GLAUx's native analysis attribute. analysis='manual' is "
                "homogenized human annotation from open treebank projects (Perseus AGDT, Pedalion, "
                "Harrington, Gorman; see works[].treebank_annotations); analysis='auto' is GLAUx's own "
                "model output (transformer morphology, statistical lemmatization/parsing; Keersmaekers "
                "2021). The newer semantic layers (animacy, WordNet senses, 10/2025) are carried natively."
            ),
            "provenance_note": (
                "provenance_tag='gorman' on manual sentences of the 40 Gorman-credited works "
                "(tag-don't-delete; dilemma filters it at read time); 'glaux' otherwise. The auto layer "
                "is the output of models trained on open treebanks plus PROIEL, i.e. tier-2 under "
                "docs/source-policy.md (PROIEL-model output: acceptable, dispreferred), NOT tier-1 "
                "PROIEL data; the 25 tier-1 PROIEL works are dropped entirely (see policy). The "
                "per-work TREEBANK_ANNOTATIONS credit is carried in works[]."
            ),
            "lemma_convention": (
                "Preserved verbatim (cog does not normalize lemma conventions). GLAUx lemmas are "
                "homogenized AGDT-style dictionary headwords without homograph-disambiguation digits; "
                "punctuation tokens carry the mark itself as lemma. Only cog encoding normalization "
                "(NFC, apostrophe, sigma) is applied to the lemma string."
            ),
            "locus_note": (
                "GLAUx cites tokens with heterogeneous per-genre citation attributes (div_book/"
                "div_chapter/div_section/line and ~50 others), where a finer attribute normally embeds "
                "its ancestors as a dotted prefix (Thucydides div_section='1.1.1'). The locus is the "
                "token's finest-ranked citation value (fixed ranking, recorded per work in works[]."
                "locus_scheme.citation_attrs). When that value's numbering RESTARTS within a document "
                "(the same value recurs in separate runs under differing container contexts, e.g. one "
                "page number in two volumes), the whole work switches to composite loci prefixed by the "
                "container context (locus_scheme.mode='composite'); a value merely straddling a "
                "container boundary (a Bekker page crossing a book break) does not trigger this. Within "
                "a merged multi-part work the locus namespace is per GLAUx document: combine locus with "
                "the token's `doc`. Tokens lacking the work's primary attribute fall back to the "
                "next-ranked one (fallback_tokens); tokens with no citation attribute have locus=null "
                "(missing_tokens). Speaker labels and the two works' named-entity marks (name/namId) "
                "are not carried."
            ),
            "sentence_id_note": (
                "GLAUx numbers sentences per document (the 'id' attribute, used verbatim) and corpus-wide "
                "(the 'struct_id' attribute, not carried). Within a merged multi-part work, (doc, "
                "sentence_id) is the unique sentence key; token ids and heads are corpus-global, so head "
                "resolution never needs the sentence key."
            ),
            "encoding_normalization": {
                "unicode": "NFC (the GLAUx corpus itself is NFD)",
                "apostrophes_to_U+2019": ["U+02BC", "U+0027", "U+2018", "U+2019"],
                "sigma": "lunate ϲ/Ϲ -> σ/Σ; final ς word-finally, medial σ otherwise (applied to form and lemma)",
                "form_original": "NFC only, editorial marks kept verbatim",
            },
            "citation": (
                "Alek Keersmaekers. 2021. The GLAUx corpus: methodological issues in designing a "
                "long-term, diverse, multi-layered corpus of Ancient Greek. Proceedings of the 2nd "
                "International Workshop on Computational Approaches to Historical Language Change 2021, "
                "39-50. doi:10.18653/v1/2021.lchange-1.6. https://github.com/alekkeersmaekers/glaux"
            ),
        },
        "policy": {
            "proiel_tier1_dropped": {
                "rule": scope_audit["proiel_dropped"]["rule"],
                "works": scope_audit["proiel_dropped"]["works"],
                "tokens_metadata": scope_audit["proiel_dropped"]["tokens_metadata"],
                "detail_file": "glaux_scope_audit.json",
            },
            "noncommercial_excluded": {
                "rule": scope_audit["noncommercial_excluded"]["rule"],
                "works": scope_audit["noncommercial_excluded"]["works"],
                "tokens_metadata": scope_audit["noncommercial_excluded"]["tokens_metadata"],
                "detail_file": "glaux_scope_audit.json",
            },
            "unclear_license_excluded": {
                "rule": scope_audit["unclear_license_excluded"]["rule"],
                "works": scope_audit["unclear_license_excluded"]["works"],
                "tokens_metadata": scope_audit["unclear_license_excluded"]["tokens_metadata"],
                "detail_file": "glaux_scope_audit.json",
            },
            "gorman_tagged": {
                "rule": scope_audit["gorman_tagged"]["rule"],
                "works": scope_audit["gorman_tagged"]["works"],
                "gorman_sentences": prov_sents["gorman"],
                "gorman_tokens": prov_tokens["gorman"],
            },
            "unmapped_ids": [r["glaux_id"] for r in scope_audit["unmapped_ids"]],
        },
        "consumers": (
            "This is the GLAUx half of annotation-consumption queue item 1e "
            "(docs/annotation-export-contract.md). dilemma pins this export by export.pin_line "
            "and filters provenance_tag='gorman' at read time."
        ),
        "works": [dict(w) for w in sorted(works, key=lambda x: x["work_key"])],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")
    with open(out_dir / "glaux_scope_audit.json", "w", encoding="utf-8") as fh:
        json.dump(scope_audit, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")

    # The git-tracked pointer stub, written next to the (gitignored) release dir.
    # Skipped for smoke tests, whose partial hash must never overwrite the pin.
    if not args.limit and not args.works:
        stub_path = out_dir.parent / f"{args.release_id}.json"
        with open(stub_path, "w", encoding="utf-8") as fh:
            json.dump(make_pointer_stub(manifest, args.hf_repo), fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"[glaux-export] pointer stub -> {stub_path}", flush=True)

    print(f"[glaux-export] wrote {len(works)} works, {totals['tokens']:,} tokens "
          f"({totals['sentences']:,} sentences) to {out_dir}", flush=True)
    print(f"[glaux-export] policy: PROIEL dropped {len(proiel)} works / "
          f"{scope_audit['proiel_dropped']['tokens_metadata']:,} tokens; NC excluded {len(nc)} works / "
          f"{scope_audit['noncommercial_excluded']['tokens_metadata']:,} tokens; unclear-license "
          f"excluded {len(unclear)} works / "
          f"{scope_audit['unclear_license_excluded']['tokens_metadata']:,} tokens", flush=True)
    print(f"[glaux-export] provenance: gorman {prov_sents['gorman']:,} sentences / "
          f"{prov_tokens['gorman']:,} tokens; glaux {prov_sents['glaux']:,} sentences / "
          f"{prov_tokens['glaux']:,} tokens", flush=True)
    print(f"[glaux-export] analysis: manual {sent_counts['manual']:,} sentences / "
          f"{tok_counts['manual']:,} tokens; auto {sent_counts['auto']:,} sentences / "
          f"{tok_counts['auto']:,} tokens", flush=True)
    if totals["missing"]:
        print(f"[glaux-export] note: {totals['missing']:,} tokens have no citation attribute (locus=null)", flush=True)
    print(f"[glaux-export] pin line: cog export {args.release_id}, {content_hash}", flush=True)


if __name__ == "__main__":
    main()
