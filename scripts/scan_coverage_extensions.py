"""Load reviewed scan additions without losing them on a TEI rebuild."""
import hashlib
import json
from pathlib import Path


def reading_digest(rows):
    selected = [{key: row.get(key) for key in ("locus", "text", "source", "edition")}
                for row in rows]
    return hashlib.sha256(json.dumps(selected, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def combine_rows(work, base, extensions):
    """Keep each old book's order while inserting newly supplied books before it."""
    def key(pair):
        position, row = pair
        if work == "cassius-dio.historiae-romanae":
            if row["locus"].startswith("cary-v"):
                volume = int(row["locus"].split("-")[1][1:])
                return (0 if volume < 3 else 2, volume, row["printed_page"], position)
            return (1, 0, 0, position)
        book = int(row["locus"].split(".")[0])
        return (book, 0, row.get("printed_page", 0), position)
    return [row for position, row in sorted(enumerate(base + extensions), key=key)]


def load_extensions(root: Path, work: str, existing_loci=(), base_rows=None):
    index = root / "data/corpus_extension_index.json"
    if not index.exists():
        return []
    entry = json.loads(index.read_text()).get("works", {}).get(work)
    if not entry:
        return []
    if entry.get("base_readings_sha256") and (base_rows is None or
            reading_digest(base_rows) != entry["base_readings_sha256"]):
        raise ValueError("The base edition changed; review coverage overlap before rebuilding")
    path = Path(entry["path"])
    if path.is_absolute() or ".." in path.parts or path.parts[:2] != ("data", "corpus_extensions"):
        raise ValueError("Unsafe scan extension path")
    raw = (root / path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise ValueError("Scan extension changed outside its reviewed importer")
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    loci = set(existing_loci)
    for row in rows:
        if row["urn"] != work or row["locus"] in loci:
            raise ValueError("Scan extension has a wrong work or repeated citation")
        loci.add(row["locus"])
    return rows
