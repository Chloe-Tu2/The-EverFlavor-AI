# World culinary coverage (2026-11-23)

How well each food tradition is represented, the headline metric from 2026-11-22 (decided by med27-coder): dish and recipe counts are secondary. Built by `scripts/knowledge/culinary_coverage.py`; per country: `data/knowledge/atlas/culinary_coverage.json`. **Audit only.**

**Level 1**, five checks: three representative dishes; a dish family; a cuisine description; a food history; regional styles (where it has culinary regions). **Level 2:** the share of its culinary regions that hold a dish. **Level 3:** the share of its dish families' known members we have. **Coverage** = 60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3 (a country with no culinary regions in the place tree: the other levels out of 80, scaled to 100), averaged over the counted countries (CLDR, 100,000 people or more: a proposed rule).

**World culinary coverage: 60.4%.** 97 of 200 counted countries meet level 1; 148 have at least one dish.

## By continent

| Continent | Counted countries | With a dish | Level 1 met | Coverage |
|---|---:|---:|---:|---:|
| Africa | 57 | 34 | 10 | 41.0% |
| Americas | 39 | 29 | 20 | 60.3% |
| Asia | 51 | 43 | 33 | 72.9% |
| Europe | 41 | 37 | 33 | 81.7% |
| Oceania | 12 | 5 | 1 | 27.9% |

## By subregion

| Continent / subregion | Counted countries | With a dish | Level 1 met | Coverage |
|---|---:|---:|---:|---:|
| Oceania / Melanesia | 5 | 1 | 0 | 8.8% |
| Oceania / Polynesia | 3 | 1 | 0 | 14.6% |
| Africa / Southern Africa | 5 | 2 | 1 | 32.3% |
| Africa / Middle Africa | 9 | 5 | 1 | 32.6% |
| Africa / Western Africa | 16 | 8 | 2 | 33.2% |
| Oceania / Micronesian Region | 2 | 1 | 0 | 38.1% |
| Americas / Caribbean | 16 | 8 | 5 | 39.8% |
| Africa / Eastern Africa | 20 | 13 | 2 | 41.0% |
| Asia / Western Asia | 18 | 13 | 9 | 62.6% |
| Americas / Central America | 8 | 7 | 4 | 63.3% |
| Asia / Eastern Asia | 8 | 6 | 6 | 70.0% |
| Asia / Central Asia | 5 | 5 | 2 | 71.4% |
| Africa / Northern Africa | 7 | 6 | 4 | 75.6% |
| Europe / Northern Europe | 11 | 10 | 8 | 78.9% |
| Europe / Southern Europe | 13 | 11 | 10 | 79.6% |
| Americas / South America | 13 | 12 | 9 | 79.9% |
| Asia / Southeast Asia | 11 | 10 | 8 | 80.1% |
| Europe / Eastern Europe | 10 | 9 | 8 | 82.3% |
| Americas / Northern America | 2 | 2 | 2 | 84.1% |
| Oceania / Australasia | 2 | 2 | 1 | 85.7% |
| Asia / Southern Asia | 9 | 9 | 8 | 88.1% |
| Europe / Western Europe | 7 | 7 | 7 | 89.0% |

## What keeps countries with dishes below level 1

| Missing | Countries |
|---|---:|
| three representative dishes | 44 |
| a food history | 37 |
| a dish family | 31 |
| a cuisine description | 1 |

## Africa, country by country (the first sprint)

| Country | Subregion | Dishes | Recipes | Score | Missing |
|---|---:|---:|---:|---:|---:|
| Cameroon | Middle Africa | 7 | 0 | 100.0 | none |
| Ethiopia | Eastern Africa | 10 | 78 | 100.0 | none |
| Madagascar | Eastern Africa | 4 | 0 | 100.0 | none |
| Morocco | Northern Africa | 20 | 1,592 | 100.0 | none |
| Senegal | Western Africa | 8 | 0 | 100.0 | none |
| South Africa | Southern Africa | 28 | 606 | 99.1 | none |
| Egypt | Northern Africa | 16 | 205 | 97.2 | none |
| Nigeria | Western Africa | 50 | 32 | 96.5 | none |
| Algeria | Northern Africa | 11 | 11 | 94.7 | none |
| Tunisia | Northern Africa | 6 | 7 | 93.8 | none |
| Angola | Middle Africa | 3 | 10 | 81.2 | a dish family |
| Mauritius | Eastern Africa | 2 | 0 | 81.2 | three representative dishes |
| Somalia | Eastern Africa | 3 | 9 | 81.2 | a food history |
| Sudan | Northern Africa | 1 | 12 | 81.2 | three representative dishes |
| Ghana | Western Africa | 6 | 0 | 77.7 | a food history |
| Uganda | Eastern Africa | 3 | 0 | 68.8 | a dish family |
| Botswana | Southern Africa | 4 | 6 | 62.5 | a dish family; a food history |
| Cape Verde | Western Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| Libya | Northern Africa | 2 | 17 | 62.5 | three representative dishes; a food history |
| Mozambique | Eastern Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| Seychelles | Eastern Africa | 3 | 0 | 62.5 | a dish family; a food history |
| South Sudan | Eastern Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| The Gambia | Western Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| Benin | Western Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Central African Republic | Middle Africa | 2 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Chad | Middle Africa | 2 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Ivory Coast | Western Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Malawi | Eastern Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Niger | Western Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Rwanda | Eastern Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Zambia | Eastern Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Kenya | Eastern Africa | 2 | 4 | 35.4 | three representative dishes; a dish family; a food history |
| Tanzania | Eastern Africa | 2 | 0 | 35.4 | three representative dishes; a dish family; a food history |
| Democratic Republic of the Congo | Middle Africa | 1 | 0 | 25.0 | three representative dishes; a dish family; a cuisine description; a food history |
| Congo | Middle Africa | 0 | 7 | 0.0 | no dish page yet |
| Namibia | Southern Africa | 0 | 4 | 0.0 | no dish page yet |

No dish and no recipe yet (21): Burkina Faso, Burundi, Comoros, Djibouti, Equatorial Guinea, Eritrea, Eswatini, Gabon, Guinea, Guinea-Bissau, Lesotho, Liberia, Mali, Mauritania, Mayotte, Réunion, Sierra Leone, São Tomé and Príncipe, Togo, Western Sahara, Zimbabwe.

## Indigenous food traditions (sprint 2)

A dish or food is tagged with a tradition only when that tradition's Wikipedia page lists it and its own intro names the people (`fetch_knowledge.INDIGENOUS_PAGES`); never guessed. A person reviews the tags (`docs/governance/needs_human_review.md`).

| Tradition | Dishes and foods | Examples |
|---|---:|---:|
| Aboriginal Australian | 3 | Bush bread, Bush tomato, Witchetty grub |
| Chamorro | 3 | Fina'denne', Guyuria, Kelaguen |
| Inuit | 2 | Bannock (Indigenous American food), Muktuk |
| Māori | 5 | Boil up, Kānga pirau, Kānga waru, Pāua, Rēwena bread |
| Native American | 14 | Bammy, Bannock (Indigenous American food), Casabe, Cauim, Colada morada, Frybread |
| Native Hawaiian | 3 | Haupia, Inamona, Kūlolo |
