# World culinary coverage (2026-11-25)

How well each food tradition is represented, the headline metric from 2026-11-22 (decided by med27-coder): dish and recipe counts are secondary. Built by `scripts/knowledge/culinary_coverage.py`; per country: `data/knowledge/atlas/culinary_coverage.json`. **Audit only.**

**Level 1**, five checks: three representative dishes; a dish family; a cuisine description; a food history; regional styles (where it has culinary regions). **Level 2:** the share of its culinary regions that hold a dish. **Level 3:** the share of its dish families' known members we have. **Coverage** = 60 x level-1 checks met / 5 + 20 x level 2 + 20 x level 3 (a country with no culinary regions in the place tree: the other levels out of 80, scaled to 100), averaged over the counted countries (CLDR, 100,000 people or more: a proposed rule).

**World culinary coverage: 70.6%.** 117 of 200 counted countries meet level 1; 165 have at least one dish.

## By continent

| Continent | Counted countries | With a dish | Level 1 met | Coverage |
|---|---:|---:|---:|---:|
| Africa | 57 | 40 | 18 | 54.5% |
| Americas | 39 | 35 | 22 | 73.4% |
| Asia | 51 | 45 | 39 | 81.2% |
| Europe | 41 | 39 | 35 | 87.8% |
| Oceania | 12 | 6 | 3 | 35.2% |

## By subregion

| Continent / subregion | Counted countries | With a dish | Level 1 met | Coverage |
|---|---:|---:|---:|---:|
| Oceania / Melanesia | 5 | 1 | 0 | 12.5% |
| Oceania / Polynesia | 3 | 2 | 0 | 22.9% |
| Africa / Southern Africa | 5 | 2 | 2 | 39.8% |
| Africa / Middle Africa | 9 | 6 | 1 | 45.8% |
| Oceania / Micronesian Region | 2 | 1 | 1 | 47.5% |
| Africa / Western Africa | 16 | 12 | 4 | 52.4% |
| Africa / Eastern Africa | 20 | 14 | 5 | 53.0% |
| Americas / Caribbean | 16 | 13 | 6 | 57.8% |
| Asia / Eastern Asia | 8 | 6 | 6 | 70.5% |
| Asia / Western Asia | 18 | 15 | 11 | 75.3% |
| Americas / Central America | 8 | 8 | 4 | 82.1% |
| Europe / Southern Europe | 13 | 12 | 10 | 83.3% |
| Americas / Northern America | 2 | 2 | 2 | 84.2% |
| Europe / Northern Europe | 11 | 10 | 9 | 84.4% |
| Africa / Northern Africa | 7 | 6 | 6 | 84.9% |
| Americas / South America | 13 | 12 | 10 | 85.6% |
| Asia / Central Asia | 5 | 5 | 4 | 88.2% |
| Asia / Southeast Asia | 11 | 10 | 10 | 88.9% |
| Asia / Southern Asia | 9 | 9 | 8 | 89.3% |
| Europe / Western Europe | 7 | 7 | 7 | 91.4% |
| Europe / Eastern Europe | 10 | 10 | 9 | 94.8% |
| Oceania / Australasia | 2 | 2 | 2 | 98.3% |

## What keeps countries with dishes below level 1

| Missing | Countries |
|---|---:|
| three representative dishes | 35 |
| a dish family | 27 |
| a food history | 23 |
| a cuisine description | 18 |

## Africa, country by country (the first sprint)

| Country | Subregion | Dishes | Recipes | Score | Missing |
|---|---:|---:|---:|---:|---:|
| Benin | Western Africa | 4 | 0 | 100.0 | none |
| Botswana | Southern Africa | 5 | 6 | 100.0 | none |
| Cameroon | Middle Africa | 8 | 0 | 100.0 | none |
| Ethiopia | Eastern Africa | 11 | 78 | 100.0 | none |
| Libya | Northern Africa | 4 | 17 | 100.0 | none |
| Madagascar | Eastern Africa | 4 | 0 | 100.0 | none |
| Mauritius | Eastern Africa | 3 | 0 | 100.0 | none |
| Morocco | Northern Africa | 22 | 1,592 | 100.0 | none |
| Senegal | Western Africa | 10 | 0 | 100.0 | none |
| Sudan | Northern Africa | 3 | 12 | 100.0 | none |
| South Africa | Southern Africa | 28 | 606 | 99.1 | none |
| Algeria | Northern Africa | 23 | 11 | 99.0 | none |
| Egypt | Northern Africa | 26 | 205 | 98.2 | none |
| Ghana | Western Africa | 9 | 0 | 97.5 | none |
| Tunisia | Northern Africa | 8 | 7 | 97.2 | none |
| Nigeria | Western Africa | 53 | 32 | 96.7 | none |
| Kenya | Eastern Africa | 5 | 4 | 95.8 | none |
| Uganda | Eastern Africa | 4 | 0 | 89.3 | none |
| Angola | Middle Africa | 3 | 10 | 81.2 | a dish family |
| Cape Verde | Western Africa | 1 | 0 | 81.2 | three representative dishes |
| Chad | Middle Africa | 3 | 0 | 81.2 | a food history |
| Eritrea | Eastern Africa | 4 | 0 | 81.2 | a cuisine description |
| Somalia | Eastern Africa | 4 | 9 | 81.2 | a food history |
| Tanzania | Eastern Africa | 3 | 0 | 75.0 | a dish family |
| Central African Republic | Middle Africa | 2 | 0 | 62.5 | three representative dishes; a dish family |
| Mali | Western Africa | 2 | 0 | 62.5 | three representative dishes; a cuisine description |
| Mozambique | Eastern Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| Niger | Western Africa | 2 | 0 | 62.5 | three representative dishes; a dish family |
| Rwanda | Eastern Africa | 1 | 0 | 62.5 | three representative dishes; a dish family |
| Seychelles | Eastern Africa | 3 | 0 | 62.5 | a dish family; a food history |
| South Sudan | Eastern Africa | 2 | 0 | 62.5 | three representative dishes; a food history |
| The Gambia | Western Africa | 1 | 0 | 62.5 | three representative dishes; a food history |
| Togo | Western Africa | 3 | 0 | 62.5 | a cuisine description; a food history |
| Congo | Middle Africa | 1 | 7 | 43.8 | three representative dishes; a dish family; a cuisine description |
| Democratic Republic of the Congo | Middle Africa | 2 | 0 | 43.8 | three representative dishes; a dish family; a cuisine description |
| Ivory Coast | Western Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Malawi | Eastern Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Sierra Leone | Western Africa | 1 | 0 | 43.8 | three representative dishes; a cuisine description; a food history |
| Zambia | Eastern Africa | 1 | 0 | 43.8 | three representative dishes; a dish family; a food history |
| Mauritania | Western Africa | 1 | 0 | 25.0 | three representative dishes; a dish family; a cuisine description; a food history |
| Namibia | Southern Africa | 0 | 4 | 0.0 | no dish page yet |

No dish and no recipe yet (16): Burkina Faso, Burundi, Comoros, Djibouti, Equatorial Guinea, Eswatini, Gabon, Guinea, Guinea-Bissau, Lesotho, Liberia, Mayotte, Réunion, São Tomé and Príncipe, Western Sahara, Zimbabwe.

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
