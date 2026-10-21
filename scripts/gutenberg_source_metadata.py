"""Register checked Gutenberg admissions without importing audit dependencies."""
import hashlib
import json


def admitted_sources(root):
    audit_path = root / "data/corpus_changes/gutenberg-historical/changes.json"
    if not audit_path.exists():
        return []
    audit = json.loads(audit_path.read_text())
    admitted = []
    for source in audit["admitted"]:
        corpus = root / source["corpus_path"]
        if not corpus.exists():
            continue  # An explicitly undone admission is no longer served.
        if hashlib.sha256(corpus.read_bytes()).hexdigest() != source["corpus_sha256"]:
            raise ValueError("Gutenberg admission differs from its checked audit")
        if hashlib.sha256((root / source["source_path"]).read_bytes()).hexdigest() != source["source_sha256"]:
            raise ValueError("Gutenberg source differs from its admission audit")
        admitted.append(source)
    return admitted


def register_gutenberg_editions(registry, root):
    for source in admitted_sources(root):
        if source["citation_scheme"] == "column.line":
            continue  # Owned by the checked critical-edition manifest.
        author = registry.mint_author(source["author_name"], slug=source["author"])
        aliases = {"cts": source["cts"]} if source.get("cts") else {}
        work = registry.mint_work(author, source["title"], slug=source["work"], aliases=aliases)
        registry.works[work].best_source = "open_corpus"
        registry.mint_edition(work, source["edition"], source["edition_name"], provider="gutenberg",
                              scheme=source["citation_scheme"], editor="; ".join(source["source_editors"]),
                              source=source["source_url"], license=source["license"], servable=True,
                              aliases={"gutenberg": str(source["ebook_id"])},
                              make_default=registry.works[work].default_edition is None)
        registry.add_tag(work, "language", "grc")
