"""Reviewed admission decisions for historical Dübner front matter.

These are historical texts, including the units held outside primary counts.
An overlapping anthology is not a reason to call historical Greek apparatus.
The table records source-supported overlaps; measurements are rebuilt from
pinned original bytes. Exact word-shingle overlap is a retrieval diagnostic,
not an OCR accuracy score or proof that two editions have identical scope.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Mapping

A_PATH = "data/corpus/scholia-in-aristophanem.scholia-in-acharnenses-scholia-vetera-et-recentiora-triclinii.jsonl"
A_SHA256 = "14736ad45cb79e53f6f6eb64160dc92d1aebe9b2f26ed28ae5ab2490834f38e3"
KAIBEL_R = "data/corpus/kaibel-cgf-1899.volume-witness-r.jsonl"
KAIBEL_S = "data/corpus/kaibel-cgf-1899.volume-witness-s.jsonl"
KAIBEL_S_SECONDARY = "data/corpus_secondary/kaibel-cgf-1899.volume-witness-s.jsonl"
WESTERMANN = "data/corpus/marcellinus.vita-thucydidis.jsonl"
SUDA = "data/corpus/suda.lexicon.jsonl"
ANTHOLOGY = "data/corpus/anthologia-graeca.anthologia-graeca.jsonl"
# The producer must archive these bytes with its original inputs. Otherwise a
# later legitimate correction to an overlapping work would invalidate this
# frozen historical admission record.
EVIDENCE_PINS = {
    KAIBEL_R: "c6f1dfa05739b357ec876bdda254fe76dd1a17dee2a160153b24ddd794994aa7",
    KAIBEL_S: "63f5447cc96e3657766613f5b981dca513caf8bf31d257ab5fd0d87c4ee87600",
    KAIBEL_S_SECONDARY: "2df7625d3629610d6de369c4673ec292980a9ab5f1ee09177b110a758abd9218",
    WESTERMANN: "f981d2caff071cb9e88ffdf3784de725ff56a3b7a49de11a58d6b1d9180e2dd7",
    SUDA: "ff6951bbc6959baf37b794c3232f669b6428e2d15a09057e17aab1cc17f599c9",
    ANTHOLOGY: "178370e7d2e0a4b92c72b5eef0bb084f4a3cb71178c28e70d62a45de5ce051ff",
}


def evidence(path: str, loci: tuple[str, ...], note: str) -> dict:
    return {"path": path, "sha256": EVIDENCE_PINS[path], "loci": list(loci), "note": note}


FRONT_DISPOSITIONS = {
    "platonius": {
        "admission": "comparative", "target": None,
        "source_role": "historical-prolegomena",
        "evidence": [
            evidence(KAIBEL_R, ("rhinthon_kaibel_cgf_1899_0026.1", "rhinthon_kaibel_cgf_1899_0029.2"),
                     "Printed Platonius heading and body in the Kaibel volume witness."),
            evidence(KAIBEL_S, ("sopater_kaibel_cgf_0022.1", "sopater_kaibel_cgf_0023.2", "sopater_kaibel_cgf_0027.1"),
                     "Overlapping readings of the Platonius treatises; use the existing combined Kaibel projection when counting its occurrences."),
        ],
        "reason": "The authentic Platonius treatises already occur in the Kaibel witnesses. Preserve Dübner as an attributed comparative edition without adding another independent lexical occurrence. The old Platonius identity must not continue to label an entire Aristophanes scholia volume.",
    },
    "anonymous-comedy-prolegomena": {
        "admission": "comparative", "target": None,
        "source_role": "historical-prolegomena",
        "evidence": [
            evidence(KAIBEL_R, ("rhinthon_kaibel_cgf_1899_0038.1", "rhinthon_kaibel_cgf_1899_0041.1", "rhinthon_kaibel_cgf_1899_0046.3"),
                     "Corresponding historical comedy prolegomena in the Kaibel anthology."),
            evidence(KAIBEL_S, ("sopater_kaibel_cgf_0032.1", "sopater_kaibel_cgf_0035.1", "sopater_kaibel_cgf_0040.2"),
                     "Second Kaibel OCR witness; not an additional independent edition."),
        ],
        "reason": "Several anonymous pieces overlap the existing Kaibel anthology. Their Dübner grouping is not an independently identified recension. Preserve every historical unit and reading while holding additional scalar lexical counts until cross-edition work and passage alignment establishes a single occurrence.",
    },
    "anonymous-coislinianus": {
        "admission": "comparative", "target": None,
        "source_role": "historical-prolegomena",
        "evidence": [
            evidence(KAIBEL_R, ("rhinthon_kaibel_cgf_1899_0075.4", "rhinthon_kaibel_cgf_1899_0075.9", "rhinthon_kaibel_cgf_1899_0075.15"),
                     "The same comedy treatise from the Coislinianus source."),
            evidence(KAIBEL_S_SECONDARY, ("sopater_kaibel_cgf_0069.4", "sopater_kaibel_cgf_0069.9"),
                     "Preserved corresponding Kaibel reading outside its primary counts."),
        ],
        "reason": "The treatise overlaps the Kaibel witnesses. Its scrambled diagrams remain unresolved historical evidence, not modern editorial prose; neither those diagrams nor another edition reading should create duplicate lexical counts.",
    },
    "tzetzes-poet-differences": {
        "admission": "comparative", "target": None,
        "source_role": "historical-prolegomena",
        "evidence": [
            evidence(KAIBEL_R, ("rhinthon_kaibel_cgf_1899_0057.2", "rhinthon_kaibel_cgf_1899_0061.28", "rhinthon_kaibel_cgf_1899_0062.7"),
                     "Explicit heading: John Tzetzes, verses on differences between poets."),
            evidence(KAIBEL_S, ("sopater_kaibel_cgf_0056.7",), "Corresponding verse reading."),
        ],
        "reason": "Dübner prints another edition of the Tzetzes verses already present in the Kaibel anthology. Preserve it as a comparative historical edition pending work-level consolidation; do not infer a new independent occurrence from another OCR source.",
    },
    "tzetzes-technical-iambics": {
        "admission": "comparative", "target": None,
        "source_role": "historical-prolegomena",
        "evidence": [
            evidence(KAIBEL_R, ("rhinthon_kaibel_cgf_1899_0064.10", "rhinthon_kaibel_cgf_1899_0064.16", "rhinthon_kaibel_cgf_1899_0065.17"),
                     "Corresponding technical iambic verses on comedy."),
            evidence(KAIBEL_S, ("sopater_kaibel_cgf_0058.1", "sopater_kaibel_cgf_0058.17"),
                     "Tzetzes heading and corresponding verse in the second Kaibel witness."),
        ],
        "reason": "The same technical verses are represented by the Kaibel anthology witnesses. Keep the Dübner readings with the printed attribution, outside additional primary frequency counts until the editions are aligned.",
    },
    "anonymous-aristophanes-lives": {
        "admission": "comparative", "target": None,
        "source_role": "historical-prolegomena",
        "evidence": [
            evidence(WESTERMANN, ("marcellinus_westermann_0183.2", "marcellinus_westermann_0184.1", "marcellinus_westermann_0185.1", "marcellinus_westermann_0186.27"),
                     "Aristophanes biographies inside the Westermann volume currently served under the Marcellinus title."),
        ],
        "reason": "The anonymous Aristophanes biographies overlap the existing Westermann anthology extraction. Preserve the Dübner biographies with their actual historical identity as comparative witnesses. Do not assign them to Marcellinus or add independent primary counts while that other volume awaits its own scope repair.",
    },
    "thomas-magister-aristophanes-life": {
        "admission": "comparative", "target": None,
        "source_role": "historical-prolegomena",
        "evidence": [
            evidence(WESTERMANN, ("marcellinus_westermann_0187.2", "marcellinus_westermann_0188.1", "marcellinus_westermann_0188.5"),
                     "Thomas Magister's Aristophanes life, including related apparatus quotations, in the Westermann anthology."),
        ],
        "reason": "Thomas Magister's life already occurs in the Westermann extraction. Keep the printed Thomas attribution and the Dübner reading as comparative evidence; the other file's current Marcellinus label is not an attribution for this biography.",
    },
    "suda-aristophanes-excerpt": {
        "admission": "secondary", "target": "suda.lexicon",
        "source_role": "historical-prolegomena", "target_loci": ["1.Α.3932"],
        "evidence": [evidence(SUDA, ("1.Α.3932",), "Dübner explicitly identifies the excerpt as taken from the Suda; the same entry is already served.")],
        "reason": "Another reading of Suda alpha 3932, not another historical text occurrence. Preserve the literal Dübner spelling as a secondary edition reading and keep existing Suda primary text unchanged.",
    },
    "antipater-thessalonica-aristophanes-epigram": {
        "admission": "secondary", "target": "anthologia-graeca.anthologia-graeca",
        "source_role": "historical-epigram",
        "target_loci": [f"9.186.{n}" for n in range(1, 7)],
        "evidence": [evidence(ANTHOLOGY, tuple(f"9.186.{n}" for n in range(1, 7)),
                              "Dübner's printed reference is Anthologia Palatina IX 186; the whole poem is already served.")],
        "reason": "The Harvard-only epigram is another OCR reading of Anthologia Graeca 9.186. Preserve it as a secondary poem witness, without adding duplicate frequencies or claiming line-level OCR equivalence.",
    },
    "diodorus-aristophanes-epitaph": {
        "admission": "secondary", "target": "anthologia-graeca.anthologia-graeca",
        "source_role": "historical-epigram", "target_loci": ["7.38.1", "7.38.2"],
        "evidence": [evidence(ANTHOLOGY, ("7.38.1", "7.38.2"),
                              "Dübner's printed reference is Anthologia Palatina VII 38; the same two-line poem is already served.")],
        "reason": "The Harvard-only epitaph is another OCR reading of Anthologia Graeca 7.38. Retain its literal reading as a secondary poem witness rather than another primary occurrence.",
    },
}

GREEK = re.compile(r"[Ͱ-Ͽἀ-῿̀-ͯ]+")


def _tokens(text):
    return ["".join(c for c in unicodedata.normalize("NFD", token.casefold())
                    if not unicodedata.combining(c)).replace("ς", "σ").replace("ϲ", "σ")
            for token in GREEK.findall(text)]


def _grams(tokens):
    return {tuple(tokens[i:i + 8]) for i in range(len(tokens) - 7)}


def _read(root, path, before):
    data = before[path] if before is not None and path in before else (Path(root) / path).read_bytes()
    expected = A_SHA256 if path == A_PATH else EVIDENCE_PINS[path]
    if not isinstance(data, bytes) or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Changed Dübner overlap evidence: " + path)
    return [json.loads(line) for line in data.splitlines() if line]


def measurements(root: Path, before: Mapping[str, bytes] | None = None) -> dict:
    """Rebuild counts and validate every cited overlapping locus from frozen bytes.

    Source front spans are ordered numerically by page and row. Target files
    retain their published row order for this reproducible retrieval diagnostic.
    It does not authorize rewriting or deleting any target corpus text.
    """
    from dubner_source_observations import build
    source = _read(root, A_PATH, before)
    source.sort(key=lambda row: tuple(map(int, row["locus"].rsplit("_", 1)[1].split("."))))
    partitions = build(source)
    units = defaultdict(list)
    for row in source:
        for part in partitions.get(row["locus"], []):
            if part["lexical_eligible"]:
                units[part["work"]].extend(_tokens(row["text"][part["start"]:part["end"]]))
    targets = {path: _read(root, path, before) for path in EVIDENCE_PINS}
    target_grams = {path: _grams([token for row in rows for token in _tokens(row["text"])])
                    for path, rows in targets.items()}
    result = {}
    for key, disposition in FRONT_DISPOSITIONS.items():
        if key not in units:  # The two epigrams exist only in the Harvard extraction.
            continue
        source_grams = _grams(units[key])
        hits = []
        for item in disposition["evidence"]:
            path = item["path"]
            available = {row["locus"] for row in targets[path]}
            missing = set(item["loci"]) - available
            if missing:
                raise ValueError(f"Missing overlap loci in {path}: {sorted(missing)}")
            shared = len(source_grams & target_grams[path])
            hits.append({"path": path, "sha256": EVIDENCE_PINS[path],
                         "shared_unique_normalized_8grams": shared})
        result[key] = {"source_greek_tokens": len(units[key]),
                       "source_unique_normalized_8grams": len(source_grams), "overlaps": hits}
    # Validate Harvard-only destination evidence as well.
    for disposition in FRONT_DISPOSITIONS.values():
        for item in disposition["evidence"]:
            if not set(item["loci"]).issubset({row["locus"] for row in targets[item["path"]]}):
                raise ValueError("A historical excerpt destination is missing")
    westermann = targets[WESTERMANN]
    westermann_pages = {int(row["locus"].rsplit("_", 1)[1].split(".")[0]) for row in westermann}
    return {
        "method": "Unique normalized Greek eight-word shingles; NFD casefold, combining marks removed, final and lunate sigma folded. A retrieval diagnostic, not OCR accuracy or full edition equivalence.",
        "front_units": result,
        "westermann_existing_scope": {
            "path": WESTERMANN, "sha256": EVIDENCE_PINS[WESTERMANN],
            "rows": len(westermann),
            "greek_tokens": sum(len(GREEK.findall(row["text"])) for row in westermann),
            "source_pdf_page_min": min(westermann_pages),
            "source_pdf_page_max": max(westermann_pages),
            "aristophanes_source_pages": [183, 184, 185, 186, 187, 188],
            "qualification": "The current Marcellinus/Vita Thucydidis file includes other biographies from the Westermann volume. These counts measure the published file, not the authentic length of Marcellinus's work. Its separate scope repair is outside the Dübner migration.",
        },
    }
