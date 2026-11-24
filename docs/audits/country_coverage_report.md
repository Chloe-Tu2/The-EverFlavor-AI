# Country coverage and depth (2026-11-23)

Coverage (how many of a country's known dishes we have, from the coverage audit) next to depth (the dish quality score). A country with many thin dishes needs enrichment before more dishes.

| Country | Coverage | Dishes | Recipes | Missing | Average score | Thin |
|---|---:|---:|---:|---:|---:|---:|
| United States | high | 366 | 131,095 | 146 | 59.8 | 17% |
| Italy | high | 329 | 24,910 | 86 | 41.7 | 51% |
| Indonesia | high | 249 | 218 | 25 | 36.4 | 52% |
| China | high | 181 | 5,878 | 99 | 50.5 | 28% |
| Mexico | high | 112 | 11,490 | 15 | 47.0 | 37% |
| Japan | medium | 109 | 2,232 | 138 | 49.3 | 30% |
| India | high | 105 | 7,312 | 64 | 46.9 | 38% |
| Canada | high | 89 | 4,577 | 20 | 55.2 | 25% |
| France | low | 88 | 8,520 | 181 | 49.2 | 32% |
| Germany | high | 88 | 1,476 | 40 | 40.1 | 50% |
| Greece | high | 88 | 4,334 | 8 | 43.9 | 48% |
| Philippines | high | 87 | 255 | 30 | 37.8 | 53% |
| South Korea | high | 79 | 605 | 9 | 39.8 | 51% |
| Thailand | high | 77 | 2,428 | 6 | 41.0 | 47% |
| Portugal | high | 72 | 434 | 5 | 29.7 | 81% |
| Vietnam | high | 72 | 500 | 6 | 35.7 | 56% |
| United Kingdom | low | 69 | 4,553 | 172 | 60.3 | 20% |
| Poland | high | 68 | 418 | 9 | 43.7 | 46% |
| Turkey | high | 65 | 458 | 31 | 37.0 | 57% |
| Australia | high | 60 | 2,758 | 4 | 50.1 | 32% |
| Spain | medium | 55 | 1,851 | 58 | 37.9 | 56% |
| Brazil | high | 51 | 311 | 6 | 32.6 | 65% |
| Norway | high | 51 | 200 | 3 | 38.8 | 53% |
| Jamaica | high | 50 | 402 | 1 | 49.4 | 30% |
| Nigeria | high | 50 | 32 | 8 | 25.6 | 82% |
| Russia | medium | 48 | 428 | 6 | 44.6 | 29% |
| Sweden | medium | 44 | 463 | 20 | 39.8 | 57% |
| Hungary | medium | 42 | 346 | 4 | 44.9 | 40% |
| Malaysia | medium | 39 | 79 | 2 | 34.1 | 67% |
| Lebanon | medium | 31 | 596 | 0 | 47.4 | 32% |
| Netherlands | medium | 31 | 245 | 30 | 37.3 | 55% |
| Chile | medium | 28 | 71 | 4 | 33.3 | 68% |
| South Africa | medium | 28 | 606 | 1 | 41.7 | 36% |
| Switzerland | medium | 27 | 323 | 31 | 38.4 | 59% |
| Belgium | medium | 25 | 113 | 18 | 44.4 | 36% |
| Finland | medium | 25 | 147 | 9 | 31.0 | 64% |
| Taiwan | medium | 25 | 5 | 8 | 31.2 | 72% |
| Cuba | medium | 22 | 397 | 0 | 41.2 | 50% |
| Georgia | medium | 22 | 0 | 4 | 25.0 | 82% |
| Ireland | medium | 22 | 711 | 7 | 51.5 | 18% |
| Romania | medium | 21 | 0 | 5 | 25.7 | 86% |
| Morocco | medium | 20 | 1,592 | 0 | 35.9 | 55% |
| Myanmar | medium | 19 | 0 | 2 | 33.6 | 58% |
| Denmark | medium | 18 | 258 | 14 | 42.3 | 33% |
| Iran | medium | 18 | 432 | 25 | 30.9 | 67% |
| Palestine | medium | 18 | 51 | 0 | 37.9 | 56% |
| Peru | medium | 18 | 98 | 11 | 42.2 | 44% |
| Colombia | medium | 17 | 70 | 2 | 35.0 | 59% |
| Croatia | medium | 17 | 8 | 1 | 25.4 | 76% |
| Egypt | medium | 16 | 205 | 2 | 35.1 | 44% |
| Ukraine | medium | 16 | 6 | 0 | 31.2 | 62% |
| Israel | medium | 15 | 0 | 3 | 33.3 | 67% |
| Nepal | low | 14 | 33 | 1 | 23.2 | 93% |
| Serbia | low | 13 | 0 | 0 | 40.9 | 46% |
| Armenia | low | 12 | 3 | 2 | 24.6 | 75% |
| Bangladesh | low | 12 | 3 | 1 | 29.9 | 75% |
| Bulgaria | low | 12 | 7 | 2 | 31.2 | 83% |
| Algeria | low | 11 | 11 | 3 | 17.3 | 91% |
| Iraq | low | 11 | 66 | 3 | 34.5 | 55% |
| Singapore | low | 11 | 0 | 1 | 33.2 | 55% |

## Remediation plan

Enrich before adding: the countries with 20+ dishes and the lowest average score are Georgia (25.0), Nigeria (25.6), Romania (25.7), Portugal (29.7), Finland (31.0), Taiwan (31.2), Brazil (32.6), Chile (33.3), Malaysia (34.1), Vietnam (35.7). Their dishes gain most from photos (`scripts/dish_photos/`) and stories (`fetch_knowledge.py --stories`); new dishes come after, from `coverage/next_500.json`.
