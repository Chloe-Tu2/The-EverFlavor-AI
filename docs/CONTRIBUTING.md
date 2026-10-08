# Working Rules

The rules every change to EverFlavor AI follows, for team members and AI assistants alike. They exist so the data stays safe to filter on, the notebooks keep running everywhere, and anyone can see why a decision was made.

## 1. Runs everywhere

- The notebooks and `src/everflavor/` must run **unchanged** in Google Colab, VS Code and Antigravity. No local paths, no tools only one environment has. The checking tools (pytest, Ruff, mypy, PyMarkdown) are for local editing and GitHub only.
- Before a change to the data pipeline is pushed, notebook 01 (and any later notebook it feeds) is run from top to bottom in two environments: the local one and one with Colab's library versions. Their results must match.
- Use Python 3.12, the version Colab runs.

## 2. Checks before every push

Run these from the project folder; all must pass (GitHub runs the same checks on every push, see `.github/workflows/checks.yml`):

```bash
python -m pytest tests                                    # tests and security checks
python -m ruff check src tests notebooks app               # mistakes and style
python -m mypy --config-file config/mypy.ini              # type hints
python -m pymarkdown --config config/pymarkdown.json scan README.md docs   # Markdown
```

A push goes ahead only when the commands themselves report success, not when the last line of their output looks fine.

## 3. Secrets

- API keys live only in Colab Secrets or `config/.env`, which git ignores. Never in a notebook, a commit, a chat message or a log.
- Code never prints a key. The security tests fail if a key from `config/.env` appears in any tracked file, notebook outputs included.
- A request that carries a key reports only the error type and status code. `raise_for_status()` and connection errors put the full URL (key included) in their message, so catch them and raise a short error `from None` (see `sources.usda_search`). Where an API allows it, send the key in a header instead of the URL.
- Notebook outputs must not show local paths (`C:\Users\<name>`); remove them before committing.

## 4. Safety rules for flags and diets

- **Flags only add cautions.** A new rule, a ready-made ingredient or a model may set a flag; nothing clears one that the keyword rules set.
- **The safety filter re-checks** every recommendation against the ingredients and name, independent of the stored flags.
- **"-friendly" is never "certified".** Ingredients cannot show how meat was slaughtered or whether a kitchen is certified.
- **Medical profiles are screens, not advice.** They list ingredients to discuss with a doctor or dietitian.
- **Anything about a store or restaurant** (its oil, its stock, its halal status) is "unverified" unless the place publishes it.
- Every new keyword comes with a test that shows a match and a look-alike that must not match (for example "eggplant" is not egg).

## 5. Decisions are recorded, with who made them

- A definition that is a matter of judgment (does falafel count as fava beans?) gets a row in `docs/flag_review/flag_policies.csv` with the reason and a source. It stays `proposed` until a named person approves it.
- Hidden-allergen evidence and its decisions live in `docs/flag_review/compound_ingredients_review.csv`; the code (`COMPOUND_INGREDIENTS`) must match the approved rows, and notebook 01 (5.13.2) checks that it does.
- Work done by an AI assistant is recorded with its name. It never counts as the human sign-off (policy P22).

## 6. Data and sources

- `data/` is never committed: the notebooks recreate it.
- A new source is added to `docs/sources.md` (URL, license, access method) **before** its first download, and only if its license allows our use.
- Downloads are cached and reused; `REFRESH_DOWNLOADS = True` fetches everything again. Paced APIs (Open Food Facts) keep their rate limits.

## 7. Code

- Reusable code goes in `src/everflavor/`, never copied between notebooks. The conventions are at the top of `src/everflavor/__init__.py`: type hints, docstrings with Args and Returns, functions that return a new table instead of changing their input, and clear errors for wrong input.
- Rule tables (keywords, maps, limits) are UPPER_CASE constants, defined once and used everywhere.

## 8. Numbers and documentation

- Numbers in the README and the docs come from the latest full run. After a rerun, update them in the same commit as the notebooks.
- Plain language, no emojis in the README, and every chart saved to `data/processed/figures/`.
- A data change updates `docs/data_dictionary.md`; a new limitation goes into the README's known gaps and `docs/datasheet.md`.

## 9. Commits

- One topic per commit, with a message that says what changed and why.
- Push to `main` only finished, checked work. Unfinished ideas go into a planning notebook or the notes, not half into the code.
