"""The dish's own name from posted recipe titles (everflavor.dish_names)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.dish_names import clean_title


def dish(title: str) -> object:
    return clean_title(title)["dish_name"]


def test_poster_words_come_off():
    assert dish("Kittencal's Famous Lasagna") == "Lasagna"
    assert dish("Grandma's Best Chicken Soup") == "Chicken Soup"
    assert dish("My Easy Pad Thai") == "Pad Thai"
    assert dish("Copycat Olive Garden Zuppa Toscana") == "Zuppa Toscana"
    assert dish("Chicken Enchiladas #2") == "Chicken Enchiladas"
    assert dish("Quick Healthy Low Fat Chili") == "Chili"
    assert dish("pumpkin pie kittencal s way") == "pumpkin pie"      # Food.com lost its apostrophes


def test_real_dish_names_stay():
    for name in ("Shepherd's Pie", "General Tso's Chicken", "Devil's Food Cake", "Better Than Sex Cake"):
        assert dish(name) == name
    assert dish("Crock Pot") == "Crock Pot"                         # nothing else left: the tag stays


def test_alternate_name_and_posted_flag():
    out = clean_title("Bulgogi (Korean BBQ Beef) - Ww Friendly")
    assert out["dish_name"] == "Bulgogi" and out["name_gloss"] == "Korean BBQ Beef"
    assert clean_title("Jane's Yummy Tacos")["posted_title"] is True
    assert clean_title("Chicken Tikka Masala")["posted_title"] is False
