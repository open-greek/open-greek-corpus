#!/usr/bin/env python3
"""Pin source-confirmed degraded OCR readings without inventing replacement text."""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_photius_geometry import ROOT, SOURCE_SHA, SOURCE_URL, known_geometry_supplement_manifests, known_gutter_manifests, known_followup_geometry_manifests

AUTHORITY = Path("data/ocr_requests/photius-source-abstentions.json")
REVIEWED = {
    "photius-bekker-0252-left-lower-gutter-part01": {
        "text_sha256": "b429d6110d43dc9874835b1f84d17ae592b1fb2010d5aaf2e49ee163e53ccdd3",
        "reason": "Source comparison confirms five faint continuous theological body lines. The outcome instead invents December25, a first-person vision, and a shield. The smaller finite remedy still does not transcribe this source span."},
    "photius-bekker-0252-left-lower-gutter-part02": {
        "text_sha256": "d6b27642beb07cfbc9ca26bcc80002e09f815b7b4f64baca0de595e15b27d15d",
        "reason": "Source comparison confirms the next five continuous body lines. The outcome instead invents repeated church clauses and Anglophones. Accents and breathing marks do not establish correspondence to the printed source."},
    "photius-bekker-0252-left-lower-gutter-part03": {
        "text_sha256": "cadea384fbbf7839622c028d73e6b46c3c25382237865c1cb903542d75ada129",
        "reason": "Source comparison confirms the final five lowercase continuous body lines. The outcome instead invents an uppercase decree with an unprinted heading. It cannot supply a reading or an omission vote."},
}


REVIEWED.update({'photius-bekker-0113-right-first-part02-part01-gutter': {'reason': 'Two faint printed rhetorical lines are '
                                                                    'replaced by unrelated theological '
                                                                    'wording about the true God and an '
                                                                    'evangelist. Complete finite retries '
                                                                    'remain retained; the exact unrelated '
                                                                    'current span abstains.',
                                                          'text_sha256': '63d1c5e95dd8df376cca9fe28be68a4f2edb32748db5a1e66abb3fa0c00833f0'},
 'photius-bekker-0113-right-first-part02-part02-gutter': {'reason': 'Two faint printed rhetorical lines are '
                                                                    'replaced by an invented imperial '
                                                                    'titulature naming Augustus, Caesar, '
                                                                    'Germanicus, Hadrian, Tiberius, and '
                                                                    'JohnScotia, ending in a doxology. This '
                                                                    'is unrelated to the source; finite '
                                                                    'retries are exhausted.',
                                                          'text_sha256': '48ead0dbb01f4475be3e0aca565c8af4b847745a875ad83ba35b22be7e1c6a53'},
 'photius-bekker-0232-left-lower-gutter-part01': {'reason': 'The source continues Eulogius theological prose '
                                                            'in five faint printed lines. The shorter '
                                                            'outcome substitutes a passage on universal '
                                                            'divine love that is not printed in this span. '
                                                            'The finite unrelated outcome remains raw and '
                                                            'abstains.',
                                                  'text_sha256': '82f471efb0909b31602d389bcd5463eb8d171732f64085f292afa2d38c7698f6'},
 'photius-bekker-0234-left-lower-gutter-part03': {'reason': 'The five faint printed source lines continue '
                                                            'the theological passage. The outcome invents a '
                                                            'long quoted testament and commands that are not '
                                                            'printed here; the shorter finite attempt '
                                                            'abstains.',
                                                  'text_sha256': '1aa439b8ba181cd74855c2d88a5d5ab851356fce20e3a7ca32f2b5be491ea2eb'},
 'photius-bekker-0234-left-middle-gutter-part02': {'reason': 'The printed theological span names JesusChrist '
                                                             'and discusses the Father; the outcome '
                                                             'substitutes JohnNeophytus, prophecy, an '
                                                             'apostle, provinces, and a household. Source '
                                                             'comparison confirms that this five-line '
                                                             'reading is unrelated.',
                                                   'text_sha256': 'c22a8f6e433b3e5ac52dc895c833d36304314e971cf2b523460e54456bf98a1b'},
 'photius-bekker-0234-left-middle-gutter-part03': {'reason': 'The printed five-line span continues '
                                                             'theological prose. The outcome instead invents '
                                                             'a furnace narrative about bronze, iron, and '
                                                             'silver absent from the source. The finite '
                                                             'shorter outcome abstains.',
                                                   'text_sha256': '529baf86c8125f3ce79cea15e37ce481dc5cb06d5cc70e1763004a34d54bdf9e'},
 'photius-bekker-0250-left-lower-gutter-part03': {'reason': 'The faint printed historical lines continue the '
                                                            'Sinope and Mithridates context. The outcome '
                                                            'substitutes Egyptian philosophy and chronicles '
                                                            'absent from this source span. It remains raw '
                                                            'without a reading or omission vote.',
                                                  'text_sha256': '85f1cab6acfc622debb192c7fa370cb040d38fe74c7aa99877749cf90badb64e'},
 'photius-bekker-0396-left-middle-gutter-part02': {'reason': 'The printed Greek historical body is replaced '
                                                             'by unrelated invented prose in Latin script. '
                                                             'The exact shorter outcome is retained and '
                                                             'abstains; no Greek text is reconstructed from '
                                                             'it.',
                                                   'text_sha256': '36391e557e03dc2eaf69849302d39f8bfaa0115a04aeb6955ab1a256a5ebe5ec'},
 'photius-bekker-0396-left-middle-gutter-part03': {'reason': 'The printed historical lines concern the '
                                                             'Viriathus and Roman context. The shorter '
                                                             'outcome invents biblicalZeus, David, Siloam, '
                                                             'and Ahab, which are absent from the source. '
                                                             'The finite unrelated outcome abstains.',
                                                   'text_sha256': 'fa2a65d636572a2990edef2710d9ddca48634dbe1f594c2b25bb249cd865efc1'}})

REVIEWED.update({'photius-bekker-0381-right-middle-part01-part01-gutter': {'classification': 'source-confirmed-systematic-mark-loss',
                                                           'reason': 'The tiny printed source span visibly '
                                                                     'preserves breathings in he, oimai, '
                                                                     'Aigaios twice, en, hai twice, allo '
                                                                     'twice, hyp, auton, and edeiknyto. The '
                                                                     'current finite remedy retains only one '
                                                                     'breathing while stripping the others; '
                                                                     'its size is below the frozen detector '
                                                                     'applicability floor. Preserve the '
                                                                     'source-corresponding degraded reading, '
                                                                     'but exclude it from votes rather than '
                                                                     'certify it as mark-complete.',
                                                           'text_sha256': '6895e2d3691d7307e73f08c608fc4109b5d8bb539b7f2e97121a83fdb57bba0e'}})

REVIEWED.update({'photius-bekker-0381-right-lower-gutter': {'classification': 'source-confirmed-line-order-error',
                                            'reason': 'The source has two short phrases at the opening of '
                                                      'this body span. The current reading displaces them to '
                                                      'its end (raw ending: ekdyn dote moi ten / Deixoi), '
                                                      'leaving them in incorrect positions. Preserve the '
                                                      'full raw alternative and every finite ancestor, but '
                                                      'withhold this entire exact current leaf from reading '
                                                      'and omission votes. The independent source reading '
                                                      'retains its actual single-witness support; no manual '
                                                      'word reordering or synthetic replacement is '
                                                      'performed.',
                                            'text_sha256': '1fc5abb15c9c45bf0e14b8a109c8ce16a8fca35edaa23a59b79436c97509447e'}})

def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def build(paths):
    catalog = {**known_gutter_manifests(), **known_followup_geometry_manifests(), **known_geometry_supplement_manifests()}
    found = {}
    for path in paths:
        raw = path.read_bytes(); lines = raw.splitlines()
        if not lines:
            continue
        meta = json.loads(lines[0]).get("_meta", {})
        authority = catalog.get(meta.get("manifest_sha256"))
        if authority is None:
            continue
        manifest = authority[1]
        jobs = {job["id"]: job for job in manifest["pages"]}
        for line in lines[1:]:
            row = json.loads(line); identifier = row.get("id")
            if identifier not in REVIEWED:
                continue
            review = REVIEWED[identifier]; text = row.get("raw_prediction")
            job = jobs[identifier]
            checkpoint = {"model": meta.get("model"), "revision": meta.get("revision")}
            prompt = manifest["prompt"] + " " + job["prompt_suffix"]
            if (identifier in found or checkpoint not in manifest["checkpoints"]
                    or not isinstance(text, str) or sha(text.encode()) != review["text_sha256"]
                    or row.get("finish_reason") != "stop" or row.get("error")
                    or row.get("region") != job["region"] or row.get("source") != job["source"]
                    or row.get("scan_page") != job["scan_page"] or row.get("prompt_sha256") != sha(prompt.encode())):
                raise ValueError("Abstention differs from its exact source-reviewed reading")
            found[identifier] = {"id": identifier, **checkpoint, "manifest_sha256": meta["manifest_sha256"],
                "scan_page": row["scan_page"], "region": row["region"], "source": row["source"],
                "source_pdf_sha256": SOURCE_SHA, "image_sha256": row["image_sha256"],
                "raw_file_sha256": sha(raw), "prediction_record_sha256": sha(line),
                "raw_prediction_sha256": review["text_sha256"], "finish_reason": row["finish_reason"],
                "original_text": text, "voting_text": "", "reason": review["reason"],
                "reviewed_at": "2026-10-18", "classification": review.get("classification", "source-confirmed-unrelated-reading")}
    if set(found) != set(REVIEWED):
        raise ValueError("Every source-reviewed abstention needs its exact retained outcome")
    return {"schema_version": 1, "kind": "photius-source-confirmed-abstentions",
        "source_pdf": {"url": SOURCE_URL, "sha256": SOURCE_SHA}, "reviewed_at": "2026-10-18",
        "records": [found[key] for key in sorted(found)],
        "policy": "Retain the complete original readings and every ancestor. These exact source-confirmed degraded spans abstain rather than vote for a reading or omission; all other independent readings retain their actual support. No corrected text or token majority is invented.",
        "generated_by": "scripts/photius_source_abstentions.py"}


def source_authority():
    path = ROOT / AUTHORITY
    return (AUTHORITY.as_posix(), path.read_bytes()) if path.exists() else (None, None)


def known_abstentions():
    _, raw = source_authority()
    if raw is None:
        return {}
    authority = json.loads(raw)
    if (authority.get("kind") != "photius-source-confirmed-abstentions"
            or authority.get("source_pdf") != {"url": SOURCE_URL, "sha256": SOURCE_SHA}
            or {r["id"] for r in authority["records"]} != set(REVIEWED)):
        raise ValueError("Unknown source-confirmed abstention authority")
    result = {}
    for row in authority["records"]:
        review = REVIEWED[row["id"]]
        if (row["voting_text"] != "" or row["reason"] != review["reason"]
                or row.get("classification") != review.get("classification", "source-confirmed-unrelated-reading")
                or sha(row["original_text"].encode()) != review["text_sha256"]
                or row["raw_prediction_sha256"] != review["text_sha256"]):
            raise ValueError("Source abstention changes its original reading or reason")
        key = (row["model"], row["revision"], row["manifest_sha256"], row["id"])
        if key in result:
            raise ValueError("Repeated source-confirmed abstention")
        result[key] = row
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--extend", action="store_true", help="Add reviewed cases while preserving every existing exact record")
    args = parser.parse_args()
    report = build(sorted(args.raw_dir.rglob("*.jsonl")))
    raw = encode(report); path = ROOT / AUTHORITY
    if args.write:
        if path.exists() and path.read_bytes() != raw:
            previous = json.loads(path.read_bytes())
            current = {r["id"]: r for r in report["records"]}
            if not args.extend or any(current.get(r["id"]) != r for r in previous["records"]):
                raise ValueError("Refusing to change an already pinned abstention authority")
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
    print(json.dumps({"source_confirmed_abstentions": len(report["records"]), "written": args.write}))


if __name__ == "__main__":
    main()
