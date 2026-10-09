# Tests

Each file pins down what one part of [src/everflavor](../src/everflavor/README.md) promises. They use small
made-up tables and fake network answers, so they need **no data, no keys, no internet and no Ollama**, and
run in a few seconds. GitHub runs them on every push.

```bash
python -m pytest tests                     # all of them
python -m pytest tests/test_safety.py      # one file
python tests/test_safety.py                # also works
```

| File | Checks |
|---|---|
| `test_everflavor.py` | Flags, diets, ingredient names: what each shared function promises |
| `test_helpers.py` | Keys, reporting, charts, features, the recommender |
| `test_pipeline.py` | `run_pipeline` end to end on tiny tables shaped like each source |
| `test_sources.py` | Download helpers, with fake network answers |
| `test_matching_and_review.py` | USDA matching and the flag review tools |
| `test_knowledge.py` | Notebook 04's tables, and that every notebook lists all shared modules |
| `test_stores.py` | Notebook 03: places, products, the Google key never shown |
| `test_freshness.py` | Notebook 05: labels, duplicates, split, license check |
| `test_variants.py` | Notebook 06: a variant never keeps or adds a forbidden ingredient |
| `test_nutrition_quality.py` | Notebook 07: Daily Value shares and macro labels |
| `test_calories.py` | Line parsing, portion weights, calories |
| `test_safety.py` | User profile, the gate, same answer as the dataset filter |
| `test_llm.py` | Ollama helpers with fake answers; the model cannot change the profile |
| `test_security.py` | No keys or personal paths in committed files; `.env` stays ignored |

**Adding a test:** put it in the file for that module, name it `test_<what it promises>`, and keep it
small enough to read in one go.
