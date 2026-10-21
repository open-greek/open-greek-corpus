from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_work_lemma_counts as counts
import frequency_projection as projection


@pytest.mark.parametrize('changed', ['repair_photius_body.py', 'photius_body_vote.py', 'repair_photius_readings.py',
                                    'repair_photius_historical_readings.py',
                                    'repair_photius_historical_batches.py',
                                    'repair_photius_complete_review.py',
                                    'assess_photius_historical.py', 'ocr_consensus.py', 'audit_compression.py',
                                    'prepare_photius_review_campaign.py'])
def test_imported_eligibility_code_changes_the_recipe_pin(tmp_path, monkeypatch, changed):
    names = tuple(projection.projection_recipe_pins())
    for name in names:
        (tmp_path / name).write_text(name)
    monkeypatch.setattr(projection, "__file__", str(tmp_path / names[0]))
    before = projection.projection_recipe_pins()
    (tmp_path / changed).write_text("changed eligibility policy")
    after = projection.projection_recipe_pins()
    assert after[changed] != before[changed]
    assert all(after[name] == before[name] for name in names if name != changed)


def test_unchanged_corpus_is_recounted_after_eligibility_policy_changes(tmp_path, monkeypatch):
    corpus = tmp_path / "work.jsonl"
    corpus.write_text('{"urn":"fixture.work","text":"λόγος σημείον"}\n')
    monkeypatch.setattr(counts, "DATA", tmp_path)
    monkeypatch.setattr(counts, "MANIFEST", tmp_path / "manifest.json")
    monkeypatch.setattr(counts, "WORK_FORMS", tmp_path / "cache")
    class Policy:
        digest = "unchanged data projection"
        recipe_digest = "policy one"
        def __init__(self, data):
            pass
        def text(self, row):
            return row["text"] if self.recipe_digest == "policy one" else "λόγος"
    monkeypatch.setattr(counts, "FrequencyProjection", Policy)
    first = counts.load_work_forms([corpus], use_cache=True)
    assert first["fixture.work"]["σημείον"] == 1
    Policy.recipe_digest = "policy two"
    second = counts.load_work_forms([corpus], use_cache=True)
    assert second["fixture.work"] == {"λόγος": 1}
