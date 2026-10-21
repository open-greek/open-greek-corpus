"""Complete source review of retained historical passages on Bekker printed272.

All four retained paragraphs in the left column were visually checked against the
pinned scan. The separate fresh-consensus right-column passage is outside this
table. Compact uncertain characters retain their original display and alternatives.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib
from prepare_photius_historical_readings import row_sha
from photius_complete_observations_boundaries import _segments,_digital_observations,_CONVENTION
REVIEWED_AT = '2026-10-21T12:30:47.378032+00:00'
_CROPS = {'A': [0.205, 0.105, 0.59, 0.315],
 'B': [0.205, 0.28, 0.59, 0.455],
 'C': [0.205, 0.45, 0.59, 0.68],
 'D': [0.205, 0.675, 0.59, 0.735]}
_SPECS = [(7,
  1,
  '0ced30d42c042f7f46a85118ccde6a7a8d20328fba349166d826bfe341dd6f38',
  'εὐσεβῶν μὴ λίαν τὴν φωνὴν ἀσπαζόμενος. μὴ οὖν λεγέτω τις (οὐδὲν γὰρ τοῦτο πρὸς τὴν εὐσέβειαν) ὡς ἐπὶ Χριστοῦ '
  'δύο φύσεις λέγειν οἱ πατέρες ἐκώλυσαν· ἀλλὰ δεικνύτω πότε ἢ πῶς τοὺς συνομολογοῦντας τὴν καθ’ ὑπόστασιν ἕνωσιν '
  'δύο λέγειν φύσεις ἀδιαιρέτως ἐκώλυσαν. καὶ γὰρ κἀνταῦθα ὅρα πῶς φησιν ὁ Ἀθανάσιος „ἐ δύο φύσεις ὁμολογοῦμεν '
  'τὸν ἕνα υἱόν, μίαν προσκυνητὴν καὶ μίαν ἀπροσκύνητον.” ἀκούεις πῶς εἶπε προσκυνητὴν καὶ ἀπροσκύνητον. καὶ τίς '
  'οὐκ οἶδεν ὅτι τὸ προσκυνητὸν καὶ ἀπροσκύνητον εἰς δύο μὲν ὑποστάσεις τέμνουσι τὸν ἕνα, τὴν καθ’ ὑπόστασιν δὲ '
  'ἕνωσιν ἐκκηρύττουσιν;',
  'εὐσεβῶν μὴ λίαν τὴν φωνὴν ἀσπαζόμενος. μὴ οὖν λεγέτω τις (οὐδὲν γὰρ τοῦτο πρὸς τὴν εὐσέβειαν) ὡς ἐπὶ Χριστοῦ '
  'δύο φύσεις λέγειν οἱ πατέρες ἐκώλυσαν· ἀλλὰ δεικνύτω πότε ἢ πῶς τοὺς συνομολογοῦντας τὴν καθ’ ὑπόστασιν ἕνωσιν '
  'δύο λέγειν φύσεις ἀδιαιρέτως ἐκώλυσαν. καὶ γὰρ κἀνταῦθα ὅρα πῶς φησιν ὁ Ἀθανάσιος „οὐ δύο φύσεις ὁμολογοῦμεν '
  'τὸν ἕνα υἱόν, μίαν προσκυνητὴν καὶ μίαν ἀπροσκύνητον.” ἀκούεις πῶς εἶπε προσκυνητὴν καὶ ἀπροσκύνητον. καὶ τίς '
  'οὐκ οἶδεν ὅτι τὸ προσκυνητὸν καὶ ἀπροσκύνητον εἰς δύο μὲν ὑποστάσεις τέμνουσι τὸν ἕνα, τὴν καθ’ ὑπόστασιν δὲ '
  'ἕνωσιν ἐκκηρύττουσιν;',
  'A',
  [],
  []),
 (7,
  2,
  'bc16020061cea74f8a0d536759a32e6189b46f4c826965d46136f989b1a0e579',
  'ἀλλ’ ἡ μὲν τοῦ μεγάλου Ἀθανασίου διάνοια δήλη· ἡ δὲ τὸν θαυματουργὸν Γρηγόριον ὑποβαλλομένη χρῆσις (λέγεται '
  'μὲν γὰρ ἐκεῖνο, τὸν δὲ Ἀπολλινάριον εἰσκομίζει) κατάφωρον προβάλλεται τὴν ἀτοπίαν. λέγει γὰρ, καὶ ἔστι Θεὸς '
  'ἀληθινὸς ὁ ἄσαρκος ἐν σαρκὶ φανερωθείς, τέλειος τῇ ἀληθινῇ καὶ θείᾳ τελειότητι, οὐ δύο πρόσωπα οὐδὲ δύο '
  'φύσεις· οὐδὲ γὰρ τέσσαρας προσκυνεῖν λέγομεν. ὁρᾷς ὅπως προφανὴς ἡ δυσσέβεια; τὸ τέλειον γὰρ εἰπὼν κατὰ τὴν '
  'θεότητα, τὴν ἀνθρωπότητα παντελῶς ἐσιώπησε. καὶ τὸ προειπεῖν δὲ „ὁ ἄσαρκος ἐν σαρκὶ φανερωθείς” τῆς '
  'Ἀπολιναρίου φρενοβλαβοῦς γεωργίας πικρόν ἐστι βλάστημα.',
  'ἀλλ’ ἡ μὲν τοῦ μεγάλου Ἀθανασίου διάνοια δήλη· ἡ δὲ τὸν θαυματουργὸν Γρηγόριον ὑποβαλλομένη χρῆσις (λέγεται '
  'μὲν γὰρ ἐκείνου, τὸν δὲ Ἀπολλινάριον εἰσκομίζει) κατάφωρον προβάλλεται τὴν ἀτοπίαν. λέγει γὰρ, καὶ ἔστι θεὸς '
  'ἀληθινὸς ὁ ἄσαρκος ἐν σαρκὶ φανερωθείς, τέλειος τῇ ἀληθινῇ καὶ θείᾳ τελειότητι, οὐ δύο πρόσωπα οὐδὲ δύο '
  'φύσεις· οὐδὲ γὰρ τέσσαρας προσκυνεῖν λέγομεν. ὁρᾷς ὅπως προφανὴς ἡ δυσσέβεια; τὸ τέλειον γὰρ εἰπὼν κατὰ τὴν '
  'θεότητα, τὴν ἀνθρωπότητα παντελῶς ἐσιώπησε. καὶ τὸ προειπεῖν δὲ „ὁ ἄσαρκος ἐν σαρκὶ φανερωθείς” τῆς '
  'Ἀπολιναρίου φρενοβλαβοῦς γεωργίας πικρόν ἐστι βλάστημα.',
  'B',
  [],
  []),
 (7,
  3,
  '54701a9ae476b50f5f71ad77cb1b1024e8b89351da3df3bc9f2db3f5aa61dc82',
  'ἀλλὰ γὰρ καὶ ἡ χρῆσις, ἣν ἡ αἵρεσις προκομίζει ἐκ τῆς πρὸς Διονύσιον ἐπιστολῆς τοῦ Ἰουλίου Ῥώμης, ἀναμφίβολον '
  'μὲν οὐκ ἔχει τὸ γνήσιον· ὁ γὰρ ἱερὸς Κύριλλος, ἐν τῇ κατ’ Ἔφεσον συνόδῳ ἐκ τῆς πρὸς Δόκιον ἐπιστολῆς αὐτοῦ '
  'χρείαν προενεγκών, οὐκ ἠξίωσεν εἰς μνήμην ταύτης ἐλθεῖν. ἣν δὲ τῇ συνόδῳ προανέγνωσεν, οὕτω τοῖς ῥήμασιν ἔχει '
  '„ὁ τοῦ θεοῦ υἱὸς σκηνώσας ἐν ἀνθρώποις, οὐκ ἐν ἀνθρώπῳ ἐνεργήσας, τέλειος Θεὸς ἐν σαρκί, τέλειος ἄνθρωπος ἐν '
  'πνεύματι· οὐ δύο υἱοί, εἷς μὲν γνήσιος υἱὸς ἀναλαβὼν ἄνθρωπον, “ἕτερος δὲ θνητὸς ἄνθρωπος ἀναληφθεὶς ὑπὸ τοῦ '
  'Θεοῦ, ἀλλ’ εἷς ἐν οὐρανῷ μονογενής, μονογενὴς ἐπὶ γῆς θεός.” ἡ μὲν τοῦ Ἰουλίου ῥῆσις ἡ τῇ συνόδῳ διαγνωσθεῖσα '
  'τοιαύτη; εἰ δὲ γνησίαν ᾔδει τὴν φωνὴν ἣν ἐκ τῆς πρὸς Διονύσιον προφέρουσιν ἐπιστολῆς καὶ μάλιστα Νεστόριον '
  'κατακρίνασαν, οὐκ ἂν ὑπερεῖδε ταύτην.',
  'ἀλλὰ γὰρ καὶ ἡ χρῆσις, ἣν ἡ αἵρεσις προκομίζει ἐκ τῆς πρὸς Διονύσιον ἐπιστολῆς τοῦ Ἰουλίου Ῥώμης, ἀναμφίβολον '
  'μὲν οὐκ ἔχει τὸ γνήσιον· ὁ γὰρ ἱερὸς Κύριλλος, ἐν τῇ κατ’ Ἔφεσον συνόδῳ ἐκ τῆς πρὸς Δόκιον ἐπιστολῆς αὐτοῦ '
  'χρείαν προενεγκών, οὐκ ἠξίωσεν εἰς μνήμην ταύτης ἐλθεῖν. ἣν δὲ τῇ συνόδῳ προανέγνωσεν, οὕτω τοῖς ῥήμασιν ἔχει '
  '„ὁ τοῦ θεοῦ υἱὸς σκηνώσας ἐν ἀνθρώποις, οὐκ ἐν ἀνθρώπῳ ἐνεργήσας, τέλειος θεὸς ἐν σαρκί, τέλειος ἄνθρωπος ἐν '
  'πνεύματι· οὐ δύο υἱοί, εἷς μὲν γνήσιος υἱὸς ἀναλαβὼν ἄνθρωπον, “ἕτερος δὲ θνητὸς ἄνθρωπος ἀναληφθεὶς ὑπὸ τοῦ '
  'θεοῦ, ἀλλ’ εἷς ἐν οὐρανῷ μονογενής, μονογενὴς ἐπὶ γῆς θεός.” ἡ μὲν τοῦ Ἰουλίου ῥῆσις ἡ τῇ συνόδῳ διαγνωσθεῖσα '
  'τοιαύτη; εἰ δὲ γνησίαν ᾔδει τὴν φωνὴν ἣν ἐκ τῆς πρὸς Διονύσιον προφέρουσιν ἐπιστολῆς καὶ μάλιστα Νεστόριον '
  'κατακρίνασαν, οὐκ ἂν ὑπερεῖδε ταύτην.',
  'C',
  [],
  [('προκομίζει',
    'προσκομίζει',
    'The compressed group before κ may include a sigma ligature, giving προσκομίζει, while the original and '
    'digital reading have προκομίζει. Keep the original until independent evidence resolves the exact group.'),
   ('διαγνωσθεῖσα',
    'διαγνωσθεῖσα',
    'The compact σθ group is not separately legible enough to exclude a reading without sigma. Retain the '
    'original διαγνωσθεῖσα; possible διαγνωθεῖσα remains explicit. See Ingram1966, printed387, '
    'https://neoclassica.co/wp-content/uploads/2025/07/ligatures-grecques.pdf .')]),
 (7,
  4,
  '80ca7d2cdfa57b69891e65527eca1349a4500f77dacac27b1eb98d31571111da',
  'ἔτι δὲ κἀκεῖνο δεῖ συνιδεῖν, ὡς ὁ σοφὸς Κύριλλος τὸν ἄνθρωπον εἰς παράδειγμα, ⟦οὐχ ∥ ἐκ⟧ ἵνα δείξῃ μίαν φύσιν '
  'ἐπὶ τοῦ Χριστοῦ, παραλαμβάνει, “ἀλλ’ ὡς ἄν',
  'ἔτι δὲ κἀκεῖνο δεῖ συνιδεῖν, ὡς ὁ σοφὸς Κύριλλος τὸν ἄνθρωπον εἰς παράδειγμα, οὐχ ἵνα δείξῃ μίαν φύσιν ἐπὶ τοῦ '
  'Χριστοῦ, παραλαμβάνει, “ἀλλ’ ὡς ἄν',
  'D',
  [],
  [('ἄν',
    'ἂν',
    'The small accent on the final word is not securely distinguishable between acute and grave in this '
    'impression. Preserve original ἄν; possible printed ἂν remains explicit.')])]

def records(rows, document, crop_png, sections):
    output, cache = [], {}
    for page, number, expected, original, reviewed, crop, fragments, unknown in _SPECS:
        locus = f'helladius_chrestomathia_photius_bekker_v2_{page:04d}.{number}'
        if row_sha(rows[locus]) != expected or rows[locus]['text'] != original:
            raise ValueError(f'Complete source review preimage changed: {locus}')
        if crop not in cache:
            cache[crop] = hashlib.sha256(crop_png(document,page,_CROPS[crop])).hexdigest()
        segments, offset = [], 0
        for start, end, old, corrected, uncertainty in _segments(original,reviewed,unknown):
            observed = uncertainty[0] if uncertainty else corrected
            digital, alignment = _digital_observations(observed,page,sections)
            segment = {'start':start,'end':end,'original_text':old,'corrected_text':corrected,
                'verification':'uncertain'if uncertainty else'verified',
                'review_basis':'direct-scan-inspection','reviewed_at':REVIEWED_AT,
                'evidence':'Direct visual inspection of every character in the recorded printed body range in the pinned Bekker1825 volume2 scan, with paragraph and physical-line boundaries checked against the page.',
                'scan':{'physical_page':page,'region':_CROPS[crop],'image_sha256':cache[crop],
                    'observed_text':observed,'max_side':3600},
                'readings':digital,'digital_alignment':alignment,'fragments':[],
                'transcription_convention':_CONVENTION+' Expand the conventional printed σθ ligature to ordinary Greek Unicode.'}
            if uncertainty:
                segment['uncertainty'] = uncertainty[1]
            for f in fragments:
                if offset <= f['start'] and f['end'] <= offset+len(corrected):
                    segment['fragments'].append({**deepcopy(f),'start':f['start']-offset,'end':f['end']-offset})
            offset += len(corrected)
            segments.append(segment)
        if offset != len(reviewed):
            raise ValueError(f'Complete source span accounting changed: {locus}')
        output.append({'locus':locus,'original_row_sha256':expected,
            'status':'reviewed-with-uncertainty'if unknown else'reviewed-verified','segments':segments})
    return output
