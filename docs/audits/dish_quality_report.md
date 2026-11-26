# Dish quality (2026-11-25)

How complete each of our 3,201 dishes is, not how many there are. The completeness score (0-100) weighs: image 20 (by its level in `image_coverage_report.md`), story 15, family 10, country of origin 10, region 10, fun facts 10, versions 10, related dishes 10, a recipe 5. **rich** = 70 or more, **fair** = 40 to 69, **thin** = under 40. Per dish: `data/knowledge/quality/dish_quality.json`.

**531 rich (14%), 1,490 fair (39%), 1,847 thin (48%).** Average 42 of 100.

## The parts, and what is missing

Twelve parts, each from a source we already use (the score is built from most of them and the region):

| Part | Dishes with it | Missing | What fills it |
|---|---:|---:|---:|
| a summary from its Wikipedia article | 3,867 (100%) | 1 | scripts/knowledge/fetch_knowledge.py |
| its own Wikipedia article to read more | 3,868 (100%) | 0 | fetch_knowledge.py (learn_more 'quick') |
| a country of origin on Wikidata (P495) | 3,032 (78%) | 836 | Wikidata itself: nothing to fill on our side |
| its ingredients on Wikidata (P186, made from) | 2,371 (61%) | 1,497 | Wikidata itself |
| a dish family (notebook 15) | 2,922 (76%) | 946 | notebook 15, when Wikidata files it under one |
| a related dish or version in EverFlavor | 1,266 (33%) | 2,602 | the Food Graph (comes with family and versions) |
| at least one recipe | 1,649 (43%) | 2,219 | a licensed recipe source; never written |
| a real photo of it (its recipe, the dish or a version) | 1,204 (31%) | 2,664 | scripts/dish_photos/ (image_coverage_report.md) |
| fun-fact sentences from its Wikipedia intro | 2,234 (58%) | 1,634 | fetch_knowledge.py |
| story sentences (history, origin, culture) | 1,780 (46%) | 2,088 | fetch_knowledge.py --stories |
| map places in the pilot area for its country | 2,577 (67%) | 1,291 | stores.COUNTRY_CUISINES and the places table |
| how to say it | 33 (1%) | 3,835 | data/reference/dish_pronunciation.csv (a person adds it) |

## By country (20 with the most dishes)

| Country | Dishes | Average score | Rich | Thin |
|---|---:|---:|---:|---:|
| United States | 366 | 59.8 | 39% | 17% |
| Italy | 329 | 41.7 | 16% | 51% |
| Indonesia | 249 | 36.4 | 4% | 52% |
| China | 181 | 50.5 | 18% | 28% |
| Mexico | 112 | 47.0 | 19% | 37% |
| Japan | 109 | 49.3 | 19% | 30% |
| India | 105 | 46.9 | 21% | 38% |
| Canada | 89 | 55.2 | 29% | 25% |
| France | 89 | 49.5 | 25% | 31% |
| Germany | 89 | 40.1 | 9% | 51% |
| Greece | 88 | 43.9 | 16% | 48% |
| Philippines | 87 | 37.8 | 8% | 53% |
| South Korea | 79 | 39.8 | 5% | 51% |
| Thailand | 77 | 41.0 | 6% | 47% |
| Portugal | 72 | 29.7 | 1% | 81% |
| Vietnam | 72 | 35.7 | 8% | 56% |
| United Kingdom | 69 | 60.3 | 43% | 20% |
| Poland | 68 | 43.7 | 16% | 46% |
| Turkey | 65 | 37.0 | 11% | 57% |
| Australia | 60 | 50.1 | 22% | 32% |

## Remediation plan

Most points can come from sources and scripts we already have, in this order of value for effort:

1. **how to say it** for 3,835 dishes: data/reference/dish_pronunciation.csv (a person adds it).
2. **a real photo of it (its recipe, the dish or a version)** for 2,664 dishes: scripts/dish_photos/ (image_coverage_report.md).
3. **a related dish or version in EverFlavor** for 2,602 dishes: the Food Graph (comes with family and versions).
4. **at least one recipe** for 2,219 dishes: a licensed recipe source; never written.
5. **story sentences (history, origin, culture)** for 2,088 dishes: fetch_knowledge.py --stories.
6. **fun-fact sentences from its Wikipedia intro** for 1,634 dishes: fetch_knowledge.py.
7. **its ingredients on Wikidata (P186, made from)** for 1,497 dishes: Wikidata itself.
8. **map places in the pilot area for its country** for 1,291 dishes: stores.COUNTRY_CUISINES and the places table.

Origin and ingredients live on Wikidata; where Wikidata has none, the dish stays without them rather than getting a guess. Recipes are never written: a dish without one stays knowledge-only.
