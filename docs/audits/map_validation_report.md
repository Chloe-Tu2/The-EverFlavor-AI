# Map coverage validation (2026-11-23)

Can the map show a place for a dish? A dish is mappable when its country's OpenStreetMap cuisine word (`stores.COUNTRY_CUISINES`) is on at least one place in the Greater Houston pilot area. From `data/knowledge/map_prep.json`.

| What | Count | Share |
|---|---:|---:|
| countries with dishes | 167 |  |
| ... with a cuisine tag | 56 | 34% |
| ... with pilot places for it | 35 | 21% |
| dishes the map can place (a dish counts once per country of origin) | 2,784 | 63% |
| linked recipes the map can place | 77,277 | 81% |

## Gaps

- **No cuisine tag** (111): Albania, Algeria, Andorra, Angola, Antigua and Barbuda, Azerbaijan, Bahrain, Barbados, Belarus, Belize, Benin, Bhutan, Bolivia, Bosnia and Herzegovina, Botswana, Brunei, Bulgaria, Cameroon, Cape Verde, Central African Republic, Chad, Costa Rica, Curaçao, Cyprus, Democratic Republic of the Congo, Dominica, Dominican Republic, El Salvador, Eritrea, Estonia, Finland, Georgia, Ghana, Grenada, Guadeloupe, Guam, Guatemala, Guyana, Haiti, Honduras, Iceland, Iraq, Israel, Ivory Coast, Jordan, Kazakhstan, Kenya, Kyrgyzstan, Latvia, Libya, Lithuania, Luxembourg, Madagascar, Malawi, Maldives, Mali, Malta, Mauritania, Mauritius, Moldova, Mongolia, Montenegro, Mozambique, Myanmar, Nepal, Netherlands, New Caledonia, New Zealand, Nicaragua, Niger, North Korea, North Macedonia, Northern Mariana Islands, Norway, Palestine, Panama, Paraguay, Romania, Rwanda, Saint Lucia, Samoa, Saudi Arabia, Senegal, Serbia, Seychelles, Sierra Leone, Singapore, Slovakia, Slovenia, Somalia, South Africa, South Sudan, Sri Lanka, Sudan, Suriname, Tajikistan, Tanzania, The Bahamas, The Gambia, Togo, Tonga, Trinidad and Tobago, Tunisia, Turkmenistan, Uganda, Ukraine, United Arab Emirates, Uruguay, Uzbekistan, Yemen, Zambia. No demonym on Wikidata, or OpenStreetMap seldom uses it.
- **A tag but no pilot place** (21): Armenia, Australia, Austria, Bangladesh, Cambodia, Canada, Chile, Croatia, Czech Republic, Denmark, Ecuador, Egypt, Hungary, Indonesia, Ireland, Laos, Poland, Russia, Sweden, Switzerland, Syria. The pilot area has no such place; another area would.
- **Places whose tag names no country of ours:** pizza 226, seafood 168, barbecue 99, tex-mex 84, burger 80, asian 76, sushi 76, steak_house 72, breakfast 61, sandwich 51, mediterranean 44, pancake 37.

## Remediation plan

1. A second pilot area changes "no pilot place" the most; the map is Houston-only by design today.
2. For the countries without a tag, OpenStreetMap's own wiki (Key:cuisine) is the source to check; a tag is added only where it is in use.
3. Kinds of food (pizza, seafood, barbecue) are not countries and should stay out of this list; they could serve dish families later (a pizza place for the pizza family), as a separate reviewed step.
