# Config

Settings and install lists. Nothing here needs editing for a normal run except your own `.env`.

| File | What it is | Install / use |
|---|---|---|
| `requirements.txt` | Libraries for the notebooks and the shared code | `pip install -r config/requirements.txt` (Colab installs its own) |
| `requirements-dev.txt` | Checking tools: pytest, ruff, mypy, pymarkdown | `pip install -r config/requirements-dev.txt` |
| `requirements-app.txt` | The starter app (Streamlit), CrewAI for the meal planner, and Ollama setup notes | `pip install -r config/requirements-app.txt` |
| `.env.example` | Template for API keys | Copy to `config/.env` and fill in |
| `.env` | **Your** keys (not on GitHub: git ignores it) | Created by you; never commit or share it |
| `mypy.ini` | Type-checker settings | `python -m mypy --config-file config/mypy.ini` |
| `pymarkdown.json` | Markdown checker settings | `pymarkdown -c config/pymarkdown.json scan ...` |

Ruff and the spell checker read `ruff.toml` and `cspell.json` in the project folder, where their VS Code
extensions find them.

## Keys

| Key | Needed for | Get it |
|---|---|---|
| `USDA_API_KEY` | Notebook 01 (nutrition) | <https://fdc.nal.usda.gov/api-key-signup> |
| `GOOGLE_PLACES_API_KEY` | Optional: live store details (notebook 03) | Google Cloud console |
| `GROQ_API_KEY` | Later: hosted model for the agents | <https://console.groq.com/keys> |
| `OLLAMA_HOST` | Optional: only if Ollama is not at `localhost:11434` | No key needed |

In Colab, put keys in **Secrets** (the key icon) instead of `.env`.
