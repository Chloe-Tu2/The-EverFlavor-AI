"""The graph assets (scripts/knowledge/graph_assets.py) only repeat the Food Graph: every name in the waiter's
lines is one of the dish's own graph names, every next dish is one of our dishes with a reason and evidence."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
KNOW = ROOT / "data" / "knowledge"


def read(name: str) -> dict:
    return json.loads((KNOW / name).read_text(encoding="utf-8"))


WALTER = read("walter_context.json")["dishes"]
PATHS = read("discovery_paths.json")["dishes"]
OURS = {json.loads(line)["qid"] for line in (KNOW / "dishes.jsonl").open(encoding="utf-8")}
TEMPLATES = [r"^(?P<d>.+) is a kind of (?P<n>.+)\.$", r"^Versions of (?P<d>.+) include (?P<n>.+)\.$",
             r"^If you enjoy (?P<d>.+), you may also like (?P<n>.+)\.$", r"^It is from (?P<n>.+)\.$"]


def test_every_line_is_a_template_filled_from_the_graph() -> None:
    assert WALTER
    for c in WALTER.values():
        names = {c["dish"], *c["kind_of"], *c["variants"], *c["related"], *c["places"]}
        joined = " | ".join(sorted(names, key=len, reverse=True))
        for line in c["lines"]:
            m = next((m for t in TEMPLATES if (m := re.match(t, line))), None)
            assert m, line
            rest = m.group("n")
            for n in sorted(names, key=len, reverse=True):   # remove known names; only joiners may be left
                rest = rest.replace(n, "")
            assert re.fullmatch(r"(, | and )*", rest), (line, joined)


def test_next_dishes_are_ours_with_a_reason_and_evidence() -> None:
    assert set(PATHS) == set(WALTER)
    for q, p in PATHS.items():
        for s in p["next"]:
            assert s["qid"] != q and s["qid"] in OURS   # one of our dishes or foods
            assert s["reason"] and s["evidence"] and s["relation"] in {"variant_of", "in_family", "part_of", "origin"}
        assert len({s["qid"] for s in p["next"]}) == len(p["next"])


def test_map_prep_only_names_tags_from_the_app() -> None:
    from everflavor.stores import COUNTRY_CUISINES
    prep = read("map_prep.json")
    for country, e in prep["countries"].items():
        assert e["cuisine_tag"] == COUNTRY_CUISINES.get(country, "")
    assert not set(prep["place_tags_without_a_country"]) & set(COUNTRY_CUISINES.values())


def test_new_cuisine_tags_are_unique_and_ambiguous_words_are_not_shop_hints() -> None:
    from everflavor.stores import COUNTRY_CUISINES, NAME_HINTS, NOT_NAME_HINTS
    words = list(COUNTRY_CUISINES.values())
    assert len(words) == len(set(words))                       # one country per tag
    assert NAME_HINTS.get("polish") != "polish" and "swiss" not in NAME_HINTS and "irish" not in NAME_HINTS
    assert NAME_HINTS["portuguese"] == "portuguese"            # a plain cuisine word still hints
    assert NOT_NAME_HINTS <= set(words)
