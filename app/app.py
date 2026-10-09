"""EverFlavor AI: a starter front end (Streamlit).

How to run it (from the project folder):

    pip install -r config/requirements-app.txt
    streamlit run app/app.py

A browser tab opens at http://localhost:8501. Save this file and the page reloads.

How Streamlit works, in one sentence: the whole file runs top to bottom every time
someone clicks something, and each `st.something(...)` call draws one thing on the page.
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Let Python find our package in src/ (same trick the notebooks use).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.diets import DIET_PROFILES
from everflavor.flags import FLAG_RULES
from everflavor.recommend import baseline_recommend
from everflavor.safety import UserProfile, check_recipe

DATA = ROOT / "data" / "processed"


def nice(column: str) -> str:
    """'contains_tree_nut' -> 'Tree nut', 'halal_friendly' -> 'Halal'."""
    return column.removeprefix("contains_").removesuffix("_friendly").replace("_", " ").capitalize()


@st.cache_data   # load the data once, not on every click
def load_recipes() -> pd.DataFrame:
    parts = [DATA / f"recipes_{split}.parquet" for split in ("train", "val", "test")]
    return pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)


# ---------- Page setup ----------
st.set_page_config(page_title="EverFlavor AI", page_icon="🍲", layout="wide")
st.title("🍲 EverFlavor AI")
st.caption("Recipes you can safely eat. Starter version for the team.")

if not (DATA / "recipes_test.parquet").exists():
    st.error("No recipe data yet. Run notebooks/01_data_acquisition_EverFlavor_V3.ipynb first.")
    st.stop()

recipes = load_recipes()

# ---------- Sidebar: the user's profile ----------
with st.sidebar:
    st.header("Your profile")
    avoid = st.multiselect("I can't eat", options=sorted(FLAG_RULES), format_func=nice)
    diets = st.multiselect("I follow", options=sorted(DIET_PROFILES), format_func=nice)
    vegetarian = st.checkbox("Vegetarian")
    vegan = st.checkbox("Vegan")
    calories = st.slider("Calories per meal", min_value=200, max_value=1500, value=600, step=50)

profile = UserProfile(avoid=tuple(avoid), diets=tuple(diets), vegetarian=vegetarian,
                      vegan=vegan, calories_per_meal=calories)

# ---------- Two tabs ----------
find_tab, check_tab = st.tabs(["🔎 Find recipes", "✅ Check my recipe"])

with find_tab:
    families = ["Any"] + sorted(recipes["cuisine_family"].dropna().unique())
    cuisine = st.selectbox("Cuisine", families)
    how_many = st.number_input("How many ideas?", min_value=1, max_value=20, value=5)

    if st.button("Find recipes", type="primary"):
        results = baseline_recommend(
            recipes,
            cuisine_family=None if cuisine == "Any" else cuisine,
            calorie_target=calories,
            vegetarian_only=vegetarian,
            vegan_only=vegan,
            avoid=avoid,
            diets=diets,
            top_n=int(how_many),
        )
        if results.empty:
            st.warning("Nothing matches all your choices. Try removing one.")
        for _, row in results.iterrows():
            with st.container(border=True):
                st.subheader(row["recipe_name"].title())
                left, middle, right = st.columns(3)
                left.metric("Calories", f"{row['calories_per_serving']:.0f}")
                middle.metric("Protein", f"{row['protein_g']:.0f} g")
                right.metric("Minutes", f"{row['minutes']:.0f}" if pd.notna(row["minutes"]) else "?")
                st.write("**Ingredients:** " + ", ".join(row["ingredient_list"]))

with check_tab:
    st.write("Paste a recipe (one ingredient per line) to see if it fits your profile.")
    name = st.text_input("Dish name", "Thai Peanut Bowl")
    lines = st.text_area("Ingredients", "2 cups jasmine rice\n3 tbsp satay sauce\n1 lb chicken breast")

    if st.button("Check it"):
        report = check_recipe(lines.splitlines(), name, profile)
        if report["passed"]:
            st.success("Safe for your profile.")
        else:
            st.error(f"{len(report['problems'])} problem(s) found:")
            for problem in report["problems"]:
                st.write(f"- **{problem['line']}**: breaks *{nice(problem['rule'])}* "
                         f"(matched: {problem['matched']})")
        st.caption("Rules checked: " + ", ".join(nice(r) for r in report["checked"]))
