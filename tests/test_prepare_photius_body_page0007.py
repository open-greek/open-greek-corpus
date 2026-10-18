"""Exact evidence and original-prefix preservation for the bounded page7 repair."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('page7_review', ROOT / 'scripts/prepare_photius_body_page0007.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class Page7BodyReviewTests(unittest.TestCase):
    def test_exact_reproduction_and_missing_body_bounds(self):
        actual = review.build()
        self.assertEqual(actual, json.loads((ROOT / review.OUT).read_text()))
        old = actual['original_row']['text']
        scope = actual['replacement_scope']
        self.assertEqual((scope['start'], scope['end']), (981, 1030))
        self.assertEqual(scope['original_text'], old[981:])
        self.assertTrue(old[:981].endswith('τὸ λοιπὸν '))
        self.assertTrue(all(w['text'].startswith('συνεκφωνεῖσθαί') for w in actual['witnesses']))
        self.assertTrue(all(w['text'].endswith('βληθῇ,') for w in actual['witnesses']))
        self.assertEqual((actual['source']['scan_page'], actual['source']['printed_page']), (7, 272))
        self.assertEqual(actual['following_body_anchor']['locus'], 'helladius_chrestomathia_photius_bekker_v2_0008.1')
        manual, digital = (w['text'] for w in actual['witnesses'])
        self.assertIn('οὐκ ἄνθρωπον', manual)
        self.assertIn('ἐκ ἀνθρώπου', digital)
        self.assertIn('ἀντικρὺς', manual)
        self.assertIn('ἀνεκήρυξε', digital)
        self.assertEqual(actual['source_library_credit']['license']['url'], 'https://creativecommons.org/licenses/by-sa/4.0/')

    def test_changed_digital_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / review.SOURCE_LIBRARY
            path.parent.mkdir(parents=True)
            path.write_bytes((ROOT / review.SOURCE_LIBRARY).read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'digital source changed'):
                review.build(root)


if __name__ == '__main__':
    unittest.main()
