"""Tests for the ingredient knowledge of notebook 04 (src/everflavor/knowledge.py).

No request leaves the computer: requests.get and time.sleep are replaced. Run
from the project folder with `python -m pytest tests`, or this file alone:

    python tests/test_knowledge.py
"""
import gzip
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import knowledge
from everflavor.knowledge import (
    foodkeeper_table,
    ingredient_pairings,
    match_shelf_life,
    names_in_languages,
    substitution_effects,
    substitutions_from_reviews,
    wikidata_matches,
)


class FakeResponse:
    """The parts of requests.Response the helpers use."""

    def __init__(self, status: int = 200, body: object = None, content: bytes = b"", headers: dict | None = None):
        self.status_code = status
        self.ok = status < 400
        self._body = body
        self.content = content
        self.headers = headers or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture
def fake_net(monkeypatch):
    """Replace requests.get with a queue of answers; record every call; never sleep."""
    calls: list[dict] = []
    answers: list[object] = []

    def fake_get(url, params=None, **kwargs):
        calls.append({"url": url, "params": params, **kwargs})
        return answers.pop(0)

    monkeypatch.setattr(knowledge.requests, "get", fake_get)
    monkeypatch.setattr(knowledge.time, "sleep", lambda *_: None)
    return calls, answers


# ------------------------------------------------------------------ pairings
def test_pairings_score_pairs_seen_together_more_than_by_chance():
    recipes = pd.DataFrame({
        "ingredient_list": [["basil", "tomato"]] * 4 + [["soy sauce", "ginger"]] * 4 + [["tomato", "ginger"]] * 2,
        "cuisine_family": ["European"] * 4 + ["Asian"] * 4 + ["Other"] * 2,
    })
    out = ingredient_pairings(recipes, min_recipes=2)
    basil = out[(out.ingredient_a == "basil") & (out.ingredient_b == "tomato")].iloc[0]
    assert basil.n_recipes == 4 and basil.scope == "all"
    assert basil.pmi == pytest.approx(round(math.log2((4 / 10) / ((4 / 10) * (6 / 10))), 3))
    assert (out.ingredient_a < out.ingredient_b).all()                     # each pair once, alphabetical
    by_family = ingredient_pairings(recipes, "cuisine_family", min_recipes=2)
    assert set(by_family.scope) == {"European", "Asian"}                  # "Other" is not a cuisine
    assert ingredient_pairings(recipes, min_recipes=50).empty


# ------------------------------------------------------------------ substitutions
def test_substitutions_need_the_original_in_the_recipe():
    recipes = pd.DataFrame({"recipe_id": ["foodcom_1", "foodcom_2", "hf_3"],
                            "ingredient_list": [["sour cream", "onion"], ["butter", "flour"], ["sugar"]]})
    reviews = pd.DataFrame({"recipe_id": [1, 1, 2, 2, 2], "rating": [5, 4, 5, 0, 5], "review": [
        "Great! I used Greek yogurt instead of the sour cream and it was lighter.",
        "used greek yogurt instead of sour cream",
        "I replaced the butter with olive oil.",
        "Substituted olive oil for butter, worked fine",
        "I used less time instead of the full hour",                       # "full hour" is not in the recipe
    ]})
    out = substitutions_from_reviews(reviews, recipes, min_reviews=2).set_index(["original", "substitute"])
    assert set(out.index) == {("sour cream", "greek yogurt"), ("butter", "olive oil")}
    assert out.loc[("sour cream", "greek yogurt"), "n_reviews"] == 2
    assert out.loc[("butter", "olive oil"), "mean_rating"] == 5.0          # a 0 rating means no rating
    effects = substitution_effects(out.reset_index()).set_index("original")
    assert effects.loc["butter", "flags_removed"] == "contains_dairy"
    assert knowledge._clean_substitute("half and half for the milk") == "half-and-half"


# ------------------------------------------------------------------ shelf life
def _foodkeeper_json() -> dict:
    def row(**cells):
        return [{k: v} for k, v in cells.items()]
    return {"fileName": "x", "sheets": [
        {"name": "Category", "data": [row(ID=7.0, Category_Name="Dairy Products & Eggs", Subcategory_Name=None)]},
        {"name": "Product", "data": [
            row(ID=1.0, Category_ID=7.0, Name="Milk", Name_subtitle="plain or flavored", Keywords="Milk",
                Refrigerate_Min=1.0, Refrigerate_Max=1.0, Refrigerate_Metric="Weeks",
                Freeze_Min=3.0, Freeze_Max=3.0, Freeze_Metric="Months", Pantry_Metric="Not Recommended"),
            row(ID=2.0, Category_ID=7.0, Name="Kefir", Name_subtitle=None, Keywords="Kefir,milk",
                Refrigerate_Min=5.0, Refrigerate_Max=7.0, Refrigerate_Metric="Days"),
            row(ID=3.0, Category_ID=7.0, Name="Cheese", Name_subtitle=None, Keywords="Cheese",
                Pantry_tips="Keep cold."),
        ]},
    ]}


def test_foodkeeper_table_and_matching(tmp_path):
    path = tmp_path / "foodkeeper.json"
    path.write_text(json.dumps(_foodkeeper_json()), encoding="utf-8")
    table = foodkeeper_table(path)
    milk = table[table.foodkeeper_id == 1].set_index("storage")
    assert milk.loc["fridge", "max_days"] == 7 and milk.loc["freezer", "min_days"] == 90
    assert milk["min_days"].isna()["pantry"] and milk.loc["pantry", "unit"] == "Not Recommended"
    assert milk.loc["fridge", "name"] == "Milk (plain or flavored)"
    assert table[table.foodkeeper_id == 3].iloc[0]["tip"] == "Keep cold."
    matches = match_shelf_life(["milk", "kefir", "cheddar cheese", "saffron"], table).set_index("ingredient")
    assert matches.loc["milk", "foodkeeper_id"] == 1 and matches.loc["milk", "match"] == "name"   # not kefir
    assert matches.loc["cheddar cheese", "match"] == "head"
    assert "saffron" not in matches.index


def test_download_foodkeeper_falls_back_to_the_archive(fake_net, tmp_path):
    calls, answers = fake_net
    body = json.dumps(_foodkeeper_json()).encode()
    answers.extend([FakeResponse(403, content=b"Access Denied"), FakeResponse(200, content=gzip.compress(body))])
    path = knowledge.download_foodkeeper(tmp_path)
    assert json.loads(path.read_text(encoding="utf-8")) == _foodkeeper_json()    # saved decompressed
    assert [c["url"] for c in calls] == [knowledge.FOODKEEPER_URL, knowledge.FOODKEEPER_ARCHIVE_URL]
    assert knowledge.download_foodkeeper(tmp_path) == path and len(calls) == 2     # reused, not downloaded again
    answers.extend([FakeResponse(403), FakeResponse(404)])
    with pytest.raises(RuntimeError):
        knowledge.download_foodkeeper(tmp_path / "other")


# ------------------------------------------------------------------ Wikidata
def _bindings(rows):
    return {"results": {"bindings": [{k: {"value": v} for k, v in r.items()} for r in rows]}}


def test_wikidata_matches_prefer_food_labels_and_cache_answers(fake_net, tmp_path):
    calls, answers = fake_net
    answers.append(FakeResponse(200, _bindings([
        {"name": "egg", "item": "http://www.wikidata.org/entity/Q29710185", "kind": "label",
         "description": "protein-coding gene in the species Drosophila melanogaster"},
        {"name": "egg", "item": "http://www.wikidata.org/entity/Q93189", "kind": "label",
         "description": "edible animal product"},
        {"name": "cilantro", "item": "http://www.wikidata.org/entity/Q41611", "kind": "alias",
         "description": "species of plant used as an herb"},
    ])))
    out = wikidata_matches(["egg", "cilantro", "zzz"], tmp_path).set_index("ingredient")
    assert out.loc["egg", "wikidata_id"] == "Q93189" and out.loc["egg", "match"] == "exact"
    assert out.loc["cilantro", "wikidata_id"] == "Q41611"
    assert out.loc["zzz", "match"] == "none"
    assert "EverFlavorAI" in calls[0]["headers"]["User-Agent"]
    wikidata_matches(["egg", "cilantro", "zzz"], tmp_path)                       # answered from the cache
    assert len(calls) == 1


def test_wikidata_matches_fall_back_to_the_last_words(fake_net, tmp_path):
    calls, answers = fake_net
    answers.append(FakeResponse(200, _bindings([])))                            # "ground cinnamon": nothing
    answers.append(FakeResponse(200, _bindings([
        {"name": "cinnamon", "item": "http://www.wikidata.org/entity/Q28165", "kind": "label",
         "description": "spice obtained from the inner bark of several tree species"}])))
    out = wikidata_matches(["ground cinnamon"], tmp_path).iloc[0]
    assert (out.wikidata_id, out.match) == ("Q28165", "head")
    assert "cinnamon" in calls[1]["params"]["query"]


def test_names_in_languages(fake_net, tmp_path):
    _, answers = fake_net
    answers.extend([FakeResponse(503, headers={"Retry-After": "0"}), FakeResponse(200, _bindings([
        {"item": "http://www.wikidata.org/entity/Q41611", "name": "cilantro", "lang": "es", "kind": "label"},
        {"item": "http://www.wikidata.org/entity/Q41611", "name": "dhania", "lang": "hi", "kind": "alias"},
    ]))])
    out = names_in_languages(["Q41611", None, "Q41611"], ["es", "hi"], tmp_path)   # type: ignore[list-item]
    assert out.values.tolist() == [["Q41611", "es", "cilantro", "label"], ["Q41611", "hi", "dhania", "alias"]]
    assert knowledge._quote('say "hi"') == '"say \\"hi\\""'


# ------------------------------------------------------------------ notebooks
def test_every_notebook_can_download_all_of_the_shared_code():
    """A notebook opened on its own downloads EVERFLAVOR_MODULES from GitHub: the list must name every module."""
    root = Path(__file__).resolve().parents[1]
    modules = {p.stem for p in (root / "src" / "everflavor").glob("*.py")}
    for notebook in sorted((root / "notebooks").glob("0*.ipynb")):
        cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
        setup = next("".join(c["source"]) for c in cells if "EVERFLAVOR_MODULES = [" in "".join(c["source"]))
        listed = set(re.findall(r'"(\w+)"', setup.split("EVERFLAVOR_MODULES = [")[1].split("]")[0]))
        assert listed == modules, f"{notebook.name}: missing {sorted(modules - listed)}, extra {sorted(listed - modules)}"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
