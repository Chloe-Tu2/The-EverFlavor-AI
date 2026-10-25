"""Cook-time estimates for recipes without a stated time (everflavor.cooking_time)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.cooking_time import (
    estimate_minutes,
    fit_time_model,
    parse_step_minutes,
    round_minutes,
    time_label,
)


def test_times_in_the_steps():
    assert parse_step_minutes("bake 30 minutes")["dur_sum"] == 30
    assert parse_step_minutes("simmer for 1 1/2 hours")["dur_sum"] == 90
    assert parse_step_minutes("cook on low 2-3 hrs")["dur_sum"] == 150
    assert parse_step_minutes("rest for half an hour")["dur_sum"] == 30
    assert parse_step_minutes("blend until smooth")["dur_steps"] == 0


def test_overnight_is_a_word_not_eight_hours():
    parsed = parse_step_minutes("mix the oats and milk\nchill overnight")
    assert parsed["dur_sum"] == 0 and parsed["dur_steps"] == 0
    assert parsed["overnight_steps"] == 1 and parsed["n_steps"] == 2


def test_food_com_lines_and_themealdb_paragraphs():
    foodcom = parse_step_minutes("preheat oven\nbake 20 minutes\nlet cool 10 minutes")
    assert foodcom["n_steps"] == 3 and foodcom["dur_steps"] == 2 and foodcom["dur_sum"] == 30
    mealdb = parse_step_minutes("step 1\r\nFry for 5 mins. Then fry 10 minutes more.\r\n\r\nstep 2\r\nBake 25 minutes.")
    assert mealdb["n_steps"] == 2                                  # the "step 1" headings are not steps
    assert mealdb["dur_sum"] == 40 and mealdb["dur_maxsum"] == 35  # largest time per step
    assert parse_step_minutes(None)["n_steps"] == 0
    assert parse_step_minutes(float("nan"))["n_steps"] == 0


def test_rounding_and_labels():
    assert round_minutes(37) == 35 and round_minutes(2) == 5 and round_minutes(68) == 75
    assert time_label(35, "recipe") == "35 min"
    assert time_label(90, "recipe") == "1 h 30 min"
    assert time_label(38.4, "estimate_name") == "About 40 min (estimated from similar recipes)"
    assert time_label(68, "estimate_steps") == "About 1 h 15 min (estimated from similar recipes)"
    assert time_label(240, "estimate_steps") == "About 4 h (estimated from similar recipes)"
    assert time_label(260, "estimate_name") == "Several hours (estimate)"
    assert time_label(300, "recipe") == "5 h"                      # a real time is shown as it is
    assert time_label(float("nan"), "estimate_name") == ""
    assert time_label(40, "unknown") == "" and time_label(None, "recipe") == ""


def _synthetic(n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    kinds = [("slow cooker beef stew", "brown the beef\nslow cook on low 6 hours", 380),
             ("quick green salad", "chop the lettuce\ntoss with dressing", 10),
             ("baked chicken", "season the chicken\nbake 45 minutes", 55)]
    rows = []
    for i in range(n):
        name, steps, minutes = kinds[i % 3]
        rows.append({"recipe_name": f"{name} {rng.integers(5)}", "instructions": steps,
                     "complexity": int(rng.integers(3, 9)), "minutes": minutes * rng.uniform(0.8, 1.2), "source": "foodcom"})
    return pd.DataFrame(rows)


def test_fit_and_estimate_round_trip():
    model = fit_time_model(_synthetic(300, 0), neighbors=10)
    new = pd.DataFrame({
        "recipe_name": ["Slow Cooker Beef Stew", "Green Salad", "Baked Chicken", "", "Baked Chicken"],
        "instructions": [None, None, "season\nbake 45 minutes", None, None],
        "complexity": [5, 4, 6, np.nan, 6],
        "minutes": [np.nan, np.nan, np.nan, np.nan, 50],
    }, index=[10, 11, 12, 13, 14])
    out = estimate_minutes(model, new)
    assert list(out.index) == [10, 11, 12, 13, 14]
    assert list(out["minutes_source"]) == ["estimate_name", "estimate_name", "estimate_steps", "unknown", "recipe"]
    stew, salad, chicken = out["minutes_estimate"].iloc[:3]
    assert stew > 240 and salad < 20 and 30 <= chicken <= 75
    assert np.isnan(out["minutes_estimate"].iloc[3]) and np.isnan(out["minutes_estimate"].iloc[4])
    assert new["minutes"].iloc[4] == 50                            # the real time is never touched
    assert time_label(stew, "estimate_name") == "Several hours (estimate)"
    again = estimate_minutes(fit_time_model(_synthetic(300, 0), neighbors=10), new)
    assert again.equals(out)                                       # fixed random_state: same estimates
