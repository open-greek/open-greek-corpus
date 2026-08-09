"""A carve has to publish the TLG id it claims, not just record it.

carve_edition_volume.py carved nine Walz volumes and wrote each work's TLG id
into its audit and nowhere else. Six works therefore published with no external
anchor while the plan had identified them all along, and nobody noticed for
months because every check the repo runs was still green: the id was present in
the plan, present in the audit, and absent from the one file a reader joins on.

So these test the property that was missing, not the code path that was wrong.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import carve_edition_volume as cev  # noqa: E402
import carve_cgpg_volume as ccv  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def test_every_walz_work_with_a_tlg_is_in_the_crosswalk():
    """The regression itself. Re-running the registration over the applied
    plan must add nothing, which is only true if everything the plan claims is
    already published."""
    plan = json.loads((REPO / "data" / "walz_carve_plan.json")
                      .read_text(encoding="utf-8"))
    vols = plan["volumes"] if isinstance(plan, dict) and "volumes" in plan else plan
    cw = json.loads((REPO / "data" / "tlg_crosswalk.json")
                    .read_text(encoding="utf-8"))
    missing = []
    for v in (vols if isinstance(vols, list) else vols.values()):
        for w in (v.get("works", []) if isinstance(v, dict) else []):
            if w.get("tlg") and w.get("rank", "primary") != "secondary":
                if w["slug"] not in cw:
                    missing.append((w["slug"], w["tlg"]))
    assert missing == [], f"carved works claiming a TLG id but absent from the crosswalk: {missing}"


def test_both_carve_scripts_register_anchors():
    """The gap was that one carve script had this and the other did not."""
    assert hasattr(cev, "update_crosswalk")
    assert hasattr(ccv, "update_crosswalk")


def test_a_work_with_no_tlg_is_skipped_not_guessed():
    before = json.loads((REPO / "data" / "tlg_crosswalk.json")
                        .read_text(encoding="utf-8"))
    added = cev.update_crosswalk({"works": [
        {"slug": "nothing.doing", "tlg": None, "title": "x"}]})
    assert added == []
    after = json.loads((REPO / "data" / "tlg_crosswalk.json")
                       .read_text(encoding="utf-8"))
    assert after == before


def test_an_id_another_slug_already_holds_is_refused():
    cw = json.loads((REPO / "data" / "tlg_crosswalk.json")
                    .read_text(encoding="utf-8"))
    taken = next((v["tlg"] for v in cw.values()
                  if isinstance(v, dict) and v.get("tlg")), None)
    assert taken, "expected the crosswalk to hold at least one tlg id"
    with pytest.raises(SystemExit, match="already claimed by"):
        cev.update_crosswalk({"works": [
            {"slug": "brand.new-slug", "tlg": taken, "title": "x"}]})
