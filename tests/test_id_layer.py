"""Tests for the opaque-id ledger mechanics (scripts/build_id_registry.py).

These exercise the Ledger class directly on synthetic slugs, so they do not
depend on the real corpus. They pin the identity invariants: append-only
minting, id-preserving renames (live + historical), and tombstoning that never
recycles an id.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_id_registry import Ledger, _fmt_id  # noqa: E402


def new_ledger():
    return Ledger("ogc")


def test_mint_is_sequential_and_zero_padded():
    L = new_ledger()
    L.mint_missing({"b.two", "a.one", "c.three"})
    L.refresh_status({"b.two", "a.one", "c.three"})
    # deterministic: sorted slug order at genesis
    assert L.current_slug_to_id() == {
        "a.one": "ogc000001", "b.two": "ogc000002", "c.three": "ogc000003"}


def test_mint_is_append_only():
    L = new_ledger()
    L.mint_missing({"a.one", "b.two"})
    before = dict(L.entries)
    # re-running over the same universe mints nothing
    assert L.mint_missing({"a.one", "b.two"}) == []
    assert L.entries == before
    # a new slug gets the next id, never disturbing existing ones
    minted = L.mint_missing({"a.one", "b.two", "d.four"})
    assert minted == ["ogc000003"]
    assert L.current_slug_to_id()["a.one"] == "ogc000001"


def test_live_rename_preserves_id():
    L = new_ledger()
    L.mint_missing({"a.one", "b.two"})
    # rename a.one -> a.renamed while its id still owns the old slug
    L.apply_renames([{"from": "a.one", "to": "a.renamed"}])
    e = L.entries["ogc000001"]
    assert e["slug"] == "a.renamed"
    assert e["former_slugs"] == ["a.one"]
    # the old slug still resolves to the same id (the redirect)
    assert L.slug_to_id()["a.one"] == "ogc000001"


def test_historical_alias_attaches_after_mint():
    L = new_ledger()
    # the old slug was retired before the ledger existed: only the new slug is
    # minted, and the rename attaches the old slug as a former_slug.
    L.mint_missing({"a.new"})
    L.apply_renames([{"from": "a.old", "to": "a.new"}])
    assert L.entries["ogc000001"]["former_slugs"] == ["a.old"]
    assert L.slug_to_id()["a.old"] == "ogc000001"


def test_rename_is_idempotent():
    L = new_ledger()
    L.mint_missing({"a.one"})
    L.apply_renames([{"from": "a.one", "to": "a.renamed"}])
    snapshot = {i: dict(e) for i, e in L.entries.items()}
    # applying the same rename again changes nothing
    L.apply_renames([{"from": "a.one", "to": "a.renamed"}])
    assert L.entries == snapshot


def test_tombstone_never_recycles_id():
    L = new_ledger()
    L.mint_missing({"a.one", "b.two"})
    # b.two leaves the served set -> retired, not deleted
    L.refresh_status({"a.one"})
    assert L.entries["ogc000002"]["status"] == "retired"
    assert L.entries["ogc000001"]["status"] == "served"
    # a brand-new work gets ogc000003, NOT the freed ogc000002
    minted = L.mint_missing({"a.one", "c.three"})
    assert minted == ["ogc000003"]


def test_rename_conflict_does_not_merge():
    L = new_ledger()
    L.mint_missing({"a.one", "b.two"})
    # both slugs are live, distinct works -> refuse to merge on rename
    msgs = L.apply_renames([{"from": "a.one", "to": "b.two"}])
    assert any("CONFLICT" in m for m in msgs)
    assert L.current_slug_to_id()["a.one"] == "ogc000001"
    assert L.current_slug_to_id()["b.two"] == "ogc000002"


def test_id_format():
    assert _fmt_id("ogc", 17) == "ogc000017"
    assert _fmt_id("oga", 1) == "oga000001"
