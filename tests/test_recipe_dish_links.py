"""The recipe -> dish linking audit: its fast match must equal the app's own (`Knowledge.find`), and the counts it
wrote must add up."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.waiter import Knowledge

spec = importlib.util.spec_from_file_location("recipe_dish_links", ROOT / "scripts" / "knowledge" / "recipe_dish_links.py")
assert spec and spec.loader
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)
KNOW = Knowledge.load(ROOT / "data" / "knowledge" / "dishes.jsonl")
LONGEST = max(len(k.split()) for k in KNOW.by_name)


def test_the_fast_match_is_the_apps_match() -> None:
    titles = ["easy beef tacos", "mushroom and sage risotto", "prosciutto chicken kabobs", "Chicken Tikka Masala",
              "pad thai with tofu", "my best salad", "peanut butter blossoms", "Hyderabadi biryani (dum)",
              "grandma's lasagna", "salmon", "", "spaghetti carbonara served with garlic bread",
              "chocolate peanut butter fudge", "peanut butter tart", "raisin bread pudding", "french dip sandwiches",
              "smoked salmon pizza", "hash brown casserole", "grilled cheese sandwich"]
    for title in titles:
        for country in (None, "Italy", "India"):
            a = KNOW.find(title, country)
            b, how = links.fast_find(KNOW, LONGEST, title, country)
            assert (a or {}).get("qid") == (b or {}).get("qid"), title
            assert (how == "none") == (b is None)


def test_the_counts_add_up() -> None:
    data = json.loads((ROOT / "data" / "knowledge" / "dish_recipe_counts.json").read_text(encoding="utf-8"))
    assert 0 < data["linked"] <= data["recipes"]
    assert sum(d["recipes"] for d in data["dishes"].values()) == data["linked"]
    assert sum(v["linked"] for v in data["by_source"].values()) == data["linked"]
    assert not set(data["dishes_without_recipes"]) & set(data["dishes"])
    assert all(sum(d["by_source"].values()) == d["recipes"] for d in data["dishes"].values())
