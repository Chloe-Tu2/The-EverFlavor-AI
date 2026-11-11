# Dish knowledge (the waiter's notebook)

Facts the waiter may tell, collected from open sources, never invented (for the waiter, planned for 0.6.3).

- `dishes.jsonl`: one dish or food per line (2026-11-10: 4,827; 3,100+ dishes, the rest foods and drinks; 2,734 with
  fun-fact candidates), built by `scripts/knowledge/fetch_knowledge.py`. It starts with what
  the app shows: the 54 countries in its Country list and its 22 regions (other countries later).
- Fields: `name`, `country`, `region` (when a region page lists it), `kind` (dish, or food or drink), `sections`
  and `regions` (headings and region columns of the Wikipedia list it came from), `summary`,
  `fun_fact_candidates`, Wikidata facts (`origin`, `inception`, `parts`, `made_from`, `named_after`, `heritage`),
  `learn_more`, `sources`, `reviewed`.
- `learn_more`: where to read more, by interest level, so the waiter offers what fits the user's settings:
  `quick` (the dish's Wikipedia article), `more` (its cuisine or region page: history and related dishes),
  `deep` (books on Open Library, UNESCO when the dish is listed there, all recorded facts on Wikidata).
- `fun_fact_candidates` are sentences copied from Wikipedia intros that look like facts (dates, names, stories).
  They are **not reviewed** (`reviewed: false`): they get tidied in the knowledge notebook before the app shows
  them, and each keeps its source.

## Licence and credit

- Wikipedia text is CC BY-SA 4.0: whoever shows it credits "Wikipedia contributors" with the article link (each
  row's `sources`), and changed text stays under CC BY-SA. Wikidata facts are CC0.
- Rerun the script to refresh; its raw answers are cached in `data/raw/knowledge_cache/` (not in git).
