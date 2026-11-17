"""How a dish is made, as a risk of its own (everflavor.preparation), and how assess shows it."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.preparation import prep_risks, step_sentences
from everflavor.restrictions import assess, rule_ids_from_profile


def test_raw_and_undercooked_named_outright() -> None:
    assert prep_risks("Sear the steak to medium-rare.") == {"undercooked": ["medium-rare"]}
    assert prep_risks("Salmon sashimi")["undercooked"] == ["sashimi"]
    assert prep_risks("Leave the yolks runny yolk style. Ferment for 3 days.").keys() == {"undercooked", "fermented"}


def test_a_sentence_that_says_it_is_cooked_is_left_out() -> None:
    assert prep_risks("Cook until no longer pink in the middle.") == {}
    assert prep_risks("Vegetarian sushi with cucumber") == {}
    assert prep_risks("Bake for 20 minutes.") == {}


def test_steps_become_short_marked_sentences() -> None:
    got = step_sentences("Dip the fish in the beer batter. Fry until golden!")
    assert got == ["(steps) Dip the fish in the beer batter.", "(steps) Fry until golden!"]


def test_pregnancy_screens_how_it_is_made() -> None:
    got = assess(["200 g beef fillet", "salt"], "Beef carpaccio", ["pregnancy"], instructions="Slice thinly.")
    prep = got["preparation"]
    assert prep and prep[0]["severity"] == "critical" and "carpaccio" in prep[0]["notes"][0]


def test_the_steps_bring_in_alcohol_the_lines_do_not_show() -> None:
    ids = rule_ids_from_profile(["contains_alcohol"])
    got = assess(["2 cod fillets", "1 cup flour"], "Fish", ids,
                 instructions="Whisk the flour with beer into a batter. Fry the fish.")
    prep = got["preparation"]
    assert any("beer" in r["line"] for r in prep)                     # the step, as a possible
    assert got["by_confidence"]["verified"] == []                     # nothing on the lines themselves
    assert all(r["severity"] == "moderate" for r in prep if "beer" in r["line"])


def test_the_steps_only_add_what_the_lines_do_not_show() -> None:
    ids = rule_ids_from_profile(["contains_peanut"])
    assert assess(["walnut", "flour"], "Cake", ids, instructions="Stir in nuts and bake.")["overall"] == "clear"
    # nuts nobody listed: possible, and still unsafe for a peanut allergy
    assert assess(["banana", "flour"], "Cake", ids, instructions="Add nuts and bake.")["overall"] == "critical"
    assert step_sentences("Poke holes all over the cake.") == ["(steps) pierce holes all over the cake."]


def test_preparation_rules_are_their_own_choice() -> None:
    got = assess(["kimchi"], "x", ["no_fermented"], instructions="Ferment the cabbage for a week.")
    assert [r["severity"] for r in got["preparation"]] == ["moderate"]
    assert assess(["eggs"], "Omelette", ["no_undercooked"])["not_checked"] == [
        "No raw or undercooked food (no steps to read)"]


def test_charred_and_aged() -> None:
    assert prep_risks("Blackened salmon") == {"charred": ["blackened"]}
    assert prep_risks("Arctic char with lemon") == {}                  # the fish, not the cooking
    assert prep_risks("A dry-aged ribeye") == {"aged": ["dry-aged"]}
    got = assess(["1 ribeye", "salt"], "Dry-aged ribeye", ["maoi", "no_grilled"], instructions="Char the steak.")
    assert {r["rules"][0] for r in got["preparation"]} == {"MAOI medicines", "No grilled or charred food"}
