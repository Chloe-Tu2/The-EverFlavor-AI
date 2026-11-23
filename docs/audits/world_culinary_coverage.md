# World culinary coverage (2026-11-22)

How well each food tradition is represented, the headline metric from 2026-11-22 (decided by med27-coder): dish and recipe counts are secondary. Built by `scripts/knowledge/culinary_coverage.py`; per country: `data/knowledge/atlas/culinary_coverage.json`. **Audit only.**

**Level 1**, five checks: three representative dishes; a dish family; a cuisine description; a food history; regional styles (where it has culinary regions). **Level 2:** the share of its culinary regions that hold a dish. **Level 3:** the share of its dish families' known members we have. **Coverage** = 60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3 (a country with no culinary regions in the place tree: the other levels out of 80, scaled to 100), averaged over the counted countries (CLDR, 100,000 people or more: a proposed rule).

**World culinary coverage: 36.3%.** 60 of 200 counted countries meet level 1; 90 have at least one dish.

## By continent

| Continent | Counted countries | With a dish | Level 1 met | Coverage |
|---|---:|---:|---:|---:|
| Africa | 57 | 29 | 9 | 33.7% |
| Americas | 39 | 19 | 14 | 41.4% |
| Asia | 51 | 19 | 16 | 32.9% |
| Europe | 41 | 20 | 20 | 44.8% |
| Oceania | 12 | 3 | 1 | 17.6% |

## By subregion

| Continent / subregion | Counted countries | With a dish | Level 1 met | Coverage |
|---|---:|---:|---:|---:|
| Oceania / Melanesia | 5 | 0 | 0 | 0.0% |
| Oceania / Micronesian Region | 2 | 0 | 0 | 0.0% |
| Oceania / Polynesia | 3 | 1 | 0 | 14.6% |
| Africa / Southern Africa | 5 | 2 | 1 | 24.8% |
| Asia / Western Asia | 18 | 5 | 4 | 26.0% |
| Africa / Middle Africa | 9 | 4 | 1 | 27.8% |
| Africa / Eastern Africa | 20 | 10 | 1 | 28.6% |
| Asia / Central Asia | 5 | 2 | 1 | 28.8% |
| Europe / Southern Europe | 13 | 4 | 4 | 29.0% |
| Asia / Southern Asia | 9 | 3 | 3 | 29.3% |
| Africa / Western Africa | 16 | 8 | 2 | 31.9% |
| Asia / Eastern Asia | 8 | 3 | 3 | 34.5% |
| Americas / Caribbean | 16 | 7 | 4 | 36.1% |
| Americas / South America | 13 | 5 | 5 | 36.1% |
| Europe / Eastern Europe | 10 | 4 | 4 | 38.3% |
| Asia / Southeast Asia | 11 | 6 | 5 | 47.9% |
| Americas / Central America | 8 | 5 | 3 | 50.0% |
| Europe / Northern Europe | 11 | 6 | 6 | 50.2% |
| Africa / Northern Africa | 7 | 5 | 4 | 65.8% |
| Europe / Western Europe | 7 | 6 | 6 | 74.7% |
| Oceania / Australasia | 2 | 2 | 1 | 83.4% |
| Americas / Northern America | 2 | 2 | 2 | 84.1% |

## What keeps countries with dishes below level 1

| Missing | Countries |
|---|---:|
| three representative dishes | 25 |
| a food history | 22 |
| a dish family | 17 |
| a cuisine description | 3 |

## Africa, country by country (the first sprint)

| Country | Subregion | Dishes | Recipes | Score | Missing |
|---|---:|---:|---:|---:|---:|
| Cameroon | Middle Africa | 7 | 0 | 100.0 | none |
| Ethiopia | Eastern Africa | 10 | 78 | 100.0 | none |
| Libya | Northern Africa | 3 | 17 | 100.0 | none |
| Morocco | Northern Africa | 20 | 1,592 | 100.0 | none |
| Senegal | Western Africa | 8 | 0 | 100.0 | none |
| South Africa | Southern Africa | 28 | 606 | 99.1 | none |
| Nigeria | Western Africa | 50 | 32 | 97.3 | none |
| Egypt | Northern Africa | 15 | 205 | 95.8 | none |
| Tunisia | Northern Africa | 6 | 7 | 93.8 | none |
| Angola | Middle Africa | 3 | 10 | 81.2 | a dish family |
| Ghana | Western Africa | 4 | 0 | 76.2 | a food history |
| Algeria | Northern Africa | 6 | 11 | 71.2 | a food history |
| Uganda | Eastern Africa | 3 | 0 | 68.8 | a dish family |
| Cape Verde | Western Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| Mozambique | Eastern Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| Seychelles | Eastern Africa | 3 | 0 | 62.5 | a dish family; a food history |
| Somalia | Eastern Africa | 2 | 9 | 62.5 | three representative dishes; a food history |
| South Sudan | Eastern Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| The Gambia | Western Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| Benin | Western Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Chad | Middle Africa | 2 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Mauritius | Eastern Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Niger | Western Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Rwanda | Eastern Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Tanzania | Eastern Africa | 2 | 0 | 35.4 | three representative dishes; a dish family; a food history |
| Malawi | Eastern Africa | 1 | 0 | 31.2 | three representative dishes; a dish family; a food history |
| Botswana | Southern Africa | 1 | 6 | 25.0 | three representative dishes; a dish family; a cuisine description; a food history |
| Democratic Republic of the Congo | Middle Africa | 1 | 0 | 25.0 | three representative dishes; a dish family; a cuisine description; a food history |
| Ivory Coast | Western Africa | 1 | 0 | 25.0 | three representative dishes; a dish family; a cuisine description; a food history |
| Congo | Middle Africa | 0 | 7 | 0.0 | no dish page yet |
| Kenya | Eastern Africa | 0 | 4 | 0.0 | no dish page yet |
| Namibia | Southern Africa | 0 | 4 | 0.0 | no dish page yet |
| Sudan | Northern Africa | 0 | 12 | 0.0 | no dish page yet |

No dish and no recipe yet (24): Burkina Faso, Burundi, Central African Republic, Comoros, Djibouti, Equatorial Guinea, Eritrea, Eswatini, Gabon, Guinea, Guinea-Bissau, Lesotho, Liberia, Madagascar, Mali, Mauritania, Mayotte, Réunion, Sierra Leone, São Tomé and Príncipe, Togo, Western Sahara, Zambia, Zimbabwe.
