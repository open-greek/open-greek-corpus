"""Source and physical-boundary observations for Hesychius columns 259–260."""

AUDIT = "data/corpus_changes/hesychius-missing-columns"
SLUG = "hesychius-lexicography.lexicon-o"
PRIMARY = f"data/corpus/{SLUG}.jsonl"
PREDECESSOR_SHA256 = "fbcd34f636c2586b3f59ae9142e77e675e5144a7e20d2333cee70aff99a76257"
EDITION = "schmidt-1867-gap-consensus-2026-10"
REVIEW_DATE = "2026-10-24"
CAPTURE_SHA256 = "f3511900b922544cd41a809f3e306e10c015666d83b5ee28b0b16052ee83689a"
OCR_SHA256 = {
    "qwen36": "9066cbe2d36e377bc6a5338ece7880f86232cf5485a7e521de36006904e979e8",
    "qwen38": "70854e294e0d64171efbcc43dbf0de89fc654bdbb39b8648f6bde0b14abee415",
}
SOURCES = {
    "harvard": {
        "label": "Hesychius, Schmidt, editio altera, Jena 1867; Harvard copy",
        "url": "https://archive.org/details/bub_gb_R-zVabafOucC",
        "artifact_url": "https://archive.org/download/bub_gb_R-zVabafOucC/bub_gb_R-zVabafOucC.pdf",
        "filename": "bub_gb_R-zVabafOucC.pdf", "pdf_pages": 850,
        "sha256": "f3bc5890c958576109d1dcbff51aec643cc0bc51c2247b989bfd0493f07d4cd9",
        "title_page": 8, "pages": {150: [257, 258], 151: [259, 260], 152: [261, 262]},
        "regions": {259: [0.14, 0.11, 0.515, 0.698], 260: [0.535, 0.11, 0.91, 0.698]},
        "gap_page": 151, "license": "PD",
    },
    "ghent": {
        "label": "Hesychius, Schmidt, editio altera, Jena 1867; Ghent copy",
        "url": "https://archive.org/details/bub_gb_PNI9AAAAcAAJ",
        "artifact_url": "https://archive.org/download/bub_gb_PNI9AAAAcAAJ/page/n{leaf}.jpg",
        "title_page": 10, "pages": {178: [257, 258], 179: [259, 260], 180: [261, 262]},
        "gap_page": 179, "numbering": "zero-based Internet Archive leaf number",
        "regions": {259: [0.175, 0.137, 0.535, 0.696], 260: [0.56, 0.137, 0.93, 0.696]},
        "image_sha256": {
            10: "bad3b715756974c10a87f2b0d607c32cad4bc11cb75ee5bfa50a431c6110bad1",
            178: "322bc7bbad2b900f5f419bdeee840515425440179940816312a3152e405e0d0a",
            179: "4c72eb27e1e29eebb5a8fb2e3e40ed0da3d390ba432d5663e76e057348b9e931",
            180: "b5b7ada2f5609285a42d7938bd3b5db52792179a1fed5161e8156622615289e0",
        },
        "license": "PD",
    },
}
BOUNDARY = {
    "insert_after": "hesychius_masked_0149.75",
    "insert_before": "hesychius_masked_0156.1",
    "previous_columns": [257, 258], "recovered_columns": [259, 260], "next_columns": [261, 262],
    "first_entry": "αὐθέκαστος", "last_entry": "αὐλώνων",
    "next_entry": "αὐλωπίαι",
    "evidence": (
        "Both title pages identify Schmidt's 1867 editio altera, indice glossarum ethnicarum aucta. "
        "Both independent physical copies contain the continuous printed sequence 257–258, 259–260, "
        "261–262. The earlier Harvard source hesychiialexand00schmgoog omits the middle leaf after "
        "a repeated gathering. Column 259 begins αὐθέκαστος, immediately after αὐθέκαστα in 258; "
        "column 260 ends with the lemma αὐλώνων and its Euripides reference, without a printed "
        "definition in that main-text line. Column 261 starts αὐλωπίαι. Do not invent a definition "
        "or import the apparatus's alternative assignment of the preceding definitions."
    ),
}
QUALIFICATION = (
    "Recovery of the two missing main-text columns from independent Harvard and Ghent copies "
    "of the same public-domain 1867 edition. Two pinned OCR checkpoints transcribe each column "
    "from both physical copies; outputs from one checkpoint share one vote group. Contrary "
    "readings remain explicit and unresolved readings do not enter scalar lexical counts. "
    "The literal predictions, both full-page images, title pages, and neighboring boundaries "
    "remain auditable. The printed COD./HES. apparatus below the main columns is outside this "
    "bounded addition; it remains visible in retained full-page source evidence. Critical signs "
    "and Latin citations are not lexical observations, and no context n-grams are inferred from "
    "the alignment projection."
)
