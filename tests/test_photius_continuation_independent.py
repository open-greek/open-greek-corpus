"""Independent continuation checks for exact punctuation and immutable replay."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_photius_editorial_continuation as prepare
import repair_photius_editorial_continuation as layer


def case(source='ἔφη <b>«σαφές</b>»', original='κακὸν λόγον'):
    """Construct an independent, attributed source with separate closer nodes."""
    text = 'ἀρχὴ ' + original + ' τέλος'
    start = text.index(original)
    end = start + len(original)
    raw = ('<h3>248</h3><h2>435a</h2><td>ἀρχὴ ' + source + ' τέλος</td>').encode()
    identity = {'id': 'tlg-photius-henry', 'edition': 'Henry, Bibliothèque',
                'citation': 'Photius, Bibliotheca 4040.001', 'sha256': layer.sha(raw)}
    indexed = list(layer.previous._source_tokens(raw, identity).values())
    tokens = [{**deepcopy(token), 'source_index': index}
              for index, token in indexed[1:-1]]
    reading = prepare.attributed_span(
        {'source_id': identity['id'], 'role': 'chosen',
         'text': ' '.join(token['text'] for token in tokens), 'tokens': tokens},
        prepare.source_document(raw))
    rendered = prepare.render(original, text, start, end, reading)
    assert rendered is not None
    reading['trim'] = rendered['trim']
    masks = [{'start': start, 'end': end, 'text': original,
              'classification': 'unresolved-source-reading',
              'qualification': 'Unclear original printed reading.'}]
    locus = 'independent-source-occurrence'
    row = {'locus': locus, 'urn': 'urn:cts:greekLit:tlg4040.tlg001:1',
           'text': text, 'analysis_text': 'ἀρχὴ τέλος',
           'complete_source_review': {'immutable': 'predecessor'},
           layer.previous.TAG: {'excluded_spans': {
               'path': layer.previous.RECORDS.as_posix(), 'locus': locus,
               'sha256': layer.sha(layer.canonical(masks))}}}
    # Noncanonical original spacing is deliberate: undo must restore bytes.
    # A corpus row is one physical JSONL line, even when its spacing is unusual.
    before = (json.dumps(row, ensure_ascii=False, separators=(', ', ': ')) + '\r\n').encode()
    scopes = {(locus, 3): {'row': row, 'start': start, 'end': end,
        'record': {'physical_page': 170, 'printed_page': 435,
                   'original_segment': {'verification': 'uncertain',
                       'text_role': 'authorial-body',
                       'uncertainty': masks[0]['qualification'], 'fragments': []}},
        'excluded_spans': masks}}
    decision = {'locus': locus, 'segment_index': 3, 'original_text': original,
                'decision': 'substitute', 'reason': 'located-editorial-reading',
                'evidence': 'An exactly located independent editorial reading.',
                'readings': [reading], **rendered}
    authored = {'schema': prepare.SCHEMA, 'reviewed_at': '2026-10-21T23:10:00Z',
                'source': identity, 'input_corpus_sha256': layer.sha(before),
                'records': [decision]}
    return before, scopes, authored, raw


def compile_case(inputs, *, literal=False):
    before, scopes, authored, raw = inputs
    return layer.compile_review(before, scopes, authored,
                                source_raw=None if literal else raw)


@pytest.mark.parametrize(('source', 'expected'), [
    ('ἔφη <b>«σαφές</b>»', 'ἔφη «σαφές»'),
    ('ἔφη <b>[σαφές</b>]', 'ἔφη [σαφές]'),
    ('ἔφη <b>«[σαφές</b>]»', 'ἔφη «[σαφές]»'),
    ('ἔφη <b>«σαφές</b> <i>ῥῆμα</i>»', 'ἔφη «σαφές ῥῆμα»'),
])
def test_standalone_and_nested_source_closers_have_exact_literal_replay(source, expected):
    inputs = case(source)
    fresh = compile_case(inputs)
    assert fresh == compile_case(inputs, literal=True)
    assert fresh['records'][0]['corrected_text'] == expected
    reading = fresh['records'][0]['readings'][0]
    assert reading['boundary_suffix']['pieces']
    assert all(piece['ref']['end'] - piece['ref']['start'] == len(piece['text'])
               for piece in reading['boundary_suffix']['pieces'])


@pytest.mark.parametrize('defect', ['greek', 'number', 'backward', 'outside', 'boolean-offset'])
def test_literal_replay_rejects_unsupported_or_unbounded_closing_nodes(defect):
    inputs = case()
    piece = inputs[2]['records'][0]['readings'][0]['boundary_suffix']['pieces'][0]
    if defect in {'greek', 'number'}:
        piece['text'] = 'α' if defect == 'greek' else '1'
    elif defect == 'backward':
        piece['ref']['html_column'] = 0
    elif defect == 'outside':
        piece['ref']['end'] += 1
    else:
        piece['ref']['start'] = False
    with pytest.raises(ValueError):
        compile_case(inputs, literal=True)


def saved_literal(root, monkeypatch):
    inputs = case()
    before, scopes, authored, _ = inputs
    names = ['independent-source-recipe.py']
    recipe_bytes = {names[0]: b'# Exact recipe input.\n',
                    Path(layer.__file__).name: Path(layer.__file__).read_bytes()}
    for name, raw in recipe_bytes.items():
        path = root / 'scripts' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    recipes = {name: layer.sha(raw) for name, raw in recipe_bytes.items()}
    authored['recipe_sha256'] = {names[0]: recipes[names[0]]}
    authored['input_pins'] = {}
    authored_raw = layer.encode(authored)
    review = compile_case(inputs)
    files, audit = layer.artifacts(before, b'{ "immutable": "aliases" }\r\n',
        layer.encode(review),
        pins={layer.SOURCE_REVIEW.as_posix(): layer.sha(authored_raw)}, recipes=recipes)
    for path, raw in {**files, layer.ALIASES: b'{ "immutable": "aliases" }\r\n',
                      layer.SOURCE_REVIEW: authored_raw}.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    monkeypatch.setattr(layer, 'BASELINE_SHA256', layer.sha(before))
    monkeypatch.setattr(layer, 'input_pins', lambda root: {})
    monkeypatch.setattr(prepare, 'recipe_names', lambda root: names)
    monkeypatch.setattr(prepare, 'scope', lambda root: (before, scopes))
    return before, files, audit


@pytest.mark.parametrize('missing', ['engine', 'source-recipe'])
def test_literal_check_requires_the_entire_recipe_set(tmp_path, monkeypatch, missing):
    _, _, audit = saved_literal(tmp_path, monkeypatch)
    assert layer.check_literal(tmp_path)['counts']['newly_editorially_substituted_spans'] == 1
    name = Path(layer.__file__).name if missing == 'engine' else 'independent-source-recipe.py'
    del audit['recipe_sha256'][name]
    (tmp_path / layer.AUDIT).write_bytes(layer.encode(audit))
    with pytest.raises(ValueError, match='pin accounting'):
        layer.check_literal(tmp_path)


def test_warmed_literal_replay_still_checks_changed_source_recipe_bytes(tmp_path, monkeypatch):
    _, _, _ = saved_literal(tmp_path, monkeypatch)
    layer.check_literal(tmp_path)
    (tmp_path / 'scripts/independent-source-recipe.py').write_bytes(b'# Changed.\n')
    with pytest.raises(ValueError, match='source recipe changed'):
        layer.check_literal(tmp_path)


def test_exact_byte_and_row_undo_after_punctuation_replay(tmp_path, monkeypatch):
    before, files, _ = saved_literal(tmp_path, monkeypatch)
    layer.check_literal(tmp_path)
    assert layer.restore_before_bytes(files[layer.CORPUS], tmp_path) == before
    row = json.loads(files[layer.CORPUS])
    assert row['text'] == 'ἀρχὴ ἔφη «σαφές» τέλος'
    assert layer.restore_before_row(row, tmp_path) == json.loads(before)
    layer.undo(tmp_path)
    assert (tmp_path / layer.CORPUS).read_bytes() == before
    assert (tmp_path / layer.ALIASES).read_bytes() == b'{ "immutable": "aliases" }\r\n'
    assert gzip.decompress((tmp_path / layer.BEFORE).read_bytes()) == before


def test_warmed_lexical_projection_rejects_changed_authority_bytes(tmp_path, monkeypatch):
    _, files, _ = saved_literal(tmp_path, monkeypatch)
    row = json.loads(files[layer.CORPUS])
    assert layer.lexical_segments(row, tmp_path) == ['ἀρχὴ ἔφη «σαφές» τέλος']
    path = tmp_path / layer.REVIEW
    path.write_bytes(path.read_bytes() + b'changed after first projection')
    with pytest.raises(ValueError, match='compiled authority'):
        layer.lexical_segments(row, tmp_path)
