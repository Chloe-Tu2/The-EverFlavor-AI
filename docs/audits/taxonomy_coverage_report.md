# Taxonomy completeness (2026-11-22)

How much of the place tree (`data/reference/food_taxonomy.csv`, World down to a culinary region) holds dishes and recipes. Per node: `data/knowledge/quality/taxonomy_coverage.json`.

| Level | Nodes | With dishes | Without dishes |
|---|---:|---:|---:|
| world | 1 | 1 | 0 |
| zone | 8 | 8 | 0 |
| region | 26 | 22 | 4 |
| country | 92 | 53 | 39 |
| division | 5 | 3 | 2 |
| state | 17 | 12 | 5 |
| culinary_region | 1 | 0 | 1 |

## Nodes without a dish

Southern US (division, 4,322 recipes), Texas (state, 1,353 recipes), California (state, 691 recipes), Ontario (state, 631 recipes), British Columbia (state, 542 recipes), Pacific Northwest (culinary_region, 506 recipes), Baja California (state, 131 recipes), Puerto Rico (country, 71 recipes), Costa Rica (country, 43 recipes), Venezuela (country, 42 recipes), Ecuador (country, 35 recipes), Iceland (country, 34 recipes), Nepal (country, 33 recipes), West Africa (region, 32 recipes), Nigeria (country, 32 recipes), Guatemala (country, 24 recipes), Laos (country, 18 recipes), Central Africa (region, 17 recipes), Libya (country, 17 recipes), Dominica (country, 15 recipes), Sudan (country, 12 recipes), Algeria (country, 11 recipes), Albania (country, 11 recipes), Honduras (country, 10 recipes), Angola (country, 10 recipes), Somalia (country, 9 recipes), Croatia (country, 8 recipes), Uruguay (country, 7 recipes), Afghanistan (country, 7 recipes), Congo (country, 7 recipes), Tunisia (country, 7 recipes), Bulgaria (country, 7 recipes), Cayman Islands (country, 7 recipes), Botswana (country, 6 recipes), Ukraine (country, 6 recipes), Aruba (country, 6 recipes), Barbados (country, 6 recipes), Caucasus (region, 5 recipes), Taiwan (country, 5 recipes), Syria (country, 5 recipes), Kenya (country, 4 recipes), Namibia (country, 4 recipes), Slovakia (country, 4 recipes), Baltic States (region, 3 recipes), Estonia (country, 3 recipes), Bangladesh (country, 3 recipes), Armenia (country, 3 recipes), Andorra (country, 3 recipes), Antigua and Barbuda (country, 3 recipes), Azerbaijan (country, 2 recipes), West Coast (division, 0 recipes).

Every dish's country is in the tree: yes.

## Remediation plan

1. Countries in the tree with recipes but no dish (Puerto Rico, Venezuela, Iceland...) need their Wikipedia cuisine list in the knowledge notebook, the same way the 54 countries were read.
2. States without dishes (Texas, California, the Southern US) have recipes (their own origin_region) but no dish placed there; their Wikipedia cuisine pages would place dishes, as for China and Mexico.
3. New levels are added only where a published source draws them (the planner's rule): the coverage audit lists the Balkans, India's states and Siberia as asked for but not drawn yet.
