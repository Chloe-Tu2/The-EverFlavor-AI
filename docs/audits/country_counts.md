# Country counts (2026-11-24)

How many countries EverFlavor covers depends on what counts as a country. Coverage uses one list (our count); most atlases use the UN's (the usual count). Both are shown so the numbers can be checked. From `scripts/knowledge/country_counts.py`; numbers update on every run. **Audit only.**

## The two counts

| Count | What it includes | Places | With a dish |
|---|---:|---:|---:|
| Our coverage count | Unicode CLDR countries and territories of 100,000 people or more | 200 | 165 |
| UN member states | the 193 members | 193 | 160 |
| UN members and observers | the usual 195: members, Palestine and Vatican City | 195 | 161 |

Other common totals: 197 (also Kosovo, the Cook Islands and Niue, without Palestine), 198 (also Taiwan), 199 (also Western Sahara). The counting rule is review item 21 in [needs_human_review.md](../governance/needs_human_review.md).

## Where the two lists differ

**In our count, not among the 195 (17):** territories and partly recognised places (marked when they have no dish): Aruba (no dish), Curaçao, French Guiana (no dish), French Polynesia (no dish), Guadeloupe, Guam, Hong Kong (no dish), Jersey (no dish), Kosovo (no dish), Macau (no dish), Martinique (no dish), Mayotte (no dish), New Caledonia, Puerto Rico, Réunion (no dish), Taiwan, Western Sahara (no dish).

**Among the 195, not in our count (12):** states under 100,000 people (marked when they have a dish). Andorra (has a dish), Dominica (has a dish), Federated States of Micronesia, Liechtenstein, Marshall Islands, Monaco, Nauru, Palau, Saint Kitts and Nevis, San Marino, Tuvalu, Vatican City.

## UN member states with no dish yet

33 of 193: Burkina Faso, Burundi, Comoros, Djibouti, Equatorial Guinea, Eswatini, Federated States of Micronesia, Fiji, Gabon, Guinea, Guinea-Bissau, Kiribati, Kuwait, Lesotho, Liberia, Liechtenstein, Marshall Islands, Monaco, Namibia, Nauru, Oman, Palau, Papua New Guinea, Qatar, Saint Kitts and Nevis, Saint Vincent and the Grenadines, San Marino, Solomon Islands, São Tomé and Príncipe, Timor-Leste, Tuvalu, Vanuatu, Zimbabwe.

## How the count grew

| When | Commit | Countries with a dish (any) | UN members with a dish | In our coverage count |
|---|---:|---:|---:|---:|
| before the atlas sprints (v0.7.2) | `d14d0fd` | 96 | 93 | 95 |
| sprint 1: Africa, Pacific, Caribbean | `4382d63` | 133 | 130 | 131 |
| sprint 2: Oceania and Indigenous foods | `67a406e` | 145 | 138 | 142 |
| sprint 3: coverage recovery | `0820fb0` | 163 | 156 | 160 |
| sprint 4: coverage recovery | `bfbc07b` | 168 | 160 | 165 |
| now (latest run) | working tree | 168 | 160 | 165 |

Sprint 1 read the cuisine pages of 74 more countries; sprint 2 their paragraph links and 'Cuisine of X' titles; sprint 3 the cuisine pages of 69 more; sprint 4 the Wikipedia categories of the weak and uncovered countries. Each sprint's report is in [sprints/](sprints/).
