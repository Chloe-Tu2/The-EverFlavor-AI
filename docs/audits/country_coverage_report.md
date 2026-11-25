# Country coverage and depth (2026-11-25)

Coverage (how many of a country's known dishes we have, from the coverage audit) next to depth (the dish quality score). A country with many thin dishes needs enrichment before more dishes.

| Country | Coverage | Dishes | Recipes | Missing | Average score | Thin |
|---|---:|---:|---:|---:|---:|---:|
| United States | high | 395 | 131,095 | 146 | 59.8 | 17% |
| Italy | high | 350 | 24,910 | 87 | 41.7 | 51% |
| Indonesia | high | 265 | 218 | 25 | 36.4 | 52% |
| China | high | 216 | 5,878 | 99 | 50.5 | 28% |
| France | medium | 137 | 8,520 | 181 | 49.2 | 32% |
| Mexico | high | 131 | 11,490 | 15 | 47.0 | 37% |
| India | high | 117 | 7,312 | 64 | 46.9 | 38% |
| Japan | medium | 115 | 2,232 | 138 | 49.3 | 30% |
| Germany | high | 109 | 1,476 | 40 | 40.1 | 50% |
| Canada | high | 92 | 4,577 | 20 | 55.2 | 25% |
| Philippines | high | 92 | 255 | 30 | 37.8 | 53% |
| Greece | high | 90 | 4,334 | 8 | 43.9 | 48% |
| United Kingdom | low | 86 | 4,553 | 172 | 60.3 | 20% |
| Turkey | high | 85 | 458 | 31 | 37.0 | 57% |
| Spain | medium | 80 | 1,851 | 58 | 37.9 | 56% |
| Portugal | high | 79 | 434 | 5 | 29.7 | 81% |
| South Korea | high | 79 | 605 | 9 | 39.8 | 51% |
| Thailand | high | 79 | 2,428 | 6 | 41.0 | 47% |
| Vietnam | high | 74 | 500 | 6 | 35.7 | 56% |
| Poland | high | 73 | 418 | 9 | 43.7 | 46% |
| Australia | high | 60 | 2,758 | 4 | 50.1 | 32% |
| Brazil | high | 59 | 311 | 6 | 33.0 | 65% |
| Malaysia | high | 55 | 79 | 3 | 34.1 | 67% |
| Norway | high | 54 | 200 | 3 | 39.2 | 51% |
| Russia | high | 54 | 428 | 6 | 44.6 | 29% |
| Nigeria | high | 53 | 32 | 8 | 25.6 | 82% |
| Jamaica | high | 51 | 402 | 1 | 49.4 | 30% |
| Sweden | medium | 48 | 463 | 20 | 39.8 | 57% |
| Hungary | medium | 45 | 346 | 4 | 44.9 | 40% |
| Netherlands | medium | 37 | 245 | 30 | 37.3 | 55% |
| Iran | medium | 32 | 432 | 26 | 30.9 | 67% |
| Switzerland | medium | 32 | 323 | 30 | 38.4 | 59% |
| Finland | medium | 31 | 147 | 9 | 31.0 | 64% |
| Lebanon | medium | 31 | 596 | 0 | 47.4 | 32% |
| Taiwan | medium | 31 | 5 | 7 | 31.2 | 72% |
| Belgium | medium | 30 | 113 | 18 | 44.4 | 36% |
| Chile | medium | 29 | 71 | 4 | 33.3 | 68% |
| South Africa | medium | 28 | 606 | 1 | 41.7 | 36% |
| Egypt | medium | 26 | 205 | 2 | 35.1 | 44% |
| Peru | medium | 24 | 98 | 11 | 42.2 | 44% |
| Romania | medium | 24 | 0 | 4 | 25.7 | 86% |
| Algeria | medium | 23 | 11 | 1 | 18.8 | 95% |
| Austria | medium | 23 | 101 | 9 | 40.0 | 60% |
| Cuba | medium | 23 | 397 | 0 | 41.2 | 50% |
| Denmark | medium | 23 | 258 | 14 | 42.3 | 33% |
| Ireland | medium | 23 | 711 | 7 | 51.5 | 18% |
| Georgia | medium | 22 | 0 | 4 | 25.0 | 82% |
| Morocco | medium | 22 | 1,592 | 0 | 35.9 | 55% |
| Ukraine | medium | 22 | 6 | 0 | 31.2 | 62% |
| Colombia | medium | 21 | 70 | 2 | 35.0 | 59% |
| Myanmar | medium | 20 | 0 | 2 | 33.6 | 58% |
| Singapore | medium | 20 | 0 | 1 | 33.2 | 55% |
| Palestine | medium | 19 | 51 | 0 | 37.9 | 56% |
| Armenia | medium | 18 | 3 | 2 | 24.6 | 75% |
| Croatia | medium | 18 | 8 | 1 | 25.4 | 76% |
| Cambodia | medium | 16 | 53 | 2 | 24.5 | 80% |
| Israel | medium | 16 | 0 | 3 | 33.3 | 67% |
| New Zealand | medium | 16 | 384 | 0 | 32.3 | 50% |
| Iraq | medium | 15 | 66 | 2 | 34.5 | 55% |
| Bulgaria | low | 14 | 7 | 2 | 31.2 | 83% |

## Remediation plan

Enrich before adding: the countries with 20+ dishes and the lowest average score are Algeria (18.8), Georgia (25.0), Nigeria (25.6), Romania (25.7), Portugal (29.7), Iran (30.9), Finland (31.0), Taiwan (31.2), Ukraine (31.2), Brazil (33.0). Their dishes gain most from photos (`scripts/dish_photos/`) and stories (`fetch_knowledge.py --stories`); new dishes come after, from `coverage/next_500.json`.
