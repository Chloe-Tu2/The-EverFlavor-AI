# Global Culinary Atlas (2026-11-22)

Coverage of the world's food by the UN's regions (M49), from Unicode CLDR 49 (Unicode License V3). Reports only: nothing is added or published.
Every dish named comes from the Wikidata backlog (`coverage_audit.py`); no dish, fact or link is invented. Data: `data/knowledge/atlas/`, written by `scripts/knowledge/atlas_audit.py`.

## How the score works

- **Breadth:** the share of the region's countries with at least one dish.
- **Depth:** the median number of dishes of those countries, against 20 (more counts as full).
- **Score:** the average of the two, 0 to 100: good from 75, fair from 50, thin from 25, else a gap.
- 250 countries and territories are counted, every one with an ISO code that CLDR places, small territories with no cuisine of their own included, so breadth is strict.
- The UN regions have no Balkans or Siberia. Those need a published source that draws them before the atlas shows them.

## Continents

| Continent | Countries | With dishes | Median dishes | Score | Band |
|---|---:|---:|---:|---:|---|
| Africa | 60 | 4 | 17.5 | 47.1 | thin |
| Americas | 57 | 10 | 39 | 58.8 | fair |
| Asia | 51 | 17 | 57 | 66.7 | fair |
| Europe | 53 | 20 | 46 | 68.9 | fair |
| Oceania | 29 | 2 | 29.5 | 53.4 | fair |

## Subregions

| Region | Countries | With dishes | Median dishes | Score | Band | Ready | To review | Blocked |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| Middle Africa (Africa) | 9 | 0 | 0 | 0 | gap |  | 1 |  |
| Western Africa (Africa) | 17 | 0 | 0 | 0 | gap | 18 | 13 | 1 |
| Central Asia (Asia) | 5 | 0 | 0 | 0 | gap |  | 9 |  |
| Melanesia (Oceania) | 5 | 0 | 0 | 0 | gap |  |  |  |
| Micronesian Region (Oceania) | 8 | 0 | 0 | 0 | gap |  | 4 |  |
| Polynesia (Oceania) | 10 | 0 | 0 | 0 | gap |  |  |  |
| Eastern Africa (Africa) | 22 | 1 | 10 | 27.3 | thin | 4 | 8 |  |
| Southern Asia (Asia) | 9 | 3 | 11 | 44.2 | thin | 106 | 13 | 2 |
| Caribbean (Americas) | 28 | 2 | 36 | 53.6 | fair | 4 | 13 | 1 |
| Central America (Americas) | 8 | 1 | 110 | 56.2 | fair | 19 | 6 | 1 |
| Northern Africa (Africa) | 7 | 2 | 17.5 | 58 | fair | 15 |  |  |
| Western Asia (Asia) | 18 | 5 | 18 | 58.9 | fair | 46 | 39 | 5 |
| Southern Africa (Africa) | 5 | 1 | 28 | 60 | fair | 1 |  |  |
| South America (Americas) | 16 | 5 | 18 | 60.6 | fair | 43 | 7 | 8 |
| Southern Europe (Europe) | 17 | 4 | 80 | 61.8 | fair | 154 | 31 | 6 |
| Australasia (Oceania) | 6 | 2 | 29.5 | 66.7 | fair | 6 |  | 3 |
| Northern Europe (Europe) | 17 | 6 | 34.5 | 67.6 | fair | 233 | 7 | 38 |
| Eastern Asia (Asia) | 8 | 3 | 108 | 68.8 | fair | 257 | 7 | 11 |
| Northern America (Americas) | 5 | 2 | 227.5 | 70 | fair | 168 | 2 | 50 |
| Eastern Europe (Europe) | 10 | 4 | 44.5 | 70 | fair | 47 | 24 | 1 |
| Southeast Asia (Asia) | 11 | 6 | 74 | 77.3 | good | 79 | 13 | 2 |
| Western Europe (Europe) | 9 | 6 | 29 | 83.3 | good | 259 | 50 | 23 |

## Where the gaps are

- **Middle Africa:** 0 of 9 countries have a dish; none yet in Angola, Cameroon, Central African Republic, Chad, Congo, Democratic Republic of the Congo, Equatorial Guinea, Gabon and more.
- **Western Africa:** 0 of 17 countries have a dish; none yet in Benin, Burkina Faso, Cape Verde, Ghana, Guinea, Guinea-Bissau, Ivory Coast, Liberia and more.
- **Central Asia:** 0 of 5 countries have a dish; none yet in Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan, Uzbekistan.
- **Melanesia:** 0 of 5 countries have a dish; none yet in Fiji, New Caledonia, Papua New Guinea, Solomon Islands, Vanuatu.
- **Micronesian Region:** 0 of 8 countries have a dish; none yet in Federated States of Micronesia, Guam, Kiribati, Marshall Islands, Nauru, Northern Mariana Islands, Palau, United States Minor Outlying Islands.
- **Polynesia:** 0 of 10 countries have a dish; none yet in American Samoa, Cook Islands, French Polynesia, Niue, Pitcairn Islands, Samoa, Tokelau, Tonga and more.
- **Eastern Africa:** 1 of 22 countries have a dish; none yet in British Indian Ocean Territory, Burundi, Comoros, Djibouti, Eritrea, French Southern and Antarctic Lands, Kenya, Madagascar and more.
- **Southern Asia:** 3 of 9 countries have a dish; none yet in Afghanistan, Bangladesh, Bhutan, Maldives, Nepal, Sri Lanka.

## The next dishes, per continent

`<Continent>_Next_500.json`: up to 500 ready backlog dishes each, a dish whose family we have first, at most 40 per country, taking turns between subregions so no one region fills the list. They are candidates for a person to approve, not additions.

- Africa: 38 dishes from 8 countries
- Americas: 126 dishes from 16 countries
- Asia: 306 dishes from 22 countries
- Europe: 412 dishes from 26 countries
- Oceania: 6 dishes from 2 countries

## Versions we lack, and the review queue

- `missing_variants.json`: 812 backlog dishes are versions of a dish EverFlavor already shows (their Wikidata family is one of our dishes), by subregion.
- `publication_review_queue.json`: 357 dishes need a person first. The problems found:
  - a country the place tree lacks yet: 190 (Romania 20, Georgia 19, Slovenia 11, Myanmar 9, Serbia 8, Ghana 7, ...)
  - not a country today (a region, city or former state): a person places it: 110 (Korea 30, Europe 3, Maghreb 3, West Germany 3, Ancient Rome 2, British Raj 2, ...)
  - in more than 3 families: check which one it belongs to: 51
  - a plant or animal on Wikidata, not a dish: 7

## Not placed

None: every place with dishes or recipes has one.
