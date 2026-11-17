"""The alcohol setting: one level for every reason, cooked-in and extracts as the person's own choices."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.confidence import ProfileResponse as R
from everflavor.restrictions import AlcoholSetting, assess

LINES = ["2 chicken thighs", "1/2 cup white wine", "1 tsp vanilla extract"]
STEPS = "Brown the chicken in a pan. Add the wine and simmer for 20 minutes."


def _severities(setting: AlcoholSetting) -> dict[str, str]:
    got = assess(LINES, "Chicken in wine", [], instructions=STEPS, alcohol=setting)
    return {i["line"]: i["severity"] for f in got["findings"] if f["rule"] == "no_alcohol" for i in f["items"]}


def test_strict_is_a_conflict_and_blocks() -> None:
    sev = _severities(AlcoholSetting(R.STRICT))
    assert sev["1/2 cup white wine"] == "major" and sev["1 tsp vanilla extract"] == "major"


def test_lighter_levels_only_inform() -> None:
    assert _severities(AlcoholSetting(R.AVOID))["1/2 cup white wine"] == "moderate"
    assert set(_severities(AlcoholSetting(R.WARN)).values()) == {"info"}
    assert _severities(AlcoholSetting(R.IGNORE)) == {}


def test_extracts_and_cooked_in_are_the_persons_choice() -> None:
    assert "1 tsp vanilla extract" not in _severities(AlcoholSetting(R.AVOID, extracts=False))
    assert set(_severities(AlcoholSetting(R.AVOID, cooked_ok=True)).values()) == {"info"}
    # cooked-in never softens strict (faith, recovery): the setting stays a conflict
    assert _severities(AlcoholSetting(R.STRICT, cooked_ok=True))["1/2 cup white wine"] == "major"


def test_an_allergy_list_pick_stays_strict() -> None:
    got = assess(LINES, "x", ["no_alcohol"], alcohol=AlcoholSetting(R.WARN), responses={"no_alcohol": R.STRICT})
    assert next(f for f in got["findings"] if f["rule"] == "no_alcohol")["severity"] == "major"
