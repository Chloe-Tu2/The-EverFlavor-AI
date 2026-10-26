"""EverFlavor AI: the front end (Streamlit), "EverFlavor Kitchen".

How to run it (from the project folder):

    pip install -r config/requirements-app.txt
    streamlit run app/app.py

A browser tab opens at http://localhost:8501. Save this file and the page reloads.

How Streamlit works, in one sentence: the whole file runs top to bottom every time
someone clicks something, and each `st.something(...)` call draws one thing on the page.

The look: a pixel-art kitchen behind the page and a pixel chef who reads out the results.
The art is drawn by design/pixel-art/make_pixel_art.py (one kitchen per color theme); the
color themes are in app/themes.py. Settings (top right of the page) switch the theme.
"""
import ast
import base64
import html
import random
import re
import sys
from functools import cache
from pathlib import Path
from typing import cast
from urllib.parse import quote

import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components

# Let Python find our package in src/ (same trick the notebooks use).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from chef_lines import (  # app/chef_lines.py: what the chef says, with its sources
    greeting,
    line,
)
from themes import NIGHT_COLORS, THEMES  # app/themes.py: each kitchen's page colors
from updates import UPDATES  # app/updates.py: the What's new notes

from everflavor import __version__
from everflavor.cuisine import ORIGIN_LABELS
from everflavor.diets import DIET_PROFILES
from everflavor.dish_names import clean_title
from everflavor.dish_steps import methods_of, split_minutes, step_breakdown
from everflavor.flags import FLAG_RULES
from everflavor.llm import check_and_explain, choose_model
from everflavor.recommend import baseline_recommend, what_blocks, why_it_fits
from everflavor.safety import UserProfile

DATA = ROOT / "data" / "processed"
ART = ROOT / "design" / "pixel-art" / "assets"   # drawn by design/pixel-art/make_pixel_art.py

# Use the lightweight demo dataset when full data is unavailable.
if not (DATA / "recipes_test.parquet").exists():
    DATA = ROOT / "data" / "demo"

# The chef in kitchens without their own: the classic white-hat chef from the team's references
# (design/pixel-art/make_chefs.py)
DEFAULT_CHEF = "ref_classic_"
# With "Match the kitchen to the cuisine" on (Settings), searching a cuisine family opens its kitchen
# (each family opens the kitchen of its biggest country in the data: China leads Asian recipes after India, which
# has no kitchen yet; Morocco leads African; Italy, Mexico and Lebanon the others. Japanese is in Settings.)
# A country opens the kitchen of its region (docs/plans/CUISINE_REGIONS.md); countries without a fitting kitchen
# yet open Classic rather than a wrong one
COUNTRY_KITCHENS = {
    **dict.fromkeys(["China", "Taiwan"], "Chinese"), "Japan": "Japanese", "Mexico": "Mexican",
    **dict.fromkeys(["Italy", "Greece", "Spain", "Portugal", "France"], "Mediterranean"),
    **dict.fromkeys(["Lebanon", "Turkey", "Iran", "Egypt", "Saudi Arabia", "Iraq", "Palestine", "Israel", "Syria"],
                    "Middle Eastern"),
    **dict.fromkeys(["Morocco", "Algeria", "Tunisia", "Libya"], "Moroccan"),
}
MIN_COUNTRY_RECIPES = 50          # a country is in the Country list with at least this many recipes
# Every way of naming where a dish is from (labels, countries, regions; lowercase) -> (country, region or None)
PLACE_WORDS = {**{label: place for label, place in ORIGIN_LABELS.items() if ":" not in label},
               **{country.lower(): (country, None) for country, _ in ORIGIN_LABELS.values()},
               **{region.lower(): (country, region) for country, region in ORIGIN_LABELS.values() if region}}


def read_search(query: object) -> tuple[str | None, str | None, list[str]]:
    """What a search asks for: the country and region it names, if any ("korean", "Louisiana", "Japan"), and the
    words left for the dish's name ("korean bbq" -> South Korea, ["bbq"]). The longest place name wins."""
    text = str(query or "").lower().split(" (")[0].strip()
    for place in sorted(PLACE_WORDS, key=len, reverse=True):
        padded = f" {text} "
        if f" {place} " in padded:
            country, region = PLACE_WORDS[place]
            return country, region, padded.replace(f" {place} ", " ").split()
    return None, None, text.split()
CUISINE_KITCHENS = {"Asian": "Chinese", "African": "Moroccan", "European": "Mediterranean",
                    "Latin American": "Mexican", "Middle Eastern": "Middle Eastern"}


def nice(column: str) -> str:
    """'contains_tree_nut' -> 'Tree nut', 'halal_friendly' -> 'Halal'."""
    return column.removeprefix("contains_").removesuffix("_friendly").replace("_", " ").capitalize()


def nice_diet(diet: str) -> str:
    """A diet as people pick it: 'halal_friendly' -> 'Halal-friendly' (a screen of the ingredients, never the
    diet itself), 'pescatarian' -> 'Pescatarian'."""
    return f"{nice(diet)}-friendly" if diet.endswith("_friendly") else nice(diet)


PHOTO_CUTOFF = -0.03     # clip_score below this: the photo does not show the dish (a first cutoff; the team refines it)


@st.cache_resource   # load the data once and share it (read only), not a fresh copy on every click
def load_recipes() -> pd.DataFrame:
    parts = [DATA / f"recipes_{split}.parquet" for split in ("train", "val", "test")]
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    # The photos and estimated times made next to the data (scripts/recipe_extras.py), when they are there
    for extra in ("recipe_photos", "recipe_times"):
        path = DATA / f"{extra}.parquet"
        if path.exists() and "recipe_id" in df:
            side = pd.read_parquet(path)
            new = [c for c in side.columns if c == "recipe_id" or c not in df.columns]   # notebook 01 may have them
            if len(new) > 1:
                df = df.merge(side[new], on="recipe_id", how="left")
    # Food.com recipes' own photos (notebook 11, a CC0 dataset): only where a recipe has no photo yet, with the same
    # logo marks and, when it has run, the same image check (photo_check_foodcom.parquet)
    foodcom = DATA / "foodcom_photos.parquet"
    if foodcom.exists() and "recipe_id" in df:
        side = pd.read_parquet(foodcom, columns=["recipe_id", "image_url", "photo_ok"])
        side_check = DATA / "photo_check_foodcom.parquet"
        if side_check.exists():
            scores = pd.read_parquet(side_check, columns=["recipe_id", "clip_score"])
            side.loc[side["recipe_id"].isin(scores.loc[scores["clip_score"] < PHOTO_CUTOFF, "recipe_id"]),
                     "photo_ok"] = False
        side = side.rename(columns={"image_url": "foodcom_url", "photo_ok": "foodcom_ok"})
        df = df.merge(side, on="recipe_id", how="left")
        if "image_url" not in df:
            df["image_url"], df["photo_ok"] = None, pd.NA
        missing = df["image_url"].isna() & df["foodcom_url"].notna()
        df.loc[missing, "image_url"] = df.loc[missing, "foodcom_url"]
        df.loc[missing, "photo_ok"] = df.loc[missing, "foodcom_ok"]
        df = df.drop(columns=["foodcom_url", "foodcom_ok"])
    # A photo the image check says does not show the dish (scripts/recipe_photos/check_photos.py, CLIP; cutoff from
    # a hand-checked sample, RECIPE_PHOTOS.md step 5) is hidden like a logo
    check = DATA / "photo_check.parquet"
    if check.exists() and "photo_ok" in df:
        scores = pd.read_parquet(check, columns=["recipe_id", "clip_score"])
        doubtful = df["recipe_id"].isin(scores.loc[scores["clip_score"] < PHOTO_CUTOFF, "recipe_id"])
        df.loc[doubtful, "photo_ok"] = False
    # Free photos of dishes in general (scripts/dish_photos/), only for recipes with no photo of their own and only
    # the dishes the review has not turned down (data/reference/dish_photo_review.csv)
    dish_photos, review = DATA / "dish_photos.parquet", ROOT / "data" / "reference" / "dish_photo_review.csv"
    if dish_photos.exists() and "recipe_id" in df:
        extra = pd.read_parquet(dish_photos, columns=["recipe_id", "dish_qid", "dish_label", "thumb_url", "file_page",
                                                      "credit"])
        if review.exists():
            refused = pd.read_csv(review).query("keep == 'no'")["dish_qid"]
            extra = extra[~extra["dish_qid"].isin(refused)]
        df = df.merge(extra, on="recipe_id", how="left")
    return df


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
@import url('https://fonts.googleapis.com/css2?family=Jersey+10&family=VT323&display=swap');
:root {{
  --panel: {theme['panel']}; --sidebar: {theme['sidebar']}; --border: {theme['border']};
  --text: {theme['text']}; --heading: {theme['heading']}; --button: {theme['button']};
  --button-hover: {theme['button_hover']}; --shadow: {theme['shadow']}; --bubble: {theme['bubble']};
  --pixel-font: 'Jersey 10', 'Courier New', monospace;   /* titles, tabs, buttons, numbers */
  --pixel-text: 'VT323', 'Courier New', monospace;       /* the chef's lines, small labels */
  /* One scale each for space, text and shadows: every size below comes from these */
  --space-1: 0.25rem; --space-2: 0.5rem; --space-3: 0.75rem; --space-4: 1rem; --space-5: 1.5rem;
  --fs-1: 1rem; --fs-2: 1.35rem; --fs-3: 1.6rem; --fs-4: 2rem; --fs-5: 3.4rem;
  --shadow-1: 4px 4px 0 var(--shadow); --shadow-2: 6px 6px 0 var(--shadow); --shadow-3: 8px 8px 0 var(--shadow);
}}
/* The kitchen fills the window; image-rendering keeps the pixels sharp when it is scaled up */
.stApp {{
  background: var(--sidebar) url('{scene}') center bottom / cover no-repeat fixed;
  image-rendering: pixelated;
  color: var(--text);
}}
[data-testid="stHeader"] {{ background: transparent; }}
/* The title, the chef and the tools stand in the kitchen; only the tools sit on a panel, so the kitchen shows */
.block-container {{ max-width: 1100px; padding: 2.5rem 1.5rem 4rem; image-rendering: auto; }}
/* The title hangs on a wooden sign */
.stApp h1 {{
  display: inline-block; background: var(--panel); border: 4px solid var(--border);
  box-shadow: var(--shadow-2); padding: 0.4rem 1.1rem !important;
}}
.tagline {{
  display: inline-block; background: var(--panel); color: var(--text); border: 2px solid var(--border);
  padding: var(--space-1) var(--space-3); margin: var(--space-2) 0 0; font-size: var(--fs-1);
}}
/* The tools: a recipe card pinned over the counter */
[data-testid="stTabs"] {{
  background: color-mix(in srgb, var(--panel) 96%, transparent); border: 4px solid var(--border);
  box-shadow: var(--shadow-3); padding: var(--space-3) var(--space-5) var(--space-5);
}}
[data-testid="stSidebar"] {{ background: var(--sidebar); border-right: 4px solid var(--border); }}
/* Every text color comes from the theme, so a computer in dark mode does not paint white text on cream */
.stApp, .stApp p, .stApp li, .stApp label, [data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"] p, [data-testid="stMetricValue"], [data-testid="stSidebar"] * {{ color: var(--text); }}
h1, h2, h3, [data-testid="stTab"] p {{
  color: var(--heading) !important; font-family: var(--pixel-font) !important; font-weight: 400 !important;
  letter-spacing: 0.02em;
}}
.stApp h1 {{ font-size: var(--fs-5) !important; line-height: 1.1 !important; }}
.stApp h3 {{ font-size: var(--fs-4) !important; }}
h1 {{ letter-spacing: 0.02em; }}
/* Inputs stay light with dark text in every theme, so they are always readable */
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, textarea, div[data-baseweb="base-input"] {{
  background: #FFFDF8 !important; border: 2px solid var(--border) !important; border-radius: 0 !important;
}}
div[data-baseweb="input"] input, textarea, div[data-baseweb="select"] * {{ color: #2B1E1A !important; }}
[data-testid="stTextInputRootElement"], div[data-baseweb="input"] {{ border-radius: 0 !important; }}
/* Chosen items in "I can't eat" / "I follow": the theme's button color, so the dark text stays readable */
[data-testid="stMultiSelectTagsContainer"] [data-tag] {{
  background: var(--button) !important; color: #2B1E1A !important; border: 2px solid var(--border) !important;
  border-radius: 0 !important;
}}
[data-testid="stMultiSelectTagsContainer"] [data-tag] * {{ color: #2B1E1A !important; }}
/* Pixel buttons: square corners, a hard shadow that "presses" on click */
.stButton button, [data-testid="stDownloadButton"] button {{
  background: var(--button); color: #2B1E1A; border: 3px solid var(--border); border-radius: 0;
  font-family: var(--pixel-font); font-size: var(--fs-2); font-weight: 400; box-shadow: var(--shadow-1); min-height: 44px;
}}
.stButton button:hover, [data-testid="stDownloadButton"] button:hover {{ background: var(--button-hover); border-color: var(--border); color: #2B1E1A; }}
.stButton button:active, [data-testid="stDownloadButton"] button:active {{ transform: translate(3px, 3px); box-shadow: 1px 1px 0 var(--shadow); }}
/* The label inside a button takes the button's pixel font and size (Streamlit sets its own on the <p>) */
.stButton button p, [data-testid="stDownloadButton"] button p {{ font-family: var(--pixel-font) !important; font-size: var(--fs-2) !important; color: inherit; }}
.stButton button p {{ white-space: normal !important; overflow: visible !important; text-overflow: clip !important; line-height: 1.1; }}
/* The main action stands out; the others are quieter, on the panel's color */
.stButton button[kind="secondary"], [data-testid="stDownloadButton"] button {{ background: var(--panel); }}
/* Filter pills: square chips on the panel; a chosen one takes the button color */
[data-testid="stButtonGroup"] button {{ border-radius: 0 !important; border: 2px solid var(--border) !important;
  background: var(--panel) !important; color: var(--text) !important; min-height: 36px; }}
[data-testid="stButtonGroup"] button[aria-pressed="true"], [data-testid="stButtonGroup"] button[aria-checked="true"] {{
  background: var(--button) !important; color: #2B1E1A !important; font-weight: 600; }}
/* Small print at full strength: Streamlit fades captions, which lowers their contrast below AA */
[data-testid="stCaptionContainer"] {{ opacity: 1 !important; }}
/* Dialogs (the setup, About this dish) in the pixel style: square, outlined, a hard shadow */
[data-testid="stDialog"] > div {{ border-radius: 0 !important; border: 4px solid var(--border); box-shadow: var(--shadow-3);
  background: var(--panel) !important; }}
/* Recipe cards (each container has a key, recipe-card-<n>, which Streamlit turns into a class) */
.stApp [class*="st-key-recipe-card"] {{
  background: var(--panel); border: 3px solid var(--border) !important; border-radius: 0 !important;
  box-shadow: var(--shadow-2); padding: var(--space-4) var(--space-5);
}}
[data-testid="stImage"] img {{ border: 3px solid var(--border); width: 100%; aspect-ratio: 4 / 3;
  object-fit: contain; background: var(--panel); }}   /* the whole photo, never cropped or zoomed */
/* The chef and the speech bubble */
.chef-row {{ display: flex; gap: 1.25rem; align-items: flex-end; margin: 0.5rem 0 1.25rem; }}
.chef {{ width: 128px; height: 128px; flex: none; background: center / contain no-repeat; image-rendering: pixelated; }}
.bubble {{
  position: relative; flex: 1 1 auto; overflow-wrap: anywhere; background: var(--bubble); color: var(--text); border: 3px solid var(--border);
  padding: 0.6rem 1rem; font-family: var(--pixel-text); font-size: var(--fs-3); line-height: 1.15;
  box-shadow: var(--shadow-1); min-width: 0;
}}
.bubble::before {{
  content: ''; position: absolute; left: -12px; bottom: 14px; border: 6px solid transparent;
  border-right-color: var(--border);
}}
/* Pixel icons instead of emoji: on the tabs, the Settings knob, and the recipe stats */
[data-testid="stTab"] p::before, [data-testid="stPopover"] button p::before, .ico {{
  content: ''; display: inline-block; vertical-align: middle; background: center / contain no-repeat;
  image-rendering: pixelated;
}}
[data-testid="stTab"] p::before {{ width: 40px; height: 40px; margin-right: 0.5rem; }}
[data-testid="stTab"][data-key="0"] p::before {{ background-image: url('{art("icon_find")}'); }}
[data-testid="stTab"][data-key="1"] p::before {{ background-image: url('{art("icon_check")}'); }}
[data-testid="stTab"][data-key="2"] p::before {{ background-image: url('{art("icon_map")}'); }}
[data-testid="stTab"] p {{ font-size: var(--fs-3); }}
/* Top right: the What's new bell and Settings (the oven knob), pixel buttons */
[data-testid="stPopover"] {{ display: flex; justify-content: flex-end; }}
[data-testid="stPopover"] button {{
  background: var(--panel); border: 3px solid var(--border); border-radius: 0; box-shadow: var(--shadow-1);
}}
[data-testid="stPopover"] button p {{ font-family: var(--pixel-font); font-size: var(--fs-2); color: var(--text); }}
[data-testid="stPopover"] button p::before {{ width: 24px; height: 24px; margin-right: 0.4rem; }}
.st-key-settings [data-testid="stPopover"] button p::before {{ background-image: url('{art("icon_settings")}'); }}
.st-key-saved-list [data-testid="stPopover"] button p::before {{ background-image: url('{art("icon_cloche")}'); }}
.st-key-whats-new [data-testid="stPopover"] button p::before {{ background-image: url('{art("icon_bell")}'); }}
/* A red dot and a little ring until this browser has opened the newest notes (set by kitchen_scene.html) */
.st-key-whats-new button {{ position: relative; }}
html[data-ef-news="1"] .st-key-whats-new button::after {{
  content: ''; position: absolute; top: -7px; right: -7px; width: 12px; height: 12px;
  background: #D9483B; border: 2px solid var(--border);
}}
html[data-ef-news="1"] .st-key-whats-new button p::before {{ animation: ring 2.4s steps(2) infinite; }}
@keyframes ring {{ 0%, 80%, 100% {{ transform: none; }} 85% {{ transform: rotate(-14deg); }} 90% {{ transform: rotate(14deg); }} }}
[data-testid="stPopoverBody"] {{
  background: var(--panel) !important; border: 3px solid var(--border) !important; border-radius: 0 !important;
  box-shadow: var(--shadow-2) !important; color: var(--text);
}}
[data-testid="stPopoverBody"] p, [data-testid="stPopoverBody"] li {{ color: var(--text); }}
.no-photo {{
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.5rem;
  aspect-ratio: 4 / 3; background: var(--sidebar); border: 3px dashed var(--border); color: var(--text);
  font-family: var(--pixel-text); font-size: var(--fs-2); text-align: center; padding: var(--space-2);
}}
.no-photo .ico {{ width: 128px; height: 128px; image-rendering: auto; }}  /* a real photo, so smooth scaling */
.no-photo small {{ font-size: var(--fs-1); }}
.updates h5 {{ font-family: var(--pixel-font); font-weight: 400; font-size: var(--fs-2); margin: var(--space-2) 0 0; color: var(--heading); }}
.updates ul {{ margin: 0.2rem 0 0.6rem 1.1rem; padding: 0; }}
.stats {{ display: flex; flex-wrap: wrap; gap: 0.75rem 1.5rem; margin: 0.25rem 0 0.75rem; }}
.stat {{ display: flex; align-items: center; gap: var(--space-2); font-family: var(--pixel-font); font-size: var(--fs-3); }}
.stat .ico, .bubble .ico {{ width: 32px; height: 32px; }}
.bubble .ico {{ margin-right: 0.5rem; }}
.stat small {{ font-family: var(--pixel-text); font-size: var(--fs-2); }}
/* The concept layout: the kitchen open under the title, the chef standing in it above the tabs (on every screen;
   the sidebar copy is not shown) */
.kitchen-view {{ height: 12vh; }}
.st-key-chef-main {{ max-width: 760px; }}
.st-key-chef-main .chef {{ width: 150px; height: 150px; }}
.st-key-chef-side {{ margin-top: 0.5rem; }}
.st-key-chef-side .chef-row {{ flex-direction: column-reverse; align-items: center; gap: 0.9rem; }}
.st-key-chef-side .chef {{ width: 132px; height: 132px; }}
.st-key-chef-side .bubble {{ font-size: 1.15rem; line-height: 1.1; width: 100%; padding: 0.45rem 0.7rem; }}
.st-key-chef-side .bubble::before {{
  left: calc(50% - 6px); bottom: -12px; border-right-color: transparent; border-top-color: var(--border);
}}
.st-key-chef-side {{ display: none; }}
/* The phone's "Your profile" button (the sidebar is hidden on phones) */
.open-profile {{ display: none; }}
@media (max-width: 640px) {{
  .open-profile {{ display: block; width: 100%; min-height: 44px; text-align: left; cursor: pointer;
    background: var(--panel); color: var(--text); border: 3px solid var(--border); box-shadow: var(--shadow-1);
    padding: var(--space-2) var(--space-3); font-size: var(--fs-1); margin-bottom: var(--space-3); }}
}}
@media (max-width: 640px) {{
  .st-key-chef-main .chef {{ width: 80px; height: 80px; }}
  .kitchen-view {{ height: 16vh; }}
  .block-container {{ padding: 1.25rem 1rem 3rem; }} .chef {{ width: 80px; height: 80px; }}
  [data-testid="stTabs"] {{ padding: 0.5rem 0.9rem 1.25rem; }}
  [data-testid="stTab"] p::before {{ width: 28px; height: 28px; margin-right: 0.3rem; }}
  [data-testid="stTab"] p {{ font-size: 1.2rem; }}
  .stApp h1 {{ font-size: 2.4rem !important; }}
  .stats {{ gap: var(--space-2) var(--space-4); }} .stat {{ font-size: var(--fs-2); }} .stat .ico {{ width: 24px; height: 24px; }}
}}
/* Badges: an icon and the back end's words; the check a recipe passed, or a warning (never the icon alone) */
.badge {{ display: flex; align-items: center; gap: var(--space-2); background: var(--bubble); color: var(--text);
  border: 2px solid var(--border); padding: var(--space-1) var(--space-3); margin: var(--space-1) 0 var(--space-3);
  font-size: var(--fs-1); line-height: 1.35; }}
.badge .ico {{ width: 24px; height: 24px; flex: none; }}
.badge-warn {{ border-style: dashed; }}
/* The landing's three promises, as quiet chips (no shadow: they are not buttons) */
.trust {{ display: flex; flex-wrap: wrap; gap: var(--space-2) var(--space-3); margin-top: var(--space-3); }}
.trust .chip {{ display: inline-flex; align-items: center; gap: var(--space-2); border: 2px solid var(--border);
  background: var(--bubble); padding: var(--space-1) var(--space-3); font-size: var(--fs-1); }}
.trust .chip .ico {{ width: 20px; height: 20px; }}
/* What the results were checked for, and the Check tab's single verdict */
.st-key-safety-summary {{ margin: var(--space-2) 0 var(--space-3); }}
.st-key-safety-summary .badge {{ margin: 0; font-size: var(--fs-1); }}
.st-key-verdict {{ background: var(--panel); border: 3px solid var(--border); box-shadow: var(--shadow-1);
  padding: var(--space-3) var(--space-4); margin-top: var(--space-3); }}
/* Footer: the disclaimer and the people behind the project, on a wooden board */
.site-footer {{
  margin-top: 2.5rem; background: var(--panel); color: var(--text); border: 4px solid var(--border);
  box-shadow: var(--shadow-2); padding: var(--space-4) var(--space-5); font-size: var(--fs-1); line-height: 1.5;
}}
.site-footer .footer-title {{ font-family: var(--pixel-font); font-weight: 400; font-size: var(--fs-3); color: var(--heading); margin: 0 0 var(--space-1); padding: 0; }}
.site-footer ul {{ margin: 0.25rem 0 0.75rem 1.1rem; padding: 0; }}
.site-footer a {{ color: var(--heading); font-weight: 600; }}
.site-footer .credits {{ display: flex; flex-wrap: wrap; gap: 0.5rem 1.25rem; margin: 0.25rem 0 0.75rem; }}
.site-footer small {{ font-size: var(--fs-1); }}
.chef {{ cursor: pointer; transition: transform 0.1s steps(2); }}
.chef:active {{ background-image: url('{art("chef_" + theme.get("chef", DEFAULT_CHEF) + "wink")}') !important; animation: hop 0.35s steps(3); }}
@keyframes hop {{ 50% {{ transform: translateY(-10px); }} }}
@keyframes wiggle {{ 25% {{ transform: rotate(-12deg); }} 75% {{ transform: rotate(12deg); }} }}
[data-testid="stTab"]:active p::before, .stat:hover .ico, .bubble:hover .ico {{ animation: wiggle 0.3s steps(2); }}
.st-key-settings [data-testid="stPopover"] button p::before {{ transition: transform 0.3s steps(3); }}
.st-key-settings [data-testid="stPopover"] button:hover p::before {{ transform: rotate(90deg); }}
/* The interactive kitchen: a layer behind the page (app/kitchen_scene.html). Taps on empty parts of the
   page fall through to it; buttons, fields, tabs, cards and the chef still get their own taps. */
.stApp {{ isolation: isolate; }}
[data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) {{
  position: fixed !important; inset: 0; z-index: -1; width: 100vw !important; height: 100vh !important; margin: 0;
}}
[data-testid="stElementContainer"]:has(iframe[title="st.iframe"]) iframe {{
  width: 100vw !important; height: 100vh !important; border: 0;
}}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > div:has([data-testid="stMain"]),
[data-testid="stMain"], .block-container, .block-container * {{ pointer-events: none; }}
[data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] {{ pointer-events: auto; }}
.block-container :is(button, input, textarea, a, label, [role="tab"], [role="slider"], [data-baseweb="select"],
  [data-testid="stTabs"], [class*="st-key-recipe-card"], [data-testid="stPopover"], .chef, .bubble,
  .stat, h1, .tagline, .site-footer, iframe) {{ pointer-events: auto; }}
@media (prefers-reduced-motion: reduce) {{
  .stButton button:active, .chef:active {{ transform: none; animation: none; }}
  [data-testid="stTab"]:active p::before, .stat:hover .ico, .bubble:hover .ico {{ animation: none; }}
  [data-testid="stPopover"] button:hover p::before {{ transform: none; }}
  html[data-ef-news="1"] .st-key-whats-new button p::before {{ animation: none; }}
}}
</style>
"""


@cache
def scene_page(scene: str, hour: str = "afternoon") -> str:
    """The interactive kitchen for one theme: app/kitchen_scene.html with that theme's pieces filled in. hour:
    morning, afternoon, evening or night, or "auto" for the visitor's clock (read in their browser)."""
    layers = ART / f"scene_{scene}.json"
    template = Path(__file__).with_name("kitchen_scene.html")
    if not (layers.exists() and template.exists()):
        return ""
    return (template.read_text(encoding="utf-8").replace("__SCENE__", layers.read_text(encoding="utf-8"))
            .replace("__VERSION__", __version__).replace("__HOUR__", hour))


def kitchen_scene(scene: str, hour: str) -> None:
    """Put the interactive kitchen behind the page (the CSS makes it fill the window). Without the
    scene files the page keeps the still picture."""
    page = scene_page(scene, hour)
    if page:
        components.html(page, height=10)


def chef_says(place, mood: str, message: str, icon: str | None = None) -> None:
    """Draw the chef with a speech bubble. mood: 'happy', 'alert' or 'thinking'; icon: one of the
    result icons ('safe', 'alert', 'empty') shown at the start of the bubble.

    The chef only reads out what the back end decided; it never decides anything itself.
    """
    figure = f'<div class="chef" role="img" aria-label="The chef, {mood}" style="background-image: url({art("chef_" + CHEF + mood)})"></div>'
    badge = f'<span class="ico" style="background-image: url({art("icon_" + icon)})"></span>' if icon else ""
    for spot in place if isinstance(place, (list, tuple)) else [place]:   # the sidebar, and the page on phones
        spot.markdown(f'<div class="chef-row">{figure}<div class="bubble">{badge}{html.escape(message)}</div></div>',
                      unsafe_allow_html=True)


def cooking(message: str = "Cooking..."):
    """The "cooking in progress" screen: an egg frying in a pan over a fire (design/pixel-art/make_loading.py),
    shown while the app works. Returns the spot it is drawn in; call .empty() on it when done."""
    spot = st.empty()
    spot.markdown(f"""<style>@keyframes fry {{ to {{ background-position: -640px 0; }} }}
.cooking {{ display: flex; flex-direction: column; align-items: center; gap: 0.4rem; padding: 1rem; }}
.cooking .pan {{ width: 160px; height: 128px; image-rendering: pixelated; animation: fry 0.8s steps(4) infinite;
  background: url('{art("loading_eggs")}') 0 0 / 640px 128px no-repeat; }}
@media (prefers-reduced-motion: reduce) {{ .cooking .pan {{ animation: none; background-position: -480px 0; }} }}
</style><div class="cooking" role="status"><div class="pan"></div><p>{html.escape(message)}</p></div>""",
                  unsafe_allow_html=True)
    return spot


LANGUAGES = {"es": "Spanish", "it": "Italian", "el": "Greek", "fr": "French", "ja": "Japanese", "hi": "Hindi",
             "ar": "Arabic", "zh": "Mandarin", "ko": "Korean", "th": "Thai", "fa": "Persian", "tr": "Turkish"}


@cache
def pronunciations() -> pd.DataFrame:
    """How to say the most common foreign dish names (data/reference/dish_pronunciation.csv, from Wikidata and
    Lingua Libre, docs/plans/DISH_PRONUNCIATION.md), longest name first so "chile chipotle" wins over "chipotle"."""
    path = ROOT / "data" / "reference" / "dish_pronunciation.csv"
    if not path.exists():
        return pd.DataFrame(columns=["dish"])
    table = pd.read_csv(path).fillna("")
    return table.iloc[table["dish"].str.len().sort_values(ascending=False).index]


def say_it(dish: str) -> dict | None:
    """The pronunciation row for the dish name the recipe's name contains (a whole word), or None."""
    words = f" {dish.lower()} "
    for row in pronunciations().itertuples():
        if f" {row.dish} " in words:
            return row._asdict()
    return None


def say_it_line(entry: dict) -> str:
    """'Say it: PEH-stoh (pesto alla genovese, Italian name)': the respelling, and the dish's own name when the
    recipe's name differs from it."""
    native = str(entry["native_name"])
    language = LANGUAGES.get(str(entry["lang"]), str(entry["lang"]))
    own = f" ({plain(native)}, {plain(language)})" if native and native.lower() != str(entry["dish"]).lower() else ""
    return f"Say it: {plain(entry['respelling'])}{own}"


def from_commons(url: object) -> bool:
    """A link that really is Wikimedia Commons over https (the dish photos and their file pages), nothing else."""
    return isinstance(url, str) and re.match(r"https://(?:upload|thumb|commons)\.wikimedia\.org/", url) is not None


def plain(text: object) -> str:
    """Text from outside (a photo's author, a dish's name, what the user typed) shown as words only, in Markdown
    (st.caption, st.markdown without HTML): every Markdown and HTML sign gets a backslash, so it shows as itself and
    nothing becomes a link, a tag or a format. (HTML codes such as &amp; would show as codes there.) A list shows
    as its items."""
    if isinstance(text, list | tuple | set):
        text = ", ".join(map(str, text))
    return re.sub(r"([\\`*_{}\[\]()#+!|<>~&-])", r"\\\1", str(text))


def video_search_link(dish: str, country: object) -> str:
    """A YouTube search for the dish (no API, no key, nothing plays by itself): the dish's own name and, when
    known, its country, so "bulgogi" finds Korean bulgogi."""
    words = f"{dish} {country if isinstance(country, str) and country != 'Unknown' else ''} recipe"
    return "https://www.youtube.com/results?search_query=" + "+".join(re.findall(r"[\w'-]+", words))


@st.dialog("About this dish", width="large")
def dish_page(row: pd.Series, dish: str) -> None:
    """The dish on its own page: where it is from, how its time divides, and each step with its time, the pan or
    pot it uses, the method and what goes in (dish_steps.py, from the recipe's own words)."""
    st.subheader(dish.title())
    named = clean_title(row["recipe_name"])
    if named["name_gloss"]:
        st.caption(f"Also called {named['name_gloss']}")
    if str(named["dish_name"]).lower() != str(row["recipe_name"]).lower():   # the checks read the posted title
        st.caption(f"Posted as \"{plain(row['recipe_name'])}\"")
    spoken = say_it(dish)
    if spoken:
        st.caption(say_it_line(spoken) + (f" · {plain(spoken['note'])}" if spoken["note"] else ""))
        if spoken["audio_file"]:   # a recording of a native speaker: plays only when tapped, with its credit
            name = str(spoken["audio_file"]).replace(" ", "_")
            st.audio(f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(name)}")
            st.caption(f"Recording: {plain(spoken['audio_author'] or 'a Wikimedia Commons contributor')}, "
                       f"{plain(spoken['audio_license'])}, via [Wikimedia Commons]"
                       f"(https://commons.wikimedia.org/wiki/File:{quote(name)})")
    where = row.get("origin_country")
    if isinstance(where, str) and where != "Unknown":
        st.caption(f"From {where}")
    steps = step_breakdown(row.get("instructions"), row.get("ingredient_list"))
    minutes = row.get("minutes")
    total = float(minutes) if minutes is not None and pd.notna(minutes) else None
    split = split_minutes(steps, total)
    times = [("Total", split["total"]), ("On the heat", split["on_heat"]), ("Preparation and waiting", split["rest"])]
    cols = st.columns(3)
    for col, (label, value) in zip(cols, times, strict=True):
        col.metric(label, f"{value:.0f} min" if value is not None else "Not written")
    ingredients = row.get("ingredient_list")
    if ingredients is not None and len(ingredients):
        st.write("**Ingredients:** " + ", ".join(map(str, ingredients)))
    st.markdown(f"[Watch it made on YouTube]({video_search_link(dish, where)})")
    methods = methods_of(row.get("instructions"))
    if methods:
        st.write("**Cooking methods:** " + ", ".join(methods))
    if not steps:
        link = row.get("url")
        st.info("This recipe has no steps in our data"
                + (f": [its own page]({link}) has them." if isinstance(link, str) and link.startswith("http") else "."))
    for i, step in enumerate(steps, 1):
        details = [str(step["vessel"]).capitalize()] if step["vessel"] else []
        details += [f"{float(str(step['minutes'])):.0f} min"] if step["minutes"] else []
        details += ["on the heat"] if step["on_heat"] else []
        goes_in = ", ".join(str(item) for item in list(step["ingredients"]))  # type: ignore[call-overload]
        st.markdown(f"**{i}.** {html.escape(str(step['text']))}"
                    + (f"  \n<small>{' · '.join(details)}{' · in: ' + html.escape(goes_in) if goes_in else ''}</small>"
                       if details or goes_in else ""), unsafe_allow_html=True)
    st.caption("Times are the ones written in the steps; a step without one is not counted.")


def stats(place, calories: float, protein: float, minutes: float | None, estimate: float | None = None) -> None:
    """A recipe's calories, protein and time, each with its pixel icon. Without its own time, the estimate from
    similar recipes (cooking_time.py) shows as "about ... min, estimated"; with neither, no time chip."""
    chips = [("icon_flame", f"{calories:.0f}", "kcal"), ("icon_protein", f"{protein:.0f} g", "protein")]
    if minutes is not None and pd.notna(minutes):
        chips.append(("icon_timer", f"{minutes:.0f}", "minutes"))
    elif estimate is not None and pd.notna(estimate):          # over 4 hours an estimate is no better than this
        chips.append(("icon_timer", "several", "hours, estimated") if estimate > 240
                     else ("icon_timer", f"about {estimate:.0f}", "min, estimated"))
    place.markdown('<div class="stats">' + "".join(
        f'<div class="stat"><span class="ico" style="background-image: url({art(icon)})"></span>'
        f'{value} <small>{label}</small></div>' for icon, value, label in chips) + "</div>", unsafe_allow_html=True)


def badge(place, icon: str, text: str, kind: str = "safe") -> None:
    """A small pixel badge: an icon and the back end's words (never the icon alone: the words carry the meaning)."""
    place.markdown(f'<div class="badge badge-{kind}"><span class="ico" style="background-image: url({art(icon)})">'
                   f'</span><span>{html.escape(text)}</span></div>', unsafe_allow_html=True)


# ---------- The profile: the sidebar's fields, the first-visit setup and the summary above the results ----------
PROFILE_DEFAULTS = {"avoid": [], "diets": [], "vegetarian": False, "vegan": False, "calories": 600}
EATING = ["I eat meat", "Vegetarian", "Vegan"]


def save_setup() -> None:
    """The setup's answers become the sidebar's profile (a callback: it runs before the page draws its fields)."""
    eating = st.session_state["setup-eating"]
    st.session_state.update(avoid=st.session_state["setup-avoid"], diets=st.session_state["setup-diets"],
                            vegetarian=eating == "Vegetarian", vegan=eating == "Vegan",
                            calories=st.session_state["setup-calories"], onboarded=True)


def skip_setup() -> None:
    st.session_state["onboarded"] = True


@st.dialog("Set up your profile", width="large", on_dismiss=skip_setup)
def setup_profile() -> None:
    """Three questions on the first visit (and from "Edit profile"), so every result is checked from the start.
    They fill the same profile as the sidebar; nothing is saved after the page closes."""
    st.markdown("Three quick questions, and every recipe is checked for you. Change them any time under "
                "**Your profile**.")
    state = st.session_state
    st.markdown("**1. What can't you eat?**")
    st.multiselect("I can't eat", sorted(FLAG_RULES), default=state.get("avoid", []), format_func=nice,
                   key="setup-avoid", label_visibility="collapsed", placeholder="Peanuts, shellfish, pork... (leave empty if nothing)")
    st.markdown("**2. Do you follow a diet?**")
    st.multiselect("I follow", sorted(DIET_PROFILES), default=state.get("diets", []), format_func=nice_diet,
                   key="setup-diets", label_visibility="collapsed", placeholder="Halal-friendly, kosher-friendly... (optional)")
    st.radio("Meat", EATING, horizontal=True, key="setup-eating", label_visibility="collapsed",
             index=2 if state.get("vegan") else 1 if state.get("vegetarian") else 0)
    st.markdown("**3. About how many calories per meal?**")
    st.slider("Calories per meal", 200, 1500, int(state.get("calories", 600)), 50, key="setup-calories",
              label_visibility="collapsed")
    save, skip = st.columns(2)
    if save.button("Save and find recipes", type="primary", on_click=save_setup, width="stretch"):
        st.rerun()
    if skip.button("Skip for now", on_click=skip_setup, width="stretch", type="secondary"):
        st.rerun()
    st.caption("Not medical advice: the checks read ingredient names. Nothing you enter is saved.")


# ---------- Finding: the filters, the order and how many ideas at a time ----------
QUICK_LABELS = {"time": "Under 30 min", "protein": "High protein (25 g+)"}
QUICK_FILTERS = list(QUICK_LABELS.values())
SORTS = {"Closest to my calories": "calories", "Quickest": "quickest", "Most protein": "protein"}
PAGE, MAX_IDEAS = 5, 30   # ideas per "Find" and per "Show more"; at most this many in all


def drop_filter(kind: str) -> None:
    st.session_state["filters"] = [f for f in st.session_state.get("filters") or [] if f != QUICK_LABELS[kind]]


def choice_label(block: dict) -> str:
    """One of the profile's choices in plain words (diets as "...-friendly ingredients", never the diet itself)."""
    kind, choice = block["kind"], str(block["choice"])
    if kind == "avoid":
        return "Vegan" if choice == "vegan" else f"No {nice(choice).lower()}"
    if kind == "diet":
        return f"{nice(choice)}-friendly ingredients" if choice.endswith("_friendly") else nice(choice)
    return kind.capitalize()


# ---------- The Check tab's words: the back end's report in plain language (no rule names or codes) ----------
def where_found(line_: str) -> str:
    """'3 tbsp satay sauce' -> '**3 tbsp satay sauce**'; '(dish name) Thai peanut bowl' -> 'The dish's name, ...'."""
    if line_.startswith("(dish name) "):
        return f"The dish's name, **{plain(line_.removeprefix('(dish name) '))}**,"
    return f"**{plain(line_)}**"


def rule_words(rule: str) -> str:
    """A rule the line breaks: 'contains_peanut' -> 'has peanut', 'vegan' -> 'is not vegan',
    'halal_friendly' -> 'is not halal-friendly'."""
    if rule.startswith("contains_"):
        return f"has {nice(rule).lower()}"
    if rule in ("vegan", "vegetarian"):
        return f"is not {rule}"
    return f"is not {nice_diet(rule).lower()}"


def because(line_: str, matched: object) -> str:
    """The word that broke the rule, only when it is not plain to see in the line (a hidden or translated
    ingredient): ' (we found "anchovy")'; '' when the line already shows it."""
    words = [str(w) for w in (matched if isinstance(matched, list | tuple | set) else [matched])]
    hidden = [w for w in words if w.lower() not in line_.lower()]
    return f" (we found \"{plain(hidden)}\")" if hidden else ""


def checked_words(rule: str) -> str:
    """What was checked: 'contains_peanut' -> 'peanut', 'halal_friendly' -> 'halal-friendly ingredients'."""
    if rule.startswith("contains_"):
        return nice(rule).lower()
    return f"{nice_diet(rule).lower()} ingredients" if rule.endswith("_friendly") else nice_diet(rule).lower()


# ---------- Saved recipes: this visit only (nothing is stored), with a file to keep them ----------
def toggle_saved(recipe_id: str, entry: dict) -> None:
    saved = st.session_state.setdefault("saved", {})
    if recipe_id in saved:
        del saved[recipe_id]
    else:
        saved[recipe_id] = entry


def saved_text(saved: dict) -> str:
    """The saved recipes as a plain text file: name, where from, the numbers, the ingredients and the link."""
    parts = ["My EverFlavor recipes (checked for the profile I had when I saved them; not medical advice)\n"]
    for entry in saved.values():
        parts.append(f"\n{entry['name']}\n" + "\n".join(f"  {line_}" for line_ in entry["lines"]))
    return "\n".join(parts) + "\n"


# ---------- Page setup ----------
CHEF_ICON = ART / "chef_happy.png"
st.set_page_config(page_title="EverFlavor Kitchen", page_icon=str(CHEF_ICON) if CHEF_ICON.exists() else "🍲",
                   layout="wide")
theme_name = st.session_state.get("theme", "Classic")
if st.session_state.get("follow_cuisine", True):
    searched_country = read_search(st.session_state.get("search"))[0]
    if searched_country:
        theme_name = COUNTRY_KITCHENS.get(searched_country, "Classic")
    elif st.session_state.get("cuisine") in CUISINE_KITCHENS:
        theme_name = CUISINE_KITCHENS[st.session_state["cuisine"]]
CHEF = THEMES[theme_name].get("chef", DEFAULT_CHEF)   # which chef stands in this kitchen (chef_says)
if st.session_state.get("cook") == "Woman" and CHEF.startswith("ref_"):   # the regions with a woman cook
    CHEF += "woman_"
# The kitchen's time of day: the visitor's clock only once they allow it (Settings), otherwise the hour they pick
HOURS = ["Morning", "Afternoon", "Evening", "Night"]
hour = "auto" if st.session_state.get("use_clock") else st.session_state.get("hour", "Afternoon").lower()
page_colors = dict(THEMES[theme_name], chef=CHEF)
if theme_name == "Classic" and hour == "night":       # (with the clock, the page keeps its day colors)
    page_colors.update(NIGHT_COLORS)
st.markdown(style(page_colors), unsafe_allow_html=True)
kitchen_scene(THEMES[theme_name]["scene"], hour)
heading, corner = st.columns([3, 2], vertical_alignment="center")
heading.title("EverFlavor Kitchen")
TRUST = [("icon_check", "Free, no sign-up"), ("icon_safe", "Nothing you enter is saved"),
         ("icon_alert", "Not medical advice")]


def landing() -> None:
    """What people see first (docs/plans/LANDING_PAGE.md, option A): the promise, one button into the app, how it
    works and how we check, drawn before the recipes load. The chef's "catch" is a fixed, reviewed fact from the
    hidden-allergen review, not a safety verdict; the app's rules make every decision."""
    st.markdown('<p class="tagline">Allergies, religious and ethical diets, calorie goals: tell the chef once, and '
                'every recipe is checked for you.</p>', unsafe_allow_html=True)
    with st.container(key="landing-start"):
        st.button("Find a safe recipe", type="primary", key="start", on_click=st.session_state.update,
                  kwargs={"started": True})
        st.markdown('<div class="trust">' + "".join(
            f'<span class="chip"><span class="ico" style="background-image: url({art(icon)})"></span>{text}</span>'
            for icon, text in TRUST) + "</div>", unsafe_allow_html=True)
    chef_says(st.container(), "happy", f"{greeting(theme_name)} Did you know satay sauce is usually made with "
                                        "peanuts? Paste any recipe and I'll check it.")
    # On the app's cream panel, like the tabs, so the text never sits on the busy kitchen
    st.markdown('<style>.st-key-landing-panel, .st-key-landing-start { background: var(--panel); border: 3px solid var(--border);'
                ' box-shadow: var(--shadow-1); padding: var(--space-4) var(--space-5); } .st-key-landing-panel * { pointer-events: auto; }</style>',
                unsafe_allow_html=True)
    with st.container(key="landing-panel"):
        st.subheader("How it works")
        for col, (title, text) in zip(st.columns(3), [
            ("1. Tell the chef", ("Pick what you can't eat, the diet you follow and your calories per meal. It takes a "
                                 "few taps.")),
            ("2. We check every ingredient", ("Each recipe is checked for allergens, hidden ones too (Worcestershire "
                                             "sauce has fish), and for your diet's rules.")),
            ("3. Cook with confidence", ("You see only recipes that pass, with why each one fits you. Or paste your own "
                                        "recipe and we check it line by line.")),
        ], strict=True):
            col.markdown(f"**{title}**  \n{text}")
        with st.expander("How we check"):
            st.markdown(
                "- **What we check:** about 290,000 recipes from open and research datasets, each checked ingredient "
                "by ingredient against allergen lists from the US, the EU and UK, Canada, Australia and New Zealand, "
                "Japan and South Korea.\n"
                "- **Safety is decided in the code, not by the AI.** The rules decide what is safe; the AI chef only "
                "explains.\n"
                "- **Not medical advice.** The checks read ingredient names and can miss things: a brand's recipe, "
                "cross-contact in a factory, an unusual spelling. With a serious allergy or a health condition, read "
                "the label and ask your doctor or dietitian.\n"
                "- **Diet labels:** \"halal-friendly ingredients\" means nothing in the ingredients is forbidden. It is "
                "not a certification.\n"
                "- **Your data:** nothing you enter is saved. No accounts, no cookies, no tracking.")
        st.caption("Made by Team EverGlow, a student capstone project (ITAI 2277): "
                   + ", ".join(f"[@{name}](https://github.com/{name})" for name in ("Chloe-Tu2", "Evaabou20", "med27-coder")))


# The landing comes first, before the data loads; ?start=1 (and the button) go straight to the app
if not st.session_state.get("started") and st.query_params.get("start") != "1":
    landing()
    st.stop()
heading.markdown('<p class="tagline">Recipes that fit what you can eat, checked ingredient by ingredient.</p>',
                 unsafe_allow_html=True)
news_spot, saved_spot, settings_spot = corner.columns(3)
saved = st.session_state.setdefault("saved", {})
with saved_spot.container(key="saved-list"), st.popover(f"Saved ({len(saved)})"):
    if not saved:
        st.markdown("Nothing saved yet. Tap **Save** on a recipe to keep it here while this page is open.")
    for recipe_id, entry in list(saved.items()):
        name_col, remove_col = st.columns([4, 1], vertical_alignment="center")
        name_col.markdown(f"**{html.escape(entry['name'])}**  \n<small>{html.escape(entry['lines'][0])}</small>",
                          unsafe_allow_html=True)
        remove_col.button("Remove", key=f"unsave-{recipe_id}", on_click=toggle_saved, args=(recipe_id, entry))
    if saved:
        st.download_button("Download my recipes", saved_text(saved), file_name="everflavor_recipes.txt",
                           mime="text/plain", on_click="ignore", width="stretch")
        st.caption("Saved for this visit only: nothing is stored. Download them to keep them.")
with news_spot.container(key="whats-new"), st.popover("What's new"):
    st.markdown('<div class="updates">' + "".join(
        f'<h5>{update["version"]} · {update["date"]}</h5><ul>'
        + "".join(f"<li>{html.escape(note)}</li>" for note in update["notes"]) + "</ul>"
        for update in UPDATES) + "</div>", unsafe_allow_html=True)
    st.caption(f"EverFlavor {__version__} (beta). Every change: "
               "[the changelog](https://github.com/Chloe-Tu2/The-EverFlavor-AI/blob/main/CHANGELOG.md).")
with settings_spot.container(key="settings"), st.popover("Settings"):
    st.selectbox("Kitchen theme", list(THEMES), key="theme",
                 help="Classic is the team's original kitchen. The time of day below sets its light.")
    st.radio("Your chef", ["Man", "Woman"], key="cook", horizontal=True,
             help="The cook who reads out your results, dressed for the kitchen's region.")
    st.toggle("Use my clock for the kitchen's light", value=False, key="use_clock",
              help="With your permission, the kitchen follows your device's time: morning, afternoon, evening or "
                   "night light. Your time stays in your browser; nothing is sent or saved.")
    st.radio("Time of day", HOURS, index=1, key="hour", horizontal=True, disabled=st.session_state.get("use_clock", False),
             help="Pick the kitchen's light yourself (used while the clock is off).")
    st.toggle("Match the kitchen to the cuisine", value=True, key="follow_cuisine",
              help="Searching a cuisine family opens its kitchen: Asian (Chinese), African (Moroccan), "
                   "European (Mediterranean), Latin American (Mexican), Middle Eastern.")
st.markdown('<div class="kitchen-view"></div>', unsafe_allow_html=True)   # leave the kitchen in view
# The chef's line, filled in below once we know what happened: in the page on phones (the sidebar is hidden there),
# and at the bottom of the sidebar on wider screens (added after the profile, below)
chef = [st.container(key="chef-main").empty()]

if not (DATA / "recipes_test.parquet").exists():
    chef_says(chef, "thinking", "My pantry is empty! Run notebook 01 first to build the recipe data.")
    st.stop()

recipes = load_recipes()


@st.cache_data(ttl=300)   # ask Ollama at most every 5 minutes (when it is off, asking takes about 4 s)
def local_ai() -> dict:
    return choose_model()   # {"kind": "ollama" or "rules", "model", "reason"}


ai = local_ai()

# ---------- Sidebar: the user's profile, then settings ----------
# The first visit opens the three-question setup; the sidebar holds the same profile afterwards
for field, default in PROFILE_DEFAULTS.items():
    st.session_state.setdefault(field, default)
if not st.session_state.get("onboarded"):
    setup_profile()
with st.sidebar:
    st.header("Your profile")
    avoid = st.multiselect("I can't eat", options=sorted(FLAG_RULES), format_func=nice, key="avoid")
    diets = st.multiselect("I follow", options=sorted(DIET_PROFILES), format_func=nice_diet, key="diets")
    vegetarian = st.checkbox("Vegetarian", key="vegetarian")
    vegan = st.checkbox("Vegan", key="vegan")
    calories = st.slider("Calories per meal", min_value=200, max_value=1500, step=50, key="calories")
    st.divider()
    if ai["kind"] == "ollama":
        use_ai = st.checkbox(f"Explain problems with local AI ({ai['model']})", value=True)
    else:
        use_ai = False
        st.caption("Local AI: off. The rules still check everything.", help=ai["reason"])
    chef.append(st.container(key="chef-side").empty())

profile = UserProfile(avoid=tuple(avoid), diets=tuple(diets), vegetarian=vegetarian,
                      vegan=vegan, calories_per_meal=calories)
# The chef's welcome: hello in the kitchen's own language, then one tip, dish fact or chef's quote, the same one
# for the whole visit (a seed per visit, so reruns do not change it)
visit = st.session_state.setdefault("chef_seed", random.randrange(1_000_000))
said = line(theme_name, visit)
said += "" if said.endswith((".", "!", "?")) else "."          # a quote ends with its source: close the sentence
chef_says(chef, "happy", f"{greeting(theme_name)} {said} Find a recipe below, or check one of yours.")

# ---------- Two tabs ----------
# On a phone the sidebar is hidden: a button above the tabs says what the profile holds and opens it (the click is
# passed to Streamlit's own sidebar button by app/kitchen_scene.html)
set_profile = [*map(nice, avoid), *map(nice_diet, diets), *(["vegetarian"] if vegetarian else []), *(["vegan"] if vegan else [])]
st.markdown(f'<button class="open-profile" type="button">Your profile: '
            f'{html.escape(", ".join(set_profile)) if set_profile else "nothing set yet"} · edit</button>',
            unsafe_allow_html=True)
find_tab, check_tab, map_tab = st.tabs(["Find recipes", "Check my recipe", "Map: Houston"])   # icons from the CSS

with find_tab:
    pool: pd.DataFrame = recipes
    cuisine = "All"
    if "origin_country" in recipes:
        # One search box (a dish, a country or a region, with suggestions as you type) and, for those who would
        # rather not type, Browse by region: every region with its countries, one tap to pick one
        counts = cast(pd.Series, recipes["origin_country"].value_counts())
        counts = cast(pd.Series, counts[(counts >= MIN_COUNTRY_RECIPES) & (counts.index != "Unknown")])
        regions = recipes.dropna(subset=["origin_region"]).groupby("origin_region")["origin_country"].first()
        suggestions = [*counts.index, *(f"{r} ({c})" for r, c in regions.items())]

        def pick_place(key: str) -> None:
            st.session_state["search"] = st.session_state[key]
            st.session_state[key] = None

        search_spot, browse_spot = st.columns([4, 1], vertical_alignment="bottom")
        query = search_spot.selectbox(
            "What would you like to eat?", suggestions, index=None, key="search", accept_new_options=True,
            placeholder="All regions. Or type a dish or where it's from: ramen, Korean, Louisiana, tacos...",
            help="Type a dish, a country or a region. The kitchen follows the country when Settings says so.")
        with browse_spot.popover("Browse by region", width="stretch"):
            # All regions is the default: nothing picked searches every country
            st.button("Show all regions", key="browse-all", on_click=st.session_state.update, kwargs={"search": None},
                      disabled=not st.session_state.get("search"))
            family_of = recipes.groupby("origin_country")["cuisine_family"].agg(lambda f: f.mode().iat[0])
            for family in ["Asian", "European", "Latin American", "Middle Eastern", "African", "Other"]:
                in_family = [c for c in counts.index if family_of.get(c) == family]
                if in_family:
                    st.pills("North America, Oceania and more" if family == "Other" else family, in_family,
                             key=f"browse-{family}", on_change=pick_place, args=(f"browse-{family}",))
        country, region, dish = read_search(query)
        if country:
            pool = cast(pd.DataFrame, pool[pool["origin_country"] == country])
        if region:
            pool = cast(pd.DataFrame, pool[pool["origin_region"] == region])
        for word in dish:
            pool = cast(pd.DataFrame, pool[pool["recipe_name"].str.contains(word, case=False, regex=False)])
        if query:                                   # what the search is doing, above the results
            asked = [f"dishes from {region + ', ' if region else ''}{country}"] if country else []
            asked += ['"' + " ".join(dish) + '" in the name'] if dish else []
            st.caption("Looking for " + ", ".join(asked) + f" · {len(pool):,} recipes")
    else:                                           # the demo data has no countries: the cuisine families only
        cuisine = st.selectbox("Cuisine", ["All"] + sorted(recipes["cuisine_family"].dropna().unique()), key="cuisine")
    # Filters, one tap each, and the order; the back end applies them, and every result still passes its checks
    filter_spot, sort_spot = st.columns([3, 2], vertical_alignment="bottom")
    quick = filter_spot.pills("Narrow it down", list(QUICK_FILTERS), selection_mode="multi", key="filters") or []
    sort_label = sort_spot.selectbox("Sort by", list(SORTS), key="sort")
    max_minutes = 30.0 if "Under 30 min" in quick else None
    min_protein = 25.0 if "High protein (25 g+)" in quick else None

    # The results stay on the page between clicks (so "About this dish" can open), but only for the exact choices
    # they were found with: change the profile, the search or a filter and they are cleared, with a note saying so
    asked = (tuple(avoid), tuple(diets), vegetarian, vegan, calories, cuisine, str(st.session_state.get("search")),
             tuple(quick), sort_label)

    def find(count: int) -> None:
        loading = cooking("Cooking up ideas...")
        st.session_state["found"] = (asked, count, baseline_recommend(
            pool, cuisine_family=None if cuisine == "All" else cuisine, calorie_target=calories,
            vegetarian_only=vegetarian, vegan_only=vegan, avoid=avoid, diets=diets, top_n=count,
            max_minutes=max_minutes, min_protein_g=min_protein, sort_by=SORTS[sort_label]))
        loading.empty()

    if st.button("Find recipes", type="primary"):
        find(PAGE)
    found = st.session_state.get("found")
    if found and found[0] != asked:
        st.info("Your choices changed, so the earlier ideas were cleared (they were checked for the old ones). "
                "Press **Find recipes** for new ones.")
    fits = why_it_fits(avoid, diets, vegetarian, vegan)   # the back end's checks, restated in plain words
    if found and found[0] == asked:
        results = found[2]
        # What every result below was checked for, with a way to change it
        with st.container(key="safety-summary"):
            said_col, edit_col = st.columns([5, 1], vertical_alignment="center")
            badge(said_col, "icon_safe" if fits else "icon_alert",
                  f"{fits or 'No profile set: these ideas are not checked for allergies or diets'}. "
                  f"About {calories} kcal per meal" + (f"; {', '.join(quick).lower()}." if quick else "."),
                  "safe" if fits else "warn")
            edit_col.button("Edit", key="edit-profile", on_click=st.session_state.update, kwargs={"onboarded": False},
                            width="stretch")
        if results.empty:
            chef_says(chef, "thinking", "Hmm, nothing fits all your choices together. Here is what is holding it back.",
                      "empty")
            blocks = [b for b in what_blocks(pool, avoid, diets, vegetarian, vegan, max_minutes, min_protein)
                      if b["recipes"]]
            # One tap only for the filters and the search; an allergy or a diet is never offered as one tap to drop
            for b in [b for b in blocks if b["kind"] in ("time", "protein")]:
                st.button(f"Drop \"{QUICK_LABELS[str(b['kind'])]}\": about {b['recipes']:,} recipes",
                          key=f"loosen-{b['kind']}", on_click=drop_filter, args=(str(b["kind"]),))
            if st.session_state.get("search"):
                st.button("Clear the search", key="loosen-search", on_click=st.session_state.update,
                          kwargs={"search": None})
            strict = [b for b in blocks if b["kind"] not in ("time", "protein")][:3]
            if strict:
                st.markdown("Your profile's strictest choices, and the recipes each one holds back (change them only "
                            "if they do not apply to you):\n\n" + "\n".join(
                                f"- **{choice_label(b)}**: about {b['recipes']:,} recipes without it" for b in strict))
        else:
            chef_says(chef, "happy", f"Here {'is' if len(results) == 1 else 'are'} {len(results)} "
                                     f"{'idea' if len(results) == 1 else 'ideas'} close to {calories} calories. "
                                     "Every one passed the safety check for your profile.", "safe")
        for number, (_, row) in enumerate(results.iterrows()):
            with st.container(border=True, key=f"recipe-card-{number}"):
                photo, link, site = row.get("image_url"), row.get("url"), row.get("source")
                ok = row.get("photo_ok")             # False: a logo, an icon or not the dish; missing: no check
                if ok is not None and not pd.isna(ok) and not bool(ok):
                    photo = None
                named = clean_title(row["recipe_name"])
                dish = str(named["dish_name"]).title()
                picture, info = st.columns([1, 2])
                if isinstance(photo, str) and photo.startswith("https://"):
                    # The photo comes with the recipe from its website; the credit links there, so anyone can check
                    picture.image(photo, width="stretch", alt=f"Photo of {dish} from the recipe's page")
                    if isinstance(link, str) and link.startswith("http"):
                        picture.caption(f"Photo: [{html.escape(str(site or 'the recipe page'))}]({link})")
                elif from_commons(row.get("thumb_url")) and from_commons(row.get("file_page")):
                    # No photo of its own: a free photo of the dish in general (Wikimedia Commons), said so plainly
                    picture.image(row["thumb_url"], width="stretch",
                                  alt=f"A photo of {row['dish_label']} in general, not this recipe")
                    picture.caption(f"A photo of {plain(row['dish_label'])} in general, not this recipe. "
                                    f"[{plain(row['credit'])}]({row['file_page']})")
                else:
                    # No photo at all: the kitchen's own picture, which says plainly that it is not the dish
                    picture.markdown(f'<div class="no-photo" role="img" aria-label="No photo of this dish yet">'
                                     f'<span class="ico" style="background-image: url({art("no_photo_photo")})"></span>'
                                     'Cooking up a picture...<small>No photo of this dish yet</small></div>',
                                     unsafe_allow_html=True)
                # A short card: the dish's own name and where it is from, the numbers, and the check it passed as
                # its badge; the other names, how to say it, the ingredients, steps and video are on its own page
                info.subheader(dish)
                where = row.get("origin_country")
                if isinstance(where, str) and where != "Unknown":
                    region = row.get("origin_region")
                    info.caption(f"From {region + ', ' if isinstance(region, str) else ''}{where}")
                stats(info, row["calories_per_serving"], row["protein_g"], row.get("minutes"), row.get("minutes_estimate"))
                badge(info, "icon_safe" if fits else "icon_alert",
                      fits or "Not checked: add what you can't eat under Your profile", "safe" if fits else "warn")
                ingredients = row["ingredient_list"]
                if isinstance(ingredients, str):
                    try:
                        ingredients = ast.literal_eval(ingredients)
                    except (ValueError, SyntaxError):
                        ingredients = [ingredients]
                about_col, save_col = info.columns([3, 1])
                if about_col.button(f"About this dish: {len(ingredients)} ingredients, steps, video",
                                    key=f"about-{number}", width="stretch"):
                    dish_page(row, str(named["dish_name"]))
                recipe_id = str(row.get("recipe_id", row["recipe_name"]))
                entry = {"name": dish, "lines": [
                    f"{row['calories_per_serving']:.0f} kcal, {row['protein_g']:.0f} g protein"
                    + (f", from {where}" if isinstance(where, str) and where != "Unknown" else ""),
                    fits or "Not checked against a profile",
                    "Ingredients: " + ", ".join(map(str, ingredients)),
                    *([f"Recipe: {link}"] if isinstance(link, str) and link.startswith("http") else [])]}
                save_col.button("Saved" if recipe_id in saved else "Save", key=f"save-{number}", width="stretch",
                                on_click=toggle_saved, args=(recipe_id, entry),
                                help="Keep it in Saved (top right) while this page is open")
        more = not results.empty and len(results) == found[1] and found[1] < MAX_IDEAS
        if more and st.button(f"Show {PAGE} more", key="more"):
            find(found[1] + PAGE)
            st.rerun()

with check_tab:
    st.write("Paste a recipe, one ingredient per line, to check it against your profile.")
    name = st.text_input("Dish name", placeholder="Thai peanut bowl")
    lines = st.text_area("Ingredients", placeholder="2 cups jasmine rice\n3 tbsp satay sauce\n1 lb chicken breast",
                         height=140)

    if st.button("Check it", type="primary"):
        if not lines.strip():
            st.warning("Paste at least one ingredient line first.")
        else:
            # The safety gate decides; the local AI (if on) only explains a failure, and its words are
            # replaced by a plain sentence when they do not match the gate's answer.
            dish_name = name.strip() or "Your recipe"
            loading = cooking("Checking every ingredient...")
            report = check_and_explain(lines.splitlines(), dish_name, profile, model=ai["model"] if use_ai else None)
            loading.empty()
            with st.container(key="verdict"):
                if report["passed"]:
                    chef_says(chef, "happy", f"{dish_name} fits your profile. Happy cooking!", "safe")
                    badge(st, "icon_safe", f"{dish_name}: nothing in these ingredients breaks your profile.")
                else:
                    problems = report["problems"]
                    count = f"{len(problems)} {'problem' if len(problems) == 1 else 'problems'}"
                    chef_says(chef, "alert", f"Watch out! I found {count} in {dish_name}.", "alert")
                    badge(st, "icon_alert", f"{dish_name}: {count} for your profile.", "warn")
                    by_line: dict[str, list[dict]] = {}
                    for problem in problems:              # one entry per ingredient line, with every rule it breaks
                        by_line.setdefault(str(problem["line"]), []).append(problem)
                    st.markdown("\n".join(
                        f"- {where_found(text)} " + "; ".join(
                            rule_words(p["rule"]) + because(text, p["matched"]) for p in found_here) + "."
                        for text, found_here in by_line.items()))
                    if report["explained_by"] != "rules":   # the local AI's words, kept only when they match the rules
                        st.markdown(plain(report["text"]))
                checked = [checked_words(r) for r in report["checked"] if r != "contains_pet_meat"]
                st.caption(("Checked for: " + ", ".join(checked) + ". " if checked else "")
                           + "The app's rules made this decision"
                           + (f"; the local AI ({report['explained_by']}) only explained it." if report["explained_by"] != "rules"
                              else ".") + " Not medical advice: the check reads ingredient names.")

with map_tab:
    # Where to buy and where to eat, Houston only for now (docs/plans/MAP.md): OpenStreetMap places from notebook 03
    # on a free OpenFreeMap street map. The map never asks where the visitor is.
    st.write("Grocers, restaurants and butchers in Houston, Texas, for now. More cities may follow.")
    places_file = DATA / "places.parquet"
    if not places_file.exists():
        places_file = ROOT / "data" / "processed" / "places.parquet"
    if not places_file.exists():
        st.info("The map needs the places from notebook 03 (data/processed/places.parquet).")
    else:
        places = pd.read_parquet(places_file).dropna(subset=["lat", "lng"])
        places["cuisine_text"] = places["cuisine"].map(lambda c: ", ".join(c) if c is not None and len(c) else "")
        kinds = {"Grocers": "grocery", "Restaurants": "restaurant", "Butchers": "butcher"}
        picked = st.pills("Show", list(kinds), default=list(kinds), selection_mode="multi", key="map-kinds") or []
        shown = cast(pd.DataFrame, places[places["category"].isin([kinds[k] for k in picked])])
        searched = read_search(st.session_state.get("search"))[0]
        adjective = next((label for label, (country, _) in ORIGIN_LABELS.items()
                          if country == searched and " " not in label and label.endswith(("an", "ese", "ish", "i"))), None)
        if adjective and st.toggle(f"Only {adjective} places (from your search)", value=True, key="map-match"):
            words = f"{adjective}|{searched.lower()}" if searched else adjective
            text = shown["cuisine_text"].str.lower() + " " + shown["name_hint"].fillna("").str.lower() + " " \
                + shown["name"].fillna("").str.lower()
            shown = cast(pd.DataFrame, shown[text.str.contains(words, regex=True)])
        st.caption(f"{len(shown):,} places in Houston from OpenStreetMap. Unverified: check with the store. "
                   "© OpenStreetMap contributors, map © OpenFreeMap.")
        colors = {"grocery": [69, 117, 54], "restaurant": [217, 72, 59], "butcher": [139, 69, 19]}
        shown = shown.assign(color=shown["category"].map(colors), label=shown["name"].fillna("(no name)"),
                             kind=shown["category"].str.capitalize())
        st.pydeck_chart(pdk.Deck(
            map_style="https://tiles.openfreemap.org/styles/liberty",
            initial_view_state=pdk.ViewState(latitude=29.76, longitude=-95.37, zoom=10.5),
            layers=[pdk.Layer("ScatterplotLayer", shown[["lng", "lat", "color", "label", "kind", "cuisine_text"]],
                              get_position="[lng, lat]", get_fill_color="color", get_radius=90, pickable=True)],
            tooltip={"text": "{label}\n{kind} {cuisine_text}\nUnverified: check with the store"}),
            height=480)

# ---------- Footer: disclaimer and contributors ----------
REPO = "https://github.com/Chloe-Tu2/The-EverFlavor-AI"
CONTRIBUTORS = ["Chloe-Tu2", "Evaabou20", "med27-coder"]   # GitHub accounts of the team (Team EverGlow)
st.markdown(f"""
<footer class="site-footer">
  <div class="footer-title">Please read</div>
  <ul>
    <li><b>Not medical advice.</b> The checks read ingredient names and can miss things: a brand's recipe,
        cross-contact in a factory, or an ingredient written in an unusual way. With a serious allergy or a
        health condition, always read the product label and ask your doctor or dietitian.</li>
    <li><b>Diet labels are not certifications.</b> "Halal", "kosher" and the other diets mean the ingredients
        contain nothing the diet forbids; they cannot show how food was produced or certified.</li>
    <li><b>Some numbers are estimates.</b> Calories and protein marked as estimated are approximate.</li>
    <li><b>Nothing you enter is saved.</b> Your choices last only while this page is open.</li>
  </ul>
  <div class="footer-title">Made by Team EverGlow</div>
  <div class="credits">{"".join(f'<a href="https://github.com/{name}" target="_blank" rel="noopener">@{name}</a>' for name in CONTRIBUTORS)}</div>
  <small>Version {__version__} (beta) · ITAI 2277 Capstone · <a href="{REPO}" target="_blank" rel="noopener">Project on GitHub</a> ·
  <a href="{REPO}/blob/main/LICENSE" target="_blank" rel="noopener">MIT License</a> · Recipe photos belong to their sources.</small>
</footer>
""", unsafe_allow_html=True)
