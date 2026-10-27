# Draft: the main README for 0.7.1

A draft for the team to read before the 0.7.1 release (planner, "Before the merge into `main`", gate 1b). It is
not the README yet: at the release, each section below replaces the section of the same name in `README.md`, and
the rest of `README.md` stays as it is. Numbers come from the latest runs (2026-10-25 and 2026-10-26); check them
again at the release, once the Food.com photos are finished.

What changes, in short:

| README section | Change |
|---|---|
| The App: EverFlavor Kitchen | Rewritten for the living kitchens, chefs, search, dish page, Map tab and photos |
| Versions and plans | 0.7.1 instead of 0.5.1 |
| Data Sources | A new "Photos and places" table; the data rule |
| Project Structure | Notebook 10, `scripts/`, the new shared modules, app files and tests |
| Watch (new, at the end) | The team's cooking demo video |
| Top links | Add [The App](#the-app-everflavor-kitchen-front-end) and [Watch](#watch) |

---

## The App: EverFlavor Kitchen (Front End)

The web page, in [app/app.py](app/app.py) ([Streamlit](https://streamlit.io)): a pixel-art kitchen that lives in
your time of day, a chef who reads out every result, and safe recipe ideas from around the world. Design, art and
plans: [design/](design/README.md). It runs after notebook 01 has built the recipe data (or on the small demo
data in `data/demo/`):

```bash
pip install -r config/requirements-app.txt
streamlit run app/app.py
```

The browser opens at `http://localhost:8501` on a short welcome page; **Find a safe recipe** opens the kitchen.

| Part | What it does |
|---|---|
| **Your profile** (sidebar) | Foods you can't eat, diets you follow, calories per meal. On phones the chef points to it |
| **Find recipes** | One search box: a dish, a country or a region ("ramen", "Korean", "Louisiana"), or **Browse by region**. All regions is the default |
| **Recipe cards** | The dish's clean name (the posted title underneath), its country, calories, protein, cook time (estimated when the recipe gives none), a "why it fits" line, how to say the dish's name, and a photo |
| **About this dish** | Ingredients, the steps one at a time, and a YouTube search for the dish |
| **Check my recipe** | Runs the safety gate on pasted ingredient lines and names the line and rule each problem breaks |
| **Map** | Grocers, restaurants and butchers in Houston from OpenStreetMap. No location is asked; the map opens on Houston |

**The kitchens.** Searching a country or region opens its kitchen (Japanese, Chinese, Mediterranean, Mexican,
Middle Eastern, Moroccan, or the Classic kitchen). The light follows your clock, with your permission, or a time
you pick in Settings: lamps are off by day and lit at sunset and night. Tap the kitchen: plants drop leaves, lamps
switch, pots steam, stools wobble. Each region has its chef, as a man or a woman (Settings > Your chef), with
greetings in the region's language and quotes from well-known chefs of that region.

**Photos.** A card shows the recipe's own photo with a link to its page. Logos and photos that do not show the
dish (an image-text check) are hidden. Without its own photo, a card may show a free photo of the dish in general
from Wikimedia Commons, labelled "not this recipe", with its credit. With no photo at all it shows a pixel-art
pan and "Cooking up a picture...".

**Safety stays in the back end.** The page only shows what `src/everflavor` decided; diet labels say
"halal-friendly ingredients", never "halal", and medical profiles are screens, not advice.

### Versions and plans

EverFlavor is in **beta** (version 0.7.1). Every change is listed in [CHANGELOG.md](CHANGELOG.md) (semantic
versions; the finished release is 1.0.0), and the app's **What's new** bell shows the latest notes. What comes
next, grouped by version, with the reasons and trade-offs: the [planner](docs/plans/README.md) (start here).

---

## Data Sources (additions)

A new table after "Nutrition and product lookups":

### Photos and places

| Source | What we use it for | License | How it is collected |
|---|---|---|---|
| Recipe photos from the recipe datasets (Hugging Face, TheMealDB) | Each recipe's own photo, with a link to its page | Each recipe site's terms; research use | Downloaded once, checked, not committed |
| [Food.com - Recipes and Reviews (Kaggle, irkaal)](https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews) | Photo links for our Food.com recipes (111,803 of 218,024), joined on the recipe number | CC0 | `kagglehub`, notebook 10 |
| [Wikimedia Commons](https://commons.wikimedia.org) via [Wikidata](https://www.wikidata.org) | A general photo of a dish when a recipe has none (1,737 dishes), and recordings of dish names | Free licenses only, credited on the card | `scripts/dish_photos/fetch_dish_photos.py` |
| [OpenStreetMap](https://www.openstreetmap.org) with [OpenFreeMap](https://openfreemap.org) tiles | The Map tab: Houston grocers, restaurants, butchers | ODbL; tiles free, no key | Overpass download, notebook 03 |

**The data rule** (decided 2026-10-24): only open-license or research-use datasets; no scraping of forums, social
media or video comments. Every source is listed in [docs/sources.md](docs/sources.md).

---

## Project Structure (changes)

Lines to add to the tree:

```text
├── notebooks/
│   └── 10_recipe_photos.ipynb                     # Food.com's own photos (CC0): links, download, logo marks
├── scripts/
│   ├── recipe_extras.py          # Cook times and photo links as side tables for the app
│   ├── recipe_photos/            # Download recipe photos, mark logos, check each photo shows its dish (CLIP)
│   └── dish_photos/              # Free general dish photos from Wikimedia Commons
├── app/
│   ├── app.py         # EverFlavor Kitchen: landing page, kitchens, search, cards, dish page, Map tab
│   ├── kitchen_scene.html  # The living kitchen: light by the hour, taps, leaves, steam
│   ├── chef_lines.py  # The chefs' greetings and world chefs' quotes, by region
│   └── updates.py     # The What's new notes
├── design/pixel-art/  # Kitchens, chefs, icons, the loading screen and the no-photo picture (drawn by code)
├── src/everflavor/
│   ├── dish_names.py    # A recipe title to the dish's clean name
│   ├── cooking_time.py  # Estimated cook time when a recipe gives none
│   └── dish_steps.py    # A recipe's steps, one at a time
└── tests/
    ├── test_dish_names.py, test_cooking_time.py, test_dish_steps.py
    ├── test_app_art.py   # Every picture the app names is drawn
    └── test_version.py   # The version, CHANGELOG and What's new agree
```

Also: the `app/` line "Starter front end" becomes the app line above.

---

## Watch

*New, at the very end, before the footer.*

See EverFlavor cook: the team's cooking demo video, [on YouTube](https://www.youtube.com/) *(link to come from the
team)*.
