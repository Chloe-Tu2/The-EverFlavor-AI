# Dish image audit (2026-11-23)

The best image each of our 3,201 dishes can show, its licence and credit, and what to fetch next. Reports only: no image was downloaded. Built by `scripts/knowledge/media_audit.py`; per dish in `data/knowledge/media/dish_media_audit.json`.

Levels, best first: a photo of one of its own recipes (100 points), a Commons photo of the dish (90), of a version of it (80), of its family (60, shown as "a dumpling in general"), else the app's pixel-art kitchen (0). A cuisine or country photo is not used, since it would not show the dish.

## Where the dishes stand

| Best level | Dishes | Share |
|---|---:|---:|
| recipe | 1,077 | 32% |
| dish | 65 | 2% |
| variant | 9 | 0% |
| family | 155 | 5% |
| placeholder | 2,065 | 61% |

Statuses: candidate 1,737, verified 1,142, missing 328, fallback 164. Every dish resolves to an image or the placeholder, so no page is empty.

## By zone

| Zone | Dishes | Own photo | Any photo | Fetchable from Wikidata | Average score |
|---|---:|---:|---:|---:|---:|
| Europe | 1,194 | 32% | 37% | 718 | 34.7 |
| Asia | 1,006 | 21% | 28% | 731 | 25.0 |
| North America | 454 | 71% | 75% | 114 | 73.1 |
| Latin America | 254 | 36% | 37% | 129 | 36.7 |
| Middle East & North Africa | 182 | 19% | 24% | 122 | 22.2 |
| Africa | 134 | 16% | 19% | 23 | 17.7 |
| Caribbean | 86 | 51% | 56% | 32 | 54.2 |
| Oceania | 61 | 52% | 56% | 20 | 54.4 |

## By country (20 with the most dishes)

| Country | Dishes | Own photo | Any photo | Fetchable | Average score |
|---|---:|---:|---:|---:|---:|
| United States | 366 | 72% | 77% | 90 | 74.5 |
| Italy | 327 | 32% | 34% | 193 | 33.5 |
| Indonesia | 248 | 10% | 17% | 217 | 14.2 |
| China | 179 | 31% | 36% | 108 | 33.3 |
| Mexico | 113 | 57% | 58% | 41 | 57.1 |
| Japan | 108 | 29% | 37% | 74 | 33.9 |
| India | 103 | 41% | 49% | 55 | 45.1 |
| Canada | 88 | 66% | 69% | 24 | 67.6 |
| Germany | 88 | 30% | 33% | 54 | 31.6 |
| Greece | 88 | 43% | 47% | 44 | 45.1 |
| France | 87 | 52% | 55% | 41 | 53.2 |
| Philippines | 87 | 16% | 22% | 67 | 19.5 |
| South Korea | 79 | 6% | 15% | 72 | 11.5 |
| Thailand | 77 | 31% | 38% | 46 | 35.1 |
| Portugal | 72 | 11% | 11% | 59 | 11.0 |
| Vietnam | 72 | 18% | 21% | 53 | 19.2 |
| United Kingdom | 69 | 55% | 59% | 21 | 57.7 |
| Poland | 66 | 30% | 44% | 41 | 38.3 |
| Australia | 59 | 54% | 58% | 19 | 56.3 |
| Turkey | 57 | 16% | 19% | 45 | 17.9 |

## Rules checked

- Every dish, version and family photo is a Wikimedia Commons file with a licence on the free list (CC0, public domain, CC BY, CC BY-SA) and a credit line; one that fails goes to `review`, never to the page.
- A recipe photo counts only from Food.com, whose photos are CC0 (`docs/sources.md`). 176 dishes have recipe photos only from the Hugging Face set, whose photo licence is not recorded yet: they are not counted until a person confirms it on the dataset page.
- Photos a person turned down (`data/reference/dish_photo_review.csv`) are not used.
- No image is generated, and no photo from a site without a free licence is used.

## Remediation plan

1. **Fetch** the Wikidata images of 1,889 dishes through the existing photo pipeline (`scripts/dish_photos/fetch_dish_photos.py meta`, `download`, `curate`, `write`), which checks each licence and keeps a credit line: 283 high priority (50+ of the 80 points besides the image), 1,606 medium (`image_priority_queue.json`).
2. **No image anywhere** for 340 dishes: Commons search by name is the next source; a person checks each match, as the photo review sheet does today.
3. **Family photos** stand in meanwhile, labelled as the family, never as the dish.

## Approved for collection

1,739 of 1,889 Wikidata images pass the photo pipeline's rules (free licence, an author to credit, a photo type, at least 400 px, not a map or drawing), read from the Commons API without downloading: 258 high priority, 1,481 medium priority, 0 low priority. The rest:

- no author to credit: 30
- smaller than 400 px: 96
- named or described as a map, logo, drawing or label, not a photo: 12
- licence not free: 18
- not a photo: 2

The queue (`data/knowledge/media/approved_image_queue.json`) is for the photo pipeline to fetch once the team agrees; a person then checks each photo by eye before the app shows it.
