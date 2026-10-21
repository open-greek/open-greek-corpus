"""Complete direct scan review of physical186, including unchanged words.

The pinned independent witness retains its conflicting readings as alternatives.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T14:39:27.618751Z'
PASSAGES={2: ('τὴν γνώμην·', 'ταύτας τοῖς ἰχθύσιν.', [('κεῖσθαι', '{u0}')]),
 3: ('ὅτι φησὶν ἐνίας',
     'ὡρίσαντο φυσικῶν.',
     [('ἐνίας', 'ἐνίους'),
      ('οὐ καὶ πεζῇ', '{u0}'),
      ('λαβόντες', 'οὐ λαβόντες')]),
 4: ('ὅτι τῶν ξενῶν',
     'εἶναι τὸ αὐτὸ ναῦν',
     [('ξενῶν', 'στενῶν'),
      ('δοκὲν', 'δοκεῖν'),
      ('κῦμα μὲν οὐ γίνεται', '{u0}'),
      ('ἄριστον', 'ἄκρον'),
      ('βυθῷ νέμονται', 'βυθῷ {u1}'),
      ('ἀφικόμεναι κοιμῶνται', '{u2}'),
      ('σιτοῦνται', '{u3}'),
      ('χρῶνται τὰς', '{u4}'),
      ('κέχρηνται', '{u5}'),
      ('τελέως, γίνεται τῷ πλάτει', 'τελέως, {u6}')]),
 5: ('οἰκίαν ἀγγεῖον', 'τοῖς εἰρημένοις ἀνθρώποις.', []),
 6: ('ὅτι οὐ πολὺ διεστῶτες',
     'γνῶσιν, τοσαῦτα.',
     [('τὰ εἰρημένα γένη', 'τοῖς εἰρημένοις γένεσι'),
      ('παραμυθοῦνται', '{u0}')]),
 7: ('ὅτι τῆς ζωῆς',
     'εὐγνωμονεῖν δυνάμενον;',
     [('συνέχονται', '{u0}'),
      ('ἄλλους δρῶσι', 'ἄλλως δρῶσι'),
      ('πάσχουσι', '{u1}'),
      ('σφάλλονται', '{u2}'),
      ('ἕκαστον τὸ ἀγνοούμενον', 'ἕκαστον οὐ τὸ ἀγνοούμενον'),
      ('τὸ βλητόν', 'τὸ βουλητόν'),
      ('ὑπερξέῃ τὰ καιροῦ', '{u3} τοῦ καιροῦ'),
      ('ἐκοῦν', 'οὐκοῦν'),
      ('ἃ δικαιοῦνται', 'οὐ {u4}'),
      ('προστάγματι', 'προστάγμασι')]),
 8: ('ὅτι μετὰ τοὺς ἰχθυοφάγους',
     'εἶτα ἐν τῷ καύματι',
     [('Ἀσαβάραν', 'Ἀσταβάραν'), ('φέρεται', '{u0}')])}
UNCERTAINTIES={(186, 2): [('κείδῃ',
             'κεῖσθαι',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.')],
 (186, 3): [('καὶ περὶ',
             'ᾧ καὶ πεζῇ / οὐ καὶ πεζῇ',
             'The compact connective and its source expansion remain '
             'unresolved independently.')],
 (186, 4): [('κῦμα μὲν οὐ γίνεται',
             'κῦμα μὲν οὐ γίνεται',
             'The compact final consonants remain unresolved independently of '
             'the digital witness.'),
            ('μένοντ’',
             'νέμονται',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.'),
            ('ἀφικνοῦνται κομιδῇ',
             'ἀφικόμεναι κοιμῶνται',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.'),
            ('σῴζουσι',
             'σιτοῦνται',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.'),
            ('χρόνον τὰς',
             'χρῶνται τὰς',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.'),
            ('κέχρηνται',
             'κέχρηνται',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.'),
            ('γίνεται τῷ πλάτει',
             'γίνεται τῷ πλάτει',
             'The compact final consonants remain unresolved independently of '
             'the digital witness.')],
 (186, 6): [('παραμνῶσι',
             'παραμυθοῦνται',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.')],
 (186, 7): [('συνέχον',
             'συνέχονται',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.'),
            ('πάσχουσι',
             'πάσχουσι',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.'),
            ('σφάλλον',
             'σφάλλονται',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.'),
            ('ὑπερίψῃ',
             'ὑπερίξῃ / ὑπερξέῃ',
             'The compact verb and vowel sequence remain unresolved '
             'independently.'),
            ('δικαιοῦν',
             'δικαιοῦνται',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.')],
 (186, 8): [('φέρετ',
             'φέρεται',
             'The compact sigma/theta or sigma/chi group remains unresolved '
             'independently of the digital witness.')]}
LEADING_FRAGMENTS={}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,186,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        region=[.025,.105,.49,.30]if number==2 else[.025,.18,.49,.40]if number==3 else[.025,.30,.49,.73]if number==4 else[.39,.105,.86,.73]
        CHUNKS[(186,number)]=[(None,target,region,begin,end)]
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
