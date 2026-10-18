#!/usr/bin/env python3
"""Prepare the separately reviewed page7 missing-body authority without corpus edits."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from repair_photius_index import ROOT, input_bytes

OUT = Path('data/ingest_reviews/photius-bekker-body-page0007.json')
SOURCE_LIBRARY = Path('data/corpus_changes/photius-bekker-coverage/source-library-local002.json.gz')
SOURCE_LIBRARY_SHA = '114949cd26dc366ed6d0a084ad1978b197175ced3e79b05301ac03e75643b291'
ROW_SHA = '3622531a16e3d29ec02027c52611d2b0399ff20a159400c4787aaa7f4202dbf5'
MANUAL = 'συνεκφωνεῖσθαί τε καὶ συνεξακούεσθαι. οὐ γάρ ἐστιν οὗτος ὁ πολὺς ἐν διανοίᾳ οὐ τοῖς ῥήμασι καὶ τοῖς ὀνόμασιν ἀεὶ τὸν νοῦν καταπιστεύων, τοῖς δὲ νοήμασι καὶ τὰ ῥήματα καὶ τὰ ὀνόματα συμμεταφέρων τε καὶ μεταρμοζόμενος. ἄκουε γὰρ τί μὲν ἐν τῷ πρώτῳ τῶν Θησαυρῶν λέγει, τί δὲ ἐν ταῖς πρὸς Σάκενσον ἐπιστολαῖς. ἐν ἐκείνῳ μὲν γάρ φησι τὸν θεὸν λόγον, ὑπὲρ ἡμῶν ἀρχιερέα γεγονότα, ὥσπερ τινὰ ποδήρη τὸν ἐκ Μαρίας ἄνθρωπον ἢ τὸν ναὸν ἀναλαβεῖν· ἐν ταύταις δὲ „οὐκοῦν γέγονέ“ φησιν „ἄνθρωπος, οὐκ ἄνθρωπον ἀνελάβετο.“ πῶς οὖν ἐκεῖ μὲν ἄνθρωπον οὐκ ἀνέλαβεν, ἐνταῦθα δὲ ἀνέλαβεν; αὐτὸς ἑαυτὸν ἑρμηνεύει· ἐπάγει γὰρ „ὡς Νεστορίῳ δοκεῖ.“ τοῦτο δὲ τί ἐστιν ἄλλο ἢ μὴ τοῖς ῥήμασι καταπιστεύειν τὸν νοῦν, τὰ δὲ ῥήματα τῇ διανοίᾳ ζυγοστατεῖν; ὥστε εἴ τις λέγων εὑρεθείη τὸν θεὸν λόγον ἄνθρωπον μὴ ἀναλαβεῖν, ἐκ τῆς παρούσης ἀντικρὺς διδασκαλίας οὐχ ἁπλῶς αὐτὸν ἀπείργειν τοῦτο μὴ λέγειν (πῶς γὰρ ἂν ἑτέρους κωλύσειεν, ὅπερ αὐτὸς λαμπρῶς διαπράττοιτο;) ἀλλὰ μὴ λέγειν οὕτως ὡς Νεστορίῳ δοκεῖ. ὁ μέντοι γε κλεινὸς Εὐλόγιος τὴν μίαν φύσιν τοῦ λόγου σεσαρκωμένην διευκρινῶν καὶ τοῦτό φησιν, ὡς εἴ τις τὸν νοῦν τοῦ διδασκάλου ἐξακριβώσασθαι βληθῇ,'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def build(root=ROOT):
    source_raw = (root / SOURCE_LIBRARY).read_bytes()
    if sha(source_raw) != SOURCE_LIBRARY_SHA:
        raise ValueError('Reviewed digital source changed')
    document = json.loads(gzip.decompress(source_raw))
    section = next(s for s in document['sections'] if s['label'] == 'Page s284')
    full = '\n'.join(b['text'] for b in section['blocks'])
    start = full.index('συνεκφωνεῖσθαί')
    digital = full[start:]
    if (start, len(full)) != (3098, 4223):
        raise ValueError('Reviewed digital body window changed')
    rows = [json.loads(line) for line in input_bytes(root).decode().splitlines()]
    row = next(r for r in rows if r['locus'] == 'helladius_chrestomathia_photius_bekker_v2_0007.5')
    if sha(encode(row)) != ROW_SHA:
        raise ValueError('Reviewed historical page7 row changed')
    if row['text'][981:] != 'συνεχῶς ἐξ ἢ συνεχῶς ἐξ ἢ συνεχῶς ἐξ ἢ συνεχῶς ἐξ':
        raise ValueError('Reviewed unprinted repetition changed')
    following = next(r for r in rows if r['locus'] == 'helladius_chrestomathia_photius_bekker_v2_0008.1')
    coverage = json.loads((root / 'data/corpus_changes/photius-bekker-coverage/coverage.json').read_text())
    credit = coverage['source_library']
    if credit['sha256'] != SOURCE_LIBRARY_SHA or credit['license']['url'] != 'https://creativecommons.org/licenses/by-sa/4.0/':
        raise ValueError('Reviewed source attribution changed')
    source_credit = {key: credit[key] for key in ('edition', 'url', 'sha256', 'license', 'rights', 'api_notice_url', 'api_notice_checked_date', 'separate_api_notice')}
    source_credit.update(source_citation=document['sourceCitation'], attribution=document['origin']['label'])
    return {
        'schema_version': 1, 'kind': 'source-reviewed-missing-body-candidate',
        'work': 'photius.bibliotheca', 'locus': row['locus'], 'original_row': row,
        'row_sha256': ROW_SHA,
        'replacement_scope': {'start': 981, 'end': len(row['text']), 'original_text': row['text'][981:],
            'policy': 'Retain every original prefix codepoint. Replace only the unprinted repeated tail with the explicitly bounded merged independent readings; preserve every disagreement. The historical witness abstains on missing body rather than voting for omission.'},
        'source': {'url': 'https://archive.org/download/bub_gb_NsiGxvHyQY0C/bub_gb_NsiGxvHyQY0C.pdf',
            'sha256': 'fd9c6881b568d80e00997a3bb859b19e4a2833ec12b7956eb09f083934927feb',
            'scan_page': 7, 'printed_page': 272, 'region': [.54, .37, .94, .735]},
        'source_library_window': {'path': SOURCE_LIBRARY.as_posix(), 'sha256': SOURCE_LIBRARY_SHA,
            'section': section['id'], 'section_label': section['label'], 'start': start, 'end': len(full),
            'original_text': digital,
            'page_label_qualification': 'Source Library label s284 maps by exact printed text to legacy physical PDF7/printed272. The label is not the printed page number.'},
        'reviewed_at': '2026-10-18',
        'source_evidence': 'Direct scan review confirms that the body continues after τὸ λοιπὸν with συνεκφωνεῖσθαί τε καὶ συνεξακούεσθαι, then the remainder of this paragraph and the following short paragraph through βληθῇ, at the right-column body bottom. The repeated συνεχῶς ἐξ tail is absent from the print. The apparatus below is excluded. The original prefix retains its historical word errors unchanged. This bounded restoration is not a proofread page.',
        'witnesses': [
            {'id': 'manual-scan-review', 'vote_group': 'manual-scan-review', 'text': MANUAL,
                'artifact_sha256': sha(MANUAL.encode()),
                'evidence': 'Independent direct reading of the enlarged right-column source body, physical PDF7/printed272. Uncertain abbreviation, accent and word readings remain disagreements with the retained digital witness.'},
            {'id': 'source-library-local002', 'vote_group': 'source-library-local002', 'text': digital,
                'artifact_sha256': sha(encode(section)), 'license': 'CC-BY-SA-4.0',
                'source_url': credit['url'], 'source_file_sha256': SOURCE_LIBRARY_SHA,
                'source_section': section['id']}],
        'following_body_anchor': {'locus': following['locus'], 'row_sha256': sha(encode(following)),
            'text_prefix': following['text'][:150],
            'evidence': 'The missing body ends at the physical page7 right-column boundary; page8 continues the same sentence. No page8 text is included.'},
        'transcription_convention': 'The manual witness expands printed Greek ligatures and abbreviations, including the καί sign and τοῦ ligatures, and joins source line-break hyphenation inside this bounded body. The final βληθῇ remains the literal printed abbreviated reading. The witness retains its direct source reading separately from all Source Library spelling, punctuation, capitalization and mark variants. No tied reading is silently preferred.',
        'source_image': {'crop_sha256': '518f2a039b7b4e4242aee7f003df56b2da386bb0b3eda8dbbc199d4e3328b79d',
            'render_recipe': 'Render physical PDF7 with PyMuPDF Matrix(5,5), clip to normalized rectangle [.54,.37,.94,.735]. The crop is a viewing context rather than a word-level segmentation.'},
        'source_library_credit': source_credit,
        'generated_by': 'scripts/prepare_photius_body_page0007.py'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    raw = (json.dumps(build(args.root), ensure_ascii=False, indent=2) + '\n').encode()
    path = args.root / OUT
    if args.write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    elif args.check and path.read_bytes() != raw:
        parser.exit(1, 'Photius bounded page7 authority drift\n')
    print(json.dumps({'path': OUT.as_posix(), 'sha256': sha(raw), 'corrected_rows': 1}))


if __name__ == '__main__':
    main()
