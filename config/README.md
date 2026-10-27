# Config

Settings and install lists. Nothing here needs editing for a normal run except your own `.env`.

| File | What it is | Install / use |
|---|---|---|
| `requirements.lock` | **Every library at a tested version** (the three lists below plus the photo tools), for Windows, Mac and Linux | `uv pip sync config/requirements.lock` in an environment made with `uv venv --python 3.12` |
| `requirements.txt` | Libraries for the notebooks and the shared code | `uv pip install -r config/requirements.txt` or `pip install ...` (Colab installs its own) |
| `requirements-dev.txt` | Checking tools: pytest, ruff, mypy, pymarkdown | `uv pip install -r config/requirements-dev.txt` (CI does this) |
| `requirements-app.txt` | The starter app (Streamlit), CrewAI for the meal planner, and Ollama setup notes (models: `llama3.2` for chat, `granite4.1:3b` for the planner) | `uv pip install -r config/requirements-app.txt` |
| `requirements-photos.txt` | The recipe-photo tools: PyTorch and open_clip (the photo check) | `uv pip install -r config/requirements-photos.txt` |
| `.env.example` | Template for API keys | Copy to `config/.env` and fill in |
| `.env` | **Your** keys (not on GitHub: git ignores it) | Created by you; never commit or share it |
| `mypy.ini` | Type-checker settings | `python -m mypy --config-file config/mypy.ini` |
| `pymarkdown.json` | Markdown checker settings | `pymarkdown -c config/pymarkdown.json scan ...` |

**uv** ([docs](https://docs.astral.sh/uv/)) is the main installer: it reads the same requirement files as pip, about
10-100 times faster, with one download cache for every environment. The `.txt` files stay the source of truth (Colab
and pip use them); after changing one, refresh the lock with
`uv pip compile config/requirements-app.txt config/requirements-dev.txt config/requirements-photos.txt --universal --python-version 3.12 -o config/requirements.lock`.

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
