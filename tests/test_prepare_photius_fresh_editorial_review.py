"""The reviewed editorial vote mask reproduces exact retained source evidence."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fresh_review', ROOT / 'scripts/prepare_photius_fresh_editorial_review.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class FreshEditorialReviewTests(unittest.TestCase):
    def test_reproduction_and_exact_partition(self):
        actual = review.build()
        self.assertEqual(actual, json.loads((ROOT / review.OUT).read_text()))
        record = actual['records'][0]
        self.assertEqual(record['scan_page'], 245)
        self.assertEqual(record['printed_page'], 233)
        original = record['original_text']
        pieces = sorted(record['exclusions'] + record['voting_segments'], key=lambda p: p['start'])
        self.assertEqual([(p['start'], p['end']) for p in pieces], [(0, 21), (21, 3854), (3854, 4353)])
        self.assertEqual(''.join(p.get('original_text', p.get('text')) for p in pieces), original)
        self.assertTrue(record['exclusions'][1]['original_text'].startswith('\na. 15. τετρακισχ.'))
        self.assertNotIn('a. 15.', record['voting_segments'][0]['text'])

    def test_changed_source_request_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [review.NETWORK, Path('data/corpus_changes/photius-bekker-coverage/witnesses') / (review.RAW_SHA + '.jsonl')]
            for path in paths:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).symlink_to(ROOT / path)
            (root / review.MANIFEST).write_bytes((ROOT / review.MANIFEST).read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'source request changed'):
                review.build(root)


if __name__ == '__main__':
    unittest.main()
