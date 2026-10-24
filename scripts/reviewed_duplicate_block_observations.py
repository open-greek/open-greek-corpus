"""Reviewed physical boundaries for the Cyril and Hesychius duplicate repair.

These observations authorize a collation, not a preferred OCR transcription.
All source readings remain literal witnesses, including their errors.
"""

AUDIT = "data/corpus_changes/reviewed-duplicate-blocks"
CYRIL = "cyrillus-theology.commentarii-in-joannem"
HESYCHIUS = "hesychius-lexicography.lexicon-o"
INPUTS = {
    f"data/corpus/{CYRIL}.jsonl": "5b09b93a6f6753b35f5c2e230088b2e5e13174e853bf3b5845e1f316db4109cd",
    f"data/corpus/{HESYCHIUS}.jsonl": "a33565ffd995674f3d30171658f81ddb069660f8f63e78c8ac40652f016e75b9",
    "data/reference/calfa-pg73/PG073_text.txt.gz": "61b8dde6ec8da1cdedb456150fbbd16cd7a6994e60afa34acd4581cb279514f9",
}
CALFA_RAW_SHA256 = "353b31b6ca09f0e1639267da976e13171b8426352ea2d8ba648a1d1c43758104"
UPSTREAM_TEXTS = ({
    "label": "Calfa Patrologia Graeca 73 text, revision 5895ab908dd4cac5ee06cfc0e36f2ef77723e143",
    "url": "https://raw.githubusercontent.com/calfa-co/Patrologia-Graeca/5895ab908dd4cac5ee06cfc0e36f2ef77723e143/PG073/PG073_text.txt",
    "sha256": CALFA_RAW_SHA256, "license": "CC-BY-4.0",
    "local_artifact": "data/reference/calfa-pg73/PG073_text.txt.gz",
},)
SOURCES = (
    {"id": "cyril-pg73", "label": "Patrologia Graeca 73, Cyril's Commentary on John, reference scan",
     "url": "https://archive.org/details/patrologiaecurs43hopfgoog",
     "artifact_url": "https://archive.org/download/patrologiaecurs43hopfgoog/patrologiaecurs43hopfgoog.pdf",
     "filename": "patrologiaecurs43hopfgoog.pdf", "pdf_pages": 575,
     "sha256": "9de7832e644fd6f9436f15b51c940f7601738a90339c29f3350210ffad2802ab"},
    {"id": "hesychius", "label": "Hesychii Alexandrini lexicon, Schmidt edition, source scan",
     "url": "https://archive.org/details/hesychiialexand00schmgoog",
     "artifact_url": "https://archive.org/download/hesychiialexand00schmgoog/hesychiialexand00schmgoog.pdf",
     "filename": "hesychiialexand00schmgoog.pdf", "pdf_pages": 882,
     "sha256": "aaa3e3e2c8d83e8f2f7e1c1a1ecc84236855be83db80afeaa1685290c23678aa"},
)
REVIEW_DATE = "2026-10-24"
RENDERER_VERSION = "1.28.2"
RENDER_SCALE = 1.3

# Calfa marker numbers are extraction labels, not the printed PG columns.
GROUPS = tuple({
    "key": f"cyril:PG073.{page}", "slug": CYRIL,
    "locus": f"reviewed-duplicate.PG073.{page}",
    "lanes": ((f"PG073.{page}",), (f"PG073.{page + 4}",)),
    "vote_group": "calfa-pg73-5895ab908dd4",
    "source": "cyril-pg73", "pdf_pages": (page + 36,),
    "printed_columns": (955 + (page - 483) * 2, 956 + (page - 483) * 2),
    "insert_before": f"PG073.{page}",
    "evidence": (
        "Both extraction markers repeat the same continuous commentary on the same printed leaf. "
        "The neighboring reference leaves, including the end of printed column 961 and start of 964, "
        "establish the reading sequence. The four repeated blocks are collated once; neither OCR "
        "reading is promoted to an independent source vote."
    ),
} for page in range(483, 487)) + ({
    "key": "hesychius:0143-0150", "slug": HESYCHIUS,
    "locus": "reviewed-duplicate.hesychius.0150",
    "lanes": (tuple(f"hesychius_masked_0143.{line}" for line in range(1, 39)),
              tuple(f"hesychius_masked_0150.{line}" for line in range(1, 74))),
    "vote_group": "qwen36-hesychius_schmidt_masked",
    "source": "hesychius", "pdf_pages": (143, 144, 150),
    "printed_columns": (247, 248), "insert_before": "hesychius_masked_0143.1",
    "evidence": (
        "PDF frames 143, 144, and 150 reproduce printed columns 247–248. The 143 reading contains "
        "38 lines from the left column; 150 contains those lines plus 35 additional lines. The "
        "collation belongs before the retained 145 reading of columns 249–250. Frames 151–155 "
        "repeat 145–149 physically but have no current corpus rows. Preserve the additional "
        "right-column reading and every contrary OCR reading."
    ),
},)

PHYSICAL_SEQUENCE = {
    "cyril-pg73": [
        {"pdf_page": p, "printed_columns": [953 + 2 * (p - 518), 954 + 2 * (p - 518)],
         "role": "context" if p in (518, 523) else "collated-leaf"} for p in range(518, 524)],
    "hesychius": [
        {"pdf_page": p, "printed_columns": cols,
         "primary_rows": count, "role": "collated-leaf" if p in (143, 150) else "context"}
        for p, cols, count in (
            (142, [245, 246], 55), (143, [247, 248], 38), (144, [247, 248], 0),
            (145, [249, 250], 59), (146, [251, 252], 49), (147, [253, 254], 66),
            (148, [255, 256], 50), (149, [257, 258], 75), (150, [247, 248], 73),
            (151, [249, 250], 0), (152, [251, 252], 0), (153, [253, 254], 0),
            (154, [255, 256], 0), (155, [257, 258], 0), (156, [261, 262], 45),
            (157, [263, 264], 34), (158, [265, 266], 51))],
}
QUALIFICATION = (
    "A source-reviewed structural collation of repeated extraction blocks. Repeated readings "
    "of one source share one vote group; contrary readings remain explicit and unresolved slots "
    "do not enter scalar lexical counts. One-sided text outside the partial witness is retained. "
    "The display is a Greek-word projection, not a punctuation-preserving transcription; every "
    "literal original row remains citable in secondary storage and the reversible archive. "
    "No new OCR or source-based spelling corrections are made. The Hesychius scan itself jumps "
    "from printed columns 257–258 to 261–262 after its repeated gathering; this repair does not "
    "claim to supply the absent printed columns 259–260."
)

# Full-page RGB PNG evidence, rendered by the pinned renderer at scale 1.3.
RETAINED_IMAGES = (
    ('cyril-pg73', 518, '532b281d30a9c333d61328819678a8c84730eb45fc5d34d05ec4b77aea5c620b'),
    ('cyril-pg73', 519, '874524c438ef4fc84066131923af160ecd09422679f1d9d85187bae8a0fa01d9'),
    ('cyril-pg73', 520, 'a7980df8b0f69d2c2d59e0983a323523c27d1119e5bff1f4db13b4a420bf132e'),
    ('cyril-pg73', 521, '66d5303f9a3db56fe18c2fe4398da18efe08b532a058cabbe80206f9b86f99f6'),
    ('cyril-pg73', 522, '4b811286b1e33e5f5d4356a00644d41334888735fcd27667a41073d200b17109'),
    ('cyril-pg73', 523, '89d35ee28700721872e817b2892fad51e3cd9f35620dfb2a11da0d28dd2ab35d'),
    ('hesychius', 8, 'a478d585ec0e89a99776de5a7c994423ec0b8933cdba6a872f6488b6051fcbae'),
    ('hesychius', 142, '4e93528d2047d343e93b9180ff33bc89d1f85b06613ad7853d612fa5ba502450'),
    ('hesychius', 143, 'a5d26084798683a8097e2c8b00cffed222151eddbcd43cd37618067bd25b39e4'),
    ('hesychius', 144, '8d44d82b9c4138b682b883505865eed239ac13b09941f5845feac87215f650f9'),
    ('hesychius', 145, '7d47bae548612d2b445f9a51135f1adfe38065885fb68888cc523071014edb74'),
    ('hesychius', 146, '78a784f74eb658e1ae527922585f5e564040e5b76624a91b3a99ec101abf92d3'),
    ('hesychius', 147, 'b741275e4955fff0462f558332e29c36b9c90eb38d0524fa6ab7a7a23a9ff33f'),
    ('hesychius', 148, 'be52215b3a64f0b18fa71dad7b242e62f5e50967a6fd5d8087583db0d6d37f51'),
    ('hesychius', 149, '1be092083cf990756e4d75bd687a77bf417025a710bd819d78db206d91dc48af'),
    ('hesychius', 150, 'd29d798c2cebb29a37f254e883554e4529e51e05904b48cb23fef8ff12520758'),
    ('hesychius', 151, '084be279c79ea7bce966229dfcf15a291130c56034ae393b7d4c2403129da586'),
    ('hesychius', 152, '353a36e3946555fd2489f6de9e441b3e141e7d0961ac36319d345983606cdb96'),
    ('hesychius', 153, '5b11c6a4211948e83fc394dc9769e8850fa8368cc026e9484eca08aefebc23ab'),
    ('hesychius', 154, '8c8dceaff87fe45a8192ccbd5b444fa3cf67da48d7d471d9b0cebf7d5ac4ece9'),
    ('hesychius', 155, '83d27b57af69671fce4561449404ffc0812143bee62672102c6c47784ac5ccfe'),
    ('hesychius', 156, 'ba89d3b6e4e5b7139af3e84f28d15ab96ea34cae1979234282e4cf77a0cbd38d'),
    ('hesychius', 157, '2d00e86a9728606dc3ff16547d899a3ebda68a300218d1c504135093820ffcc7'),
    ('hesychius', 158, '0dcd4430e8b5da73bd809a7911a981125c484c8f55f6e5ab3e8380e4838c4c70'),
)
