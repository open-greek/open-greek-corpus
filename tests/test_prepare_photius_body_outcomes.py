"""Only completed, occurrence-reviewed raw attempts can enter body admission."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_photius_body_outcomes as outcomes
import repair_photius_readings as repair


@pytest.fixture
def first_batch(tmp_path, monkeypatch):
    batch = deepcopy(repair.BODY_BATCHES[0])
    monkeypatch.setattr(repair, 'BODY_BATCHES', (batch,))
    monkeypatch.setattr(outcomes, 'NOTES', {k: v for k, v in outcomes.NOTES.items()
                                        if k.startswith(('0066-', '0073-'))})
    import photius_body_source_observations as first
    monkeypatch.setattr(outcomes, 'source_observation_tables', lambda: (first,))
    for name in [batch['request'], *batch['raw_files']]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    return tmp_path, batch


def test_completed_review_preserves_exact_errors_and_all_prediction_pins(first_batch):
    root, _ = first_batch
    result = outcomes.build(root)
    assert len(result['records']) == 18
    masks = [span for row in result['records'] for span in row['exclusions']]
    assert len(masks) >= 6
    assert {'τύχης', 'ἑταίροις', '1017 R.'} <= {s['observed_printed_text'] for s in masks}
    assert all(row['decision'] == 'eligible-as-raw-witness' for row in result['records'])
    assert all(len(row['prediction_record_sha256']) == 64 for row in result['records'])


def test_every_strip_requires_an_explicit_completed_source_decision(first_batch, monkeypatch):
    root, _ = first_batch
    notes = dict(outcomes.NOTES)
    del notes[next(iter(notes))]
    monkeypatch.setattr(outcomes, 'NOTES', notes)
    with pytest.raises(ValueError, match='No completed source comparison'):
        outcomes.build(root)


@pytest.mark.parametrize('change', ['missing', 'duplicate', 'truncated'])
def test_incomplete_or_repeated_attempts_do_not_enter_outcome_review(first_batch, change):
    root, batch = first_batch
    path = root / batch['raw_files'][0]
    rows = list(map(json.loads, path.read_bytes().splitlines()))
    if change == 'missing':
        rows.pop()
    elif change == 'duplicate':
        rows.append(deepcopy(rows[-1]))
    else:
        rows[-1]['finish_reason'] = 'length'
    path.write_bytes(repair.jsonl(rows))
    with pytest.raises(ValueError, match='completed strip exactly once|incomplete prediction|source-observation raw file changed'):
        outcomes.build(root)
