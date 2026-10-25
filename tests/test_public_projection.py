import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from frequency_projection import FrequencyProjection, lexical_text


class PublicProjectionTests(unittest.TestCase):
    def setUp(self):
        self.projection = FrequencyProjection(Path("data"))

    def test_lexical_exclusions_do_not_manufacture_adjacency(self):
        row = {"text": "λόγος ⟦ἀσαφές⟧ καλός", "analysis_text": "λόγος καλός",
               "analysis_segments": ["λόγος", "καλός"], "contextual_eligible": False}
        self.assertEqual(self.projection.text(row), "λόγος καλός")
        self.assertEqual(self.projection.segments(row), ["λόγος", "καλός"])
        self.assertIsNone(self.projection.contextual_text(row))

    def test_an_opaque_projection_supplies_no_context(self):
        row = {"text": "λόγος καλός", "analysis_text": "λόγος"}
        self.assertEqual(self.projection.segments(row), [])
        self.assertIsNone(self.projection.contextual_text(row))

    def test_unprojected_text_preserves_context(self):
        row = {"text": "λόγος καλός"}
        self.assertEqual(self.projection.segments(row), ["λόγος καλός"])
        self.assertEqual(self.projection.contextual_text(row), "λόγος καλός")

    def test_malformed_export_is_rejected(self):
        with self.assertRaises(ValueError):
            lexical_text({"analysis_text": None})
        with self.assertRaises(ValueError):
            self.projection.segments({"text": "λόγος", "analysis_segments": [None]})
