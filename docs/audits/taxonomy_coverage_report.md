# Taxonomy completeness (2026-11-23)

How much of the place tree (`data/reference/food_taxonomy.csv`, World down to a culinary region) holds dishes and recipes. Per node: `data/knowledge/quality/taxonomy_coverage.json`.

| Level | Nodes | With dishes | Without dishes |
|---|---:|---:|---:|
| world | 1 | 1 | 0 |
| zone | 8 | 8 | 0 |
| region | 30 | 30 | 0 |
| country | 205 | 148 | 57 |
| division | 5 | 3 | 2 |
| state | 17 | 12 | 5 |
| culinary_region | 1 | 0 | 1 |

## Nodes without a dish

Southern US (division, 4,322 recipes), Texas (state, 1,353 recipes), California (state, 691 recipes), Ontario (state, 631 recipes), British Columbia (state, 542 recipes), Pacific Northwest (culinary_region, 506 recipes), Baja California (state, 131 recipes), Dominica (country, 15 recipes), Congo (country, 7 recipes), Cayman Islands (country, 7 recipes), Aruba (country, 6 recipes), Barbados (country, 6 recipes), Syria (country, 5 recipes), Namibia (country, 4 recipes), Andorra (country, 3 recipes), Jordan (country, 0 recipes), Oman (country, 0 recipes), Qatar (country, 0 recipes), Kuwait (country, 0 recipes), West Coast (division, 0 recipes), Mali (country, 0 recipes), Burkina Faso (country, 0 recipes), Guinea (country, 0 recipes), Guinea-Bissau (country, 0 recipes), Liberia (country, 0 recipes), Sierra Leone (country, 0 recipes), Togo (country, 0 recipes), Mauritania (country, 0 recipes), Gabon (country, 0 recipes), Equatorial Guinea (country, 0 recipes), São Tomé and Príncipe (country, 0 recipes), Burundi (country, 0 recipes), Eritrea (country, 0 recipes), Djibouti (country, 0 recipes), Comoros (country, 0 recipes), Zimbabwe (country, 0 recipes), Lesotho (country, 0 recipes), Eswatini (country, 0 recipes), Fiji (country, 0 recipes), Papua New Guinea (country, 0 recipes), Solomon Islands (country, 0 recipes), Vanuatu (country, 0 recipes), Samoa (country, 0 recipes), Kiribati (country, 0 recipes), Panama (country, 0 recipes), Tuvalu (country, 0 recipes), Nauru (country, 0 recipes), Marshall Islands (country, 0 recipes), Palau (country, 0 recipes), Federated States of Micronesia (country, 0 recipes), Cook Islands (country, 0 recipes), Niue (country, 0 recipes), French Polynesia (country, 0 recipes), Northern Mariana Islands (country, 0 recipes), American Samoa (country, 0 recipes), Belarus (country, 0 recipes), Montenegro (country, 0 recipes), Timor-Leste (country, 0 recipes), Grenada (country, 0 recipes), Saint Lucia (country, 0 recipes), Saint Vincent and the Grenadines (country, 0 recipes), Saint Kitts and Nevis (country, 0 recipes), Curaçao (country, 0 recipes), Guadeloupe (country, 0 recipes), Martinique (country, 0 recipes).

Every dish's country is in the tree: yes.

## Remediation plan

1. Countries in the tree with recipes but no dish (Puerto Rico, Venezuela, Iceland...) need their Wikipedia cuisine list in the knowledge notebook, the same way the 54 countries were read.
2. States without dishes (Texas, California, the Southern US) have recipes (their own origin_region) but no dish placed there; their Wikipedia cuisine pages would place dishes, as for China and Mexico.
3. New levels are added only where a published source draws them (the planner's rule): the coverage audit lists the Balkans, India's states and Siberia as asked for but not drawn yet.
