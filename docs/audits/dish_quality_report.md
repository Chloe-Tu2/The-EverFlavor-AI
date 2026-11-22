# Dish quality (2026-11-22)

How complete each of our 3,201 dishes is, not how many there are. The completeness score (0-100) weighs: image 20 (by its level in `dish_image_report.md`), story 15, family 10, country of origin 10, region 10, fun facts 10, versions 10, related dishes 10, a recipe 5. **rich** = 70 or more, **fair** = 40 to 69, **thin** = under 40. Per dish: `data/knowledge/quality/dish_quality.json`.

**508 rich (16%), 1,331 fair (42%), 1,362 thin (43%).** Average 44 of 100.

## The parts, and what is missing

Twelve parts, each from a source we already use (the score is built from most of them and the region):

| Part | Dishes with it | Missing | What fills it |
|---|---:|---:|---:|
| a summary from its Wikipedia article | 3,201 (100%) | 0 | scripts/knowledge/fetch_knowledge.py |
| its own Wikipedia article to read more | 3,201 (100%) | 0 | fetch_knowledge.py (learn_more 'quick') |
| a country of origin on Wikidata (P495) | 2,537 (79%) | 664 | Wikidata itself: nothing to fill on our side |
| its ingredients on Wikidata (P186, made from) | 2,031 (63%) | 1,170 | Wikidata itself |
| a dish family (notebook 15) | 2,507 (78%) | 694 | notebook 15, when Wikidata files it under one |
| a related dish or version in EverFlavor | 1,130 (35%) | 2,071 | the Food Graph (comes with family and versions) |
| at least one recipe | 1,522 (48%) | 1,679 | a licensed recipe source; never written |
| a real photo of it (its recipe, the dish or a version) | 1,130 (35%) | 2,071 | scripts/dish_photos/ (dish_image_report.md) |
| fun-fact sentences from its Wikipedia intro | 1,848 (58%) | 1,353 | fetch_knowledge.py |
| story sentences (history, origin, culture) | 1,587 (50%) | 1,614 | fetch_knowledge.py --stories |
| map places in the pilot area for its country | 2,402 (75%) | 799 | stores.COUNTRY_CUISINES and the places table |
| how to say it | 33 (1%) | 3,168 | data/reference/dish_pronunciation.csv (a person adds it) |

## By country (20 with the most dishes)

| Country | Dishes | Average score | Rich | Thin |
|---|---:|---:|---:|---:|
| United States | 367 | 59.7 | 39% | 17% |
| Italy | 326 | 41.4 | 15% | 52% |
| Indonesia | 248 | 36.2 | 3% | 53% |
| China | 178 | 50.3 | 17% | 29% |
| Mexico | 110 | 47.0 | 19% | 37% |
| Japan | 108 | 49.2 | 19% | 31% |
| India | 102 | 46.5 | 21% | 38% |
| Canada | 88 | 55.1 | 30% | 25% |
| Greece | 88 | 43.4 | 16% | 49% |
| Germany | 87 | 40.5 | 9% | 49% |
| Philippines | 86 | 38.0 | 8% | 52% |
| France | 84 | 48.2 | 23% | 33% |
| South Korea | 79 | 39.8 | 5% | 51% |
| Thailand | 77 | 41.5 | 8% | 45% |
| Portugal | 72 | 29.7 | 1% | 81% |
| Vietnam | 71 | 36.1 | 8% | 55% |
| United Kingdom | 67 | 61.2 | 45% | 21% |
| Poland | 65 | 42.4 | 15% | 49% |
| Australia | 58 | 50.6 | 22% | 29% |
| Turkey | 57 | 36.8 | 9% | 58% |

## Remediation plan

Most points can come from sources and scripts we already have, in this order of value for effort:

1. **how to say it** for 3,168 dishes: data/reference/dish_pronunciation.csv (a person adds it).
2. **a related dish or version in EverFlavor** for 2,071 dishes: the Food Graph (comes with family and versions).
3. **a real photo of it (its recipe, the dish or a version)** for 2,071 dishes: scripts/dish_photos/ (dish_image_report.md).
4. **at least one recipe** for 1,679 dishes: a licensed recipe source; never written.
5. **story sentences (history, origin, culture)** for 1,614 dishes: fetch_knowledge.py --stories.
6. **fun-fact sentences from its Wikipedia intro** for 1,353 dishes: fetch_knowledge.py.
7. **its ingredients on Wikidata (P186, made from)** for 1,170 dishes: Wikidata itself.
8. **map places in the pilot area for its country** for 799 dishes: stores.COUNTRY_CUISINES and the places table.

Origin and ingredients live on Wikidata; where Wikidata has none, the dish stays without them rather than getting a guess. Recipes are never written: a dish without one stays knowledge-only.
