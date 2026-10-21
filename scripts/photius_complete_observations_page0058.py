"""Complete direct scan review of physical 58.

Every retained word inspected; unresolved glyphs and digital alternatives preserved.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T14:45:28.339071Z'
PASSAGES={1: ('μόριον, ὡς ἀρχὴ',
     'σημαινόμενα οὐκέτι.',
     [('μόριον', 'τασκευάσματος μόριον')]),
 2: ('ὅτι ἀντὶ τοῦ ἐν ἀρχῇ', 'αὐτὸ μετειλήφασιν.', [('ἐσχηματίσθη', '{u0}')]),
 3: ('ὅτι φησίν, Οὐρανὸν',
     'ἢ καὶ τὸ ἄλλως πως συμβαῖνον.',
     [('ταῦτα καλεῖ', 'ταῦτα {u0}')]),
 4: ('ὅτι τὸ ψηλαφητὸν',
     'οὕτω τὰ ψηλαφώμενα.',
     [('εἰρῆσθαι', '{u0}'),
      ('τὰς μεταβάσεις ποιεῖσθαι', 'τὰς μεταβάσεις {u1}')]),
 5: ('ὅτι ἄβυσσος παρὰ', '„καὶ πνεῦμα', [('μηνύειν', 'μὴ βαίνειν')]),
 7: ('γὰρ „Θεοῦ ἐπεφέρετο',
     'ἐπ᾽ ἀμφοῖν κέχρηται τῷ ὀνόματι.',
     [('ἐπινήχετο', '{u0}'), ('κέχρηται', '{u1}')]),
 8: ('ὅτι τὰς ἀγγέλους',
     'ὑπὸ Θεοῦ μετέχε γενέσεως.',
     [('ἀλλ᾽ ἐν οὐδὲ δεῖ λέγειν', '{u0}'),
      ('συνυπέστησαν', '{u1}'),
      ('πειρᾶται', '{u2}'),
      ('διαμάχεσθαι', '{u3}'),
      ('συνδεδέσθαι', '{u4}'),
      ('συγκαταβληθῆναι', '{u5}'),
      ('συνυποστῆναι σώματι', '{u6} σώματι')]),
 10: ('ὅτι Βαβυλῶνά φησι',
      'ὁπόσα ἐς ἔφυδρον ξύνδεσιν',
      [('τετειχίσθαι', '{u0}'),
       ('τέμνεται', '{u1}'),
       ('ὑποσείχει', 'ὑποστείχει'),
       ('λέγεται', '{u2}'),
       ('ξύνδεσιν', 'ξύνδε-')])}
UNCERTAINTIES={(58, 2): [('ἐχρημάτισε',
            'ἐσχηματίσθαι',
            'The compact sigma/theta or sigma/chi group remains unresolved '
            'independently of the digital witness.')],
 (58, 3): [('καλεῖ',
            'καλεῖται',
            'The compact final consonants remain unresolved independently of '
            'the digital witness.')],
 (58, 4): [('εἰρῆσθαι',
            'εἰρῆσθαι',
            'The compact sigma/theta or sigma/chi group remains unresolved '
            'independently of the digital witness.'),
           ('ποιεῖ',
            'ποιεῖσθαι',
            'The compact sigma/theta or sigma/chi group remains unresolved '
            'independently of the digital witness.')],
 (58, 7): [('ἐπινῆχε)',
            'ἐπινήχετο',
            'The compact final consonants remain unresolved independently of '
            'the digital witness.'),
           ('χέχρηται',
            'κέχρηται',
            'The compact final consonants remain unresolved independently of '
            'the digital witness.')],
 (58, 8): [('ἀλλ’ ἐν ὧδε δεῖ λέγειν',
            'ἀλλ’ ἐν οὐδὲ δεῖ λέγειν',
            'The compressed connective remains uncertain independently of the '
            'digital witness.'),
           ('συννηλέχθαι',
            'συνυπέστησαν',
            'The compact verb remains unresolved independently of the digital '
            'witness.'),
           ('περίθαι',
            'πειρᾶται',
            'The compact final consonants remain unresolved independently of '
            'the digital witness.'),
           ('διαμάχελη',
            'διαμάχεσθαι',
            'The compact sigma/theta or sigma/chi group remains unresolved '
            'independently of the digital witness.'),
           ('συνδεδοθ.ς',
            'συνδεδέσθαι',
            'The compact sigma/theta or sigma/chi group remains unresolved '
            'independently of the digital witness.'),
           ('συγκαταβεβλη.ς',
            'συγκαταβληθῆναι',
            'The compact sigma/theta or sigma/chi group remains unresolved '
            'independently of the digital witness.'),
           ('συννοσῆναι',
            'συνυποστῆναι',
            'The compact sigma/theta or sigma/chi group remains unresolved '
            'independently of the digital witness.')],
 (58, 9): [('Ἀνεγνώσθη',
            'Ἀνεγνώσθη',
            'The compact sigma/theta or sigma/chi group remains unresolved '
            'independently of the digital witness.')],
 (58, 10): [('τετευχλᾶς',
             'τετειχίσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.'),
            ('τέμνε)',
             'τέμνεται',
             'The compact final consonants remain unresolved independently of '
             'the digital witness.'),
            ('λέγε)',
             'λέγεται',
             'The compact final consonants remain unresolved independently of '
             'the digital witness.')]}
LEADING_FRAGMENTS={(58, 1): 'τασκευάσματος'}
LINES={}
HEADINGS={9: ('{u0} ἐκ τοῦ εἰς τὸν Ἀπολλώνιον ἀπὸ φωνῆς ΦΙΛΟΣΤΡΑΤΟΥ.',
     'Ἀνεγνώσθη ἐκ τοῦ εἰς',
     'ἀπὸ φωνῆς ΦΙΛΟΣΤΡΑΤΟΥ.',
     [0.405, 0.55, 0.835, 0.64])}
RIGHT_BOUNDS=None
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,58,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        region=[0.025, 0.105, 0.49, 0.73]if number<=5 else[0.39, 0.105, 0.86, 0.73]
        CHUNKS[(58,number)]=[(None,target,region,begin,end)]
    for number,target in LINES.items():
        region=[0.39, 0.105, 0.86, 0.73]
        begin,end=RIGHT_BOUNDS if RIGHT_BOUNDS else(None,None)
        CHUNKS[(58,number)]=[(None,target,region,begin,end)]
    for number,(target,begin,end,region)in HEADINGS.items():
        CHUNKS[(58,number)]=[(None,target,region,begin,end,'unclassified-heading')]
    return _records(rows,document,crop_png,sections)

def _row_sha(row):
    return hashlib.sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _reading(sections,page,begin,end):
    if begin is None:return []
    section=f'tlg4040-tlg001-local002-s{page+277}'; full=sections[section]
    starts=[m.start()for m in re.finditer(re.escape(begin),full)]
    if len(starts)!=1:raise ValueError(f'Ambiguous digital bound {page}: {begin!r}')
    a=starts[0];b=full.index(end,a)+len(end)
    return [{'kind':'digital','section':section,'start':a,'end':b,'text':full[a:b]}]


def _records(rows,document,crop_png,sections):
    result=[];image_hashes={}
    for (page,number),chunks in sorted(CHUNKS.items()):
        locus=f'helladius_chrestomathia_photius_bekker_v2_{page:04}.{number}'
        row=rows[locus]; original=row['text']; cursor=0; segments=[]
        for chunk in chunks:
            anchor,target,region,begin,last,*role_info=chunk
            end=len(original)if anchor is None else original.index(anchor,cursor)+len(anchor)
            role=role_info[0]if role_info else None
            literal=role_info[1]if len(role_info)>1 else None
            key=(page,tuple(region))
            if key not in image_hashes:image_hashes[key]=hashlib.sha256(crop_png(document,page,region)).hexdigest()
            reading=_reading(sections,page,begin,last)
            ranges=[]
            for i,(old,observed,reason)in enumerate(UNCERTAINTIES.get((page,number),[])):
                marker='{u'+str(i)+'}'
                if marker in target:
                    a=original.index(old,cursor,end); ranges.append((a,a+len(old),observed,reason,marker))
            ranges.sort();part_cursor=cursor;target_cursor=0
            def add(a,b,text,observed=None,reason=None):
                if a==b:
                    if text:raise ValueError('Unattached insertion')
                    return
                fragments=[]
                leading=LEADING_FRAGMENTS.get((page,number))
                if a==0 and leading:
                    if not text.startswith(leading):raise ValueError('Changed printed leading fragment')
                    fragments.append({'start':0,'end':len(leading),'text':leading,'side':'leading','qualification':'Printed continuation of a word begun on the preceding source line or page. Preserve the suffix without supplying missing letters or counting it as a standalone lexical form.'})
                if text.endswith('-'):
                    m=re.search(r'[^\W\d_]+-$',text)
                    fragments.append({'start':m.start(),'end':m.end(),'text':m.group(),'side':'trailing','qualification':'This retained passage ends within a visibly divided printed word; preserve the source fragment and exclude it from lexical counts.'})
                segment={'start':a,'end':b,'original_text':original[a:b],'corrected_text':text,
                    'verification':'uncertain'if reason else'verified','review_basis':'direct-scan-inspection',
                    'reviewed_at':REVIEWED_AT,'evidence':'Direct inspection of every word and punctuation mark, including unchanged text, in this contiguous passage. The overlapping pinned crops cover the full retained source. Independent digital readings remain bounded alternatives, not automatic authority.',
                    'scan':{'physical_page':page,'region':region,'max_side':3600,'image_sha256':image_hashes[key],'observed_text':observed if observed is not None else literal if literal is not None else text},
                    'readings':deepcopy(reading),'fragments':fragments,
                    'transcription_convention':'Expand clearly visible printed ου, στ, and καί ligatures. Reflow complete words visibly divided between lines within a retained passage. Preserve incomplete passage boundaries; omit marginal references and printed line numbers from body transcription.'}
                if reason:segment['uncertainty']=reason
                if role:
                    segment['text_role']=role
                    segment['evidence']+=(' This is an isolated marginal reference label; the body projection omits it.'if role=='marginal-reference'else' This is part of the centered, letter-spaced source-identification heading between extracts. Its placement and type establish the heading boundary without establishing authorship; preserve its literal text and exclude it from lexical admission pending attribution.'if role=='unclassified-heading'else' This inset small-type explanatory paragraph follows the large-type body and precedes the lower apparatus; its typography establishes boundaries without establishing authorship. Exclude it pending attribution.')
                segments.append(segment)
            for a,b,observed,reason,marker in ranges:
                mark=target.index(marker,target_cursor)
                add(part_cursor,a,target[target_cursor:mark]);add(a,b,original[a:b],observed,reason)
                part_cursor=b;target_cursor=mark+len(marker)
            add(part_cursor,end,target[target_cursor:]);cursor=end
        if cursor!=len(original):raise ValueError('Incomplete reviewed row')
        result.append({'locus':locus,'original_row_sha256':_row_sha(row),'status':'reviewed-with-uncertainty'if any(s['verification']=='uncertain'for s in segments)else'reviewed-verified','segments':segments})
    return result


def occurrence_observations(rows, document, crop_png, sections):
    """Project only exact, unambiguous, paired occurrences already source-reviewed.

    This creates no new review status. Uncertain glyphs, source-disagreement
    changes, marginal references, unclassified small type, and printed fragments
    cannot enter this conservative projection for the existing batch schema.
    """
    from difflib import SequenceMatcher
    from assess_photius_historical import tokens
    output = []
    for record in records(rows, document, crop_png, sections):
        row = rows[record['locus']]
        page = int(record['locus'].split('_')[-1].split('.')[0])
        section = f'tlg4040-tlg001-local002-s{page+277}'
        digital = sections[section]
        digital_tokens = tokens(digital)
        boundaries = {(word['start'], word['end']) for word in digital_tokens}
        for segment in record['segments']:
            if segment['verification'] != 'verified' or segment.get('text_role'):
                continue
            before, after = segment['original_text'], segment['corrected_text']
            old_words, new_words = tokens(before), tokens(after)
            matcher = SequenceMatcher(None, [w['text'] for w in old_words],
                [w['text'] for w in new_words], autojunk=False)
            for action, a, b, c, d in matcher.get_opcodes():
                if action != 'replace' or not a < b or not c < d:
                    continue
                old_start, old_end = old_words[a]['start'], old_words[b-1]['end']
                new_start, new_end = new_words[c]['start'], new_words[d-1]['end']
                if any(new_start < fragment['end'] and new_end > fragment['start']
                       for fragment in segment['fragments']):
                    continue
                old, new = before[old_start:old_end], after[new_start:new_end]
                positions = set()
                for reading in segment['readings']:
                    if reading.get('kind') != 'digital':
                        continue
                    for match in re.finditer(re.escape(new), reading['text']):
                        start = reading['start'] + match.start()
                        end = start + len(new)
                        # Multiword spans need exact token boundaries at both ends.
                        if (any(w['start'] == start for w in digital_tokens)
                                and any(w['end'] == end for w in digital_tokens)):
                            positions.add(start)
                if len(positions) != 1:
                    continue
                chosen = positions.pop()
                old_matches = [m.start() for m in re.finditer(re.escape(old), row['text'])]
                new_matches = [m.start() for m in re.finditer(re.escape(new), digital)]
                original_start = segment['start'] + old_start
                if original_start not in old_matches or chosen not in new_matches:
                    raise ValueError('Reviewed occurrence projection changed an exact span')
                item = {'locus': record['locus'], 'page': page,
                    'original_text': old, 'corrected_text': new,
                    'source_region': segment['scan']['region'],
                    'evidence': 'Direct inspection of the complete retained passage on the pinned Bekker scan confirms this exact occurrence; its corrected reading also agrees with one explicitly bounded digital counterpart. This projection excludes unresolved glyphs, differing witness readings, word fragments, and unclassified material.'}
                if len(old_matches) != 1:
                    item['occurrence'] = old_matches.index(original_start)
                if len(new_matches) != 1:
                    item['digital_occurrence'] = new_matches.index(chosen)
                output.append(item)
    return output
