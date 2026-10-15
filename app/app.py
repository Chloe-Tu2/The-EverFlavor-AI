"""EverFlavor AI: the front end (Streamlit), "EverFlavor Kitchen".

How to run it (from the project folder):

    pip install -r config/requirements-app.txt
    streamlit run app/app.py

A browser tab opens at http://localhost:8501. Save this file and the page reloads.

How Streamlit works, in one sentence: the whole file runs top to bottom every time
someone clicks something, and each `st.something(...)` call draws one thing on the page.

The look: a pixel-art kitchen behind the page and a pixel chef who reads out the results.
The art is drawn by design/pixel-art/make_pixel_art.py (one kitchen per color theme); the
color themes are in THEMES below. Settings (bottom of the sidebar) switch the theme.
"""
import ast
import base64
import html
import sys
from functools import cache
from pathlib import Path

import pandas as pd
import streamlit as st

# Let Python find our package in src/ (same trick the notebooks use).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from everflavor.diets import DIET_PROFILES
from everflavor.flags import FLAG_RULES
from everflavor.llm import check_and_explain, choose_model
from everflavor.recommend import baseline_recommend
from everflavor.safety import UserProfile

DATA = ROOT / "data" / "processed"
ART = ROOT / "design" / "pixel-art" / "concept"

# Use the lightweight demo dataset when full data is unavailable.
if not (DATA / "recipes_test.parquet").exists():
    DATA = ROOT / "data" / "demo"

# Color themes. "Classic" is Eva's cooking-game palette and the default. Each theme has its own
# kitchen picture (scene) and the colors of the page drawn over it.
THEMES = {
    "Classic": {"scene": "classic", "panel": "#FFF8E7", "sidebar": "#FFF1E6", "border": "#8B4513",
                "text": "#4A2C2A", "heading": "#8B4513", "button": "#FFB6C1", "button_hover": "#FF8FAB",
                "shadow": "#D9A679", "bubble": "#FFFFFF"},
    "Morning": {"scene": "morning", "panel": "#FFF9EC", "sidebar": "#FFF4D6", "border": "#8A5427",
                "text": "#4A3122", "heading": "#B05A1E", "button": "#F2C14E", "button_hover": "#E6A91F",
                "shadow": "#E6B77C", "bubble": "#FFFDF5"},
    "Night": {"scene": "night", "panel": "#2A2138", "sidebar": "#241C31", "border": "#FF8FAB",
              "text": "#F3E9F5", "heading": "#FFD98A", "button": "#FF8FAB", "button_hover": "#FF6F95",
              "shadow": "#120D1A", "bubble": "#3A2E4A"},
    "Basil": {"scene": "basil", "panel": "#F7FBF2", "sidebar": "#EEF5E6", "border": "#457536",
              "text": "#2F3A26", "heading": "#457536", "button": "#9BD07F", "button_hover": "#7FBF5F",
              "shadow": "#C8DDB6", "bubble": "#FFFFFF"},
}


def nice(column: str) -> str:
    """'contains_tree_nut' -> 'Tree nut', 'halal_friendly' -> 'Halal'."""
    return column.removeprefix("contains_").removesuffix("_friendly").replace("_", " ").capitalize()


@st.cache_data   # load the data once, not on every click
def load_recipes() -> pd.DataFrame:
    parts = [DATA / f"recipes_{split}.parquet" for split in ("train", "val", "test")]
    return pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)


@cache
def art(name: str) -> str:
    """A pixel-art PNG as a data URI, so the page needs no file server ('' if it is missing)."""
    path = ART / f"{name}.png"
    return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode()}" if path.exists() else ""


def style(theme: dict) -> str:
    """The page's CSS for one theme: the kitchen behind everything, panels over it, pixel fonts."""
    scene = art(f"kitchen_{theme['scene']}")
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@400;700&display=swap');
:root {{
  --panel: {theme['panel']}; --sidebar: {theme['sidebar']}; --border: {theme['border']};
  --text: {theme['text']}; --heading: {theme['heading']}; --button: {theme['button']};
  --button-hover: {theme['button_hover']}; --shadow: {theme['shadow']}; --bubble: {theme['bubble']};
  --pixel-font: 'Pixelify Sans', 'Courier New', monospace;
}}
/* The kitchen fills the window; image-rendering keeps the pixels sharp when it is scaled up */
.stApp {{
  background: var(--sidebar) url('{scene}') center bottom / cover no-repeat fixed;
  image-rendering: pixelated;
  color: var(--text);
}}
[data-testid="stHeader"] {{ background: transparent; }}
/* The page sits on a panel over the kitchen, like a recipe card pinned to the wall */
.block-container {{
  background: color-mix(in srgb, var(--panel) 94%, transparent);
  border: 4px solid var(--border);
  box-shadow: 8px 8px 0 var(--shadow);
  margin-top: 3rem; margin-bottom: 3rem;
  padding: 2rem 2.5rem;
  image-rendering: auto;
}}
[data-testid="stSidebar"] {{ background: var(--sidebar); border-right: 4px solid var(--border); }}
/* Every text color comes from the theme, so a computer in dark mode does not paint white text on cream */
.stApp, .stApp p, .stApp li, .stApp label, [data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"] p, [data-testid="stMetricValue"], [data-testid="stSidebar"] * {{ color: var(--text); }}
h1, h2, h3, button[role="tab"] p {{ color: var(--heading) !important; font-family: var(--pixel-font); }}
h1 {{ letter-spacing: 0.02em; }}
/* Inputs stay light with dark text in every theme, so they are always readable */
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, textarea, div[data-baseweb="base-input"] {{
  background: #FFFDF8 !important; border: 2px solid var(--border) !important; border-radius: 0 !important;
}}
div[data-baseweb="input"] input, textarea, div[data-baseweb="select"] * {{ color: #2B1E1A !important; }}
/* Pixel buttons: square corners, a hard shadow that "presses" on click */
.stButton > button {{
  background: var(--button); color: #2B1E1A; border: 3px solid var(--border); border-radius: 0;
  font-family: var(--pixel-font); font-weight: 700; box-shadow: 4px 4px 0 var(--shadow);
}}
.stButton > button:hover {{ background: var(--button-hover); border-color: var(--border); color: #2B1E1A; }}
.stButton > button:active {{ transform: translate(3px, 3px); box-shadow: 1px 1px 0 var(--shadow); }}
/* Recipe cards */
div[data-testid="stVerticalBlockBorderWrapper"] {{
  background: var(--panel); border: 3px solid var(--border) !important; border-radius: 0;
  box-shadow: 5px 5px 0 var(--shadow);
}}
[data-testid="stImage"] img {{ border: 3px solid var(--border); }}
/* The chef and the speech bubble */
.chef-row {{ display: flex; gap: 1rem; align-items: flex-end; margin: 0.5rem 0 1.25rem; }}
.chef-row img {{ width: 96px; height: 96px; image-rendering: pixelated; flex: none; }}
.bubble {{
  position: relative; background: var(--bubble); color: var(--text); border: 3px solid var(--border);
  padding: 0.75rem 1rem; font-family: var(--pixel-font); font-size: 1.05rem; line-height: 1.4;
  box-shadow: 4px 4px 0 var(--shadow); min-width: 0;
}}
.bubble::before {{
  content: ''; position: absolute; left: -12px; bottom: 14px; border: 6px solid transparent;
  border-right-color: var(--border);
}}
@media (max-width: 640px) {{ .block-container {{ padding: 1.25rem 1rem; }} .chef-row img {{ width: 64px; height: 64px; }} }}
@media (prefers-reduced-motion: reduce) {{ .stButton > button:active {{ transform: none; }} }}
</style>
"""


def chef_says(place, mood: str, message: str) -> None:
    """Draw the chef with a speech bubble. mood: 'happy', 'alert' or 'thinking'.

    The chef only reads out what the back end decided; it never decides anything itself.
    """
    sprite = art(f"chef_{mood}")
    image = f'<img src="{sprite}" alt="Pixel chef, {mood}">' if sprite else ""
    place.markdown(f'<div class="chef-row">{image}<div class="bubble">{html.escape(message)}</div></div>',
                   unsafe_allow_html=True)


# ---------- Page setup ----------
st.set_page_config(page_title="EverFlavor Kitchen", page_icon="🍲", layout="wide")
theme_name = st.session_state.get("theme", "Classic")
st.markdown(style(THEMES[theme_name]), unsafe_allow_html=True)
st.title("EverFlavor Kitchen")
st.caption("Discover recipes, explore ingredients, and cook safely.")
chef = st.empty()   # the chef's line, filled in below once we know what happened

if not (DATA / "recipes_test.parquet").exists():
    chef_says(chef, "thinking", "My pantry is empty! Run notebook 01 first to build the recipe data.")
    st.stop()

recipes = load_recipes()


@st.cache_data(ttl=60)   # ask Ollama at most once a minute
def local_ai() -> dict:
    return choose_model()   # {"kind": "ollama" or "rules", "model", "reason"}


ai = local_ai()

# ---------- Sidebar: the user's profile, then settings ----------
with st.sidebar:
    st.header("Your profile")
    avoid = st.multiselect("I can't eat", options=sorted(FLAG_RULES), format_func=nice)
    diets = st.multiselect("I follow", options=sorted(DIET_PROFILES), format_func=nice)
    vegetarian = st.checkbox("Vegetarian")
    vegan = st.checkbox("Vegan")
    calories = st.slider("Calories per meal", min_value=200, max_value=1500, value=600, step=50)
    st.divider()
    if ai["kind"] == "ollama":
        use_ai = st.checkbox(f"Explain problems with local AI ({ai['model']})", value=True)
    else:
        use_ai = False
        st.caption(f"Local AI is off: {ai['reason']}")
    with st.expander("⚙ Settings"):
        st.selectbox("Kitchen theme", list(THEMES), key="theme",
                     help="Classic is the team's original look. Night is easier on the eyes in the dark.")

profile = UserProfile(avoid=tuple(avoid), diets=tuple(diets), vegetarian=vegetarian,
                      vegan=vegan, calories_per_meal=calories)
chef_says(chef, "happy", "Welcome to the kitchen! Tell me what you can't eat in the sidebar, "
                         "then find a recipe or check one of yours.")

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
            chef_says(chef, "thinking", "Hmm, nothing matches all your choices. Try removing one.")
        else:
            chef_says(chef, "happy", f"Here {'is' if len(results) == 1 else 'are'} {len(results)} "
                                     f"{'idea' if len(results) == 1 else 'ideas'} close to {calories} calories. "
                                     "Every one passed the safety check for your profile.")
        for _, row in results.iterrows():
            with st.container(border=True):
                photo = row.get("image_url")
                if isinstance(photo, str) and photo.startswith("https://"):
                    picture, info = st.columns([1, 2])
                    picture.image(photo, width="stretch")
                else:
                    info = st.container()
                info.subheader(row["recipe_name"].title())
                left, middle, right = info.columns(3)
                left.metric("Calories", f"{row['calories_per_serving']:.0f}")
                middle.metric("Protein", f"{row['protein_g']:.0f} g")
                minutes = row.get("minutes")
                right.metric("Minutes", f"{minutes:.0f}" if pd.notna(minutes) else "N/A")
                ingredients = row["ingredient_list"]

                if isinstance(ingredients, str):
                    try:
                        ingredients = ast.literal_eval(ingredients)
                    except (ValueError, SyntaxError):
                        ingredients = [ingredients]

                info.write("**Ingredients:** " + ", ".join(map(str, ingredients)))

with check_tab:
    st.write("Paste a recipe (one ingredient per line) to see if it fits your profile.")
    name = st.text_input("Dish name", "Thai Peanut Bowl")
    lines = st.text_area("Ingredients", "2 cups jasmine rice\n3 tbsp satay sauce\n1 lb chicken breast")

    if st.button("Check it"):
        # The safety gate decides; the local AI (if on) only explains a failure, and its words are
        # replaced by a plain sentence when they do not match the gate's answer.
        with st.spinner("Checking..."):
            report = check_and_explain(lines.splitlines(), name, profile, model=ai["model"] if use_ai else None)
        if report["passed"]:
            chef_says(chef, "happy", f"{name} is safe for your profile. Happy cooking!")
            st.success("Safe for your profile.")
        else:
            first = report["problems"][0]
            chef_says(chef, "alert", f"Watch out! \"{first['line']}\" breaks {nice(first['rule'])}"
                                     + (f", and I found {len(report['problems']) - 1} more."
                                        if len(report["problems"]) > 1 else "."))
            st.error(f"{len(report['problems'])} problem(s) found:")
            for problem in report["problems"]:
                st.write(f"- **{problem['line']}**: breaks *{nice(problem['rule'])}* "
                         f"(matched: {problem['matched']})")
        st.info(report["text"])
        st.caption(f"Explained by: {report['explained_by']}. Rules checked: "
                   + ", ".join(nice(r) for r in report["checked"]))
