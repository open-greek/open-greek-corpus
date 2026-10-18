import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/prepare_photius_body_correction.py'
AUTHORITY = Path('data/ingest_reviews/photius-bekker-body-corrections.json')
INPUTS = [Path('data/corpus_changes/photius-bekker-index/before.jsonl.gz'),
          Path('data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz'),
          Path('data/corpus_changes/photius-bekker-coverage/coverage.json')]


def fixture_root(tmp_path):
    for path in INPUTS:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, tmp_path / path)
    return tmp_path


def run(root, flag):
    return subprocess.run([sys.executable, str(SCRIPT), '--root', str(root), flag],
                          capture_output=True, text=True)


def test_reproduces_authority_and_rejects_output_drift(tmp_path):
    root = fixture_root(tmp_path)
    assert run(root, '--write').returncode == 0
    assert (root / AUTHORITY).read_bytes() == (ROOT / AUTHORITY).read_bytes()
    assert run(root, '--check').returncode == 0
    document = json.loads((root / AUTHORITY).read_text())
    assert 'consensus' not in document
    assert document['source_library_credit']['separate_api_notice']['tdm_reservation'] == 1
    document['replacement_scope']['start'] = 163
    (root / AUTHORITY).write_text(json.dumps(document))
    assert run(root, '--check').returncode != 0


def test_changed_digital_artifact_is_not_reauthorized(tmp_path):
    root = fixture_root(tmp_path)
    source = root / INPUTS[1]
    source.write_bytes(source.read_bytes() + b'\n')
    assert run(root, '--write').returncode != 0
    assert not (root / AUTHORITY).exists()
