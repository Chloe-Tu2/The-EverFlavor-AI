# CLAUDE.md

Guidance for Claude Code (and anyone new) working in this repository. The README has the full picture; these
are the rules that must not be broken.

## What this is

EverFlavor AI (Team EverGlow, ITAI 2277 Capstone): recipe recommendations that respect allergies, religious and
ethical diets and calorie goals. Data pipelines in `notebooks/` (01-09), the shared code in `src/everflavor/`,
the Streamlit front end in `app/` (the pixel-art kitchen; design notes in `design/`), tests in `tests/`.

## Environments and commands

- Everything must run unchanged in **Google Colab, VS Code and Antigravity** (the notebooks' setup cell finds the
  project folder and downloads missing `src/everflavor` files in Colab).
- Run the app: `python -m streamlit run app/app.py` (port 8501).
- Before every push, run the same checks as CI (`.github/workflows/checks.yml`):
  `python -m pytest -q`, `ruff check src tests notebooks`, `mypy --config-file config/mypy.ini` (no path), and
  `python -m pymarkdown --config config/pymarkdown.json scan README.md docs app/README.md config/README.md data/README.md notebooks/README.md src/everflavor/README.md tests/README.md`.
  Do not pipe a check into `tail` without keeping its exit code.
- Do not edit `src/` while a notebook run is in progress (the kernel imports it); run notebooks cell by cell.

## Rules

- **Secrets:** API keys live only in `config/.env` (git-ignored) or Colab Secrets. Never commit them, not even
  encrypted. `.claude/hooks/guard_secrets.py` and the git pre-commit hook (`precommit_secrets.py --install`)
  enforce it.
- **User data** (profiles, chat history, audit logs; `data/user/`, `logs/`) is never committed, and the audit log
  never records the user's words (`docs/ethics_privacy.md`).
- **Safety decisions come from the back end** (`src/everflavor`: flags, safety gate, recommend). The app and the
  AI models only show or explain them; never filter or "fix" safety in the page or in a prompt.
- **Flags only ever add cautions.** Diet labels say "halal-friendly ingredients", never "halal"; medical profiles are
  screens, not advice.
- **Every judgment call is a recorded policy** with who decided it; README numbers come from the latest full run.
- Local AI runs through Ollama (`src/everflavor/llm.py`, default `llama3.2`); in Colab everything falls back to rules.

## Conventions

- Plain, short sentences in docs and notebook text; numbers in docs must match the code or the latest run.
- Commit messages: a one-line summary of what changed and why, then details; end with the co-author line.
- Push verified work only (all checks green); front-end concepts go on a branch first.
