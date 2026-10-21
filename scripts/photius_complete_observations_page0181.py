"""Complete direct scan observations for retained historical physical page 181.

Every source word and unchanged passage was inspected. All unresolved glyphs,
independent digital alternatives, and column boundaries remain explicit.
"""
from copy import deepcopy
import hashlib,json,re
REVIEWED_AT='2026-10-21T13:49:43.405992Z'
PASSAGES={1: ('γένοιτ’ ἂν ἐμφανής',
     'ἐπ’ αὐταῖς εὕρῃς ταῖς δοκιμασίαις.',
     [('τῷ συντελεσθέντος', '{u0}'),
      ('ἐκ ὀλίγοις', 'οὐκ ὀλίγοις'),
      ('περὶ τότε', 'περὶ τούτου'),
      ('ἐκπεφευγότες', '{u1}'),
      ('τὰς ἄμεινον', 'τοὺς ἄμεινον')]),
 2: ('"Ἡγησίας μὲν',
     'καὶ μεταφορὰ σκληρά,',
     [('διαλέγεσθαι', '{u0}'),
      ('ἐστοχάζετο', '{u1}'),
      ('φωρᾶται', '{u2}'),
      ('δισαγμὸν', 'δισταγμὸν'),
      ('ἐνεργάσῃ', '{u3}'),
      ('τὰς ἀξιώσεις', '{u4}'),
      ('διακοσμεῖν', '{u5}'),
      ('σκληρά,', 'σκλη-')]),
 3: ('σκληρά, τὸ δὲ',
     'πρὸς ἐλεεινολογίαν λέγοι,',
     [('σκληρά, τὸ δὲ', 'ρά, τὸ δὲ'),
      ('ἡτοιμάσθαι', '{u0}'),
      ('φαίνεται', '{u1}'),
      ('ἐφορᾶσθαι', '{u2}'),
      ('ἐκ ὀλοφύρεσθαι', '{u3}'),
      ('συγκύψαιτο', '{u4}'),
      ('δοκᾶσιν', '{u5}'),
      ('τὰς σπαρτὰς', 'τοὺς σπαρτοὺς'),
      ('ἀλλ’ ἐκ ἔστως', 'ἀλλ’ οὐχ οὕτως'),
      ('μηλόβοτον γενέσθαι τὴν Ἀττικήν', 'μηλόβοτον {u6}'),
      ('ἄσπορον γενέσθαι τὴν τοὺς', 'ἄσπορον {u7}'),
      ('ἐσχάτην', '{u8}'),
      ('λέγοι,', 'λέ-')])}
UNCERTAINTIES={(181, 1): [('τῷ συντελέσαντι',
             'τοῦ συντελεσθέντος',
             'The compact sigma/theta group remains unresolved independently.'),
            ('ὑπερφυγόντες',
             'οὐ πεφυγότες / ἐκπεφευγότες',
             'The compact prefix and participle remain unresolved independently.')],
 (181, 2): [('διαλέγεσθαι', 'διαλέγεσθαι', 'The unchanged compact sigma/theta group remains unresolved independently.'),
            ('ἢ σχίζει', 'ἀστοχάζεται / ἐστοχάζετο', 'The compact verb and ending remain unresolved independently.'),
            ('φωρῷ)', 'φωρᾶται', 'The compact final consonants and ending remain unresolved independently.'),
            ('ἐνεργῶν', 'ἐνεργάσηται / ἐνεργάσῃ', 'The compact final consonants remain unresolved independently.'),
            ('τὸς ἀξιώμας', 'τὰς ἀξιώσεις', 'The compact noun ending remains unresolved independently.'),
            ('διακοσμεῖν', 'διακοσμῇ / διακοσμεῖν', 'The compact final ending remains unresolved independently.')],
 (181, 3): [('ἡτοιμάζω', 'ἡτοιμάσθαι', 'The compact sigma/theta group remains unresolved independently.'),
            ('φαινεῖν', 'φαίνεται', 'The compact final consonants and ending remain unresolved independently.'),
            ('ἐφορώθη', 'ἐφορᾶσθαι', 'The compact sigma/theta group remains unresolved independently.'),
            ('ὡς ὑλοφρόνως', 'οὐκ ὀλοφύρεσθαι', 'The compact sigma/theta group remains unresolved independently.'),
            ('συνηκόψαι', 'συμψύξαιτο', 'The compact consonants and ending remain unresolved independently.'),
            ('δοκεῖν', 'δοκεῖν / δοκῶ', 'The compact verb ending remains unresolved independently.'),
            ('γενέσθαι τὴν Ἀττικὴν',
             'γενέσθαι τὴν Ἀττικήν',
             'The compact sigma/theta group remains unresolved independently.'),
            ('γενέσθαι τὴν τῶς',
             'γενέσθαι τὴν τοὺς',
             'The compact sigma/theta group remains unresolved independently.'),
            ('ἐχάτην', 'ἐσχάτην', 'The compact sigma/chi group remains unresolved independently.')]}
LEADING_FRAGMENTS={(181,3):'ρά'}
CHUNKS={}
def records(rows,document,crop_png,sections):
    global CHUNKS
    CHUNKS={}
    for number,(begin,end,changes)in PASSAGES.items():
        target=_reading(sections,181,begin,end)[0]['text']
        for before,after in changes:
            if before not in target:raise ValueError((number,before))
            target=target.replace(before,after)
        region=[.20,.105,.65,.34]if number==1 else[.20,.27,.65,.73]if number==2 else[.56,.105,.99,.73]
        chunks=[(None,target,region,begin,end)]
        if number==2:chunks.insert(0,('1336R ','',[.20,.27,.65,.37],None,None,'marginal-reference','1336R.'))
        CHUNKS[(181,number)]=chunks
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
