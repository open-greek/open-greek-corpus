from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_ocr_quality_report import consensus_qualification


def test_consensus_measurement_does_not_certify_unassessed_rows():
    records = [{'text': 'old raw reading'},
        {'ocr_consensus': {'counts': {'agreement': 7, 'unresolved': 3}}},
        {'ocr_consensus': {'counts': {'agreement': 2, 'single-witness': 1, 'incomplete-reading': 1}}},
        {'ocr_consensus': {'policy': 'older metadata without slot measurements'}}]
    value = consensus_qualification(records)
    assert value['rows_with_counted_consensus'] == 2
    assert value['rows_without_counted_consensus'] == 2
    assert value['slot_counts'] == {'agreement': 9, 'incomplete-reading': 1, 'single-witness': 1, 'unresolved': 3}
    assert 'not a count of recognition errors' in value['counting_basis']
    assert 'shared recognition error' in value['qualification']


def test_no_consensus_measurement_is_not_reported_as_zero_errors():
    assert consensus_qualification([{'text': 'raw OCR'}]) is None


@pytest.mark.parametrize('count', [-1, 2.5, True, '3'])
def test_invalid_slot_counts_cannot_enter_quality_measurement(count):
    with pytest.raises(ValueError, match='integer slot counts'):
        consensus_qualification([{'ocr_consensus': {'counts': {'unresolved': count}}}])
