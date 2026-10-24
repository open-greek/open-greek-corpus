"""Source boundaries preserve literal readings and distinguish edition apparatus."""
from __future__ import annotations
import copy
import importlib.util
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import westermann_source_observations as observations

@pytest.fixture(scope='module')
def rows():
 return {r['locus']:r for r in observations.original_rows(ROOT)}


def test_every_original_row_has_a_lossless_ordered_partition(rows):
 assert len(rows)==7013
 for row in rows.values():
  parts=observations.partitions(row)
  assert parts[0]['start']==0
  assert parts[-1]['end']==len(row['text'])
  assert all(a['end']==b['start'] for a,b in zip(parts,parts[1:]))
  assert ''.join(row['text'][p['start']:p['end']] for p in parts)==row['text']
  assert all(p['work'] is None or p['work'] in observations.work_definitions() for p in parts)


def test_source_pages_and_edition_identity_are_not_marcellinus(rows):
 review=observations.source_review(ROOT)
 assert review['source']['year']==1845
 assert review['source']['editor']=='Antonius Westermann'
 assert review['source']['pdf_pages']==520
 assert [p['source_pdf_page'] for p in review['pages']]==list(range(5,517))
 assert sum(p['original_rows'] for p in review['pages'])==7013
 assert len(review['works'])==96
 assert observations.partitions(rows['marcellinus_westermann_0005.1'])[0]['role']=='editorial'
 assert observations.partitions(rows['marcellinus_westermann_0028.1'])[0]['role']=='editorial'
 assert observations.partitions(rows['marcellinus_westermann_0489.1'])[0]['role']=='index'


def test_actual_marcellinus_scope_stops_before_anonymous_life(rows):
 before=observations.partitions(rows['marcellinus_westermann_0214.5'])[0]
 after=observations.partitions(rows['marcellinus_westermann_0228.2'])[0]
 assert before['work']=='marcellinus-thucydides'
 assert before['role']=='historical-body'
 assert after['work']=='thucydides-anonymous'


def test_thomas_paragraph_does_not_admit_prior_life_apparatus(rows):
 row=rows['marcellinus_westermann_0187.2']
 first,last=observations.partitions(row)
 assert first['work']=='aristophanes-thomas'
 assert first['role']=='historical-body'
 assert last['role']=='apparatus'
 assert row['text'][last['start']:].startswith('ὑποκριτῶν ἐπτάκις')
 assert 'Dindorfius' not in row['text'][first['start']:first['end']]


def test_inserted_suda_apparatus_does_not_consume_later_body(rows):
 row=rows['marcellinus_westermann_0451.1']
 first,last=observations.partitions(row)
 assert first['role']=='historical-body'
 assert last['role']=='apparatus'
 assert observations.partitions(rows['marcellinus_westermann_0451.2'])[0]['role']=='historical-body'
 assert observations.partitions(rows['marcellinus_westermann_0451.3'])[0]['role']=='heading'


def test_greek_only_apparatus_continuations_remain_outside_primary_counts(rows):
 for locus in ['marcellinus_westermann_0186.27','marcellinus_westermann_0231.27',
               'marcellinus_westermann_0271.20','marcellinus_westermann_0278.26']:
  assert observations.partitions(rows[locus])[0]['role']=='apparatus'


def test_no_author_is_inferred_from_a_biography_subject():
 works=observations.work_definitions()
 assert works['aratus-a']['author']=='biographi-anonymi'
 assert works['oppian-manasses']['author']=='constantinus-manasses'
 assert works['suda-epic-poets']['author']=='suda'
 assert works['aristotle-ammonius']['author']=='pseudo-ammonius'
 assert works['antiphon-eudocia']['author']!='eudocia-augusta'
 assert 'personal identity uncertain' in works['antiphon-eudocia']['author_name']


def test_comparative_commentary_target_is_not_the_biography_identity():
 works=observations.work_definitions()
 for key in ['euripides-anonymous','aeschylus-life','nicander-life','theocritus-life','de-comoedia']:
  assert works[key]['admission']=='comparative'
  assert 'related_existing_primary' in works[key]
  assert 'canonical_target' not in works[key]


def test_changed_inline_anchors_fail_closed(rows):
 row=copy.deepcopy(rows['marcellinus_westermann_0187.2'])
 row['text']=row['text'].replace('ὑποκριτῶν ἐπτάκις','changed')
 with pytest.raises(ValueError,match='inline partition anchor changed'):
  observations.partitions(row)


def test_unknown_locus_is_rejected(rows):
 row=copy.deepcopy(rows['marcellinus_westermann_0187.2']);row['locus']='unknown'
 with pytest.raises(ValueError,match='Unexpected Westermann source locus'):
  observations.partitions(row)
