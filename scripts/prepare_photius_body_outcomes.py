#!/usr/bin/env python3
"""Reproduce completed source comparisons of missing-body OCR attempts.

These decisions admit raw witnesses to a qualified vote, not proofread text.
Exact source-confirmed recognition errors abstain without changing raw text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('data/ingest_reviews/photius-bekker-body-outcomes.json')
REVIEWED_AT = '2026-10-18T21:56:02Z'
# Every listed strip was compared with its actual rendered source image and
# both completed predictions. Unlisted strips cannot receive an admission.
NOTES = {
    '0066-left-part01': 'Both readings follow the seven source lines from the opening continuation through the reply to the vine prohibition; word and mark errors remain.',
    '0066-left-part02': 'Both readings follow the seven source lines through the Philostratus passage. The visible first and last split words remain literal; recognition of ligatures is imperfect. The cropped marginal reference introduces a fictitious Greek letter and is explicitly held.',
    '0066-left-part03': 'Both readings follow the nine source lines through the quoted maxim and its following clause. Substantial recognition errors remain, including mixed script in one reading; these are variants, not approved spellings.',
    '0066-left-part04': 'Both readings cover the criticism of Philostratus and the final full-size authorial subsection heading. The small apparatus below the column is outside the crop; the heading is retained despite recognition errors.',
    '0073-right-part01': 'Both readings follow the eight source lines, beginning with the continued-word fragment and ending with the next incomplete clause. The first fragment must not become a complete lexical token. Mixed script in the earlier checkpoint remains raw evidence.',
    '0073-right-part02': 'Both readings follow the eight source lines describing appearance, age, conversation, and upbringing. Marginal numbers are not authorial words; lexical and accent disagreements remain explicit.',
    '0073-right-part03': 'Both readings follow the eight source lines, including the smaller full-size authorial synonym paragraph. The first line prints τύχης; the shared τέχνης recognition is explicitly held.',
    '0073-right-part04': 'Both readings correspond to all six source lines. The earlier checkpoint loses nearly all polytonic marks, while the later checkpoint retains imperfect marked readings. Neither reading is approved as proofread text.',
    '0073-right-part05': 'Both readings follow the final eight body lines through εἰς τὸν Γοργίαν. The scan prints ἑταίροις; both occurrences of the shared ἰταλοῖς recognition are explicitly held. The apparatus lies outside the crop.',
    '0079-left-part01': 'Both readings follow all seventeen printed lines, including the paragraphs on Jacob and the literal divided words. Shared wrong words and ligatures have exact source observations; neither prediction is proofread.',
    '0079-left-part02': 'Both readings correspond to the ten source lines. They insert an article before the misread θεραπεύοντας and share additional wrong words; the source observations hold those exact spans without changing raw text.',
    '0079-left-part03': 'Both readings follow all ten source lines. Printed marginal numbers are distinguished from authorial words; proper names, ligatures, and word readings remain imperfect.',
    '0079-left-part04': 'Both readings follow the three final body lines before the existing right column. The raw mixed script and lexical differences are retained, with no apparatus below the crop.',
    '0090-right-part01': 'Both readings follow all eight source lines from the continued-word suffix. The source fragment remains incomplete, and the marginal reference inside a divided word cannot count as authorial Greek.',
    '0090-right-part02': 'Both readings correspond to the eight printed lines, despite different raw line wrapping. Word and mark substitutions remain; there is no unrelated paragraph, loop, or footer apparatus.',
    '0090-right-part03': 'Both readings follow all nine source lines. The printed κάθοδον is misread differently by the two checkpoints; exact source observations retain the evidence without selecting a word for fluency.',
    '0090-right-part04': 'Both readings correspond to the nine printed lines, including the genuine authorial subsection title and ἐκ τῆς θεωρίας. The title is substantially misread and remains body matter.',
    '0090-right-part05': 'The later checkpoint corresponds to all six printed lines. The earlier checkpoint omits the complete authorial heading Ἐκ αὐτῆς τῆς μελέτης τὸ προοίμιον, so its entire strip abstains as incomplete source coverage. Both raw predictions remain archived. The final divided word and marginal1084 reference cannot supply complete authorial words.',
    '0100-left-part01': 'Both readings follow all eight source lines. Initial ποις continues the previous printed column and stays ineligible as a complete word. Word and mark errors remain explicit.',
    '0100-left-part02': 'Both readings follow all nine source lines. Their Η. before τερον comes from marginal594H, inside the divided πρότερον; it is not an authorial Greek letter. Exact source observations hold the artifact.',
    '0100-left-part03': 'Both readings correspond to all nine source lines through the closing appeal. Lexical, punctuation, and accent disagreements remain imperfect raw readings.',
    '0100-left-part04': 'Both readings correspond to the three printed heading lines, but severely misread their words and names. This heading is legitimate authorial matter, not a running title or footer.',
    '0100-left-part05': 'Both readings follow all thirteen printed lines. The final πολ- is a literal incomplete source word, not authority for a completed form. Neither raw prediction imports the smaller apparatus.',
    '0148-left-part01': 'Both readings follow the six printed lines. The first two include existing148.2 context, held through the unique αὐταῖς τοίνυν boundary. Clipped neighboring-column ink creates extra short raw readings; exact observations hold them without rewriting the prediction.',
    '0148-left-part02': 'Both readings correspond to all ten printed lines, including the genuine square-bracketed phrase. Word, ligature, and mark substitutions remain, without a missing source line or imported footer.',
    '0148-left-part03': 'Both readings follow the final eight printed lines through the complete word ὑπὲρ before the existing right column. Their lexical and accent differences remain raw evidence; no smaller apparatus is imported.',
    '0154-right-part01': 'Both readings follow all ten source lines below preserved154.50. Initial κειτο continues the earlier προ- and cannot count as a complete word. Proper names, ordinary words, and marks remain imperfect.',
    '0154-right-part02': 'Both readings correspond to all eight source lines in order. No authorial block, unrelated paragraph, loop, or footnote is introduced; individual words and marks are not certified.',
    '0154-right-part03': 'Both readings follow all nine printed lines. Their substantial lexical substitutions remain variants; no source line or complete authorial block is omitted.',
    '0154-right-part04': 'Both readings correspond to all ten printed lines through τὴν ὑπὲρ τούτου. The marginal1364 reference is separated from authorial words. Short local corrupt repetitions remain imperfect readings, not an unbounded generation loop.',
    '0189-left-part01': 'Both readings correspond to all nine printed lines from χειμῶνα to the divided περιτι-. Clipped marginal ink corrupts the first word, and other lexical errors remain. Neither output loops or imports footnotes.',
    '0189-left-part02': 'Both readings follow all nine printed lines between the continued θέασι and trailing τρωγλοδύ-. The raw split-word halves, ligatures, and word substitutions remain imperfect evidence.',
    '0189-left-part03': 'Both readings correspond to all eight source lines, including the legitimate καμάρας sentence. Marginal ink fuses with πάντας in the raw text. The final divided οὕ- and its following continuation cannot become separate complete words.',
    '0189-left-part04': 'Both readings follow the six final source lines before existing right-column ταῖς κηδείαις. The opening continuation of οὕτω remains an incomplete fragment despite its raw substitutions. No smaller apparatus is imported.',
}
# Corrections identify rejected model spans and the visible source reading.
# They never replace the retained prediction or manufacture an extra vote.
WRONG_READINGS = {
    '0066-left-part02': [('7Π.', '1017 R.', 'The complete margin prints the reference 1017 R. before ὅτι, also visible on combined scan343. The crop retains only its end; both predictions turn the reference letter into Greek Π. This is marginal reference matter, not an authorial word or subdivision.')],
    '0073-right-part03': [('τέχνης', 'τύχης', 'The first complete source line reads πον τῆς τύχης; both checkpoints substitute τέχνης.')],
    '0073-right-part05': [('ἰταλοῖς', 'ἑταίροις', 'The sixth source line reads Γοργίαν τοῖς ἑταίροις; the two checkpoints share the same wrong word.')],
}
MODEL_WRONG_READINGS = {
    ('0090-right-part01', 'mlx-community/Qwen3.8-27B-8bit'): [
        ('Σηβ]', '578', 'The right edge of the sixth source line contains the small marginal numeric reference578, after the authorial divided ἤπει-. The later checkpoint turns the clipped digits into Greek letters. These are reference matter, not an authorial word.', 'marginal-reference')],
}


def source_observation_tables():
    import photius_body_source_observations as first
    import photius_body_source_observations_remaining as remaining
    return (first, remaining)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def build(root=ROOT):
    from repair_photius_readings import BODY_BATCHES
    from photius_body_vote import CHECKPOINTS
    records, batches, seen = [], [], set()
    tables = source_observation_tables()
    observations, expected_observations, applied_observations = {}, set(), set()
    for table in tables:
        for field, target in (('RECORDS', 'exclusions'), ('ARTIFACTS', 'exclusions'),
                              ('FRAGMENTS', 'source_fragments')):
            for observation in getattr(table, field, ()):
                for span in observation['raw_spans']:
                    identity = (observation['id'], span['model'], observation['observation_id'],
                                target, span['start'], span['end'])
                    if identity in expected_observations:
                        raise ValueError('A source-observation occurrence is repeated')
                    expected_observations.add(identity)
                    observations.setdefault((observation['id'], span['model']), []).append((observation, span, target))
    for batch in BODY_BATCHES:
        request_raw = (root / batch['request']).read_bytes()
        request = json.loads(request_raw)
        jobs = {p['id']: p for p in request['pages']}
        batches.append({'request': batch['request'], 'sha256': sha(request_raw)})
        for path in batch['raw_files']:
            raw = (root / path).read_bytes()
            for table in tables:
                for pin in table.RAW_FILES:
                    if pin['path'] == path and pin.get('sha256') is not None and sha(raw) != pin['sha256']:
                        raise ValueError('A source-observation raw file changed')
            lines = raw.splitlines()
            metadata = json.loads(lines[0])['_meta']
            model = metadata['model']
            if CHECKPOINTS.get(model) != metadata['revision'] or metadata['manifest_sha256'] != sha(request_raw):
                raise ValueError('Outcome review checkpoint or request changed')
            predictions = {json.loads(line)['id']: (json.loads(line), line) for line in lines[1:]}
            if len(predictions) != len(lines) - 1 or set(predictions) != set(jobs):
                raise ValueError('Outcome review requires every completed strip exactly once')
            for identifier in sorted(jobs):
                suffix = identifier.removeprefix('photius-bekker-legacy-')
                if suffix not in NOTES:
                    raise ValueError('No completed source comparison for ' + identifier)
                seen.add(suffix)
                prediction, line = predictions[identifier]
                text = prediction['raw_prediction']
                if not text.strip() or prediction['finish_reason'] != 'stop':
                    raise ValueError('An incomplete prediction cannot be admitted by an outcome review')
                exclusions, fragments = [], []
                rejected = [*WRONG_READINGS.get(suffix, []),
                            *MODEL_WRONG_READINGS.get((suffix, model), [])]
                for original, printed, evidence, *classification in rejected:
                    if text.count(original) != 1:
                        raise ValueError('A reviewed wrong-reading occurrence changed')
                    start = text.index(original)
                    exclusions.append({'start': start, 'end': start + len(original),
                        'original_text': original, 'observed_printed_text': printed,
                        'classification': classification[0] if classification else 'source-confirmed-wrong-reading', 'evidence': evidence,
                        'source_image_sha256': prediction['image_sha256']})
                prediction_sha = sha(json.dumps(prediction, ensure_ascii=False, sort_keys=True,
                                                separators=(',', ':')).encode())
                for observation, span, target in observations.get((identifier, model), []):
                    if (span['revision'] != metadata['revision']
                            or span['prediction_record_sha256'] != prediction_sha
                            or span['text_sha256'] != sha(text.encode())
                            or span['source_image_sha256'] != prediction['image_sha256']
                            or text[span['start']:span['end']] != span['original_text']):
                        raise ValueError('An exact source-observation occurrence changed')
                    applied_observations.add((identifier, model, observation['observation_id'],
                                              target, span['start'], span['end']))
                    destination = fragments if target == 'source_fragments' else exclusions
                    destination.append({key: span[key] for key in ('start', 'end', 'original_text',
                                                                 'source_image_sha256')})
                    destination[-1].update({
                        'observation_id': observation['observation_id'],
                        'observed_printed_text': observation['observed_printed_text'],
                        'classification': observation.get('classification',
                            'source-split-word-fragment' if target == 'source_fragments' else 'source-confirmed-wrong-reading'),
                        'evidence': observation['evidence'],
                        'digital_counterpart': observation.get('digital_counterpart'),
                        'digital_context': observation.get('digital_context')})
                exclusions.sort(key=lambda span: (span['start'], span['end']))
                for left_index, left in enumerate(exclusions):
                    for right in exclusions[left_index + 1:]:
                        if left['end'] <= right['start']:
                            continue
                        container = left if left['start'] <= right['start'] and left['end'] >= right['end'] else right
                        if (container.get('classification') != 'incomplete-source-coverage'
                                or container['start'] != 0 or container['end'] != len(text)):
                            raise ValueError('Source-reviewed outcome exclusions overlap')
                records.append({'id': identifier, 'model': model, 'revision': metadata['revision'],
                    'raw_file': path, 'raw_file_sha256': sha(raw), 'prediction_record_sha256': prediction_sha,
                    'text_sha256': sha(text.encode()), 'image_sha256': prediction['image_sha256'],
                    'reviewed_at': REVIEWED_AT, 'evidence': NOTES[suffix],
                    'decision': 'eligible-as-raw-witness', 'exclusions': exclusions,
                    'source_fragments': sorted(fragments, key=lambda span: (span['start'], span['end']))})
    if seen != set(NOTES):
        raise ValueError('Outcome decisions contain an unknown or omitted strip')
    if applied_observations != expected_observations:
        raise ValueError('A source-observation occurrence has no completed prediction')
    return {'schema_version': 1, 'work': 'photius.bibliotheca', 'reviewed_at': REVIEWED_AT,
        'kind': 'completed-source-comparison-of-raw-body-witnesses', 'batches': batches,
        'source_observation_tables': [
            {'path': 'scripts/' + Path(table.__file__).name,
             'sha256': sha(Path(table.__file__).read_bytes())} for table in tables],
        'policy': 'Admit each completed checkpoint once as an imperfect raw reading. Preserve all errors and disagreements; explicitly source-rejected spans abstain. No source text substitution, word completion, or additional family vote is authorized.',
        'qualification': 'The review checks correspondence, extent, order, repetition, and editorial boundaries. It does not certify a proofread transcription or make OCR agreement a measurement of accuracy.',
        'records': records, 'generated_by': 'scripts/prepare_photius_body_outcomes.py'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--write', action='store_true')
    actions.add_argument('--check', action='store_true')
    args = parser.parse_args()
    expected = encode(build())
    if args.write:
        (ROOT / OUT).write_bytes(expected)
    elif args.check:
        if (ROOT / OUT).read_bytes() != expected:
            raise SystemExit('Body outcome authority does not reproduce')
    else:
        print(expected.decode(), end='')
