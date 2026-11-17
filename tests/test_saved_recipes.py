"""Saved recipes in the browser: the round trip, and that untrusted storage can't break or flood the app."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import saved_recipes as sr

ENTRY = {"name": "Tacos al pastor", "lines": ["450 kcal, 25 g protein, from Mexico", "Ingredients: pork, pineapple"]}


def test_round_trip_keeps_entries_and_date():
    text = sr.encode({"r1": ENTRY}, today="2026-11-11")
    back = sr.decode(text)
    assert back == {"r1": {**ENTRY, "saved_on": "2026-11-11"}}
    assert sr.decode(sr.encode(back, today="2030-01-01"))["r1"]["saved_on"] == "2026-11-11"


def test_bad_storage_loads_nothing():
    for text in (None, "", "not json", "[]", '{"app": "other", "recipes": {}}', '{"app": "everflavor"}',
                 '{"app": "everflavor", "recipes": []}', "x" * (sr.MAX_BYTES + 1)):
        assert sr.decode(text) == {}


def test_malformed_entries_are_left_out_and_text_is_capped():
    recipes = {"ok": ENTRY, "no-name": {"lines": ["a"]}, "no-lines": {"name": "x", "lines": []},
               "bad-lines": {"name": "x", "lines": [1, None]}, "": ENTRY, "list": ["x"],
               "long": {"name": "n" * 999, "lines": ["l" * 9999] * 50, "saved_on": {"x": 1}}}
    back = sr.decode(json.dumps({"app": "everflavor", "recipes": recipes}))
    assert set(back) == {"ok", "long"}
    assert len(back["long"]["name"]) == sr.MAX_NAME
    assert len(back["long"]["lines"]) == sr.MAX_LINES and len(back["long"]["lines"][0]) == sr.MAX_LINE
    assert "saved_on" not in back["long"]


def test_count_is_capped_and_merge_prefers_this_visit():
    many = {f"r{i}": ENTRY for i in range(sr.MAX_RECIPES + 50)}
    assert len(sr.decode(json.dumps({"app": "everflavor", "recipes": many}))) == sr.MAX_RECIPES
    mine = {"r1": {**ENTRY, "name": "Mine"}}
    assert sr.merge(mine, {"r1": ENTRY, "r2": ENTRY})["r1"]["name"] == "Mine"
    assert len(sr.merge({}, many)) == sr.MAX_RECIPES
