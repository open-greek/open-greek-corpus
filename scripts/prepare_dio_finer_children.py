#!/usr/bin/env python3
"""Reproduce source-pinned child retries of completed but defective Dio strips."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from prepare_dio_ocr_retries import ROOT, DIRECTORY, CHECKPOINTS, encode, sha, load_originals

PROFILES = {'qwen38-main': {'parent': 'data/ingest_reviews/coverage/cassius-dio-qwen38-retry-jobs.json',
                 'regions': {'dio-cary-v9-pdf0179-reviewed-strip-2': [[0.04, 0.2795, 0.47, 0.34717],
                                                                      [0.04, 0.34717, 0.47, 0.44333],
                                                                      [0.04, 0.44333, 0.47, 0.51483]],
                             'dio-cary-v9-pdf0188-reviewed-strip-2': [[0.04, 0.3075, 0.47, 0.402],
                                                                      [0.04, 0.402, 0.47, 0.4745],
                                                                      [0.04, 0.4745, 0.47, 0.5685]],
                             'dio-cary-v9-pdf0192-reviewed-strip-3': [[0.04, 0.61717, 0.47, 0.71183],
                                                                      [0.04, 0.71183, 0.47, 0.8065],
                                                                      [0.04, 0.8065, 0.47, 0.91]],
                             'dio-cary-v9-pdf0193-reviewed-strip-1': [[0.04, 0.065, 0.47, 0.161],
                                                                      [0.04, 0.161, 0.47, 0.2575],
                                                                      [0.04, 0.2575, 0.47, 0.35167]],
                             'dio-cary-v9-pdf0201-reviewed-strip-1': [[0.04, 0.065, 0.47, 0.15317],
                                                                      [0.04, 0.15317, 0.47, 0.24783],
                                                                      [0.04, 0.24783, 0.47, 0.34283]],
                             'dio-cary-v9-pdf0201-reviewed-strip-2': [[0.04, 0.34283, 0.47, 0.43883],
                                                                      [0.04, 0.43883, 0.47, 0.53283],
                                                                      [0.04, 0.53283, 0.47, 0.62867]],
                             'dio-cary-v9-pdf0201-reviewed-strip-3': [[0.04, 0.62867, 0.47, 0.7225],
                                                                      [0.04, 0.7225, 0.47, 0.81833],
                                                                      [0.04, 0.81833, 0.47, 0.91]],
                             'dio-cary-v9-pdf0216-reviewed-strip-2': [[0.04, 0.30517, 0.47, 0.3995],
                                                                      [0.04, 0.3995, 0.47, 0.495],
                                                                      [0.04, 0.495, 0.47, 0.58867]]},
                 'pins': {'dio-cary-v9-pdf0179-reviewed-strip-2': '25a3c6255b4b40a6b7209a5fbdd361f20cc160141eefb94217da1f83b54d9246',
                          'dio-cary-v9-pdf0188-reviewed-strip-2': '07feffb95557d11efd8bd81ca3d7e68d164750ebef4fdafdd361cbf467744e6f',
                          'dio-cary-v9-pdf0192-reviewed-strip-3': '65ae331c0dcabe8b59c23b4ec1bf9fb0fb2e4c2f350c4feaaf579c35547f0499',
                          'dio-cary-v9-pdf0193-reviewed-strip-1': 'c5a9200262580862e97479a94eb8b600e043cf6d09ed1287b2331463fb16b1e5',
                          'dio-cary-v9-pdf0201-reviewed-strip-1': 'b794c8a4003ddc2709ab66842df1dd97f15713c6ae6105d2d85495c730132bcd',
                          'dio-cary-v9-pdf0201-reviewed-strip-2': 'de33c5d5b084825b1bf1d61cf1845838d4ec7d8b27e80d929f0133918fdfecc2',
                          'dio-cary-v9-pdf0201-reviewed-strip-3': 'da633602091d71c89236dbdded85bdd93f5d2c3353f44db07f593ed47eceb19d',
                          'dio-cary-v9-pdf0216-reviewed-strip-2': '58a578ce8c15d12b6e1dbeda0496d04247fff64588ad4066634938ed9d4612e8'},
                 'parent_sha256': 'd97e081912f3b45da68370f59eed1768d8c911af44b0323258443aaeb63ac029'},
 'qwen36-supplementary': {'parent': 'data/ingest_reviews/coverage/cassius-dio-qwen36-supplementary-retry-jobs.json',
                          'regions': {'dio-cary-v2-pdf0195-comparison-supplement-strip-1': [[0.04,
                                                                                             0.4542,
                                                                                             0.47,
                                                                                             0.5085],
                                                                                            [0.04,
                                                                                             0.5085,
                                                                                             0.47,
                                                                                             0.56],
                                                                                            [0.04,
                                                                                             0.56,
                                                                                             0.47,
                                                                                             0.6115]]},
                          'pins': {'dio-cary-v2-pdf0195-comparison-supplement-strip-1': 'a4626d41a892ead6dfb57c764799101ddcbaf13632f6ad3bfe654cd3da7072ea'},
                          'parent_sha256': 'd21af7f7b4c6a9b9f1eedab7e69d6b09238012df01d00c70a03e3282e17f765f'},
 'qwen38-supplementary': {'parent': 'data/ingest_reviews/coverage/cassius-dio-qwen38-supplementary-retry-jobs.json',
                          'regions': {'dio-cary-v2-pdf0195-comparison-supplement-strip-1': [[0.04,
                                                                                             0.4542,
                                                                                             0.47,
                                                                                             0.5085],
                                                                                            [0.04,
                                                                                             0.5085,
                                                                                             0.47,
                                                                                             0.56],
                                                                                            [0.04,
                                                                                             0.56,
                                                                                             0.47,
                                                                                             0.6115]]},
                          'pins': {'dio-cary-v2-pdf0195-comparison-supplement-strip-1': '7a1b29499750d0fa540211a2d6da1d129bf70d3e0af5f7138cdfa15e74627bdb'},
                          'parent_sha256': 'e6b9550f3cb4953d1d27929bd47281978c89fe2e25bccd00723e56493119813e'},
 'qwen38-child': {'parent': 'data/ingest_reviews/coverage/cassius-dio-qwen38-child-strip-retry-jobs.json',
                  'regions': {'dio-cary-v6-pdf0206-reviewed-strip-1-supplement-strip-1': [[0.04,
                                                                                           0.065,
                                                                                           0.47,
                                                                                           0.11],
                                                                                          [0.04,
                                                                                           0.11,
                                                                                           0.47,
                                                                                           0.13335],
                                                                                          [0.04,
                                                                                           0.13335,
                                                                                           0.47,
                                                                                           0.1558]]},
                  'pins': {'dio-cary-v6-pdf0206-reviewed-strip-1-supplement-strip-1': '07e00dfacf8e27894efd823c77d598cbf47e9b7fb8995f097f72211d7cd8a714'},
                  'parent_sha256': '7a1abf750af835b01493ffa849e1fa07bfb75eccbc951fc2a0df3ef7c0383218'}}
EVIDENCE = [{'description': 'finer-seams-01.png; source-rendered internal whitespace boundaries, inspected against the '
                 'complete parent crop.',
  'sha256': '44fc53faf6eaaf79abae3a094077c563e419cb47246d77e28d0ddca47a85e6b2'},
 {'description': 'finer-seams-02.png; source-rendered internal whitespace boundaries, inspected against the '
                 'complete parent crop.',
  'sha256': 'bdbf0f9d9f9313a2083cc165e89af3470eb18ea5deb41d83cc3e18bd21e30f71'},
 {'description': 'finer-seams-03.png; source-rendered internal whitespace boundaries, inspected against the '
                 'complete parent crop.',
  'sha256': 'a1a5a973ca0786567d200c846abba8df0ebdb1469dd650f0a4ce4f4dc0c896f0'},
 {'description': 'Final VI206 one-line grandchild boundaries .11 and .13335, replacing preliminary '
                 'empty-margin proposal.',
  'sha256': '5efbc37e6bf5ac07410c80b8c837d0b1310fb1661c147511668195384e7c5c52'}]
OUTPUTS = {
    "qwen38-main": "cassius-dio-qwen38-main-finer-child-jobs.json",
    "qwen36-supplementary": "cassius-dio-qwen36-supplementary-finer-child-jobs.json",
    "qwen38-supplementary": "cassius-dio-qwen38-supplementary-finer-child-jobs.json",
    "qwen38-child": "cassius-dio-qwen38-vi206-grandchild-jobs.json",
}
PROMPT = ("Transcribe this narrow Greek body strip exactly, preserving EVERY printed "
    "accent and breathing mark, including on short fragments. For each printed "
    "lacuna-dot run output exactly ONE ellipsis character … instead of repeated "
    "full stops. Keep every visible Greek fragment before and after each gap. "
    "This is an explicit punctuation normalization; the original finite dot runs "
    "remain in the source image. Never expand a gap, guess missing text, or repeat "
    "a word or line. Preserve source credits, reference numbers and printed hyphens. "
    "Do not join a word across the image boundary. Return only this transcription.")


def finding(identifier):
    if identifier.startswith("dio-cary-v2-"):
        return "Source-confirmed polytonic loss in the first enlarged Zonaras9.27 strip: the printed breathings and accents remain visible on short Greek lines. Frozen200-letter applicability does not certify this shorter strip. Retain the exact parent and refine its source geometry without altering successful siblings."
    if identifier.startswith("dio-cary-v6-"):
        return "The first child of Cary VI402 still loses printed breathings (106 Greek letters, zero breathings). Its three source rows print πόλει, κἀκ, ἄλλα and ὕπατον. This review is based on source pixels, even though the frozen detector abstains below200 letters. Three one-line children preserve all body and parent boundaries."
    if identifier.startswith("dio-cary-v9-pdf0193"):
        return "The first Cary IX376 retry strip stops but strips printed polytonic marks (176 Greek letters, one accent and zero breathings). The source visibly prints τῇ τε ἐπὶ, ἔγραψεν ἁπλῶς, ἐποίησε and ὑπώπτευσαν ὥστε καὶ δημοσιευθῆναι. The source review applies despite the frozen200-letter applicability limit."
    return "The completed parent strip expands an unprinted full-stop series and omits later visible Greek lines or fragments. Source inspection confirms finite lacuna bands and the omitted following text. Three narrower children exactly partition the parent at reviewed gaps; one ellipsis per printed dot run is an explicit punctuation normalization, with every source pixel and original reading retained."


def prepare(root, original_paths, pdf_dir, output_dir):
    originals = load_originals(original_paths)
    results = {}
    for key, profile in PROFILES.items():
        raw = (root / profile["parent"]).read_bytes()
        if sha(raw) != profile["parent_sha256"]:
            raise ValueError("A source-reviewed immediate parent request changed")
        parent = json.loads(raw)
        family = key.split("-", 1)[0]
        model, revision = CHECKPOINTS[family]
        pages = {p["id"]: p for p in parent["pages"]}
        checked, jobs = {}, []
        for identifier, artifact in profile["pins"].items():
            if artifact not in originals:
                raise ValueError("Missing exact held parent strip: " + identifier)
            metadata, row = originals[artifact]
            page = pages[identifier]
            if ((metadata.get("model"), metadata.get("revision"), metadata.get("manifest_sha256")) !=
                    (model, revision, profile["parent_sha256"]) or row.get("finish_reason") != "stop" or row.get("error") or
                    (row.get("id"), row.get("source"), row.get("scan_page"), row.get("region")) !=
                    (identifier, page["source"], page["scan_page"], page["region"])):
                raise ValueError("The reviewed defective parent outcome changed")
            source = parent["sources"][page["source"]]
            if sha((pdf_dir / (page["source"] + ".pdf")).read_bytes()) != source["sha256"]:
                raise ValueError("A reviewed source PDF changed")
            regions = profile["regions"][identifier]
            if (regions[0][:3] != page["region"][:3] or regions[-1][3] != page["region"][3]
                    or any(a[3] != b[1] for a,b in zip(regions, regions[1:]))):
                raise ValueError("Children no longer partition the exact parent")
            checked[identifier] = {"artifact_sha256": artifact, "original_metadata": metadata,
                "original_prediction": row, "source_evidence": finding(identifier),
                "source_pdf_sha256": source["sha256"], "original_region": page["region"],
                "retry_regions": regions}
            for order, region in enumerate(regions, 1):
                jobs.append({**page, "id": identifier + f"-finer-child-{order}",
                    "reconstructs": identifier, "reading_order": order,
                    "region": region, "max_side": 3200, "prompt_suffix": PROMPT})
        request = {"schema_version": 1, "generated_by": "scripts/prepare_dio_finer_children.py",
            "purpose": "Source-reviewed child attempts for exact stop-terminated omissions or mark loss; every immediate parent remains held evidence.",
            "sources": parent["sources"], "prompt": parent["prompt"],
            "retry_of": {"path": profile["parent"], "sha256": profile["parent_sha256"],
                "model": model, "revision": revision, "region_ids": list(profile["pins"])},
            "review": {"reviewed_at": "2026-10-18", "original_predictions": checked,
                "source_rendered_evidence": EVIDENCE,
                "policy": "Replace only these exact parent strips after every completed child passes source comparison. Preserve successful siblings, every held attempt, source references and independent checkpoints. These children add no voting family.",
                "punctuation_normalization": {"original": "Each finite printed lacuna-dot run in the pinned image",
                    "corrected": "One U+2026 ellipsis per run", "source": "Manual inspection of the hash-pinned Cary source crops", "reviewed_at": "2026-10-18", "reversal": "Recover original finite dots from the retained image; all original and parent OCR text remains archived unchanged."}},
            "nonlexical_source_regions": {}, "pages": jobs}
        path = output_dir / OUTPUTS[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode(request));results[key] = request
    registry = {"schema_version": 1,
        "page_requests": {key: DIRECTORY + "/cassius-dio-" + family + suffix + "-retry-jobs.json"
            for key,family,suffix in [("qwen36_main","qwen36",""),("qwen36_supplementary","qwen36","-supplementary"),("qwen38_main","qwen38",""),("qwen38_supplementary","qwen38","-supplementary")]},
        "child_requests": {"qwen38_vi206_first": DIRECTORY + "/cassius-dio-qwen38-child-strip-retry-jobs.json",
            **{key.replace("-", "_"): DIRECTORY + "/" + name for key,name in OUTPUTS.items()}}}
    (output_dir / "cassius-dio-retry-authorities.json").write_bytes(encode(registry))
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, action="append", required=True)
    p.add_argument("--pdf-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=ROOT / DIRECTORY)
    a = p.parse_args();r = prepare(ROOT, a.original, a.pdf_dir, a.output_dir)
    print(json.dumps({key: len(value["pages"]) for key,value in r.items()}))


if __name__ == "__main__":
    main()
