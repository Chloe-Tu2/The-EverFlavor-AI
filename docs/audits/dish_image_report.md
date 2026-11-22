# Dish image audit (2026-11-22)

The best image each of our 3,201 dishes can show, its licence and credit, and what to fetch next. Reports only: no image was downloaded. Built by `scripts/knowledge/media_audit.py`; per dish in `data/knowledge/media/dish_media_audit.json`.

Levels, best first: a photo of one of its own recipes (100 points), a Commons photo of the dish (90), of a version of it (80), of its family (60, shown as "a dumpling in general"), else the app's pixel-art kitchen (0). A cuisine or country photo is not used, since it would not show the dish.

## Where the dishes stand

| Best level | Dishes | Share |
|---|---:|---:|
| recipe | 1,059 | 33% |
| dish | 62 | 2% |
| variant | 9 | 0% |
| family | 150 | 5% |
| placeholder | 1,921 | 60% |

Statuses: candidate 1,731, verified 1,121, missing 190, fallback 159. Every dish resolves to an image or the placeholder, so no page is empty.

## By zone

| Zone | Dishes | Own photo | Any photo | Fetchable from Wikidata | Average score |
|---|---:|---:|---:|---:|---:|
| Europe | 1,185 | 32% | 37% | 715 | 34.9 |
| Asia | 994 | 22% | 28% | 729 | 25.5 |
| North America | 455 | 71% | 76% | 113 | 73.4 |
| Latin America | 233 | 36% | 38% | 129 | 37.5 |
| Middle East & North Africa | 165 | 20% | 25% | 122 | 23.3 |
| Caribbean | 72 | 53% | 57% | 32 | 55.6 |
| Oceania | 59 | 56% | 58% | 19 | 56.9 |
| Africa | 38 | 26% | 34% | 23 | 30.8 |

## By country (20 with the most dishes)

| Country | Dishes | Own photo | Any photo | Fetchable | Average score |
|---|---:|---:|---:|---:|---:|
| United States | 367 | 72% | 77% | 89 | 74.8 |
| Italy | 326 | 33% | 34% | 193 | 33.6 |
| Indonesia | 248 | 10% | 17% | 217 | 14.2 |
| China | 178 | 31% | 36% | 108 | 33.5 |
| Mexico | 110 | 56% | 57% | 41 | 56.8 |
| Japan | 108 | 29% | 37% | 74 | 33.9 |
| India | 102 | 41% | 49% | 55 | 45.6 |
| Canada | 88 | 66% | 69% | 24 | 67.6 |
| Greece | 88 | 43% | 47% | 44 | 45.1 |
| Germany | 87 | 30% | 33% | 54 | 32.0 |
| Philippines | 86 | 16% | 22% | 67 | 19.8 |
| France | 84 | 50% | 54% | 41 | 51.5 |
| South Korea | 79 | 6% | 15% | 72 | 11.5 |
| Thailand | 77 | 34% | 40% | 44 | 37.7 |
| Portugal | 72 | 11% | 11% | 59 | 11.0 |
| Vietnam | 71 | 18% | 21% | 53 | 19.4 |
| United Kingdom | 67 | 55% | 60% | 21 | 57.9 |
| Poland | 65 | 31% | 43% | 41 | 38.0 |
| Australia | 58 | 57% | 59% | 18 | 57.9 |
| Turkey | 57 | 16% | 19% | 45 | 17.9 |

## Rules checked

- Every dish, version and family photo is a Wikimedia Commons file with a licence on the free list (CC0, public domain, CC BY, CC BY-SA) and a credit line; one that fails goes to `review`, never to the page.
- A recipe photo counts only from Food.com, whose photos are CC0 (`docs/sources.md`). 168 dishes have recipe photos only from the Hugging Face set, whose photo licence is not recorded yet: they are not counted until a person confirms it on the dataset page.
- Photos a person turned down (`data/reference/dish_photo_review.csv`) are not used.
- No image is generated, and no photo from a site without a free licence is used.

## Remediation plan

1. **Fetch** the Wikidata images of 1,882 dishes through the existing photo pipeline (`scripts/dish_photos/fetch_dish_photos.py meta`, `download`, `curate`, `write`), which checks each licence and keeps a credit line: 280 high priority (50+ of the 80 points besides the image), 1,602 medium (`image_priority_queue.json`).
2. **No image anywhere** for 198 dishes: Commons search by name is the next source; a person checks each match, as the photo review sheet does today.
3. **Family photos** stand in meanwhile, labelled as the family, never as the dish.
