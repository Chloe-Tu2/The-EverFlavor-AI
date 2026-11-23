# World culinary coverage (2026-11-22)

How well each food tradition is represented, the headline metric from 2026-11-22 (decided by med27-coder): dish and recipe counts are secondary. Built by `scripts/knowledge/culinary_coverage.py`; per country: `data/knowledge/atlas/culinary_coverage.json`. **Audit only.**

**Level 1**, five checks: three representative dishes; a dish family; a cuisine description; a food history; regional styles (where it has culinary regions). **Level 2:** the share of its culinary regions that hold a dish. **Level 3:** the share of its dish families' known members we have. **Coverage** = 60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3, averaged over the counted countries (CLDR, 100,000 people or more: a proposed rule).

**World culinary coverage: 24.7%.** 50 of 200 counted countries meet level 1; 53 have at least one dish.

## By continent

| Continent | Counted countries | With a dish | Level 1 met | Coverage |
|---|---:|---:|---:|---:|
| Africa | 57 | 4 | 4 | 6.9% |
| Americas | 39 | 10 | 10 | 23.8% |
| Asia | 51 | 17 | 15 | 30.8% |
| Europe | 41 | 20 | 20 | 45.5% |
| Oceania | 12 | 2 | 1 | 14.7% |

## By subregion

| Continent / subregion | Counted countries | With a dish | Level 1 met | Coverage |
|---|---:|---:|---:|---:|
| Africa / Middle Africa | 9 | 0 | 0 | 0.0% |
| Africa / Western Africa | 16 | 0 | 0 | 0.0% |
| Asia / Central Asia | 5 | 0 | 0 | 0.0% |
| Oceania / Melanesia | 5 | 0 | 0 | 0.0% |
| Oceania / Micronesian Region | 2 | 0 | 0 | 0.0% |
| Oceania / Polynesia | 3 | 0 | 0 | 0.0% |
| Africa / Eastern Africa | 20 | 1 | 1 | 5.0% |
| Americas / Central America | 8 | 1 | 1 | 10.9% |
| Americas / Caribbean | 16 | 2 | 2 | 12.5% |
| Africa / Southern Africa | 5 | 1 | 1 | 19.9% |
| Asia / Western Asia | 18 | 5 | 4 | 26.5% |
| Africa / Northern Africa | 7 | 2 | 2 | 28.1% |
| Europe / Southern Europe | 13 | 4 | 4 | 29.4% |
| Asia / Southern Asia | 9 | 3 | 3 | 29.9% |
| Asia / Eastern Asia | 8 | 3 | 3 | 35.0% |
| Americas / South America | 13 | 5 | 5 | 36.5% |
| Europe / Eastern Europe | 10 | 4 | 4 | 38.7% |
| Asia / Southeast Asia | 11 | 6 | 5 | 49.7% |
| Europe / Northern Europe | 11 | 6 | 6 | 50.8% |
| Europe / Western Europe | 7 | 6 | 6 | 76.9% |
| Americas / Northern America | 2 | 2 | 2 | 84.1% |
| Oceania / Australasia | 2 | 2 | 1 | 88.2% |

## What keeps countries with dishes below level 1

| Missing | Countries |
|---|---:|
| three representative dishes | 3 |
| a food history | 1 |

## Africa, country by country (the first sprint)

| Country | Subregion | Dishes | Recipes | Score | Missing |
|---|---:|---:|---:|---:|---:|
| Ethiopia | Eastern Africa | 10 | 78 | 100.0 | none |
| Morocco | Northern Africa | 20 | 1,592 | 100.0 | none |
| South Africa | Southern Africa | 28 | 606 | 99.3 | none |
| Egypt | Northern Africa | 15 | 205 | 96.7 | none |
| Algeria | Northern Africa | 0 | 11 | 0.0 | no dish page yet |
| Angola | Middle Africa | 0 | 10 | 0.0 | no dish page yet |
| Botswana | Southern Africa | 0 | 6 | 0.0 | no dish page yet |
| Congo | Middle Africa | 0 | 7 | 0.0 | no dish page yet |
| Kenya | Eastern Africa | 0 | 4 | 0.0 | no dish page yet |
| Libya | Northern Africa | 0 | 17 | 0.0 | no dish page yet |
| Namibia | Southern Africa | 0 | 4 | 0.0 | no dish page yet |
| Nigeria | Western Africa | 0 | 32 | 0.0 | no dish page yet |
| Somalia | Eastern Africa | 0 | 9 | 0.0 | no dish page yet |
| Sudan | Northern Africa | 0 | 12 | 0.0 | no dish page yet |
| Tunisia | Northern Africa | 0 | 7 | 0.0 | no dish page yet |

No dish and no recipe yet (42): Benin, Burkina Faso, Burundi, Cameroon, Cape Verde, Central African Republic, Chad, Comoros, Democratic Republic of the Congo, Djibouti, Equatorial Guinea, Eritrea, Eswatini, Gabon, Ghana, Guinea, Guinea-Bissau, Ivory Coast, Lesotho, Liberia, Madagascar, Malawi, Mali, Mauritania, Mauritius, Mayotte, Mozambique, Niger, Rwanda, Réunion, Senegal, Seychelles, Sierra Leone, South Sudan, São Tomé and Príncipe, Tanzania, The Gambia, Togo, Uganda, Western Sahara, Zambia, Zimbabwe.
