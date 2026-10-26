"""The dish phrase a Commons photo search uses (scripts/dish_photos/fetch_dish_photos.py, core_phrase)."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _core_phrase():
    spec = importlib.util.spec_from_file_location("fetch_dish_photos",
                                                  ROOT / "scripts" / "dish_photos" / "fetch_dish_photos.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.core_phrase


core_phrase = _core_phrase()


@pytest.mark.parametrize(("name", "core"), [
    ("sloppy joes", "sloppy joes"),
    ("Easy Homemade Sloppy Joes", "sloppy joes"),
    ("grandma's meatloaf", "meatloaf"),
    ("my mom's best banana bread", "banana bread"),
    ("aunt sue's chili", "chili"),
    ("crock pot pulled pork", "pulled pork"),
    ("low-fat chocolate chip cookies", "chocolate chip cookies"),
    ("chicken tikka masala with rice", "chicken tikka masala"),
    ("Moules Marinieres with Fries", "moules marinieres"),
    ("e s duck gumbo", "duck gumbo"),
    ("shepherd's pie", "shepherd's pie"),
    ("pigs in a blanket", "pigs in a blanket"),
    ("beef stroganoff in a slow cooker", "beef stroganoff"),
    ("chicken alfredo dup", "chicken alfredo"),
])
def test_core_phrase_keeps_the_dish(name, core):
    assert core_phrase(name) == core


@pytest.mark.parametrize("name", [
    "chicken", "Easy Chicken", "grandma's pie", "best ever brownies",  # generic words only
    "special treat", "breakfast bowl",                                 # vague words only
    "broccoli", "chicken breast", "Mussels with Tomato Broth",          # a plain ingredient
    "middle eastern lamb casserole baked under vine leaves",           # too long to be one dish's name
    "", "5",
])
def test_core_phrase_gives_nothing_for_no_specific_dish(name):
    assert core_phrase(name) == ""
