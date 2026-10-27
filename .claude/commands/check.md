---
description: Run the four CI checks (pytest, ruff, mypy, pymarkdown) the way GitHub runs them, and report pass or fail
---

Run the same checks as `.github/workflows/checks.yml`, from the project folder, with the project's Python (the one
that has the project's libraries; on the team's own PCs, the environment built from `config/requirements.lock`).
Run all four even if one fails, and keep each exit code (never pipe a check into `tail` or `head` without it):

1. `python -m pytest -q`
2. `python -m ruff check src tests notebooks`
3. `python -m mypy --config-file config/mypy.ini` (no path: the files are listed in the config)
4. `python -m pymarkdown --config config/pymarkdown.json scan README.md docs app/README.md config/README.md data/README.md notebooks/README.md src/everflavor/README.md tests/README.md`

Report one line per check: pass, or fail with the failing names (test names, ruff codes and lines, mypy errors,
markdown rules and lines), only the lines that matter. Do not fix anything unless asked; if all four pass, say so
in one line. Do not run this while a notebook run is in progress if a check imports `src/` that is being changed.
