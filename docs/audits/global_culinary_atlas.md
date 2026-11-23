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
| Africa | 60 | 29 | 2 | 29.2 | thin |
| Americas | 57 | 19 | 10 | 41.7 | thin |
| Asia | 51 | 19 | 38 | 68.6 | fair |
| Europe | 53 | 20 | 46 | 68.9 | fair |
| Oceania | 29 | 3 | 1 | 7.7 | gap |

## Subregions

| Region | Countries | With dishes | Median dishes | Score | Band | Ready | To review | Blocked |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| Melanesia (Oceania) | 5 | 0 | 0 | 0 | gap |  |  |  |
| Micronesian Region (Oceania) | 8 | 0 | 0 | 0 | gap |  | 4 |  |
| Polynesia (Oceania) | 10 | 1 | 1 | 7.5 | gap |  |  |  |
| Caribbean (Americas) | 28 | 7 | 3 | 20 | gap | 6 | 2 | 1 |
| Western Africa (Africa) | 17 | 8 | 1 | 26 | thin | 8 |  |  |
| Eastern Africa (Africa) | 22 | 10 | 1.5 | 26.5 | thin | 8 |  |  |
| Middle Africa (Africa) | 9 | 4 | 2.5 | 28.5 | thin |  |  |  |
| Central Asia (Asia) | 5 | 2 | 3.5 | 28.8 | thin | 4 |  |  |
| Southern Asia (Asia) | 9 | 3 | 13 | 49.2 | thin | 104 | 13 | 2 |
| Northern Africa (Africa) | 7 | 5 | 6 | 50.7 | fair | 9 |  |  |
| Central America (Americas) | 8 | 5 | 8 | 51.2 | fair | 16 | 2 | 1 |
| Southern Africa (Africa) | 5 | 2 | 14.5 | 56.2 | fair | 1 |  |  |
| Western Asia (Asia) | 18 | 5 | 18 | 58.9 | fair | 81 | 4 | 5 |
| South America (Americas) | 16 | 5 | 18 | 60.6 | fair | 43 | 7 | 8 |
| Southern Europe (Europe) | 17 | 4 | 80 | 61.8 | fair | 154 | 31 | 6 |
| Australasia (Oceania) | 6 | 2 | 30 | 66.7 | fair | 6 |  | 3 |
| Northern Europe (Europe) | 17 | 6 | 34.5 | 67.6 | fair | 231 | 7 | 38 |
| Eastern Asia (Asia) | 8 | 3 | 108 | 68.8 | fair | 257 | 7 | 11 |
| Northern America (Americas) | 5 | 2 | 227 | 70 | fair | 166 | 2 | 50 |
| Eastern Europe (Europe) | 10 | 4 | 45 | 70 | fair | 47 | 24 | 1 |
| Southeast Asia (Asia) | 11 | 6 | 74.5 | 77.3 | good | 78 | 13 | 2 |
| Western Europe (Europe) | 9 | 6 | 29 | 83.3 | good | 257 | 50 | 23 |

## Where the gaps are

- **Melanesia:** 0 of 5 countries have a dish; none yet in Fiji, New Caledonia, Papua New Guinea, Solomon Islands, Vanuatu.
- **Micronesian Region:** 0 of 8 countries have a dish; none yet in Federated States of Micronesia, Guam, Kiribati, Marshall Islands, Nauru, Northern Mariana Islands, Palau, United States Minor Outlying Islands.
- **Polynesia:** 1 of 10 countries have a dish; none yet in American Samoa, Cook Islands, French Polynesia, Niue, Pitcairn Islands, Samoa, Tokelau, Tuvalu and more.
- **Caribbean:** 7 of 28 countries have a dish; none yet in Anguilla, Antigua and Barbuda, Aruba, British Virgin Islands, Caribbean Netherlands, Cayman Islands, Curaçao, Dominica and more.
- **Western Africa:** 8 of 17 countries have a dish; none yet in Burkina Faso, Guinea, Guinea-Bissau, Liberia, Mali, Mauritania, Saint Helena, Ascension and Tristan da Cunha, Sierra Leone and more.
- **Eastern Africa:** 10 of 22 countries have a dish; none yet in British Indian Ocean Territory, Burundi, Comoros, Djibouti, Eritrea, French Southern and Antarctic Lands, Kenya, Madagascar and more.
- **Middle Africa:** 4 of 9 countries have a dish; none yet in Central African Republic, Congo, Equatorial Guinea, Gabon, São Tomé and Príncipe.
- **Central Asia:** 2 of 5 countries have a dish; none yet in Kyrgyzstan, Tajikistan, Turkmenistan.
- **Southern Asia:** 3 of 9 countries have a dish; none yet in Afghanistan, Bangladesh, Bhutan, Maldives, Nepal, Sri Lanka.

## The next dishes, per continent

`<Continent>_Next_500.json`: up to 500 ready backlog dishes each, a dish whose family we have first, at most 40 per country, taking turns between subregions so no one region fills the list. They are candidates for a person to approve, not additions.

- Africa: 26 dishes from 12 countries
- Americas: 125 dishes from 16 countries
- Asia: 344 dishes from 30 countries
- Europe: 411 dishes from 26 countries
- Oceania: 6 dishes from 2 countries

## Versions we lack, and the review queue

- `missing_variants.json`: 779 backlog dishes are versions of a dish EverFlavor already shows (their Wikidata family is one of our dishes), by subregion.
- `publication_review_queue.json`: 275 dishes need a person first. The problems found:
  - not a country today (a region, city or former state): a person places it: 109 (Korea 30, Europe 3, Maghreb 3, West Germany 3, Ancient Rome 2, British Raj 2, ...)
  - a country the place tree lacks yet: 109 (Romania 20, Slovenia 11, Myanmar 9, Serbia 8, Sri Lanka 7, Paraguay 5, ...)
  - in more than 3 families: check which one it belongs to: 51
  - a plant or animal on Wikidata, not a dish: 7

## Not placed

None: every place with dishes or recipes has one.
