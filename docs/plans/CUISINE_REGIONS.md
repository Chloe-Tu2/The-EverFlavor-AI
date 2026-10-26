# Cuisine Regions

A plan for country-level cuisines (Chinese, Taiwanese, Korean, Japanese, Moroccan and so on) in place of the five
broad families. It covers the data, the app's Cuisine menu and which kitchen each country opens. Part of version
0.6.0 ([planner](README.md)), next to [REGIONAL_KITCHENS.md](REGIONAL_KITCHENS.md).

Written 2026-10-24 (Claude, with med27-coder). This is a plan.

**Status (2026-10-25, notebook 01 rerun):** steps 1 and 3 are done and part of step 4. `ORIGIN_LABELS` has the
missing labels and the region rule keeps the narrower region (Louisiana 1,657, Texas 1,353; both were 0). The
country model now picks only countries inside a broad label's area (`AREA_COUNTRIES`, `area_mask`, `best_in_area`
in `cuisine.py`), without raising its confidence, so an area with no likely known country stays Unknown. A first
name rule (`origin_from_name`: "jamaican", "jerk", "taiwan(ese)") gives `origin_source` "named" (389 recipes:
Jamaica 384, Taiwan 5). Mexico went from 14,849 to 11,508 recipes (predicted 5,818 to 2,477); Jamaica from 18 to
402; of the 287 Jamaica-named recipes 226 are now Jamaica (was 9) and 4 Mexico (was 132). Cuba 409 to 399, Brazil
321 to 311, Peru 98 (not in the model), Taiwan 0 to 5. South American recipes mostly stay Unknown (79 of 1,733 got
a country). Validation at 0.70: 73.9% kept, 90.1% right. Still open: `origin_area` column, smaller-country setting,
the full name rule and dish-word CSV, the review sample. The counts below are from before this run.

All numbers come from `data/processed/recipes_{train,val,test}.parquet` (291,755 recipes, all splits), counted on
2026-10-24. The model numbers come from the last full run of notebook 01 (section 5.9.1).

## 1. Where the data stands

### Families

| Family | Recipes |
|---|---|
| Other | 200,526 |
| European | 48,150 |
| Asian | 20,788 |
| Latin American | 15,706 |
| Middle Eastern | 3,406 |
| African | 3,179 |

"Other" holds most of the American, Canadian and Australian recipes. The family list has no "american" name, so
`map_cuisine` gives them "Other". Of the 56,181 recipes labeled United States, 53,660 are in "Other".

### How each recipe gets its country

| origin_source | Recipes | What it means |
|---|---|---|
| labeled | 121,449 | The source's own label names one country |
| predicted | 108,663 | The country model guessed, with confidence 0.70 or more |
| unknown | 61,643 | No label and no confident guess; `origin_country` is "Unknown" |

By source:

| Source | labeled | predicted | unknown | total |
|---|---|---|---|---|
| CulinaryDB | 26,759 | 5,642 | 2,924 | 35,325 |
| Food.com | 65,622 | 98,498 | 53,904 | 218,024 |
| Hugging Face | 28,485 | 4,523 | 4,815 | 37,823 |
| TheMealDB | 583 | 0 | 0 | 583 |

`origin_confidence` is filled only for predicted recipes (labeled and Unknown recipes have none):

| Confidence | Predicted recipes |
|---|---|
| 0.70 to 0.80 | 22,156 |
| 0.80 to 0.90 | 31,024 |
| 0.90 to 0.95 | 22,326 |
| 0.95 to 1.00 | 33,157 |

The 61,643 Unknown recipes: 49,299 are in family "Other" and 48,440 have no cuisine label at all. 13,203 have only a
broad label: mediterranean 2,046, european 2,040, asian 1,346, world 666, indian subcontinent 634, nordic 514,
middle eastern 513, middle east 487, eastern europe 456, african 417, british isles 407, "asian, middle-eastern" 362.

### Countries (all with 50 or more recipes)

| Country | Recipes | labeled | predicted | Family |
|---|---|---|---|---|
| United States | 131,336 | 56,181 | 75,155 | Other |
| Italy | 25,150 | 16,209 | 8,941 | European |
| Mexico | 14,849 | 9,031 | 5,818 | Latin American |
| France | 8,691 | 6,636 | 2,055 | European |
| India | 7,403 | 3,281 | 4,122 | Asian |
| China | 5,984 | 3,139 | 2,845 | Asian |
| United Kingdom | 4,669 | 3,596 | 1,073 | European |
| Canada | 4,565 | 4,063 | 502 | Other |
| Greece | 4,363 | 2,951 | 1,412 | European |
| Australia | 2,800 | 2,196 | 604 | Other |
| Thailand | 2,421 | 1,582 | 839 | Asian |
| Japan | 2,269 | 1,548 | 721 | Asian |
| Spain | 1,845 | 1,506 | 339 | European |
| Morocco | 1,592 | 794 | 798 | African |
| Germany | 1,478 | 1,027 | 451 | European |
| Ireland | 707 | 448 | 259 | European |
| South Korea | 606 | 515 | 91 | Asian |
| South Africa | 603 | 297 | 306 | African |
| Lebanon | 587 | 191 | 396 | Middle Eastern |
| Vietnam | 509 | 323 | 186 | Asian |
| Turkey | 471 | 225 | 246 | Middle Eastern |
| Sweden | 467 | 312 | 155 | European |
| Russia | 445 | 296 | 149 | European |
| Portugal | 432 | 385 | 47 | European |
| Iran | 429 | 208 | 221 | Middle Eastern |
| Cuba | 409 | 193 | 216 | Latin American |
| Poland | 408 | 290 | 118 | European |
| New Zealand | 387 | 369 | 18 | Other |
| Hungary | 352 | 225 | 127 | European |
| Switzerland | 332 | 277 | 55 | European |
| Brazil | 321 | 226 | 95 | Latin American |
| Denmark | 259 | 197 | 62 | European |
| Netherlands | 255 | 215 | 40 | European |
| Philippines | 255 | 189 | 66 | Asian |
| Indonesia | 218 | 172 | 46 | Asian |
| Egypt | 206 | 157 | 49 | African |
| Norway | 202 | 162 | 40 | European |
| Finland | 147 | 147 | 0 | European |
| Belgium | 113 | 113 | 0 | European |
| Argentina | 108 | 108 | 0 | Latin American |
| Austria | 101 | 101 | 0 | European |
| Peru | 98 | 98 | 0 | Latin American |
| Czech Republic | 94 | 94 | 0 | European |
| Pakistan | 82 | 82 | 0 | Asian |
| Malaysia | 79 | 79 | 0 | Asian |
| Ethiopia | 78 | 78 | 0 | African |
| Saudi Arabia | 73 | 73 | 0 | Middle Eastern |
| Puerto Rico | 71 | 71 | 0 | Latin American |
| Chile | 71 | 71 | 0 | Latin American |
| Colombia | 70 | 70 | 0 | Latin American |
| Iraq | 66 | 66 | 0 | Middle Eastern |
| Cambodia | 53 | 53 | 0 | Asian |
| Palestine | 51 | 51 | 0 | Middle Eastern |

43 more countries have fewer than 50 (for example Costa Rica 43, Nepal 33, Nigeria 32, Guatemala 24, Jamaica 18,
Libya 17, Algeria 11, Tunisia 7). Taiwan and Israel have 0.

Note: [REGIONAL_KITCHENS.md](REGIONAL_KITCHENS.md) has older counts (for example Italy 18,041; now 25,150). They
should be refreshed from this table.

Regions named by a source: Southern US 4,322, Midwestern US 2,440, Northeastern US 1,621, Southwestern US 1,611,
England 1,274, Ontario 631, British Columbia 542, Pacific Northwest 506, California 443, Scotland 386, Hawaii 372,
Quebec 140, Baja California 131, Sichuan 102, Guangdong 82, Wales 67, Oaxaca 61, Hunan 23, Beijing 16.

### How the country is decided today

1. **Source labels** (`src/everflavor/cuisine.py`, `origin_from_labels`, called in `pipeline.run_pipeline`).
   Each source's label column is looked up in `ORIGIN_LABELS` (label to country and region): Food.com `tags`,
   Hugging Face `cuisine_type`, CulinaryDB `cuisine`, TheMealDB `area`. A label with a region beats a plain
   country label ("mexican" + "tex-mex" gives United States, Texas). Two different countries give "Unknown".
   Broad labels ("asian", "caribbean", "middle east") are not in `ORIGIN_LABELS`, so they give "Unknown".
2. **Country model** (notebook 01, section 5.9.1). A logistic regression on title and ingredient text
   (`TextFeatures`), trained on labeled train recipes of countries with at least 100 of them (37 countries).
   The guess must belong to the recipe's family (`COUNTRY_FAMILY`); "Other" recipes may get any country. Kept only
   at confidence 0.70 or more (`ORIGIN_MIN_CONFIDENCE`), otherwise "Unknown".
3. **Family** (`map_cuisine`, `FAMILY_PRIORITY`) is separate. Recipe names are never read for the family or the
   label country; they are read only as model features.

Last run, on 17,998 validation recipes with a labeled country: 80.6% right at the top guess; at 0.70 confidence
74.8% get a country and 89.3% of those are right. Found per real country: United States 66%, Italy 86%, Mexico 99%,
France 54%, Canada 8%, United Kingdom 49%, India 88%, China 78%, Australia 20%, Japan 69%, Morocco 95%.

## 2. Why Taiwan is 0 and Korea is low

### Taiwan

- No source has a Taiwan label. The word "taiwanese" is in no `cuisine_raw` value.
- "taiwanese" is in the family list (`CUISINE_FAMILIES["Asian"]`) but not in `ORIGIN_LABELS`. Even a Taiwanese
  label would give "Unknown" today.
- Only 16 recipe names say "taiwan" or "taiwanese". 14 of them are labeled or predicted China (their sources tag
  them "asian, chinese" or CulinaryDB "china"), 2 are Unknown.
- Dish words add very little and are ambiguous:

| Name contains | Recipes | Current country |
|---|---|---|
| taiwan, taiwanese | 16 | China 14, Unknown 2 |
| beef noodle soup | 22 | China 8, Vietnam 5, Unknown 4, Thailand 2 |
| three cup, san bei | 5 | China 4, United States 1 |
| gua bao, lu rou fan, braised pork rice | 1 | China 1 |
| oyster omelet | 1 | United States 1 |
| bubble tea, boba, pearl milk tea | 10 | India 4, United Kingdom 3, others |
| pineapple cake | 51 | United States 41 (mostly American pineapple cakes) |
| scallion or green onion pancake | 22 | China 7, South Korea 6, Unknown 5 |
| popcorn chicken | 14 | United States 8, China 3 |
| stinky tofu, formosa | 0 | |

A careful Taiwan rule (the word Taiwan or Taiwanese, plus lu rou fan, gua bao and three-cup chicken) finds about 20
recipes. Taiwan stays under 50 with today's sources. It needs a new source with Taiwanese recipes.

### Korea

Korea is not low because of a bug. The sources have few Korean recipes. 581 recipes have a Korean label
(Food.com "korean" 320, CulinaryDB "korea" 261); 548 of them are South Korea.

| Signal | Recipes | Current country |
|---|---|---|
| Label korean or korea | 581 | South Korea 548, Unknown 14, China 6, Japan 5, Mexico 4 |
| Name says korea or korean | 375 | South Korea 351, Unknown 10, Mexico 7, Japan 2 |
| Name has a Korean dish word (kimchi, bulgogi, bibimbap, gochujang, japchae, galbi, tteok, kimbap, mandu, jjigae, sundubu, doenjang, ssam, pajeon...) | 259 | South Korea 229, United States 10, Unknown 8 |
| Ingredients have gochujang, gochugaru or kimchi | 197 | South Korea 166, United States 8, Unknown 7 |
| Name says korean or has a dish word | 550 | South Korea 497; 53 elsewhere (18 Unknown) |

The 14 Unknown labeled ones carry two countries ("asian, chinese, japanese, korean"; "mexican, korean"), so
`origin_from_labels` calls them ambiguous. Name and dish rules would add about 50 recipes (606 to about 650).
"south korean" is also missing from `ORIGIN_LABELS`.

### Other gaps found the same way

Names that say a country, compared with the country they have now:

| Name says | Recipes | Already that country | Unknown | Another country |
|---|---|---|---|---|
| Jamaica, Jamaican | 287 | 9 | 65 | 213 (Mexico 132, United States 71) |
| Puerto Rico | 113 | 29 | 13 | 71 (Mexico 63) |
| Peruvian | 113 | 54 | 9 | 50 (Mexico 45) |
| Argentina | 78 | 45 | 6 | 27 (Mexico 16) |
| Israel, Israeli | 89 | 0 | 63 | 26 (Lebanon 8, Turkey 4) |
| Hong Kong | 23 | 0 (no such region) | 1 | 22 (China 20) |
| Pakistan | 44 | 12 | 7 | 25 (India 22) |
| Malaysia | 46 | 15 | 11 | 20 (India 10) |
| Ethiopia | 85 | 47 | 28 | 10 |
| Korea | 375 | 351 | 10 | 14 |
| Japan | 481 | 461 | 8 | 12 |
| Morocco | 830 | 703 | 91 | 36 |
| France, French | 2,247 | 1,181 | 508 | 558 (United States 409) |

Three causes stand out:

1. **Small countries cannot be predicted.** The model only knows countries with 100+ labeled train recipes. A
   recipe with only the broad label "caribbean" or "south american" must get a Latin American country, and Mexico
   is the only big one. Of 2,343 recipes labeled only Caribbean or Central American, 1,681 became Mexico. Of 1,723
   labeled only South American, 1,429 became Mexico. Validation cannot see this error, because these recipes have
   no labeled country to check against.
2. **Labels missing from `ORIGIN_LABELS`** that the family list already knows: taiwanese, israeli, persian,
   iranian, south korean, singaporean, sri lankan, burmese, afghan, bangladeshi, yemeni, jordanian, emirati,
   ghanaian, senegalese, somali, bahamas. Israel is 0 for this reason.
3. **Regions cancel each other.** Food.com tags Cajun recipes "cajun" and "southern-united-states". Both carry a
   region, so `origin_from_labels` keeps the country but drops the region. Louisiana has 0 recipes, although 1,826
   names say cajun, creole, gumbo, jambalaya or etouffee (1,805 of them United States). Texas has 0 for the same
   reason (343 names say tex-mex).

Names can also mislead: 1,333 names say french fries, french toast, french onion, french dressing or french bread
(596 of them are France now). "Spanish rice" (150) is split Unknown 44, Spain 43, Mexico 43.

## 3. Proposed cuisine list for the app

Rule: a country gets its own menu entry when it has 50 or more recipes (labeled, or named or predicted after the
fixes in section 4). Smaller countries stay searchable by name but have no entry. "Opens" is the kitchen that shows.
A country with no fitting kitchen opens Classic, as REGIONAL_KITCHENS rule 1 asks ("accurate, not a costume
party"): an Indian or Korean dish should not open the Chinese or Japanese kitchen.

| Kitchen | Country entries (recipes now) | Regions inside | Own kitchen later |
|---|---|---|---|
| **Chinese** | China 5,984 | Sichuan 102, Guangdong 82, Hunan 23, Beijing 16; Hong Kong (about 23 after the fix) | |
| **Chinese** | Taiwan (0 now, about 20 after the fix) | | Only when it reaches 50 (needs a new source) |
| **Japanese** | Japan 2,269 | | |
| **Mediterranean** | Italy 25,150, Greece 4,363, Spain 1,845, Portugal 432 | | Italian (planned priority 2) |
| **Mediterranean** | France 8,691 | | French (planned priority 3) |
| **Middle Eastern** | Lebanon 587, Turkey 471, Iran 429, Egypt 206, Saudi Arabia 73, Iraq 66, Palestine 51, Israel (0 now, about 89 after the fix) | | Turkish, Persian (priority 10) |
| **Moroccan** | Morocco 1,592 | | |
| **Moroccan** | North Africa: Algeria 11, Libya 17, Tunisia 7 (one entry, 35; under 50) | | |
| **Mexican** | Mexico 14,849 | Baja California 131, Oaxaca 61 | |
| **Classic** | United States 131,336 | Southern US 4,322, Midwestern 2,440, Northeastern 1,621, Southwestern 1,611, Pacific Northwest 506, California 443, Hawaii 372; Louisiana and Texas after the region fix | |
| **Classic** | Canada 4,565, Australia 2,800, New Zealand 387 | Ontario 631, British Columbia 542, Quebec 140 | |
| **Classic** | United Kingdom 4,669, Ireland 707 | England 1,274, Scotland 386, Wales 67 | British (priority 5) |
| **Classic** | Germany 1,478, Sweden 467, Russia 445, Poland 408, Hungary 352, Switzerland 332, Denmark 259, Netherlands 255, Norway 202, Finland 147, Belgium 113, Austria 101, Czech Republic 94 | | |
| **Classic** | India 7,403, Pakistan 82 | | Indian (priority 1) |
| **Classic** | Thailand 2,421, Vietnam 509, Philippines 255, Indonesia 218, Malaysia 79, Cambodia 53 | | Thai (priority 4), Vietnamese (priority 10) |
| **Classic** | South Korea 606 | | Korean (priority 6) |
| **Classic** | South Africa 603, Ethiopia 78 | | South African (7), Ethiopian (8) |
| **Classic** | Cuba 409, Brazil 321, Argentina 108, Peru 98, Puerto Rico 71, Chile 71, Colombia 70; Jamaica (18 now, about 280 after the fix) | | Caribbean, Brazilian, Peruvian (priority 9) |

Choices for the team to record as policies (who decided, in the policy list):

- **Taiwan** is its own entry, named "Taiwan", as its recipes name themselves. It is not a region of China.
  **Hong Kong** is a region under China, like Guangdong. Both appear only once they reach the size rule.
- **Korea opens Classic** until the Korean kitchen exists. The other choice is the Japanese kitchen; it is closer
  in look but would show a Korean dish in the wrong country.
- **Latin America outside Mexico opens Classic**, not Mexican, for the same reason. Today the family rule opens
  Mexican for all of them.
- **Egypt opens Middle Eastern**, not Moroccan (an Arab, eastern Mediterranean kitchen is the closer fit).
- **France opens Mediterranean** until the French kitchen exists.

How the menu works:

- Keep the Cuisine menu (family) and add a **Country** menu under it: "Any country" plus the entries of that
  family, biggest first, with the recipe count. The Classic group's family is "Other" today; show it as "American
  and other" or give US, Canada, Australia and New Zealand a family "North American and Oceanian" (a data change,
  a policy).
- The kitchen follows the chosen country; with "Any country" it follows the country most results come from
  (REGIONAL_KITCHENS option B), and Classic when that country has no kitchen.
- Predicted countries say "probably", as the ethics notes ask. The filter and the counts come from the back end
  (`agent_tools` already filters by `origin_country`); the page only shows them.

## 4. Making the country logic more accurate

### Signal order (highest wins)

| Rank | Signal | origin_source | Notes |
|---|---|---|---|
| 1 | The source names one country | labeled | As now, after the label fixes below |
| 2 | The name says a country or demonym ("Jamaican jerk chicken") | named (new) | Only where rank 1 has no country or only a broad area |
| 3 | A curated dish word ("bulgogi", "lu rou fan", "tagine") | keyword (new) | Only where ranks 1 and 2 give nothing; never on its own for ambiguous words |
| 4 | The country model, inside the broad area | predicted | Confidence 0.70 or more, as now |
| 5 | Nothing sure | unknown | Keep the broad area in a new column |

A name or dish word never overrides a country the source gave. When it disagrees with the source, count it as a
conflict in the notebook instead.

### Changes, one by one

1. **Fill the gaps in `ORIGIN_LABELS`**: taiwanese (Taiwan), israeli (Israel), persian and iranian (Iran), south
   korean (South Korea), singaporean, sri lankan, burmese, afghan, bangladeshi, yemeni, jordanian, emirati,
   ghanaian, senegalese, somali, bahamas. Add a Hong Kong region under China.
2. **Fix the region rule**: when two regions of one country appear, keep the more specific one (Louisiana over
   Southern US, Texas over Southwestern US). A small table of which region lies inside which does this.
3. **A new column `origin_area`** from the broad labels (Caribbean, Central America, South America, Middle East,
   North Africa, West Africa, Southeast Asia, Indian subcontinent, Mediterranean, Nordic, British Isles, DACH,
   Eastern Europe, Australia and New Zealand). The model may only pick countries inside that area. If none is sure,
   the country stays Unknown but the area is kept. This stops the 3,110 Caribbean and South American recipes
   becoming Mexico.
4. **Small countries**: lower `ORIGIN_MIN_EXAMPLES` (100) to about 30 inside a constrained area, or leave the
   country Unknown and keep only the area. Test both on the hand-labeled sample.
5. **Name rule** (`origin_from_name`, new, in `cuisine.py`): demonyms and country names in the title, with an
   exceptions list for dishes named after a place but not from it: french fries, french toast, french dressing,
   french onion, spanish rice, german chocolate, swiss steak, swedish meatballs, indian pudding, indian
   corn, english muffin, danish (pastry), "-style", "inspired", "fusion".
6. **Dish words per kitchen country** (a CSV in `data/reference/`, one row per word, with country, region and a
   "needs a second signal" flag):

| Country | Strong dish words (alone are enough) | Weak (need a second signal) |
|---|---|---|
| South Korea | bulgogi, bibimbap, japchae, galbi/kalbi, tteokbokki, kimbap/gimbap, jjigae, sundubu, doenjang, banchan, hotteok, pajeon | kimchi, gochujang, mandu, ssam |
| Taiwan | lu rou fan, gua bao, three-cup chicken (san bei ji) | beef noodle soup, pineapple cake, popcorn chicken, bubble tea, scallion pancake |
| China | kung pao, mapo tofu, char siu, chow mein, lo mein, moo shu, dim sum, har gow, siu mai, general tso | fried rice, sweet and sour, wonton, egg roll, hoisin |
| Japan | sushi, sukiyaki, tonkatsu, okonomiyaki, takoyaki, onigiri, yakitori, oyakodon, donburi, tamagoyaki | teriyaki, ramen, miso, tempura, katsu, matcha, edamame |
| Morocco | tagine/tajine, harira, b'stilla/pastilla, chermoula, ras el hanout, zaalouk, msemen | couscous, kefta, preserved lemon |
| Lebanon | fattoush, kibbeh, manakish | hummus, falafel, tabbouleh, labneh, shawarma, za'atar |
| Mexico | mole, pozole, tamales, chilaquiles, cochinita pibil, tlayuda | taco, enchilada, salsa, burrito (often Tex-Mex) |
| Jamaica | jerk, ackee, escovitch, bammy | |
| Peru | lomo saltado, aji de gallina, causa | ceviche |
| Ethiopia | injera, doro wat, berbere, niter kibbeh, mitmita | |
| Egypt | koshari, ful medames, molokhia | |

"Weak" words are common in American recipes. For example 229 recipes with a Japanese word are United States, such
as "teriyaki ranch chicken"; 1,095 names say "asian", and 441 of them became China.

### How to measure it

- **A hand-labeled sample**, like the flag review rounds (`docs/flag_review/`): `docs/origin_review/round1.csv`.
  Draw 30 recipes per menu country (50 for the seven kitchen countries and the United States), split evenly over
  labeled, named, keyword and predicted. Add 100 Unknown recipes, to see what is missed. Columns: recipe_id, name,
  ingredients, the pipeline's country and source, the reviewer's country (or "unsure", "fusion", "generic"), the
  reviewer. Two reviewers; a third settles disagreements.
- **Precision per country and per source**, with a 95% interval (30 recipes give about plus or minus 15 points,
  so the kitchen countries get 50).
- **A bar for the menu**: a country is shown when its precision is 85% or more on its labeled, named and keyword
  recipes; predicted recipes need 80% or more, or the country shows only its sure recipes (as `_origin_pool` does
  with labeled recipes and confidence 0.9).

### What notebook 01 should report

Section 5.9 already prints accuracy by predicted country and "found" by real country. Add:

1. One table per country: recipes by origin_source (labeled, named, keyword, predicted, unknown), validation
   precision and found (recall), and F1. Show macro F1 next to the overall accuracy, so small countries count.
2. The top confusions (real country, given country, recipes), for example Jamaica as Mexico.
3. Per broad area: how many recipes got a country and how many stayed area-only.
4. Conflicts: names or dish words that disagree with the source label, per country.
5. The hand-labeled precision per country, read from the review CSV, in the same table.
6. Save these in the dataset record (`origin_model` block) so the README numbers come from the run.

## 5. Risks and order of work

### Risks

- **Fusion and "-style" dishes**: "korean tacos", "thai pizza", "mexican lasagna" (97 names). The rule should give
  the country the dish names, or mark it fusion, never two countries. The review sample has a "fusion" answer.
- **American "Asian-style" recipes**: 1,095 names say "asian" (441 China, 404 Unknown) and 323 say "oriental"
  (165 China). Without a country word they should stay at area level, not become China.
- **Place names that are not origins**: french toast, spanish rice, german chocolate cake (section 2).
- **Moving the US share**: an earlier test of class weights pushed most US recipes to other countries (US found 68%
  to 20-22%). Every change must show the United States numbers before and after.
- **Political naming**: Taiwan and Hong Kong, Palestine and Israel. Name entries as the recipes and sources do,
  and record the choice as a policy.
- **Kitchens show a country**: a wrong country now shows a wrong kitchen. The kitchen follows only labeled or named
  countries and sure predictions.
- **A full rerun**: the new columns and sources change the splits' content. Notebooks 01 to 09 that read the
  country need a batched rerun, with `src/` frozen during it (`CLAUDE.md`). `validate_recipes` checks the allowed
  `origin_source` values and must learn "named" and "keyword".

### Order of work

| Step | Work | Where | Size |
|---|---|---|---|
| 1 | Fill the `ORIGIN_LABELS` gaps; fix the region rule; tests | `cuisine.py`, `tests/` | Small |
| 2 | Build the hand-labeled sample on today's data (round 1, the baseline) | `docs/origin_review/` | Medium |
| 3 | `origin_area` and the area-limited model; smaller-country setting | notebook 01, 5.9 | Medium |
| 4 | Name rule with exceptions; dish-word CSV; new origin_source values | `cuisine.py`, `data/reference/`, `pipeline.py` | Medium |
| 5 | One batched rerun of notebook 01 and the notebooks after it; new per-country report | notebooks | Long run |
| 6 | Review round 2 on the new data; set the menu bar | `docs/origin_review/` | Medium |
| 7 | Refresh the counts in REGIONAL_KITCHENS.md and the README from the run | docs | Small |
| 8 | App: the Country menu and kitchen-by-country; "probably" for predicted | `app/app.py`, `agent_tools.py` | Medium |
| 9 | Look for a source with Taiwanese, Korean, Caribbean and African recipes | data | Open |
