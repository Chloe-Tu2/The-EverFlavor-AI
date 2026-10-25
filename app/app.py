"""EverFlavor AI: the front end (Streamlit), "EverFlavor Kitchen".

How to run it (from the project folder):

    pip install -r config/requirements-app.txt
    streamlit run app/app.py

A browser tab opens at http://localhost:8501. Save this file and the page reloads.

How Streamlit works, in one sentence: the whole file runs top to bottom every time
someone clicks something, and each `st.something(...)` call draws one thing on the page.

The look: a pixel-art kitchen behind the page and a pixel chef who reads out the results.
The art is drawn by design/pixel-art/make_pixel_art.py (one kitchen per color theme); the
color themes are in THEMES below. Settings (top right of the page) switch the theme.
"""
import ast
import base64
import html
import sys
from functools import cache
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Let Python find our package in src/ (same trick the notebooks use).
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from updates import UPDATES  # app/updates.py: the What's new notes

from everflavor import __version__
from everflavor.cuisine import ORIGIN_LABELS
from everflavor.diets import DIET_PROFILES
from everflavor.flags import FLAG_RULES
from everflavor.llm import check_and_explain, choose_model
from everflavor.recommend import baseline_recommend
from everflavor.safety import UserProfile

DATA = ROOT / "data" / "processed"
ART = ROOT / "design" / "pixel-art" / "assets"   # drawn by design/pixel-art/make_pixel_art.py

# Use the lightweight demo dataset when full data is unavailable.
if not (DATA / "recipes_test.parquet").exists():
    DATA = ROOT / "data" / "demo"

# The kitchens. "Classic" is Eva's cooking-game palette and the default. Each has its own kitchen picture (scene)
# and the colors of the page drawn over it. The time of day (Settings) is the kitchen's light, not a kitchen of its
# own: Classic's morning and night are the former Morning and Night themes (design/pixel-art/build_classic_scene.py).
THEMES = {
    "Classic": {"scene": "classic_hours", "panel": "#FFF8E7", "sidebar": "#FFF1E6", "border": "#8B4513",
                "text": "#4A2C2A", "heading": "#8B4513", "button": "#FFB6C1", "button_hover": "#FF8FAB",
                "shadow": "#D9A679", "bubble": "#FFFFFF"},
    # The cuisine kitchens, each with its own chef. Chinese, Mediterranean, Mexican and Middle Eastern are the v5
    # kitchens (traced from the team's art, four hours, design/pixel-art/build_scenes.py); Japanese and Moroccan the
    # code-drawn drafts (design/pixel-art/cuisine_kitchens.py)
    "Japanese": {"scene": "japanese", "chef": "ref_japanese_", "panel": "#FBF3E2", "sidebar": "#F3E6CC",
                 "border": "#5B3A29", "text": "#3A2A20", "heading": "#8E2C2C", "button": "#E9C46A",
                 "button_hover": "#D9AE4A", "shadow": "#C9A57A", "bubble": "#FFFDF7"},
    "Chinese": {"scene": "v5_chinese", "chef": "ref_chinese_", "panel": "#FBF5EA", "sidebar": "#F4E9D8",
                "border": "#7A2A22", "text": "#3A2420", "heading": "#B22D2D", "button": "#E9B44C",
                "button_hover": "#D99E30", "shadow": "#CDBFA6", "bubble": "#FFFDF7"},
    "Moroccan": {"scene": "moroccan", "chef": "moroccan_", "panel": "#FCF3E8", "sidebar": "#F6E2D2",
                 "border": "#7A4B22", "text": "#3B2418", "heading": "#1F6F5C", "button": "#E2B33C",
                 "button_hover": "#CF9E25", "shadow": "#D69068", "bubble": "#FFFDF6"},
    "Mediterranean": {"scene": "v5_mediterranean", "panel": "#FBF6EC", "sidebar": "#EFE6D6", "border": "#6B4A2F",
                      "text": "#3B2E22", "heading": "#4F6B2A", "button": "#D9A441", "button_hover": "#C48F2C",
                      "shadow": "#CDBDA3", "bubble": "#FFFFFF"},
    "Mexican": {"scene": "v5_mexican", "chef": "mexican_", "panel": "#FFF6E5", "sidebar": "#FCE8C8",
                "border": "#8C3B1F", "text": "#3B2218", "heading": "#1F5FA8", "button": "#F2A541",
                "button_hover": "#E08E22", "shadow": "#D88A3A", "bubble": "#FFFDF5"},
    "Middle Eastern": {"scene": "v5_middle_eastern", "chef": "ref_middle_eastern_", "panel": "#FBF3E4",
                       "sidebar": "#F3E2C2", "border": "#7A4B22", "text": "#3B2A1A", "heading": "#1E6F80",
                       "button": "#D9A830", "button_hover": "#C49420", "shadow": "#C9A46B", "bubble": "#FFFDF6"},
}
# The page's colors for the Classic kitchen at night (the former Night theme): easier on the eyes in the dark
NIGHT_COLORS = {"panel": "#2A2138", "sidebar": "#241C31", "border": "#FF8FAB", "text": "#F3E9F5", "heading": "#FFD98A",
                "button": "#FF8FAB", "button_hover": "#FF6F95", "shadow": "#120D1A", "bubble": "#3A2E4A"}
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


@st.cache_resource   # load the data once and share it (read only), not a fresh copy on every click
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
@import url('https://fonts.googleapis.com/css2?family=Jersey+10&family=VT323&display=swap');
:root {{
  --panel: {theme['panel']}; --sidebar: {theme['sidebar']}; --border: {theme['border']};
  --text: {theme['text']}; --heading: {theme['heading']}; --button: {theme['button']};
  --button-hover: {theme['button_hover']}; --shadow: {theme['shadow']}; --bubble: {theme['bubble']};
  --pixel-font: 'Jersey 10', 'Courier New', monospace;   /* titles, tabs, buttons, numbers */
  --pixel-text: 'VT323', 'Courier New', monospace;       /* the chef's lines, small labels */
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
  box-shadow: 6px 6px 0 var(--shadow); padding: 0.4rem 1.1rem !important;
}}
.tagline {{
  display: inline-block; background: var(--panel); color: var(--text); border: 2px solid var(--border);
  padding: 0.25rem 0.75rem; margin: 0.4rem 0 0; font-size: 1rem;
}}
/* The tools: a recipe card pinned over the counter */
[data-testid="stTabs"] {{
  background: color-mix(in srgb, var(--panel) 96%, transparent); border: 4px solid var(--border);
  box-shadow: 8px 8px 0 var(--shadow); padding: 0.75rem 1.75rem 1.75rem;
}}
[data-testid="stSidebar"] {{ background: var(--sidebar); border-right: 4px solid var(--border); }}
/* Every text color comes from the theme, so a computer in dark mode does not paint white text on cream */
.stApp, .stApp p, .stApp li, .stApp label, [data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"],
[data-testid="stMetricLabel"] p, [data-testid="stMetricValue"], [data-testid="stSidebar"] * {{ color: var(--text); }}
h1, h2, h3, [data-testid="stTab"] p {{
  color: var(--heading) !important; font-family: var(--pixel-font) !important; font-weight: 400 !important;
  letter-spacing: 0.02em;
}}
.stApp h1 {{ font-size: 3.4rem !important; line-height: 1.1 !important; }}
.stApp h3 {{ font-size: 2rem !important; }}
h1 {{ letter-spacing: 0.02em; }}
/* Inputs stay light with dark text in every theme, so they are always readable */
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, textarea, div[data-baseweb="base-input"] {{
  background: #FFFDF8 !important; border: 2px solid var(--border) !important; border-radius: 0 !important;
}}
div[data-baseweb="input"] input, textarea, div[data-baseweb="select"] * {{ color: #2B1E1A !important; }}
/* Chosen items in "I can't eat" / "I follow": the theme's button color, so the dark text stays readable */
[data-testid="stMultiSelectTagsContainer"] [data-tag] {{
  background: var(--button) !important; color: #2B1E1A !important; border: 2px solid var(--border) !important;
  border-radius: 0 !important;
}}
[data-testid="stMultiSelectTagsContainer"] [data-tag] * {{ color: #2B1E1A !important; }}
/* Pixel buttons: square corners, a hard shadow that "presses" on click */
.stButton > button {{
  background: var(--button); color: #2B1E1A; border: 3px solid var(--border); border-radius: 0;
  font-family: var(--pixel-font); font-size: 1.35rem; font-weight: 400; box-shadow: 4px 4px 0 var(--shadow);
}}
.stButton > button:hover {{ background: var(--button-hover); border-color: var(--border); color: #2B1E1A; }}
.stButton > button:active {{ transform: translate(3px, 3px); box-shadow: 1px 1px 0 var(--shadow); }}
/* Recipe cards (each container has a key, recipe-card-<n>, which Streamlit turns into a class) */
.stApp [class*="st-key-recipe-card"] {{
  background: var(--panel); border: 3px solid var(--border) !important; border-radius: 0 !important;
  box-shadow: 5px 5px 0 var(--shadow); padding: 1rem 1.25rem;
}}
[data-testid="stImage"] img {{ border: 3px solid var(--border); }}
/* The chef and the speech bubble */
.chef-row {{ display: flex; gap: 1.25rem; align-items: flex-end; margin: 0.5rem 0 1.25rem; }}
.chef {{ width: 128px; height: 128px; flex: none; background: center / contain no-repeat; image-rendering: pixelated; }}
.bubble {{
  position: relative; flex: 1 1 auto; overflow-wrap: anywhere; background: var(--bubble); color: var(--text); border: 3px solid var(--border);
  padding: 0.6rem 1rem; font-family: var(--pixel-text); font-size: 1.45rem; line-height: 1.15;
  box-shadow: 4px 4px 0 var(--shadow); min-width: 0;
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
[data-testid="stTab"] p {{ font-size: 1.5rem; }}
/* Top right: the What's new bell and Settings (the oven knob), pixel buttons */
[data-testid="stPopover"] {{ display: flex; justify-content: flex-end; }}
[data-testid="stPopover"] button {{
  background: var(--panel); border: 3px solid var(--border); border-radius: 0; box-shadow: 4px 4px 0 var(--shadow);
}}
[data-testid="stPopover"] button p {{ font-family: var(--pixel-font); font-size: 1.3rem; color: var(--text); }}
[data-testid="stPopover"] button p::before {{ width: 24px; height: 24px; margin-right: 0.4rem; }}
.st-key-settings [data-testid="stPopover"] button p::before {{ background-image: url('{art("icon_settings")}'); }}
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
  box-shadow: 6px 6px 0 var(--shadow) !important; color: var(--text);
}}
[data-testid="stPopoverBody"] p, [data-testid="stPopoverBody"] li {{ color: var(--text); }}
.no-photo {{
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 0.5rem;
  aspect-ratio: 4 / 3; background: var(--sidebar); border: 3px dashed var(--border); color: var(--text);
  font-family: var(--pixel-text); font-size: 1.2rem; text-align: center; padding: 0.5rem;
}}
.no-photo .ico {{ width: 80px; height: 80px; }}
.updates h5 {{ font-family: var(--pixel-font); font-weight: 400; font-size: 1.4rem; margin: 0.5rem 0 0; color: var(--heading); }}
.updates ul {{ margin: 0.2rem 0 0.6rem 1.1rem; padding: 0; }}
.stats {{ display: flex; flex-wrap: wrap; gap: 0.75rem 1.5rem; margin: 0.25rem 0 0.75rem; }}
.stat {{ display: flex; align-items: center; gap: 0.5rem; font-family: var(--pixel-font); font-size: 1.6rem; }}
.stat .ico, .bubble .ico {{ width: 32px; height: 32px; }}
.bubble .ico {{ margin-right: 0.5rem; }}
.stat small {{ font-family: var(--pixel-text); opacity: 0.8; font-size: 1.2rem; }}
/* The concept layout: the kitchen open under the title, the chef at the bottom of the sidebar */
.kitchen-view {{ height: 30vh; }}
.st-key-chef-side {{ margin-top: 0.5rem; }}
.st-key-chef-side .chef-row {{ flex-direction: column-reverse; align-items: center; gap: 0.9rem; }}
.st-key-chef-side .chef {{ width: 132px; height: 132px; }}
.st-key-chef-side .bubble {{ font-size: 1.15rem; line-height: 1.1; width: 100%; padding: 0.45rem 0.7rem; }}
.st-key-chef-side .bubble::before {{
  left: calc(50% - 6px); bottom: -12px; border-right-color: transparent; border-top-color: var(--border);
}}
@media (min-width: 641px) {{ .st-key-chef-main {{ display: none; }} }}
@media (max-width: 640px) {{
  .st-key-chef-side {{ display: none; }}
  .kitchen-view {{ height: 16vh; }}
  .block-container {{ padding: 1.25rem 1rem 3rem; }} .chef {{ width: 80px; height: 80px; }}
  [data-testid="stTabs"] {{ padding: 0.5rem 0.9rem 1.25rem; }}
  [data-testid="stTab"] p::before {{ width: 28px; height: 28px; margin-right: 0.3rem; }}
  [data-testid="stTab"] p {{ font-size: 1.2rem; }}
  .stApp h1 {{ font-size: 2.4rem !important; }}
}}
/* Footer: the disclaimer and the people behind the project, on a wooden board */
.site-footer {{
  margin-top: 2.5rem; background: var(--panel); color: var(--text); border: 4px solid var(--border);
  box-shadow: 6px 6px 0 var(--shadow); padding: 1rem 1.5rem; font-size: 0.95rem; line-height: 1.5;
}}
.site-footer .footer-title {{ font-family: var(--pixel-font); font-weight: 400; font-size: 1.5rem; color: var(--heading); margin: 0 0 0.25rem; padding: 0; }}
.site-footer ul {{ margin: 0.25rem 0 0.75rem 1.1rem; padding: 0; }}
.site-footer a {{ color: var(--heading); font-weight: 600; }}
.site-footer .credits {{ display: flex; flex-wrap: wrap; gap: 0.5rem 1.25rem; margin: 0.25rem 0 0.75rem; }}
.site-footer small {{ opacity: 0.85; }}
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
  .stButton > button:active, .chef:active {{ transform: none; animation: none; }}
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


def stats(place, calories: float, protein: float, minutes: float | None) -> None:
    """A recipe's calories, protein and time, each with its pixel icon."""
    chips = [("icon_flame", f"{calories:.0f}", "kcal"), ("icon_protein", f"{protein:.0f} g", "protein"),
             ("icon_timer", f"{minutes:.0f}" if minutes is not None and pd.notna(minutes) else "N/A", "minutes")]
    place.markdown('<div class="stats">' + "".join(
        f'<div class="stat"><span class="ico" style="background-image: url({art(icon)})"></span>'
        f'{value} <small>{label}</small></div>' for icon, value, label in chips) + "</div>", unsafe_allow_html=True)


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
heading.markdown('<p class="tagline">Recipes that fit what you can eat, checked ingredient by ingredient.</p>',
                 unsafe_allow_html=True)
news_spot, settings_spot = corner.columns(2)
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
        st.caption("Local AI: off. The rules still check everything.", help=ai["reason"])
    chef.append(st.container(key="chef-side").empty())

profile = UserProfile(avoid=tuple(avoid), diets=tuple(diets), vegetarian=vegetarian,
                      vegan=vegan, calories_per_meal=calories)
chef_says(chef, "happy", "Welcome to the kitchen! Tell me what you can't eat in the sidebar, "
                         "then find a recipe or check one of yours.")

# ---------- Two tabs ----------
find_tab, check_tab = st.tabs(["Find recipes", "Check my recipe"])   # their pixel icons come from the CSS

with find_tab:
    pool, cuisine = recipes, "Any"
    if "origin_country" in recipes:
        # One search box (a dish, a country or a region, with suggestions as you type) and, for those who would
        # rather not type, Browse by region: every region with its countries, one tap to pick one
        counts = recipes["origin_country"].value_counts()
        counts = counts[(counts >= MIN_COUNTRY_RECIPES) & (counts.index != "Unknown")]
        regions = recipes.dropna(subset=["origin_region"]).groupby("origin_region")["origin_country"].first()
        suggestions = [*counts.index, *(f"{r} ({c})" for r, c in regions.items())]

        def pick_place(key: str) -> None:
            st.session_state["search"] = st.session_state[key]
            st.session_state[key] = None

        search_spot, browse_spot = st.columns([4, 1], vertical_alignment="bottom")
        query = search_spot.selectbox(
            "What would you like to eat?", suggestions, index=None, key="search", accept_new_options=True,
            placeholder="A dish or where it's from: ramen, Korean, Louisiana, tacos...",
            help="Type a dish, a country or a region. The kitchen follows the country when Settings says so.")
        with browse_spot.popover("Browse by region", width="stretch"):
            family_of = recipes.groupby("origin_country")["cuisine_family"].agg(lambda f: f.mode().iat[0])
            for family in ["Asian", "European", "Latin American", "Middle Eastern", "African", "Other"]:
                in_family = [c for c in counts.index if family_of.get(c) == family]
                if in_family:
                    st.pills("North America, Oceania and more" if family == "Other" else family, in_family,
                             key=f"browse-{family}", on_change=pick_place, args=(f"browse-{family}",))
        country, region, dish = read_search(query)
        if country:
            pool = pool[pool["origin_country"] == country]
        if region:
            pool = pool[pool["origin_region"] == region]
        for word in dish:
            pool = pool[pool["recipe_name"].str.contains(word, case=False, regex=False)]
        if query:                                   # what the search is doing, above the results
            asked = [f"dishes from {region + ', ' if region else ''}{country}"] if country else []
            asked += ['"' + " ".join(dish) + '" in the name'] if dish else []
            st.caption("Looking for " + ", ".join(asked) + f" · {len(pool):,} recipes")
    else:                                           # the demo data has no countries: the cuisine families only
        cuisine = st.selectbox("Cuisine", ["Any"] + sorted(recipes["cuisine_family"].dropna().unique()), key="cuisine")
    how_many = st.number_input("How many ideas?", min_value=1, max_value=20, value=5)

    if st.button("Find recipes", type="primary"):
        loading = cooking("Cooking up ideas...")
        results = baseline_recommend(
            pool,
            cuisine_family=None if cuisine == "Any" else cuisine,
            calorie_target=calories,
            vegetarian_only=vegetarian,
            vegan_only=vegan,
            avoid=avoid,
            diets=diets,
            top_n=int(how_many),
        )
        loading.empty()
        if results.empty:
            chef_says(chef, "thinking", "Hmm, nothing matches all your choices. Try removing one.", "empty")
        else:
            chef_says(chef, "happy", f"Here {'is' if len(results) == 1 else 'are'} {len(results)} "
                                     f"{'idea' if len(results) == 1 else 'ideas'} close to {calories} calories. "
                                     "Every one passed the safety check for your profile.", "safe")
        for number, (_, row) in enumerate(results.iterrows()):
            with st.container(border=True, key=f"recipe-card-{number}"):
                photo, link, site = row.get("image_url"), row.get("url"), row.get("source")
                picture, info = st.columns([1, 2])
                if isinstance(photo, str) and photo.startswith("https://"):
                    # The photo comes with the recipe from its website; the credit links there, so anyone can check
                    picture.image(photo, width="stretch")
                    if isinstance(link, str) and link.startswith("http"):
                        picture.caption(f"Photo: [{html.escape(str(site or 'the recipe page'))}]({link})")
                else:
                    picture.markdown(f'<div class="no-photo"><span class="ico" style="background-image: '
                                     f'url({art("icon_cloche")})"></span>No photo of this dish yet</div>',
                                     unsafe_allow_html=True)
                info.subheader(row["recipe_name"].title())
                where = row.get("origin_country")
                if isinstance(where, str) and where != "Unknown":
                    region = row.get("origin_region")
                    info.caption(f"From {region + ', ' if isinstance(region, str) else ''}{where}")
                stats(info, row["calories_per_serving"], row["protein_g"], row.get("minutes"))
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
        loading = cooking("Checking every ingredient...")
        report = check_and_explain(lines.splitlines(), name, profile, model=ai["model"] if use_ai else None)
        loading.empty()
        if report["passed"]:
            chef_says(chef, "happy", f"{name} is safe for your profile. Happy cooking!", "safe")
            st.success("Safe for your profile.")
        else:
            first = report["problems"][0]
            chef_says(chef, "alert", f"Watch out! \"{first['line']}\" breaks {nice(first['rule'])}"
                                     + (f", and I found {len(report['problems']) - 1} more."
                                        if len(report["problems"]) > 1 else "."), "alert")
            st.error(f"{len(report['problems'])} problem(s) found:")
            for problem in report["problems"]:
                st.write(f"- **{problem['line']}**: breaks *{nice(problem['rule'])}* "
                         f"(matched: {problem['matched']})")
        st.info(report["text"])
        st.caption(f"Explained by: {report['explained_by']}. Rules checked: "
                   + ", ".join(nice(r) for r in report["checked"]))

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
