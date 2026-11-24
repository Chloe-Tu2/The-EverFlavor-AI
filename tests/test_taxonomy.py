"""The Food Taxonomy (taxonomy.py): one checked tree with cross-links that points straight into the recipes."""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.taxonomy import TAXONOMY_FILE, load_taxonomy

TAX = load_taxonomy()
RECIPES = pd.DataFrame({
    "origin_country": ["China", "China", "Japan", "United States", "United States", "United States", "Turkey",
                       "Mexico", "Unknown"],
    "origin_region": [None, "Sichuan", None, "Louisiana", "Southern US", "Texas", None, "Oaxaca", None],
})


def test_paths_and_breadcrumbs() -> None:
    assert [n.name for n in TAX.path("cn_sichuan")] == ["World", "Asia", "East Asia", "China", "Sichuan"]
    country = TAX.ancestor("us_texas", "country")
    assert country is not None and country.name == "United States"
    assert [n.name for n in TAX.children("east_asia")] == ["China", "Japan", "South Korea", "Taiwan", "Mongolia", "North Korea"]


def test_cross_links_put_a_branch_in_two_places() -> None:
    assert "turkey" in TAX.subtree("europe") and "turkey" in TAX.subtree("mena")
    assert "morocco" in TAX.subtree("africa")          # through North Africa
    assert "mexico" in TAX.subtree("north_america") and "mexico" in TAX.subtree("latin_america")
    assert "us_texas" in TAX.subtree("us_south") and "us_texas" in TAX.subtree("us_southwest")


def test_masks_follow_the_branch() -> None:
    def picked(slug: str) -> list[int]:
        return list(RECIPES.index[TAX.mask(RECIPES, slug)])
    assert picked("east_asia") == [0, 1, 2]
    assert picked("cn_sichuan") == [1]
    assert picked("us_south") == [3, 4, 5]               # Louisiana, Southern US itself, and Texas (cross-link)
    assert picked("europe") == [6] and picked("mena") == [6]
    assert picked("world") == list(range(len(RECIPES)))
    counts = TAX.counts(RECIPES)
    assert counts["asia"] == 3 and counts["us_louisiana"] == 1 and counts["mexico"] == 1


def test_lookups() -> None:
    assert TAX.node_for("United States", "Louisiana") == "us_louisiana"
    assert TAX.node_for("Japan", None) == "japan"
    assert TAX.node_for("Atlantis") is None
    assert [n.slug for n in TAX.find("cantonese")] == ["cn_guangdong"]
    assert [n.name for n in TAX.related("japan")] == ["China", "South Korea", "Taiwan", "Mongolia", "North Korea"]


def test_every_app_country_is_in_the_tree_and_names_match_the_data() -> None:
    from everflavor.stores import COUNTRY_CUISINES
    countries = {n.name for n in TAX.nodes.values() if n.level == "country"}
    assert set(COUNTRY_CUISINES) - {"Taiwan", "Nigeria"} <= countries   # the map's countries (two with few recipes)


def test_bad_tables_are_refused(tmp_path: Path) -> None:
    good = TAXONOMY_FILE.read_text(encoding="utf-8")
    for bad_row, message in [("x,X,zone,east_asia,,", "cannot sit under"), ("y,Y,country,nowhere,,", "unknown parent"),
                             ("z,Z,planet,world,,", "unknown level")]:
        path = tmp_path / "bad.csv"
        path.write_text(good + bad_row + "\n", encoding="utf-8")
        with pytest.raises(ValueError, match=message):
            load_taxonomy(path)


def test_every_recipe_country_is_in_the_tree() -> None:
    """Notebook 13 found 38 recipe countries missing; with the data on disk, none may go missing again."""
    data = Path(__file__).resolve().parents[1] / "data" / "processed" / "recipes_test.parquet"
    if not data.exists():
        pytest.skip("no recipe data on this computer")
    countries = set(pd.read_parquet(data, columns=["origin_country"])["origin_country"].dropna()) - {"Unknown"}
    known = {n.name for n in TAX.nodes.values() if n.level == "country"}
    assert not countries - known, sorted(countries - known)


def test_the_middle_eastern_kitchen_follows_the_place_tree() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
    from themes import kitchen_countries
    kitchens = kitchen_countries(TAX)
    before = {"Lebanon", "Turkey", "Iran", "Egypt", "Saudi Arabia", "Iraq", "Palestine", "Israel", "Syria"}
    assert all(kitchens[c] == "Middle Eastern" for c in before)                 # no country lost its kitchen
    assert {"Jordan", "Yemen", "Oman", "Armenia", "Georgia"} <= set(kitchens)   # the tree's regions, and the Caucasus
    assert "Morocco" not in kitchens and TAX.node_for("Egypt") == "egypt"        # Egypt stays North Africa in the tree
