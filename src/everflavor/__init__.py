"""EverFlavor AI: shared code for the data pipeline notebook and, later, the agents.

Modules:
    checks       input checks with clear error messages
    environment  secrets (Colab Secrets or config/.env) and the download checker
    charts       chart style and helpers
    sources      download helpers for USDA, Open Food Facts, CulinaryDB and TheMealDB
    parsing      lists and labels stored as text
    cuisine      cuisine families and country / region of origin
    ingredients  cleaning and normalizing ingredient names
    flags        restriction flags (keyword rules)
    diets        diet profiles built from the flags
    nutrition    nutrition per serving, plausibility checks, USDA matching
    features     text features shared by the models
    pipeline     cleaning, run_pipeline, combining, splitting, validation
    review       blind hand-check samples for the flags
    recommend    the baseline recommender and its safety filter
    reporting    small table and checklist helpers
    progress     progress bars that work in Colab, VS Code, Antigravity and a terminal
    cooking      cooking methods and cooking fats (notebook 02)
    knowledge    ingredient pairings, substitutions, shelf life and names (notebook 04)
    stores       OpenStreetMap, Google Places and Open Food Facts products (notebook 03)
    freshness    image labels, near-duplicates, split and training (notebook 05)
    variants     halal, vegan, gluten-free ... versions of each dish (notebook 06)
    nutrition_quality  macro labels and nutrient-rich ingredients (notebook 07)
    calories     calorie calculator: ingredient lines -> grams -> USDA calories (Week 7)
    safety       user profile and the safety gate for recipes the agents write
    llm          local models through Ollama (VS Code / Antigravity only, never Colab)
    seasons      meat supply season and pasture season (notebook 08)

Conventions (Google Python Style Guide, PEP 257):
    - Every public function has type hints and a docstring with Args, Returns
      and Raises where they apply.
    - Functions never change the dataframe they are given: they return a new one.
    - Settings (API keys, folders, REFRESH_DOWNLOADS) are passed in as arguments,
      never read from the notebook's variables.
    - Wrong input fails early with a ValueError that names what is missing.
    - Rule tables (keywords, maps, limits) are UPPER_CASE module constants.
    - tests/test_everflavor.py pins down what each function promises.
    - Each module lists its public names in __all__: those are supported for the
      notebook and the agents. Names starting with _ are internal steps of a
      public function and may change without notice.
"""

__version__ = "0.1.0"
