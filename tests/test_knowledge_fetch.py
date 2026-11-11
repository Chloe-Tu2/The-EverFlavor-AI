"""Knowledge collector for the waiter (scripts/knowledge/fetch_knowledge.py): the pure rules (no network)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "knowledge"))
import fetch_knowledge as fk

PAGE = """
<div class="sidebar"><img src="x.png"><br>Part of a series</div>
<h2>Regional dishes</h2>
<table class="wikitable"><tr><th>Image</th><th>Name</th><th>General Region</th></tr>
<tr><td><a href="/wiki/File:Fish.jpg">pic</a></td><td><a href="/wiki/Fish_boil">Fish boil</a></td><td>Midwest</td></tr>
<tr><td></td><td>Unlinked dish</td><td>South</td></tr></table>
<h2>Dishes by region</h2><h3>Chaozhou</h3>
<ul><li><a href="/wiki/Hao_kuih">Hao kuih</a>, a snack</li><li><a href="/wiki/Chaozhou_cuisine">x</a></li></ul>
<h2>See also</h2><ul><li><a href="/wiki/Gumbo">Gumbo</a></li></ul>
<table class="navbox"><tr><td><a href="/wiki/Pizza">Pizza</a></td></tr></table>
"""


def rows() -> list[dict]:
    parser = fk.ListPage()
    parser.feed(PAGE)
    return [r for r in parser.rows if not fk.NOT_DISH_TITLE.search(r["title"])]


def test_table_rows_use_the_name_column_and_keep_the_region() -> None:
    first = rows()[0]
    assert first["title"] == "Fish boil"
    assert first["regions"] == ["Midwest"]
    assert first["section"] == ["Regional dishes"]


def test_bullets_keep_their_section_and_cuisine_pages_are_left_out() -> None:
    titles = [r["title"] for r in rows()]
    assert titles == ["Fish boil", "Hao kuih"]   # no unlinked row, cuisine page, "See also" or navbox links
    assert rows()[1]["section"] == ["Dishes by region", "Chaozhou"]


def test_fun_fact_candidates_skip_the_definition_and_need_a_signal() -> None:
    intro = ("Hao kuih is a snack from Shantou. It is believed to have first appeared in Chaoyang District long ago. "
             "It is round and made of flour mixed with water and other ingredients.")
    assert fk.fact_candidates(intro) == ["It is believed to have first appeared in Chaoyang District long ago."]


def test_learn_more_links_go_from_quick_to_deep() -> None:
    links = fk.learn_more("Mole poblano", "Mole poblano", "Q1", ["Mexican cuisine", "List of Mexican dishes"],
                          ["Intangible Cultural Heritage"])
    assert [link["level"] for link in links] == ["quick", "more", "more", "deep", "deep", "deep"]
    assert links[0]["url"] == "https://en.wikipedia.org/wiki/Mole_poblano"
    assert any("unesco" in link["url"] for link in links)
    assert fk.learn_more("Taco", "Taco", "Q2", [], [])[-1]["url"] == "https://www.wikidata.org/wiki/Q2"
