"""Reviewed body roles and boundary exclusions stay exact and reproducible."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reading_windows', ROOT / 'scripts/prepare_photius_reading_windows.py')
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReadingWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authority = review.build()
        cls.rows = {r['scan_page']: r for r in cls.authority['records']}

    def test_reproduction_and_absent_early_source(self):
        self.assertEqual(self.authority, json.loads((ROOT / review.OUT).read_text()))
        expected = {14, *range(34, 279), *range(379, 422)} - {85, 87, 95, 96}
        self.assertEqual(expected, set(self.rows))
        self.assertEqual(sum(r['source_section'] is not None for r in self.rows.values()), 284)
        self.assertEqual(len([r for r in self.authority['records'] if r['scan_page'] == 153]), 1)
        table = self.authority['review_tables'][0]
        self.assertEqual(table['sha256'], review.sha((ROOT / table['path']).read_bytes()))
        self.assertIsNone(self.rows[14]['source_section'])
        self.assertEqual([r['scan_page'] for r in self.authority['unavailable_source_library']], [14, 33, 85, 87, 95, 96])
        self.assertNotIn(13, self.rows)
        self.assertNotIn(33, self.rows)

    def test_complete_raw_partition_and_no_invented_boundary_tokens(self):
        for page, row in self.rows.items():
            if row['source_section'] is None:
                continue
            text = row['source_section']['full_original_text']
            pieces = sorted(row['voting_segments'] + row['held_spans'], key=lambda s: s['start'])
            self.assertEqual(pieces[0]['start'], 0)
            self.assertEqual(pieces[-1]['end'], len(text))
            self.assertEqual(''.join(p.get('text', p.get('original_text')) for p in pieces), text)
            self.assertTrue(all(a['end'] == b['start'] for a, b in zip(pieces, pieces[1:])))
        for page, excluded in [(37, 'Περσῶν'), (40, 'Κωνξαντίνῃ'), (232, 'θαυμιαζὸν'), (385, 'χελιδόνων'), (396, 'ἐγίνοντο'), (384, 'ἡμέτερος'), (387, 'σοφώτερος.'), (389, 'συνεἰδότων'), (390, 'δίμορφον'), (393, 'τοσαύτην'), (397, 'ἀποπληρῦντος,'), (402, 'ἐξηλλαγμένην'), (403, 'ἐπονομάσαντες.'), (407, 'ἀσφαλῶς'), (411, 'κρείττονος'), (419, 'πολλαῖς')]:
            self.assertTrue(self.rows[page]['held_spans'][0]['original_text'].endswith(excluded))
            self.assertFalse(self.rows[page]['voting_segments'][0]['text'].endswith(excluded))
        self.assertIn('abstain-at-unobserved-prefix', self.rows[385]['first_boundary_policy'])
        self.assertEqual(self.rows[385]['printed_prefix_fragment'], 'ρος')
        self.assertEqual(self.rows[38]['printed_prefix_fragment'], 'σῶν')
        self.assertEqual(self.rows[41]['printed_prefix_fragment'], 'σαντίνῃ')
        self.assertEqual(self.rows[88]['printed_prefix_fragment'], 'ρεῖς')
        self.assertEqual(self.rows[88]['held_spans'][0]['original_text'], 'ρεῖς ')
        self.assertEqual(self.rows[88]['voting_segments'][0]['start'], 5)

    def test_only_exact_source_confirmed_headers_masked(self):
        for page, end in [(14, len(review.HEADER_PREFIXES[14])), (36, len(review.HEADER_PREFIXES[36])), (37, len(review.HEADER_PREFIXES[37])), (153, 12), (396, 15)]:
            mask = self.rows[page]['raw_witness_masks'][0]
            span = mask['exclusions'][0]
            self.assertEqual((span['start'], span['end']), (0, end))
            self.assertEqual(span['original_text'], mask['original_text'][:end])
            self.assertEqual(span['classification'], 'running_header')
            self.assertGreater(len(mask['original_text'][end:]), 1000)
        self.assertGreaterEqual(sum(len(r['raw_witness_masks']) for r in self.rows.values()), 16)
        both_models = self.rows[256]['raw_witness_masks']
        self.assertEqual({m['witness']['model'] for m in both_models},
                         {'Qwen/Qwen3.6-27B', 'Qwen/Qwen3.8-27B-FP8'})
        self.assertEqual(len(both_models), 2)
        for page in (265, 271, 379, 404, 407, 415, 418):
            self.assertEqual(len(self.rows[page]['raw_witness_masks']), 1)
        for page, fragment in {386: 'λιδόνων', 388: 'φώτερος', 390: 'εἰδότων',
                               391: 'φον', 394: 'σαύτην', 397: 'νοντο', 398: 'ρῦντος',
                               403: 'λαγμένην', 404: 'μάσαντες', 408: 'λῶς',
                               412: 'τονος', 420: 'λαῖς'}.items():
            self.assertEqual(self.rows[page]['printed_prefix_fragment'], fragment)

    def test_changed_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / review.LIBRARY).parent.mkdir(parents=True)
            (root / review.LIBRARY).write_bytes((ROOT / review.LIBRARY).read_bytes() + b'\n')
            (root / review.NETWORKS).symlink_to(ROOT / review.NETWORKS)
            with self.assertRaisesRegex(ValueError, 'Pinned source'):
                review.build(root)


if __name__ == '__main__':
    unittest.main()
