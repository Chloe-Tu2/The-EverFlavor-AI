# Map coverage validation (2026-11-24)

Can the map show a place for a dish? A dish is mappable when its country's OpenStreetMap cuisine word (`stores.COUNTRY_CUISINES`) is on at least one place in the Greater Houston pilot area. From `data/knowledge/map_prep.json`.

| What | Count | Share |
|---|---:|---:|
| countries with dishes | 167 |  |
| ... with a cuisine tag | 79 | 47% |
| ... with pilot places for it | 38 | 23% |
| dishes the map can place (a dish counts once per country of origin) | 2,807 | 63% |
| linked recipes the map can place | 77,286 | 81% |

## Gaps

- **No cuisine tag** (88): Albania, Algeria, Andorra, Angola, Antigua and Barbuda, Azerbaijan, Bahrain, Barbados, Belarus, Belize, Benin, Bhutan, Bosnia and Herzegovina, Botswana, Brunei, Cameroon, Cape Verde, Central African Republic, Chad, Costa Rica, Curaçao, Cyprus, Democratic Republic of the Congo, Dominica, Eritrea, Estonia, Finland, Ghana, Grenada, Guadeloupe, Guam, Guyana, Honduras, Iceland, Iraq, Ivory Coast, Jordan, Kazakhstan, Kenya, Kyrgyzstan, Latvia, Libya, Lithuania, Luxembourg, Malawi, Maldives, Mali, Malta, Mauritania, Mauritius, Moldova, Montenegro, Mozambique, New Caledonia, New Zealand, Nicaragua, Niger, North Korea, North Macedonia, Northern Mariana Islands, Norway, Palestine, Panama, Paraguay, Rwanda, Saint Lucia, Samoa, Saudi Arabia, Seychelles, Sierra Leone, Slovakia, Slovenia, Somalia, South Africa, South Sudan, Sudan, Tajikistan, Tanzania, The Bahamas, The Gambia, Togo, Tonga, Trinidad and Tobago, Turkmenistan, Uganda, United Arab Emirates, Uruguay, Zambia. No demonym on Wikidata, or OpenStreetMap seldom uses it.
- **A tag but no pilot place** (41): Armenia, Australia, Austria, Bangladesh, Bolivia, Bulgaria, Cambodia, Canada, Chile, Croatia, Czech Republic, Denmark, Dominican Republic, Ecuador, Egypt, Georgia, Guatemala, Haiti, Hungary, Indonesia, Ireland, Israel, Laos, Madagascar, Myanmar, Netherlands, Poland, Romania, Russia, Senegal, Serbia, Singapore, Sri Lanka, Suriname, Sweden, Switzerland, Syria, Tunisia, Ukraine, Uzbekistan, Yemen. The pilot area has no such place; another area would.
- **Places whose tag names no country of ours:** pizza 226, seafood 168, barbecue 99, tex-mex 84, burger 80, asian 76, sushi 76, steak_house 72, breakfast 61, sandwich 51, mediterranean 44, pancake 37.

## Remediation plan

1. A second pilot area changes "no pilot place" the most; the map is Houston-only by design today.
2. For the countries without a tag, OpenStreetMap's own wiki (Key:cuisine) is the source to check; a tag is added only where it is in use.
3. Kinds of food (pizza, seafood, barbecue) are not countries and should stay out of this list; they could serve dish families later (a pizza place for the pizza family), as a separate reviewed step.
