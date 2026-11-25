# Dish enrichment queues (2026-11-24)

Two queues for people, built from the quality files by `scripts/knowledge/enrichment_queues.py`. Nothing in them is filled or published; each gap names the source or script that can fill it.

## Rich-dish upgrade queue

`data/knowledge/quality/rich_dish_upgrade_queue.json`: the 3,334 of 3,863 dishes that are not rich, lowest effort first.

| What | Dishes |
|---|---:|
| become rich with low work only (a staged photo signed off) | 205 |
| could become rich with low and medium work, at most (if the sources we already use have the facts) | 2,517 |
| stay below rich even then (they need a recipe source, a Wikidata fact or a new photo) | 817 |

Gaps by work:

| Work | Gaps |
|---|---:|
| low | 1,122 |
| medium | 10,618 |
| high | 3,896 |

The first ten:

| Dish | Country | Score | With low work | With low and medium |
|---|---:|---:|---:|---:|
| Bakpia | Philippines | 50 | 70 | 95 |
| Bibim-guksu | South Korea | 52 | 72 | 97 |
| Callos | Philippines | 50 | 70 | 95 |
| Cantonese seafood soup | China | 52 | 72 | 97 |
| Danger dog | United States | 52 | 72 | 97 |
| Jamón | Spain | 55 | 75 | 100 |
| Maeun-tang | South Korea | 52 | 72 | 97 |
| Nasi kebuli | Indonesia | 52 | 72 | 97 |
| Pan de coco | Philippines | 52 | 72 | 97 |
| Tom yum | Thailand | 52 | 72 | 97 |

## Walter enrichment queue

`data/knowledge/quality/walter_enrichment_queue.json`: 3,590 of 3,863 dishes miss at least one thing the waiter tells. Technique is not counted: no source we use states it.

| Missing | Dishes | Filled by |
|---|---:|---:|
| history | 2,083 | fetch_knowledge.py --stories |
| origin | 837 | Wikidata P495 (nothing on our side) |
| ingredient explanation | 1,496 | Wikidata P186 (made from) |
| interesting fact | 1,635 | fetch_knowledge.py (intro sentences) |
| related dishes | 2,599 | the Food Graph (family, versions) |

Dishes missing only one thing: 799.
