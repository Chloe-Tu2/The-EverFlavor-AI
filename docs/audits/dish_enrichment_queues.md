# Dish enrichment queues (2026-11-22)

Two queues for people, built from the quality files by `scripts/knowledge/enrichment_queues.py`. Nothing in them is filled or published; each gap names the source or script that can fill it.

## Rich-dish upgrade queue

`data/knowledge/quality/rich_dish_upgrade_queue.json`: the 2,865 of 3,371 dishes that are not rich, lowest effort first.

| What | Dishes |
|---|---:|
| become rich with low work only (a staged photo signed off) | 204 |
| could become rich with low and medium work, at most (if the sources we already use have the facts) | 2,433 |
| stay below rich even then (they need a recipe source, a Wikidata fact or a new photo) | 432 |

Gaps by work:

| Work | Gaps |
|---|---:|
| low | 1,122 |
| medium | 9,169 |
| high | 2,916 |

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

`data/knowledge/quality/walter_enrichment_queue.json`: 3,116 of 3,371 dishes miss at least one thing the waiter tells. Technique is not counted: no source we use states it.

| Missing | Dishes | Filled by |
|---|---:|---:|
| history | 1,749 | fetch_knowledge.py --stories |
| origin | 697 | Wikidata P495 (nothing on our side) |
| ingredient explanation | 1,256 | Wikidata P186 (made from) |
| interesting fact | 1,430 | fetch_knowledge.py (intro sentences) |
| related dishes | 2,227 | the Food Graph (family, versions) |

Dishes missing only one thing: 736.
