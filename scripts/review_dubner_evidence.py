"""Reversible continuation of the Dübner source, layout, and reading review.

Complete column extracts supply one vote per original extraction group. Narrow
duplicate snippets remain attributed raw evidence, outside reading and omission
votes. Printed occurrence decisions preserve the prior slot and all variants.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import json
from pathlib import Path
import tempfile
import unicodedata

import dubner_evidence_observations as observations
import repair_dubner_readings as previous
from experiment_dubner_alignment import diagnostics, line_cells
from ocr_consensus import compact_corpus_consensus, lexical_eligible, merge_witnesses

ROOT, AUDIT = observations.ROOT, observations.AUDIT
AUTHORITY, BEFORE = AUDIT + "/changes.json", AUDIT + "/before.json.gz"
NETWORKS, RECORDS = AUDIT + "/word-networks.json.gz", AUDIT + "/records.jsonl.gz"
ASSESSMENT = AUDIT + "/assessment.json"
sha, encoded, jsonl, publish, local_path = previous.sha, previous.encoded, previous.jsonl, previous.publish, previous.local_path
QUALIFICATION = (
    "Three source-reviewed partial-duplicate column extractions are separated into complete "
    "column projections and literal clipped-snippet evidence. The latter supplies neither "
    "extra occurrences nor reading or omission votes. Complete extracts retain both original "
    "extraction groups and every unresolved full-column variant. Forty-nine printed reading "
    "decisions retain original slots and contrary readings. The notes and indexes are "
    "locators, not additional historical attestations or independent editions. No editorial "
    "emendation is adopted. Other spellings remain unassessed; disagreement is not an error rate."
)


def recipe_pins():
    return {name:sha((Path(__file__).parent/name).read_bytes()) for name in (
        "review_dubner_evidence.py","dubner_evidence_observations.py",
        "capture_dubner_evidence.py","dubner_current_state.py","ocr_consensus.py",
        "citation_alias_state.py")}


@contextmanager
def predecessor_view(root, before):
    root = Path(root)
    if all((local_path(root,name).read_bytes() if local_path(root,name).is_file() else None) == raw
            for name,raw in before.items() if raw is not None):
        yield root
        return
    from citation_alias_state import _overlay
    with tempfile.TemporaryDirectory(prefix="dubner-evidence-predecessor-") as temporary:
        view = Path(temporary)
        _overlay(root,view,{Path(name).parts:raw for name,raw in before.items() if raw is not None})
        yield view


def sources(root):
    from capture_dubner_evidence import check, MANIFEST
    manifest = check(root)
    paths = [MANIFEST,*(item["path"] for item in manifest["files"])]
    for decision in observations.LAYOUTS.values():
        paths.extend(f"data/corpus_changes/dubner-layout-review/pages/{scan}-{page:04d}.png"
            for scan,page in zip(("toronto","harvard"),decision["pages"]))
    return {name:sha(local_path(root,name).read_bytes()) for name in sorted(set(paths))}


def route_columns(witness, key, *, recorded_at):
    """Separate reviewed clipped duplicate cells; keep the entire literal lane.

    This function accepts only the explicitly enumerated three source decisions.
    A new nonblank cell, missing fragment, changed row count, or extra delimiter
    fails closed. No source character is replaced and no witness is added.
    """
    decision = observations.LAYOUTS[key]
    if not witness["vote_group"].endswith("harvard") or len(witness["text"].splitlines()) != decision["lines"]:
        raise ValueError("Reviewed Dübner column witness changed")
    parts = line_cells(witness)
    content = [p for p in parts if p["cell"] not in {"delimiter","line-ending"} and p["text"].strip()]
    excluded = {(line,decision["column"]) for line in decision["duplicate_lines"]}
    if not excluded <= {(p["line"],p["cell"]) for p in content}:
        raise ValueError("A reviewed duplicate fragment is missing")
    complete, snippets = [], []
    for part in content:
        (snippets if (part["line"],part["cell"]) in excluded else complete).append(part)
    if any(p["cell"] == decision["column"] and
            (p["line"] >= 54 if key == "equites:0094" else True) for p in complete):
        raise ValueError("An unreviewed duplicate-column cell cannot be admitted")
    expected = {"equites:0094":107,"equites:0107":67,"aves:0271":55}[key]
    if len(complete) != expected:
        raise ValueError("Reviewed full-column cell accounting changed")
    if "".join(p["text"] for p in parts) != witness["text"]:
        raise ValueError("Column review lost literal source characters")
    text = "\n".join(p["text"] for p in complete)
    record = {"page_key":key,"recorded_at":recorded_at,
        "original_witness":deepcopy(witness),"parts":parts,
        "complete_cells":[[p["line"],p["cell"]] for p in complete],
        "duplicate_fragments":[{**deepcopy(p),"source_column":decision["column"],
            "disposition":"clipped-duplicate-column-extract-outside-lexical-voting",
            "qualification":"Literal alternative reading retained; the crop does not establish a separate occurrence or an independent vote."} for p in snippets],
        "source_pages":[{"scan":scan,"pdf_page":page,
            "capture":f"data/corpus_changes/dubner-layout-review/pages/{scan}-{page:04d}.png"}
            for scan,page in zip(("toronto","harvard"),decision["pages"])],
        "evidence":decision["observation"],"original_text_sha256":sha(witness["text"].encode()),
        "projected_text_sha256":sha(text.encode()),"generated_separator":"\n"}
    projected = deepcopy(witness)
    projected.update(text=text,source_artifact_sha256=witness["artifact_sha256"],
        artifact_sha256=sha(encoded(record)),
        duplicate_column_review={"authority":AUTHORITY,"page_key":key,
            "record_sha256":sha(encoded(record)),"original_text_sha256":record["original_text_sha256"]})
    projected.pop("text_sha256",None)
    return projected,record


def render(result):
    display, lexical = [], []
    for slot in result["ocr_consensus"]["slots"]:
        if "dubner_evidence_review" in slot:
            display.append(slot["selected"])
        elif slot["status"] == "unresolved":
            display.append("⟦"+" ∥ ".join(form or "∅" for form in slot["tied_readings"])+"⟧")
        elif slot["status"] != "omission":
            reading = next(r for r in slot["readings"] if r["text"] == slot["selected"])
            counts = Counter(reading["surfaces"].values())
            winners = sorted(s for s,n in counts.items() if n == max(counts.values()))
            display.append(winners[0] if len(winners) == 1 else "⟦"+" ∥ ".join(winners)+"⟧")
        if slot["lexical_eligible"]:
            lexical.append(slot["selected"])
    result.update(text=" ".join(display),analysis_text=" ".join(lexical))
    result["ocr_consensus"]["counts"] = dict(Counter(s["status"] for s in result["ocr_consensus"]["slots"]))
    return result


def adjudicate(result, decision, *, recorded_at):
    key,position,expected,corrected,column,additional = decision
    slot = result["ocr_consensus"]["slots"][position]
    if slot["status"] != "unresolved" or tuple(slot["tied_readings"]) != expected:
        raise ValueError(f"Dübner source occurrence changed: {key}:{position}")
    if not lexical_eligible(corrected) or slot["terminal_fragment_support"]:
        raise ValueError("A source letter decision cannot complete a page-end fragment")
    page = int(key.rsplit(":",1)[1])
    capture = f"toronto-{page:04d}-{column}" if key != "vespae:0190" else "toronto-0190-phorbeia"
    captures = list(dict.fromkeys([capture,*additional]))
    if not set(captures) <= observations.CAPTURES.keys():
        raise ValueError("Source occurrence lacks a retained capture")
    record = {"page_key":key,"slot_position":position,"recorded_at":recorded_at,
        "original_text":"⟦"+" ∥ ".join(s or "∅" for s in expected)+"⟧",
        "corrected_text":corrected,"original_slot":deepcopy(slot),
        "decision":"direct-inspection-of-printed-occurrence",
        "source_captures":captures,"authority":AUTHORITY,
        "qualification":"The printed body controls this occurrence. Index and annotation hits are locators; no modern emendation or additional OCR vote is inferred."}
    slot["dubner_evidence_review"] = deepcopy(record)
    slot.update(selected=corrected,status="source-reviewed",lexical_eligible=True,lexical_exclusion=None)
    return record


def kappa_chi_inventory(networks):
    """Locate exact κ/χ ties without selecting a word or inferring an error."""
    candidates = []
    for key,result in sorted(networks.items()):
        for slot in result["ocr_consensus"]["slots"]:
            forms = [form for form in slot["tied_readings"] if form]
            if (slot["status"] == "unresolved" and len(forms) == 2
                    and forms[0].replace("χ","κ").replace("Χ","Κ") == forms[1].replace("χ","κ").replace("Χ","Κ")):
                candidates.append({"page_key":key,"slot_position":slot["position"],"readings":forms})
    pairs = Counter(tuple(c["readings"]) for c in candidates)
    return {"slots":len(candidates),"pages":len({c["page_key"] for c in candidates}),
        "most_frequent_pairs":[{"readings":list(pair),"slots":n} for pair,n in sorted(pairs.items(),key=lambda p:(-p[1],p[0]))[:25]],
        "candidates":candidates,"qualification":"Exact κ/χ disagreement candidates, including valid alternatives such as οὐκ/οὐχ. No global substitution is approved."}


def evidence_hits(root):
    """Keep source-specific OCR locators from annotations and indexes separate."""
    def normalize(text):
        return "".join(c for c in unicodedata.normalize("NFD",text.lower()) if unicodedata.category(c) != "Mn")
    hits = []
    for line in (Path(root)/"data/paratext/dubner-1855-editorial.jsonl").read_bytes().splitlines():
        row = json.loads(line)
        if (row["witness_group"] == "dubner-1855-toronto" and
                row["source_pdf_page"] in {449,767} and
                any(term in normalize(row["text"]) for term in ("αφελ","φορδ","φορβ"))):
            hits.append({key:row[key] for key in ("locus","text","source_pdf_page","source_role","witness_group")})
    return hits


def build(root, before, *, recorded_at):
    root = Path(root)
    if sha((root/previous.AUDIT/"changes.json").read_bytes()) != observations.PREDECESSOR_AUTHORITY:
        raise ValueError("Dübner predecessor authority changed")
    raw = (root/previous.NETWORKS).read_bytes()
    if sha(raw) != observations.PREDECESSOR_NETWORK:
        raise ValueError("Dübner predecessor vote network changed")
    pins = sources(root)
    with predecessor_view(root,before) as view:
        old,_ = previous.checked_state(view)
        import dubner_layers
        metadata = dubner_layers.metadata(view)
    networks = json.loads(gzip.decompress(raw))
    baseline = deepcopy(networks)
    routes,changes = [],[]
    for key in observations.LAYOUTS:
        witnesses = []
        for witness in networks[key]["ocr_consensus"]["witnesses"]:
            if witness["vote_group"].endswith("harvard"):
                projected,record = route_columns(witness,key,recorded_at=recorded_at)
                witnesses.append(projected); routes.append(record)
            else:
                witnesses.append(deepcopy(witness))
        if sum(record["page_key"] == key for record in routes) != 1:
            raise ValueError("Each reviewed layout must have exactly one literal Harvard lane")
        result = merge_witnesses(witnesses)
        result["ocr_consensus"]["duplicate_column_evidence"] = [r for r in routes if r["page_key"] == key]
        networks[key] = result
    layout_counts = dict(sum((Counter(r["ocr_consensus"]["counts"]) for r in networks.values()),Counter()))
    for decision in observations.READINGS:
        changes.append(adjudicate(networks[decision[0]],decision,recorded_at=recorded_at))
    changed = set(observations.LAYOUTS) | {d[0] for d in observations.READINGS}
    for key in changed:
        render(networks[key])
    outputs,works = {},{}
    for name,raw in before.items():
        rows = [json.loads(line) for line in raw.splitlines()]
        for row in rows:
            key = row["dubner_scope_review"]["network_key"]
            if key in changed:
                row.update(compact_corpus_consensus(networks[key],{"path":NETWORKS,"key":key}))
                row["dubner_evidence_review"] = {"authority":AUTHORITY,"network_key":key}
                row["corrections"] = sorted(set(row.get("corrections",[])) | {"manual"})
        outputs[name] = jsonl(rows) if any(r["dubner_scope_review"]["network_key"] in changed for r in rows) else raw
        slug = rows[0]["urn"]
        works[slug] = {k:metadata[slug][k] for k in ("primary_rows","secondary_rows")}
        works[slug].update(analysis_tokens=sum(len(previous.base.GREEK.findall(r["analysis_text"])) for r in rows),
            surface_tokens=sum(len(previous.base.GREEK.findall(r["text"])) for r in rows),
            counts=dict(sum((Counter(r["ocr_consensus"]["counts"]) for r in rows),Counter())))
    statuses = dict(sum((Counter(r["ocr_consensus"]["counts"]) for r in networks.values()),Counter()))
    assessment = diagnostics(networks)
    assessment.pop("candidates",None)
    counts = {"works":len(works),"primary_rows":sum(w["primary_rows"] for w in works.values()),
        "previous_review_counts":deepcopy(old["counts"]),"changed_pages":len(changed),
        "approved_layout_pages":old["counts"]["approved_layout_pages"]+len(routes),
        "source_observations":old["counts"]["source_observations"]+len(changes),
        "primary_source_observations":old["counts"]["primary_source_observations"]+len(changes),
        "outside_primary_observations":old["counts"]["outside_primary_observations"],
        "source_reviewed_slots":statuses["source-reviewed"],
        "partial_duplicate_layouts_reviewed":len(routes),"held_layout_pages":0,
        "retained_duplicate_fragments":sum(len(r["duplicate_fragments"]) for r in routes),
        "new_source_reviewed_slots":len(changes),"reading_statuses":statuses,
        "baseline_reading_statuses":old["counts"]["reading_statuses"],
        "layout_only_reading_statuses":layout_counts,
        "unresolved_reduction":old["counts"]["reading_statuses"]["unresolved"]-statuses["unresolved"],
        "analysis_tokens":sum(w["analysis_tokens"] for w in works.values()),
        "remaining_unresolved_categories":assessment["unresolved_categories"]}
    assessment.update(review_scope="Three held partial-duplicate layouts and 49 exact printed occurrences, including the index-linked φορβειά passages; no exhaustive proofreading claim.",
        qualification=QUALIFICATION,held_layouts=[],
        reopening_circumstances=["New occurrence-specific scan evidence resolves a remaining reading.",
            "A source capture, duplicate-fragment classification, or occurrence anchor is invalidated; unapply this layer before replacing its authority."],
        kappa_chi_baseline=kappa_chi_inventory(baseline),kappa_chi_remaining=kappa_chi_inventory(networks),
        editorial_source_review=deepcopy(observations.NOTE_REVIEW),editorial_ocr_locators=evidence_hits(root),
        source_review_deferred=json.loads((root/previous.ASSESSMENT).read_bytes())["source_review_deferred"])
    records = [{"kind":"layout",**r} for r in routes]+[{"kind":"reading",**c} for c in changes]
    outputs.update({NETWORKS:gzip.compress(encoded(networks),mtime=0),
        RECORDS:gzip.compress(jsonl(records),mtime=0),ASSESSMENT:encoded(assessment)})
    return outputs,works,counts,pins


def archived_inputs(root):
    document = json.loads(gzip.decompress((Path(root)/BEFORE).read_bytes()))
    return {name:None if raw is None else raw.encode() for name,raw in document.items()}


@lru_cache(maxsize=4)
def _active(root_name, dependency_state):
    root = Path(root_name)
    if (root/AUTHORITY).exists() != (root/BEFORE).exists():
        raise ValueError("Orphaned Dübner continuation authority or archive")
    if not (root/AUTHORITY).exists():
        if (root/NETWORKS).exists() or any(b'"dubner_evidence_review"' in p.read_bytes() for p in (root/"data/corpus").glob("*dubner*.jsonl")):
            raise ValueError("Dübner continuation projection lacks its authority")
        return False
    before = archived_inputs(root)
    return any((local_path(root,name).read_bytes() if local_path(root,name).is_file() else None) != raw
        for name,raw in before.items())


def active(root=ROOT):
    root = Path(root).absolute()
    names = {AUTHORITY,BEFORE,NETWORKS}
    if (root/AUTHORITY).is_file():
        names.update(json.loads((root/AUTHORITY).read_bytes())["outputs"])
    else:
        names.update(p.relative_to(root).as_posix() for p in (root/"data/corpus").glob("*dubner*.jsonl"))
    state = tuple((name,(root/name).stat().st_size,(root/name).stat().st_mtime_ns)
        if (root/name).is_file() else (name,None,None) for name in sorted(names))
    return _active(str(root),state)


def verify(root=ROOT, *, active_only=True):
    root = Path(root)
    audit = json.loads((root/AUTHORITY).read_bytes())
    if (audit.get("schema_version") != 1 or audit.get("qualification") != QUALIFICATION
            or audit.get("recipe_sha256") != recipe_pins()
            or audit.get("before_sha256") != sha((root/BEFORE).read_bytes())):
        raise ValueError("Dübner continuation authority, recipe, or preimage changed")
    for name,pin in audit["recipe_sha256"].items():
        if sha((root/"scripts"/name).read_bytes()) != pin:
            raise ValueError("Dübner continuation recipe changed: " + name)
    before = archived_inputs(root)
    if set(before) != set(audit["outputs"]):
        raise ValueError("Dübner continuation preimage/output inventories differ")
    primaries = {n:r for n,r in before.items() if n.startswith("data/corpus/")}
    if any(r is None for r in primaries.values()) or any(r is not None for n,r in before.items() if n not in primaries):
        raise ValueError("Dübner continuation claims an unowned destination")
    if set(before)-set(primaries) != {NETWORKS,RECORDS,ASSESSMENT}:
        raise ValueError("Dübner continuation generated-output inventory changed")
    for name,pin in audit["outputs"].items():
        if active_only and sha(local_path(root,name).read_bytes()) != pin:
            raise ValueError("Dübner continuation output changed: " + name)
    outputs,works,counts,pins = build(root,primaries,recorded_at=audit["recorded_at"])
    if (audit["outputs"] != {n:sha(r) for n,r in outputs.items()}
            or audit["works"] != works or audit["counts"] != counts or audit["source_sha256"] != pins):
        raise ValueError("Dübner continuation source replay differs from its authority")
    return audit,before


def signature(root):
    root = Path(root)
    names = {AUTHORITY,BEFORE,NETWORKS,RECORDS,ASSESSMENT,
        "data/paratext/dubner-1855-editorial.jsonl","data/work_ids.json",
        *("scripts/"+n for n in recipe_pins())}
    if (root/AUTHORITY).is_file():
        audit = json.loads((root/AUTHORITY).read_bytes())
        names.update(audit["outputs"]); names.update(audit["source_sha256"])
    names.update(name for name,*_ in previous._state_signature(root))
    return tuple((name,(root/name).stat().st_size,(root/name).stat().st_mtime_ns)
        if (root/name).is_file() else (name,None,None) for name in sorted(names))


@lru_cache(maxsize=2)
def _checked(root_name, initial):
    root = Path(root_name)
    audit,before = verify(root)
    rows = {(r["urn"],r["locus"]):r for name in audit["outputs"] if name.startswith("data/corpus/")
        for r in map(json.loads,(root/name).read_bytes().splitlines())}
    if signature(root) != initial:
        raise ValueError("Dübner continuation changed during verification")
    return audit,before,rows


def _state(root=ROOT):
    """Internal immutable-by-contract state for scalar projection adapters."""
    root = Path(root).absolute()
    return _checked(str(root),signature(root))


def checked_state(root=ROOT):
    return deepcopy(_state(root))


def apply(root=ROOT, *, recorded_at=None):
    root = Path(root)
    if active(root):
        raise ValueError("Dübner continuation is already active")
    old = None
    if (root/AUTHORITY).exists():
        old,before = verify(root,active_only=False)
        if recorded_at is not None and recorded_at != old["recorded_at"]:
            raise ValueError("Frozen Dübner continuation timestamp changed")
        recorded_at = old["recorded_at"]
        before = {n:r for n,r in before.items() if n.startswith("data/corpus/")}
    else:
        previous.checked_state(root)
        import dubner_layers
        scope,_ = dubner_layers.verify_scope(root)
        before = {n:local_path(root,n).read_bytes() for n,pin in scope["outputs"].items()
            if n.startswith("data/corpus/") and pin is not None}
    recorded_at = recorded_at or datetime.now(timezone.utc).isoformat()
    outputs,works,counts,pins = build(root,before,recorded_at=recorded_at)
    preimages = {name:before.get(name) for name in outputs}
    for name,expected in preimages.items():
        actual = local_path(root,name).read_bytes() if local_path(root,name).is_file() else None
        if actual != expected:
            raise ValueError("Refusing to overwrite a later Dübner change: " + name)
    archive = gzip.compress(encoded({n:None if r is None else r.decode() for n,r in preimages.items()}),mtime=0)
    audit = {"schema_version":1,"recorded_at":recorded_at,"before_sha256":sha(archive),
        "recipe_sha256":recipe_pins(),"source_sha256":pins,
        "outputs":{n:sha(r) for n,r in outputs.items()},"works":works,"counts":counts,
        "qualification":QUALIFICATION}
    if old is not None and encoded(audit) != (root/AUTHORITY).read_bytes():
        raise ValueError("Dübner continuation reapply differs from its frozen authority")
    publish(root,{**outputs,BEFORE:archive,AUTHORITY:encoded(audit)})
    return audit


def undo(root=ROOT):
    """Literal recovery remains possible after source evidence is invalidated."""
    root = Path(root)
    audit = json.loads((root/AUTHORITY).read_bytes())
    if sha((root/BEFORE).read_bytes()) != audit["before_sha256"]:
        raise ValueError("Dübner continuation undo preimage changed")
    before = archived_inputs(root)
    if set(before) != set(audit["outputs"]):
        raise ValueError("Dübner continuation undo inventory changed")
    for name,pin in audit["outputs"].items():
        if sha(local_path(root,name).read_bytes()) != pin:
            raise ValueError("Refusing to overwrite a later Dübner change: " + name)
    publish(root,before)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("apply","verify","undo"))
    parser.add_argument("--root",type=Path,default=ROOT)
    args = parser.parse_args()
    if args.action == "undo":
        undo(args.root)
        print("Restored the exact prior Dübner reading review")
    else:
        audit = apply(args.root) if args.action == "apply" else verify(args.root)[0]
        print(json.dumps(audit["counts"],sort_keys=True))
