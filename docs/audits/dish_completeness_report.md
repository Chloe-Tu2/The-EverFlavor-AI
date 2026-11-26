# Dish completeness (2026-11-25)

How complete our 3,868 dishes are, by the completeness score (0-100, the team's weights; full detail per part in [dish_quality_report.md](dish_quality_report.md)), and what would move them up. Nothing here changes a dish: the second column is a projection.

| Tier | Today | With the approved images | Change |
|---|---:|---:|---:|
| rich (from 70) | 531 (14%) | 681 (18%) | +150 |
| fair (from 40) | 1,490 (39%) | 1,971 (51%) | +481 |
| thin (from 0) | 1,847 (48%) | 1,216 (31%) | -631 |

## The approved images

1,740 of 1,891 Wikidata images pass the photo pipeline's licence and credit rules (`data/knowledge/media/approved_image_queue.json`; see [image_coverage_report.md](image_coverage_report.md)). Fetched and checked by eye, each would show a photo of the dish itself (90% of the image weight) instead of a family photo or the placeholder. 781 dishes would change tier:

- thin to fair: 631
- fair to rich: 150

Examples of dishes that would become rich: Baozi (65 to 83), Doner kebab (65 to 83), Gukbap (65 to 83), Patriotic soup (65 to 83), Shark fin soup (65 to 83), Tong sui (65 to 83), Wine gum (65 to 83), Xuanwei ham (65 to 83), Ajiaco (60 to 78), Ashure (60 to 78), Birria (60 to 78), Bridie (60 to 78), Bubur ketan hitam (60 to 78), Chapli kebab (60 to 78), Coconut jam (60 to 78).

## What keeps the others from rich

Of the 3,337 dishes below rich, the parts they lack most (a dish can lack several):

| Part | Dishes without it | Where it would come from |
|---|---:|---|
| how to say it | 3,327 | data/reference/dish_pronunciation.csv (a person adds it) |
| a real photo of it (its recipe, the dish or a version) | 2,642 | scripts/dish_photos/ (image_coverage_report.md) |
| a related dish or version in EverFlavor | 2,462 | the Food Graph (comes with family and versions) |
| at least one recipe | 2,204 | a licensed recipe source; never written |
| story sentences (history, origin, culture) | 2,065 | fetch_knowledge.py --stories |
| fun-fact sentences from its Wikipedia intro | 1,488 | fetch_knowledge.py |
| its ingredients on Wikidata (P186, made from) | 1,402 | Wikidata itself |
| map places in the pilot area for its country | 1,219 | stores.COUNTRY_CUISINES and the places table |
| a dish family (notebook 15) | 929 | notebook 15, when Wikidata files it under one |
| a country of origin on Wikidata (P495) | 767 | Wikidata itself: nothing to fill on our side |
| a summary from its Wikipedia article | 1 | scripts/knowledge/fetch_knowledge.py |

Every source in the last column is one we already use. A part with no source on our side (Wikidata itself, a licensed recipe, a person's pronunciation) stays missing rather than written by us.
