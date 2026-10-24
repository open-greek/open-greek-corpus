"""The preserved Harvard readings must not acquire independent vote weight."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import dubner_witness_alignment as alignment
from repair_dubner_scholias import archived_inputs


class HarvardWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = {path: raw for path, raw in archived_inputs(ROOT).items()
                      if path in alignment.PINS}
        cls.records = alignment.source_rows(ROOT, cls.before)

    def test_every_literal_and_fallback_reading_shares_one_vote_group(self):
        self.assertEqual(Counter(r["derived"] for r in self.records),
                         {False: 20395, True: 476})
        self.assertEqual({r["group"] for r in self.records}, {alignment.B_GROUP})
        self.assertEqual(len({r["id"] for r in self.records}), len(self.records))
        self.assertEqual(sum(len(r["alternatives"]) for r in self.records), 1854)

    def test_archived_inputs_allow_replay_without_current_legacy_files(self):
        self.assertEqual(alignment.source_rows(Path("/not-a-current-checkout"), self.before),
                         self.records)
        changed = dict(self.before)
        changed[alignment.B_PRIMARY] += b"\n"
        with self.assertRaisesRegex(ValueError, "pin mismatch"):
            alignment.source_rows(ROOT, changed)

    def test_constructed_lane_retains_literal_preimages_and_all_alternatives(self):
        originals = {r["id"]: r for r in self.records if not r["derived"]}
        for record in self.records:
            if not record["derived"]:
                continue
            original = originals[record["id"].removesuffix(":fallback-alternative")]
            text = original["row"]["text"]
            for variant in sorted(record["alternatives"], key=lambda v: v["offset"], reverse=True):
                start = variant["offset"]
                self.assertEqual(text[start:start + len(variant["original"])], variant["original"])
                text = text[:start] + variant["alternative"] + text[start + len(variant["original"]):]
            self.assertEqual(record["row"]["text"], text)
            self.assertNotEqual(record["row"]["text"], original["row"]["text"])

    def test_fallback_preimage_drift_is_not_fuzzy_relocated(self):
        rows = [json.loads(line) for line in self.before[alignment.B_PRIMARY].splitlines()]
        audit = json.loads(self.before[alignment.MERGE_AUDIT])
        guesses = json.loads(self.before[alignment.MERGE_GUESSES])
        record = next(r for r in self.records if r["derived"])
        row = next(r for r in rows if r["locus"] == record["row"]["locus"])
        row["text"] = "changed " + row["text"]
        with self.assertRaisesRegex(ValueError, "preimage mismatch"):
            alignment.fallback_rows(rows, audit, guesses)

    def test_page_concordance_accounts_for_repeated_and_missing_leaves(self):
        for harvard, toronto in [(24, 23), (44, 43), (138, 137), (139, 130),
                                 (209, 182), (382, 355), (383, 358),
                                 (534, 509), (535, 508), (793, 768)]:
            self.assertEqual(alignment.harvard_to_toronto(harvard), toronto)
        self.assertIsNone(alignment.harvard_to_toronto(698))
        self.assertIsNone(alignment.harvard_to_toronto(800))
        self.assertTrue(all(r["toronto_page"] is not None for r in self.records
                            if 24 <= r["source_page"] <= 683))


if __name__ == "__main__":
    unittest.main()
