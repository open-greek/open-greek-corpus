#!/usr/bin/env python3
"""Reproduce the exact source-reviewed page255 body authority, without corpus edits."""
import gzip
import hashlib
import json
import argparse
from pathlib import Path

from repair_photius_index import ROOT as DEFAULT_ROOT, input_bytes

parser = argparse.ArgumentParser(description='Prepare the bounded, scan-reviewed Photius physical page255 missing-body authority.')
parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
mode = parser.add_mutually_exclusive_group()
mode.add_argument('--write', action='store_true')
mode.add_argument('--check', action='store_true')
args = parser.parse_args()
ROOT = args.root

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

source_path = ROOT / 'data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz'
source_raw = source_path.read_bytes()
document = json.loads(gzip.decompress(source_raw))
section = next(s for s in document['sections'] if s['label'] == 'Page s532')
full = '\n'.join(b['text'] for b in section['blocks'])
start = full.index('ἡρμήνευεν ἐξουσίαν')
digital = full[start:]
manual = 'ἡρμήνευεν ἐξουσίαν· εἰπὼν δὲ „ἐβασίλευσε“ τὴν διὰ σαρκὸς αὐτοῦ οἰκονομίαν λέγει, δι’ ἧς ἡ φύσις ἡμῶν τὴν ἐπικράτειαν τοῦ διαβόλου, τῆς ἁμαρτίας, τοῦ θανάτου ἀποσεισαμένη, ἐπέγνω πλάστην τὸν ὡς ἀληθῶς βασιλέα, τὸν χορηγὸν τῆς ἀφθαρσίας, τῆς ἀναστάσεως. εὐαγγελίζεται τοίνυν ὁ Δαβὶδ τοῖς ὑπὸ τῆς ἁμαρτίας, ὑπὸ τοῦ θανάτου, ὑπὸ τοῦ διαβόλου πάλαι βασιλευομένοις, „ὅτι ὁ ζυγὸς ἐκεῖνος συντέτριπται, τὸ κράτος λέλυται, καὶ βασιλεύει πάντων ὁ κύριος. ὡς καὶ αὐτὸς μετὰ τὴν ἀνάστασιν ἔφη, „ἐδόθη μοι πᾶσα ἐξουσία ἐν οὐρανῷ καὶ ἐπὶ γῆς.“ πρὶν δὲ ἐβασίλευεν ἡμῶν ὁ θάνατος'
row = next(json.loads(line) for line in input_bytes(ROOT).decode().splitlines()
           if json.loads(line)['locus'] == 'helladius_chrestomathia_photius_bekker_v2_0255.6')
witnesses = [
    {'id': 'manual-scan-review', 'vote_group': 'manual-scan-review',
     'text': manual, 'artifact_sha256': sha(manual.encode()),
     'evidence': 'Direct reading of the high-resolution printed source region, physical PDF255/printed520; this is a bounded transcription, not a full-page proofread.'},
    {'id': 'source-library-local002', 'vote_group': 'source-library-local002',
     'text': digital, 'artifact_sha256': sha(encode(section)), 'license': 'CC-BY-SA-4.0',
     'source_url': 'https://gitlab.lisn.upsaclay.fr/api/v4/projects/1918/packages/generic/corpus/1/works/tlg4040/tlg001/local002.json.gz',
     'source_file_sha256': sha(source_raw), 'source_section': section['id']},
]
# The print has no comma after ἔφη; preserve its exact punctuation before voting.
manual = manual.replace('ἔφη, „ἐδόθη', 'ἔφη „ἐδόθη')
witnesses[0]['text'] = manual
witnesses[0]['artifact_sha256'] = sha(manual.encode())
result = {
    'schema_version': 1, 'kind': 'source-reviewed-missing-body-candidate',
    'work': 'photius.bibliotheca', 'locus': row['locus'], 'original_row': row,
    'row_sha256': sha(encode(row)),
    'replacement_scope': {
        'start': 162, 'end': len(row['text']), 'original_text': row['text'][162:],
        'policy': 'Retain every original prefix codepoint. Replace only the unprinted repeated tail with the explicitly bounded merged independent readings; preserve every disagreement. The historical witness abstains on missing body rather than voting for omission.'},
    'source': {
        'url': 'https://archive.org/download/bub_gb_NsiGxvHyQY0C/bub_gb_NsiGxvHyQY0C.pdf',
        'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb',
        'scan_page': 255, 'printed_page': 520, 'region': [.58, .522, .955, .729]},
    'source_library_window': {
        'path': 'data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz',
        'sha256': sha(source_raw), 'section': section['id'], 'section_label': section['label'],
        'start': start, 'end': len(full), 'original_text': digital,
        'page_label_qualification': 'Source Library label s532 maps by exact printed text to physical PDF255/printed520; label s520 is a different passage.'},
    'reviewed_at': '2026-10-18T15:12:02+00:00',
    'source_evidence': 'The old row stops after αὐτοῦ and repeats ἡμῖν six times plus final partial ἡμ. The source instead prints ἡρμήνευεν ἐξουσίαν followed by the remainder of the same right-column paragraph to πρὶν δὲ ἐβασίλευεν ἡμῶν ὁ θάνατος at the page bottom. The appended body ends before the apparatus and continues on the following page. Manual reading and Source Library agree on the bounded passage with local spelling/abbreviation/mark differences retained.',
    'witnesses': witnesses,
}
following = next(json.loads(line) for line in input_bytes(ROOT).decode().splitlines()
                 if json.loads(line)['locus'] == 'helladius_chrestomathia_photius_bekker_v2_0256.1')
result['following_body_anchor'] = {'locus': following['locus'], 'row_sha256': sha(encode(following)),
                                   'text_prefix': following['text'][:150],
                                   'evidence': 'The missing paragraph ends at the physical page255 main-column boundary; page256 resumes the sentence. No text from the following row is included in the correction.'}
result['transcription_convention'] = 'The manually source-read witness expands printed Greek ligatures and abbreviations, including the printed καί sign and τοῦ ligatures, to their full Greek readings. Source Library retains its original independent spelling and abbreviation readings. Every disagreement remains a consensus alternative; the manual transcription does not silently replace the digital reading.'
result['source_image'] = {'crop_sha256': 'ed8844d5e319ef12d391f85570d5eefcdcf5fb0739f9bdb80ba15a087ff38cd9', 'render_sha256': '3b45cbd1b2543c4de67e532c252b36c7d071acca2ad943e3ced9dd272949d191', 'pixel_bbox': [2242, 2610, 3692, 3645], 'render_dimensions': [3867, 5000], 'render_recipe': 'Render only physical PDF page255 with pdftoppm -scale-to 5000 -png -singlefile, then take the exact pixel rectangle.'}
report = json.loads((ROOT / 'data/corpus_changes/photius-bekker-coverage/coverage.json').read_text())
credit = report['source_library']
if credit['sha256'] != sha(source_raw) or credit['license']['url'] != 'https://creativecommons.org/licenses/by-sa/4.0/':
    raise ValueError('Reviewed Source Library credit no longer matches the retained source')
result['source_library_credit'] = {key: credit[key] for key in ('edition', 'url', 'sha256', 'license', 'rights', 'api_notice_url', 'api_notice_checked_date', 'separate_api_notice')}
result['source_library_credit']['source_citation'] = document['sourceCitation']
result['source_library_credit']['attribution'] = document['origin']['label']
if sha(source_raw) != '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291':
    raise ValueError('The original digital artifact changed')
if result['row_sha256'] != 'a6b2d707fe79fd4c7c5ffcb1657c735ef82e57df956d75fa6bfebc8635c4f823':
    raise ValueError('The original page255 row changed')
if (start, len(full)) != (3640, 4189):
    raise ValueError('The reviewed digital window changed')
raw = (json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode()
out = ROOT / 'data/ingest_reviews/photius-bekker-body-corrections.json'
if args.write:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
elif args.check and (not out.exists() or out.read_bytes() != raw):
    parser.exit(1, 'Photius bounded body authority drift\n')
print(json.dumps({'path': str(out.relative_to(ROOT)), 'sha256': sha(raw), 'corrected_rows': 1}))
