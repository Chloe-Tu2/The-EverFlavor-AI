"""Red-team tests for brand names and dishes whose name hides an allergen (flags.PRODUCT_CAUTIONS).

"2 snickers bars" has peanuts, a croissant is made with butter, carbonara with cured pork. The table is a
recorded policy (decided by Claude for review by Team EverGlow, 2026-11-16); these tests pin each entry, the
ordinary words that must stay clear, and the rule that the table only ever adds cautions.

Run with `python -m pytest tests`, or alone:

    python tests/test_product_cautions.py
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor import flags
from everflavor.flags import (
    ANIMAL_EXCEPTIONS,
    ANIMAL_KEYWORDS,
    FLAG_RULES,
    MEAT_EXCEPTIONS,
    MEAT_KEYWORDS,
    PRODUCT_CAUTIONS,
    keyword_flag,
    not_product_names,
    product_names,
    recipe_text,
    with_spellings,
)
from everflavor.recommend import passes_safety_filter
from everflavor.safety import UserProfile, check_recipe

# Each ingredient as a recipe may write it -> the cautions it must raise
MUST_FLAG = {
    "contains_peanut": ["2 Snickers bars, chopped", "snickers candy bar", "snicker", "Reese's peanut-free cups",
                        "reese's piece", "reeses pieces", "Reese’s minis", "nutter butter sandwich cookie",
                        "Nutter Butters", "butterfinger candy bar", "Butterfingers, crushed", "pad thai",
                        "pad thai sauce", "kung pao sauce", "kung-pao chicken"],
    "contains_dairy": ["M&M's plain chocolate candy", "m&m'", "miniature m&m baking bit", "m&ms", "M & M's",
                       "hershey chocolate kiss", "Hershey's bar", "hersheys kisses", "Hershey’s Hugs",
                       "kit kat bar", "KitKat", "Kit-Kat bars", "plain croissant", "2 croissants",
                       "cheeseburger", "cheeseburgers"],
    "contains_gluten": ["croissant", "gravy mix", "chicken gravy mix", "turkey gravy mixes", "ladyfinger",
                        "24 ladyfingers", "lady fingers", "savoiardi", "sponge fingers", "everything bagel"],
    "contains_egg": ["ladyfinger", "ladyfingers", "lady finger", "savoiardi biscuits", "sponge finger"],
    "contains_sesame": ["everything bagel", "everything bagels", "everything bagel seasoning",
                        "everything but the bagel seasoning"],
    "contains_tree_nut": ["Ferrero Rocher", "ferrero chocolates", "almond joy candy bar", "Toblerone chocolate bar"],
    "contains_pork": ["carbonara", "carbonara sauce"],
    "contains_meat": ["cheeseburger", "burger patty", "4 burger patties", "frozen burger patties"],
}
# Ordinary words and look-alikes that must not raise the caution (over-blocking makes the assistant useless)
MUST_CLEAR = {
    "contains_peanut": ["butterfly pea flower", "snickerdoodle", "snickerdoodles", "butter", "fingerling potato",
                        "pad thai rice noodle", "pad thai noodles", "thai basil", "reed avocado"],
    "contains_dairy": ["butterfly pea flower", "hershey's cocoa", "hersheys cocoa powder", "hershey's syrup",
                       "hersheys chocolate syrup", "Hershey's unsweetened cocoa", "kitchen twine", "mm of ginger",
                       "m", "kiwi", "veggie burger"],
    "contains_gluten": ["lady's finger", "ladies' fingers", "ladies finger", "okra", "bhindi", "gravy",
                        "everything", "finger chili", "sponge"],
    "contains_egg": ["lady's finger", "ladies finger", "okra", "bhindi masala", "finger millet"],
    "contains_sesame": ["everything", "everything spice"],
    "contains_tree_nut": ["ferret", "joy of cooking rice"],
    "contains_pork": ["carbon steel pan rice", "carbonated water"],
    "contains_meat": ["veggie burger patties", "vegan burger patty", "black bean burger patties", "bean burger patty",
                      "plant-based burger patties", "lentil burger patty", "burger bun seeds", "patty pan squash"],
}


def flagged(item: str, flag: str, name: str = "") -> bool:
    """The flag as the data pipeline and the safety filter read it."""
    return keyword_flag(recipe_text([item], name), flag)


@pytest.mark.parametrize("flag,item", [(f, i) for f, items in MUST_FLAG.items() for i in items])
def test_products_and_dishes_raise_their_caution(flag, item):
    assert flagged(item, flag)
    assert not check_recipe([item], "", UserProfile(avoid=(flag,)))["passed"]              # the gate
    row = pd.Series({"ingredient_list": [item], "recipe_name": "Dinner"})
    assert not passes_safety_filter(row, avoid=(flag,))                                    # the recommender


@pytest.mark.parametrize("flag,item", [(f, i) for f, items in MUST_CLEAR.items() for i in items])
def test_ordinary_words_and_look_alikes_stay_clear(flag, item):
    assert not flagged(item, flag)
    assert check_recipe([item], "", UserProfile(avoid=(flag,)))["passed"]


@pytest.mark.parametrize("name,flag", [("Snickers Cheesecake Bars", "contains_peanut"),
                                       ("Easy Pad Thai", "contains_peanut"), ("Kung Pao Tofu", "contains_peanut"),
                                       ("Spaghetti Carbonara", "contains_pork"), ("Kit Kat Cake", "contains_dairy"),
                                       ("Croissant French Toast", "contains_dairy"),
                                       ("Classic Tiramisu with Ladyfingers", "contains_egg"),
                                       ("Everything Bagel Dip", "contains_sesame"),
                                       ("Toblerone Mousse", "contains_tree_nut")])
def test_the_dish_name_counts_too(name, flag):
    assert flagged("water", flag, name)
    assert not check_recipe(["water"], name, UserProfile(avoid=(flag,)))["passed"]


def test_every_entry_adds_every_flag_it_lists():
    for name, entry in PRODUCT_CAUTIONS.items():
        assert entry["flags"], name
        for flag in entry["flags"]:
            assert flag in FLAG_RULES, (name, flag)
            for written in [name, *entry.get("aliases", [])]:
                assert flagged(written, flag), (written, flag)
                assert written in product_names(flag)


def test_the_diets_that_follow_from_the_cautions():
    # pork in carbonara: not vegetarian, not halal-friendly, not kosher-friendly
    assert not check_recipe(["carbonara sauce"], "", UserProfile(vegetarian=True))["passed"]
    assert not check_recipe(["carbonara sauce"], "", UserProfile(diets=("halal_friendly",)))["passed"]
    # a cheeseburger is meat with dairy (not kosher-friendly) and never vegetarian or vegan
    assert not check_recipe(["cheeseburger"], "", UserProfile(diets=("kosher_friendly",)))["passed"]
    assert not check_recipe(["burger patties"], "", UserProfile(vegetarian=True))["passed"]
    # butter in a croissant, milk chocolate, egg in a ladyfinger: not vegan
    for item in ["croissant", "m&m's", "hershey bar", "kit kat", "ladyfingers"]:
        assert not check_recipe([item], "", UserProfile(vegan=True))["passed"], item
    # the plant versions stay vegetarian and vegan
    for item in ["veggie burger patties", "vegan burger patty", "bean burger patties"]:
        assert check_recipe([item], "", UserProfile(vegan=True))["passed"], item


def test_okra_called_by_its_own_names_is_not_the_biscuit():
    # Recorded choice: a plain "ladyfinger" is read as the biscuit (the safe side); okra's own names are not
    for okra in ["lady's finger", "ladies' fingers", "okra", "bhindi"]:
        assert check_recipe([okra, "turmeric", "oil"], "Okra Stir Fry",
                            UserProfile(avoid=("contains_gluten", "contains_egg"), vegan=True))["passed"], okra
    assert not check_recipe(["ladyfinger", "turmeric"], "", UserProfile(avoid=("contains_gluten",)))["passed"]


def test_look_alikes_hide_only_their_own_product_never_another_keyword():
    """Flags only ever add cautions: a look-alike ("hershey's cocoa", "veggie burger patt") is removed from the
    text before matching, so it must not contain any keyword other than the product it belongs to."""
    products = set(with_spellings([n for name, e in PRODUCT_CAUTIONS.items() for n in [name, *e.get("aliases", [])]]))
    look_alikes = set(with_spellings([p for e in PRODUCT_CAUTIONS.values() for p in e.get("not_this", [])]))
    assert look_alikes
    rules = {**FLAG_RULES, "vegetarian": (MEAT_KEYWORDS, MEAT_EXCEPTIONS), "vegan": (ANIMAL_KEYWORDS, ANIMAL_EXCEPTIONS)}
    checked = 0
    for column, (keywords, exceptions) in rules.items():
        others = tuple(k for k in keywords if k not in products)
        if not others:
            continue
        pattern = flags._keyword_pattern(others)
        for phrase in look_alikes & set(with_spellings(list(exceptions))):
            # the phrase may stop mid-word ("... burger patt"): complete it both ways
            for text in (phrase, phrase + "y", phrase + "ies"):
                assert not pattern.search(text), (column, phrase, pattern.search(text))
            checked += 1
    assert checked >= len(look_alikes)   # every look-alike is in at least one exception list


def test_look_alikes_reach_only_the_lists_of_their_own_flags():
    assert set(not_product_names("contains_dairy")) <= set(with_spellings(FLAG_RULES["contains_dairy"][1]))
    assert set(not_product_names("contains_peanut")) <= set(with_spellings(FLAG_RULES["contains_peanut"][1]))
    assert set(not_product_names("contains_meat")) <= set(with_spellings(FLAG_RULES["contains_meat"][1]))
    # the gluten in a real pad thai noodle dish is still seen: the peanut look-alike hides nothing from gluten
    assert flagged("pad thai noodles", "contains_gluten") and not flagged("pad thai noodles", "contains_peanut")
    # a look-alike never hides a real allergen next to it
    assert flagged("hershey's cocoa and milk", "contains_dairy")
    assert flagged("veggie burger patties with bacon", "contains_meat")
    assert flagged("pad thai noodles with peanuts", "contains_peanut")


def test_cautions_that_were_already_raised_are_still_raised():
    still = [("croissant", "contains_gluten"), ("everything bagel", "contains_gluten"),
             ("cheeseburger", "contains_beef"), ("carbonara", "contains_egg"), ("nutter butter", "contains_dairy"),
             ("almond joy", "contains_tree_nut"), ("brown gravy mix", "contains_dairy"),
             ("Reese's peanut butter cup", "contains_peanut"), ("m&m's peanut chocolate candy", "contains_peanut"),
             ("hershey's semi-sweet chocolate chip", "contains_dairy"), ("veggie burger with cheese", "contains_dairy")]
    for item, flag in still:
        assert flagged(item, flag), (item, flag)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
