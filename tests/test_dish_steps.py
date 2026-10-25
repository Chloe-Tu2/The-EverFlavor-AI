"""A recipe's steps broken down for the dish page (everflavor.dish_steps)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.dish_steps import split_minutes, step_breakdown

STEPS = ("heat oil in a large skillet\nadd chicken and cook 4 minutes on each side\nremove from heat\n"
         "pour into a 9 x 13 baking dish\nbake 30 minutes\nlet stand 5 minutes")
INGREDIENTS = ["olive oil", "boneless skinless chicken breast half", "chicken broth"]


def test_each_step_says_its_time_vessel_heat_and_ingredients():
    steps = step_breakdown(STEPS, INGREDIENTS)
    assert [s["minutes"] for s in steps] == [None, 4.0, None, None, 30.0, 5.0]
    assert [s["on_heat"] for s in steps] == [True, True, False, False, True, False]
    assert steps[0]["vessel"] == "skillet" and steps[3]["vessel"] == "baking dish"
    assert steps[1]["ingredients"] == ["boneless skinless chicken breast half"]   # "chicken" is not the broth
    assert steps[3]["methods"] == []                                             # a baking dish is not baking
    assert steps[4]["methods"] == ["bake or roast"]


def test_time_splits_into_on_the_heat_and_the_rest():
    steps = step_breakdown(STEPS, INGREDIENTS)
    assert split_minutes(steps, 60) == {"on_heat": 34.0, "rest": 26.0, "total": 60}
    assert split_minutes(steps, None)["rest"] is None
    assert split_minutes(step_breakdown("mix everything", []), 10)["on_heat"] is None
