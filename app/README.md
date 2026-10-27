# App (front end)

The starter web page, [app.py](app.py), built with [Streamlit](https://streamlit.io): plain Python, no HTML.
It is a starting point for the front-end team. (The proposal names Gradio; the back end works with either.)

## Run it

From the project folder, after notebook 01 has built the recipe data:

```bash
uv pip install -r config/requirements-app.txt   # or pip install ...
streamlit run app/app.py
```

The browser opens at `http://localhost:8501`. Save the file and the page reloads. Stop with **Ctrl+C**.

## The look

A pixel-art kitchen behind the page, a pixel chef who reads out the results, real food photos in the recipe
cards, and four color themes (**Settings**, top right; Classic is Eva's palette). The art and
the concept are in [design/](../design/README.md). Searching a cuisine family can open its
own kitchen (Japanese, Mediterranean, Mexican, Middle Eastern; Settings > Match the kitchen to the cuisine).
`.streamlit/config.toml` fixes Streamlit's own theme to
light, so the colors look the same on every computer.

## What is on the page

| Part | Uses |
|---|---|
| Sidebar: foods to avoid, diets, vegetarian / vegan, calories | `safety.UserProfile` |
| Tab **Find recipes** | `recommend.baseline_recommend` |
| Tab **Check my recipe** | `llm.check_and_explain`: the safety gate names the line and rule each problem breaks; when Ollama is running, a local model explains a failure in friendly words (shown only if they match the gate) |
| Sidebar: local AI on / off | `llm.choose_model`: a local Ollama model (`llama3.2` when installed: `ollama pull llama3.2`), or plain sentences when Ollama is not running (always in Colab) |

**Not on the page yet** (the back end is ready): a chat tab using `llm.ask_agent` (a local model with the five tools, every answer screened) and the meal planner `crew.plan_meal` (a CrewAI Chef writes a recipe, the code checks it). Both need Ollama running; see the main README's "Agent tools and the meal planner".

**Try the safety gate** in the Check my recipe tab: `3 tbsp satay sauce` (hidden peanut), `200 g p0rk belly` or
`panceta de cerdo` (disguised and foreign words, both read as pork), `1 cup chocolate pigs` (a sweet: passes).

**Golden rule:** safety decisions come from the back end ([src/everflavor](../src/everflavor/README.md)).
The page only shows them; never filter or "fix" safety in the page code.
