"""Source-reviewed Photius middle-page comparison windows.

Only listed physical pages have been inspected against the pinned full scan.
Offsets address the original Source Library text without normalization.
"""

SPECS = {131: (4094,
       4094,
       'The body finishes the chronology of Chrysostom homilies and then begins the internal codex175 '
       'Pamphila introduction, ending with γυναικὸς ἔκγονον οὖσα. Source Library omits the initial printed '
       'τὰ continuing prior-page με-; abstain on that suffix. The aggregate top running header and smaller '
       'numbered notes are outside the digital body; the exact Qwen3.6 header is separately masked.'),
 132: (3981,
       3981,
       'The body finishes Pamphila and begins the internal codex176 Theopompus title and historical-book '
       'outline, including its discussions of historians and letters. Both columns reach the complete final '
       'συγγραψαμένῳ. The top running header and smaller critical apparatus are absent from this digital '
       'body.'),
 133: (4094,
       4103,
       'Both columns continue the Theopompus critique and begin the internal codex177 Theodore of Antioch '
       'title and discussion of a fifth gospel. The final printed body ends συν-, while Source Library '
       'completes συντάξαι; hold the entire completed digital word. The aggregate running header, small '
       'notes, and printer signature are absent.'),
 134: (4190,
       4190,
       'Both columns continue the Theodore discussion of sin, baptism, and remission, ending with the '
       'complete τοῦτο. The first printed τάξαι continues prior-page συν- and is absent digitally, so the '
       'Source Library prefix abstains. The top running header and small numbered apparatus are outside the '
       'digital body.'),
 135: (4099,
       4099,
       'The body concludes the Theodore discussion and begins the internal codex178 Dioscorides title and '
       'comparison of pharmacological authors, ending with καὶ Γαληνὸς μετὰ. Both columns are represented in '
       'order. The top aggregate running header, smaller apparatus, and printer signature are absent.'),
 136: (4148,
       4148,
       'Both columns finish the Dioscorides comparison and begin the internal codex179 Agapius title and '
       'critique of his theology. The final printed body words are ἀποσπαράσσων δὲ ῥητά, also the digital '
       'endpoint. The running header and separate small critical notes are outside the window; printed body '
       'brackets remain readings.'),
 137: (3938,
       3938,
       'Both columns finish Agapius and introduce the internal codex180 John Lydus and codex181 Damascius '
       'titles. The Damascius dedication passage continues to the final αὕτη θυγάτηρ ἐγεγόνει. The aggregate '
       'running header and smaller apparatus are absent from the digital body.'),
 138: (4181,
       4181,
       'Both columns continue the Damascius Life of Isidore review, its style and biographical criticism, '
       'and the closing account of his studies. The source ends with γεωμετρίας δὲ καὶ ἀριθμητικῆς, matching '
       'the complete digital endpoint. The running header and small critical apparatus remain outside the '
       'body.'),
 139: (4012,
       4012,
       'The body finishes the Damascius account and begins the internal codex182 Eulogius title and '
       'discussion of Novatus and Cornelius. The right column ends with τῇ εὐσεβεῖ δόξῃ μαχομένων. The '
       'source and digital body contain the same ordered extent; the top running header and smaller numbered '
       'notes are absent.'),
 140: (3986,
       3994,
       'Both columns finish Eulogius and introduce the internal codex183 Eudocia Octateuch poem and codex184 '
       'Cyprian/Justina narrative, including its genuine quoted verse. The final print ends λαμ-, while '
       'Source Library completes λαμπρῶν; hold that complete digital word. The aggregate running header and '
       'small apparatus are absent.'),
 141: (4043,
       4043,
       'Both columns finish the Cyprian narrative and begin the internal codex185 Dionysius of Aegae '
       'medical-question list. The initial printed πρῶν continues prior-page λαμ- and is not supplied by '
       'Source Library, so it receives no omission vote. The digital body ends at the printed λβ καὶ ὅτι οὐ '
       'καθ’ before the smaller apparatus; numbered medical chapters are authorial body.'),
 142: (4264,
       4264,
       'Both columns complete the Dionysius medical-question list, retain the internal codex186 Conon title, '
       'and begin the Midas narrative. The printed body ends with μακρὰ ὦτα ἔχειν, matching the digital '
       'extent. The running header and small apparatus are absent; repeated medical-question alternatives '
       'belong to the body and are preserved.'),
 143: (3886,
       3886,
       'Both source columns contain the Conon narrative sequence from the end of Midas through the fifth '
       'story of the locrian musicians; the final phrase τῆς ᾠδῆς is complete. The printed running header '
       'ΔΙΗΓΗΣΕΙΣ is outside the body and present only in the Qwen3.6 raw prefix; the small footer is '
       'outside the Source Library body.'),
 144: (3686,
       3686,
       'Both source columns continue Conon stories six through twelve, including Mopsus, Orpheus, Heracles, '
       'and the Trojan genealogy. The final τὸ Ἴλιον αἴρει is complete, and no small apparatus or repeated '
       'top header enters this Source Library body.'),
 145: (3897,
       3897,
       'Both source columns contain Conon stories thirteen through nineteen. The Source Library window ends '
       'at the complete printed Λίνος ᾄδεται; the following printed μνήμα begins the next sentence and is '
       'not claimed by this digital window. The repeated ΔΙΗΓΗΣΕΙΣ raw Qwen3.6 prefix is the running header '
       'above the body.'),
 146: (3948,
       3958,
       'Both source columns continue Conon stories twenty through twenty-four. The digital final θεραπείας '
       'completes the printed terminal θερα- and is held in full; the remainder stays an independent raw '
       'reading. The initial τε is a complete particle after the prior leaf sentence.'),
 147: (4107,
       4107,
       'Both columns continue Conon stories twenty-five through twenty-nine. The printed initial πείας '
       'continues the preceding leaf θερα- and is absent from the Source Library beginning, so its '
       'unobserved prefix abstains. The final εἰς τὴν is complete; repeated top header and small footer do '
       'not enter this digital window.'),
 148: (3740,
       3751,
       'Both columns continue Conon stories thirty through thirty-four. The source ends in ἀποχω-; Source '
       'Library completes ἀποχωρήσας and that whole final word is held. Body paragraphs, including the '
       'Branchus narrative, remain in original order and the small footer is excluded.'),
 149: (3971,
       3971,
       'Both columns continue Conon through stories thirty-five to thirty-seven, including the two shepherds '
       'and Cadmus. The initial printed ρήσας continues 148 ἀποχω- and is absent from Source Library, so its '
       'unobserved prefix abstains. The final πρὸς τὰς νῦν is complete.'),
 150: (3895,
       3895,
       'Both columns continue the Cadmus account and Conon stories thirty-eight to forty, including the '
       'Milesian deposit, Melanthus, and Andromeda. The final ἡ Ἀνδρομέδα, ὡς is complete; no final word '
       'completion or apparatus enters the digital body.'),
 151: (3969,
       3969,
       'Both columns contain Conon stories forty-one to forty-four with Antandrus, Gelon, the Aetna '
       'brothers, and the beginning of the Milesian kingship dispute. The final ἐξίσαντο is complete. '
       'Repeated story headings and body narrative are retained, while the top running header and footer '
       'remain outside the digital witness.'),
 152: (4077,
       4077,
       'Both source columns complete the Milesian dispute, Orpheus, the Aeneas narrative, and the beginning '
       'of Conon story forty-seven. The final τοῦ Ἡρακλειδῶν γένους is complete; no small apparatus is in '
       'the Source Library body.'),
 154: (3874,
       3874,
       'Both source columns finish Conon, retain the Apollodorus introduction and its authorial quoted '
       'verse, then begin codex187 Nicomachus. The final ἵνα θεὸς ᾖ is complete. The internal book title and '
       'verses belong to the body and are retained; the repeated top header and small footer are outside the '
       'digital witness.'),
 155: (4157,
       4157,
       'Both columns continue Nicomachus with the monad, dyad, and triad explanations and their deity lists. '
       'The final Κραταΐδα is a complete printed word. The repeated top book header and small apparatus are '
       'not present in the digital body; no boundary word completion is voted.'),
 156: (4142,
       4142,
       'Both source columns continue Nicomachus number theology from the tetrad through the nine and their '
       'deity names. The last printed Διὸς is complete and followed on the next leaf by ἀδελφήν; no word is '
       'completed across the boundary. The repeated top header and small footer are outside the digital '
       'text.'),
 157: (3814,
       3814,
       'Both columns finish Nicomachus, preserve the internal188 Alexander and189 Sotion titles and the '
       'Protagoras and Nicolaus discussions. The final ἔστι μὲν καὶ is complete. These internal titles are '
       'body text, unlike the repeated top multi-author running header.'),
 158: (3944,
       3944,
       'Both columns contain the Nicolaus conclusion, Acestorius introduction, and internal190 Ptolemy '
       'Hephaestion title and mythographic examples. The final λουμένην is complete. Small apparatus and the '
       'repeated author header are outside the Source Library body.'),
 159: (3961,
       3961,
       'Both columns continue Ptolemy Hephaestion mythography, moving from Aphrodite and Adonis through the '
       'Heracles material to the Cretan Zeus account. The final ὅτι δὴ is complete. ΚΑΙΝΗ ΙΣΤΟΡΙΑ is the '
       'repeated printed running header and matches the Qwen3.6 raw prefix outside the body.'),
 160: (3990,
       4001,
       'Both columns continue Ptolemy Hephaestion, including book-three material and the later Sophocles and '
       'Herodotus notices. The source ends καλου- and Source Library completes καλουμένης, so that whole '
       'digital word is held. The Qwen3.6 prefix is the repeated author running header above the body.'),
 161: (4162,
       4162,
       'Both source columns continue the Ptolemy Hephaestion notices on Alexander, Helen, and Homeric moly. '
       'The initial printed μένης continues160 καλου- and is absent from Source Library, so its unobserved '
       'prefix abstains. The final τὸν Γίγαντα is complete; small footer notes remain outside the digital '
       'body.'),
 162: (3960,
       3967,
       'Both columns continue Ptolemy Hephaestion through the book-four notices ending with Agamemnon and '
       'Palamedes. The printed final Ἕλ- is completed as Ἕλλησι by Source Library; that whole word is held. '
       'The raw Qwen3.6 author prefix is the repeated top running header.'),
 163: (3772,
       3772,
       'Both columns continue book four and begin book five of Ptolemy Hephaestion. The first printed λησι '
       'continues162 Ἕλ- but is absent from Source Library, so that unobserved prefix abstains. The final '
       'τῶν Ἕκτορος ὀστῶν is complete, with apparatus excluded.'),
 164: (3990,
       3990,
       'Both columns continue Ptolemy Hephaestion book five with the Achilles, Zeus, Homer, Odysseus, and '
       'Heracles notices. The final ἐδωρήσατο is a complete printed word and no Source Library boundary '
       'completion is voted. The small footer and repeated top author header remain outside the digital '
       'text.'),
 165: (3706,
       3706,
       'Both columns finish Ptolemy Hephaestion, preserve his quoted epigram and other authorial examples, '
       'then begin internal191 Basil of Caesarea. The final αὐτῷ is complete. The repeated multi-author '
       'running header and the small notes are outside the digital body.'),
 166: (4096,
       4096,
       'Both columns finish Basil and begin internal192 Maximus, preserving the narrative criticism and '
       'passions explanation. The digital witness ends at the complete printed ἐπινοήματα and does not claim '
       'the following printed ἀλλ’ ὁ. No apparatus enters the reviewed digital window.'),
 167: (3719,
       3719,
       'Both columns continue Maximus with the doctrinal explanation and numbered scriptural questions. The '
       'final εἰ ἄρα is complete. Quoted scriptural phrases and their numbered questions are authorial body '
       'text; the repeated book header and small reference apparatus are outside Source Library.'),
 168: (3718,
       3729,
       'Both columns finish the Maximus scriptural-question sequence and its discussion. The source ends '
       'ἠπο-; the digital final ὑπορημένα is a completed cross-leaf reading and is held as a whole word. The '
       'Qwen3.6 prefix192 author/book title is the repeated running header above the body.'),
 169: (3982,
       3993,
       'Both columns conclude the Maximus questions and letters and introduce internal193 the ascetic work. '
       'The first printed ρημένα continues168 ἠπο- and is not observed by Source Library. The source ends '
       'συγ-; the completed digital συγγραφεὺς is held. Internal193 and192(B) titles remain body.'),
 170: (4034,
       4034,
       'Both columns conclude the193 discussion and introduce internal194 the letter to Siricinus and its '
       'numbered theological arguments. Printed initial γραφεὺς continues169 συγ- and is absent from Source '
       'Library, so its unobserved prefix abstains. Final διαίρεσιν is complete; the repeated top header and '
       'footer notes remain excluded.'),
 171: (3441,
       3441,
       'The digital window follows both columns through the Maximus letters and the dialogue with Pyrrhus, '
       'ending at the complete τὸ ἀγώνισμα in the right column. The subsequent printed196 Ephraim heading '
       'and numbered-discourse opening are absent from this digital section and are not claimed by it; the '
       'digital witness abstains beyond its observed endpoint.'),
 172: (3990,
       3990,
       'Both columns continue Ephraim through his numbered discourses and criticism and begin internal197 '
       'Cassian. The digital final λόγοι β is complete; repeated top196 ΕΦΡΑΙΜ is the raw Qwen3.6 running '
       'header outside the body, while the internal197 heading remains body.'),
 173: (4001,
       4001,
       'Both columns contain Cassian and introduce internal198 the monastic lives and numbered works. The '
       'final καὶ τὸ ζ ὅτι is complete. The small footer apparatus and repeated multi-author top header are '
       'outside the Source Library body.'),
 174: (4047,
       4047,
       'Both columns finish the monastic lives, preserve internal199 John Moschus and internal200 Mark the '
       'Monk headings, and discuss the first four Mark works. The final πνεύματος is complete; repeated top '
       'author header and small footer are outside the digital body.'),
 175: (4012,
       4012,
       'Both columns continue Mark the Monk and retain internal201 Diadochus with Nilus and John of '
       'Carpathus, then internal202 Hippolytus. The final ἀγαπᾷν is complete. These internal author names '
       'are body, while the repeated running header and small footer are excluded.'),
 176: (3727,
       3727,
       'Both source columns finish Hippolytus, preserve internal203 and204 Theodoret,205 the same prophet '
       'commentary, and206 Procopius. The final κομψότερον is complete. The digital window includes the body '
       'headings in order without the small apparatus or top running header.'),
 177: (3960,
       3960,
       'Both columns preserve internal207 Procopius,208 Eulogius, and209 Dio Chrysostom with the initial '
       'criticism and discourse listing. The final standalone ὁ is printed complete. Running header and '
       'small apparatus are outside the digital body, while all internal titles stay.'),
 178: (4161,
       4161,
       'Both columns continue Dio Chrysostom discourse descriptions from the sixth through the Nicaea '
       'material. The final ἐν Νικαίᾳ is complete and the digital reading corresponds to the source body, '
       'with no header or footer included.'),
 179: (4175,
       4186,
       'Both source columns continue the Dio Chrysostom discourse list through trust and distrust. The '
       'printed final ἐζη- is completed digitally as ἐζημίωσεν; the whole final word is held from voting. '
       'The running header and small notes remain outside the digital body.'),
 180: (4158,
       4158,
       'Both columns finish Dio Chrysostom and preserve internal210 Caesarius and211 Dionysius of Aegae. The '
       'first printed μίωσεν continues179 ἐζη- but is absent from Source Library, so its unobserved prefix '
       'abstains. Final χυμῶν is complete, and the numbered opposing medical propositions are body.'),
 181: (4144,
       4152,
       'Both columns complete the Dionysius medical propositions and introduce internal212 Aenesidemus with '
       'the opening Pyrrhonian argument. The printed final εἴ- is completed as εἴρηκεν by Source Library and '
       'that word is held. Header and apparatus are outside the digital body.'),
 182: (4063,
       4063,
       'Both source columns continue Aenesidemus through the numbered book summaries and the criticism. The '
       'initial ρηκεν continues181 εἴ- and is not in the digital beginning, so its unobserved prefix '
       'abstains. Final τῆς διανοίας is complete; repeated philosophical alternatives are authorial text, '
       'not OCR loops.'),
 183: (4019,
       4019,
       'Both columns finish Aenesidemus, preserve internal213 Agatharchides with his stylistic criticism, '
       'and begin internal214 Hierocles. The final ἔριδι καὶ is complete. No repeated top author header or '
       'small apparatus is in this digital body.'),
 184: (4171,
       4171,
       'Both columns continue Hierocles on providence, Plato and Aristotle, Ammonius, and the criticism of '
       'transmigration. The final ὑπὸ is a complete printed preposition, with no word completed across the '
       'leaf. Header and footer remain outside the digital body.'),
 185: (3874,
       3874,
       'Both columns finish Hierocles and preserve internal215 John Philoponus and216 Oribasius, including '
       'the opening quotation to Julian. The final εἰς τὴν ἰατρικήν is complete. Genuine internal book '
       'titles and quotations stay in the body; the repeated top header and apparatus do not.'),
 186: (4061,
       4073,
       'Both columns continue Oribasius, preserving internal217 and218 summaries and their quoted prefaces. '
       'Source ends διακει- while the digital final διακειμένως completes the word; it is held in full. The '
       'repeated top author header and small footer are outside the digital body.'),
 187: (4066,
       4066,
       'Both columns continue Oribasius medical book summaries and disease/treatment lists. Printed initial '
       'μένως continues186 διακει- and is absent from Source Library, so the unobserved prefix abstains. '
       'Final καὶ πρὸς is complete; the long medical lists are authorial body, not apparatus.'),
 188: (3906,
       3917,
       'Both columns finish Oribasius and preserve internal219 his further epitome and220 Theon. The digital '
       'final ἀναγράφων completes printed ἀνα- and is held as a whole word. All preceding medical summaries '
       'remain body, without the small apparatus.'),
 189: (4369,
       4369,
       'Both columns finish Theon and introduce internal221 Aetius with numbered medical book summaries. '
       'Printed initial γράφων continues188 ἀνα- but is absent from Source Library, so that prefix abstains. '
       'The final τὰς is complete, with no small footer or repeated running header in the digital text.'),
 190: (4203,
       4203,
       'Both source columns continue the Aetius numbered medical-book summaries, from fevers and prognoses '
       'through head, eye, and mouth conditions. Final τὰς is complete; repeated disease clauses are '
       'authorial body, with the small footer and repeated top header outside the digital text.'),
 191: (4164,
       4164,
       'Both columns continue Aetius through respiratory, abdominal, poison, and antidote topics. The final '
       'καὶ τὴν is complete. No header or small apparatus enters the Source Library body; medical '
       'enumerations remain in their source order.'),
 192: (4217,
       4217,
       'Both columns finish the Aetius medical compendium, including the later surgical and gynecological '
       'books. The final βιβλίον is complete. The repeated ΑΕΤΙΟΥ header and the small apparatus remain '
       'outside the digital witness, while the authorial summaries are retained.'),
 193: (4157,
       4172,
       'Both columns contain the Aetius criticism and internal222 Job with allegorical scriptural '
       'interpretation. The source ends πεπυρωμέ-; digital πεπυρωμένον completes the word and is held '
       'together with its trailing quotation punctuation. Internal222 remains body; the repeated top header '
       'and small notes do not enter this window.'),
 194: (4182,
       4182,
       'Both source columns continue Job on the incarnation, creation, judgment, and renewal. Printed '
       'initial νον continues193 πεπυρωμέ- and is absent from Source Library, so the unobserved prefix '
       'abstains. The final νομοθέτε is a digital variant of a complete printed word, not a cross-leaf '
       'completion, and is retained as a variant.'),
 195: (4037,
       4037,
       'Both columns continue Job on judgment, the incarnation, and divine omnipotence. The final δυνάμεως '
       'is complete. The raw Qwen3.6 prefix ΟΙΚΟΥΜΕΝΙΚΗ ΠΡΑΓΜΑΤΕΙΑ is the repeated top running header '
       'outside the body; the Source Library window excludes the small notes.'),
 196: (4150,
       4150,
       'Both columns continue Job on omnipotence and restoration, including the prodigal-son comparison and '
       'the concluding discussion of the incarnation. The final ἀνασώσαθ is the digital reading of a '
       'complete printed abbreviated word, retained without completing or correcting it; no header or '
       'apparatus enters this window.'),
 197: (4085,
       4085,
       'Both source columns continue Job through the objections about human creation, angels, and '
       'repentance. The final βουλομένων is complete. The source contains the quoted scriptural passages and '
       'repeated argument forms as body; the top running header and small footer are outside the digital '
       'witness.'),
 198: (4181,
       4181,
       'Both columns continue Job on human and angelic nature and the incarnation, ending with the quoted '
       'angelic-creation passage and καὶ μυρία ἄλλα. That final phrase is complete, and the repeated top '
       'header and small notes are absent from the digital body.'),
 199: (4161,
       4161,
       'Both columns continue Job on instruction, revelation, Moses, and the divine lawgiver. Final '
       'ὑπερτίθεται is complete. The raw Qwen3.6 prefix ΟΙΚΟΥΜΕΝΙΚΗ ΠΡΑΓΜΑΤΕΙΑ is the repeated top running '
       'header outside the authorial body.'),
 200: (4125,
       4125,
       'Both columns continue Job on Moses, angels, the three periods, and the fifth-discourse introduction. '
       'Final τεχνίτην is complete; no cross-leaf word completion is voted, and the repeated top header and '
       'small apparatus are outside the Source Library text.'),
 201: (4273,
       4285,
       'Both columns continue Job on creation, renewal, judgment, and the baptismal command. The printed '
       'final βαπτί- is completed as βαπτίζοντες by Source Library; that whole word is held. The Qwen3.6 '
       'initial book title is the repeated running header, not a body heading.'),
 202: (4372,
       4372,
       'Both columns continue Job on the Trinity and the seraphic coal and tongs interpretation. The initial '
       'printed ζοντες continues201 βαπτί- and is absent from Source Library, so that unobserved prefix '
       'abstains. Final ὕλην is complete; the small notes are outside the digital body.'),
 203: (4188,
       4188,
       'Both columns continue Job with the seraphim, temple, numerical symbols, and six days. Final '
       'ἀσυνθέτου is complete. The initial Qwen3.6 ΟΙΚΟΥΜΕΝΙΚΗ ΠΡΑΓΜΑΤΕΙΑ prefix is the repeated top running '
       'header outside the body.'),
 204: (4203,
       4215,
       'Both columns continue Job through Trinitarian symbols and the use of Father as a divine name. The '
       'source ends ἀνε-; Source Library completes ἀνεμάθομεν and that whole final word is held. Repeated '
       'top header and small notes remain outside the digital body.'),
 205: (4122,
       4122,
       'Both columns continue Job on Father, Son, Spirit, and relational divine names. Initial printed '
       'μάθομεν continues204 ἀνε- and is absent from Source Library, so the unobserved prefix abstains. The '
       'final δένδρου is complete. Raw Qwen3.6 initial ΟΙΚΟΝΟΜΙΚΗ ΠΡΑΓΜΑΤΕΙΑ is the printed running header.'),
 206: (4279,
       4286,
       'Both columns continue Job on Spirit, scriptural names, and the revelation of Father and Son. Source '
       'ends πα- while Source Library completes πατρὸς, so the whole final word is held. The leading617R in '
       'one raw model is a marginal Latin/numeric reference and is not recast as authorial Greek.'),
 207: (3799,
       3799,
       'Both columns continue Job on the incarnation, Gospel testimony, and degrees of Trinitarian '
       'revelation. The printed first τρὸς continues206 πα- and is absent from Source Library, so its '
       'unobserved prefix abstains. The final ἀλλ’ is complete; repeated running header and small apparatus '
       'are outside the digital body.'),
 208: (4132,
       4132,
       'Both columns continue Job on the spiritual pledge, religious instruction, and interpretation of '
       'Scripture. The final αἴγλην is complete. No top header or apparatus enters the Source Library body, '
       'and the genuine opposing theological comparisons remain.'),
 209: (4347,
       4347,
       'Both columns continue Job on the obscurity of law, revelation, and guarded sacred teaching. Final '
       'εἰς is complete. The Qwen3.6 ΟΙΚΟΝΟΜΙΚΗ ΠΡΑΓΜΑΤΕΙΑ prefix is the repeated top running header outside '
       'the body; the small footer remains outside the digital text.'),
 210: (4289,
       4289,
       'Both source columns continue Job on scriptural obscurity and move into the seventh-discourse '
       'arguments. The final τούτων is complete. The digital body preserves the theological argument and '
       'excludes the repeated top running header and small critical apparatus.'),
 211: (4272,
       4281,
       'Both columns continue Job through the argument about divine persons and the beginning of the '
       'eighth-discourse angel discussion. The source ends the split ὀφθή- before212; digital ὀφθῆναι is a '
       'completed variant and is held. The Qwen3.6 ΟΙΚΟΝΟΜΙΚΗ ΠΡΑΓΜΑΤΕΙΑ prefix is the top running header.'),
 212: (4207,
       4220,
       'Both columns continue Job on angelic honor and the preaching in Hades. The literal digital initial '
       'σεθαι is the printed continuation of211 final ὀφθή- and is held from voting as a known incomplete '
       'word. The final πεπισευκότων completes printed πε- and is also held. All raw spellings remain '
       'preserved.'),
 213: (4183,
       4183,
       'Both columns continue Job through the preaching-in-Hades argument and the comparison of Jewish and '
       'Gentile hearers. The printed first πιστευκότων continues212 πε- but is absent from Source Library, '
       'so that unobserved prefix abstains. Final εἰ is complete. The Qwen3.6 initial ΟΙΚΟΝΟΜΙΚΗ ΠΡΑΓΜΑΤΕΙΑ '
       'is the running header.'),
 214: (4093,
       4093,
       'Both columns continue Job with scriptural examples on righteous and sinful hearers. A source zoom '
       'confirms the entire last printed line, including προῃτιασάμεθα Ἰουδαίους καὶ Ἕλληνας πάντας ὑφ’ '
       'ἁμαρτίαν εἶναι, belongs to this leaf; Source Library retains it even though both fresh witnesses '
       'stop earlier. Final εἶναι is complete; no footer is admitted.'),
 215: (4072,
       4086,
       'Both columns continue Job on the reconciliation of humans with God and conclude with quoted Pauline '
       'passages. The printed final δικαιω- is completed as δικαιωθέντες digitally; that whole word is held. '
       'The repeated top running header and small notes are outside the digital window.'),
 216: (4080,
       4080,
       'Both columns continue Job on peace, sinful flesh, and forgiveness. Printed first θέντες continues215 '
       'δικαιω- and is absent from Source Library, so it receives no omission vote. The digital window ends '
       'at complete τυγχάνουσιν and does not claim the following printed paragraph beginning Ἔτι δὲ through '
       'terminal ἀνα-.'),
 217: (4297,
       4310,
       'Both source columns continue Job on angelic and human salvation and the mutability of embodied life. '
       'The source ends συνεπο- while Source Library completes συνεπομένης; that whole final word is held. '
       'Initial λαβεῖν continues a prior split ἀνα-, so its known first suffix is held from digital voting '
       'as an incomplete word.'),
 218: (4148,
       4148,
       'Both source columns continue Job on embodied change, demons, and human solidarity. Printed initial '
       'μένης continues217 συνεπο- and is absent from Source Library, so that unobserved prefix abstains. '
       'Final τοῖς Ἰουδαίοις is complete; the top running header and small footer are excluded.'),
 219: (4312,
       4312,
       'Both columns continue Job on human solidarity and the differing conditions of this life and the '
       'future kingdom. The final ὑποκείμενος is complete. The repeated top book header and small critical '
       'notes are outside the digital body; full authorial scriptural comparisons remain.'),
 220: (4173,
       4173,
       'Both columns finish Job and preserve the internal223 Diodorus title and the opening argument against '
       'fate. The final τῶν is complete. The long initial Qwen3.6 multi-author book title is the repeated '
       'top running header, separate from the genuine internal223 title.'),
 221: (4177,
       4188,
       'Both columns continue Diodorus against fate on generation, change, the elements, and providence. The '
       'source ends συγ-; digital συγκχέοιτο is a completed variant and held as a whole word. The repeated '
       'top title and small apparatus remain outside the digital body.'),
 222: (4326,
       4326,
       'Both columns continue Diodorus against fate through the argument about elements, the second-book '
       'conclusion, and the opening third-book astronomical objections. Printed initial χέοιτο continues221 '
       'συγ- and is absent digitally, so that unobserved prefix abstains. Final ἀλλὰ is complete; the small '
       'apparatus is outside the digital body.'),
 223: (4220,
       4220,
       'Both columns continue Diodorus astronomical objections, discussing zodiacal houses and planetary '
       'relations. Final κοινὰ is complete. The long sequence of interrogatives is authorial body, with the '
       'separate top ΚΑΤΑ ΕΙΜΑΡΜΕΝΗΣ header and small notes outside the digital witness.'),
 224: (4193,
       4200,
       'Both columns finish the third Diodorus book and begin the fourth with climatic, Nile, regional, and '
       'botanical differences. The source ends κα-; the digital final καμήθ’ completes that split word as a '
       'variant and is held in full. Initial αν is a complete particle, not a continued-word suffix.'),
 225: (4225,
       4225,
       'Both source columns continue Diodorus on regional differences, birth, plants, animals, and divine '
       'providence. Printed initial μήλῳ continues224 κα- and is absent from Source Library, so its '
       'unobserved prefix abstains. Final ἐκ is a digital variant of the complete printed οὐκ, retained '
       'without correction; no header or small notes enter the body.')}

HELD_SUFFIXES = {133: ' συντάξαι',
 140: ' λαμπρῶν',
 146: ' θεραπείας',
 148: ' ἀποχωρήσας',
 160: ' καλουμένης',
 162: ' Ἕλλησι',
 168: ' ὑπορημένα,',
 169: ' συγγραφεὺς',
 179: ' ἐζημίωσεν.',
 181: ' εἴρηκεν',
 186: ' διακειμένως',
 188: ' ἀναγράφων,',
 193: ' πεπυρωμένον”),',
 201: ' βαπτίζοντες',
 204: ' ἀνεμάθομεν.',
 206: ' πατρὸς',
 211: ' ὀφθῆναι.',
 212: ' πεπισευκότων',
 215: ' „δικαιωθέντες',
 217: ' συνεπομένης.',
 221: ' συγκχέοιτο',
 224: ' καμήθ’'}

HELD_PREFIXES = {212: 'σεθαι. ', 217: 'λαβεῖν '}

FIRST_FRAGMENTS = {131: 'τὰ',
 134: 'τάξαι',
 141: 'πρῶν',
 147: 'πείας',
 149: 'ρήσας',
 161: 'μένης',
 163: 'λησι',
 169: 'ρημένα',
 170: 'γραφεὺς',
 180: 'μίωσεν',
 182: 'ρηκεν',
 187: 'μένως',
 189: 'γράφων',
 194: 'νον',
 202: 'ζοντες',
 205: 'μάθομεν',
 207: 'τρὸς',
 212: 'σεθαι',
 213: 'πιστευκότων',
 216: 'θέντες',
 217: 'λαβεῖν',
 218: 'μένης',
 222: 'χέοιτο',
 225: 'μήλῳ'}

REGIONS = {131: {'body': [0.035, 0.055, 0.975, 0.842],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.752, 0.975, 0.842]},
 132: {'body': [0.035, 0.055, 0.975, 0.823],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.733, 0.975, 0.823]},
 133: {'body': [0.035, 0.055, 0.975, 0.842],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.752, 0.975, 0.842]},
 134: {'body': [0.035, 0.055, 0.975, 0.831],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.741, 0.975, 0.831]},
 135: {'body': [0.035, 0.055, 0.975, 0.838],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.748, 0.975, 0.838]},
 136: {'body': [0.035, 0.055, 0.975, 0.84],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.75, 0.975, 0.84]},
 137: {'body': [0.035, 0.055, 0.975, 0.823],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.733, 0.975, 0.823]},
 138: {'body': [0.035, 0.055, 0.975, 0.826],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.736, 0.975, 0.826]},
 139: {'body': [0.035, 0.055, 0.975, 0.844],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.754, 0.975, 0.844]},
 140: {'body': [0.035, 0.055, 0.975, 0.833],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.743, 0.975, 0.833]},
 141: {'body': [0.035, 0.055, 0.975, 0.842],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.752, 0.975, 0.842]},
 142: {'body': [0.035, 0.055, 0.975, 0.853],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.763, 0.975, 0.853]},
 143: {'body': [0.035, 0.055, 0.975, 0.842],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.752, 0.975, 0.842]},
 144: {'body': [0.035, 0.055, 0.975, 0.815],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.725, 0.975, 0.815]},
 145: {'body': [0.035, 0.055, 0.975, 0.851],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.761, 0.975, 0.851]},
 146: {'body': [0.035, 0.055, 0.975, 0.846],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.756, 0.975, 0.846]},
 147: {'body': [0.035, 0.055, 0.975, 0.852],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.762, 0.975, 0.852]},
 148: {'body': [0.035, 0.055, 0.975, 0.825],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.735, 0.975, 0.825]},
 149: {'body': [0.035, 0.055, 0.975, 0.852],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.762, 0.975, 0.852]},
 150: {'body': [0.035, 0.055, 0.975, 0.834],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.744, 0.975, 0.834]},
 151: {'body': [0.035, 0.055, 0.975, 0.842],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.752, 0.975, 0.842]},
 152: {'body': [0.035, 0.055, 0.975, 0.849],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.759, 0.975, 0.849]},
 154: {'body': [0.035, 0.055, 0.975, 0.841],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.751, 0.975, 0.841]},
 155: {'body': [0.035, 0.055, 0.975, 0.858],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.768, 0.975, 0.858]},
 156: {'body': [0.035, 0.055, 0.975, 0.855],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.765, 0.975, 0.855]},
 157: {'body': [0.035, 0.055, 0.975, 0.839],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.749, 0.975, 0.839]},
 158: {'body': [0.035, 0.055, 0.975, 0.845],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.755, 0.975, 0.845]},
 159: {'body': [0.035, 0.055, 0.975, 0.833],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.743, 0.975, 0.833]},
 160: {'body': [0.035, 0.055, 0.975, 0.844],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.754, 0.975, 0.844]},
 161: {'body': [0.035, 0.055, 0.975, 0.855],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.765, 0.975, 0.855]},
 162: {'body': [0.035, 0.055, 0.975, 0.839],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.749, 0.975, 0.839]},
 163: {'body': [0.035, 0.055, 0.975, 0.787],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.6970000000000001, 0.975, 0.787]},
 164: {'body': [0.035, 0.055, 0.975, 0.841],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.751, 0.975, 0.841]},
 165: {'body': [0.035, 0.055, 0.975, 0.837],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.747, 0.975, 0.837]},
 166: {'body': [0.035, 0.055, 0.975, 0.831],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.741, 0.975, 0.831]},
 167: {'body': [0.035, 0.055, 0.975, 0.768],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.678, 0.975, 0.768]},
 168: {'body': [0.035, 0.055, 0.975, 0.758],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.668, 0.975, 0.758]},
 169: {'body': [0.035, 0.055, 0.975, 0.858],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.768, 0.975, 0.858]},
 170: {'body': [0.035, 0.055, 0.975, 0.837],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.747, 0.975, 0.837]},
 171: {'body': [0.035, 0.055, 0.975, 0.835],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.745, 0.975, 0.835]},
 172: {'body': [0.035, 0.055, 0.975, 0.835],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.745, 0.975, 0.835]},
 173: {'body': [0.035, 0.055, 0.975, 0.834],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.744, 0.975, 0.834]},
 174: {'body': [0.035, 0.055, 0.975, 0.842],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.752, 0.975, 0.842]},
 175: {'body': [0.035, 0.055, 0.975, 0.835],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.745, 0.975, 0.835]},
 176: {'body': [0.035, 0.055, 0.975, 0.839],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.749, 0.975, 0.839]},
 177: {'body': [0.035, 0.055, 0.975, 0.851],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.761, 0.975, 0.851]},
 178: {'body': [0.035, 0.055, 0.975, 0.836],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.746, 0.975, 0.836]},
 179: {'body': [0.035, 0.055, 0.975, 0.842],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.752, 0.975, 0.842]},
 180: {'body': [0.035, 0.055, 0.975, 0.853],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.763, 0.975, 0.853]},
 181: {'body': [0.035, 0.055, 0.975, 0.854],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.764, 0.975, 0.854]},
 182: {'body': [0.035, 0.055, 0.975, 0.827],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.737, 0.975, 0.827]},
 183: {'body': [0.035, 0.055, 0.975, 0.835],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.745, 0.975, 0.835]},
 184: {'body': [0.035, 0.055, 0.975, 0.849],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.759, 0.975, 0.849]},
 185: {'body': [0.035, 0.055, 0.975, 0.853],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.763, 0.975, 0.853]},
 186: {'body': [0.035, 0.055, 0.975, 0.852],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.762, 0.975, 0.852]},
 187: {'body': [0.035, 0.055, 0.975, 0.854],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.764, 0.975, 0.854]},
 188: {'body': [0.035, 0.055, 0.975, 0.847],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.757, 0.975, 0.847]},
 189: {'body': [0.035, 0.055, 0.975, 0.889],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.799, 0.975, 0.889]},
 190: {'body': [0.035, 0.055, 0.975, 0.866],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.776, 0.975, 0.866]},
 191: {'body': [0.035, 0.055, 0.975, 0.859],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.769, 0.975, 0.859]},
 192: {'body': [0.035, 0.055, 0.975, 0.865],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.775, 0.975, 0.865]},
 193: {'body': [0.035, 0.055, 0.975, 0.849],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.759, 0.975, 0.849]},
 194: {'body': [0.035, 0.055, 0.975, 0.851],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.761, 0.975, 0.851]},
 195: {'body': [0.035, 0.055, 0.975, 0.855],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.765, 0.975, 0.855]},
 196: {'body': [0.035, 0.055, 0.975, 0.853],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.763, 0.975, 0.853]},
 197: {'body': [0.035, 0.055, 0.975, 0.824],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.734, 0.975, 0.824]},
 198: {'body': [0.035, 0.055, 0.975, 0.855],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.765, 0.975, 0.855]},
 199: {'body': [0.035, 0.055, 0.975, 0.845],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.755, 0.975, 0.845]},
 200: {'body': [0.035, 0.055, 0.975, 0.85],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.76, 0.975, 0.85]},
 201: {'body': [0.035, 0.055, 0.975, 0.878],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.788, 0.975, 0.878]},
 202: {'body': [0.035, 0.055, 0.975, 0.873],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.783, 0.975, 0.873]},
 203: {'body': [0.035, 0.055, 0.975, 0.872],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.782, 0.975, 0.872]},
 204: {'body': [0.035, 0.055, 0.975, 0.863],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.773, 0.975, 0.863]},
 205: {'body': [0.035, 0.055, 0.975, 0.86],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.77, 0.975, 0.86]},
 206: {'body': [0.035, 0.055, 0.975, 0.861],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.771, 0.975, 0.861]},
 207: {'body': [0.035, 0.055, 0.975, 0.807],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.7170000000000001, 0.975, 0.807]},
 208: {'body': [0.035, 0.055, 0.975, 0.837],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.747, 0.975, 0.837]},
 209: {'body': [0.035, 0.055, 0.975, 0.874],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.784, 0.975, 0.874]},
 210: {'body': [0.035, 0.055, 0.975, 0.864],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.774, 0.975, 0.864]},
 211: {'body': [0.035, 0.055, 0.975, 0.851],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.761, 0.975, 0.851]},
 212: {'body': [0.035, 0.055, 0.975, 0.858],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.768, 0.975, 0.858]},
 213: {'body': [0.035, 0.055, 0.975, 0.854],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.764, 0.975, 0.854]},
 214: {'body': [0.035, 0.055, 0.975, 0.81],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.7200000000000001, 0.975, 0.81]},
 215: {'body': [0.035, 0.055, 0.975, 0.832],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.742, 0.975, 0.832]},
 216: {'body': [0.035, 0.055, 0.975, 0.842],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.752, 0.975, 0.842]},
 217: {'body': [0.035, 0.055, 0.975, 0.876],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.786, 0.975, 0.876]},
 218: {'body': [0.035, 0.055, 0.975, 0.846],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.756, 0.975, 0.846]},
 219: {'body': [0.035, 0.055, 0.975, 0.85],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.76, 0.975, 0.85]},
 220: {'body': [0.035, 0.055, 0.975, 0.848],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.758, 0.975, 0.848]},
 221: {'body': [0.035, 0.055, 0.975, 0.858],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.768, 0.975, 0.858]},
 222: {'body': [0.035, 0.055, 0.975, 0.874],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.784, 0.975, 0.874]},
 223: {'body': [0.035, 0.055, 0.975, 0.866],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.776, 0.975, 0.866]},
 224: {'body': [0.035, 0.055, 0.975, 0.85],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.76, 0.975, 0.85]},
 225: {'body': [0.035, 0.055, 0.975, 0.854],
       'first': [0.035, 0.055, 0.51, 0.16],
       'last': [0.5, 0.764, 0.975, 0.854]}}

IMAGE_SHAS = {131: '68204e471e2947e6576535fdf57a259390c75729ebc193c0eaf5663e5b6606f3',
 132: '3556b2efefbe19f30002a44b4c981faa05f7f98ad3bc4c255bffbd64866d182b',
 133: '834eecd73faae99c841b7614940636b5ae25bd829578b52350efc677a776c7ff',
 134: '8790768b21d984619f6313bccdff90d24a31c8ca3e86a3a700aa2bbd850e14ce',
 135: '572408a688b5803ec52a3890b1007ca87ce0dec1fe669e19e324c91aa8ff550d',
 136: '43b1f462060314af195a71857f15fae046785f843f54dea6e20a62db09c188df',
 137: 'be1021ff2c2a707a80a8f3ba6ffae0740fe75533f7b718af0c82c433012ccd22',
 138: '155d699a5f9f99d92c33f9b31f09fbf57c2d1a7cd823dbbba5c32fe6a85c143c',
 139: 'e7faf81e5f93f23ed44fa71b0ac6f298768f104bb41b2fa96ff34b3e698d4b52',
 140: 'a8ea607f40f86a0e37edd5c9b7a5b5419beb75e3b44b72c41ae11da1d168f130',
 141: '34b5dc53e34c45e5116a135edbe832284fe72fb11dcd5a1c0898dae79b82da9d',
 142: '48e498245b737be13a41cf7b82489f05b33f5b3d89d4d70263653f54e15b63a6',
 143: '5e8a3cd13b3abc5cb421539fc455216675233aa08607a92e6580afc8a8f633d1',
 144: '1afed356d7e6c03be30c97df03fdf3c97816340c9210e1accc535795040c1662',
 145: 'efe5225752e107ddb9c613b05053f8df9f17ac32fffe1f0a36205abf1ed343c9',
 146: 'df5fd6ec98e4426679b8a1a031c555e614c0f17c0940a8ff25f718b6f5570cef',
 147: 'deca29d6e05f9434775af207d02b87a7a1bd836268bd8b3b32bf26fe8bcda562',
 148: 'f6f8dd1cd91432bcfa53a355fb231c3861caa444e91e4909ff2de2c398d47556',
 149: '62e97515fbd4a6a436c73ae9dc5e32feb1a920549fd1d4295dd9346e53173960',
 150: 'c0b3be51c9ac7ca3852f8fd40cb5dc84d24460c54cf8b09f8521942403385c91',
 151: 'cc02df01c92f4519ae57b0c317adfba23fa6f5388539d07f8ca46236a2a42810',
 152: '38034b74f324d25628017823d3e6a6c03733efaf03427ac21e50d0bfdcbc60bc',
 154: '41907386a0c0e39fbb50505289747caa95e8b03ce6ab7655ffed299f364e4713',
 155: '77dcd270d21d08a18b6c6cd442083563325a948570d8980c434ac86649bd0cf4',
 156: 'dfd13eaaf6b5a3f849d621e6a86102385310f23aa12b3306387349653aa9f0d7',
 157: '891c68e75349c18c7b481d4a3ccb43022dffb873434d984db6481c82ce678bff',
 158: '92e85720988704654173cbfe67db7ba7722713174e018a8bc4d424d5914c0dfe',
 159: '4ebabfaec57f3a3a88d1a3565faba4ead4aecaa9b6eb3e77321466a96496b739',
 160: 'bd66865be3778f87c553241c5ba32a53d69c3f6baf6cfa2809b71954bc269e6b',
 161: '3cd961db426c2b412e31abce31c5397174a1280b0bb263927cdfbeb76b2e540d',
 162: '32dd990a06bb083c23d97128de3b0678fc83dfb0ccb0b6421fdeec7af39ade8b',
 163: '57ef7293f5c960a6338505ab1758aade877cad31f0fd4915bd7d3e15d9a9a253',
 164: 'b62b44364a41983523bc7542cd9864e82661d05edb42d61ee7c717831e75c86e',
 165: '5a293821ec5d630a660cd8d38d65f56742cb37f6c17149f023eccbacdcc6f431',
 166: '241097d47feff2c6b3f3597b92add5fe3f31a2348dd449411e80653086a268a3',
 167: '0910d2b5eeec458c9e3e393801842822460a351d6b1fbd0d10222c68227b9d66',
 168: '0627afe852905f108627f41db37244c2aad0a7987efc71aed28c407d978c3936',
 169: '992348dfb909dd7e105a61edb99a9aa852a68dc94a3f16b694f17b71fcc0ec67',
 170: '7ea2e34e5442dc78e2e89767c464fc8c4d80cbe7619361410e0f55017e98a08e',
 171: '9243b69d2378af60df8fbae15bbce71263e6ca28628a2588a125810341cae603',
 172: 'aa1c3a8764b057b8499e736194387124ee641a23e7579fa86251a53caefb97df',
 173: 'c4c5da9ae51c244f926b49d13bc7958f7c6e08b4c57716dcf0d451dbfd67b853',
 174: '5fc08130d68b784544e5558d9857baffaf14110c436522b2c6c95b431cdf92fd',
 175: 'f5d0d7dd87e57a16d3cf6716e180139423a5fa1759721d355b97094f1ee87132',
 176: '05717ad3a68a629c3a8775524525b1f6fab5c2ff2ff8c71ddb7c90a3eaaee670',
 177: '4f2d2350a5d008da21dbb4a5ea7cd8c3d957bac18b4020968d08f911912f5b31',
 178: '6a7ca4353964eef3e0b0e9856d2fc7290e1cbf77bb5cc1d87bbfc8c405a3d23a',
 179: 'eeeff1d52cf39c0df863b120837ea92a9148dd8e7dfd9147767d1f80d2e3f892',
 180: '1d03e2cf109ba4438b9732ba6bd059dd4015f2f2bb419aadcd61471c40bf93ae',
 181: '0323e102117b6ed5d98f5f6b11ce0a68ef800da06a281b0093580e8f56299c39',
 182: '6ae5447fb1c66565e43285767cf6501499578ee503f93990891ef238c1404bba',
 183: '6bcc1d29942d9c6d88390d40ca32c5a993bf7b02be03a9b15fb02a91e875db6c',
 184: '5582465656a4944bda352b51000d0a4ca4bc2520c73eb7f0b0fa1fa11aa6d9f6',
 185: 'deb942486d7640fc20b9feb11cc29f57260fdd26c3c3042bcef2b1689905e375',
 186: '7c77618693666e2cd3b0fce849badd0e8e6ccd634a9b110d8a8bf13aac5a0b15',
 187: '228672f6e3fc6b8ae153bf29067fa10ff26e6880bd587d54b4c1f6fe287ee4ae',
 188: '642ddd52c3497f6aa70fd27f89fc6b4a82c5f66410d1a711db619d6a1e0ea82e',
 189: 'c9928d878bd694ffe085717c9d5ef3811f7cadcf149fa74a88a2fb93b6bd4007',
 190: 'e58d8fd5f85f029090f394048395e63be6d2e2e23da9e990881b4b5ce3504b59',
 191: 'a7fa87e7b13dbef72a32c32b5762a9ba6f56ede5989fb141901f595f6c8f9a59',
 192: '756213b598acdcb27cc1af9ad83735096915e6d1db08693599ec35e238f93729',
 193: 'ce4dcf4306b48b61158ae9057d2cd358d508a08388efc7167d05f36d3f1210fc',
 194: 'aff557181f1e1756561ebe85c9a04cc6320126fff83762ebc9856f2a85edb91c',
 195: '3ea3249f354880dac514c5b532006cd4381d96d7c8f3a6d780da744ebed55ce1',
 196: 'ef418625457a55fa5e65c8d498e912539db0ed7dba63c219eeb44d7218565ba9',
 197: '8636367e71e0b90cdefa542a8d456b91ed947020908202f549ed289c6451d76d',
 198: '5bf978c8ed2bf8d11f394f13d44cf5ad6ad2744a6880d4f4475acd6defe19005',
 199: '75f575b0d039c8ff6daaaaa75c60263d0dcee8d25e5884b0dd2d33bb78746e6d',
 200: 'ff2510cb325b00449a7ece0b9fe83ff244620edd954a74ba0aedbb17bd5e5fc0',
 201: 'ad134138844e32f64f96c4dd4f9411660f24e2b5adc00f02f603ac802fd2de1f',
 202: '630a5fc9d4cf743d3ca0137b6620c5eb73d99370ba5fe6a2f826392018ff6d5d',
 203: 'ee0a27f3b04ab8d9b96268b89257d1869178c7ba537b27d1976730688587fa23',
 204: 'c8ec527480628f9070d098aa4d52f51b7d3ca8c4a0c969a32ab7ab04e361476d',
 205: 'f92ee18588845b853b8cdb6da3768e3a7de99e22efddd288371a86ba472e91ae',
 206: 'fa9a53dae9b798deab40a379314ef51ca555a051679ffc238728ab112466921f',
 207: 'b7d9018301abc29d9318655accf0caad51060c6aacbccd832a4260089934ecbf',
 208: 'cd4e4d2912c72f6c68c0d16af24943aaafd5459a082b22844feba979ed1cc115',
 209: 'ab4a88e40ffd770aa9f09bd54fcc23a10f2f44e1f8b235877b4a959e16aedf3a',
 210: '9e735b88041f58d8d73120ce76cd8ff607fe7bce552e638291ec4a30f5c7c402',
 211: '3f1132d888d3408870c53102118e5c21476d665101d23baece791fcbacd07887',
 212: 'f291da7549bd863854ccb345755ab6f5d9b2c0b8bc174749f166c068cc589a1a',
 213: 'd20e39e8499051a78797df591ed129a03a09c79ecbb459c634d95c08cebe476b',
 214: 'd70d5dd2f3b4f6ca6a9b105a21bb25458cb78c5d4eede0c2ab822e0f803e23bc',
 215: '086cd265c9655ea7add36a43d824bfd82a09625ce37bc40f6934c73d25b76443',
 216: 'efbd335374d13aee78bc706aa0911e6aae34a5d8b4c33c4b5f2418df1ca74df3',
 217: '75b19e6e378e767f3c137f4bf7864482ad09e9d43ceeaf0b9178df7c14b07def',
 218: '1adb20301bd8e6e13bda7c517cd26e89ec0bb3e5d5a5527ec5e5be7545804a8a',
 219: '059cac9ebf41fe1d62c7a2a11d442f4e59bd9277f6c2e1a1478970804e323c2b',
 220: 'ff67bb7296be095a4a8b9bedaaf674b0221d00a7ac02ae3d6556fb71616ec429',
 221: 'adf312180913fdd48e8ec1fd3e6bdbc269c436ea6f18a38f424a7988a5038b83',
 222: '7cafe136108fd14f95e9f19727e47247ebe412a53680b21c1d8599f237a13dbc',
 223: '2c712628bcb5a3b544fc91c5f3f17408d891792c9056ef3dd5cef7e5788c690c',
 224: '348dece1c141c5307e919f1456c808947f13dfd6446473adcd6744fff43f030e',
 225: 'c649a60709b51e9c88902a7d6412c5c67d3b4c368d03f2dddd8eebb111e1a4bc'}

HEADER_PREFIXES = {(131, 'Qwen/Qwen3.6-27B'): '174. 175. ΙΩΑΝΝΟΥ ΤΟΥ ΧΡΥΣΟΣΤΟΜΟΥ. ΠΑΜΦΙΛΗΣ.\n\n',
 (143, 'Qwen/Qwen3.6-27B'): 'ΔΙΗΓΗΣΕΙΣ.\n\n',
 (145, 'Qwen/Qwen3.6-27B'): 'ΔΙΗΓΗΣΕΙΣ.\n\n',
 (159, 'Qwen/Qwen3.6-27B'): 'ΚΑΙΝΗ ΙΣΤΟΡΙΑ.\n\n',
 (160, 'Qwen/Qwen3.6-27B'): '190. ΠΤΟΛΕΜΑΙΟΥ ΤΟΥ ΗΦΑΙΣΤΙΩΝΟΣ\n\n',
 (162, 'Qwen/Qwen3.6-27B'): '190. ΠΤΟΛΕΜΑΙΟΥ ΤΟΥ ΗΦΑΙΣΤΙΩΝΟΣ\n\n',
 (168, 'Qwen/Qwen3.6-27B'): '192. ΜΑΞΙΜΟΥ ΑΠΟΡΗΜΑΤΑ ΓΡΑΦΙΚΑ.\n\n',
 (172, 'Qwen/Qwen3.6-27B'): '196. ΕΦΡΑΙΜ.\n\n',
 (195, 'Qwen/Qwen3.6-27B'): 'ΟΙΚΟΥΜΕΝΙΚΗ ΠΡΑΓΜΑΤΕΙΑ.\n\n',
 (199, 'Qwen/Qwen3.6-27B'): 'ΟΙΚΟΥΜΕΝΙΚΗ ΠΡΑΓΜΑΤΕΙΑ.\n\n',
 (201, 'Qwen/Qwen3.6-27B'): 'ΟΙΚΟΥΜΕΝΙΚΗ ΠΡΑΓΜΑΤΕΙΑ.\n\n',
 (203, 'Qwen/Qwen3.6-27B'): 'ΟΙΚΟΥΜΕΝΙΚΗ ΠΡΑΓΜΑΤΕΙΑ.\n\n',
 (205, 'Qwen/Qwen3.6-27B'): 'ΟΙΚΟΝΟΜΙΚΗ ΠΡΑΓΜΑΤΕΙΑ.\n\n',
 (209, 'Qwen/Qwen3.6-27B'): 'ΟΙΚΟΝΟΜΙΚΗ ΠΡΑΓΜΑΤΕΙΑ.\n\n',
 (211, 'Qwen/Qwen3.6-27B'): 'ΟΙΚΟΝΟΜΙΚΗ ΠΡΑΓΜΑΤΕΙΑ.\n\n',
 (213, 'Qwen/Qwen3.6-27B'): 'ΟΙΚΟΝΟΜΙΚΗ ΠΡΑΓΜΑΤΕΙΑ.\n\n',
 (220, 'Qwen/Qwen3.6-27B'): '222. ΙΩΒΙΟΥ ΟΙΚΟΝΟΜΙΚΗ ΠΡΑΓΜΑΤΕΙΑ. 223. ΔΙΟΔΩΡΟΥ\n\n'}
