# Taxonomy validation (2026-11-22)

The Food Taxonomy (`data/reference/food_taxonomy.csv`) checked against the UN's regions (Unicode CLDR, see the atlas) and against what the Food Graph attaches to it. A food region may differ from the UN's on purpose, so differences are listed for a person to look at; nothing is changed here. Data: `data/knowledge/quality/taxonomy_validation.json` (`scripts/knowledge/taxonomy_validation.py`).

## Structure

Valid: 222 places (1 world, 8 zone, 30 region, 160 country, 5 division, 17 state, 1 culinary_region), every parent known, every level under an allowed one, no loops (`load_taxonomy` refuses a table that breaks these).
Countries whose name has no ISO code in our country list: none.

## Zones against the UN continents

Every country's zone matches its UN continent (MENA counts as Asia and Africa).

## Regions against the UN subregions

Each of our regions is compared with the closest UN subregions (Central Europe with Western and Eastern Europe, the Persian Region with Southern and Central Asia). A difference is often a food choice, not an error.

None: all 160 countries sit in a region that matches their UN subregion.

## Countries with dishes or recipes that the taxonomy lacks

These cannot be placed on the map or in discovery until a node is added (from a published source):

None: every country with a dish or a recipe has a node.

## Culinary regions below a country

States, divisions and culinary regions, with the dishes placed there (Wikidata origin or the Wikipedia cuisine list) and the recipes whose source labels name them:

| Place | Level | Country | Dishes | Recipes |
|---|---|---|---:|---:|
| Pacific Northwest | culinary_region | United States | 0 | 387 |
| Midwestern US | division | United States | 51 | 1791 |
| Northeastern US | division | United States | 32 | 1136 |
| Southern US | division | United States | 0 | 3101 |
| Southwestern US | division | United States | 45 | 1205 |
| West Coast | division | United States | 0 | 0 |
| British Columbia | state | Canada | 0 | 406 |
| Ontario | state | Canada | 0 | 499 |
| Quebec | state | Canada | 34 | 81 |
| Beijing | state | China | 33 | 13 |
| Guangdong | state | China | 68 | 54 |
| Hunan | state | China | 5 | 21 |
| Sichuan | state | China | 15 | 77 |
| Baja California | state | Mexico | 0 | 74 |
| Oaxaca | state | Mexico | 8 | 42 |
| England | state | United Kingdom | 13 | 932 |
| Scotland | state | United Kingdom | 81 | 228 |
| Wales | state | United Kingdom | 1 | 58 |
| California | state | United States | 0 | 553 |
| Hawaii | state | United States | 13 | 316 |
| Louisiana | state | United States | 58 | 1083 |
| Pennsylvania | state | United States | 32 | 229 |
| Texas | state | United States | 0 | 930 |

1 of 23 hold nothing directly (a division may still hold its states and culinary regions): West Coast.

Countries with no dish and no recipe yet (21): Bahrain, Burundi, Central African Republic, Comoros, Djibouti, Equatorial Guinea, Eswatini, Fiji, Gabon, Guinea-Bissau, Kiribati, Lesotho, Liberia, Papua New Guinea, Qatar, Solomon Islands, São Tomé and Príncipe, The Bahamas, Turkmenistan, Vanuatu, Zimbabwe.
