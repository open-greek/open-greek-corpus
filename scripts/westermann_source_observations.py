#!/usr/bin/env python3
"""Reviewed source scope of Westermann, Vitarum Scriptores Graeci Minores (1845).

The extraction was incorrectly filed as one Marcellinus work. The ranges below
follow the printed contents and headings, never the identity of a biography's
subject. Full original rows and every Unicode character remain reconstructible.
"""
from __future__ import annotations
import bisect
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_PATH = 'data/corpus/marcellinus.vita-thucydidis.jsonl'
ORIGINAL_SHA256 = 'f981d2caff071cb9e88ffdf3784de725ff56a3b7a49de11a58d6b1d9180e2dd7'
ARCHIVE_PATH = 'data/ocr_witnesses/westermann-1845-original-rows.jsonl'
OUTPUT = 'data/corpus_changes/westermann-source-review'
REVIEW_PATH = OUTPUT + '/source-review.json'
CAPTURE_PATH = OUTPUT + '/capture.json'
REVIEWED_AT = '2026-10-24'
SOURCE = {
 'id': 'westermann-toronto-1845',
 'title': 'Βιογράφοι. Vitarum Scriptores Graeci Minores',
 'editor': 'Antonius Westermann', 'year': 1845,
 'place': 'Brunsvigae', 'publisher': 'Georgius Westermann',
 'url': 'https://archive.org/details/biographoivitaru00westuoft',
 'artifact_url': 'https://archive.org/download/biographoivitaru00westuoft/biographoivitaru00westuoft.pdf',
 'filename': 'biographoivitaru00westuoft.pdf',
 'sha256': '01581997fcec0a973d059b9c62727ced6bfff76e3e7b7ea16a06732b236fe1e7',
 'bytes': 32649726, 'pdf_pages': 520, 'license': 'PD',
 'printed_to_pdf_offset': 28,
 'qualification': 'The printed attribution is retained, including anonymous and bracketed attributions. Printed biography subjects are not assigned authorship. This is one edition and one scan, not multiple independent witnesses.',
}
# start PDF page and numeric extraction row, source unit, attribution, title,
# admission, independently served target (when the scope is a complete work).
# Boundary headings and modern apparatus are separately routed by partitions().
UNITS = (
 (29,1,'homer-herodotean','pseudo-herodotus','Pseudo-Herodotus','Vita Homeri (Herodotean life)','comparative','vitae-homeri.vita-herodotea'),
 (49,1,'homer-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Homeri (Westermann excerpt)','comparative','vitae-homeri.plutarchi-vita'),
 (52,11,'homer-proclus','proclus-grammaticus','Proclus (printed attribution)','De Homero (Chrestomathia excerpt)','comparative','vitae-homeri.vita-proculea-e-chrestomathia'),
 (55,5,'homer-anonymous-4','biographi-anonymi','Anonymous','Vita Homeri IV (Westermann)','comparative','vitae-homeri.vita-quarta'),
 (56,15,'homer-anonymous-5','biographi-anonymi','Anonymous','Vita Homeri V (Westermann)','comparative','vitae-homeri.vita-quinta'),
 (58,20,'homer-anonymous-6','biographi-anonymi','Anonymous','Vita Homeri VI (Westermann)','comparative','vitae-homeri.vita-sexta'),
 (59,4,'suda-homer','suda','Suda','Lexicon: Homer excerpt','comparative','suda.lexicon'),
 (61,20,'homer-hesiod-contest','biographi-anonymi','Anonymous','Certamen Homeri et Hesiodi','comparative','certamen-homeri-et-hesiodi.certamen-homeri-et-hesiodi'),
 (73,20,'hesiod-proclus','proclus-grammaticus','Proclus (printed attribution)','Genus Hesiodi','comparative','vitae-hesiodi-particula.vitae-hesiodi-particula'),
 (77,19,'suda-hesiod','suda','Suda','Lexicon: Hesiod excerpt','comparative','suda.lexicon'),
 (78,2,'apollonius-a','biographi-anonymi','Anonymous','Vita Apollonii A (Westermann)','comparative',None),
 (79,1,'apollonius-b','biographi-anonymi','Anonymous','Vita Apollonii B (Westermann)','comparative',None),
 (79,3,'suda-apollonius','suda','Suda','Lexicon: Apollonius excerpt','comparative','suda.lexicon'),
 (80,1,'aratus-a','biographi-anonymi','Anonymous','Vita Arati A (Westermann)','comparative',None),
 (84,2,'aratus-b','biographi-anonymi','Anonymous','Vita Arati B (Westermann)','comparative',None),
 (85,6,'aratus-c','biographi-anonymi','Anonymous','Vita Arati C (Westermann)','comparative',None),
 (87,2,'aratus-d','biographi-anonymi','Anonymous','Vita Arati D (Westermann)','comparative',None),
 (89,1,'suda-aratus','suda','Suda','Lexicon: Aratus excerpt','comparative','suda.lexicon'),
 (89,3,'nicander-life','biographi-anonymi','Anonymous','Genus Nicandri (Westermann)','comparative',None),
 (90,2,'suda-nicander','suda','Suda','Lexicon: Nicander excerpt','comparative','suda.lexicon'),
 (91,2,'oppian-a','biographi-anonymi','Anonymous','Vita Oppiani A (Westermann)','comparative',None),
 (93,5,'oppian-b','biographi-anonymi','Anonymous','Vita Oppiani B (Westermann)','comparative',None),
 (94,5,'suda-oppian','suda','Suda','Lexicon: Oppian excerpt','comparative','suda.lexicon'),
 (95,2,'oppian-manasses','constantinus-manasses','Constantine Manasses','Genus Oppiani (political verses)','primary',None),
 (97,1,'dionysius-life','biographi-anonymi','Anonymous','Vita Dionysii Periegetae (Westermann)','primary',None),
 (97,4,'suda-epic-poets','suda','Suda','Lexicon: epic poet excerpts','comparative','suda.lexicon'),
 (118,1,'pindar-eustathius','eustathius-thessalonicensis','Eustathius of Thessalonica','Prologue to the Pindar commentary (excerpt)','primary',None),
 (124,2,'pindar-anonymous','biographi-anonymi','Anonymous','Vita Pindari (Westermann)','comparative','vitae-pindari-et-varia-de-pindaro.vita-ambrosiana'),
 (126,6,'pindar-thomas','thomas-magister','Thomas Magister','Genus Pindari','comparative','vitae-pindari-et-varia-de-pindaro.vita-thomana-et-hypothesis-olympiorum'),
 (129,2,'suda-lyric-poets','suda','Suda','Lexicon: Pindar and lyric poet excerpts','comparative','suda.lexicon'),
 (145,1,'aeschylus-life','biographi-anonymi','Anonymous','Vita Aeschyli (Westermann)','comparative',None),
 (153,26,'suda-aeschylus','suda','Suda','Lexicon: Aeschylus excerpt','comparative','suda.lexicon'),
 (154,2,'sophocles-life','biographi-anonymi','Anonymous','Vita Sophoclis (Westermann)','primary',None),
 (160,12,'suda-sophocles','suda','Suda','Lexicon: Sophocles excerpt','comparative','suda.lexicon'),
 (161,7,'euripides-anonymous','biographi-anonymi','Anonymous','Vita Euripidis (anonymous Westermann life)','comparative','scholia-in-euripidem.vitae-euripidis'),
 (167,1,'euripides-thomas','thomas-magister','Thomas Magister','Synopsis vitae Euripidis','comparative','scholia-in-euripidem.vitae-euripidis'),
 (169,1,'euripides-moschopulus','manuel-moschopulus','Manuel Moschopulus','Synopsis vitae Euripidis','comparative','scholia-in-euripidem.vitae-euripidis'),
 (170,2,'lycophron-tzetzes','joannes-tzetzes','John Tzetzes','De genere vita et scriptis Lycophronis (excerpt)','primary',None),
 (171,2,'suda-tragic-poets','suda','Suda','Lexicon: Lycophron and tragic poet excerpts','comparative','suda.lexicon'),
 (183,1,'aristophanes-anonymous','biographi-anonymi','Anonymous','Vita Aristophanis (Westermann anonymous life)','primary',None),
 (187,1,'aristophanes-thomas','thomas-magister','Thomas Magister','Synopsis vitae Aristophanis','primary',None),
 (188,3,'suda-aristophanes','suda','Suda','Lexicon: Aristophanes excerpt','comparative','suda.lexicon'),
 (189,2,'de-comoedia','biographi-anonymi','Anonymous','De comoedia (Westermann)','comparative',None),
 (192,5,'suda-comic-poets','suda','Suda','Lexicon: comic poet excerpts','comparative','suda.lexicon'),
 (213,1,'theocritus-life','biographi-anonymi','Anonymous','Genus Theocriti (Westermann)','comparative',None),
 (213,6,'suda-theocritus-moschus','suda','Suda','Lexicon: Theocritus and Moschus excerpts','comparative','suda.lexicon'),
 (214,1,'marcellinus-thucydides','marcellinus','Marcellinus','Vita Thucydidis','primary',None),
 (228,1,'thucydides-anonymous','biographi-anonymi','Anonymous','Vita Thucydidis (Westermann anonymous life)','primary',None),
 (231,11,'suda-thucydides','suda','Suda','Lexicon: Thucydides excerpt','comparative','suda.lexicon'),
 (232,2,'photius-theopompus','photius','Photius','Bibliotheca codex 176: Theopompus (excerpt)','comparative','photius.bibliotheca'),
 (234,2,'suda-historians','suda','Suda','Lexicon: Theopompus and historian excerpts','comparative','suda.lexicon'),
 (258,1,'antiphon-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Antiphontis (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (263,2,'antiphon-anonymous','biographi-anonymi','Anonymous','Genus Antiphontis (Westermann)','primary',None),
 (264,7,'suda-antiphon','suda','Suda','Lexicon: Antiphon excerpt','comparative','suda.lexicon'),
 (264,12,'antiphon-eudocia','eudocia-printed-ionia','Eudocia (Ionia attribution; personal identity uncertain)','Ionia: Antiphon excerpt','primary',None),
 (265,2,'andocides-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Andocidis (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (267,2,'suda-andocides','suda','Suda','Lexicon: Andocides excerpt','comparative','suda.lexicon'),
 (268,2,'lysias-dionysius','dionysius-halicarnassensis-history','Dionysius of Halicarnassus','De Lysia (biographical excerpt)','comparative','dionysius-halicarnassensis-history.de-lysia'),
 (269,1,'lysias-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Lysiae (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (272,13,'suda-lysias','suda','Suda','Lexicon: Lysias excerpt','comparative','suda.lexicon'),
 (273,2,'isocrates-dionysius','dionysius-halicarnassensis-history','Dionysius of Halicarnassus','De Isocrate (biographical excerpt)','comparative','dionysius-halicarnassensis-history.de-isocrate'),
 (274,2,'isocrates-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Isocratis (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (281,18,'isocrates-anonymous','biographi-anonymi','Anonymous','Vita Isocratis (Westermann anonymous life)','comparative',None),
 (287,2,'suda-isocrates','suda','Suda','Lexicon: Isocrates excerpt','comparative','suda.lexicon'),
 (288,1,'isaeus-dionysius','dionysius-halicarnassensis-history','Dionysius of Halicarnassus','De Isaeo (biographical excerpt)','comparative','dionysius-halicarnassensis-history.de-isaeo'),
 (288,4,'isaeus-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Isaei (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (289,2,'isaeus-anonymous','biographi-anonymi','Anonymous','Genus Isaei (Westermann)','primary',None),
 (290,2,'suda-isaeus','suda','Suda','Lexicon: Isaeus excerpt','comparative','suda.lexicon'),
 (290,4,'aeschines-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Aeschinis (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (293,2,'aeschines-apollonius','apollonius-biography','Apollonius (printed attribution)','De Aeschine oratore','comparative',None),
 (296,11,'aeschines-anonymous','biographi-anonymi','Anonymous','Vita Aeschinis (Westermann anonymous life)','comparative',None),
 (297,2,'suda-aeschines','suda','Suda','Lexicon: Aeschines excerpt','comparative','suda.lexicon'),
 (298,2,'lycurgus-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Lycurgi (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (308,2,'suda-lycurgus','suda','Suda','Lexicon: Lycurgus excerpt','comparative','suda.lexicon'),
 (309,1,'demosthenes-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Demosthenis (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (321,2,'demosthenes-libanius','libanius','Libanius','Vita Demosthenis (letter to Montius and biography)','primary',None),
 (325,2,'demosthenes-zosimus','zosimus-ascalonita','Zosimus of Ascalon','Vita Demosthenis','comparative',None),
 (330,5,'demosthenes-anonymous','biographi-anonymi','Anonymous','Vita Demosthenis (Westermann anonymous life)','comparative',None),
 (337,2,'suda-demosthenes','suda','Suda','Lexicon: Demosthenes excerpt','comparative','suda.lexicon'),
 (340,3,'hyperides-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Hyperidis (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (343,2,'suda-hyperides','suda','Suda','Lexicon: Hyperides excerpt','comparative','suda.lexicon'),
 (344,6,'dinarchus-dionysius','dionysius-halicarnassensis-history','Dionysius of Halicarnassus','De Dinarcho (biographical excerpt)','comparative','dionysius-halicarnassensis-history.de-dinarcho'),
 (349,2,'dinarchus-plutarch','pseudo-plutarch','Pseudo-Plutarch','Vita Dinarchi (Lives of the Ten Orators excerpt)','comparative','plutarchus.vitae-decem-oratorum-sp-832b-852e'),
 (350,2,'suda-dinarchus','suda','Suda','Lexicon: Dinarchus excerpt','comparative','suda.lexicon'),
 (350,4,'aristides-anonymous','biographi-anonymi','Anonymous','Vita Aristidis (Westermann)','primary',None),
 (355,2,'suda-rhetors','suda','Suda','Lexicon: Aristides and rhetor and sophist excerpts','comparative','suda.lexicon'),
 (387,2,'suda-grammarians','suda','Suda','Lexicon: grammarian excerpts','comparative','suda.lexicon'),
 (410,1,'plato-olympiodorus','olympiodorus-philosophy','Olympiodorus (printed attribution)','Vita Platonis (Westermann excerpt)','primary',None),
 (416,6,'plato-anonymous','biographi-anonymi','Anonymous','Vita Platonis (Westermann anonymous life)','primary',None),
 (424,2,'suda-plato','suda','Suda','Lexicon: Plato excerpt','comparative','suda.lexicon'),
 (425,2,'aristotle-dionysius','dionysius-halicarnassensis-history','Dionysius of Halicarnassus','Epistula ad Ammaeum I: Aristotle excerpt','comparative','dionysius-halicarnassensis-history.ad-ammaeum'),
 (426,2,'aristotle-ammonius','pseudo-ammonius','Ammonius (bracketed printed attribution)','Vita Aristotelis (Westermann bracketed Ammonius life)','primary',None),
 (429,2,'aristotle-anonymous','biographi-anonymi','Anonymous','Vita Aristotelis et scripta (Westermann)','primary',None),
 (433,5,'suda-philosophers','suda','Suda','Lexicon: philosopher excerpts','comparative','suda.lexicon'),
 (477,1,'hippocrates-soranus','soranus','Soranus (bracketed printed attribution)','Vita Hippocratis','comparative','soranus.vita-hippocratis'),
 (481,22,'suda-physicians','suda','Suda','Lexicon: Hippocrates and physician excerpts','comparative','suda.lexicon'),
)

# Apparatus rows have been checked against their transcribed reference format.
# On mixed pages this is a row boundary, never an all-Greek page permission.
# The exact page/row values are emitted into source-review.json and validated
# against the pinned input, so an upstream extraction change cannot move them.
APPARATUS_STARTS = {29: 4, 30: 2, 31: 2, 34: 29, 35: 4, 37: 28, 38: 29, 39: 8, 40: 2, 41: 4, 42: 31, 44: 23, 45: 24, 46: 23, 48: 4, 50: 29, 52: 25, 53: 28, 55: 18, 56: 20, 57: 8, 58: 23, 60: 2, 61: 24, 66: 28, 67: 26, 69: 30, 71: 30, 73: 30, 77: 25, 78: 5, 79: 5, 81: 29, 86: 21, 87: 5, 88: 2, 91: 5, 92: 14, 93: 26, 94: 7, 96: 30, 97: 10, 102: 21, 104: 22, 107: 12, 109: 6, 112: 2, 113: 4, 115: 8, 116: 24, 123: 29, 124: 4, 127: 2, 128: 2, 129: 4, 130: 20, 132: 4, 134: 3, 136: 23, 141: 29, 143: 26, 147: 20, 148: 19, 153: 28, 158: 2, 159: 20, 160: 20, 161: 19, 162: 20, 163: 5, 164: 28, 165: 21, 167: 3, 168: 5, 173: 26, 174: 21, 181: 27, 182: 4, 183: 3, 184: 2, 185: 2, 186: 21, 187: 3, 188: 5, 195: 23, 197: 20, 202: 19, 203: 24, 211: 7, 213: 10, 214: 6, 216: 2, 220: 26, 225: 2, 231: 18, 233: 2, 236: 25, 238: 8, 247: 9, 250: 8, 251: 8, 254: 26, 255: 30, 257: 22, 258: 16, 262: 2, 263: 4, 266: 2, 268: 5, 270: 24, 271: 26, 272: 18, 274: 4, 275: 2, 276: 2, 279: 6, 281: 24, 282: 33, 283: 2, 285: 35, 290: 6, 294: 2, 295: 2, 296: 28, 309: 4, 310: 2, 318: 25, 319: 2, 321: 4, 324: 2, 325: 4, 327: 2, 328: 32, 329: 2, 331: 30, 333: 2, 334: 2, 337: 4, 338: 3, 339: 2, 340: 27, 341: 2, 343: 5, 345: 2, 348: 2, 349: 4, 353: 4, 355: 4, 356: 31, 357: 15, 358: 31, 360: 30, 362: 25, 364: 11, 365: 29, 367: 26, 369: 29, 372: 6, 373: 30, 374: 31, 378: 28, 385: 28, 389: 5, 391: 8, 392: 29, 394: 31, 395: 28, 399: 3, 400: 6, 401: 29, 406: 31, 407: 4, 408: 30, 411: 31, 412: 31, 414: 34, 421: 29, 432: 33, 433: 27, 434: 28, 436: 4, 444: 6, 447: 10, 456: 28, 457: 6, 460: 32, 461: 32, 463: 6, 464: 28, 468: 9, 470: 2, 473: 28, 474: 32, 476: 6, 481: 31, 482: 2, 483: 9, 487: 25, 488: 3}

APPARATUS_STARTS.update({119:28,138:25,193:24,271:20,272:17,278:22})

# One raw paragraph interleaves the current work and a prior work's apparatus;
# another inserts apparatus after a small body fragment before resuming body.
INLINE_PARTITIONS = {
 'marcellinus_westermann_0187.2': ('ὑποκριτῶν ἐπτάκις', 'apparatus', 'Small-type continuation of anonymous Aristophanes-life apparatus; the Thomas text ends with ἀπαντα on this page and resumes on PDF188.'),
 'marcellinus_westermann_0451.1': ('  ||', 'apparatus', 'Apparatus inserted inside first extracted paragraph; historical Suda body resumes in the next paragraph.'),
}


def sha(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=1)+'\n').encode()
def coordinate(locus):
 m=re.fullmatch(r'marcellinus_westermann_(\d{4})\.(\d+)',locus)
 if not m: raise ValueError('Unexpected Westermann source locus: '+locus)
 return tuple(map(int,m.groups()))


def original_rows(root=ROOT):
 root=Path(root)
 for name in (ARCHIVE_PATH,ORIGINAL_PATH):
  p=root/name
  if p.exists() and sha(p.read_bytes())==ORIGINAL_SHA256:
   rows=[json.loads(line) for line in p.read_bytes().splitlines()]
   if len(rows)!=7013 or len({r['locus'] for r in rows})!=7013:
    raise ValueError('Westermann original row accounting changed')
   return rows
 raise ValueError('Pinned Westermann original rows missing or changed')


def work_definitions():
 result={}
 for position,(page,row,key,author,author_name,title,admission,target) in enumerate(UNITS):
  slug='marcellinus.vita-thucydidis' if key=='marcellinus-thucydides' else author+'.'+key+'-westermann'
  result[key]={'slug':slug,'author':author,'author_name':author_name,'title':title,
   'admission':admission,'source_scope':{'first_pdf_page':page,'first_original_locus':f'marcellinus_westermann_{page:04d}.{row}',
       'printed_page':page-28,'source_review':REVIEW_PATH},
   'attribution_qualification':'Printed attribution retained; no author is inferred from the biography subject.',
   'evidence':[f'{OUTPUT}/source-evidence/page-{page:04d}.jpg',f'{OUTPUT}/source-evidence/page-0489.jpg', f'{OUTPUT}/source-evidence/page-0494.jpg', f'{OUTPUT}/source-evidence/page-0496.jpg', f'{OUTPUT}/source-evidence/page-0498.jpg']}
  next_start=UNITS[position+1][:2] if position+1<len(UNITS) else (489,1)
  result[key]['source_scope']['next_original_locus']=f'marcellinus_westermann_{next_start[0]:04d}.{next_start[1]}'
  result[key]['source_scope']['last_pdf_page']=next_start[0] if next_start[1]>1 else next_start[0]-1
  if target:result[key]['canonical_target']=target
  related={
   'nicander-life':('scholia-in-nicandrum.scholia-et-glossae-in-nicandri-theriaca-scholia-vetera-et',['0']),
   'oppian-a':('scholia-in-oppianum.scholia-et-glossae-in-cynegetica-scholia-vetera-et-recentiora',['scholia_oppianum_bussemaker_didot_0265.2','scholia_oppianum_bussemaker_didot_0265.28']),
   'oppian-b':('scholia-in-oppianum.scholia-et-glossae-in-cynegetica-scholia-vetera-et-recentiora',['scholia_oppianum_bussemaker_didot_0265.2','scholia_oppianum_bussemaker_didot_0265.28']),
   'aeschylus-life':('scholia-in-aeschylum.scholia-in-aeschylum-scholia-vetera',['scholia_aeschylum_depauw_stanley_0030.1','scholia_aeschylum_depauw_stanley_0034.1','scholia_aeschylum_depauw_stanley_0034.2']),
   'de-comoedia':('kaibel-cgf-1899.volume-witness-r',['rhinthon_kaibel_cgf_1899_0029.4']),
   'theocritus-life':('scholia-in-theocritum.scholia-vetera-et-recentiora',['scholia_oppianum_bussemaker_didot_0023.2']),
   'isocrates-anonymous':('scholia-in-isocratem.scholia-in-isocratem-scholia-vetera',[]),
   'aeschines-apollonius':('scholia-in-aeschinem.scholia-in-aeschinem-scholia-vetera',[]),
   'aeschines-anonymous':('scholia-in-aeschinem.scholia-in-aeschinem-scholia-vetera',[]),
   'demosthenes-zosimus':('scholia-in-demosthenem.scholia-demosthenem-dindorf-v8',[]),
   'demosthenes-anonymous':('scholia-in-demosthenem.scholia-demosthenem-dindorf-v8',[]),
  }
  if key in related:
   work,loci=related[key]
   result[key]['related_existing_primary']=work
   result[key]['related_primary_loci']=loci
   result[key]['admission_reason']='The historical life or parallel recension is already embedded in this served primary. Preserve this source-specific reading outside additional primary counts; the containing commentary is not reassigned as the biography Work.'
  if key in ('apollonius-a','apollonius-b','aratus-a','aratus-b','aratus-c','aratus-d','oppian-a','oppian-b'):
   family='apollonius-prose-lives' if key.startswith('apollonius') else 'aratus-prose-lives' if key.startswith('aratus') else 'oppian-prose-lives'
   result[key]['parallel_recension_family']=family
   result[key]['admission_reason']='Unaligned parallel prose recensions are preserved as distinct source readings outside additional primary counts. No preferred reading is chosen and the whole family is not counted as independent historical occurrences.'
  if key=='photius-theopompus':result[key]['related_primary_loci']=['photius_bekker1824_0132.1','photius_bekker1824_0133.1']
  if key=='aristotle-dionysius':result[key]['related_primary_loci']=['5']
  if key=='antiphon-eudocia':result[key]['attribution_qualification']='The print attributes this excerpt to the Ionia of Eudocia. Personal identity and date are left unspecified; it is not assigned to the fifth-century Eudocia Augusta.'
  if key in ('euripides-anonymous','euripides-thomas','euripides-moschopulus'):
   result[key]['related_existing_primary']='scholia-in-euripidem.vitae-euripidis'
   result[key].pop('canonical_target',None)
 return result


_STARTS=[(u[0],u[1]) for u in UNITS]
_KEYS=[u[2] for u in UNITS]
_UNIT_HEADINGS=set(_STARTS)
_UNIT_HEADINGS.update((page,row) for page,values in {
29:[1,2],61:[20,21],73:[20,21],78:[2,3],91:[2,3],97:[1,2,4,5],
118:[1,2,3,4],131:[1,2],145:[1,2],154:[2,3],161:[7,8],170:[2,3],
192:[5,6],213:[1,2,6],214:[1,2,3,4],232:[2,3],235:[2,3],258:[1,2,3],
265:[2,3],268:[2,3],273:[2,3],288:[1,2],298:[2,3],309:[1,2],340:[3,4],
344:[6,7],356:[1,2],387:[2,3],410:[1,2,3],425:[2,3],433:[5,6],477:[1,2],
483:[6,7]}.items() for row in values)

def _is_heading(text):
 letters=[c for c in text if c.isalpha()]
 return bool(letters) and all(c.upper()==c for c in letters) or text in ('ΑΛΛΩΝ','ΑΛΑΩΝ') or bool(re.fullmatch(r'ἐκ τῶν Σουίδα, κατὰ στοιχεῖον\.',text))


def partitions(row):
 """Ordered exact character spans; no text edits or normalization are allowed."""
 text=row['text'];page,number=coordinate(row['locus'])
 if page<29:return [{'start':0,'end':len(text),'work':None,'role':'editorial','evidence':'Title/front matter and modern corrigenda; source PDF5 and28.'}]
 if page>=489:return [{'start':0,'end':len(text),'work':None,'role':'index','evidence':'Modern index vitarum/scriptorum/nominum; source PDF489–516.'}]
 i=bisect.bisect_right(_STARTS,(page,number))-1
 if i<0:raise ValueError('Historical page precedes the first source unit')
 key=_KEYS[i]
 evidence=f'{OUTPUT}/source-evidence/page-{page:04d}.jpg'
 if row['locus'] in INLINE_PARTITIONS:
  marker,role,reason=INLINE_PARTITIONS[row['locus']]
  if text.count(marker)!=1:raise ValueError('Westermann inline partition anchor changed')
  cut=text.index(marker)
  return [{'start':0,'end':cut,'work':key,'role':'historical-body','evidence':evidence},
          {'start':cut,'end':len(text),'work':None,'role':role,'evidence':evidence+'; '+reason}]
 if page in APPARATUS_STARTS and number>=APPARATUS_STARTS[page]:
  return [{'start':0,'end':len(text),'work':None,'role':'apparatus','evidence':evidence+'; small-type modern critical notes, including quoted historical variants.'}]
 role='heading' if (page,number) in _UNIT_HEADINGS or _is_heading(text) else 'historical-body'
 return [{'start':0,'end':len(text),'work':key,'role':role,'evidence':evidence}]


def source_review(root=ROOT):
 rows=original_rows(root)
 by_page={}
 for row in rows:by_page.setdefault(coordinate(row['locus'])[0],[]).append(row)
 totals={};page_inventory=[]
 for page in range(5,517):
  items=[]
  for row in by_page.get(page,[]):
   spans=partitions(row)
   if ''.join(row['text'][s['start']:s['end']] for s in spans)!=row['text']:
    raise ValueError('Westermann partition lost source characters')
   for s in spans:
    totals[s['role']]=totals.get(s['role'],0)+len(re.findall(r'[\u0370-\u03ff\u1f00-\u1fff]+',row['text'][s['start']:s['end']]))
   items.append({'locus':row['locus'],'row_sha256':sha(encoded(row)),
    'text_sha256':sha(row['text'].encode()),'partitions':spans})
  page_inventory.append({'source_pdf_page':page,'printed_page':page-28 if 29<=page<=488 else None,
   'original_rows':len(items),'rows':items})
 return {'schema_version':1,'reviewed_at':REVIEWED_AT,'source':SOURCE,
  'original':{'path':ORIGINAL_PATH,'sha256':ORIGINAL_SHA256,'rows':len(rows)},
  'qualification':'Complete accounting of the existing extraction, not a new transcription. Modern editorial notes retain their Greek quotations as apparatus. Historical text remains in primary or comparative witnesses by source identity and deduplication, and OCR spelling is not silently changed.',
  'contents':{'source_pdf_pages':list(range(489,499)),'books':[
   {'book':i,'title':t,'pdf_pages':[a,b],'printed_pages':[a-28,b-28]} for i,t,a,b in [
    (1,'Epic poets',29,117),(2,'Lyric poets',118,144),(3,'Tragic poets',145,182),(4,'Comic and bucolic poets',183,213),
    (5,'Historians',214,257),(6,'Orators, sophists, and grammarians',258,409),(7,'Philosophers',410,476),(8,'Physicians',477,488)]]},
  'works':work_definitions(),'apparatus_starts':APPARATUS_STARTS,'inline_partitions':INLINE_PARTITIONS,
  'role_greek_tokens':totals,'count_basis':'Greek-script regex chunks in the original row text; release lexical eligibility is accounted independently by the corpus projection.',
  'parallel_recension_families':{
   'apollonius-prose-lives':{'units':['apollonius-a','apollonius-b'],'status':'comparative-unaligned'},
   'aratus-prose-lives':{'units':['aratus-a','aratus-b','aratus-c','aratus-d'],'status':'comparative-unaligned'},
   'oppian-prose-lives':{'units':['oppian-a','oppian-b'],'status':'comparative-to-served-life-and-unaligned'},
  },
  'admission_qualification':'Parallel Apollonius, Aratus, and Oppian prose recensions remain comparative readings until occurrence-level alignment can preserve shared text and all variants without duplicate lexical counts. The bounded scope repair neither selects one arbitrarily nor counts all recensions as independent works. Distinct attributed compositions, including Manasses political verses, retain their printed identity.',
  'remaining_review_condition':'New independently supported work identity or occurrence-level alignment of a parallel family can authorize a later admission review. Source attribution uncertainty, including the personal identity behind the Ionia attribution to Eudocia and the bracketed Ammonius attribution, is explicit rather than silently resolved.',
  'pages':page_inventory}
