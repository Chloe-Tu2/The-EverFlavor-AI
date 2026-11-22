# Dish knowledge (the waiter's notebook)

Facts the waiter may tell, collected from open sources, never invented (for the waiter, planned for 0.6.3).

- `dishes.jsonl`: one dish or food per line (2026-11-11: 4,885; 3,201 dishes, the rest foods and drinks; 2,806 with
  fun-fact candidates and 2,415 with story sentences; 11,044 facts shown first and 9,035 "more"), built by
  `scripts/knowledge/fetch_knowledge.py`. It starts with what
  the app shows: the 54 countries in its Country list and its 22 regions (other countries later).
- `dish_families.json`: which dishes belong together (notebook 15, Wikidata "subclass of", CC0): families,
  categories by main ingredient and groupings, each with its members (QID, name, country, whether EverFlavor has
  it, its English Wikipedia article). The Food Graph (`everflavor.domain.FoodGraph`) and the dish page read it.
- `dish_recipe_counts.json`: how many of our recipes the app links to each dish (`waiter.Knowledge.find` on the
  cleaned dish name), by source and by how the name matched, and the dishes with no recipe; counts only, from
  `scripts/knowledge/recipe_dish_links.py` (2026-11-21: 80,741 of 291,755 recipes; see
  `docs/audits/recipe_dish_linking.md`).
- `countries.json`: the world's countries and territories (Wikidata, CC0: ISO code, continent, population), from
  `scripts/knowledge/fetch_countries.py`, for the coverage audit.
- `coverage/`: the coverage audit (`scripts/knowledge/coverage_audit.py`; reports in `docs/audits/`): coverage by
  country and culinary region, the families and variants we lack, the missing countries and regions, the expansion
  backlog (every Wikidata family member we do not have, with its sources and approval state: ready, needs review,
  blocked) and `next_500.json`. `wikidata_types.json` (from `fetch_backlog_types.py`) says which candidates are
  brands or events, which are blocked. Nothing in it is shown by the app.
- Regions: China by region and province (16 cuisine pages: the Eight Great Traditions, Beijing, Shanghai, Hong
  Kong, Yunnan, Xinjiang, the Northeast, Hakka, Teochew; 282 Chinese entries); Mexico by state (its region pages
  are prose, so a dish gets the state its own intro or Wikidata origin names first: 45 dishes, such as Al pastor in
  Puebla and Torta ahogada in Jalisco).
- Fields: `name`, `country`, `region` (when a region page lists it), `kind` (dish, or food or drink), `sections`
  and `regions` (headings and region columns of the Wikipedia list it came from), `summary`,
  `fun_fact_candidates`, Wikidata facts (`origin`, `inception`, `parts`, `made_from`, `named_after`, `heritage`,
  `inventor`, `created_in`, `based_on`, `not_to_confuse`),
  `learn_more`, `sources`, `reviewed`.
- `learn_more`: where to read more, by interest level, so the waiter offers what fits the user's settings:
  `quick` (the dish's Wikipedia article), `more` (its cuisine or region page: history and related dishes),
  `deep` (books on Open Library, UNESCO when the dish is listed there, all recorded facts on Wikidata).
- `fun_fact_candidates` are sentences copied from Wikipedia intros that look like facts (dates, names, stories);
  `story_candidates` the same from each article's History, Origin, Etymology and Culture sections (`--stories`).
- `dishes/`: the readable knowledge notebook, one page per country (notebook 11). Its facts are sorted by
  topic (inspiration, origin, culture, history, about): three from different topics come first, the rest are
  "more fun facts" for a user who asks for more, before the links. Wikidata facts become short lines ("comes
  from Mexico", "named after ...") credited to Wikidata.
  They are **not reviewed** (`reviewed: false`): they get tidied in the knowledge notebook before the app shows
  them, and each keeps its source. Tidying never shows a fact that needs a missing sentence ("She has operated
  the restaurant ...") or is unsuitable (a murder film), and ranks facts that may not be about the dish last.
- `review/focus_review.csv`: the review sheet for 65 of the focus areas' best-documented dishes (USA, Mexico,
  China, Middle East, Africa; 260 rows: summary and the first three facts), from
  `scripts/knowledge/review_sheet.py`. `warnings` are automatic, `pre_review` is Claude's reading (2026-11-11:
  6 drops and 5 fixes suggested, 10 to check), and `verdict` / `reviewer` / `note` are for a person: `keep`,
  `fix` or `drop`. Walter never says a fact marked `drop`. Rerunning the script keeps what people wrote.
- `review/origin_elsewhere.csv`: dishes a country's Wikipedia list names but whose Wikidata origin is elsewhere
  (130, such as Baguette under the United States): their country needs a person's check.

## Licence and credit

- Wikipedia text is CC BY-SA 4.0: whoever shows it credits "Wikipedia contributors" with the article link (each
  row's `sources`), and changed text stays under CC BY-SA. Wikidata facts are CC0.
- Rerun the script to refresh; its raw answers are cached in `data/raw/knowledge_cache/` (not in git).
