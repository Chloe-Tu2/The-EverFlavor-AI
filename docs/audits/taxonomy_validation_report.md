# Taxonomy validation (2026-11-23)

The Food Taxonomy (`data/reference/food_taxonomy.csv`) checked against the UN's regions (Unicode CLDR, see the atlas) and against what the Food Graph attaches to it. A food region may differ from the UN's on purpose, so differences are listed for a person to look at; nothing is changed here. Data: `data/knowledge/quality/taxonomy_validation.json` (`scripts/knowledge/taxonomy_validation.py`).

## Structure

Valid: 267 places (1 world, 8 zone, 30 region, 205 country, 5 division, 17 state, 1 culinary_region), every parent known, every level under an allowed one, no loops (`load_taxonomy` refuses a table that breaks these).
Countries whose name has no ISO code in our country list: none.

## Zones against the UN continents

- Cyprus: our Europe, the UN's Asia

## Regions against the UN subregions

Each of our regions is compared with the closest UN subregions (Central Europe with Western and Eastern Europe, the Persian Region with Southern and Central Asia). A difference is often a food choice, not an error.

- Serbia: our Eastern Europe, the UN's Southern Europe
- North Macedonia: our Eastern Europe, the UN's Southern Europe
- Slovenia: our Central Europe, the UN's Southern Europe
- Cyprus: our Mediterranean Europe, the UN's Western Asia

## Countries with dishes or recipes that the taxonomy lacks

These cannot be placed on the map or in discovery until a node is added (from a published source):

None: every country with a dish or a recipe has a node.

## Culinary regions below a country

States, divisions and culinary regions, with the dishes placed there (Wikidata origin or the Wikipedia cuisine list) and the recipes whose source labels name them:

| Place | Level | Country | Dishes | Recipes |
|---|---|---|---:|---:|
| Pacific Northwest | culinary_region | United States | 0 | 387 |
| Midwestern US | division | United States | 51 | 1790 |
| Northeastern US | division | United States | 32 | 1131 |
| Southern US | division | United States | 0 | 3102 |
| Southwestern US | division | United States | 46 | 1205 |
| West Coast | division | United States | 0 | 0 |
| British Columbia | state | Canada | 0 | 405 |
| Ontario | state | Canada | 0 | 498 |
| Quebec | state | Canada | 34 | 79 |
| Beijing | state | China | 33 | 13 |
| Guangdong | state | China | 68 | 54 |
| Hunan | state | China | 5 | 21 |
| Sichuan | state | China | 15 | 77 |
| Baja California | state | Mexico | 0 | 74 |
| Oaxaca | state | Mexico | 8 | 42 |
| England | state | United Kingdom | 13 | 930 |
| Scotland | state | United Kingdom | 81 | 228 |
| Wales | state | United Kingdom | 1 | 58 |
| California | state | United States | 0 | 552 |
| Hawaii | state | United States | 13 | 314 |
| Louisiana | state | United States | 58 | 1083 |
| Pennsylvania | state | United States | 32 | 229 |
| Texas | state | United States | 0 | 930 |

1 of 23 hold nothing directly (a division may still hold its states and culinary regions): West Coast.

Countries with no dish and no recipe yet (26): American Samoa, Burundi, Comoros, Cook Islands, Equatorial Guinea, Eswatini, Federated States of Micronesia, Fiji, French Polynesia, Gabon, Guinea-Bissau, Kiribati, Lesotho, Liberia, Martinique, Nauru, Niue, Palau, Papua New Guinea, Qatar, Saint Kitts and Nevis, Saint Vincent and the Grenadines, Solomon Islands, São Tomé and Príncipe, Timor-Leste, Zimbabwe.
