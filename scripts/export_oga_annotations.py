#!/usr/bin/env python3
"""Export Opera Graeca Adnotata (OGA) v0.2.0 as cog's standardized annotation export.

This produces the annotation export defined by docs/annotation-export-contract.md:
per-work, CTS-URN-keyed streams of token records, with cog-owned encoding
normalization and source-native tagsets/lemmas preserved verbatim. It is item 1a
of the annotation-consumption queue and is what dilemma Phase 2 pins ("cog export
<release_id>, hash <content_hash>").

Inputs (all from the retained OGA clone, default ~/Documents/oga):
  - workspace/conllu/<work>.tok01_sentence-seg01_annotated_lemma.conllu
      the morphosyntactic annotation (form, lemma, native pos + 9-char AGDT/Perseus
      morph tag, head, deprel, per-token id in the MISC column).
  - workspace/oga/oga_v0.2.0_{1..5}/<work>/<work>.tok01_cts01.xml
      the PAULA standoff CTS layer mapping each token id -> its CTS passage.
  - original_Greek_files.zip (PTA subtree)
      the PTA per-file TEI licences, read to exclude any NonCommercial work.

cog owns encoding normalization (NFC; elision apostrophes -> U+2019; standard
final/medial sigma). cog does NOT normalize lemma conventions: OGA's homograph
digits (e.g. "λέγω3") and lowercase Koine headwords are preserved verbatim.

Provenance/policy (docs/source-policy.md):
  - OGA's whole morphosyntactic layer is model-produced (Trankit morphosyntax +
    GreTa lemmatization). There is no per-token manual/auto marking in v0.2.0, so
    every token is analysis="auto", provenance_tag="oga". OGA's models are trained
    on Perseus/PROIEL UD data, which makes this tier-2 (PROIEL-model output:
    acceptable, dispreferred), not tier-1 PROIEL data. It is not Gorman-derived.
  - NonCommercial works are excluded. The only NC file in the OGA/PTA set is
    pta0036.pta001.pta-grc1 (CC BY-NC-SA 3.0); this is verified from the PTA TEI
    licences at run time, not hard-coded.

The export is deterministic: gzip is written with mtime=0 and the content hash is
computed over the uncompressed per-work payloads, so re-running on unchanged input
reproduces byte-identical files and the same content_hash.

Storage (docs/annotation-export-contract.md, "Storage"): the payload this writes
is NOT committed to git. It is uploaded to the Hugging Face dataset repo with
scripts/upload_annotation_export.py; git tracks this exporter plus the pointer
stub written next to the release dir (data/annotations/oga/<release_id>.json).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import gzip
import hashlib
import html
import io
import json
import os
import re
import sys
import unicodedata
import zipfile
from pathlib import Path

# The HF dataset repo that holds export payloads (see the module docstring and
# docs/annotation-export-contract.md, "Storage"); the release id is the path in
# the repo. scripts/upload_annotation_export.py shares this default.
HF_EXPORTS_REPO = "ciscoriordan/open-greek-corpus-annotation-exports"


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
            "payload": ("works/<work_id>.jsonl.gz per exported work, plus manifest.json "
                        "and pta_license_audit.json"),
            "note": ("docs/annotation-export-contract.md, 'Storage': export payloads live on "
                     "the Hub; git tracks the exporter script and this pointer stub only. "
                     "Regenerate locally with scripts/export_oga_annotations.py, publish with "
                     "scripts/upload_annotation_export.py."),
        },
        "counts": exp["counts"],
        "generated_by": exp["generated_by"],
        "generated_at": exp["generated_at"],
        "contract": exp["contract"],
        "upstream_pin": {
            "source": f"{manifest['source']['name']} {manifest['source']['version']}",
            "version_doi": manifest["source"]["version_doi"],
            "note": "cog pins the upstream; consumers pin only pin_line (docs/pinning-discipline.md)",
        },
    }


# --- cog-owned encoding normalization -------------------------------------

# Elision / apostrophe characters that are unified to U+2019 (right single
# quotation mark). Deliberately conservative: U+00B4 (acute) and U+2032 (prime)
# are NOT included because OGA uses them as the Greek numeral keraia (e.g. "ρ´" =
# 100), and U+0060 (grave) appears only as an intra-word artifact; treating any of
# them as an apostrophe would corrupt the token.
_APOSTROPHES = {
    "ʼ",  # MODIFIER LETTER APOSTROPHE (the dominant OGA elision mark, e.g. παρʼ)
    "'",  # APOSTROPHE
    "‘",  # LEFT SINGLE QUOTATION MARK
    "’",  # RIGHT SINGLE QUOTATION MARK (target)
}
_APOS_TABLE = {ord(c): "’" for c in _APOSTROPHES}


def _normalize_sigma(s: str) -> str:
    """Map lunate sigma to standard sigma and enforce final/medial position.

    ϲ (U+03F2) / Ϲ (U+03F9) -> σ / Σ, then every σ/ς is placed by position: final
    form (ς) when no Greek letter follows within the token, medial (σ) otherwise.
    """
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


def normalize(text: str) -> str:
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
    """Full CTS URN for an OGA work id (textgroup.work.edition)."""
    textgroup = work_id.split(".", 1)[0]
    namespace = "pta" if textgroup.startswith("pta") else "greekLit"
    return f"urn:cts:{namespace}:{work_id}"


def _locus_from_cts_value(value: str, work_id: str) -> str:
    """Reduce a PAULA cts feat value to the bare passage locus.

    greekLit works store the bare passage with '_' between levels (e.g. "1_1");
    PTA works store the full urn (e.g. "urn:cts:pta:pta0001.pta001.pta-grc1_1").
    Both yield a dotted locus ("1.1" / "1").
    """
    value = html.unescape(value).strip()
    if value.startswith("urn:cts:"):
        marker = work_id + "_"
        idx = value.find(marker)
        passage = value[idx + len(marker):] if idx != -1 else value.rsplit(":", 1)[-1]
    else:
        passage = value
    return passage.replace("_", ".")


_CTS_FEAT_RE = re.compile(r'xlink:href="#([te]_\d+)"\s+value="([^"]*)"')


def parse_cts_layer(path: str, work_id: str) -> dict[str, str]:
    """token_id ('t_N'/'e_N') -> locus, from a PAULA tok01_cts01.xml layer."""
    loci: dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = _CTS_FEAT_RE.search(line)
            if m:
                loci[m.group(1)] = _locus_from_cts_value(m.group(2), work_id)
    return loci


# --- CoNLL-U parsing ------------------------------------------------------

def parse_conllu_sentences(path: str):
    """Yield sentences; each is a list of raw 10-column CoNLL-U field lists."""
    sentence: list[list[str]] = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                if sentence:
                    yield sentence
                    sentence = []
                continue
            cols = line.split("\t")
            if len(cols) >= 10:
                sentence.append(cols)
    if sentence:
        yield sentence


# --- PTA per-file licence audit (NonCommercial exclusion) -----------------

_LICENCE_RE = re.compile(rb"licenses/([a-z0-9./-]+)")
_PTA_TEI_RE = re.compile(r"/data/(pta[0-9]+)/(pta[0-9]+)/([^/]+\.pta-grc[0-9]+)\.xml$")


def _is_noncommercial(target: str) -> bool:
    t = target.lower()
    return ("by-nc" in t) or ("by-nd" in t) or ("-nc-" in t) or ("-nd-" in t) or ("noncommercial" in t)


def audit_pta_licences(original_zip: str) -> list[dict]:
    """Read every PTA work's TEI licence target from original_Greek_files.zip.

    Returns a sorted list of {work_id, license, noncommercial} records so the NC
    exclusion is reproducible from source rather than a hand-maintained list.
    """
    records: dict[str, dict] = {}
    with zipfile.ZipFile(original_zip) as zf:
        for name in zf.namelist():
            m = _PTA_TEI_RE.search(name)
            if not m:
                continue
            work_id = m.group(3)  # e.g. pta0001.pta001.pta-grc1
            with zf.open(name) as member:
                head = member.read(8192)
            lm = _LICENCE_RE.search(head)
            target = ("licenses/" + lm.group(1).decode("ascii")) if lm else "UNKNOWN"
            records[work_id] = {
                "work_id": work_id,
                "license": target,
                "noncommercial": _is_noncommercial(target),
            }
    return sorted(records.values(), key=lambda r: r["work_id"])


# --- Export ---------------------------------------------------------------

TOKEN_FIELD_ORDER = [
    "id", "form", "lemma", "pos", "morph", "head", "deprel",
    "locus", "sentence_id", "analysis", "provenance_tag",
]


def build_token_record(cols, sentence_id, locus):
    lemma = cols[2]
    if lemma == "_":
        lemma = None
    try:
        head = int(cols[6])
    except ValueError:
        head = cols[6]
    try:
        tok_id = int(cols[0])
    except ValueError:
        tok_id = cols[0]
    return {
        "id": tok_id,
        "form": normalize(cols[1]),
        "lemma": normalize(lemma) if lemma is not None else None,
        "pos": cols[3],
        "morph": cols[4],
        "head": head,
        "deprel": cols[7],
        "locus": locus,
        "sentence_id": sentence_id,
        "analysis": "auto",
        "provenance_tag": "oga",
    }


def export_work(conllu_path: str, cts_path: str, work_id: str, out_path: Path):
    """Write one work's JSONL.gz (deterministic) and return per-work stats."""
    loci = parse_cts_layer(cts_path, work_id)
    buf = io.StringIO()
    n_tokens = 0
    n_ellipsis = 0
    n_missing_locus = 0
    sentence_id = 0
    for sentence in parse_conllu_sentences(conllu_path):
        sentence_id += 1
        for cols in sentence:
            tok_key = cols[9].split("|")[0].strip()  # MISC holds the t_/e_ token id
            locus = loci.get(tok_key)
            if locus is None:
                n_missing_locus += 1
            rec = build_token_record(cols, sentence_id, locus)
            if isinstance(rec["id"], str) or cols[3] == "-":
                n_ellipsis += 1
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
        "sentences": sentence_id,
        "ellipsis_nodes": n_ellipsis,
        "sha256": sha,
        "_missing_locus": n_missing_locus,
    }


def index_cts_layers(oga_version_dir: Path) -> dict[str, str]:
    """work_id -> path of its tok01_cts01.xml, from the official PAULA layout."""
    index: dict[str, str] = {}
    pattern = str(oga_version_dir / "workspace" / "oga" / "oga_v0.2.0_*" / "*" / "*.tok01_cts01.xml")
    for path in glob.glob(pattern):
        base = os.path.basename(path)
        work_id = base[: -len(".tok01_cts01.xml")]
        index[work_id] = path
    return index


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--oga-root", default=os.environ.get("OGA_ROOT", os.path.expanduser("~/Documents/oga")),
                    help="retained OGA clone (default $OGA_ROOT or ~/Documents/oga)")
    ap.add_argument("--out-dir", default=None,
                    help="output release dir (default <repo>/data/annotations/oga/<release_id>)")
    ap.add_argument("--release-id", default="oga-v1", help="cog export release id (default oga-v1)")
    ap.add_argument("--limit", type=int, default=None, help="export only the first N works (smoke test)")
    ap.add_argument("--works", nargs="*", default=None, help="export only these work ids (smoke test)")
    ap.add_argument("--hf-repo", default=HF_EXPORTS_REPO,
                    help="HF dataset repo the pointer stub records as the payload home")
    args = ap.parse_args()

    oga_root = Path(args.oga_root)
    version_dir = oga_root / "opera_graeca_adnotata_v0.2.0"
    conllu_dir = version_dir / "workspace" / "conllu"
    original_zip = version_dir / "original_Greek_files.zip"
    repo_root = Path(__file__).resolve().parent.parent
    out_dir = Path(args.out_dir) if args.out_dir else repo_root / "data" / "annotations" / "oga" / args.release_id

    if not conllu_dir.is_dir():
        sys.exit(f"CoNLL-U dir not found: {conllu_dir}")

    print(f"[oga-export] indexing PAULA cts layers under {version_dir}/workspace/oga ...", flush=True)
    cts_index = index_cts_layers(version_dir)
    print(f"[oga-export] indexed {len(cts_index)} cts layers", flush=True)

    print("[oga-export] auditing PTA per-file licences ...", flush=True)
    pta_audit = audit_pta_licences(str(original_zip))
    nc_works = {r["work_id"] for r in pta_audit if r["noncommercial"]}
    # Guard: the policy-named NC file must be detected. If it is not, something in
    # the source or the detector changed and the run must not silently ship it.
    if "pta0036.pta001.pta-grc1" not in nc_works:
        sys.exit("[oga-export] ABORT: pta0036 (the known NC file) was not detected as NonCommercial")
    print(f"[oga-export] PTA works audited: {len(pta_audit)}; NonCommercial (excluded): {sorted(nc_works)}", flush=True)

    conllu_files = sorted(glob.glob(str(conllu_dir / "*.conllu")))
    if args.works:
        wanted = set(args.works)
        conllu_files = [f for f in conllu_files
                        if os.path.basename(f)[: -len(".tok01_sentence-seg01_annotated_lemma.conllu")] in wanted]
    if args.limit:
        conllu_files = conllu_files[: args.limit]

    works: list[dict] = []
    excluded: list[dict] = []
    total_tokens = total_sentences = total_ellipsis = total_missing = 0
    suffix = ".tok01_sentence-seg01_annotated_lemma.conllu"

    for i, conllu_path in enumerate(conllu_files, 1):
        base = os.path.basename(conllu_path)
        work_id = base[: -len(suffix)] if base.endswith(suffix) else base.split(".tok01")[0]
        if work_id in nc_works:
            lic = next((r["license"] for r in pta_audit if r["work_id"] == work_id), "UNKNOWN")
            excluded.append({"work_id": work_id, "cts_urn": work_cts_urn(work_id),
                             "license": lic, "reason": "NonCommercial (docs/source-policy.md)"})
            continue
        cts_path = cts_index.get(work_id)
        if cts_path is None:
            excluded.append({"work_id": work_id, "cts_urn": work_cts_urn(work_id),
                             "reason": "no PAULA cts layer found"})
            continue
        out_path = out_dir / "works" / f"{work_id}.jsonl.gz"
        stats = export_work(conllu_path, cts_path, work_id, out_path)
        total_tokens += stats["tokens"]
        total_sentences += stats["sentences"]
        total_ellipsis += stats["ellipsis_nodes"]
        total_missing += stats.pop("_missing_locus")
        works.append(stats)
        if i % 200 == 0 or i == len(conllu_files):
            print(f"[oga-export] {i}/{len(conllu_files)} works ... {total_tokens:,} tokens", flush=True)

    # Deterministic content hash over the uncompressed per-work payloads.
    hasher = hashlib.sha256()
    for w in sorted(works, key=lambda x: x["work_id"]):
        hasher.update(f"{w['work_id']}:{w['sha256']}\n".encode("utf-8"))
    content_hash = "sha256:" + hasher.hexdigest()

    zip_hashes = {
        "workspace/conllu.zip": {
            "sha256": "549fef7a63a935ce40ce2b4551546cc95d27a3bf98b3cf5ec9b1a7e2427b9d41",
            "bytes": 504291325,
        },
        "workspace/oga.zip": {
            "sha256": "349e49a9015b6ad4caccf40a0796d61e15717d9b2fc4e36357b8cbcb68b4416c",
            "bytes": 3225283562,
        },
    }

    manifest = {
        "export": {
            "release_id": args.release_id,
            "contract": "docs/annotation-export-contract.md",
            "generated_by": "scripts/export_oga_annotations.py",
            "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content_hash": content_hash,
            "content_hash_method": (
                "sha256 over the newline-joined '<work_id>:<sha256-of-uncompressed-jsonl>' lines, "
                "work_id-sorted; excludes generated_at and gzip framing so it is reproducible on unchanged input"
            ),
            "pin_line": f"cog export {args.release_id}, {content_hash}",
            "record_layout": (
                "per-work JSONL under works/<work_id>.jsonl.gz (gzip mtime=0, deterministic); "
                "one token record per line; the work's CTS URN is the file/work key (see works[].cts_urn)"
            ),
            "token_fields": {
                "id": "OGA native in-sentence token index; the integer that 'head' points to (0 = sentence root)",
                "form": "surface form, cog-normalized (see source.encoding_normalization)",
                "lemma": "lemma in OGA's native convention, preserved verbatim except cog encoding normalization",
                "pos": "OGA native single-letter part of speech (see OGA query/morphology.md); not remapped",
                "morph": "OGA native 9-char AGDT/Perseus positional morphology tag; not remapped",
                "head": "in-sentence id of the governing token (0 = root); scoped by sentence_id",
                "deprel": "AGDT/Perseus dependency relation; not remapped",
                "locus": "CTS logical passage of the token within the work (dotted); combine with works[].cts_urn",
                "sentence_id": "per-work 1-based sentence index (the annotation unit); see source.sentence_id_note",
                "analysis": "'auto' for all OGA tokens (see source.annotation_method)",
                "provenance_tag": "'oga' for all tokens",
            },
            "counts": {
                "works_exported": len(works),
                "works_excluded": len(excluded),
                "tokens": total_tokens,
                "sentences": total_sentences,
                "ellipsis_nodes": total_ellipsis,
                "tokens_missing_locus": total_missing,
            },
        },
        "source": {
            "name": "Opera Graeca Adnotata (OGA)",
            "version": "v0.2.0",
            "version_doi": "10.5281/zenodo.14206061",
            "concept_doi_note": (
                "The concept DOI floats to the latest release and is deliberately NOT the pin "
                "(docs/pinning-discipline.md). Pin the version DOI above."
            ),
            "retained_clone": "~/Documents/oga (versioned tree opera_graeca_adnotata_v0.2.0/)",
            "input_artifacts": zip_hashes,
            "input_artifacts_note": (
                "Zenodo per-file checksums of the two published archives this export derives from: "
                "workspace/conllu.zip (morphosyntax) and workspace/oga.zip (PAULA cts layer)."
            ),
            "github": "https://github.com/OperaGraecaAdnotata/OGA",
            "license_upstream": "CC BY-SA 4.0 (collection); PTA has per-file licences (see policy.pta_license_audit)",
            "annotation_method": (
                "Model-produced: Trankit morphosyntax + GreTa lemmatization (arXiv:2410.12055, arXiv:2404.00739). "
                "OGA v0.2.0 carries no per-token or per-sentence manual/auto marking, so every token is analysis='auto'."
            ),
            "provenance_note": (
                "provenance_tag='oga' for all tokens. OGA's models are trained on Perseus/PROIEL UD data, which makes "
                "this annotation tier-2 under docs/source-policy.md (output of a PROIEL-trained model: acceptable, "
                "dispreferred where a non-PROIEL source covers the same work). It is NOT tier-1 PROIEL data and is NOT "
                "Gorman-derived, so no tokens are tagged provenance=gorman or proiel-*."
            ),
            "lemma_convention": (
                "Preserved verbatim (cog does not normalize lemma conventions). OGA lemmas are lowercased, use Koine/"
                "standard dictionary headwords, and carry homograph-disambiguation digits appended to the headword "
                "(e.g. 'λέγω3'). Only cog encoding normalization (NFC, apostrophe, sigma) is applied to the lemma string."
            ),
            "sentence_id_note": (
                "OGA provides no explicit sentence identifier; sentences are the blank-line groups of the CoNLL-U. "
                "cog assigns a per-work 1-based index in document order as sentence_id."
            ),
            "encoding_normalization": {
                "unicode": "NFC",
                "apostrophes_to_U+2019": ["U+02BC", "U+0027", "U+2018", "U+2019"],
                "apostrophes_left_untouched": {
                    "U+00B4": "acute; used by OGA as the Greek numeral keraia (e.g. 'ρ´' = 100), not an apostrophe",
                    "U+2032": "prime; used as a numeral/prime mark, not an apostrophe",
                    "U+0060": "grave; only an intra-word artifact",
                },
                "sigma": "lunate ϲ/Ϲ -> σ/Σ; final ς word-finally, medial σ otherwise (applied to form and lemma)",
            },
            "citation": "Giuseppe G. A. Celano. 2024. Opera Graeca Adnotata (v0.2.0). Zenodo. https://doi.org/10.5281/zenodo.14206061",
        },
        "policy": {
            "nc_ban": "docs/source-policy.md: any NonCommercial licence is banned in every role.",
            "nc_excluded": excluded,
            "pta_license_audit": {
                "checked": len(pta_audit),
                "noncommercial": sorted(nc_works),
                "detail_file": "pta_license_audit.json",
                "method": "read <licence target> from each PTA work's TEI header in original_Greek_files.zip at run time",
            },
            "non_pta_license_note": (
                "A full scan of the canonical-greekLit and First1KGreek TEI in original_Greek_files.zip found no "
                "NonCommercial or NoDerivatives licence (all CC BY-SA 4.0 / BY-SA 3.0), matching OGA/source-policy.md's "
                "statement that pta0036 is the single BY-NC-SA file in the OGA/PTA set."
            ),
        },
        "consumers": (
            "This is annotation-consumption queue item 1a (docs/annotation-export-contract.md). "
            "dilemma Phase 2 pins this export by export.pin_line."
        ),
        "works": [dict(w) for w in sorted(works, key=lambda x: x["work_id"])],
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")
    with open(out_dir / "pta_license_audit.json", "w", encoding="utf-8") as fh:
        json.dump({"version_doi": "10.5281/zenodo.14206061", "works": pta_audit}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    # The git-tracked pointer stub, written next to the (gitignored) release dir.
    # Skipped for smoke tests, whose partial hash must never overwrite the pin.
    if not args.limit and not args.works:
        stub_path = out_dir.parent / f"{args.release_id}.json"
        with open(stub_path, "w", encoding="utf-8") as fh:
            json.dump(make_pointer_stub(manifest, args.hf_repo), fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        print(f"[oga-export] pointer stub -> {stub_path}", flush=True)

    print(f"[oga-export] wrote {len(works)} works, {total_tokens:,} tokens to {out_dir}", flush=True)
    print(f"[oga-export] excluded {len(excluded)} works; content_hash = {content_hash}", flush=True)
    if total_missing:
        print(f"[oga-export] WARNING: {total_missing} tokens had no CTS locus", flush=True)
    print(f"[oga-export] pin line: cog export {args.release_id}, {content_hash}", flush=True)


if __name__ == "__main__":
    main()
