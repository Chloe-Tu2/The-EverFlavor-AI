# Regional source research (Q1 phase 0, 2026-11-24)

115 countries with a dish have no regional data. The goal of phase 0 is a trustworthy source, not data. From `scripts/knowledge/regional_sources.py`. **Audit only:** no region is added; a person chooses the source and the mapping rule (a review item).

## Candidate sources

| Source | Licence | What it gives | Use |
|---|---:|---:|---:|
| Wikidata cuisine items (measured here) | CC0 | already used; items carry a country and often a region | best first candidate |
| Wikipedia 'Category:Cuisine by region' and regional cuisine articles | CC BY-SA 4.0 (credit) | already used for dishes; region pages need reading, not a structured list | second, by hand per country |
| GeoNames or OpenStreetMap administrative regions | CC BY 4.0 / ODbL | places only, no food: could name regions, never say a region has a cuisine | only to place a sourced region |
| UNESCO Intangible Cultural Heritage lists | facts reusable, texts copyrighted | a few regional food traditions per country, with the country | for preservation, not full coverage |
| Commercial food atlases (for example TasteAtlas) | proprietary | broad but not reusable | not allowed |

## How far Wikidata reaches

Wikidata has at least one non-national cuisine item for 35 of the 115 countries (30%); the other 80 have none, so no single free source covers them all. Items are often ethnic or diaspora cuisines (Chinese Islamic, Indonesian-Dutch), not regions, so each needs a check: is it a place within the country?

## Proposed mapping (for a person to accept)

1. A Wikidata cuisine item becomes a culinary region only if it names a place within the country (its own P131 or P276, or its label is a region's name), never an ethnic group or diaspora.
2. Its dishes come from Wikidata (P2012 cuisine, or the dish's origin being that region), not from proximity on a page.
3. Countries Wikidata does not reach keep the gap; the debt counts it honestly.

## Countries Wikidata reaches

| Country | Items | Examples |
|---|---:|---:|
| Austria | 3 | Viennese cuisine, cuisine of Burgenland, cuisine of Vorarlberg |
| Bangladesh | 5 | Bengali cuisine, Chittagonian cuisine, Sylheti cuisine, cuisine of Dhaka |
| Belgium | 6 | Limburgian cuisine, cuisine of Brussels, cuisine of Brussels and Wallonia, cuisine of Liège |
| Brunei | 1 | cuisine of Malaysia, Singapore and Brunei |
| Cambodia | 1 | Khmer royal cuisine |
| Chile | 2 | Pascuense cuisine, cuisine of Chiloé |
| Colombia | 1 | cuisine of the Paisa Region |
| Congo | 1 | Congolese cuisine |
| Costa Rica | 1 | cuisine of Limón Province |
| Cyprus | 1 | cuisine of Northern Cyprus |
| Denmark | 2 | Faroese cuisine, Greenlandic cuisine |
| Ecuador | 3 | cuisine of Guayaquil, cuisine of Manabí Province, cuisine of Quito |
| Georgia | 1 | Abkhazian cuisine |
| Honduras | 1 | cuisine of Tegucigalpa |
| Iraq | 1 | Mosuli cuisine |
| Ireland | 1 | cuisine of Britain and Ireland |
| Israel | 1 | cuisine of Jerusalem |
| Luxembourg | 1 | Luxembourger cuisine |
| Moldova | 1 | Gagauz cuisine |
| Norway | 1 | cuisine of Svalbard |
| Pakistan | 3 | Muhajir cuisine, Punjabi cuisine, cuisine of Karachi |
| Paraguay | 1 | cuisine of Asunción |
| Peru | 4 | Arequipan cuisine, Nikkei cuisine, cuisine of Junín, cuisine of Tarma |
| Poland | 7 | Lublin cuisine, Opole Silesian cuisine, Pomeranian cuisine, cuisine of Greater Poland |
| Russia | 4 | Chukotka cuisine, Komi cuisine, Yamal cuisine, cuisine of Commander Islands |
| Serbia | 1 | Kosovan cuisine |
| Singapore | 2 | Indian Singaporean cuisine, cuisine of Malaysia, Singapore and Brunei |
| South Korea | 2 | Seoul cuisine, South Korean cuisine |
| Switzerland | 1 | cuisine of Ticino |
| Syria | 1 | Aleppo cuisine |
| Turkey | 2 | cuisine of İzmir, Şanlıurfa cuisine |
| Ukraine | 5 | Hutsul cuisine, Podolian cuisine, cuisine of Odesa, cuisine of Zakarpattia |
| Uruguay | 1 | cuisine of Montevideo |
| Venezuela | 2 | cuisine of Monagas state, cuisine of Mérida state |
| Yemen | 1 | Hadhrami cuisine |

## Countries with no candidate

Afghanistan, Albania, Andorra, Antigua and Barbuda, Armenia, Azerbaijan, Bahrain, Barbados, Belarus, Belize, Benin, Bhutan, Bolivia, Bosnia and Herzegovina, Bulgaria, Central African Republic, Chad, Curaçao, Czech Republic, Dominica, Dominican Republic, El Salvador, Eritrea, Estonia, Grenada, Guadeloupe, Guam, Guatemala, Guyana, Haiti, Iceland, Jordan, Kazakhstan, Kenya, Kyrgyzstan, Laos, Latvia, Lithuania, Madagascar, Malawi, Maldives, Mali, Malta, Mauritania, Mauritius, Mongolia, Montenegro, Mozambique, Nepal, New Caledonia, New Zealand, Nicaragua, North Korea, North Macedonia, Northern Mariana Islands, Palestine, Panama, Puerto Rico, Romania, Rwanda, Saint Lucia, Samoa, Sierra Leone, Slovakia, Slovenia, Somalia, South Sudan, Sri Lanka, Suriname, Sweden, Tajikistan, The Bahamas, The Gambia, Togo, Tonga, Trinidad and Tobago, Turkmenistan, United Arab Emirates, Uzbekistan, Zambia
