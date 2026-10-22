"""The later source-role layer preserves identity, witnesses, and exclusions."""
from collections import Counter
from copy import deepcopy
from unittest.mock import patch
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import photius_remaining_roles as roles
import prepare_photius_editorial_continuation as continuation


class RemainingRoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before,cls.scopes=continuation.scope(ROOT)

    def test_exact_published_nonbody_accounting(self):
        expected={k for k,v in self.scopes.items()
                  if v['record']['decision']=='retained-nonbody'}
        authored={(r['locus'],r['segment_index'])for r in roles.SPECS}
        self.assertEqual(authored,expected)
        self.assertEqual(len(roles.SPECS),39)
        self.assertEqual(Counter(s['role']for s in roles.SPECS),{
            'authorial-body':16,'transmitted-historical-commentary':20,
            'marginal-reference':3})
        for spec in roles.SPECS:
            target=self.scopes[spec['locus'],spec['segment_index']]
            self.assertEqual(spec['original_text'],
                target['row']['text'][target['start']:target['end']])
            self.assertEqual(spec['original_role'],
                target['record']['original_segment']['text_role'])

    def test_wrapper_retirement_has_exact_original_greek_extents(self):
        key=('helladius_chrestomathia_photius_bekker_v2_0220.6',0)
        self.assertEqual(roles.RETIRED_WRAPPERS,{key:{'prefix':'# ','suffix':'.1452B.'}})
        spec=next(s for s in roles.SPECS if(s['locus'],s['segment_index'])==key)
        words=list(roles.edition.WORD.finditer(spec['original_text']))
        self.assertEqual(spec['original_text'][:words[0].start()],'# ')
        self.assertEqual(spec['original_text'][words[-1].end():],'.1452B.')

    def test_rendering_overrides_are_two_exact_reviewed_boundaries(self):
        self.assertEqual(roles.RENDERING,{
            ('helladius_chrestomathia_photius_bekker_v2_0220.6',0):
                {'retire_prefix':'# ','retire_suffix':'1452B.'},
            ('helladius_chrestomathia_photius_bekker_v2_0164.5',3):
                {'separate_verified_suffix':'καὶ','boundary_after':' '}})
        target=self.scopes['helladius_chrestomathia_photius_bekker_v2_0164.5',3]
        self.assertTrue(target['row']['text'][target['end']:].startswith('καὶ μὴν'))
        self.assertEqual(target['row']['text'][target['start']:target['end']],'αὐτὸ')

    def test_frozen_source_pins(self):
        for path,expected in roles.SOURCE_PINS.items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),expected)

    def test_every_role_has_inspected_region_and_independent_qualification(self):
        for spec in roles.SPECS:
            self.assertEqual(spec['confidence'],'high')
            self.assertIn('physical_page',spec['scan'])
            self.assertEqual(len(spec['scan']['region']),4)
            self.assertEqual(len(spec['scan']['image_sha256']),64)
            self.assertTrue(spec['evidence'])
            if spec['role']=='marginal-reference':
                self.assertIsNone(spec['selection'])
            else:
                self.assertIsNotNone(spec['selection'])
                self.assertNotIn('personally composed',spec['evidence'])
        self.assertIn('does not independently date',
            roles._QUALIFICATIONS['transmitted-historical-commentary'])
        self.assertIn('No choice between competing numeral readings',
            roles._QUALIFICATIONS['marginal-reference'])

    def test_unpinned_html_rejected_without_input_mutation(self):
        before=deepcopy(self.scopes)
        with self.assertRaisesRegex(ValueError,'differs from the reviewed source'):
            roles.review_roles(b'<html>another source</html>',self.scopes)
        self.assertEqual(self.scopes,before)

    def test_source_reading_must_be_unique_inside_reviewed_paragraph(self):
        def token(text,unit):
            return {'text':text,'key':roles.edition.normalize(text),
                    'refs':[{'unit_index':unit,'start':0,'end':len(text),
                        'html_line':1,'html_column':0,'bekker':'424a','codex':'248'}]}
        spec={'selection':(0,1,'σίγα')}
        self.assertEqual(roles._reading(spec,[token('σίγα',0)])[0]['text'],'σίγα')
        with self.assertRaisesRegex(ValueError,'absent or repeated'):
            roles._reading(spec,[token('σίγα',0),token('σίγα',0)])
        with self.assertRaisesRegex(ValueError,'absent or repeated'):
            roles._reading(spec,[token('σίγα',1)])

    def test_only_exact_role_identity_is_eligible(self):
        for spec in roles.SPECS:
            self.assertTrue(spec['locus'].startswith('helladius_chrestomathia_photius_bekker_v2_'))
            self.assertIsInstance(spec['segment_index'],int)
        self.assertEqual(len({(s['scan']['physical_page'],tuple(s['scan']['region']))
                              for s in roles.SPECS}),29)


class StrictRecordedRoleTests(unittest.TestCase):
    def role_case(self,*,boundary=False):
        spec=deepcopy(roles.SPECS[20 if boundary else 0])
        text='ἀεί'if boundary else'σαφές'
        units=[{'text':text,'html_line':1,'html_column':0,'unit_index':0,
                'codex':'248','bekker':'429b'}]
        spec.update(selection=(0,1,text),context_sha256=roles._digest(units))
        return spec,roles._role_record(spec,units)

    def test_every_recorded_role_field_is_bound_to_authored_evidence(self):
        spec,record=self.role_case();key=(spec['locus'],spec['segment_index'])
        mutations=[
            lambda r:r.update(role='marginal-reference'),
            lambda r:r.update(original_role='authorial-body'),
            lambda r:r.update(original_text='changed'),
            lambda r:r.update(confidence='low'),
            lambda r:r.update(subtype='changed'),
            lambda r:r.update(evidence='changed'),
            lambda r:r.update(qualification='changed'),
            lambda r:r.update(rendering={'retire_suffix':'.'}),
            lambda r:r.update(retired_wrappers={'prefix':'#'}),
            lambda r:r['scan'].update(physical_page=999),
            lambda r:r['scan'].update(region=[0,0,1,1]),
            lambda r:r['scan'].update(image_sha256='0'*64),
            lambda r:r['scan']['source'].update(path='another.pdf'),
            lambda r:r['scan']['source'].update(sha256='0'*64),
            lambda r:r['scan'].update(reviewed_at='changed'),
            lambda r:r['scan'].update(review_basis='another method'),
            lambda r:r['scan'].update(prior_observed_text='changed'),
            lambda r:r['role_context'].update(sha256='0'*64),
            lambda r:r['role_context'].update(source_id='another-source'),
            lambda r:r['role_context'].update(qualification='changed'),
            lambda r:r['role_context']['units'][0].update(text='changed'),
            lambda r:r['role_context']['units'][0].update(html_column=1),
            lambda r:r['readings'][0].update(text='changed'),
            lambda r:r['readings'][0].update(source_id='another-source'),
            lambda r:r['readings'][0]['tokens'][0].update(text='changed'),
            lambda r:r['readings'][0]['tokens'][0]['refs'][0].update(start=1),
            lambda r:r.update(extra_unreviewed_permission=True)]
        with patch.object(roles,'SPECS',[spec]):
            self.assertEqual(roles.validate_record(key,record),record)
            for i,mutate in enumerate(mutations):
                with self.subTest(field=i):
                    changed=deepcopy(record);mutate(changed)
                    with self.assertRaises(ValueError):roles.validate_record(key,changed)
            with self.assertRaisesRegex(ValueError,'Unknown'):
                roles.validate_record(('another-row',0),record)

    def test_fixed_following_token_and_rendering_cannot_change(self):
        spec,record=self.role_case(boundary=True);key=(spec['locus'],spec['segment_index'])
        with patch.object(roles,'SPECS',[spec]):
            self.assertEqual(roles.validate_record(key,record),record)
            for field in ('boundary_after','separate_verified_suffix'):
                changed=deepcopy(record);changed['rendering'][field]='changed'
                with self.assertRaises(ValueError):roles.validate_record(key,changed)
            changed=deepcopy(record)
            changed['rendering']['next_source_token']['refs'][0]['unit_index']+=1
            with self.assertRaises(ValueError):roles.validate_record(key,changed)

    def test_fresh_verified_correction_has_its_own_strict_authority(self):
        spec=deepcopy(roles.CORRECTIONS[0])
        units=[{'text':'τὸ δεῖ νομίζειν.','html_line':1,'html_column':0,
                'unit_index':0,'codex':'248','bekker':'429b'}]
        spec.update(selection=(0,1,'τὸ δεῖ νομίζειν'),context_sha256=roles._digest(units))
        record=roles._correction_record(spec,units)
        with patch.object(roles,'CORRECTIONS',[spec]):
            self.assertEqual(roles.validate_correction_record(record),record)
            for field in ('id','locus','start','end','original_row_sha256',
                          'original_text','corrected_text','prior_verification',
                          'evidence','qualification'):
                changed=deepcopy(record);changed[field]='changed'
                with self.assertRaises(ValueError):roles.validate_correction_record(changed)
            changed=deepcopy(record);changed['source_context']['units'][0]['text']='changed'
            with self.assertRaises(ValueError):roles.validate_correction_record(changed)
            changed=deepcopy(record);changed['readings'][0]['tokens'][0]['text']='changed'
            with self.assertRaises(ValueError):roles.validate_correction_record(changed)
            changed=deepcopy(record);changed['scan']['observed_text']='changed'
            with self.assertRaises(ValueError):roles.validate_correction_record(changed)

    def test_complete_reviewed_note_accounts_for_every_verified_fix(self):
        _,scopes=continuation.scope(ROOT)
        row=scopes['helladius_chrestomathia_photius_bekker_v2_0164.8',0]['row']
        text=row['text'];edits=[(s['start'],s['end'],s['corrected_text'])for s in roles.CORRECTIONS]
        # The two old uncertain words are adopted from their distinct reviewed
        # Henry witnesses; the four newly discovered verified defects stay separate.
        edits.extend([(0,6,'Λείπει'),(25,51,'Κρανίαν τὴν περικεφαλαίαν')])
        for a,b,new in sorted(edits,reverse=True):text=text[:a]+new+text[b:]
        self.assertEqual(text,'Λείπει τὸ δεῖ νομίζειν. Κρανίαν τὴν περικεφαλαίαν λέγει, βύρσαν δὲ τὸ ὅπλον παρὰ τὸ ἔχειν βύρσαν περὶ αὐτὸ, νήϊα δὲ τὰ σχοινία, κωπέας δὲ τὰ ξύλα τὰ πρὸς κώπας ἐπιτήδεια.')
        for spec in roles.CORRECTIONS:
            proof=spec['prior_verification_evidence']
            self.assertEqual(proof['verification'],'verified')
            self.assertLessEqual(proof['start'],spec['start'])
            self.assertGreaterEqual(proof['end'],spec['end'])
            self.assertEqual(row['text'][proof['start']:proof['end']],proof['text'])

    def test_context_pins_cover_every_original_and_fresh_case(self):
        self.assertEqual(len(roles.CORRECTIONS),4)
        for spec in roles.SPECS+roles.CORRECTIONS:
            self.assertRegex(spec['context_sha256'],r'^[0-9a-f]{64}$')
        self.assertEqual(roles.CORRECTIONS[0]['prior_verification'],'verified')
        old={(s['locus'],s['segment_index'])for s in roles.SPECS}
        self.assertNotIn((roles.CORRECTIONS[0]['locus'],'verified-correction'),old)


if __name__=='__main__':
    unittest.main()
