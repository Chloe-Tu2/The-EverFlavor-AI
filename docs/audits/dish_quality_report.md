# Dish quality (2026-11-22)

How complete each of our 3,201 dishes is, not how many there are. The completeness score (0-100) weighs: image 20 (by its level in `image_coverage_report.md`), story 15, family 10, country of origin 10, region 10, fun facts 10, versions 10, related dishes 10, a recipe 5. **rich** = 70 or more, **fair** = 40 to 69, **thin** = under 40. Per dish: `data/knowledge/quality/dish_quality.json`.

**506 rich (15%), 1,356 fair (40%), 1,509 thin (45%).** Average 43 of 100.

## The parts, and what is missing

Twelve parts, each from a source we already use (the score is built from most of them and the region):

| Part | Dishes with it | Missing | What fills it |
|---|---:|---:|---:|
| a summary from its Wikipedia article | 3,370 (100%) | 1 | scripts/knowledge/fetch_knowledge.py |
| its own Wikipedia article to read more | 3,371 (100%) | 0 | fetch_knowledge.py (learn_more 'quick') |
| a country of origin on Wikidata (P495) | 2,674 (79%) | 697 | Wikidata itself: nothing to fill on our side |
| its ingredients on Wikidata (P186, made from) | 2,115 (63%) | 1,256 | Wikidata itself |
| a dish family (notebook 15) | 2,507 (74%) | 864 | notebook 15, when Wikidata files it under one |
| a related dish or version in EverFlavor | 1,144 (34%) | 2,227 | the Food Graph (comes with family and versions) |
| at least one recipe | 1,559 (46%) | 1,812 | a licensed recipe source; never written |
| a real photo of it (its recipe, the dish or a version) | 1,151 (34%) | 2,220 | scripts/dish_photos/ (image_coverage_report.md) |
| fun-fact sentences from its Wikipedia intro | 1,941 (58%) | 1,430 | fetch_knowledge.py |
| story sentences (history, origin, culture) | 1,622 (48%) | 1,749 | fetch_knowledge.py --stories |
| map places in the pilot area for its country | 2,474 (73%) | 897 | stores.COUNTRY_CUISINES and the places table |
| how to say it | 33 (1%) | 3,338 | data/reference/dish_pronunciation.csv (a person adds it) |

## By country (20 with the most dishes)

| Country | Dishes | Average score | Rich | Thin |
|---|---:|---:|---:|---:|
| United States | 366 | 59.5 | 39% | 17% |
| Italy | 327 | 41.3 | 15% | 52% |
| Indonesia | 248 | 36.2 | 3% | 53% |
| China | 179 | 50.3 | 17% | 28% |
| Mexico | 113 | 47.2 | 19% | 38% |
| Japan | 108 | 49.2 | 19% | 31% |
| India | 103 | 46.3 | 20% | 39% |
| Canada | 88 | 55.1 | 30% | 25% |
| Germany | 88 | 40.0 | 9% | 50% |
| Greece | 88 | 43.4 | 16% | 49% |
| France | 87 | 48.6 | 23% | 32% |
| Philippines | 87 | 37.6 | 8% | 53% |
| South Korea | 79 | 39.8 | 5% | 51% |
| Thailand | 77 | 41.0 | 6% | 47% |
| Portugal | 72 | 29.7 | 1% | 81% |
| Vietnam | 72 | 35.6 | 8% | 56% |
| United Kingdom | 69 | 60.0 | 42% | 20% |
| Poland | 66 | 42.4 | 15% | 48% |
| Australia | 59 | 49.8 | 22% | 32% |
| Turkey | 57 | 36.8 | 9% | 58% |

## Remediation plan

Most points can come from sources and scripts we already have, in this order of value for effort:

1. **how to say it** for 3,338 dishes: data/reference/dish_pronunciation.csv (a person adds it).
2. **a related dish or version in EverFlavor** for 2,227 dishes: the Food Graph (comes with family and versions).
3. **a real photo of it (its recipe, the dish or a version)** for 2,220 dishes: scripts/dish_photos/ (image_coverage_report.md).
4. **at least one recipe** for 1,812 dishes: a licensed recipe source; never written.
5. **story sentences (history, origin, culture)** for 1,749 dishes: fetch_knowledge.py --stories.
6. **fun-fact sentences from its Wikipedia intro** for 1,430 dishes: fetch_knowledge.py.
7. **its ingredients on Wikidata (P186, made from)** for 1,256 dishes: Wikidata itself.
8. **map places in the pilot area for its country** for 897 dishes: stores.COUNTRY_CUISINES and the places table.

Origin and ingredients live on Wikidata; where Wikidata has none, the dish stays without them rather than getting a guess. Recipes are never written: a dish without one stays knowledge-only.
