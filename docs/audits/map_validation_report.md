# Map coverage validation (2026-11-22)

Can the map show a place for a dish? A dish is mappable when its country's OpenStreetMap cuisine word (`stores.COUNTRY_CUISINES`) is on at least one place in the Greater Houston pilot area. From `data/knowledge/map_prep.json`.

| What | Count | Share |
|---|---:|---:|
| countries with dishes | 74 |  |
| ... with a cuisine tag | 56 | 76% |
| ... with pilot places for it | 35 | 47% |
| dishes the map can place (a dish counts once per country of origin) | 2,628 | 72% |
| linked recipes the map can place | 80,554 | 82% |

## Gaps

- **No cuisine tag** (18): Algeria, Andorra, Azerbaijan, Costa Rica, Finland, Iraq, Kenya, Netherlands, New Zealand, Norway, Palestine, Saudi Arabia, Slovakia, Somalia, South Africa, Sudan, Ukraine, Uruguay. No demonym on Wikidata, or OpenStreetMap seldom uses it.
- **A tag but no pilot place** (21): Armenia, Australia, Austria, Bangladesh, Cambodia, Canada, Chile, Croatia, Czech Republic, Denmark, Ecuador, Egypt, Hungary, Indonesia, Ireland, Laos, Poland, Russia, Sweden, Switzerland, Syria. The pilot area has no such place; another area would.
- **Places whose tag names no country of ours:** pizza 226, seafood 168, barbecue 99, tex-mex 84, burger 80, asian 76, sushi 76, steak_house 72, breakfast 61, sandwich 51, mediterranean 44, pancake 37.

## Remediation plan

1. A second pilot area changes "no pilot place" the most; the map is Houston-only by design today.
2. For the countries without a tag, OpenStreetMap's own wiki (Key:cuisine) is the source to check; a tag is added only where it is in use.
3. Kinds of food (pizza, seafood, barbecue) are not countries and should stay out of this list; they could serve dish families later (a pizza place for the pizza family), as a separate reviewed step.
