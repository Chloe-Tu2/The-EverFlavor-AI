"""The profile in levels (restrictions.py): the gate still decides; findings come sorted by category and severity."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.diets import DIET_PROFILES
from everflavor.flags import FLAG_RULES
from everflavor.restrictions import CATEGORIES, RULES, assess, profile_for, rules_in

LINES = ["2 chicken breasts", "2 tbsp satay sauce", "1 tbsp soy sauce", "2 cloves garlic", "1 tbsp beer"]


def test_every_rule_points_at_something_real() -> None:
    for rid, rule in RULES.items():
        assert rule.category in CATEGORIES, rid
        if rule.kind == "flag":
            assert set(rule.targets) <= set(FLAG_RULES), rid
        if rule.kind == "diet":
            assert set(rule.targets) <= set(DIET_PROFILES), rid
        if rule.category == "medical":
            assert rule.note or rule.kind == "diet", f"{rid}: a medical screen says what it checks"
    assert rules_in("allergies")[:3] == ["peanut", "tree_nut", "shellfish"]


def test_only_blocking_rules_reach_the_gate() -> None:
    profile = profile_for(["peanut", "halal", "vegan", "lactose", "low_carb", "no_fried", "ibs"])
    assert profile.avoid == ("contains_peanut",) and profile.diets == ("halal_friendly",) and profile.vegan
    assert "contains_dairy" not in profile.avoid and "contains_allium" not in profile.avoid   # cautions stay out


def test_levels_from_worst_to_good_to_know() -> None:
    got = assess(LINES, "Peanut chicken", ["peanut", "celiac", "halal", "allium", "no_deep_fried", "low_carb",
                                           "lactose"], skip=["garlic"], instructions="Deep fry the chicken.",
                 nutrition={"carbs_g": 40})
    by_rule = {f["rule"]: f for f in got["findings"]}
    assert by_rule["peanut"]["severity"] == "critical" and by_rule["celiac"]["severity"] == "critical"
    assert set(by_rule["celiac"]["why"]) >= {"soy sauce", "beer"}          # every reason, not only the first
    assert by_rule["halal"]["severity"] == "major" and by_rule["no_deep_fried"]["severity"] == "major"
    assert by_rule["allium"]["severity"] == "moderate" and by_rule["low_carb"]["severity"] == "moderate"
    assert by_rule["skip"]["severity"] == "info"
    assert got["ok"] == ["Lactose"] and got["overall"] == "critical"


def test_unchecked_is_said_and_clear_is_clear() -> None:
    got = assess(["chickpeas", "parsley"], "Salad", ["peanut", "no_fried", "lower_sodium"])
    assert got["overall"] == "clear" and got["ok"] == ["Peanuts"]
    assert got["not_checked"] == ["No fried food (no steps to read)", "Lower sodium (no nutrition for this recipe)"]
    assert assess(["water"], "x", ["high_protein"], nutrition={"protein_g": float("nan")})["not_checked"]


def test_every_flag_and_diet_belongs_to_a_level() -> None:
    from everflavor.restrictions import rule_ids_from_profile
    flags = sorted(set(FLAG_RULES) - {"contains_pet_meat"})
    assert all(rule_ids_from_profile([f]) for f in flags)   # each flag has its rule (two share "No alcohol")
    assert len(rule_ids_from_profile(diets=list(DIET_PROFILES))) == len(DIET_PROFILES)
    assert rule_ids_from_profile(["contains_gluten", "contains_pork", "contains_carmine"], ["halal_friendly"],
                                 vegan=True) == ["wheat", "no_pork", "no_carmine", "halal", "vegan"]
