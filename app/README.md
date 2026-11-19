# App (front end)

The EverFlavor Kitchen, [app.py](app.py), built with [Streamlit](https://streamlit.io). What it does for the people
who use it is in the main README, "The App: EverFlavor Kitchen". This page is for whoever changes it.

## Run it

From the project folder, after notebook 01 has built the recipe data (or on `data/demo/`, as the live site does):

```bash
uv pip install -r config/requirements-app.txt   # or pip install ...
streamlit run app/app.py
```

The browser opens at `http://localhost:8501`. Save the file and the page reloads. Stop with **Ctrl+C**.
`?start=1` in the address skips the welcome page.

## The files

| File | What is in it |
|---|---|
| [app.py](app.py) | The page: welcome, sidebar profile, Find recipes, the dish page, Check my recipe, Map: Houston, Settings, the bell |
| [kitchen_scene.html](kitchen_scene.html) | The living kitchen behind the page: light by the hour, taps, leaves, steam |
| `static/` | Files Streamlit serves at `app/static/`; the app copies the kitchen scenes into `static/scenes/` (not committed) so the browser fetches each kitchen once |
| [chef_lines.py](chef_lines.py) | What the chefs say: greetings, small talk and quotes, each with its source |
| [dish_info.py](dish_info.py) | The dish page's nutrition facts, as the data has them |
| [themes.py](themes.py) | Each kitchen's page colours (checked for contrast by `tests/test_app_contrast.py`) |
| [updates.py](updates.py) | The What's new notes and which of the team's banners they show (`design/pixel-art/assets/banner_*.png`) |

## Where each part gets its answers

| Part | Back end (`src/everflavor`) |
|---|---|
| Sidebar profile, in four groups, each rule strict, avoid, warn or ignore | `restrictions`, `confidence.ProfileResponse`, `safety.UserProfile` |
| **Find recipes**, Browse by region, Explore by place | `recommend`, `taxonomy` |
| The dish page: name, steps, cookware, times, nutrition | `dish_names`, `dish_steps`, `cooking_time`, `calories` |
| The waiter (Walter or Nathalie) | `waiter`, with the facts in `data/knowledge/` |
| **Check my recipe**: findings with a pixel sign and how sure we are; the nutrition estimate | `recipe_check`, `restrictions.assess`, `confidence`, `preparation`, `calories.nutrition_estimate` |
| A local model's friendly words for a problem (only shown if they match the gate) | `llm.check_and_explain`, `llm.choose_model` (`llama3.2` with Ollama; plain sentences without it) |
| **Map: Houston** and "Where to buy" | `places` (each claim with its evidence), `stores` |
| My Cookbook (saved recipes) | `saved_recipes` (this browser only) |

The severity signs are pixel art from `design/pixel-art/make_pixel_art.py` (`sign_*.png`), not emoji.

**Not on the page yet** (the back end is ready): a chat with the chef using `llm.ask_agent` and the meal planner
`crew.plan_meal`. Both need Ollama; see the main README's "Agent tools and the meal planner" and the planner.

**Try the safety gate** in the Check my recipe tab: `3 tbsp satay sauce` (hidden peanut), `200 g p0rk belly` or
`panceta de cerdo` (disguised and foreign words, both read as pork), `1 cup chocolate pigs` (a sweet: passes).

**Golden rule:** safety decisions come from the back end ([src/everflavor](../src/everflavor/README.md)).
The page only shows them; never filter or "fix" safety in the page code.
