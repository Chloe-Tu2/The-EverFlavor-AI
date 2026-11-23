# Country coverage and depth (2026-11-22)

Coverage (how many of a country's known dishes we have, from the coverage audit) next to depth (the dish quality score). A country with many thin dishes needs enrichment before more dishes.

| Country | Coverage | Dishes | Recipes | Missing | Average score | Thin |
|---|---:|---:|---:|---:|---:|---:|
| United States | high | 366 | 131,095 | 146 | 59.5 | 17% |
| Italy | high | 327 | 24,910 | 79 | 41.3 | 52% |
| Indonesia | high | 248 | 218 | 24 | 36.2 | 53% |
| China | high | 179 | 5,878 | 99 | 50.3 | 28% |
| Mexico | high | 113 | 11,490 | 16 | 47.2 | 38% |
| Japan | medium | 108 | 2,232 | 139 | 49.2 | 31% |
| India | high | 103 | 7,312 | 63 | 46.3 | 39% |
| Canada | high | 88 | 4,577 | 20 | 55.1 | 25% |
| Germany | high | 88 | 1,476 | 40 | 40.0 | 50% |
| Greece | high | 88 | 4,334 | 8 | 43.4 | 49% |
| France | low | 87 | 8,520 | 177 | 48.6 | 32% |
| Philippines | high | 87 | 255 | 29 | 37.6 | 53% |
| South Korea | high | 79 | 605 | 9 | 39.8 | 51% |
| Thailand | high | 77 | 2,428 | 7 | 41.0 | 47% |
| Portugal | high | 72 | 434 | 5 | 29.7 | 81% |
| Vietnam | high | 72 | 500 | 6 | 35.6 | 56% |
| United Kingdom | low | 69 | 4,553 | 171 | 60.0 | 20% |
| Poland | high | 66 | 418 | 11 | 42.4 | 48% |
| Australia | high | 59 | 2,758 | 5 | 49.8 | 32% |
| Turkey | high | 57 | 458 | 32 | 36.8 | 58% |
| Brazil | high | 51 | 311 | 5 | 32.2 | 67% |
| Norway | high | 51 | 200 | 3 | 38.8 | 53% |
| Jamaica | high | 50 | 402 | 1 | 49.0 | 30% |
| Nigeria | high | 50 | 32 | 6 | 20.4 | 92% |
| Spain | medium | 49 | 1,851 | 60 | 37.8 | 57% |
| Russia | medium | 48 | 428 | 8 | 44.6 | 29% |
| Sweden | medium | 44 | 463 | 20 | 39.6 | 57% |
| Hungary | medium | 42 | 346 | 4 | 44.9 | 40% |
| Malaysia | medium | 38 | 79 | 3 | 34.5 | 66% |
| Lebanon | medium | 31 | 596 | 0 | 47.4 | 32% |
| Netherlands | medium | 31 | 245 | 30 | 37.3 | 55% |
| Chile | medium | 28 | 71 | 4 | 33.3 | 68% |
| South Africa | medium | 28 | 606 | 1 | 41.7 | 36% |
| Switzerland | medium | 27 | 323 | 32 | 38.4 | 59% |
| Belgium | medium | 25 | 113 | 18 | 44.4 | 36% |
| Finland | medium | 25 | 147 | 10 | 31.0 | 64% |
| Cuba | medium | 22 | 397 | 0 | 41.2 | 50% |
| Ireland | medium | 22 | 711 | 7 | 51.5 | 18% |
| Morocco | medium | 20 | 1,592 | 0 | 35.9 | 55% |
| Denmark | medium | 18 | 258 | 14 | 42.3 | 33% |
| Palestine | medium | 18 | 51 | 0 | 37.9 | 56% |
| Peru | medium | 18 | 98 | 11 | 42.2 | 44% |
| Colombia | medium | 16 | 70 | 3 | 35.0 | 56% |
| Egypt | medium | 15 | 205 | 3 | 31.5 | 47% |
| Iran | low | 13 | 432 | 26 | 26.2 | 85% |
| Iraq | low | 11 | 66 | 2 | 34.5 | 55% |
| Argentina | low | 10 | 108 | 10 | 37.5 | 60% |
| Czech Republic | low | 10 | 94 | 4 | 48.2 | 30% |
| Ethiopia | low | 10 | 78 | 0 | 28.7 | 90% |
| Guatemala | low | 8 | 24 | 0 | 22.5 | 75% |
| Nicaragua | low | 8 | 0 | 0 | 20.0 | 88% |
| Senegal | low | 8 | 0 | 0 | 19.4 | 88% |
| Cameroon | low | 7 | 0 | 0 | 16.4 | 100% |
| Pakistan | low | 7 | 82 | 5 | 42.9 | 43% |
| Algeria | low | 6 | 11 | 4 | 19.2 | 83% |
| Tunisia | low | 6 | 7 | 2 | 26.7 | 100% |
| Uzbekistan | low | 6 | 0 | 0 | 20.0 | 100% |
| Austria | low | 5 | 101 | 9 | 40.0 | 60% |
| Haiti | low | 5 | 0 | 0 | 23.0 | 80% |
| Ghana | low | 4 | 0 | 1 | 21.8 | 75% |

## Remediation plan

Enrich before adding: the countries with 20+ dishes and the lowest average score are Nigeria (20.4), Portugal (29.7), Finland (31.0), Brazil (32.2), Chile (33.3), Malaysia (34.5), Vietnam (35.6), Morocco (35.9), Indonesia (36.2), Turkey (36.8). Their dishes gain most from photos (`scripts/dish_photos/`) and stories (`fetch_knowledge.py --stories`); new dishes come after, from `coverage/next_500.json`.
