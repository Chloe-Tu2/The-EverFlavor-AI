# Map coverage validation (2026-11-22)

Can the map show a place for a dish? A dish is mappable when its country's OpenStreetMap cuisine word (`stores.COUNTRY_CUISINES`) is on at least one place in the Greater Houston pilot area. From `data/knowledge/map_prep.json`.

| What | Count | Share |
|---|---:|---:|
| countries with dishes | 118 |  |
| ... with a cuisine tag | 56 | 47% |
| ... with pilot places for it | 35 | 30% |
| dishes the map can place (a dish counts once per country of origin) | 2,699 | 70% |
| linked recipes the map can place | 76,858 | 82% |

## Gaps

- **No cuisine tag** (62): Algeria, Andorra, Angola, Antigua and Barbuda, Azerbaijan, Barbados, Belize, Benin, Botswana, Cameroon, Cape Verde, Chad, Costa Rica, Democratic Republic of the Congo, Dominica, Dominican Republic, El Salvador, Eritrea, Finland, Ghana, Guatemala, Haiti, Iraq, Israel, Ivory Coast, Jordan, Kazakhstan, Kenya, Kyrgyzstan, Libya, Malawi, Mauritius, Mozambique, Netherlands, New Zealand, Nicaragua, Niger, Norway, Palestine, Panama, Rwanda, Saudi Arabia, Senegal, Seychelles, Sierra Leone, Slovakia, Somalia, South Africa, South Sudan, Sudan, Tajikistan, Tanzania, The Gambia, Togo, Tonga, Trinidad and Tobago, Tunisia, Uganda, Ukraine, Uruguay, Uzbekistan, Yemen. No demonym on Wikidata, or OpenStreetMap seldom uses it.
- **A tag but no pilot place** (21): Armenia, Australia, Austria, Bangladesh, Cambodia, Canada, Chile, Croatia, Czech Republic, Denmark, Ecuador, Egypt, Hungary, Indonesia, Ireland, Laos, Poland, Russia, Sweden, Switzerland, Syria. The pilot area has no such place; another area would.
- **Places whose tag names no country of ours:** pizza 226, seafood 168, barbecue 99, tex-mex 84, burger 80, asian 76, sushi 76, steak_house 72, breakfast 61, sandwich 51, mediterranean 44, pancake 37.

## Remediation plan

1. A second pilot area changes "no pilot place" the most; the map is Houston-only by design today.
2. For the countries without a tag, OpenStreetMap's own wiki (Key:cuisine) is the source to check; a tag is added only where it is in use.
3. Kinds of food (pizza, seafood, barbecue) are not countries and should stay out of this list; they could serve dish families later (a pizza place for the pizza family), as a separate reviewed step.
