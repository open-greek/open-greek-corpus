"""Only actual images from this validation call may establish crop digests."""
from copy import deepcopy
import gzip
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import prepare_photius_review_campaign as campaign
import build_photius_review_observations as driver
from test_photius_review_campaign import fixture, compile_fixture, slice_segment


def count_renders(monkeypatch):
    render, calls = campaign._render_crop_png, []
    def counted(*args):
        calls.append(args[1:])
        return render(*args)
    monkeypatch.setattr(campaign, '_render_crop_png', counted)
    return calls


def authored(fixture, producer):
    return campaign.compile_authored_campaign(fixture['manifest'], producer, *fixture['inputs'])


def test_authoring_and_compilation_render_each_shared_geometry_once(fixture, monkeypatch):
    reviews = deepcopy(fixture['reviews'])
    end = len(fixture['rows'][0]['text'])
    reviews['records'][0]['segments'] = [slice_segment(fixture, a, b)
                                       for a, b in ((0, 2), (2, 8), (8, end))]
    def producer(token, crop_png):
        assert not hasattr(token, '__getitem__')
        for segment in reviews['records'][0]['segments']:
            scan = segment['scan']
            scan['image_sha256'] = campaign.sha(crop_png(token, scan['physical_page'], scan['region']))
        return reviews, {}
    calls = count_renders(monkeypatch)
    returned, result = authored(fixture, producer)
    assert returned == reviews and result['scope_complete']
    assert result['counts']['unchanged_segments'] == 3 and len(calls) == 1
    # Ordinary validation of saved reviews owns a separate, fresh source pass.
    assert campaign.compile_campaign(fixture['manifest'], reviews, *fixture['inputs']) == result
    assert len(calls) == 2


def test_a_prerendered_geometry_cannot_validate_a_forged_recorded_hash(fixture):
    def producer(token, crop_png):
        review = deepcopy(fixture['reviews'])
        scan = review['records'][0]['segments'][0]['scan']
        crop_png(token, scan['physical_page'], scan['region'])
        scan['image_sha256'] = 'f' * 64
        return review, {}
    with pytest.raises(ValueError, match='crop image changed'):
        authored(fixture, producer)


@pytest.mark.parametrize('field', ['characters', 'baseline_commit', 'campaign_id', 'created_at'])
def test_source_and_manifest_validation_surround_authoring(fixture, field):
    def unexpected(*args):
        pytest.fail('A changed source must be rejected before authoring')
    inputs = list(fixture['inputs']); inputs[1] += b'changed source bytes'
    with pytest.raises(ValueError, match='pinned scan'):
        campaign.compile_authored_campaign(fixture['manifest'], unexpected, *inputs)
    def change_manifest(*args):
        if field == 'characters':
            fixture['manifest']['scope']['characters'] += 1
        else:
            fixture['manifest'][field] = {'baseline_commit': '1' * 40,
                'campaign_id': 'changed-campaign', 'created_at': '2026-10-22T10:00:00Z'}[field]
        return fixture['reviews'], {}
    with pytest.raises(ValueError, match='scope'):
        authored(fixture, change_manifest)


def test_callback_failure_closes_the_source_pass(fixture):
    escaped = {}
    def producer(token, crop_png):
        escaped.update(token=token, crop_png=crop_png)
        crop_png(token, 2, [.1, .1, .9, .9])
        raise RuntimeError('Failed authored table')
    with pytest.raises(RuntimeError, match='Failed authored'):
        authored(fixture, producer)
    with pytest.raises(ValueError, match='closed'):
        escaped['crop_png'](escaped['token'], 2, [.1, .1, .9, .9])


def test_a_rerender_cannot_silently_replace_a_captured_digest(fixture, monkeypatch):
    monkeypatch.setattr(campaign, '_MAX_CROP_PNG_BYTES', 0)
    with campaign._ReviewCrops(fixture['inputs'][1]) as crops:
        def producer(token, crop_png):
            raw = crop_png(token, 2, [.1, .1, .9, .9])
            monkeypatch.setattr(campaign, '_render_crop_png', lambda *args: raw + b'changed pixels')
            with pytest.raises(ValueError, match='rendering changed'):
                crop_png(token, 2, [.1, .1, .9, .9])
        crops.author(producer)


def test_private_pass_bounds_pixels_and_discards_all_receipts(fixture, monkeypatch):
    calls = count_renders(monkeypatch)
    monkeypatch.setattr(campaign, '_MAX_CROP_PNGS', 1)
    monkeypatch.setattr(campaign, '_MAX_CROP_PNG_BYTES', 100_000)
    boxes = [[.1, .1, .9, .9], [.2, .1, .9, .9], [.3, .1, .9, .9]]
    escaped = {}
    with campaign._ReviewCrops(fixture['inputs'][1]) as crops:
        def producer(token, crop_png):
            escaped.update(token=token, crop_png=crop_png)
            with pytest.raises(ValueError, match='another validation'):
                crop_png(object(), 2, boxes[0])
            return [campaign.sha(crop_png(token, 2, box)) for box in boxes]
        hashes = crops.author(producer)
        assert len(crops._ReviewCrops__pngs) <= 1
        assert crops._ReviewCrops__png_bytes <= 100_000
        assert [crops.digest(2, box) for box in boxes] == hashes
        assert len(calls) == 3  # Evicted pixels do not require another render.
        with pytest.raises(ValueError, match='already been authored'):
            crops.author(producer)
    assert not crops._ReviewCrops__pngs and not crops._ReviewCrops__digests
    with pytest.raises(ValueError, match='closed'):
        escaped['crop_png'](escaped['token'], 2, boxes[0])
    with pytest.raises(ValueError, match='closed'):
        crops.digest(2, boxes[0])
    with pytest.raises(ValueError, match='closed'):
        crops.author(producer)
    with pytest.raises(ValueError, match='closed'):
        with crops:
            pass


def test_digest_eviction_and_oversized_pixels_rerender_without_trusting_hashes(fixture, monkeypatch):
    calls = count_renders(monkeypatch)
    monkeypatch.setattr(campaign, '_MAX_CROP_DIGESTS', 1)
    monkeypatch.setattr(campaign, '_MAX_CROP_PNG_BYTES', 0)
    with campaign._ReviewCrops(fixture['inputs'][1]) as crops:
        first = crops.digest(2, [.1, .1, .9, .9])
        crops.digest(2, [.2, .1, .9, .9])
        assert len(crops._ReviewCrops__digests) == 1 and not crops._ReviewCrops__pngs
        assert crops.digest(2, [.1, .1, .9, .9]) == first
        assert len(calls) == 3


@pytest.mark.parametrize('setting', ['antialias', 'icc'])
def test_next_invocation_renders_afresh_after_global_renderer_changes(setting):
    # ICC has no reliable getter. An isolated child avoids guessing how to
    # restore its state in the shared test process.
    code = '''
import sys
sys.path.insert(0, 'scripts')
import pymupdf
import prepare_photius_review_campaign as c
c.MAX_SIDE = 120
with pymupdf.open() as doc:
    page = doc.new_page(width=120, height=180)
    page.insert_text((15, 40), 'Printed source witness')
    raw = doc.tobytes()
original, calls = c._render_crop_png, []
def counted(*args):
    calls.append(1)
    return original(*args)
c._render_crop_png = counted
hashes = []
for value in (0, 8):
    if sys.argv[1] == 'antialias':
        pymupdf.TOOLS.set_aa_level(value)
    else:
        pymupdf.TOOLS.set_icc(bool(value))
    with c._ReviewCrops(raw) as crops:
        hashes.append(crops.digest(1, [.1, .1, .9, .9]))
    with pymupdf.open(stream=raw, filetype='pdf') as doc:
        assert hashes[-1] == c.sha(original(doc, 1, [.1, .1, .9, .9], 120))
assert len(calls) == 2
if sys.argv[1] == 'antialias':
    assert hashes[0] != hashes[1]
'''
    subprocess.run([sys.executable, '-c', code, setting], cwd=ROOT, check=True,
                   capture_output=True, text=True)


def install_driver_fixture(fixture, root, monkeypatch):
    monkeypatch.setattr(driver, 'HELPERS', ())
    monkeypatch.setattr(driver, 'TABLES', ('fixture_observations',))
    for path, raw in [(campaign.MANIFEST, campaign.encode(fixture['manifest'])),
                      (campaign.BASELINE, gzip.compress(fixture['inputs'][0], mtime=0)),
                      *zip((campaign.CORPUS, campaign.SCAN, campaign.LIBRARY,
                            campaign.ORIGINAL, campaign.COVERAGE), fixture['inputs'])]:
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_bytes(raw)
    path = root / 'scripts/fixture_observations.py'
    path.parent.mkdir(parents=True)
    return path


def write_table(path, records, *, forge=False):
    path.write_text("import hashlib\ndef records(rows, document, crop_png, sections):\n"
                    f"    records = {records!r}\n"
                    "    scan = records[0]['segments'][0]['scan']\n"
                    "    raw = crop_png(document, scan['physical_page'], scan['region'])\n"
                    + ("    scan['image_sha256'] = 'f' * 64\n" if forge else
                       "    scan['image_sha256'] = hashlib.sha256(raw).hexdigest()\n")
                    + "    return records\n")


def test_driver_rereads_changed_table_bytes_and_rejects_forged_hashes(fixture, tmp_path, monkeypatch):
    path = install_driver_fixture(fixture, tmp_path, monkeypatch)
    records = deepcopy(fixture['reviews']['records'])
    write_table(path, records)
    calls = count_renders(monkeypatch)
    first, _ = driver.build(tmp_path)
    stamp = path.stat()
    records[0]['segments'][0]['evidence'] += ' Additional source evidence.'
    write_table(path, records)
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    second, _ = driver.build(tmp_path)
    assert first != second and len(calls) == 2
    write_table(path, records, forge=True)
    with pytest.raises(ValueError, match='crop image changed'):
        driver.build(tmp_path)


@pytest.mark.parametrize('change', ['source', 'missing_source'])
def test_driver_does_not_reuse_source_receipts_between_builds(fixture, tmp_path, monkeypatch, change):
    path = install_driver_fixture(fixture, tmp_path, monkeypatch)
    write_table(path, fixture['reviews']['records'])
    driver.build(tmp_path)
    source = tmp_path / campaign.SCAN
    if change == 'source':
        stamp, raw = source.stat(), source.read_bytes()
        source.write_bytes(raw.replace(b'%PDF-1.', b'%PDF-2.', 1))
        os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    else:
        source.unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        driver.build(tmp_path)
