# The-EverFlavor-AI

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-FF6B35)
![Gradio](https://img.shields.io/badge/Gradio-Chat%20Interface-F97316)
![LLM](https://img.shields.io/badge/LLM-Groq%20%7C%20LLaMA%203.1-00A67E?logo=meta&logoColor=white)
![Multi-Agent](https://img.shields.io/badge/Architecture-Multi--Agent%20System-crimson)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![ITAI2277](https://img.shields.io/badge/ITAI%202277-Capstone%20Project-blueviolet)
![Project](https://img.shields.io/badge/Project%20Tier-Advanced%20%7C%20Agentic%20AI-gold)

**Multi-Agent Diet & Discovery System**

> A conversational multi-agent AI that helps users create authentic global recipes while respecting calorie limits, dietary restrictions, and ingredient availability — then finds the nearest specialty supermarket.

---

## Overview

**EverFlavor AI** solves everyday decision fatigue around food. Users simply talk to the system in natural language, for example:

> “I have 550 calories left, no pork, I’m tired after work, and I want something bold from Middle Eastern or Latin American cuisine. I can drive 15 minutes.”

The system returns:
- A complete step-by-step recipe from one of five major cuisine families
- Smart ingredient substitutions
- Accurate calorie & nutrition information
- The nearest specialty supermarket for that cuisine
- Full respect for religious, medical, and ethical restrictions

---

## Key Features

- **Multi-Agent Architecture** with three specialized agents
- Support for **5 major global cuisine families**:
  - Asian
  - European
  - Latin American
  - African
  - Middle Eastern
- Smart ingredient substitutions
- Hard-coded safety filter for dietary restrictions (cannot be overridden by the LLM)
- Real specialty store search via Google Places API
- Nutrition grounded in Open Food Facts + USDA FoodData Central
- Human-in-the-Loop safety gates
- Gradio chat interface for easy demonstration

---

## Architecture

### Three Specialized Agents

| Agent                        | Responsibility                                      |
|-----------------------------|-----------------------------------------------------|
| **Nutritionist & Preference Agent** | Extracts calories, restrictions, cuisine preference, and driving radius |
| **Chef Agent**                   | Generates authentic recipes + practical substitutions |
| **Sourcing Agent**               | Finds the nearest specialty supermarket             |

**Orchestration:** Sequential workflow using CrewAI with shared context and an independent safety filter that runs after recipe generation.

---

## Tech Stack

- **Language:** Python 3.10+
- **Multi-Agent Framework:** CrewAI
- **Interface:** Gradio
- **LLM:** Groq (LLaMA 3.1) or compatible tool-calling model
- **APIs:**
  - Open Food Facts
  - USDA FoodData Central
  - Google Places API
- **Safety:** Hard-coded post-generation restriction filter

---

## Project Scope (Prototype)

- Five major cuisine families only
- One metro area for store search (e.g., Houston)
- Session-based user profiles
- Clear substitution logic
- Full restriction handling (religious, medical, ethical)

---

## Data Sources

### Recipe datasets

All four are collected in Week 4 of the notebook and combined into one recipe table in Week 5:

| Dataset | Size | What we use it for | How it is collected |
|---|---|---|---|
| [Food.com Recipes (Kaggle)](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions) | ~231,000 recipes | Main recipe source: ingredients, steps, calories, cook time, and cuisine tags (including ~2,800 African and ~2,000 Middle Eastern recipes) | `kagglehub` download |
| [Hugging Face: recipes-with-nutrition](https://huggingface.co/datasets/datahiveai/recipes-with-nutrition) | ~39,000 recipes | Exact nutrition (calories, protein, fat, carbs, sodium), health labels (vegetarian, gluten-free, allergens), cuisine labels | `datasets` library |
| [CulinaryDB](https://cosylab.iiitd.edu.in/culinarydb/) | ~45,700 recipes, 22 regions | Extra African (~650) and Middle Eastern (~990) recipes; titles and ingredients only | Free zip download |
| [TheMealDB](https://www.themealdb.com) | ~790 recipes | Recipes with full instructions from many countries | Free public API (no key needed) |

### Nutrition and product lookups

Small samples are collected in Week 4. Later, the agents will look up ingredients through these APIs.

| Source | What we use it for | Key needed |
|---|---|---|
| [USDA FoodData Central](https://fdc.nal.usda.gov/) | Official calorie and nutrient values for single ingredients | Yes: `USDA_API_KEY` (free) |
| [Open Food Facts](https://world.openfoodfacts.org) | Packaged and specialty products (miso, tahini, ghee): nutrition, allergens, Nutri-Score | No |

### Planned or optional
- **[RecipeDB](https://cosylab.iiitd.edu.in/recipedb/):** ~118,000 recipes with nutrition. Needs an API key from the CoSyLab team (see section 2.4.7 in the notebook).
- **Google Places API:** store search for the Sourcing Agent (not built yet).

### Licenses
- **CulinaryDB and RecipeDB:** CC BY-NC-SA 3.0, which allows non-commercial use with credit.
- **Open Food Facts:** Open Database License (ODbL).
- **USDA data:** public domain.
- **Food.com, Hugging Face and TheMealDB:** see each source's page for its terms.

This is a non-commercial student project. Check the terms again before any commercial use.

---

## Project Structure

```
The-EverFlavor-AI/
├── notebooks/
│   └── 01_data_acquisition_EverFlavor_V3.ipynb   # Weeks 4-6: data acquisition, preprocessing, EDA, baseline
├── data/
│   ├── raw/          # Original downloads and samples (generated, not committed)
│   ├── interim/      # Combined, cleaned recipe table (generated, not committed)
│   └── processed/    # Train/val/test splits and plots (generated, not committed)
├── src/              # Agent code (to come)
├── docs/
│   └── proposal/     # Capstone proposal slides and Phase 1 document (PDF)
├── config/
│   ├── requirements.txt  # Python libraries for the notebook
│   └── .env.example      # Template for API keys (copy to config/.env, which git ignores)
├── .gitignore
├── LICENSE
└── README.md
```

---

## Current Status

**Done (Weeks 4-6):**
- Data collected from USDA FoodData Central, Open Food Facts, Food.com (Kaggle), Hugging Face, CulinaryDB and TheMealDB.
- Cleaning and feature engineering:
  - cuisine family for every source, using Food.com's cuisine tags
  - restriction flags for pork, alcohol, gluten, dairy, seven common allergens, vegetarian and vegan
  - calories and macronutrients in grams per serving
  - normalized ingredient lists and a complexity score
- All sources combined into one recipe table with duplicates removed, saved as Parquet:
  - **Total:** 292,014 recipes, including 3,180 African, 3,406 Middle Eastern, 20,881 Asian, 48,200 European and 15,722 Latin American.
  - **Restriction flags:** agree with Food.com's own dietary tags 90–98% of the time.
- Stratified train/validation/test split (70/15/15), exploratory analysis, and a rule-based baseline recommender that handles restrictions such as "no pork, no alcohol".

**Known data gaps:**
- Many recipes still have no cuisine label ("Other"), mostly American recipes and Food.com recipes without a cuisine tag.
- Food.com macros are converted from percent of daily value, so they are approximate. CulinaryDB and TheMealDB have no nutrition data.
- Restriction flags come from ingredient keywords (plus Hugging Face health labels), so they are approximate.

**Next:** Week 7 model development, then the CrewAI agents, Google Places integration, and the Gradio interface.

---

## Running the Notebook

`notebooks/01_data_acquisition_EverFlavor_V3.ipynb` runs in Google Colab, VS Code, and Antigravity. Its setup cell (section 2.3) detects the environment, moves to the project folder, and loads API keys from the right place.

Running all cells in order does everything: Week 4 downloads all six sources, Week 5 cleans and combines them, and Week 6 analyzes them. The only key needed is `USDA_API_KEY`.

### Google Colab

1. Open the notebook in Colab.
2. Click the key icon in the left sidebar and add a secret named `USDA_API_KEY` ([get a free key](https://fdc.nal.usda.gov/api-guide.html)). Switch on **Notebook access**.
3. Run all cells. Colab clears `data/` when its session ends, so a new session downloads the data again.

### VS Code or Antigravity

1. Install the **Python** and **Jupyter** extensions.
2. In a terminal in the project folder, run `pip install -r config/requirements.txt`.
3. Copy `config/.env.example` to `config/.env` and fill in `USDA_API_KEY`. Git ignores `.env`, so your keys are never pushed.
4. Open the notebook, pick the Python interpreter you installed into as the kernel, and run all cells.

After a kernel restart, run the cells in sections 2.2 and 2.3 again before any later section.

### Output files

Generated data files in `data/` are not committed; the notebook recreates them. The main outputs are Parquet files, a compressed format that a text editor cannot open:
- `data/interim/recipes_all.parquet`
- `data/processed/recipes_train.parquet`, `recipes_val.parquet` and `recipes_test.parquet`

To look at one, either:
- load it in a notebook with `pd.read_parquet("data/interim/recipes_all.parquet").head()`, or
- install the **Data Wrangler** extension in VS Code.

---
