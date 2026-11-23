# Taxonomy completeness (2026-11-23)

How much of the place tree (`data/reference/food_taxonomy.csv`, World down to a culinary region) holds dishes and recipes. Per node: `data/knowledge/quality/taxonomy_coverage.json`.

| Level | Nodes | With dishes | Without dishes |
|---|---:|---:|---:|
| world | 1 | 1 | 0 |
| zone | 8 | 8 | 0 |
| region | 30 | 26 | 4 |
| country | 160 | 90 | 70 |
| division | 5 | 3 | 2 |
| state | 17 | 12 | 5 |
| culinary_region | 1 | 0 | 1 |

## Nodes without a dish

Southern US (division, 4,322 recipes), Texas (state, 1,353 recipes), California (state, 691 recipes), Ontario (state, 631 recipes), British Columbia (state, 542 recipes), Pacific Northwest (culinary_region, 506 recipes), Baja California (state, 131 recipes), Costa Rica (country, 43 recipes), Venezuela (country, 42 recipes), Ecuador (country, 35 recipes), Iceland (country, 34 recipes), Nepal (country, 33 recipes), Laos (country, 18 recipes), Dominica (country, 15 recipes), Sudan (country, 12 recipes), Albania (country, 11 recipes), Honduras (country, 10 recipes), Croatia (country, 8 recipes), Uruguay (country, 7 recipes), Afghanistan (country, 7 recipes), Congo (country, 7 recipes), Bulgaria (country, 7 recipes), Cayman Islands (country, 7 recipes), Ukraine (country, 6 recipes), Aruba (country, 6 recipes), Caucasus (region, 5 recipes), Taiwan (country, 5 recipes), Syria (country, 5 recipes), Kenya (country, 4 recipes), Namibia (country, 4 recipes), Slovakia (country, 4 recipes), Baltic States (region, 3 recipes), Estonia (country, 3 recipes), Bangladesh (country, 3 recipes), Armenia (country, 3 recipes), Andorra (country, 3 recipes), Antigua and Barbuda (country, 3 recipes), Azerbaijan (country, 2 recipes), Melanesia (region, 0 recipes), Micronesia (region, 0 recipes), Israel (country, 0 recipes), Jordan (country, 0 recipes), Yemen (country, 0 recipes), Oman (country, 0 recipes), United Arab Emirates (country, 0 recipes), Qatar (country, 0 recipes), Kuwait (country, 0 recipes), Bahrain (country, 0 recipes), Georgia (country, 0 recipes), West Coast (division, 0 recipes), Mali (country, 0 recipes), Burkina Faso (country, 0 recipes), Guinea (country, 0 recipes), Guinea-Bissau (country, 0 recipes), Liberia (country, 0 recipes), Sierra Leone (country, 0 recipes), Togo (country, 0 recipes), Mauritania (country, 0 recipes), Gabon (country, 0 recipes), Central African Republic (country, 0 recipes), Equatorial Guinea (country, 0 recipes), São Tomé and Príncipe (country, 0 recipes), Burundi (country, 0 recipes), Eritrea (country, 0 recipes), Djibouti (country, 0 recipes), Madagascar (country, 0 recipes), Comoros (country, 0 recipes), Zambia (country, 0 recipes), Zimbabwe (country, 0 recipes), Lesotho (country, 0 recipes), Eswatini (country, 0 recipes), Fiji (country, 0 recipes), Papua New Guinea (country, 0 recipes), Solomon Islands (country, 0 recipes), Vanuatu (country, 0 recipes), Samoa (country, 0 recipes), Kiribati (country, 0 recipes), The Bahamas (country, 0 recipes), Panama (country, 0 recipes), Kyrgyzstan (country, 0 recipes), Tajikistan (country, 0 recipes), Turkmenistan (country, 0 recipes).

Every dish's country is in the tree: yes.

## Remediation plan

1. Countries in the tree with recipes but no dish (Puerto Rico, Venezuela, Iceland...) need their Wikipedia cuisine list in the knowledge notebook, the same way the 54 countries were read.
2. States without dishes (Texas, California, the Southern US) have recipes (their own origin_region) but no dish placed there; their Wikipedia cuisine pages would place dishes, as for China and Mexico.
3. New levels are added only where a published source draws them (the planner's rule): the coverage audit lists the Balkans, India's states and Siberia as asked for but not drawn yet.
