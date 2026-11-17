"""Regional photo source (Wikidata, native names): the pure rules (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "dish_photos"))
import fetch_regional as fr


def page(title="Dosa.jpg", lic="CC BY-SA 4.0", mime="image/jpeg", w=800, h=600, pid=1):
    return {"pageid": pid, "title": f"File:{title}", "index": pid, "imageinfo": [{
        "mime": mime, "width": w, "height": h, "thumburl": "https://upload.wikimedia.org/x/480px-a.jpg?x=1",
        "descriptionurl": f"https://commons.wikimedia.org/wiki/File:{title}",
        "extmetadata": {"LicenseShortName": {"value": lic}, "Artist": {"value": "Ann"}}}]}


def test_regions():
    assert set(fr.REGIONS) >= {"india", "japan", "spain", "mexico", "east_asia", "southeast_asia", "middle_east",
                               "africa", "latin_america", "europe"}
    assert "Pakistan" in fr.region_countries("india")
    assert fr.region_languages("japan") == ["ja"]
    assert {"hi", "ta", "en"} <= set(fr.region_languages("india"))
    with pytest.raises(ValueError):
        fr.region_countries("atlantis")


def test_sparql_query():
    q = fr.sparql_query("spain")
    assert '"Spain"@en' in q and "wdt:P495" in q and "Q746549" in q and '"ca"' in q
    assert "LANG(?nl) IN" not in fr.sparql_query("india").replace('"hi"', "") or '"en"' not in \
        fr.sparql_query("india").split("IN (")[1].split(")")[0]


def test_parse_and_match():
    j = {"results": {"bindings": [
        {"item": {"value": "http://www.wikidata.org/entity/Q1"}, "label": {"value": "Masala dosa"},
         "aliases": {"value": "Masala dosai|dosa masala"}, "native": {"value": "मसाला डोसा"},
         "img": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/Masala%20Dosa.jpg"},
         "cat": {"value": "Masala dosa"}},
        {"item": {"value": "http://www.wikidata.org/entity/Q1"}, "label": {"value": "Masala dosa"},
         "aliases": {"value": ""}, "native": {"value": ""}}]}}
    items = fr.parse_sparql(j)
    assert len(items) == 1 and items[0]["images"] == ["Masala Dosa.jpg"] and items[0]["cats"] == ["Masala dosa"]
    rec = pd.DataFrame({"recipe_id": ["a", "b", "c"], "gk": ["masala dosa", "dosa masala", "pizza"]})
    assert fr.match_recipes(rec, items) == {"Q1": ["a", "b"]}   # alias matches, unmatched "pizza" is skipped
    rec2 = pd.DataFrame({"recipe_id": ["a"], "gk": [fr.fdp.key("Masala dosas")]})
    assert fr.match_recipes(rec2, items) == {"Q1": ["a"]}        # key() singular form


def test_free_candidates():
    j = {"query": {"pages": [page(pid=1), page("B.jpg", "CC BY-NC 4.0", pid=2), page("C.jpg", "CC0", pid=3),
                             page("D.jpg", "Public domain", pid=4), page("Box of X.jpg", pid=5),
                             page("E.jpg", pid=6, w=200, h=200), page("F.svg", mime="image/svg+xml", pid=7),
                             page("G.jpg", "CC BY-ND 2.0", pid=8), page("Used.jpg", pid=9)]}}
    got = fr.free_candidates(j, {"Used.jpg"})
    assert [c["pageid"] for c in got] == [1, 3, 4]
    assert got[0]["thumb_url"] == "https://upload.wikimedia.org/x/480px-a.jpg"


@pytest.mark.parametrize("lic,ok", [("CC BY 4.0", True), ("CC BY-SA 3.0", True), ("CC0", True), ("Public domain", True),
                                    ("CC BY-NC 2.0", False), ("CC BY-ND 2.0", False), ("", False)])
def test_is_free(lic, ok):
    assert fr.is_free(lic) is ok


def test_used_titles_and_merge():
    assert fr.used_titles(["https://commons.wikimedia.org/wiki/File:A_b%C3%A9.jpg", "nonsense"]) == {"A bé.jpg"}
    a, b = {"pageid": 1}, {"pageid": 2}
    assert fr.merge_candidates([[a], [a, b]]) == [a, b]
    assert fr.merge_candidates([[a, b]], limit=1) == [a]


def test_report_totals():
    matched = {"Q1": ["a", "b"], "Q2": ["b", "c"], "Q3": ["d"]}
    t = fr.report_totals(10, matched, {"Q1": {}, "Q2": {}})
    assert t == {"photoless_recipes_in_region": 10, "matched_items": 3, "matched_recipes": 4,
                 "unmatched_recipes": 6, "items_with_accepted_photo": 2, "recipes_that_would_get_a_photo": 3}


def test_subregions_and_levels():
    assert fr.LEVELS == ("country", "subregion", "continent")
    for region in fr.REGIONS:
        assert fr.region_subregions(region)
        assert fr.region_continent(region) in fr.CONTINENTS
    for cont, cuisines, countries in fr.SUBREGIONS.values():
        assert cont in fr.CONTINENTS and countries and all(c.startswith("Q") for c in cuisines)
    assert fr.region_subregions("india") == ["south_asia"] and fr.region_continent("india") == "asia"
    assert set(fr.region_countries("india")) <= set(fr.SUBREGIONS["south_asia"][2])


def test_sparql_levels():
    sub = fr.sparql_query("india", "subregion")
    assert "wd:Q7566053" in sub and "wdt:P2012/wdt:P279*" in sub and '"Nepal"@en' in sub and "UNION" in sub
    assert '"Thailand"@en' not in sub
    cont = fr.sparql_query("india", "continent_p30", offset=3000)
    assert "wd:Q48" in cont and "wdt:P30 ?cont" in cont and "OFFSET 3000" in cont
    assert "wd:Q728206" in fr.sparql_query("india", "continent_cuisine")
    assert "wdt:P2012" not in fr.sparql_query("india")
    with pytest.raises(ValueError):
        fr.sparql_query("india", "galaxy")


def item(qid, label):
    return {"qid": qid, "label": label, "aliases": [], "native": [], "images": [], "cats": []}


def test_match_levels_order():
    rec = pd.DataFrame({"recipe_id": ["a", "b", "u"], "gk": ["dosa", "kebab", "kebab"]})
    country = rec.iloc[:2]            # the country level sees the region's recipes only
    items = {"country": [item("Q1", "Dosa")], "subregion": [item("Q1", "Dosa"), item("Q2", "Kebab")],
             "continent": [item("Q3", "Kebab")]}
    matched, source = fr.match_levels({"country": country, "subregion": rec, "continent": rec}, items)
    assert matched == {"Q1": ["a"], "Q2": ["b", "u"]}      # Q1 keeps country; Q3 finds nothing left
    assert source == {"Q1": "country", "Q2": "subregion"}
    # a continent item only matches what the earlier levels left
    items["subregion"] = [item("Q1", "Dosa")]
    matched, source = fr.match_levels({"country": country, "subregion": rec, "continent": rec}, items)
    assert source == {"Q1": "country", "Q3": "continent"} and matched["Q3"] == ["b", "u"]


def test_report_totals_by_level():
    matched = {"Q1": ["a"], "Q2": ["b", "u"], "Q3": ["c"]}
    source = {"Q1": "country", "Q2": "subregion", "Q3": "continent"}
    t = fr.report_totals(10, matched, {"Q1": {}, "Q2": {}}, source, {"u"})
    assert t["matched_recipes"] == 3 and t["recipes_that_would_get_a_photo"] == 2
    assert t["by_level"]["subregion"] == {"items": 1, "recipes": 1, "recipes_gained": 1}
    assert t["by_level"]["continent"] == {"items": 1, "recipes": 1, "recipes_gained": 0}
    assert t["unknown_origin_recipes_matched"] == 1 and t["unknown_origin_recipes_that_would_get_a_photo"] == 1
