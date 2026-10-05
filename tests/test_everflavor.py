"""Tests for the shared code in src/everflavor.

Each test pins down one promise a function makes, so a later change that breaks
it is caught at once. Run from the project folder, either with pytest:

    python -m pytest tests

or without installing anything:

    python tests/test_everflavor.py
"""
import contextlib
import io
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from everflavor.checks import require_columns
from everflavor.cooking import (
    FAT_KEYWORDS,
    add_alcohol_estimate,
    add_cooking_labels,
    alcohol_left_range,
    fat_reference,
    fats_from_ingredients,
    method_label_agreement,
    methods_from_instructions,
    methods_from_tags,
    top_fats_by_group,
)
from everflavor.cuisine import map_cuisine, origin_from_labels
from everflavor.diets import ALLERGEN_SETS, DIET_PROFILES, add_diet_profiles, meets_diet
from everflavor.flags import (
    FLAG_COLUMNS,
    FOOD_NAME_GROUPS,
    WINE_NAME_EXCEPTIONS,
    WINE_NAME_GROUPS,
    add_keyword_flags,
    explain_flag,
    flags_for_term,
    foodcom_tag_agreement,
    keyword_flag,
    make_flag,
    print_flag_counts,
    spelling_variants,
    term_group_of,
    term_groups,
    term_names,
    wine_name_groups,
    wine_names,
    with_spellings,
)
from everflavor.ingredients import (
    normalize_ingredient,
    normalize_ingredient_list,
)
from everflavor.parsing import parse_label_list, parse_list_string
from everflavor.pipeline import (
    MAX_KCAL_PER_SERVING,
    clean_huggingface,
    remove_excluded_recipes,
    run_pipeline,
    split_by_ingredient_group,
    split_tables,
)
from everflavor.recommend import passes_safety_filter
from everflavor.review import compound_evidence, declared_allergens


def expect_error(error, function, *args, **kwargs):
    """Return the error message if `function` raises `error`; fail otherwise."""
    try:
        function(*args, **kwargs)
    except error as e:
        return str(e)
    raise AssertionError(f"{function.__name__} did not raise {error.__name__}")


# ------------------------------------------------------------------ parsing and ingredients
def test_parse_lists_in_both_text_formats():
    assert parse_list_string('["salt", "sugar"]') == ["salt", "sugar"]
    assert parse_list_string("['salt', 'sugar']") == ["salt", "sugar"]
    assert parse_list_string("not a list") == []
    assert parse_label_list("Middle East") == ["middle east"]


def test_normalize_ingredient_removes_quantities_and_plurals():
    assert normalize_ingredient("2 Large Eggs") == ["egg"]
    assert normalize_ingredient("1/2 cup grated parmesan cheese") == ["parmesan cheese"]
    assert normalize_ingredient("canola oil or vegetable oil") == ["canola oil"]
    assert normalize_ingredient("salt and pepper") == ["salt", "pepper"]
    assert normalize_ingredient("4 green chilies") == ["green chili"]          # not "green chily"
    assert normalize_ingredient("berries") == ["berry"] and normalize_ingredient("veggies") == ["veggie"]
    assert normalize_ingredient_list(["egg", "2 eggs", "Chopped Onions"]) == ["egg", "onion"]


# ------------------------------------------------------------------ flags
def test_make_flag_matches_whole_words_only():
    pork = ["ham", "bacon"]
    assert make_flag("smoked ham", pork)
    assert not make_flag("graham cracker", pork)              # 'ham' inside 'graham'
    assert make_flag("ham hocks", pork)                       # plural still matches
    assert not make_flag("turkey bacon", pork, ["turkey bacon"])   # exception phrase
    assert not make_flag(None, pork)                          # not text


def test_keyword_flags_read_hidden_ingredients():
    assert keyword_flag("soy sauce | rice", "contains_gluten")    # soy sauce has wheat
    assert keyword_flag("za'atar | olive oil", "contains_sesame")
    assert not keyword_flag("butter lettuce | tomato", "contains_dairy")
    assert not keyword_flag("tofu | rice | soy sauce", "contains_meat")
    assert not keyword_flag("grilled lamb chops", "vegetarian")


def test_add_keyword_flags_uses_the_name_and_does_not_change_its_input():
    df = pd.DataFrame({"ingredients": [["yogurt", "garlic"]], "name": ["Grilled Lamb Chops with Tzatziki"]})
    before = df.copy()
    flagged = add_keyword_flags(df, "ingredients", name_col="name")
    assert not flagged.loc[0, "vegetarian"]                   # lamb is only in the name
    assert flagged.loc[0, "contains_dairy"]
    assert set(FLAG_COLUMNS) <= set(flagged.columns)
    pd.testing.assert_frame_equal(df, before)                 # the caller's table is unchanged


def test_gluten_free_name_does_not_count_as_wheat():
    df = pd.DataFrame({"ingredients": [["rice flour", "egg"]], "name": ["Gluten-Free Bread"]})
    assert not add_keyword_flags(df, "ingredients", name_col="name").loc[0, "contains_gluten"]


def test_missing_column_gives_a_clear_error():
    message = expect_error(ValueError, add_keyword_flags, pd.DataFrame({"x": [1]}), "ingredients")
    assert "ingredients" in message and "add_keyword_flags" in message
    expect_error(ValueError, require_columns, pd.DataFrame(), ["a"], "here")


# ------------------------------------------------------------------ diets
def flags_frame(**values):
    """One recipe with every flag False except the ones given."""
    row = dict.fromkeys(FLAG_COLUMNS, False)
    row.update(values)
    return pd.DataFrame([row])


def test_diet_rules():
    assert meets_diet(flags_frame(), "halal_friendly").all()
    assert not meets_diet(flags_frame(contains_pork=True), "halal_friendly").all()
    assert meets_diet(flags_frame(contains_meat=True), "kosher_friendly").all()
    assert not meets_diet(flags_frame(contains_meat=True, contains_dairy=True), "kosher_friendly").all()
    assert meets_diet(flags_frame(vegetarian=True), "jain_friendly").all()
    assert not meets_diet(flags_frame(vegetarian=True, contains_allium=True), "jain_friendly").all()
    assert "Unknown diet" in expect_error(ValueError, meets_diet, flags_frame(), "paleo")


def test_add_diet_profiles_returns_a_copy_and_needs_listed_nutrition():
    df = flags_frame(vegetarian=True).assign(nutrition_plausible=[False], sodium_mg=[100.0], carbs_g=[5.0])
    before = df.copy()
    out = add_diet_profiles(df)
    assert set(DIET_PROFILES) <= set(out.columns)
    assert not out.loc[0, "lower_sodium"]                     # nutrition not listed/plausible
    pd.testing.assert_frame_equal(df, before)


# ------------------------------------------------------------------ cuisine and origin
def test_cuisine_family_and_origin():
    assert map_cuisine("['african', 'middle-eastern']", substring_match=False) == "African"  # priority
    assert map_cuisine("Italy") == "European"
    assert origin_from_labels("['mexican', 'tex-mex']") == ("United States", "Texas")
    assert origin_from_labels("['iranian-persian']") == ("Iran", None)
    assert origin_from_labels("['american', 'italian']") == ("Unknown", None)


# ------------------------------------------------------------------ pipeline
def test_clean_huggingface_converts_calories_and_drops_bad_servings():
    raw = pd.DataFrame({
        "recipe_name": ["a", "b", "c", "d"],
        "calories": [800.0, 500.0, 900.0, 100_000.0],
        "cuisine_type": ["['italian']"] * 4,
        "servings": [4, 0, 60, 2],
    })
    clean = clean_huggingface(raw)
    assert clean["recipe_name"].tolist() == ["a"]             # b: 0 servings, c: > 50, d: too many kcal
    assert clean.loc[clean.index[0], "calories_per_serving"] == 200.0
    assert (clean["calories_per_serving"] <= MAX_KCAL_PER_SERVING).all()


def test_run_pipeline_rejects_unknown_sources_and_missing_columns():
    assert "Unknown source" in expect_error(ValueError, run_pipeline, pd.DataFrame(), source="recipedb")
    assert "recipe_name" in expect_error(ValueError, run_pipeline, pd.DataFrame({"x": [1]}), source="culinarydb")


def test_split_keeps_ingredient_groups_together_and_does_not_change_its_input():
    df = pd.DataFrame({
        "ingredient_group": [f"g{i // 2}" for i in range(400)],   # 200 groups of 2 recipes
        "cuisine_family": ["European", "Asian"] * 200,
    })
    before = df.copy()
    split = split_by_ingredient_group(df, verbose=False)
    assert "split" not in df.columns
    pd.testing.assert_frame_equal(df, before)
    assert (split.groupby("ingredient_group")["split"].nunique() == 1).all()
    train, val, test = split_tables(split)
    assert len(train) + len(val) + len(test) == len(df)
    assert 0.6 < len(train) / len(df) < 0.8


# ------------------------------------------------------------------ safety filter
def test_safety_filter_rechecks_ingredients_and_name():
    row = pd.Series({"ingredient_list": ["rice", "egg"], "recipe_name": "Fried Rice with Bacon"})
    assert not passes_safety_filter(row, avoid=("contains_pork",))       # bacon only in the name
    assert not passes_safety_filter(row, diets=("halal_friendly",))
    assert passes_safety_filter(row, avoid=("contains_peanut",))
    assert not passes_safety_filter(row, vegan=True)



# ------------------------------------------------------------------ bugs found by the type checker (mypy)
def test_score_flags_accepts_a_tuple_of_flags(tmp_path=None):
    import tempfile

    from everflavor.review import score_flags
    folder = Path(tmp_path or tempfile.mkdtemp())
    labeled = folder / "labeled.csv"
    pd.DataFrame({"recipe_id": ["r1", "r2"], "recipe_name": ["a", "b"], "ingredients": ["ham", "rice"],
                  "contains_pork": ["1", "0"]}).to_csv(labeled, index=False)
    df_all = pd.DataFrame({"recipe_id": ["r1", "r2"], "contains_pork": [True, False]})
    scores, disagreements = score_flags(labeled, df_all, ("contains_pork",))   # a tuple, not a list
    assert scores.loc["contains_pork", "recall"] == 1.0
    assert disagreements.empty


def test_retry_helpers_refuse_zero_retries():
    from everflavor.sources import (
        _get_json,  # private, but its promise is worth testing
    )
    assert "retries" in expect_error(ValueError, _get_json, "https://example.invalid", retries=0)


# ------------------------------------------------------------------ flag review round 3 and human verification (5.13)
def test_round3_keyword_fixes():
    assert keyword_flag("jamón ibérico | croquetas", "contains_pork")
    assert not keyword_flag("merguez sausage | couscous", "contains_pork")
    assert not keyword_flag("sherry wine vinegar | olive oil", "contains_alcohol")
    assert keyword_flag("hard italian roll | provolone", "contains_gluten")
    assert not keyword_flag("california roll | nori", "contains_gluten")
    assert keyword_flag("rawa idli", "contains_gluten")
    assert keyword_flag("frozen seafood mix | rice", "contains_shellfish")
    assert not keyword_flag("old bay seafood seasoning | corn", "contains_shellfish")
    assert not keyword_flag("black bean | southwestern caviar mock caviar", "contains_fish")
    assert keyword_flag("black bean | southwestern caviar mock caviar", "vegetarian")
    assert not keyword_flag("wild mushrooms (such as oyster, crimini) | turkey", "contains_shellfish")
    assert not keyword_flag("marinated portobello steak | barley", "contains_meat")
    assert keyword_flag("marinated portobello steak | barley", "vegetarian")
    assert not keyword_flag("swordfish steak | red onion", "contains_meat")
    assert not keyword_flag("swordfish steak | red onion", "vegetarian")   # still fish
    assert keyword_flag("schmaltz | onion", "contains_meat")
    assert keyword_flag("smen | couscous", "contains_dairy")
    assert keyword_flag("gingelly oil | rice", "contains_sesame")
    assert not keyword_flag("poultry seasoning | bread", "contains_meat")
    assert not keyword_flag("air fryer fries | potato", "contains_meat")


def test_team_policies_oats_nuts_gelatin():
    assert keyword_flag("rolled oats | honey", "contains_gluten")
    assert not keyword_flag("gluten-free oats | honey", "contains_gluten")
    assert keyword_flag("mixed nuts | raisins", "contains_peanut")
    assert not keyword_flag("pine nuts | basil", "contains_peanut")
    assert not keyword_flag("coconut | nutmeg | walnut", "contains_peanut")
    assert keyword_flag("jell-o | whipped cream", "contains_meat")


def test_red_meat_poultry_and_processed_meat():
    assert keyword_flag("pork shoulder", "contains_red_meat")          # pork is red meat (USDA)
    assert keyword_flag("lamb | beef liver", "contains_red_meat")
    assert not keyword_flag("chicken breast | chicken liver", "contains_red_meat")
    assert keyword_flag("chicken breast", "contains_poultry")
    assert not keyword_flag("salmon | shrimp", "contains_poultry")     # fish is not white meat
    assert not keyword_flag("salmon | shrimp", "contains_red_meat")
    assert not keyword_flag("kidney beans | rice", "contains_red_meat")
    assert keyword_flag("turkey bacon", "contains_processed_meat")
    assert not keyword_flag("turkey bacon", "contains_red_meat")
    assert keyword_flag("bulgogi | rice", "contains_meat")              # every beef word is also meat
    assert not keyword_flag("bulgogi | rice", "vegetarian")
    assert explain_flag("pork shoulder | chicken", "contains_red_meat") == ["pork"]


def test_shellfish_splits_into_crustaceans_and_molluscs():
    assert keyword_flag("shrimp | garlic", "contains_crustacean")
    assert not keyword_flag("shrimp | garlic", "contains_mollusc")
    assert keyword_flag("oyster sauce | broccoli", "contains_mollusc")
    assert not keyword_flag("oyster mushrooms | rice", "contains_mollusc")
    for text in ["seafood mix", "frutti di mare"]:                    # policy P5: may be either
        assert keyword_flag(text, "contains_crustacean") and keyword_flag(text, "contains_mollusc")
    for text in ["shrimp", "squid", "cuttlefish | ink"]:              # every split word is still shellfish
        assert keyword_flag(text, "contains_shellfish")


def test_allergens_labeled_outside_the_us():
    assert keyword_flag("dijon | honey", "contains_mustard")
    assert keyword_flag("old bay seasoning | shrimp", "contains_celery")
    assert keyword_flag("lupini beans", "contains_lupin")
    assert keyword_flag("soba noodles | soy sauce", "contains_buckwheat")
    assert not keyword_flag("chuka soba noodles", "contains_buckwheat")    # wheat noodles
    assert not keyword_flag("yakisoba sauce", "contains_buckwheat")
    assert keyword_flag("dry white wine | butter", "contains_sulfites")
    assert not keyword_flag("unsulfured molasses", "contains_sulfites")


def test_religious_diet_flags_and_profiles():
    # Kosher: no fish without scales, no rabbit, no carmine
    assert keyword_flag("catfish fillets", "contains_scaleless_fish")
    assert not keyword_flag("eel sauce | rice", "contains_scaleless_fish")   # soy sauce, mirin, sugar
    assert keyword_flag("rabbit | thyme", "contains_unclean_meat")
    assert not keyword_flag("cheddar | welsh rabbit", "contains_unclean_meat")
    assert keyword_flag("cheddar | welsh rabbit", "vegetarian")               # cheese on toast
    assert not keyword_flag("frog legs | butter", "vegetarian")
    assert not keyword_flag("cochineal | sugar", "vegan")
    # Asafoetida is separate from onion and garlic: Jain cooks use it instead of them
    assert keyword_flag("hing | cumin", "contains_asafoetida")
    assert not keyword_flag("hing | cumin", "contains_allium")
    # Coffee and tea, not dishes named after them or herbal teas
    assert keyword_flag("brewed coffee | sugar", "contains_coffee_or_tea")
    for text in ["sour cream coffee cake", "chamomile tea | honey", "sugar | teaspoon"]:
        assert not keyword_flag(text, "contains_coffee_or_tea")
    assert not keyword_flag("chocolate truffles | cocoa", "contains_mushroom")
    assert keyword_flag("truffle oil | pasta", "contains_mushroom")

    flags = pd.DataFrame([
        {**dict.fromkeys(FLAG_COLUMNS, False), "vegetarian": True},                           # plain veg dish
        {**dict.fromkeys(FLAG_COLUMNS, False), "contains_fish": True, "contains_scaleless_fish": True},
        {**dict.fromkeys(FLAG_COLUMNS, False), "vegetarian": True, "contains_asafoetida": True},
        {**dict.fromkeys(FLAG_COLUMNS, False), "contains_shellfish": True, "contains_mollusc": True},
    ])
    assert meets_diet(flags, "kosher_friendly").tolist() == [True, False, True, False]
    assert meets_diet(flags, "buddhist_vegetarian").tolist() == [True, False, False, False]
    assert meets_diet(flags, "jain_friendly").tolist() == [True, False, True, False]
    assert meets_diet(flags, "orthodox_fasting").tolist() == [True, False, True, True]   # shellfish allowed


def test_ready_made_ingredients_count_only_in_the_ingredient_list():
    recipes = pd.DataFrame({"ingredients": [["flour", "coconut oil", "sugar"], ["cookie", "cream cheese"],
                                            ["asafoetida", "lentil"]],
                            "name": ["Vegan Cookies", "Cookie Pie", "Dal"]})
    out = add_keyword_flags(recipes, "ingredients", name_col="name")
    assert out["vegan"].tolist() == [True, False, True]            # the dish name is not a store cookie
    assert out["contains_dairy"].tolist() == [False, True, False]
    assert out["contains_gluten"].tolist() == [True, True, True]    # compounded hing is cut with wheat
    assert passes_safety_filter(pd.Series({"ingredient_list": ["flour", "sugar"], "recipe_name": "Vegan Cookies"}),
                                vegan=True)


def test_wines_named_without_the_word_wine():
    for text in ["chardonnay | butter", "tawny port | figs", "pinot noir | beef", "sangria", "dry cider | pork"]:
        assert keyword_flag(text, "contains_alcohol"), text
        assert keyword_flag(text, "contains_sulfites"), text
    for text in ["apple cider | cinnamon", "cider vinegar", "port salut | crackers", "rose water | sugar",
                 "red wine vinegar | oil"]:
        assert not keyword_flag(text, "contains_alcohol"), text


def test_spelling_variants_cover_accents_and_hyphens():
    assert spelling_variants("café beaujolais") == ["café beaujolais", "cafe beaujolais", "café-beaujolais",
                                                    "cafe-beaujolais"]
    assert spelling_variants("Port-Salut") == ["port-salut", "port salut"]
    assert spelling_variants("rosé", keep_accents=True) == ["rosé"]


def test_wine_names_and_groups_agree():
    names = wine_names()
    assert len(names) == len(set(names))
    assert {"gewürztraminer", "gewurztraminer", "rosé", "rose wine", "syrah", "pinot gris"} <= set(names)
    assert "rose" not in names
    groups = wine_name_groups()
    assert set(groups) == set(WINE_NAME_GROUPS)
    assert sorted(s for g in groups.values() for s in g["same_wine"]) == sorted(names)
    assert {"rosé water", "rose water", "rosé-water"} <= set(groups["rosé"]["not_wine"])
    assert not set(names) & set(WINE_NAME_EXCEPTIONS)


def test_wine_look_alikes_are_not_alcohol_but_real_wine_still_is():
    for text in ["rosé water | pistachios", "almond baklava with rosé-water", "virgin white sangria",
                 "non-alcoholic sangria punch | grape juice", "cafe beaujolais sour cream waffles",
                 "port huron-style coney sauce", "persian tomato and cucumber salad shiraz salad"]:
        assert not keyword_flag(text, "contains_alcohol"), text
    for text in ["rosé | strawberries", "rose wine | peaches", "gewürztraminer | onion", "syrah | lamb",
                 "virgin sangria | red wine", "cabernet-braised short ribs"]:
        assert keyword_flag(text, "contains_alcohol"), text
        assert keyword_flag(text, "contains_sulfites"), text


def test_every_keyword_matches_in_every_spelling():
    assert with_spellings(["jamón", "tri-tip", "rosé"]) == ["jamón", "jamon", "tri-tip", "tri tip", "rosé"]
    assert keyword_flag("crème fraîche | chives", "contains_dairy")          # keyword written "creme fraiche"
    assert keyword_flag("jalapeno | lime", "contains_nightshade")
    assert keyword_flag("jalapeño | lime", "contains_nightshade")
    assert keyword_flag("tri tip | rub", "contains_beef")                     # keyword written "tri-tip"
    assert not keyword_flag("rose | sugar", "contains_alcohol")              # the flower, not rosé
    assert explain_flag("crème fraîche", "contains_dairy") == ["creme fraiche"]
    assert explain_flag("jalapeño | lime", "contains_nightshade") == ["jalapeño"]   # once, as written


def test_exceptions_start_a_word_and_goat_dairy_is_not_vegan():
    assert keyword_flag("goat milk | sugar", "contains_dairy")               # "oat milk" is not inside it
    assert keyword_flag("pineapple butter | toast", "contains_dairy")        # nor "apple butter"
    assert not keyword_flag("oat milk | oats", "contains_dairy")
    assert not keyword_flag("red kidney beans | rice", "contains_high_purine")   # a phrase's end may run on
    for text in ["goat cheese | baguette", "goat-cheese medallion", "goats cheese | beet"]:
        assert keyword_flag(text, "vegetarian"), text
        assert not keyword_flag(text, "vegan"), text


def test_named_foods_from_round4_and_their_look_alikes():
    assert keyword_flag("pilchard | spaghetti", "contains_fish")
    assert not keyword_flag("pilchard | spaghetti", "vegetarian")
    assert keyword_flag("brisling sardines | toast", "contains_fish")
    assert keyword_flag("roasted chestnuts | sage", "contains_tree_nut")
    assert keyword_flag("marron glace | cream", "contains_tree_nut")
    assert not keyword_flag("water chestnut | soy sauce", "contains_tree_nut")
    assert not keyword_flag("chestnut mushroom | thyme", "contains_tree_nut")
    for flag in ["contains_red_meat", "contains_meat"]:
        assert keyword_flag("ground buffalo | chili bean", flag)
        for text in ["buffalo mozzarella | basil", "buffalo cauliflower bites | hot sauce"]:
            assert not keyword_flag(text, flag), text
    assert not keyword_flag("buffalo wing sauce | chicken wing", "contains_red_meat")   # chicken is poultry
    assert keyword_flag("buffalo mozzarella | basil | tomato", "vegetarian")


def test_term_groups_and_lookups():
    groups = term_groups(FOOD_NAME_GROUPS)
    assert set(groups) == set(FOOD_NAME_GROUPS)
    assert {"chestnut", "marron glace", "chataigne"} <= set(groups["chestnut"]["same"])
    assert "water chestnut" in groups["chestnut"]["not_this"]
    assert sorted(s for g in groups.values() for s in g["same"]) == sorted(term_names(FOOD_NAME_GROUPS))
    assert term_group_of("Brisling") == "sprat"
    assert term_group_of("syrah") == "shiraz"
    assert term_group_of("tofu") is None
    assert flags_for_term("chestnut") == ["contains_tree_nut"]
    assert "contains_fish" in flags_for_term("pilchard")
    assert flags_for_term("water chestnut") == []


def test_pet_meat_and_pet_food_are_never_served():
    assert keyword_flag("dog meat | chili paste", "contains_pet_meat")
    assert keyword_flag("bosintang", "contains_pet_meat")
    assert not keyword_flag("dog meat | chili paste", "vegetarian")
    for text in ["hot dog | bun", "firehouse hot dog meat sauce", "chili dog stew", "yuk gaejang | beef",
                 "catfish | cornmeal", "monkey bread | cinnamon"]:
        assert not keyword_flag(text, "contains_pet_meat"), text
    recipes = pd.DataFrame({
        "recipe_name": ["Beef Stew", "Peanut Butter Dog Biscuits", "Chicken Casserole for Dogs", "Bosintang",
                        "Hot Dog Stew", "Dog Food", "Dog Biscuit Cocktail", "Human Cat Food"],
        "ingredient_list": [["beef"], ["flour", "peanut butter"], ["chicken", "rice"], ["dog meat"],
                            ["hot dog"], ["chocolate chips", "rice chex"], ["beer", "lemonade"], ["tuna fish"]],
        "contains_pet_meat": [False, False, False, True, False, False, False, False],
        "contains_alcohol": [False, False, False, False, False, False, True, False]})
    kept, removed = remove_excluded_recipes(recipes)
    # Joke names for people food stay: chocolate and alcohol are poisonous to pets, "human" says who eats it
    assert kept["recipe_name"].tolist() == ["Beef Stew", "Hot Dog Stew", "Dog Food", "Dog Biscuit Cocktail",
                                            "Human Cat Food"]
    assert removed == {"meat from household pets": 1, "made for pets, not people": 2}
    # The safety filter rejects pet meat even when nobody asked to avoid it
    assert not passes_safety_filter(pd.Series({"ingredient_list": ["dog meat"], "recipe_name": "Stew"}))
    assert passes_safety_filter(pd.Series({"ingredient_list": ["beef"], "recipe_name": "Hot Dog Stew"}))


def test_alcohol_extracts_are_their_own_flag():
    assert keyword_flag("vanilla | flour | sugar", "contains_alcohol_extract")
    assert keyword_flag("angostura bitters | orange", "contains_alcohol_extract")
    assert not keyword_flag("vanilla ice cream | vanilla wafers", "contains_alcohol_extract")
    assert not keyword_flag("vanilla | flour | sugar", "contains_alcohol")      # a flag of its own
    for name in ["alcohol-free vanilla", "alcohol-free vanilla extract", "non-alcoholic vanilla", "vanilla glycerite"]:
        assert not keyword_flag(f"{name} | flour", "contains_alcohol_extract"), name


def test_policy_p18_halal_rule():
    halal = DIET_PROFILES["halal_friendly"]["without"]
    assert {"contains_alcohol_extract", "contains_carmine", "contains_rennet"} <= set(halal)
    assert "contains_shellfish" not in halal                                     # shrimp and molluscs are fine
    assert keyword_flag("milk | rennet tablet | sugar", "contains_rennet")
    assert not keyword_flag("milk | vegetable rennet", "contains_rennet")
    assert not keyword_flag("cheddar cheese | macaroni", "contains_rennet")    # cheese is not flagged


def test_medical_screens():
    assert keyword_flag("fava beans | lemon", "contains_fava")
    assert keyword_flag("falafel mix", "contains_fava")
    assert keyword_flag("tomatoes | basil", "contains_nightshade")
    assert not keyword_flag("sweet potato | black pepper", "contains_nightshade")
    assert not keyword_flag("serrano ham | melon", "contains_nightshade")
    assert keyword_flag("swordfish steaks", "contains_high_mercury_fish")
    assert keyword_flag("beef carpaccio", "contains_raw_animal")
    assert not keyword_flag("sushi rice | nori | cucumber", "contains_raw_animal")
    assert keyword_flag("brie | crackers", "contains_soft_cheese")
    assert keyword_flag("anchovies | beer", "contains_high_purine")
    assert not keyword_flag("kidney beans | root beer", "contains_high_purine")
    assert keyword_flag("parmesan cheese", "contains_high_tyramine")
    flags = pd.DataFrame([{**dict.fromkeys(FLAG_COLUMNS, False), "contains_red_meat": True}])
    assert not meets_diet(flags, "alpha_gal_friendly").iloc[0]


def test_allergen_sets_use_known_flags():
    for region, flags in ALLERGEN_SETS.items():
        assert set(flags) <= set(FLAG_COLUMNS), region
        assert len(flags) == len(set(flags)), region
    assert len(ALLERGEN_SETS["EU_UK"]) == 14
    assert len(ALLERGEN_SETS["US"]) == 9
    assert "contains_mollusc" not in ALLERGEN_SETS["US"]        # US "shellfish" means crustaceans
    assert "contains_buckwheat" in ALLERGEN_SETS["Japan"]
    # Buckwheat groats: labeled in Japan, not in the US (soba noodles would also be gluten:
    # most soba is made with some wheat flour)
    row = pd.Series({"ingredient_list": ["buckwheat groats", "onion"], "recipe_name": "Kasha"})
    assert not passes_safety_filter(row, avoid=ALLERGEN_SETS["Japan"])
    assert passes_safety_filter(row, avoid=ALLERGEN_SETS["US"])


def test_compound_evidence_suggests_only_well_supported_allergens():
    products = [{"product_name": "Ranch Dressing", "allergens_tags": ["en:milk", "en:eggs"]}] * 4 + [
        {"product_name": "Light Ranch Dressing", "allergens_tags": ["en:milk"]},
        {"product_name": "Salad kit with dressing", "allergens_tags": ["en:gluten"]},   # name does not match
    ]
    assert declared_allergens("ranch dressing", products) == (5, {"contains_dairy": 1.0, "contains_egg": 0.8})
    candidates = pd.DataFrame({"ingredient": ["ranch dressing", "mystery sauce"], "recipes": [300, 120]})

    def search(query):
        if query == "mystery sauce":
            raise ConnectionError("offline")
        return products

    evidence = compound_evidence(candidates, search)
    assert evidence.loc[0, "suggested_flags"] == "contains_dairy contains_egg"
    assert evidence.loc[1, "products"] == -1 and evidence.loc[1, "suggested_flags"] == ""
    # A saved table is reused: no new search, and the team's decision is kept
    evidence.loc[0, "team_decision"] = "approve"
    again = compound_evidence(candidates.head(1), lambda *_: [], previous=evidence)
    assert again.loc[0, "suggested_flags"] == "contains_dairy contains_egg"
    assert again.loc[0, "team_decision"] == "approve"


def test_policy_file_has_one_row_per_policy_and_known_statuses():
    policies = pd.read_csv(Path(__file__).resolve().parents[1] / "docs" / "flag_review" / "flag_policies.csv")
    assert policies["policy_id"].is_unique
    assert set(policies["status"]) <= {"approved", "proposed", "rejected"}
    approved = policies[policies["status"] == "approved"]
    assert approved["decided_by"].notna().all() and approved["decided_on"].notna().all()


# ------------------------------------------------------------------ cooking methods and fats (notebook 02)
def test_methods_from_instructions_finds_frying_and_ignores_side_phrases():
    deep = "Heat 2 inches of oil in a heavy pot to 350F. Drop by tablespoonfuls into hot oil and drain."
    assert methods_from_instructions(deep) == ["deep_fry"]   # plain "fry" words do not add pan_fry
    assert methods_from_instructions("Mix the yogurt, cucumber and mint in a bowl and chill for an hour.") == ["no_cook"]
    assert methods_from_instructions("Whisk the baking powder into the flour, cover and chill well.") == ["no_cook"]
    assert methods_from_instructions("Cut slits in the top crust to let steam escape and bake 40 minutes.") == ["bake_roast"]
    assert methods_from_instructions("Steam the asparagus until tender, about 5 minutes.") == ["steam"]
    assert methods_from_instructions(None) == []
    assert methods_from_tags("['oven', 'deep-fry', 'easy']") == ["deep_fry", "bake_roast"]
    assert methods_from_tags(float("nan")) == []


def test_fats_from_ingredients_skips_look_alikes_and_marks_plain_oil():
    fats = fats_from_ingredients(["peanut butter", "butter beans", "tuna in olive oil", "oil for frying",
                                  "clarified butter", "canola oil", "butter"])
    assert fats == ["oil_unspecified", "ghee", "canola_oil", "butter"]
    assert fats_from_ingredients(None) == []


def test_add_cooking_labels_flags_fried_dishes_with_unknown_fat_and_returns_a_copy():
    df = pd.DataFrame({
        "recipe_id": ["foodcom_1", "hf_2", "hf_3", "hf_4"],
        "recipe_name": ["Vegetable Pakoras", "Oven-Fried Chicken", "Fried Rice", "Garden Salad"],
        "ingredient_list": [["chickpea flour", "oil"], ["chicken"], ["rice", "peanut oil"], ["lettuce"]],
        "instructions": [None, None, None, None],
    })
    out = add_cooking_labels(df, {"foodcom_1": ["deep-fry"]})
    assert "frying_fat_unknown" not in df.columns
    assert out["fried_by_name"].tolist() == [True, False, True, False]
    assert out["frying_fat_unknown"].tolist() == [True, False, False, False]   # peanut oil is a known fat
    assert out["methods_tags"].tolist() == [["deep_fry"], [], [], []]
    assert out["has_tags"].tolist() == [True, False, False, False]
    expect_error(ValueError, add_cooking_labels, df.drop(columns="instructions"))


def test_cooking_fat_reference_file_matches_the_keyword_table():
    reference = pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "reference" / "cooking_fats.csv")
    assert not reference["fat_id"].duplicated().any()
    # every fat the rules can return has a row, so the agents can always look it up
    assert set(FAT_KEYWORDS) | {"oil_unspecified"} <= set(reference["fat_id"])
    low, high = reference["smoke_point_c_low"], reference["smoke_point_c_high"]
    assert (low.isna() == high.isna()).all() and (low.dropna() <= high.dropna()).all()
    assert len(fat_reference(reference)) == len(reference)


def test_fat_reference_joins_one_usda_row_per_fat():
    reference = pd.DataFrame({"fat_id": ["butter", "lard"], "usda_fdc_id": ["173410", None]})
    usda = pd.DataFrame({"fdc_id": [173410, 173410], "description": ["Butter, salted"] * 2,
                         "saturated_g_100g": [51.4] * 2, "mono_g_100g": [21.0] * 2, "poly_g_100g": [3.0] * 2})
    out = fat_reference(reference, usda)
    assert out["fat_id"].tolist() == ["butter", "lard"]                       # a food listed twice adds no row
    assert out["saturated_g_100g"].tolist()[0] == 51.4 and pd.isna(out["usda_description"].tolist()[1])
    expect_error(ValueError, fat_reference, pd.concat([reference, reference]))   # repeated fat_id


def test_top_fats_by_group_and_method_agreement():
    df = pd.DataFrame({"cuisine_family": ["Asian"] * 3 + ["European"],
                       "cooking_fats": [["sesame_oil"], ["sesame_oil", "peanut_oil"], ["oil_unspecified"], ["butter"]]})
    out = top_fats_by_group(df, "cuisine_family", min_recipes=2)
    assert out.to_dict("records") == [{"cuisine_family": "Asian", "recipes_with_fat": 2,
                                       "top_fats": "sesame_oil 100% | peanut_oil 50%"}]
    empty = top_fats_by_group(df, "cuisine_family", min_recipes=50)            # no group is big enough
    assert empty.empty and list(empty.columns) == ["cuisine_family", "recipes_with_fat", "top_fats"]
    labels = pd.DataFrame({"methods_instructions": [["bake_roast"], ["bake_roast"], [], ["deep_fry"]],
                           "methods_tags": [["bake_roast"], [], ["bake_roast"], ["deep_fry"]],
                           "has_instructions": [True, True, True, False], "has_tags": [True, True, True, True]})
    agreement = method_label_agreement(labels)
    assert agreement[["tagged", "rule", "both"]].loc[["bake_roast"]].to_numpy().tolist() == [[2, 2, 1]]
    assert agreement.loc["bake_roast", "rule_finds_tag"] == 0.5
    assert agreement.loc["deep_fry", "tagged"] == 0 and pd.isna(agreement.loc["deep_fry", "rule_finds_tag"])


def test_alcohol_left_after_cooking_is_a_range_that_never_clears_the_flag():
    assert alcohol_left_range([], None, None) == (0.70, 1.0)                    # not heated
    assert alcohol_left_range(["boil_simmer"], "Simmer 2 hours.", 150) == (0.05, 0.85)
    assert alcohol_left_range(["boil_simmer"], "Simmer.", 10) == (0.40, 0.85)
    assert alcohol_left_range(["pan_fry"], "Add brandy and flambe.", 20) == (0.35, 0.75)
    assert alcohol_left_range(["bake_roast"], "Bake.", float("nan")) == (0.05, 0.85)   # time unknown
    recipes = pd.DataFrame({"contains_alcohol": [True, False], "contains_alcohol_extract": [False, False],
                            "methods_instructions": [["boil_simmer"], []], "methods_tags": [[], []],
                            "instructions": ["Simmer for 1 hour.", ""], "minutes": [60, 10]})
    out = add_alcohol_estimate(recipes)
    left = out[["alcohol_left_min", "alcohol_left_max"]]
    assert left.iloc[0].tolist() == [0.25, 0.85]
    assert left.iloc[1].isna().tolist() == [True, True]                         # no alcohol: no estimate
    assert out["contains_alcohol"].tolist() == [True, False]                       # never cleared
    assert "alcohol_left_min" not in recipes                                        # input unchanged

def test_flag_reports_line_up_and_compare_with_foodcom_tags():
    df = pd.DataFrame({**{flag: [False, True] for flag in FLAG_COLUMNS},
                       "tags": ["['vegetarian']", "['vegetarian', 'gluten-free']"]})
    df["vegetarian"] = [True, False]
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        print_flag_counts(df, "test")
    lines = printed.getvalue().splitlines()[1:]
    assert len(lines) == len(FLAG_COLUMNS) and len({line.index(":") for line in lines}) == 1   # one column
    agreement = foodcom_tag_agreement(df)
    assert agreement.loc["vegetarian", "recipes"] == 2 and agreement.loc["vegetarian", "agree (%)"] == 50
    assert agreement.loc["gluten-free", "agree (%)"] == 0 and "vegan" not in agreement.index

if __name__ == "__main__":
    tests = [(name, test) for name, test in sorted(globals().items()) if name.startswith("test_")]
    failed = 0
    for name, test in tests:
        try:
            test()
            print(f"  pass  {name}")
        except Exception as e:  # noqa: BLE001 - report every failing test, then exit with an error
            failed += 1
            print(f"  FAIL  {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed} of {len(tests)} tests passed")
    sys.exit(1 if failed else 0)
