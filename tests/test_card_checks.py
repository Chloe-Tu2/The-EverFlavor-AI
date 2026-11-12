"""The recipe card's tick list (recommend.fit_checks, within_calories): only checks that really ran."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.recommend import fit_checks, why_it_fits, within_calories


def test_one_tick_per_check_and_the_line_agrees() -> None:
    ticks = fit_checks(["contains_peanut", "contains_tree_nut"], ["halal_friendly"], vegetarian=True)
    assert ticks == ["no peanut", "no tree nut", "halal-friendly ingredients", "vegetarian"]
    assert why_it_fits(["contains_peanut", "contains_tree_nut"], ["halal_friendly"], vegetarian=True) == (
        "Checked for you: " + ", ".join(ticks))
    assert fit_checks() == [] and fit_checks(vegan=True, vegetarian=True) == ["vegan"]


def test_within_calories_only_when_both_numbers_are_known() -> None:
    assert within_calories(450, 600) and within_calories(600.0, 600)
    assert not within_calories(601, 600)
    assert not within_calories(float("nan"), 600) and not within_calories(None, 600)
    assert not within_calories(0, 600) and not within_calories(300, 0)
