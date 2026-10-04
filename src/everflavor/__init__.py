"""EverFlavor AI: shared code for the data pipeline notebook and, later, the agents.

Modules:
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
"""

__version__ = "0.1.0"
