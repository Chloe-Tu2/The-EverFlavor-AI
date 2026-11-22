# Country coverage and depth (2026-11-22)

Coverage (how many of a country's known dishes we have, from the coverage audit) next to depth (the dish quality score). A country with many thin dishes needs enrichment before more dishes.

| Country | Coverage | Dishes | Recipes | Missing | Average score | Thin |
|---|---:|---:|---:|---:|---:|---:|
| United States | high | 367 | 131,095 | 148 | 59.6 | 17% |
| Italy | high | 326 | 24,910 | 79 | 41.4 | 52% |
| Indonesia | high | 248 | 218 | 24 | 36.2 | 53% |
| China | high | 178 | 5,878 | 99 | 50.3 | 29% |
| Mexico | high | 110 | 11,490 | 18 | 47.0 | 37% |
| Japan | medium | 108 | 2,232 | 139 | 49.2 | 31% |
| India | high | 102 | 7,312 | 65 | 46.5 | 38% |
| Canada | high | 88 | 4,577 | 20 | 55.1 | 25% |
| Greece | high | 88 | 4,334 | 8 | 43.4 | 49% |
| Germany | high | 87 | 1,476 | 40 | 40.5 | 49% |
| Philippines | high | 86 | 255 | 30 | 38.0 | 52% |
| France | low | 84 | 8,520 | 179 | 48.2 | 33% |
| South Korea | high | 79 | 605 | 9 | 39.8 | 51% |
| Thailand | high | 77 | 2,428 | 7 | 41.0 | 47% |
| Portugal | high | 72 | 434 | 5 | 29.7 | 81% |
| Vietnam | high | 71 | 500 | 6 | 36.1 | 55% |
| United Kingdom | low | 67 | 4,553 | 172 | 61.2 | 21% |
| Poland | high | 65 | 418 | 11 | 42.4 | 49% |
| Australia | high | 58 | 2,758 | 5 | 50.2 | 31% |
| Turkey | high | 57 | 458 | 32 | 36.8 | 58% |
| Brazil | high | 51 | 311 | 5 | 32.2 | 67% |
| Norway | high | 51 | 200 | 3 | 38.8 | 53% |
| Jamaica | high | 50 | 402 | 1 | 49.0 | 30% |
| Spain | medium | 49 | 1,851 | 60 | 37.8 | 57% |
| Russia | medium | 48 | 428 | 8 | 44.4 | 29% |
| Sweden | medium | 44 | 463 | 20 | 39.6 | 57% |
| Hungary | medium | 41 | 346 | 4 | 45.7 | 39% |
| Malaysia | medium | 38 | 79 | 3 | 34.5 | 66% |
| Lebanon | medium | 31 | 596 | 0 | 47.4 | 32% |
| Netherlands | medium | 31 | 245 | 30 | 37.3 | 55% |
| Chile | medium | 28 | 71 | 4 | 33.3 | 68% |
| South Africa | medium | 28 | 606 | 1 | 41.3 | 36% |
| Switzerland | medium | 27 | 323 | 32 | 38.4 | 59% |
| Belgium | medium | 25 | 113 | 18 | 44.4 | 36% |
| Finland | medium | 25 | 147 | 10 | 31.0 | 64% |
| Cuba | medium | 22 | 397 | 0 | 41.2 | 50% |
| Ireland | medium | 22 | 711 | 8 | 51.5 | 18% |
| Morocco | medium | 20 | 1,592 | 0 | 35.4 | 55% |
| Denmark | medium | 18 | 258 | 14 | 42.3 | 33% |
| Palestine | medium | 18 | 51 | 0 | 37.9 | 56% |
| Peru | medium | 18 | 98 | 11 | 42.2 | 44% |
| Colombia | medium | 16 | 70 | 3 | 35.0 | 56% |
| Egypt | medium | 15 | 205 | 3 | 31.5 | 47% |
| Iran | low | 11 | 432 | 26 | 27.3 | 82% |
| Iraq | low | 11 | 66 | 2 | 34.5 | 55% |
| Argentina | low | 10 | 108 | 10 | 37.5 | 60% |
| Czech Republic | low | 10 | 94 | 4 | 48.2 | 30% |
| Ethiopia | low | 10 | 78 | 0 | 28.7 | 90% |
| Pakistan | low | 6 | 82 | 5 | 47.5 | 33% |
| Austria | low | 5 | 101 | 9 | 40.0 | 60% |
| Saudi Arabia | low | 2 | 73 | 0 | 32.5 | 100% |
| Cambodia | low | 1 | 53 | 7 | 40.0 | 0% |
| New Zealand | low | 1 | 384 | 1 | 45.0 | 0% |
| Afghanistan | recipes only | 0 | 7 | 5 |  |  |
| Albania | recipes only | 0 | 11 | 0 |  |  |
| Algeria | recipes only | 0 | 11 | 6 |  |  |
| Andorra | recipes only | 0 | 3 | 0 |  |  |
| Angola | recipes only | 0 | 10 | 0 |  |  |
| Antigua and Barbuda | recipes only | 0 | 3 | 0 |  |  |
| Armenia | recipes only | 0 | 3 | 5 |  |  |

## Remediation plan

Enrich before adding: the countries with 20+ dishes and the lowest average score are Portugal (29.7), Finland (31.0), Brazil (32.2), Chile (33.3), Malaysia (34.5), Morocco (35.4), Vietnam (36.1), Indonesia (36.2), Turkey (36.8), Netherlands (37.3). Their dishes gain most from photos (`scripts/dish_photos/`) and stories (`fetch_knowledge.py --stories`); new dishes come after, from `coverage/next_500.json`.
