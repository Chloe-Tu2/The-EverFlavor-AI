# App (front end)

The starter web page, [app.py](app.py), built with [Streamlit](https://streamlit.io): plain Python, no HTML.
It is a starting point for the front-end team. (The proposal names Gradio; the back end works with either.)

## Run it

From the project folder, after notebook 01 has built the recipe data:

```bash
pip install -r config/requirements-app.txt
streamlit run app/app.py
```

The browser opens at `http://localhost:8501`. Save the file and the page reloads. Stop with **Ctrl+C**.

## What is on the page

| Part | Uses |
|---|---|
| Sidebar: foods to avoid, diets, vegetarian / vegan, calories | `safety.UserProfile` |
| Tab **Find recipes** | `recommend.baseline_recommend` |
| Tab **Check my recipe** | `safety.check_recipe`: names the line and the rule each problem breaks |

**Golden rule:** safety decisions come from the back end ([src/everflavor](../src/everflavor/README.md)).
The page only shows them; never filter or "fix" safety in the page code.
