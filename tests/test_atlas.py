"""The Global Culinary Atlas audit: the UN regions read from CLDR's tree, the score, the next-dish lists (ready
dishes only, the per-country cap, turns between subregions) and the committed files agreeing with the backlog."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "knowledge"))

import atlas_audit
import fetch_regions

ATLAS = ROOT / "data" / "knowledge" / "atlas"


def test_each_country_gets_its_continent_and_smallest_region() -> None:
    tree = {"150": ["155", "039"], "155": ["FR", "DE"], "039": ["IT"], "019": ["419"], "419": ["005"], "005": ["BR"]}
    names = {"150": "Europe", "155": "Western Europe", "039": "Southern Europe", "019": "Americas",
             "419": "Latin America", "005": "South America"}
    found = fetch_regions.regions(tree, names)
    assert found["FR"] == {"continent": "Europe", "subregion": "Western Europe"}
    assert found["BR"] == {"continent": "Americas", "subregion": "South America"}   # the smallest, not Latin America


def test_the_score_is_breadth_and_depth() -> None:
    rows = [{"dishes": 40, "recipes": 1}, {"dishes": 0, "recipes": 0}]
    s = atlas_audit.score(rows)
    assert s["breadth"] == 0.5 and s["depth"] == 1.0 and s["score"] == 75 and s["band"] == "good"
    assert atlas_audit.score([{"dishes": 0, "recipes": 0}])["band"] == "gap"


def test_next_dishes_take_turns_and_keep_the_cap() -> None:
    def dish(name: str, country: str) -> dict:
        return {"dish": name, "country": country, "families": [], "sources": [{}, {}]}
    place = {"A": ("X", "North"), "B": ("X", "South")}
    ready = [dish(f"a{i}", "A") for i in range(atlas_audit.PER_COUNTRY_CAP + 5)] + [dish("b1", "B")]
    out = atlas_audit.next_dishes(ready, place)
    assert [d["country"] for d in out[:2]] == ["A", "B"]                     # the two subregions take turns
    assert sum(d["country"] == "A" for d in out) == atlas_audit.PER_COUNTRY_CAP


def test_the_committed_atlas_matches_the_backlog() -> None:
    backlog = json.loads((ROOT / "data" / "knowledge" / "coverage" / "expansion_backlog.json").read_text(
        encoding="utf-8"))["dishes"]
    status = {b["wikidata"]: b["status"] for b in backlog}
    regions = json.loads((ATLAS / "regions.json").read_text(encoding="utf-8"))
    assert "Unicode" in regions["source"]["licence"]
    for f in ATLAS.glob("*_Next_500.json"):
        dishes = json.loads(f.read_text(encoding="utf-8"))["dishes"]
        assert len(dishes) <= atlas_audit.NEXT_SIZE
        assert all(status[d["wikidata"]] == "ready" for d in dishes), f.name   # never a dish to review or blocked
    review = json.loads((ATLAS / "publication_review_queue.json").read_text(encoding="utf-8"))["dishes"]
    assert len(review) == sum(s == "needs_review" for s in status.values())
    scores = json.loads((ATLAS / "coverage_scores.json").read_text(encoding="utf-8"))
    for c in scores["continents"]:
        subs = [s for s in scores["subregions"] if s["continent"] == c["continent"]]
        assert sum(s["countries"] for s in subs) == c["countries"]
