# Dish quality (2026-11-23)

How complete each of our 3,201 dishes is, not how many there are. The completeness score (0-100) weighs: image 20 (by its level in `image_coverage_report.md`), story 15, family 10, country of origin 10, region 10, fun facts 10, versions 10, related dishes 10, a recipe 5. **rich** = 70 or more, **fair** = 40 to 69, **thin** = under 40. Per dish: `data/knowledge/quality/dish_quality.json`.

**510 rich (15%), 1,378 fair (40%), 1,534 thin (45%).** Average 43 of 100.

## The parts, and what is missing

Twelve parts, each from a source we already use (the score is built from most of them and the region):

| Part | Dishes with it | Missing | What fills it |
|---|---:|---:|---:|
| a summary from its Wikipedia article | 3,421 (100%) | 1 | scripts/knowledge/fetch_knowledge.py |
| its own Wikipedia article to read more | 3,422 (100%) | 0 | fetch_knowledge.py (learn_more 'quick') |
| a country of origin on Wikidata (P495) | 2,704 (79%) | 718 | Wikidata itself: nothing to fill on our side |
| its ingredients on Wikidata (P186, made from) | 2,136 (62%) | 1,286 | Wikidata itself |
| a dish family (notebook 15) | 2,624 (77%) | 798 | notebook 15, when Wikidata files it under one |
| a related dish or version in EverFlavor | 1,159 (34%) | 2,263 | the Food Graph (comes with family and versions) |
| at least one recipe | 1,571 (46%) | 1,851 | a licensed recipe source; never written |
| a real photo of it (its recipe, the dish or a version) | 1,158 (34%) | 2,264 | scripts/dish_photos/ (image_coverage_report.md) |
| fun-fact sentences from its Wikipedia intro | 1,972 (58%) | 1,450 | fetch_knowledge.py |
| story sentences (history, origin, culture) | 1,632 (48%) | 1,790 | fetch_knowledge.py --stories |
| map places in the pilot area for its country | 2,478 (72%) | 944 | stores.COUNTRY_CUISINES and the places table |
| how to say it | 33 (1%) | 3,389 | data/reference/dish_pronunciation.csv (a person adds it) |

## By country (20 with the most dishes)

| Country | Dishes | Average score | Rich | Thin |
|---|---:|---:|---:|---:|
| United States | 367 | 59.7 | 39% | 17% |
| Italy | 327 | 41.4 | 15% | 51% |
| Indonesia | 248 | 36.3 | 3% | 52% |
| China | 179 | 50.3 | 17% | 28% |
| Mexico | 112 | 46.9 | 19% | 37% |
| Japan | 108 | 49.2 | 19% | 31% |
| India | 103 | 46.4 | 20% | 39% |
| Canada | 89 | 55.2 | 29% | 25% |
| Germany | 88 | 40.1 | 9% | 50% |
| Greece | 88 | 43.7 | 16% | 48% |
| France | 87 | 48.8 | 23% | 32% |
| Philippines | 87 | 37.8 | 8% | 53% |
| South Korea | 79 | 39.8 | 5% | 51% |
| Thailand | 77 | 41.0 | 6% | 47% |
| Portugal | 72 | 29.7 | 1% | 81% |
| Vietnam | 72 | 35.7 | 8% | 56% |
| United Kingdom | 69 | 60.1 | 43% | 20% |
| Poland | 66 | 42.5 | 15% | 48% |
| Australia | 60 | 50.1 | 22% | 32% |
| Turkey | 57 | 37.2 | 9% | 56% |

## Remediation plan

Most points can come from sources and scripts we already have, in this order of value for effort:

1. **how to say it** for 3,389 dishes: data/reference/dish_pronunciation.csv (a person adds it).
2. **a real photo of it (its recipe, the dish or a version)** for 2,264 dishes: scripts/dish_photos/ (image_coverage_report.md).
3. **a related dish or version in EverFlavor** for 2,263 dishes: the Food Graph (comes with family and versions).
4. **at least one recipe** for 1,851 dishes: a licensed recipe source; never written.
5. **story sentences (history, origin, culture)** for 1,790 dishes: fetch_knowledge.py --stories.
6. **fun-fact sentences from its Wikipedia intro** for 1,450 dishes: fetch_knowledge.py.
7. **its ingredients on Wikidata (P186, made from)** for 1,286 dishes: Wikidata itself.
8. **map places in the pilot area for its country** for 944 dishes: stores.COUNTRY_CUISINES and the places table.

Origin and ingredients live on Wikidata; where Wikidata has none, the dish stays without them rather than getting a guess. Recipes are never written: a dish without one stays knowledge-only.
