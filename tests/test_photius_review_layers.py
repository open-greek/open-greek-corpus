"""Both later authorities preserve the exact complete-review predecessor."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from test_photius_context import ROOT, STAMP, compiled_case
import prepare_photius_review_campaign as campaign
import repair_photius_complete_review as complete
import repair_photius_context as context
import repair_photius_uncertainties as uncertainty
import frequency_projection as frequency


@pytest.fixture
def stack(tmp_path):
    import pymupdf
    text = 'πρῶτος λογος σαφὴς καὶ δεύτερος λόγος τέλος.'
    a = text.index('λογος')
    fixture = compiled_case(text, text, uncertain=(a, a+5))
    compiled = fixture['compiled']
    record = compiled['rows'][0]
    record['physical_page'] = 169
    record['segments'][1]['uncertainty'] = 'The source glyph is unresolved.'
    section = campaign.SECTION_PREFIX+'446'
    library = gzip.decompress(fixture['library'])
    library = library.replace((campaign.SECTION_PREFIX+'280').encode(), section.encode())
    library = gzip.compress(library, mtime=0)
    compiled['input_pins']['digital_archive']['sha256'] = campaign.sha(library)
    for segment in record['segments']:
        for reading in segment['readings']:
            reading['section'] = section
            reading['source'] = deepcopy(compiled['input_pins']['digital_archive'])
    doc = pymupdf.open()
    for _ in range(169):
        doc.new_page(width=40, height=40)
    scan = doc.tobytes(); doc.close()
    compiled['input_pins']['scan']['sha256'] = campaign.sha(scan)
    original = fixture['before']
    compiled_raw = campaign.encode(compiled)
    outputs, _ = complete.artifacts(original, compiled_raw)
    for path, raw in {**outputs, campaign.BASELINE: fixture['baseline'],
                      campaign.LIBRARY: library, campaign.SCAN: scan}.items():
        (tmp_path/path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path/path).write_bytes(raw)
    (tmp_path/'scripts').mkdir(exist_ok=True)
    for name in context.RECIPE_NAMES:
        (tmp_path/'scripts'/name).write_bytes((ROOT/'scripts'/name).read_bytes())
    aliases = (tmp_path/complete.ALIASES).read_bytes()
    context.apply(tmp_path, recorded_at=STAMP)
    context_row = json.loads((tmp_path/campaign.CORPUS).read_bytes())
    decision = {'locus': record['locus'], 'segment_index': 1,
        'original_text': 'λογος', 'corrected_text': 'λόγος', 'decision': 'resolved',
        'evidence': 'Synthetic source-review authority for layered replay.',
        'bekker_region': [.1, .1, .9, .9], 'comparisons': []}
    table = ('REVIEWED_AT = '+repr(STAMP)+'\nSOURCES = {}\nEXPECTED_SCOPE = '+
        repr([(record['locus'], 1)])+'\ndef records():\n    return '+repr([decision])+'\n')
    (tmp_path/uncertainty.TABLE).write_text(table)
    uncertainty.apply(tmp_path)
    return tmp_path, original, context_row, compiled_raw, aliases


def test_layered_checks_projections_and_exact_no_source_undo(stack, monkeypatch):
    root, original, context_row, compiled_raw, aliases = stack
    row = json.loads((root/campaign.CORPUS).read_bytes())
    assert row['text'] == context_row['text'].replace('λογος', 'λόγος', 1)
    assert row['complete_source_review'] == context_row['complete_source_review']
    assert row[context.TAG] == context_row[context.TAG]
    assert uncertainty.check(root)['counts']['current_uncertainty_spans'] == 0
    assert context.check(root)['counts']['changed_display_rows'] == 0
    import build_photius_review_observations as observations
    monkeypatch.setattr(observations, 'build', lambda root: (
        {campaign.OUT: gzip.compress(compiled_raw, mtime=0)}, json.loads(compiled_raw)))
    assert complete.check(root)
    assert complete.restore_before_bytes((root/campaign.CORPUS).read_bytes(), root) == original
    assert complete.restore_before_row(row, root) == json.loads(original)
    latest_segments = uncertainty.lexical_segments
    monkeypatch.setattr(uncertainty, 'lexical_segments', lambda rec: latest_segments(rec, root))
    projection = frequency.FrequencyProjection(root/'data')
    assert projection.text(row) == row['analysis_text']
    assert projection.segments(row) == latest_segments(row, root)
    assert (root/complete.ALIASES).read_bytes() == aliases
    (root/campaign.SCAN).unlink()
    (root/campaign.LIBRARY).unlink()
    with pytest.raises(FileNotFoundError):
        uncertainty.check(root)
    with pytest.raises(ValueError, match='Undo later layers'):
        context.undo(root)
    uncertainty.undo(root)
    assert json.loads((root/campaign.CORPUS).read_bytes()) == context_row
    context.undo(root)
    assert complete.restore_before_bytes((root/campaign.CORPUS).read_bytes(), root) == original
    assert (root/complete.ALIASES).read_bytes() == aliases
