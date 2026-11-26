# Walter's five questions (2026-11-25)

For each of our dishes, can Walter answer what it is, where it is from, why it matters, similar dishes and its versions from a sourced field? From `scripts/knowledge/walter_gaps.py`. A missing answer is never filled in by a model; it waits for a source. **Audit only.**

| Question | Dishes with an answer | Share |
|---|---:|---:|
| what is it | 3,870 | 100% |
| where is it from | 3,138 | 81% |
| why it matters | 3,094 | 80% |
| similar dishes | 3,870 | 100% |
| its versions | 250 | 6% |

## How many of the five each dish answers

| Answers | Dishes |
|---|---:|
| 5 | 149 |
| 4 | 2,471 |
| 3 | 1,091 |
| 2 | 160 |
| 1 | 0 |
| 0 | 0 |

## The most seen dishes with a gap

Dishes the app links the most recipes to, first (the full list: `data/knowledge/quality/walter_gap_queue.json`).

| Dish | Country | Recipes linked | Missing |
|---|---:|---:|---:|
| Pork chop | China | 1,859 | its versions |
| Cheesecake | Germany | 1,244 | where is it from, its versions |
| Peanut butter | Canada | 1,130 | its versions |
| Potato salad | Germany | 1,091 | where is it from, its versions |
| Lasagna | Italy | 1,018 | its versions |
| Spaghetti | Italy | 731 | its versions |
| Chocolate chip cookie | United States | 728 | its versions |
| Enchilada | United States | 690 | its versions |
| Risotto | Italy | 667 | its versions |
| Carrot | France | 666 | where is it from, its versions |
| French toast | China | 623 | its versions |
| Gratin | Norway | 595 | its versions |
| Quesadilla | United States | 556 | its versions |
| Cobbler (food) | Canada | 521 | its versions |
| Macaroni and cheese | Jamaica | 488 | its versions |
| Banana bread | Jamaica | 476 | its versions |
| Vegetable soup | Poland | 471 | where is it from |
| Fruit salad | Mexico | 450 | where is it from, why it matters |
| Penne | Italy | 431 | its versions |
| Apple pie | United States | 428 | its versions |
| Pot roast | Canada | 423 | where is it from |
| Baked beans | Canada | 407 | where is it from |
| Pot pie | United States | 387 | where is it from, its versions |
| Chicken soup | Mexico | 377 | where is it from, why it matters |
| Tomato soup | Greece | 369 | where is it from |

## Walter coverage score per country

The average number of the five questions a country's dishes answer (0 to 5), weakest first; 171 countries, all in `data/knowledge/quality/walter_country_scores.json`. A low score points to missing stories, origins, variants or graph links there.

| Country | Dishes | Score (of 5) | Dishes with all five |
|---|---:|---:|---:|
| Belize | 1 | 2.00 | 0 |
| The Bahamas | 1 | 2.00 | 0 |
| Central African Republic | 2 | 2.50 | 0 |
| Tonga | 2 | 2.50 | 0 |
| Turkmenistan | 2 | 2.50 | 0 |
| Mauritius | 3 | 3.00 | 0 |
| Seychelles | 3 | 3.00 | 0 |
| Mali | 2 | 3.00 | 0 |
| Monaco | 2 | 3.00 | 0 |
| South Sudan | 2 | 3.00 | 0 |
| Andorra | 1 | 3.00 | 0 |
| Bahrain | 1 | 3.00 | 0 |
| Curaçao | 1 | 3.00 | 0 |
| Malawi | 1 | 3.00 | 0 |
| Mauritania | 1 | 3.00 | 0 |
| Montenegro | 1 | 3.00 | 0 |
| Mozambique | 1 | 3.00 | 0 |
| New Caledonia | 1 | 3.00 | 0 |
| Rwanda | 1 | 3.00 | 0 |
| Samoa | 1 | 3.00 | 0 |
| The Gambia | 1 | 3.00 | 0 |
| Zambia | 1 | 3.00 | 0 |
| Slovakia | 11 | 3.09 | 0 |
| Puerto Rico | 9 | 3.11 | 0 |
| Algeria | 23 | 3.17 | 0 |
