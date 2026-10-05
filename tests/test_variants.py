"""Tests for dish variants (src/everflavor/variants.py), notebook 06.

The key promise: a variant never keeps or adds an ingredient its target diet rules
out, because the whole new dish is checked again. Run with `python -m pytest tests`,
or alone:

    python tests/test_variants.py
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.flags import keyword_flag
from everflavor.variants import (
    TARGET_CAUTIONS,
    TARGETS,
    diet_blockers,
    dish_variants,
    make_variant,
)
from everflavor.variants import _swap_table as swap_table

REVIEWED = pd.DataFrame({"original": ["butter", "butter", "egg", "egg white"],
                         "substitute": ["margarine", "olive oil", "eggbeater", "whole wheat flour"],
                         "n_reviews": [120, 270, 7, 1]})


def test_blockers_follow_the_flag_rules():
    assert diet_blockers(["butter", "flour", "egg", "salt"], "vegan") == ["butter", "egg"]
    assert diet_blockers(["bacon", "red wine", "onion"], "halal_friendly") == ["bacon", "red wine"]
    assert diet_blockers(["rice", "tofu"], "vegan") == []
    assert set(TARGETS) >= {"vegan", "gluten_free", "halal_friendly", "kosher_friendly", "jain_friendly"}


def test_a_variant_never_keeps_or_adds_a_forbidden_ingredient():
    table = swap_table(REVIEWED)
    v = make_variant(["butter", "flour", "egg", "sugar"], "vegan", table)
    assert v["status"] == "variant"
    assert ("butter", "olive oil", "reviews") in v["swaps"]          # the most reviewed swap that fits
    assert ("egg", "flax egg", "guidance") in v["swaps"]             # eggbeater is egg whites: not vegan
    assert keyword_flag(" | ".join(v["ingredients"]), "vegan")
    assert make_variant(["rice", "beans"], "vegan", table)["status"] == "fits"
    stuck = make_variant(["cheddar cheese", "bread"], "vegan", table)
    assert stuck["status"] == "no_variant" and stuck["missing"] == ["cheddar cheese"]
    assert "whole wheat flour" not in [s for _, s, _ in make_variant(["egg white"], "egg_free", table)["swaps"]]


def test_halal_and_jain_variants_carry_their_cautions():
    table = swap_table(None)
    halal = make_variant(["bacon", "potato", "white wine"], "halal_friendly", table)
    assert halal["status"] == "variant" and halal["caution"] == TARGET_CAUTIONS["halal_friendly"]
    assert not {"bacon", "white wine"} & set(halal["ingredients"])
    jain = make_variant(["garlic", "rice", "cumin"], "jain_friendly", table)
    assert jain["ingredients"] == ["asafoetida", "rice", "cumin"]


def test_dish_variants_table():
    recipes = pd.DataFrame({"recipe_id": ["r1", "r2"], "recipe_name": ["Butter Cake", "Rice"],
                            "ingredient_list": [["butter", "flour", "sugar"], ["rice", "water"]]})
    out = dish_variants(recipes, ["vegan", "gluten_free"], REVIEWED).set_index(["recipe_id", "target"])
    assert out.loc[("r1", "vegan"), "swaps"] == "butter -> olive oil"
    assert out.loc[("r1", "gluten_free"), "status"] == "variant"
    assert out.loc[("r2", "vegan"), "status"] == "fits" and out.loc[("r2", "vegan"), "n_swaps"] == 0
    with pytest.raises(KeyError):
        dish_variants(recipes, ["not_a_diet"])


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
