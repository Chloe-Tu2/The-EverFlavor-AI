# Country coverage and depth (2026-11-22)

Coverage (how many of a country's known dishes we have, from the coverage audit) next to depth (the dish quality score). A country with many thin dishes needs enrichment before more dishes.

| Country | Coverage | Dishes | Recipes | Missing | Average score | Thin |
|---|---:|---:|---:|---:|---:|---:|
| United States | high | 367 | 131,162 | 148 | 59.7 | 17% |
| Italy | high | 326 | 24,918 | 79 | 41.4 | 52% |
| Indonesia | high | 248 | 218 | 24 | 36.2 | 53% |
| China | high | 178 | 5,867 | 99 | 50.3 | 29% |
| Mexico | high | 110 | 11,508 | 18 | 47.0 | 37% |
| Japan | medium | 108 | 2,249 | 139 | 49.2 | 31% |
| India | high | 102 | 7,319 | 65 | 46.5 | 38% |
| Canada | high | 88 | 4,563 | 20 | 55.1 | 25% |
| Greece | high | 88 | 4,352 | 8 | 43.4 | 49% |
| Germany | high | 87 | 1,475 | 40 | 40.5 | 49% |
| Philippines | high | 86 | 254 | 30 | 38.0 | 52% |
| France | low | 84 | 8,509 | 179 | 48.2 | 33% |
| South Korea | high | 79 | 606 | 9 | 39.8 | 51% |
| Thailand | high | 77 | 2,413 | 7 | 41.5 | 45% |
| Portugal | high | 72 | 432 | 5 | 29.7 | 81% |
| Vietnam | high | 71 | 509 | 6 | 36.1 | 55% |
| United Kingdom | low | 67 | 4,545 | 172 | 61.2 | 21% |
| Poland | high | 65 | 407 | 11 | 42.4 | 49% |
| Australia | high | 58 | 2,800 | 5 | 50.6 | 29% |
| Turkey | high | 57 | 471 | 32 | 36.8 | 58% |
| Brazil | high | 51 | 311 | 5 | 32.2 | 67% |
| Norway | high | 51 | 202 | 3 | 38.8 | 53% |
| Jamaica | high | 50 | 402 | 1 | 49.0 | 30% |
| Spain | medium | 49 | 1,840 | 60 | 38.3 | 55% |
| Russia | medium | 48 | 445 | 8 | 44.4 | 29% |
| Sweden | medium | 44 | 466 | 20 | 39.9 | 59% |
| Hungary | medium | 41 | 349 | 4 | 46.2 | 37% |
| Malaysia | medium | 38 | 79 | 3 | 34.5 | 66% |
| Lebanon | medium | 31 | 587 | 0 | 47.4 | 32% |
| Netherlands | medium | 31 | 245 | 30 | 37.3 | 55% |
| Chile | medium | 28 | 71 | 4 | 33.3 | 68% |
| South Africa | medium | 28 | 603 | 1 | 41.3 | 36% |
| Switzerland | medium | 27 | 327 | 32 | 38.4 | 59% |
| Belgium | medium | 25 | 113 | 18 | 44.4 | 36% |
| Finland | medium | 25 | 147 | 10 | 31.0 | 64% |
| Cuba | medium | 22 | 399 | 0 | 41.2 | 50% |
| Ireland | medium | 22 | 705 | 8 | 51.5 | 18% |
| Morocco | medium | 20 | 1,591 | 0 | 35.4 | 55% |
| Denmark | medium | 18 | 259 | 14 | 42.3 | 33% |
| Palestine | medium | 18 | 51 | 0 | 37.9 | 56% |
| Peru | medium | 18 | 98 | 11 | 42.2 | 44% |
| Colombia | medium | 16 | 70 | 3 | 35.0 | 56% |
| Egypt | medium | 15 | 206 | 3 | 31.5 | 47% |
| Iran | low | 11 | 429 | 26 | 27.3 | 82% |
| Iraq | low | 11 | 66 | 2 | 34.5 | 55% |
| Argentina | low | 10 | 108 | 10 | 37.5 | 60% |
| Czech Republic | low | 10 | 94 | 4 | 48.2 | 30% |
| Ethiopia | low | 10 | 78 | 0 | 28.7 | 90% |
| Pakistan | low | 6 | 82 | 5 | 47.5 | 33% |
| Austria | low | 5 | 101 | 9 | 40.0 | 60% |
| Saudi Arabia | low | 2 | 73 | 0 | 32.5 | 100% |
| Cambodia | low | 1 | 53 | 7 | 40.0 | 0% |
| New Zealand | low | 1 | 387 | 1 | 45.0 | 0% |
| Afghanistan | recipes only | 0 | 7 | 5 |  |  |
| Albania | recipes only | 0 | 11 | 0 |  |  |
| Algeria | recipes only | 0 | 11 | 6 |  |  |
| Andorra | recipes only | 0 | 3 | 0 |  |  |
| Angola | recipes only | 0 | 10 | 0 |  |  |
| Antigua and Barbuda | recipes only | 0 | 3 | 0 |  |  |
| Armenia | recipes only | 0 | 3 | 5 |  |  |

## Remediation plan

Enrich before adding: the countries with 20+ dishes and the lowest average score are Portugal (29.7), Finland (31.0), Brazil (32.2), Chile (33.3), Malaysia (34.5), Morocco (35.4), Vietnam (36.1), Indonesia (36.2), Turkey (36.8), Netherlands (37.3). Their dishes gain most from photos (`scripts/dish_photos/`) and stories (`fetch_knowledge.py --stories`); new dishes come after, from `coverage/next_500.json`.
