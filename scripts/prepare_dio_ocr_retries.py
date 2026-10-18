#!/usr/bin/env python3
"""Reproduce checkpoint-specific Dio retries from source-reviewed strip boundaries."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = "data/ingest_reviews/coverage"
MANIFEST = DIRECTORY + "/cassius-dio-reviewed-ocr-jobs.json"
MANIFEST_SHA256 = "e3ffc58c93811a2f7dd851a76f216caa504a31b23e63be6d7c19b9b072dd41e0"
CHECKPOINTS = {
    "qwen36": ("Qwen/Qwen3.6-27B-FP8", "e89b16ebf1988b3d6befa7de50abc2d76f26eb09"),
    "qwen38": ("Qwen/Qwen3.8-27B-FP8", "017b9c7af6b5689d5dd426a76e0bc077eb5ca20a"),
}
# These are per-record pins, including the exact original runtime metadata.
# A still-growing sibling part never changes a reviewed page's identity.
ORIGINAL_PINS = {'qwen36': {'dio-cary-v9-pdf0179': 'f8de791142465ecc8188737b945a077ba76a6e6942a7f92e762058d7bf707c27',
            'dio-cary-v9-pdf0188': 'fb1a802ee1fc51a53d3d81aa781936de822183e3cc6c94c65d610a5532261f06',
            'dio-cary-v9-pdf0187': '16a32e1338b6ac1bfbe69ad99154c2bedfc15e284821de20551c2544e161b1ae',
            'dio-cary-v9-pdf0192': '2b63b2b4a16bdeee324a20b4b4ca31eb31c469cd804a278aba1fda40cc1bb816',
            'dio-cary-v9-pdf0193': '22dbab0ba10b49a7e96fd08a3f96497ea0a6b2b8f1b34d405f85fa5084f131bf',
            'dio-cary-v9-pdf0201': 'b3e73dd41af7b521c55306e0a8669919941fba43126dfd8878047fa32b2193ee',
            'dio-cary-v9-pdf0208': 'c8cc31aee464df05a85c4ef582adbc5186e4d27c9b1ebbe46228c0f11f830caa',
            'dio-cary-v9-pdf0205': 'd2b6f7f4bd9cbe2e21eec30f594473c02b9805de8798f3c2a954ce828d9d42d5',
            'dio-cary-v9-pdf0212': '71badbbd882184379db0e70190d3ceeba963da702efe31ce1bff292a7bfc78ce',
            'dio-cary-v9-pdf0216': '30a72c529daacb3e0528b42a7c536ed85f934caef2aa23c11c85272530e62e47',
            'dio-cary-v9-pdf0217': 'e538a89d89241a476be50261c6efc38cf9ba0e507b7d8863b2f1b8099e3b88cc',
            'dio-cary-v9-pdf0221': '561102a4c27c7c4e3c0ea4b10caabfae036a866aa077c968aaf2f262061347ba',
            'dio-cary-v9-pdf0226': '2750f676dc667613ed326211cc267339ddf1ae985238f83e39511f4408ed0bf0',
            'dio-cary-v9-pdf0231': 'f8e4e4a252a014de1befee69833ac6fb55b9eb94f3f54b40d4dfa9fea7926e3f'},
 'qwen38': {'dio-cary-v6-pdf0206': '4f2a5ee9641715320ccfc8d95c683e3aa02c1a7c8c2345c8e7c4ec002744f8ea',
            'dio-cary-v8-pdf0116': '1f3baef17b574be3db2c20b47eadd27fc266b3ce183e4b404388fb402fb72c38',
            'dio-cary-v9-pdf0179': '6564d14431d02029c5d1b62d32a66bd838f676137d8dfad6026971f16e14f8a4',
            'dio-cary-v9-pdf0178': '82cc0c02aa7641ed56765c20f35a038bb6ff1b4cf395b12dd55739d8d138b48c',
            'dio-cary-v9-pdf0188': 'b7b67a9439b2dad2fed2a8f84e964e90f044672a629e54f31a43b1aeba8660ce',
            'dio-cary-v9-pdf0187': '38bae89726b6623295b8e932b2bb7a847eeeb54f177dbc34eafe7daa3e934ae0',
            'dio-cary-v9-pdf0192': '625eb8f0ed1030a8d5a317bb34114db6b0bd774d0aff1e42dec10d4debc53181',
            'dio-cary-v9-pdf0193': 'ebf41735829815216a52041dba92b81f808f36cc72089506c9522d2273ca2a6d',
            'dio-cary-v9-pdf0196': '48d0c10fe1bd56b174fe1232715c54bc32c950a8d386fd06fc8d1d3fd1e12958',
            'dio-cary-v9-pdf0201': '5bc5f2d8bb3fb8d195b895d09d07df4378775e5501b07c55f9a61060d0398d96',
            'dio-cary-v9-pdf0208': 'a042b25f219c71d552505c6252dcd0511ab922ecafdc559f2f6926f1393426fd',
            'dio-cary-v9-pdf0205': '5f26cbb9d243e0a934f453dd76a25cb70e27680e991d8a64500deeb4f0e4f777',
            'dio-cary-v9-pdf0212': '99071f996b50ef9b015bfe688ce323a153bf2cd939580363cc54322bcb2c2471',
            'dio-cary-v9-pdf0210': 'fab457da56f7301244753cdf86d70f1e83e13bf1b1328b944ea80b7422c42b5d',
            'dio-cary-v9-pdf0213': '5c5540efb7f0290fe562958304f7813ef814632ef45619a32dafc964910250d6',
            'dio-cary-v9-pdf0216': '241e831e0b9357b5c262188dacb7445d81af6a1ebd0d1a9681fb0a0ca7fe27ec',
            'dio-cary-v9-pdf0217': 'e54023e632ebd5d008a1ba05a8533ef5af9d9967896ff833317ffa94fb92cebd',
            'dio-cary-v9-pdf0226': 'b8cce1d1e08195dff027617e13f4aae2cc14133cd278e97a08cc892e2c7c074a'}}

# All forty internal edges were inspected in the source pixels. Every finite
# lacuna-dot row remains inside one strip; there are no omitted gap bands.
REGIONS = {'dio-cary-v6-pdf0206': [[0.04, 0.065, 0.47, 0.27083],
                         [0.04, 0.27083, 0.47, 0.452],
                         [0.04, 0.452, 0.47, 0.6725]],
 'dio-cary-v8-pdf0116': [[0.04, 0.065, 0.47, 0.31133],
                         [0.04, 0.31133, 0.47, 0.52783],
                         [0.04, 0.52783, 0.47, 0.77455]],
 'dio-cary-v9-pdf0178': [[0.04, 0.065, 0.47, 0.31567],
                         [0.04, 0.31567, 0.47, 0.59717],
                         [0.04, 0.59717, 0.47, 0.85841]],
 'dio-cary-v9-pdf0179': [[0.04, 0.065, 0.47, 0.2795],
                         [0.04, 0.2795, 0.47, 0.51483],
                         [0.04, 0.51483, 0.47, 0.76364]],
 'dio-cary-v9-pdf0187': [[0.04, 0.065, 0.47, 0.32817],
                         [0.04, 0.32817, 0.47, 0.56517],
                         [0.04, 0.56517, 0.47, 0.83409]],
 'dio-cary-v9-pdf0188': [[0.04, 0.065, 0.47, 0.3075],
                         [0.04, 0.3075, 0.47, 0.5685],
                         [0.04, 0.5685, 0.47, 0.81023]],
 'dio-cary-v9-pdf0192': [[0.04, 0.065, 0.47, 0.35804],
                         [0.04, 0.35804, 0.47, 0.61717],
                         [0.04, 0.61717, 0.47, 0.91]],
 'dio-cary-v9-pdf0193': [[0.04, 0.065, 0.47, 0.35167],
                         [0.04, 0.35167, 0.47, 0.63906],
                         [0.04, 0.63906, 0.47, 0.91]],
 'dio-cary-v9-pdf0196': [[0.04, 0.065, 0.47, 0.3455], [0.04, 0.3455, 0.47, 0.6315], [0.04, 0.6315, 0.47, 0.91]],
 'dio-cary-v9-pdf0201': [[0.04, 0.065, 0.47, 0.34283],
                         [0.04, 0.34283, 0.47, 0.62867],
                         [0.04, 0.62867, 0.47, 0.91]],
 'dio-cary-v9-pdf0205': [[0.04, 0.065, 0.47, 0.35533],
                         [0.04, 0.35533, 0.47, 0.61732],
                         [0.04, 0.61732, 0.47, 0.91]],
 'dio-cary-v9-pdf0208': [[0.04, 0.065, 0.47, 0.30183],
                         [0.04, 0.30183, 0.47, 0.53917],
                         [0.04, 0.53917, 0.47, 0.78409]],
 'dio-cary-v9-pdf0210': [[0.04, 0.065, 0.47, 0.30533],
                         [0.04, 0.30533, 0.47, 0.58933],
                         [0.04, 0.58933, 0.47, 0.85409]],
 'dio-cary-v9-pdf0212': [[0.04, 0.065, 0.47, 0.30567],
                         [0.04, 0.30567, 0.47, 0.552],
                         [0.04, 0.552, 0.47, 0.80636]],
 'dio-cary-v9-pdf0213': [[0.04, 0.065, 0.47, 0.32617],
                         [0.04, 0.32617, 0.47, 0.587],
                         [0.04, 0.587, 0.47, 0.83386]],
 'dio-cary-v9-pdf0216': [[0.04, 0.065, 0.47, 0.30517],
                         [0.04, 0.30517, 0.47, 0.58867],
                         [0.04, 0.58867, 0.47, 0.83955]],
 'dio-cary-v9-pdf0217': [[0.04, 0.065, 0.47, 0.32233],
                         [0.04, 0.32233, 0.47, 0.58183],
                         [0.04, 0.58183, 0.47, 0.84864]],
 'dio-cary-v9-pdf0221': [[0.04, 0.065, 0.47, 0.31083],
                         [0.04, 0.31083, 0.47, 0.5625],
                         [0.04, 0.5625, 0.47, 0.82682]],
 'dio-cary-v9-pdf0226': [[0.04, 0.065, 0.47, 0.3035],
                         [0.04, 0.3035, 0.47, 0.54083],
                         [0.04, 0.54083, 0.47, 0.78545]],
 'dio-cary-v9-pdf0231': [[0.04, 0.065, 0.47, 0.30939],
                         [0.04, 0.30939, 0.47, 0.52283],
                         [0.04, 0.52283, 0.47, 0.79795]]}
REVIEWED_AT = "2026-10-18"
SEAM_EVIDENCE = [
    {"sha256": "1d77e673681062e3ac82c37af7236d6fe77fc4ba7fd297c3d4aab907278bd145", "description": "Source-rendered seam details: VI206, VIII116, IX178/179/187, both edges per page."},
    {"sha256": "74215e9f6079bb041f3beb16ec71d1ebd7c0922f173c0ef04d688c04feca6578", "description": "Source-rendered seam details: IX188/192/193/196/201, both edges per page."},
    {"sha256": "383210eefa51a1f84077083a9f07c3077be628ff691789aedde6f1a2de0c5b93", "description": "Source-rendered seam details: IX205/208/210/212/213, both edges per page."},
    {"sha256": "601246568d14264a570286f670b113b8b853cd7ebbf85bb2a1a957256481a680", "description": "Source-rendered seam details: IX216/217/221/226/231, both edges per page."},
]
STRIP_PROMPT = ("This image is one enlarged strip of the reviewed Greek body. "
    "Copy every visible accent and breathing mark. Printed lacuna dots are finite: "
    "copy each visible dot sequence once, then continue immediately with the next "
    "visible word or printed line. Never extend or repeat a dot sequence, word, or line. "
    "Preserve source attribution references and printed hyphens. Do not join a word "
    "across the image boundary. Return only the transcription of this strip.")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode()


def source_evidence(identifier, row):
    if identifier == "dio-cary-v6-pdf0206":
        return ("Cary VI printed402 is polytonic throughout. The original Qwen3.8 output "
            "has severe breathing loss (four breathing marks among929 Greek letters). "
            "Both reviewed seams preserve complete printed lines, including the "
            "breathing above Ἀρμενίαν. The original 55.9.4 overlap remains evidence; "
            "only the existing uniquely anchored overlap rule may remove it later.")
    if identifier == "dio-cary-v8-pdf0116":
        return ("Cary VIII printed222 is polytonic throughout. The original Qwen3.8 "
            "output has973 Greek letters with no accents or breathing marks. The "
            "three strips retain the Xiphilinus and Zonaras reference line and all body.")
    if identifier == "dio-cary-v9-pdf0231":
        return ("Cary IX printed452 contains ordinary continuous Greek prose, with "
            "no printed lacuna-dot band. The pinned Qwen3.6 attempt repeats prose "
            "until its length limit. All body paragraphs and section numbers remain "
            "in three strips, whose two internal boundaries lie between complete "
            "printed lines. The reviewed bottom edge excludes editorial apparatus.")
    return ("Source inspection of the complete Cary IX Greek page confirms finite "
        "printed lacuna-dot series interspersed with Greek body, not an indefinitely "
        "repeated passage. The original pinned checkpoint reached its length limit "
        "while repeating dots or text. Both new internal crop edges lie between "
        "complete printed lines. All finite dot rows, Greek text, section numbers "
        "and attribution references remain in the three ordered strips. The "
        "previously reviewed bottom edge excludes editorial apparatus.")


def load_originals(paths):
    originals = {}
    for path in paths:
        values = [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]
        if not values or set(values[0]) != {"_meta"}:
            raise ValueError("Original OCR part lacks exact runtime metadata")
        metadata = values[0]["_meta"]
        for row in values[1:]:
            artifact = sha(encode({"metadata": metadata, "prediction": row}))
            if artifact in originals:
                raise ValueError("Repeated original prediction artifact")
            originals[artifact] = (metadata, row)
    return originals


def prepare(manifest_path, original_paths, pdf_dir, output_dir):
    manifest_raw = manifest_path.read_bytes()
    if sha(manifest_raw) != MANIFEST_SHA256:
        raise ValueError("The complete reviewed Dio manifest changed")
    prior = json.loads(manifest_raw)
    pages = {p["id"]: p for p in prior["pages"]}
    if len(prior["pages"]) != 1500 or len(pages) != 1500:
        raise ValueError("Dio retry retains the exact complete1500 request")
    originals = load_originals(original_paths)
    for source_id in {pages[identifier]["source"] for identifier in REGIONS}:
        if sha((pdf_dir / (source_id + ".pdf")).read_bytes()) != prior["sources"][source_id]["sha256"]:
            raise ValueError("A source-reviewed Dio PDF changed")
    result = {}
    for family, pins in ORIGINAL_PINS.items():
        model, revision = CHECKPOINTS[family]
        checked, jobs = {}, []
        for identifier, artifact in pins.items():
            if artifact not in originals:
                raise ValueError("Missing exact reviewed original artifact: " + identifier)
            metadata, row = originals[artifact]
            page = pages[identifier]
            if ((metadata.get("model"), metadata.get("revision")) != (model, revision)
                    or (row.get("id"), row.get("source"), row.get("scan_page"), row.get("region")) !=
                    (identifier, page["source"], page["scan_page"], page["region"])):
                raise ValueError("Original reviewed prediction changed source or checkpoint")
            degraded = identifier in {"dio-cary-v6-pdf0206", "dio-cary-v8-pdf0116"}
            if row.get("error") or row.get("finish_reason") != ("stop" if degraded else "length"):
                raise ValueError("Original reviewed outcome changed")
            checked[identifier] = {"artifact_sha256": artifact,
                "original_metadata": metadata, "original_prediction": row,
                "source_evidence": source_evidence(identifier, row),
                "source_pdf_sha256": prior["sources"][page["source"]]["sha256"],
                "original_region": page["region"], "retry_regions": REGIONS[identifier]}
            for order, region in enumerate(REGIONS[identifier], 1):
                jobs.append({**page, "id": identifier + f"-reviewed-strip-{order}",
                    "region": region, "max_side": 3200, "reading_order": order,
                    "reconstructs": identifier, "prompt_suffix": STRIP_PROMPT,
                    "crop_evidence": "Source-inspected gap between complete printed lines; no lacuna-dot row omitted."})
        request = {"schema_version": 1, "generated_by": "scripts/prepare_dio_ocr_retries.py",
            "purpose": "Source-reviewed enlarged Dio strips replacing only exact failed or degraded checkpoint/page inputs after completed comparison.",
            "sources": prior["sources"], "prompt": prior["prompt"],
            "retry_of": {"path": MANIFEST, "sha256": MANIFEST_SHA256,
                "model": model, "revision": revision, "region_ids": list(pins)},
            "review": {"reviewed_at": REVIEWED_AT,
                "extent": "Complete body of all20 distinct source pages and all40 internal seams inspected. Narrow top/side crops preserve every body line and section number; the prior reviewed bottom boundary remains unchanged.",
                "original_predictions": checked, "source_rendered_evidence": SEAM_EVIDENCE,
                "policy": "Retain all original predictions unchanged. Require every successful enlarged strip and an explicit completed source comparison before replacing one input from the same checkpoint. Keep independent checkpoints separate and every tied reading. Do not invent joined words across strips."},
            "nonlexical_source_regions": {}, "pages": jobs}
        path = output_dir / f"cassius-dio-{family}-retry-jobs.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encode(request))
        result[family] = request
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, default=ROOT / MANIFEST)
    p.add_argument("--original", type=Path, action="append", required=True, help="Retained original parts, repeated for both checkpoints")
    p.add_argument("--pdf-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, default=ROOT / DIRECTORY)
    a = p.parse_args()
    requests = prepare(a.manifest, a.original, a.pdf_dir, a.output_dir)
    print(json.dumps({key: {"pages": len(value["review"]["original_predictions"]), "strips": len(value["pages"])} for key, value in requests.items()}))


if __name__ == "__main__":
    main()
