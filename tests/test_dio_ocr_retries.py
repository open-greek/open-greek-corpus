"""Exact artifact scopes preserve failed originals without weakening defaults."""
from pathlib import Path
import json
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import dio_ocr_retries as retry
import scan_ocr_bundle as generic


def jsonl(rows):
    return b"\n".join(json.dumps(row, ensure_ascii=False).encode() for row in rows) + b"\n"


def put(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


@pytest.fixture(params=["qwen36", "qwen38"])
def fixture(request, tmp_path, monkeypatch):
    key = request.param
    model, revision, family = retry.CHECKPOINTS[key]
    locations = {"dio-cary-v6-pdf0206": (6,206), "dio-cary-v8-pdf0116": (8,116),
                 "dio-cary-v9-pdf0178": (9,178), "dio-cary-v9-pdf0179": (9,179),
                 "dio-cary-v9-pdf0231": (9,231)}
    targets = set(locations) - {"dio-cary-v9-pdf0231"} if key == "qwen38" else {"dio-cary-v9-pdf0231"}
    failed_ids = targets & {"dio-cary-v9-pdf0178", "dio-cary-v9-pdf0179", "dio-cary-v9-pdf0231"}
    pages = [{"id": identifier, "source": "scan" + str(volume), "source_volume": volume,
              "scan_page": scan, "region": [0,0,.5,.9], "work": "cassius-dio.historiae-romanae"}
             for identifier, (volume,scan) in locations.items()]
    pages += [{**pages[0], "id": f"other-{i}"} for i in range(1495)]
    sources = {"scan" + str(v): {"url": f"https://example.org/{v}.pdf", "sha256": str(v) * 64, "license": "PD"}
               for v in [6,8,9]}
    manifest = {"prompt": "Transcribe Greek body only.", "sources": sources, "pages": pages}
    manifest_raw = retry.encode(manifest)
    manifest_path = put(tmp_path / "manifest.json", manifest_raw)
    metadata = {"model": model, "revision": revision, "prompt": manifest["prompt"],
                "manifest_sha256": retry.sha(manifest_raw), "runner_sha256": "a" * 64, "runtime": {"gpu": "fixture"}}
    original_rows = [{"id": p["id"], "source": p["source"], "scan_page": p["scan_page"], "region": p["region"],
                      "finish_reason": "length" if p["id"] in failed_ids else "stop", "raw_prediction": "επει γαρ ..." if p["id"] in targets else "Ἐπεὶ γὰρ δέδεικται",
                      "image_sha256": retry.sha(p["id"].encode()), "prompt_sha256": retry.sha(manifest["prompt"].encode())}
                     for p in pages]
    original_by_id = {r["id"]: r for r in original_rows}
    part = put(tmp_path / "part.jsonl", jsonl([{"_meta": metadata}, *original_rows]))
    original = tmp_path / "original.bundle.json"
    generic.write_bundle([(part,manifest_path)], manifest_path, original)
    jobs = []
    for identifier in sorted(targets):
        page = next(p for p in pages if p["id"] == identifier)
        for index in range(3):
            jobs.append({**page, "id": identifier + "-strip-" + str(index+1), "reconstructs": identifier,
                         "reading_order": index+1, "region": [0,index*.3,.5,(index+1)*.3]})
    authority = {"prompt": manifest["prompt"], "sources": sources, "pages": jobs,
                 "retry_of": {"path": retry.MANIFEST_PATH, "sha256": retry.sha(manifest_raw), "model": model, "revision": revision},
                 "review": {"original_predictions": {identifier: {"artifact_sha256": retry.sha(retry.encode({"metadata": metadata, "prediction": original_by_id[identifier]})),
                     "original_metadata": metadata, "original_prediction": original_by_id[identifier],
                     "source_evidence": "Complete source page and all strip boundaries inspected; original loss or loop confirmed."}
                     for identifier in sorted(targets)}}}
    authority_path = put(tmp_path / "authority.json", retry.encode(authority))
    monkeypatch.setattr(retry, "AUTHORITIES", {key: authority_path})
    retry_meta = {**metadata, "manifest_sha256": retry.sha(authority_path.read_bytes()),
                  "generation_policy": json.loads(json.dumps(retry.GENERATION_POLICY)),
                  "temperature": retry.GENERATION_POLICY["temperature"], "max_tokens": 6000, "backend": "http",
                  "runner": "scripts/run_reviewed_scan_retry.py", "runner_sha256": retry.RETRY_RUNNER_SHA256,
                  "image_helper_sha256": retry.IMAGE_HELPER_SHA256,
                  "runtime": {**metadata["runtime"], "model": model, "revision": revision}}
    retry_rows = [{"id": p["id"], "source": p["source"], "scan_page": p["scan_page"], "region": p["region"],
                   "finish_reason": "stop", "raw_prediction": "Ἐπεὶ γὰρ δέδεικται", "image_sha256": retry.sha(p["id"].encode()),
                   "prompt_sha256": retry.sha(manifest["prompt"].encode())} for p in jobs]
    raw_retry = put(tmp_path / "retry.jsonl", jsonl([{"_meta": retry_meta}, *retry_rows]))
    calls = []
    def leaf(raw, request_raw, request_manifest, *, allow_failed_ids=frozenset()):
        calls.append(set(allow_failed_ids))
        try:
            document = json.loads(raw)
        except ValueError:
            document = None
        if isinstance(document, dict) and document.get("kind") == generic.KIND:
            return generic.load_bundle(raw, request_raw,
                lambda original_raw, original_manifest_raw: leaf(original_raw, original_manifest_raw,
                    json.loads(original_manifest_raw), allow_failed_ids=allow_failed_ids)[0])[0], raw
        meta, rows = retry.records(raw)
        if meta["manifest_sha256"] != retry.sha(request_raw):
            raise ValueError("Wrong request")
        jobs_by_id = {p["id"]: p for p in request_manifest["pages"]}
        result = {}
        for row in rows:
            job = jobs_by_id[row["id"]]
            if retry.failed(row) and row["id"] not in allow_failed_ids:
                raise ValueError("Ordinary strict loader rejects failed OCR")
            if row["region"] != job["region"] or row["source"] != job["source"] or row["scan_page"] != job["scan_page"]:
                raise ValueError("Unchecked source crop")
            result[row["id"]] = {"id": meta["model"] + "@" + meta["revision"], "model": meta["model"],
                "revision": meta["revision"], "vote_group": family, "text": row["raw_prediction"],
                "artifact_sha256": retry.sha(retry.encode({"metadata": meta, "prediction": row})),
                "image_sha256": row["image_sha256"]}
        return result, raw
    evidence = {identifier: "All complete retry strips compared with the pinned scan; body coverage, marks, finite gaps and apparatus boundaries checked. Literal local errors remain variants." for identifier in targets}
    return {"key": key, "model": model, "revision": revision, "family": family,
            "original": original, "part": part, "retry": raw_retry, "request": authority_path,
            "manifest": manifest_path, "targets": targets, "failed_ids": failed_ids,
            "evidence": evidence, "leaf": leaf, "calls": calls, "tmp": tmp_path}


def build(f):
    review, out = f["tmp"] / "review.json", f["tmp"] / "reviewed.bundle.json"
    descriptor = retry.write_reviewed_bundle(f["original"], f["retry"], f["manifest"], review, out,
        f["evidence"], "2026-10-18T00:00:00Z", f["leaf"], request_path=f["request"])
    return review, out, descriptor


def test_checkpoint_scopes_retain_original_bytes_and_one_vote(fixture):
    f = fixture
    review, out, descriptor = build(f)
    manifest_raw = f["manifest"].read_bytes()
    result, retained = retry.load_bundle(out.read_bytes(), manifest_raw, json.loads(manifest_raw), f["leaf"])
    assert len(result) == 1500
    assert sum("preprocessing" in w for w in result.values()) == len(f["targets"])
    assert all(w["model"] == f["model"] and w["revision"] == f["revision"] and w["vote_group"] == f["family"] for w in result.values())
    assert set(descriptor["replaced_page_ids"]) == f["targets"]
    assert set(descriptor["held_length_failure_ids"]) == f["failed_ids"]
    assert retry.unpack(json.loads(retained)["original"]) == f["original"].read_bytes()
    assert retry.unpack(json.loads(retained)["retry"]) == f["retry"].read_bytes()
    assert all(not allowed or allowed == f["failed_ids"] for allowed in f["calls"])
    for identifier in f["targets"]:
        assert result[identifier]["text"] == "\n".join(["Ἐπεὶ γὰρ δέδεικται"] * 3)
        assert result[identifier]["preprocessing"][0]["original_text"] == "επει γαρ ..."


def test_ordinary_loading_remains_strict(fixture):
    f = fixture
    raw = f["manifest"].read_bytes()
    with pytest.raises(ValueError, match="strict loader rejects"):
        f["leaf"](f["original"].read_bytes(), raw, json.loads(raw))


def test_additional_failed_page_cannot_receive_an_exception(fixture):
    f = fixture
    values = [json.loads(line) for line in f["part"].read_bytes().splitlines()]
    values[-1]["finish_reason"] = "length"
    f["part"].write_bytes(jsonl(values))
    f["original"].unlink()
    generic.write_bundle([(f["part"],f["manifest"])], f["manifest"], f["original"])
    with pytest.raises(ValueError, match="unreviewed failed Dio"):
        build(f)
    assert f["calls"] == []
    assert not (f["tmp"] / "review.json").exists()


def test_failed_original_text_is_never_rewritten_to_pass(fixture):
    f = fixture
    values = [json.loads(line) for line in f["part"].read_bytes().splitlines()]
    row = next(r for r in values[1:] if r["id"] in f["failed_ids"])
    row["raw_prediction"] += "changed"
    f["part"].write_bytes(jsonl(values))
    f["original"].unlink()
    generic.write_bundle([(f["part"],f["manifest"])], f["manifest"], f["original"])
    with pytest.raises(ValueError, match="exact source-reviewed artifact"):
        build(f)
    assert not (f["tmp"] / "reviewed.bundle.json").exists()


def test_any_failed_retry_strip_rejects_before_private_exception(fixture):
    f = fixture
    values = [json.loads(line) for line in f["retry"].read_bytes().splitlines()]
    values[1]["finish_reason"] = "length"
    f["retry"].write_bytes(jsonl(values))
    with pytest.raises(ValueError, match="successful complete reviewed strip"):
        build(f)
    assert f["calls"] == []


def test_changed_retry_checkpoint_rejects_without_substitution(fixture):
    f = fixture
    values = [json.loads(line) for line in f["retry"].read_bytes().splitlines()]
    values[0]["_meta"]["revision"] = "different-revision"
    f["retry"].write_bytes(jsonl(values))
    with pytest.raises(ValueError, match="checkpoint"):
        build(f)


def test_missing_completed_page_evidence_cannot_be_approved(fixture):
    f = fixture
    f["evidence"][next(iter(f["targets"]))] = ""
    with pytest.raises(ValueError, match="completed source comparison"):
        build(f)


def test_archive_checksum_guards_original_and_review(fixture):
    f = fixture
    _, out, _ = build(f)
    bundle = json.loads(out.read_bytes())
    bundle["source_review"]["sha256"] = "0" * 64
    raw = f["manifest"].read_bytes()
    with pytest.raises(ValueError, match="artifact bytes changed"):
        retry.load_bundle(retry.encode(bundle), raw, json.loads(raw), f["leaf"])


def test_real_corpus_dispatch_preserves_scoped_failures(fixture):
    admission = pytest.importorskip("ingest_scan_coverage")
    f = fixture
    def actual(raw, request_raw, manifest, *, allow_failed_ids=frozenset()):
        return admission.load_predictions(None, request_raw, manifest, raw, allow_failed_ids=allow_failed_ids)
    f["leaf"] = actual
    _, out, _ = build(f)
    raw = f["manifest"].read_bytes()
    result, retained = admission.load_predictions(out, raw, json.loads(raw))
    assert len(result) == 1500
    assert sum("preprocessing" in w for w in result.values()) == len(f["targets"])


@pytest.mark.parametrize("field", ["presence_penalty", "seed", "top_k", "chat_template_kwargs"])
def test_unapproved_decoder_policy_cannot_replace_reviewed_source(fixture, field):
    f = fixture
    values = [json.loads(line) for line in f["retry"].read_bytes().splitlines()]
    values[0]["_meta"]["generation_policy"][field] = "unapproved"
    f["retry"].write_bytes(jsonl(values))
    with pytest.raises(ValueError, match="decoding policy"):
        build(f)
    assert f["calls"] == []


@pytest.mark.parametrize("field", ["runner_sha256", "image_helper_sha256", "max_tokens"])
def test_original_runner_and_image_helper_authorities_are_pinned(fixture, field):
    f = fixture
    values = [json.loads(line) for line in f["retry"].read_bytes().splitlines()]
    values[0]["_meta"][field] = "changed"
    f["retry"].write_bytes(jsonl(values))
    with pytest.raises(ValueError, match="decoding policy"):
        build(f)


def test_frozen_policy_matches_separate_approved_runner():
    runner = pytest.importorskip("run_reviewed_scan_retry")
    assert retry.GENERATION_POLICY == runner.POLICY
    assert retry.sha(Path(runner.__file__).read_bytes()) == retry.RETRY_RUNNER_SHA256
    assert retry.sha(Path(runner.original.__file__).read_bytes()) == retry.IMAGE_HELPER_SHA256


def additional_part(f, monkeypatch):
    """A disjoint later request must not invalidate the first raw request."""
    base = json.loads(f['request'].read_bytes())
    meta, rows = retry.records(f['part'].read_bytes())
    row = next(r for r in rows if r['id'] == 'other-0')
    page = next(p for p in json.loads(f['manifest'].read_bytes())['pages'] if p['id'] == row['id'])
    jobs = [{**page, 'id': 'additional-strip-' + str(i+1), 'reconstructs': row['id'],
             'reading_order': i+1, 'region': [0,i*.3,.5,(i+1)*.3]} for i in range(3)]
    request = {**base, 'pages': jobs, 'review': {'original_predictions': {row['id']: {
        'original_metadata': meta, 'original_prediction': row,
        'artifact_sha256': retry.sha(retry.encode({'metadata':meta,'prediction':row})),
        'source_evidence': 'Additional complete source body independently inspected.'}}}}
    path = put(f['tmp']/'supplementary.json',retry.encode(request))
    monkeypatch.setattr(retry,'AUTHORITIES',{**retry.AUTHORITIES,f['key']+'-supplementary':path})
    retry_meta, retry_rows = retry.records(f['retry'].read_bytes())
    retry_meta['manifest_sha256'] = retry.sha(path.read_bytes())
    retry_rows = [{**retry_rows[0], 'id':p['id'], 'source':p['source'], 'scan_page':p['scan_page'],
                   'region':p['region'],'raw_prediction':'ἀλλὰ μὴν ἔστιν','finish_reason':'stop',
                   'image_sha256':retry.sha(p['id'].encode())} for p in jobs]
    raw = put(f['tmp']/'additional.jsonl',jsonl([{'_meta':retry_meta},*retry_rows]))
    return {'request_path':path,'retry_path':raw,'review_path':f['tmp']/'additional-review.json',
            'source_evidence':{row['id']:'All three strips compared with their source, including marks and first/last lines.'}}


def child_part(f, monkeypatch, *, failed_parent=False, suffix=""):
    request = json.loads(f['request'].read_bytes())
    job = request['pages'][0]
    meta, rows = retry.records(f['retry'].read_bytes())
    row = next(r for r in rows if r['id'] == job['id'])
    if failed_parent:
        row['finish_reason'] = 'length'
        f['retry'].write_bytes(jsonl([{'_meta':meta},*rows]))
    x0,y0,x1,y1 = job['region']
    edges = [y0,y0+(y1-y0)/3,y0+2*(y1-y0)/3,y1]
    jobs = [{**job,'id':job['id']+'-child-'+str(i+1),'reconstructs':job['id'],
             'reading_order':i+1,'region':[x0,edges[i],x1,edges[i+1]]} for i in range(3)]
    child = {**request,'pages':jobs,'retry_of':{**request['retry_of'],
        'path':'data/ingest_reviews/coverage/'+f['request'].name,'sha256':retry.sha(f['request'].read_bytes())},
        'review':{'original_predictions':{job['id']:{'original_metadata':meta,'original_prediction':row,
            'artifact_sha256':retry.sha(retry.encode({'metadata':meta,'prediction':row})),
            'source_evidence':'Exact parent strip has confirmed residual mark loss; three complete child crops inspected.'}}}}
    path = put(f['tmp']/('child-authority'+suffix+'.json'),retry.encode(child))
    monkeypatch.setattr(retry,'CHILD_AUTHORITIES',{**retry.CHILD_AUTHORITIES,f['key']+suffix:path})
    child_meta={**meta,'manifest_sha256':retry.sha(path.read_bytes())}
    child_rows=[{**row,'id':p['id'],'region':p['region'],'finish_reason':'stop','raw_prediction':text,
                 'image_sha256':retry.sha(p['id'].encode())}
                for p,text in zip(jobs,['Ἐπεὶ γάρ','οἱ δέ','τὰ πρῶτα'])]
    raw=put(f['tmp']/('child'+suffix+'.jsonl'),jsonl([{'_meta':child_meta},*child_rows]))
    return {'request_path':path,'retry_path':raw,'review_path':f['tmp']/('child-review'+suffix+'.json'),
            'source_evidence':{job['id']:'Source body, all child seams, marks and finite gaps compared; unchanged siblings retained.'}}


def multi_build(f, parts):
    out=f['tmp']/'multi.bundle.json'
    descriptor=retry.write_reviewed_bundles(f['original'],f['manifest'],parts,out,
        '2026-10-18T00:00:00Z',f['leaf'])
    return out,descriptor


def base_config(f):
    return {'request_path':f['request'],'retry_path':f['retry'],'review_path':f['tmp']/'review.json',
            'source_evidence':f['evidence']}


def test_disjoint_requests_and_child_strip_keep_one_model_vote(fixture,monkeypatch):
    f=fixture
    child=child_part(f,monkeypatch,failed_parent=True)
    extra=additional_part(f,monkeypatch)
    base={**base_config(f),'children':[child]}
    out,descriptor=multi_build(f,[base,extra])
    manifest_raw=f['manifest'].read_bytes()
    result,raw=retry.load_bundle(out.read_bytes(),manifest_raw,json.loads(manifest_raw),f['leaf'])
    bundle=json.loads(raw)
    assert len(result)==1500
    assert sum('preprocessing' in row for row in result.values())==len(f['targets'])+1
    assert all(row['vote_group']==f['family'] for row in result.values())
    assert set(descriptor['replaced_page_ids'])==f['targets']|{'other-0'}
    assert retry.unpack(bundle['original'])==f['original'].read_bytes()
    assert retry.unpack(bundle['parts'][0]['retry'])==f['retry'].read_bytes()
    assert retry.unpack(bundle['parts'][0]['children'][0]['retry'])==child['retry_path'].read_bytes()
    identifier=json.loads(f['request'].read_bytes())['pages'][0]['reconstructs']
    assert result[identifier]['text']=='\n'.join(['Ἐπεὶ γάρ','οἱ δέ','τὰ πρῶτα',*['Ἐπεὶ γὰρ δέδεικται']*2])
    assert len(result[identifier]['preprocessing'][0]['child_retries'])==1
    assert child['review_path'].exists()


def test_repeated_request_cannot_add_a_vote(fixture):
    f=fixture
    one=base_config(f)
    two={**one,'review_path':f['tmp']/'duplicate-review.json'}
    with pytest.raises(ValueError,match='repeat a model/page'):
        multi_build(f,[one,two])
    assert f['calls']==[]


@pytest.mark.parametrize('mutation',['crop-gap','parent-checksum','parent-artifact','child-failure','child-policy'])
def test_unreviewed_child_substitution_cannot_pass(fixture,monkeypatch,mutation):
    f=fixture
    child=child_part(f,monkeypatch,failed_parent=True)
    request=json.loads(child['request_path'].read_bytes())
    values=[json.loads(line) for line in child['retry_path'].read_bytes().splitlines()]
    if mutation=='crop-gap':
        request['pages'][1]['region'][1]+=.001
    elif mutation=='parent-checksum':
        request['retry_of']['sha256']='0'*64
    elif mutation=='parent-artifact':
        pin=next(iter(request['review']['original_predictions'].values()))
        pin['original_prediction']['raw_prediction']+=' changed'
        pin['artifact_sha256']=retry.sha(retry.encode({'metadata':pin['original_metadata'],'prediction':pin['original_prediction']}))
    elif mutation=='child-failure':
        values[1]['finish_reason']='length'
    else:
        values[0]['_meta']['generation_policy']['presence_penalty']=0
    child['request_path'].write_bytes(retry.encode(request))
    values[0]['_meta']['manifest_sha256']=retry.sha(child['request_path'].read_bytes())
    child['retry_path'].write_bytes(jsonl(values))
    with pytest.raises(ValueError):
        multi_build(f,[{**base_config(f),'children':[child]}])
    assert not child['review_path'].exists()
    assert not (f['tmp']/'multi.bundle.json').exists()
    assert f['failed_ids'] not in f['calls']


def test_duplicated_child_target_rejected(fixture,monkeypatch):
    f=fixture
    child=child_part(f,monkeypatch)
    duplicate={**child,'review_path':f['tmp']/'duplicate-child-review.json'}
    with pytest.raises(ValueError,match='same parent strip twice'):
        multi_build(f,[{**base_config(f),'children':[child,duplicate]}])


def test_real_corpus_dispatch_supports_additive_child_bundle(fixture,monkeypatch):
    admission=pytest.importorskip('ingest_scan_coverage')
    f=fixture
    child=child_part(f,monkeypatch,failed_parent=True)
    extra=additional_part(f,monkeypatch)
    def actual(raw,request_raw,manifest,*,allow_failed_ids=frozenset()):
        return admission.load_predictions(None,request_raw,manifest,raw,allow_failed_ids=allow_failed_ids)
    f['leaf']=actual
    out,_=multi_build(f,[{**base_config(f),'children':[child]},extra])
    raw=f['manifest'].read_bytes()
    result,_=admission.load_predictions(out,raw,json.loads(raw))
    assert len(result)==1500
    assert sum('preprocessing' in row for row in result.values())==len(f['targets'])+1


def test_recursive_child_retries_preserve_every_ancestor(fixture,monkeypatch):
    f=fixture
    child=child_part(f,monkeypatch,failed_parent=True)
    descendant_fixture={**f,'request':child['request_path'],'retry':child['retry_path']}
    grandchild=child_part(descendant_fixture,monkeypatch,failed_parent=True,suffix='-nested')
    child['children']=[grandchild]
    out,_=multi_build(f,[{**base_config(f),'children':[child]}])
    raw=f['manifest'].read_bytes()
    result,_=retry.load_bundle(out.read_bytes(),raw,json.loads(raw),f['leaf'])
    identifier=json.loads(f['request'].read_bytes())['pages'][0]['reconstructs']
    text=result[identifier]['text']
    assert text=='\n'.join(['Ἐπεὶ γάρ','οἱ δέ','τὰ πρῶτα','οἱ δέ','τὰ πρῶτα',*['Ἐπεὶ γὰρ δέδεικται']*2])
    bundle=json.loads(out.read_bytes())
    ancestor=bundle['parts'][0]['children'][0]
    assert retry.unpack(ancestor['retry'])==child['retry_path'].read_bytes()
    assert retry.unpack(ancestor['children'][0]['retry'])==grandchild['retry_path'].read_bytes()
    assert result[identifier]['preprocessing'][0]['child_retries'][0]['child_retries']


def test_known_source_confirmed_child_is_mandatory_even_for_stop(fixture,monkeypatch):
    f=fixture
    child_part(f,monkeypatch)
    with pytest.raises(ValueError,match='source-confirmed degraded or looping'):
        multi_build(f,[base_config(f)])
    assert f['failed_ids'] not in f['calls']


def test_authority_registry_accepts_stable_ids_and_pins_hashes(fixture,monkeypatch):
    f=fixture
    # Registry paths are repository-relative and may have descriptive IDs
    # independent of checkpoint labels. Every optional digest remains binding.
    target=f['tmp']/'data/ingest_reviews/coverage/authority.json'
    put(target,f['request'].read_bytes())
    registry=put(f['tmp']/'registry.json',retry.encode({'schema_version':1,
        'page_requests':{'main':{'path':'data/ingest_reviews/coverage/authority.json','sha256':retry.sha(target.read_bytes())}},
        'child_requests':{}}))
    monkeypatch.setattr(retry,'ROOT',f['tmp'])
    monkeypatch.setattr(retry,'AUTHORITY_REGISTRY',registry)
    build(f)
    target.write_bytes(target.read_bytes()+b' ')
    with pytest.raises(ValueError,match='changed request bytes'):
        retry.authority_catalog('page_requests')


def test_known_source_confirmed_supplement_cannot_be_omitted(fixture,monkeypatch):
    f=fixture
    additional_part(f,monkeypatch)
    with pytest.raises(ValueError,match='source-required Dio page retry'):
        multi_build(f,[base_config(f)])
    assert f['calls']==[]


def test_real_corpus_dispatch_retains_recursive_child_failures(fixture,monkeypatch):
    admission=pytest.importorskip('ingest_scan_coverage')
    f=fixture
    child=child_part(f,monkeypatch,failed_parent=True)
    grandchild=child_part({**f,'request':child['request_path'],'retry':child['retry_path']},
                         monkeypatch,failed_parent=True,suffix='-nested')
    child['children']=[grandchild]
    extra=additional_part(f,monkeypatch)
    def actual(raw,request_raw,manifest,*,allow_failed_ids=frozenset()):
        return admission.load_predictions(None,request_raw,manifest,raw,allow_failed_ids=allow_failed_ids)
    f['leaf']=actual
    out,_=multi_build(f,[{**base_config(f),'children':[child]},extra])
    raw=f['manifest'].read_bytes()
    result,_=admission.load_predictions(out,raw,json.loads(raw))
    assert len(result)==1500
    assert {r['vote_group'] for r in result.values()}=={f['family']}
    assert sum('preprocessing' in row for row in result.values())==len(f['targets'])+1
