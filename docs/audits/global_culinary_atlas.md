# Global Culinary Atlas (2026-11-23)

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
| Africa | 60 | 34 | 2 | 33.3 | thin |
| Americas | 57 | 29 | 7 | 42.9 | thin |
| Asia | 51 | 43 | 11 | 69.7 | fair |
| Europe | 53 | 37 | 18 | 79.9 | good |
| Oceania | 29 | 5 | 2 | 13.6 | gap |

## Subregions

| Region | Countries | With dishes | Median dishes | Score | Band | Ready | To review | Blocked |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| Polynesia (Oceania) | 10 | 1 | 2 | 10 | gap |  |  |  |
| Melanesia (Oceania) | 5 | 1 | 1 | 12.5 | gap |  |  |  |
| Micronesian Region (Oceania) | 8 | 1 | 4 | 16.2 | gap | 1 |  |  |
| Caribbean (Americas) | 28 | 8 | 4.5 | 25.5 | thin | 3 | 2 | 1 |
| Western Africa (Africa) | 17 | 8 | 1 | 26 | thin | 10 |  |  |
| Middle Africa (Africa) | 9 | 5 | 2 | 32.8 | thin |  |  |  |
| Eastern Africa (Africa) | 22 | 13 | 2 | 34.5 | thin | 5 |  |  |
| Central America (Americas) | 8 | 7 | 3 | 51.2 | fair | 14 | 2 | 1 |
| Central Asia (Asia) | 5 | 5 | 2 | 55 | fair | 2 |  |  |
| South America (Americas) | 16 | 12 | 8 | 57.5 | fair | 35 | 1 | 7 |
| Southern Africa (Africa) | 5 | 2 | 16 | 60 | fair | 1 |  |  |
| Western Asia (Asia) | 18 | 13 | 11 | 63.6 | fair | 50 |  | 1 |
| Northern Africa (Africa) | 7 | 6 | 8.5 | 64.1 | fair | 7 |  |  |
| Southern Europe (Europe) | 17 | 11 | 13 | 64.9 | fair | 159 | 3 | 5 |
| Australasia (Oceania) | 6 | 2 | 31 | 66.7 | fair | 5 |  | 3 |
| Northern America (Americas) | 5 | 2 | 227.5 | 70 | fair | 166 | 2 | 50 |
| Southern Asia (Asia) | 9 | 9 | 9 | 72.5 | fair | 103 |  | 2 |
| Northern Europe (Europe) | 17 | 10 | 20 | 79.4 | good | 227 | 2 | 38 |
| Eastern Europe (Europe) | 10 | 9 | 16 | 85 | good | 35 |  | 1 |
| Eastern Asia (Asia) | 8 | 6 | 52 | 87.5 | good | 255 | 1 | 11 |
| Western Europe (Europe) | 9 | 7 | 27 | 88.9 | good | 260 | 49 | 23 |
| Southeast Asia (Asia) | 11 | 10 | 29 | 95.5 | good | 79 | 1 | 2 |

## Where the gaps are

- **Polynesia:** 1 of 10 countries have a dish; none yet in American Samoa, Cook Islands, French Polynesia, Niue, Pitcairn Islands, Samoa, Tokelau, Tuvalu and more.
- **Melanesia:** 1 of 5 countries have a dish; none yet in Fiji, Papua New Guinea, Solomon Islands, Vanuatu.
- **Micronesian Region:** 1 of 8 countries have a dish; none yet in Federated States of Micronesia, Kiribati, Marshall Islands, Nauru, Northern Mariana Islands, Palau, United States Minor Outlying Islands.
- **Caribbean:** 8 of 28 countries have a dish; none yet in Anguilla, Aruba, Barbados, British Virgin Islands, Caribbean Netherlands, Cayman Islands, Curaçao, Dominica and more.
- **Western Africa:** 8 of 17 countries have a dish; none yet in Burkina Faso, Guinea, Guinea-Bissau, Liberia, Mali, Mauritania, Saint Helena, Ascension and Tristan da Cunha, Sierra Leone and more.
- **Middle Africa:** 5 of 9 countries have a dish; none yet in Congo, Equatorial Guinea, Gabon, São Tomé and Príncipe.
- **Eastern Africa:** 13 of 22 countries have a dish; none yet in British Indian Ocean Territory, Burundi, Comoros, Djibouti, Eritrea, French Southern and Antarctic Lands, Mayotte, Réunion and more.

## The next dishes, per continent

`<Continent>_Next_500.json`: up to 500 ready backlog dishes each, a dish whose family we have first, at most 40 per country, taking turns between subregions so no one region fills the list. They are candidates for a person to approve, not additions.

- Africa: 23 dishes from 10 countries
- Americas: 112 dishes from 14 countries
- Asia: 309 dishes from 34 countries
- Europe: 393 dishes from 29 countries
- Oceania: 6 dishes from 3 countries

## Versions we lack, and the review queue

- `missing_variants.json`: 691 backlog dishes are versions of a dish EverFlavor already shows (their Wikidata family is one of our dishes), by subregion.
- `publication_review_queue.json`: 172 dishes need a person first. The problems found:
  - not a country today (a region, city or former state): a person places it: 109 (Korea 30, Europe 3, Maghreb 3, West Germany 3, Ancient Rome 2, British Raj 2, ...)
  - in more than 3 families: check which one it belongs to: 51
  - a plant or animal on Wikidata, not a dish: 7
  - a country the place tree lacks yet: 6 (Bermuda 1, Greenland 1, Jersey 1, Montserrat 1, San Marino 1, United States Virgin Islands 1)

## Not placed

None: every place with dishes or recipes has one.
