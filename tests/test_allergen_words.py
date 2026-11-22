"""Spanish, French and Italian allergen words (flags.FOREIGN_ALLERGEN_KEYWORDS), reviewed one by one in
docs/flag_review/allergen_words_es_fr_it.csv. A word only adds a caution; words with another meaning stay out."""
import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.flags import (
    FOREIGN_ALLERGEN_EXCEPTIONS,
    FOREIGN_ALLERGEN_KEYWORDS,
    flags_for_term,
)

SHEET = ROOT / "docs" / "flag_review" / "allergen_words_es_fr_it.csv"
ROWS = list(csv.DictReader(SHEET.open(encoding="utf-8")))


@pytest.mark.parametrize("word, flag", [
    ("huevos", "contains_egg"), ("œufs", "contains_egg"), ("tuorlo", "contains_egg"),
    ("leche", "contains_dairy"), ("lait", "contains_dairy"), ("fromage", "contains_dairy"), ("formaggi", "contains_dairy"),
    ("cacahuètes", "contains_peanut"), ("cacahuate", "contains_peanut"), ("arachidi", "contains_peanut"),
    ("nueces", "contains_tree_nut"), ("noci", "contains_tree_nut"), ("pistacchi", "contains_tree_nut"),
    ("almendras", "contains_tree_nut"),
    ("pescado", "contains_fish"), ("poisson", "contains_fish"), ("atún", "contains_fish"), ("tonno", "contains_fish"),
    ("crevettes", "contains_crustacean"), ("gambas", "contains_crustacean"), ("camarones", "contains_crustacean"), ("homard", "contains_crustacean"),
    ("calamar", "contains_mollusc"), ("cozze", "contains_mollusc"), ("huîtres", "contains_mollusc"),
    ("mejillones", "contains_shellfish"), ("sésamo", "contains_sesame"), ("graines de sésame", "contains_sesame"),
    ("salsa de soja", "contains_soy"), ("harina", "contains_gluten"), ("farine", "contains_gluten"),
    ("pane", "contains_gluten"), ("trigo", "contains_gluten"),
])
def test_foreign_allergen_words_set_their_flag(word: str, flag: str) -> None:
    assert flag in flags_for_term(word)


@pytest.mark.parametrize("text", ["a frying pan", "demi-glace", "masa harina", "chocolate bar", "halwa", "moule"])
def test_words_with_another_meaning_add_no_allergen(text: str) -> None:
    allergens = [f for f in flags_for_term(text) if f in FOREIGN_ALLERGEN_KEYWORDS]
    assert allergens == []


def test_steak_bleu_and_soba_keep_their_old_flags() -> None:
    assert set(flags_for_term("steak bleu")) & set(FOREIGN_ALLERGEN_KEYWORDS) == set()   # rare steak, not blue cheese
    assert "contains_soy" not in flags_for_term("soba")


@pytest.mark.parametrize("text", ["lait de coco", "leche de almendra", "burro di arachidi", "harina de arroz",
                                  "farine de riz", "queso vegano"])
def test_foreign_names_of_english_exceptions_stay_exempt(text: str) -> None:
    """'lait de coco' is coconut milk: not dairy, as the English phrase is not."""
    flags = flags_for_term(text)
    assert "contains_dairy" not in flags and "contains_gluten" not in flags


def test_fish_and_seafood_words_make_a_dish_not_vegetarian() -> None:
    from everflavor.flags import MEAT_KEYWORDS, make_flag
    assert make_flag("pescado blanco", MEAT_KEYWORDS) and make_flag("gambas al ajillo", MEAT_KEYWORDS)


def test_every_word_in_the_code_is_a_kept_row_of_the_review_sheet() -> None:
    kept = {(r["flag"], r["word"]) for r in ROWS if r["decision"] == "keep"}
    dropped = {(r["flag"], r["word"]) for r in ROWS if r["decision"] == "drop"}
    in_code = {(f, w) for f, ws in FOREIGN_ALLERGEN_KEYWORDS.items() for w in ws}
    assert in_code <= kept, sorted(in_code - kept)[:5]
    assert not in_code & dropped
    assert all(r["reason"] and r["decided_by"] for r in ROWS)
    assert all(" " in p for ps in FOREIGN_ALLERGEN_EXCEPTIONS.values() for p in ps)   # never a single word
    exceptions = {(r["flag"], r["word"]) for r in ROWS if r["decision"] == "exception"}
    assert {(f, p) for f, ps in FOREIGN_ALLERGEN_EXCEPTIONS.items() for p in ps} <= exceptions


@pytest.mark.parametrize("text, flag", [("crème de menthe", "contains_dairy"), ("kecap manis", "contains_peanut"),
                                        ("noix de coco", "contains_tree_nut"), ("pork noisettes", "contains_tree_nut"),
                                        ("zuppa sarda", "contains_fish"), ("pumpkin spice latte", "contains_dairy"),
                                        ("beurre manié", "contains_peanut"), ("aam panna", "contains_dairy")])
def test_clashes_found_in_the_change_report_stay_clean(text: str, flag: str) -> None:
    assert flag not in flags_for_term(text)
