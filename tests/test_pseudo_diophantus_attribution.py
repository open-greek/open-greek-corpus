import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import correct_pseudo_diophantus_attribution as owner


class AttributionReplayTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        audit = json.loads((ROOT / owner.AUDIT).read_bytes())
        for name in (*owner.FILES, owner.AUDIT, *(v['path'] for v in audit['evidence'])):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def tearDown(self):
        self.temp.cleanup()

    def rewrite(self, name, change):
        path = self.root / name
        value = json.loads(path.read_bytes())
        change(value)
        path.write_text(json.dumps(value, ensure_ascii=False))

    def test_exact_scope_native_id_and_reversible_unknowns(self):
        owner.replay(self.root, check=True)
        before = {name: json.loads((self.root / name).read_bytes()) for name in owner.FILES}
        withdrawn = owner.replay(self.root, apply=True, undo=True)
        self.assertEqual(len(withdrawn['changed']), 3)
        owner.replay(self.root, check=True, undo=True)
        self.assertRaises(ValueError, owner.replay, self.root, check=True)
        owner.replay(self.root, apply=True)
        after = {name: json.loads((self.root / name).read_bytes()) for name in owner.FILES}
        self.assertEqual(before, after)
        self.assertEqual(owner.replay(self.root, check=True)['changed'], [])
        work = after[owner.FILES[2]]['works'][owner.WORK]
        self.assertEqual(work['id'], 'ogc001159')
        self.assertEqual(work['author']['name'], 'Pseudo-Diophantus')
        self.assertEqual(work['author']['authorities'], {})
        self.assertIsNone(work['attribution']['year'])
        self.assertIsNone(work['attribution']['place'])
        self.assertEqual(work['work_anchors']['cts'], owner.CTS)

    def test_every_foreign_value_and_absence_is_preserved(self):
        owner.replay(self.root, apply=True, undo=True)
        self.rewrite(owner.FILES[0], lambda d: d['works']['abydenus.fragmenta']['editions']['abydenus.fragmenta.dfhg'].__setitem__('year', None))
        before = json.loads((self.root / owner.FILES[0]).read_bytes())
        owner.replay(self.root, apply=True)
        after = json.loads((self.root / owner.FILES[0]).read_bytes())
        for key, value in before['works'].items():
            if key != owner.WORK:
                self.assertEqual(value, after['works'][key])

    def test_wrong_primary_source_refuses_before_writes(self):
        path = self.root / 'data/corpus_changes/sources/diophantus_fragment_20261109/edition.xml'
        path.write_bytes(path.read_bytes().replace(b'PSEUDEPIGRAPHUS', b'GENUINUS'))
        before = [(self.root / n).read_bytes() for n in owner.FILES]
        self.assertRaisesRegex(ValueError, 'primary evidence', owner.replay, self.root, apply=True)
        self.assertEqual(before, [(self.root / n).read_bytes() for n in owner.FILES])

    def test_changed_audit_refuses(self):
        self.rewrite(owner.AUDIT, lambda d: d.__setitem__('cts', 'urn:cts:greekLit:tlg2039.tlg001'))
        self.assertRaisesRegex(ValueError, 'declaration changed', owner.replay, self.root, apply=True)

    def test_foreign_work_anchor_refuses(self):
        self.rewrite(owner.FILES[2], lambda d: d['works'][owner.WORK]['work_anchors'].__setitem__('cts', 'urn:cts:greekLit:tlg2039.tlg001'))
        self.assertRaisesRegex(ValueError, 'anchors', owner.replay, self.root, apply=True)

    def test_mixed_original_and_corrected_state_refuses(self):
        self.rewrite(owner.FILES[0], lambda d: d['works'][owner.WORK].__setitem__('author', 'diophantus-mathematics'))
        self.assertRaisesRegex(ValueError, 'original/corrected', owner.replay, self.root, apply=True)

    def test_injected_personal_authority_refuses(self):
        self.rewrite(owner.FILES[0], lambda d: d['authors']['pseudo-diophantus']['aliases'].__setitem__('wikidata', 'Q178217'))
        self.assertRaisesRegex(ValueError, 'name-only author identity', owner.replay, self.root, apply=True)

    def test_withdrawal_never_reuses_or_deletes_agent_id(self):
        before = json.loads((self.root / owner.FILES[1]).read_bytes())
        owner.replay(self.root, apply=True, undo=True)
        after = json.loads((self.root / owner.FILES[1]).read_bytes())
        self.assertEqual(set(before['authors']), set(after['authors']))
        pseudo = [i for i, row in after['authors'].items() if row['slug'] == 'pseudo-diophantus']
        self.assertEqual(len(pseudo), 1)
        self.assertEqual(after['authors'][pseudo[0]]['status'], 'retired')

    def test_owned_integer_cannot_be_replaced_by_equal_float(self):
        value = json.loads((self.root / owner.FILES[2]).read_bytes())
        integer = value['works'][owner.WORK]['manifestation']['n_tokens']
        self.assertEqual(integer, float(integer))  # ordinary Python equality misses it
        self.rewrite(owner.FILES[2], lambda d: d['works'][owner.WORK]['manifestation'].__setitem__('n_tokens', float(integer)))
        self.assertRaisesRegex(ValueError, 'identity or types', owner.replay, self.root, apply=True)

    def test_owned_count_cannot_be_replaced_by_boolean(self):
        self.rewrite(owner.FILES[2], lambda d: d['works'][owner.WORK]['manifestation'].__setitem__('n_analysis_tokens', True))
        self.assertRaisesRegex(ValueError, 'identity or types', owner.replay, self.root, apply=True)

    def test_strict_json_identity_distinguishes_false_zero_and_integer_float(self):
        self.assertFalse(owner.same({'x': False}, {'x': 0}))
        self.assertFalse(owner.same({'x': 3}, {'x': 3.0}))
        self.assertFalse(owner.same({'x': None}, {}))

    def test_withdrawal_keeps_label_served_when_foreign_work_uses_it(self):
        self.rewrite(owner.FILES[0], lambda d: d['works']['abydenus.fragmenta'].__setitem__('author', 'pseudo-diophantus'))
        self.rewrite(owner.FILES[2], lambda d: d['works']['abydenus.fragmenta'].__setitem__('author', d['works'][owner.WORK]['author']))
        before = json.loads((self.root / owner.FILES[2]).read_bytes())['works']['abydenus.fragmenta']
        owner.replay(self.root, apply=True, undo=True)
        after = json.loads((self.root / owner.FILES[2]).read_bytes())
        self.assertTrue(owner.same(before, after['works']['abydenus.fragmenta']))
        ledger = json.loads((self.root / owner.FILES[1]).read_bytes())
        self.assertEqual([r['status'] for r in ledger['authors'].values() if r['slug'] == 'pseudo-diophantus'], ['served'])

    def test_preexisting_wrong_label_name_refuses_even_without_qid(self):
        self.rewrite(owner.FILES[0], lambda d: d['authors']['pseudo-diophantus'].__setitem__('name', 'Diophantus'))
        self.assertRaisesRegex(ValueError, 'name-only author identity', owner.replay, self.root, apply=True)

    def test_original_registry_null_is_not_the_absent_owned_field(self):
        owner.replay(self.root, apply=True, undo=True)
        self.rewrite(owner.FILES[0], lambda d: d['works'][owner.WORK].__setitem__('attribution', None))
        self.assertRaisesRegex(ValueError, 'original/corrected', owner.replay, self.root, apply=True)
