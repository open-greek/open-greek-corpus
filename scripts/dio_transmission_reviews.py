"""Qualify late Cary transmission without changing immutable OCR requests."""
SOURCE = "e7c88e1f1cbd7be0a7d8b3ea4d3e2583733e0101b284dae00940c6e2073a6576"
PINS = {
    8: "c9ad3d5aed55f35259c30d16583880041d25a67b737294fe8d6711adc6f988e3",
    9: "f71fb53d3b4fa4894947148f7fdf018739c746b3d413c9ba179176b17cb70db4",
}


def reviewed_transmission(page, source):
    volume = page.get("source_volume")
    if (page["work"] != "cassius-dio.historiae-romanae" or volume not in PINS
            or page.get("admission") == "comparative-paratext"):
        return None
    if source["sha256"] != PINS[volume]:
        raise ValueError("The reviewed late Dio transmission source changed")
    label = "epitome-and-excerpts" if volume == 8 else "mixed-direct-manuscript-excerpts-and-epitomes"
    evidence = {"review_id": "cary-late-transmission-2026-10-18", "reviewed_at": "2026-10-18",
        "source_kind": "edition-transmission-review", "original_value": page.get("transmission"),
        "corrected_value": label,
        "source": {"edition": "Cary volume I introduction", "sha256": SOURCE,
            "scan_pages": [15,20,24], "printed_pages": ["xvii","xxii","xxvi"],
            "reviewed_images": [
                {"scan_page": 15, "sha256": "53a022763bbf5bdf575f7d49ab47e51f4da46c39aafa485ab467cb77f695a4a3"},
                {"scan_page": 20, "sha256": "5530ab8f9a934731d9b62beeb7bbcccff846b40fc158c23315d4a7305f970649"},
                {"scan_page": 24, "sha256": "46e3176d3d538aa8c1d883903fc401aeb0f55a20b3351e605db04fa71b75e7a1"}]},
        "evidence": "Source inspection of Cary I identifies Xiphilinus as the chief authority for Books 61–80 and distinguishes the direct Vaticanus Graecus 1288 text at traditional 78.2.2–79.8.3 (reformed 79.2.2–80.8.3). Volume VIII therefore represents epitome and excerpts; IX combines those channels with surviving direct manuscript text. The queued generic direct-text label is too broad.",
        "scope": "An edition-level transmission qualification, not an attribution of every word on a page to one manuscript. Exact printed Xiphilinus, Zonaras and excerpt credits remain separate witness reference lines. Fragment quotations and comparative panels retain their distinct labels; no missing Greek is reconstructed.",
        "numbering": "Traditional and reformed book references are distinguished; do not apply a blanket numeric offset to the physical page citations."}
    return label, evidence
