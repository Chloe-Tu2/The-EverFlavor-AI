"""The waiter's dish knowledge (everflavor.dish_knowledge): cleaning and ranking keep the sources' words."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import dish_knowledge as dk


def test_clean_fact_drops_translations_and_names_the_dish() -> None:
    text = "It is known as Brita cake (Swedish: Britatårta, Finnish: Brita-kakku) after Brita Edland ."
    assert dk.clean_fact(text, "Kvæfjord cake") == "Kvæfjord cake is known as Brita cake after Brita Edland."
    assert dk.clean_fact("Hao kuih (鱟粿) is a snack.", "Hao kuih") == "Hao kuih is a snack."
    unknown = "It is unknown where pollo al disco originated."
    assert dk.clean_fact(unknown, "Pollo al disco") == unknown   # a placeholder "it" stays


def test_stories_rank_first_and_company_news_is_dropped() -> None:
    dish = {"name": "Ginger beef", "reviewed": False, "fun_fact_candidates": [
        "Traditional ingredients include beef and ginger.",
        "In 2022, the company announced it would close and was acquired.",
        "Legend has it the dish was invented in Calgary in the 1970s."]}
    tidy = dk.tidy_dish(dish)
    assert [f["text"] for f in tidy["fun_facts"]] == ["Legend has it the dish was invented in Calgary in the 1970s.",
                                                      "Traditional ingredients include beef and ginger."]
    assert tidy["fun_facts"][0]["topic"] == "inspiration"
    assert tidy["review"] == "auto-cleaned"


def test_best_facts_mix_topics_and_the_rest_wait_as_more() -> None:
    dish = {"name": "Mole", "origin": ["Mexico"], "named_after": ["Nahuatl molli"],
            "fun_fact_candidates": ["It was first made in Puebla in the 17th century by nuns.",
                                    "The dish is served at weddings and festivals across Mexico.",
                                    "Legend has it that nuns invented it for an archbishop in 1680."]}
    tidy = dk.tidy_dish(dish)
    assert len({f["topic"] for f in tidy["fun_facts"]}) == 3   # three different topics
    every = {f["text"] for f in tidy["fun_facts"] + tidy["more_fun_facts"]}
    assert {"Mole comes from Mexico.", "Mole is named after Nahuatl molli."} <= every
    assert all(f["source"] in ("Wikipedia", "Wikidata") for f in tidy["more_fun_facts"])


def test_write_notebook_makes_one_page_per_country_with_sources(tmp_path: Path) -> None:
    dishes = [dk.tidy_dish({"name": "Fish boil", "country": "United States", "region": "Midwestern US",
                            "kind": "dish", "summary": "A fish boil is a tradition.", "reviewed": False,
                            "sources": [{"name": "Wikipedia: Fish boil", "url": "https://en.wikipedia.org/wiki/Fish_boil",
                                         "licence": "CC BY-SA 4.0"}],
                            "learn_more": [{"level": "quick", "title": "Fish boil (Wikipedia)",
                                            "url": "https://en.wikipedia.org/wiki/Fish_boil"}]})]
    assert dk.write_notebook(dishes, tmp_path) == {"United States": 1}
    page = (tmp_path / "united_states.md").read_text(encoding="utf-8")
    assert "### Fish boil" in page and "From: Midwestern US, United States" in page
    assert "CC BY-SA 4.0" in page and "quick: [Fish boil (Wikipedia)]" in page
    assert "[United States](united_states.md)" in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_wikidata_lines_skip_unknown_values():
    dish = {"inventor": ["http://www.wikidata.org/.well-known/genid/abc"], "named_after": ["Victor Hirtzler"]}
    lines = dk.wikidata_lines(dish, "Celery Victor")
    assert lines == ["Celery Victor is named after Victor Hirtzler."]
