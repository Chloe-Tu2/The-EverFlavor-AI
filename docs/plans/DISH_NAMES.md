# Dish Names

A plan for showing a dish's real name ("Lasagna") when the recipe title is one a person posted as their own
("Kittencal's Famous Lasagna"). It covers the size of the problem, a rule-based cleaner, its measured accuracy,
a check against Wikidata dish names and where the code would live. See the [planner](README.md).

Written 2026-10-24 (Claude, with med27-coder). This is a plan. Nothing in `src/`, the notebooks or the app has
changed yet. The prototype scripts live outside the repository (in the session scratchpad), not in git.

All numbers come from `data/processed/recipes_{train,val,test}.parquet` (291,755 recipes, all splits), counted on
2026-10-24.

## 1. The problem

Many titles carry words that are not part of the dish: a person's name, praise, a copycat restaurant, a diet tag,
an appliance or a number. Food.com titles are lower case and lost their apostrophes ("ina garten s chicken pot
pie"), so the cleaner first puts the `'s` back.

Counts by pattern (one title can be in several rows; the patterns are regular expressions, so a few counts hold
some false hits):

| Pattern | All | foodcom (218,024) | huggingface (37,823) | culinarydb (35,325) | themealdb (583) |
|---|---|---|---|---|---|
| Possessive (X's) | 20,102 (6.9%) | 16,429 (7.5%) | 1,184 (3.1%) | 2,485 (7.0%) | 4 (0.7%) |
| my / our / mom / grandma / aunt | 4,717 (1.6%) | 4,032 (1.8%) | 262 (0.7%) | 423 (1.2%) | 0 |
| Praise (best, famous, yummy, easy, ...) | 15,964 (5.5%) | 13,422 (6.2%) | 1,543 (4.1%) | 995 (2.8%) | 4 (0.7%) |
| Copycat / restaurant | 1,772 (0.6%) | 1,667 (0.8%) | 93 (0.2%) | 10 (0.0%) | 2 (0.3%) |
| Diet tag (ww, low fat, keto, gluten free) | 8,072 (2.8%) | 6,941 (3.2%) | 1,034 (2.7%) | 96 (0.3%) | 1 (0.2%) |
| Appliance (crock pot, instant pot, air fryer) | 7,008 (2.4%) | 5,853 (2.7%) | 894 (2.4%) | 257 (0.7%) | 4 (0.7%) |
| Numbering (#2, II, a trailing number) | 2,221 (0.8%) | 1,208 (0.6%) | 482 (1.3%) | 531 (1.5%) | 0 |
| Parentheses | 3,016 (1.0%) | 0 | 1,333 (3.5%) | 1,607 (4.5%) | 76 (13.0%) |
| "Not your ..." / "Better than ..." | 248 (0.1%) | 229 (0.1%) | 12 (0.0%) | 7 (0.0%) | 0 |
| quick / healthy / low fat / simple | 8,283 (2.8%) | 6,969 (3.2%) | 881 (2.3%) | 431 (1.2%) | 2 (0.3%) |
| The word "recipe(s)" | 9,673 (3.3%) | 1,128 (0.5%) | 8,427 (22.3%) | 100 (0.3%) | 18 (3.1%) |
| **Any of the above** | **66,731 (22.9%)** | 47,467 (21.8%) | 13,104 (34.6%) | 6,082 (17.2%) | 103 (17.7%) |

Food.com has the most personal titles. Hugging Face titles often end in "recipes" (the scraped page name).
CulinaryDB and TheMealDB use parentheses for a second name, such as "Pork and Hominy Stew (Pozole Rojo)".

### Examples (random, with what the cleaner gives)

| Source | Title | Cleaned dish name |
|---|---|---|
| foodcom | potato kugel passover gluten free | potato kugel passover |
| foodcom | make ahead mashed potatoes for a crowd | make ahead mashed potatoes |
| foodcom | gluten free caraway rye dough | caraway rye dough |
| huggingface | This Roasted Potato and Egg Sheet Pan Brunch Is Perfect for Lazy Weekends | This Roasted Potato and Egg Sheet Pan Brunch Is for Weekends |
| foodcom | company s coming layered ziti casserole | coming layered ziti casserole (wrong) |
| foodcom | chuy s restaurant hatch green chili salsa | restaurant hatch green chili salsa (wrong) |
| culinarydb | Pork and Hominy Stew (Pozole Rojo) | Pork and Hominy Stew; gloss: Pozole Rojo |
| huggingface | Roasted Bacon, Brussel Sprout, and Feta Salad with Dill Dressing recipes | Roasted Bacon, Brussel Sprout, and Feta Salad with Dill Dressing |
| culinarydb | Mac's Toad-in-the-Hole (Non-Traditional) | Toad-in-the-Hole |
| foodcom | best gingerbread cookies | gingerbread cookies |
| foodcom | linda s macaroon fruit casserole | macaroon fruit casserole |
| foodcom | low fat raspberry vinaigrette dressing | raspberry vinaigrette dressing |
| culinarydb | Pizza Salad II | Pizza Salad |
| foodcom | perfect pinwheels | pinwheels |
| huggingface | Yummy Breakfast Yogurt With Oatmeal | Breakfast Yogurt With Oatmeal |
| foodcom | the best pie crust recipe | pie crust |
| foodcom | canadian bacon onion quiche oamc | canadian bacon onion quiche |
| foodcom | skinny person rice krispies | person rice krispies (wrong) |
| foodcom | gluten free coconut macaroon | coconut macaroon |
| foodcom | gina s baked potato soup crock pot | baked potato soup |
| foodcom | pumpkin nut muffins healthier | pumpkin nut muffins |
| huggingface | Easy Hummus | Hummus |
| foodcom | tasty low sodium chili | chili |
| foodcom | yummy cheesy corn | cheesy corn |
| foodcom | coq au vin pressure cooker | coq au vin |
| huggingface | Terrific and Tasty Tidy Friday Pan Fry! | Tidy Friday Pan Fry |
| foodcom | easy frozen chicken breast | frozen chicken breast |
| foodcom | weight watchers candy | candy |
| huggingface | Cauliflower Rice Enchilada Bowl recipes | Cauliflower Rice Enchilada Bowl |
| huggingface | Easy Vegan Pie Crust recipes | Vegan Pie Crust |

## 2. The cleaner (rules)

The cleaner returns four things for each title: `dish_name`, `name_gloss` (a second name, if any),
`posted_title` (True when the title names a person or family) and the kinds of words it removed.

The rules, in order:

1. **Normalize.** Curly quotes to `'`; Food.com's "garten s" back to "garten's".
2. **Second names.** Text in parentheses goes to `name_gloss` unless it is a tag ("(Crock Pot)", "(Low Fat)").
   "Bulgogi (Korean BBQ Beef) - Ww Friendly" gives dish "Bulgogi", gloss "Korean BBQ Beef". "X aka Y" and
   "X | Y" also give a gloss.
3. **Tags after a dash or colon.** "- Ww Friendly", ": Low Fat" are dropped. Serious Eats column names before a
   colon ("Meatless Monday:") are dropped.
4. **Better than / copycat.** "Better Than Olive Garden's Alfredo" gives "Alfredo"; "Better Than Sex Cake" stays
   (it is a named cake). "Copycat" and about 70 restaurant names are dropped. Names that are also food words
   (Chipotle, Subway, Sonic, Outback) are dropped only after "copycat" or as "Chipotle's" or "Chipotle style".
5. **Not your mama's / like mom used to make.** Dropped; the title is marked as posted.
6. **Possessives.** "Kittencal's", "Grandma Nellie's", "Aunt Peggy and Uncle Bill's" are dropped and the title
   is marked as posted. A protect list keeps the possessives that belong to dishes or brands: Shepherd's Pie,
   General Tso's, Devil's Food, Hunter's, Ploughman's, New Year's, Reese's, Hershey's, s'mores and others.
7. **my / our / mom / grandma / aunt / nonna / abuela** without a possessive are dropped and the title is marked
   as posted.
8. **End of title only:** "recipe(s)", "#2", "II", a trailing number, "version 2", "for two", "serves 4",
   "made easy".
9. **Anywhere:** praise words (best, famous, yummy, easy, amazing, ultimate, perfect, awesome, delicious, quick,
   simple, classic, authentic, homemade, healthy, skinny, ...), diet tags (ww, Weight Watchers points, low fat,
   low carb, keto, paleo, sugar free, any "X free", diabetic friendly, oamc) and appliance tags (crock pot, slow
   cooker, instant pot, pressure cooker, air fryer, microwave, bread machine, "30 minute").
10. **Fallback.** If removing a tag would leave nothing ("Crock Pot", "Easy"), the tag word stays.

Kept on purpose: cooking techniques (grilled, fried, baked, skillet, no-bake), vegan, vegetarian and veggie
(they describe the dish, not a diet claim), "Simple Syrup", "Quick Bread" and named regional words.

Across all 291,755 titles the cleaner changes 73,579 (25.2%) and marks 21,145 (7.2%) as posted:

| Source | Changed | Marked as posted |
|---|---|---|
| foodcom | 24.1% | 17,486 (8.0%) |
| huggingface | 37.1% | 1,188 (3.1%) |
| culinarydb | 19.2% | 2,469 (7.0%) |
| themealdb | 19.2% | 2 (0.3%) |

It finds a second name for 2,861 titles and falls back to the original for 41.

## 3. Measured accuracy

Claude labeled two samples of 150 titles by hand. Each sample holds 100 titles the first cleaner changed and 50
it left alone, so the hard cases are over-sampled. "Exact" means the output equals the hand label (ignoring case
and spaces). "Acceptable" means the output is still a correct, clean name (for example "Deluxe Grilled Cheese"
for "grilled cheese").

The first sample was used to fix the rules, so its score is optimistic. The second sample was drawn later, from
other rows, and labeled from the titles alone before scoring. Its numbers are the honest ones.

| Cleaner | Sample | Exact | Acceptable |
|---|---|---|---|
| First version | development (150) | 126 (84.0%) | 138 (92.0%) |
| First version | held-out test (150) | 116 (77.3%) | 129 (86.0%) |
| Final version | development (150) | 141 (94.0%) | 149 (99.3%) |
| **Final version** | **held-out test (150)** | **126 (84.0%)** | **138 (92.0%)** |

On the test sample, the changed titles score 79/100 exact and 88/100 acceptable; the untouched titles score
47/50 and 50/50. Weighted back to all titles (25.4% changed), that is about **90% exact and 97% acceptable**.

The `posted_title` flag on the test sample: precision 25/28 (89%), recall 25/27 (93%).

### Failure kinds (the 12 test titles that were not acceptable)

| Kind | Count | Example (title, then output) |
|---|---|---|
| A trailing description is kept | 5 | "yummy stuffed garlic rolls everyone loves em" gives "stuffed garlic rolls everyone loves em" |
| A person's name without `'s` | 2 | "barefoot contessa s shortbread hearts ina garten" gives "shortbread hearts ina garten" |
| A diet or appliance tag half removed | 2 | "art s french bread not bread machine" gives "french bread not" |
| A praise word not in the list | 2 | "Quick Fix Tiramisu Parfaits" gives "Fix Tiramisu Parfaits" |
| The wrong side of a colon kept | 1 | "Recipe: Trisha Yearwood's Crock-Pot Chocolate Candy" gives "Recipe" |

Other misses seen in the random examples: "company's coming" read as a person, a restaurant name without a
copycat word ("chuy's restaurant"), "skinny person rice krispies".

## 4. A trained model?

A token tagger (each word: keep or drop) could learn the long tail, but there are no labels to train it on. The
300 hand labels here are enough to measure, not to train; a tagger would need a few thousand. Labels made by the
rules would only teach the rules' own mistakes. Most of the remaining errors are rare phrases ("everyone loves
em", "fit for a king"), each needing its own example.

The rules are also easier to explain and to record as policy (who decided to drop "easy", who decided to keep
"vegan"), which the project requires. So the recommendation is **rules plus a list of known dish names**, with a
model left as an option for later. A local model (Ollama) could review only the changed titles in a notebook and
the results be saved, but it must stay optional, since Colab falls back to rules.

## 5. Wikidata dish names as the list

Wikidata is CC0. The prototype asked the public SPARQL endpoint for every subclass of dish (Q746549) and every
item whose "instance of" is one of them, with English labels and aliases. The endpoint allowed one request per
minute that day, so the script sent 6 requests, 65 seconds apart, with a descriptive User-Agent. The download is
2.3 MB.

| Item | Count |
|---|---|
| Dish classes (subclass of dish) | 13,267 |
| Dish instances | 7,512 |
| Items with an English label | 15,121 |
| English aliases | 7,840 |
| Distinct names after normalizing (lower case, plurals) | 21,379 |

How many names match a Wikidata label or alias:

| Rows | Raw title, exact | Cleaned dish name, exact | Dish name or gloss, exact | Holds a 2+ word Wikidata dish |
|---|---|---|---|---|
| All (291,755) | 1.0% | 5.1% | 5.2% | 30.7% |
| foodcom | 0.7% | 4.9% | 4.9% | 31.1% |
| huggingface | 1.9% | 6.0% | 6.2% | 31.1% |
| culinarydb | 1.3% | 5.3% | 5.9% | 27.7% |
| themealdb | 10.1% | 15.3% | 17.0% | 29.7% |

On the titles the cleaner changed, exact matches go from 0.0% (raw) to 16.5% (cleaned). The 3,137 matched names
are the everyday dishes: meatloaf (190 recipes), chili (188), lasagna (158), banana bread (120), potato salad
(114). Most titles are longer than a dish name ("carrot and lentil soup"), so a full-name match is rare; but 30.7%
of titles hold a known two-word or longer dish ("lentil soup", "pot roast", "Cuban sandwich"). Matches on one word
alone are not useful: the top single-word hits are "salad", "chocolate", "sweet", "bean" and "italian".

Wikidata is most useful in two places:

- **The protect list.** Wikidata has 186 dish names with a possessive. 45 recipe titles hold one of them, and the
  rules removed it in 24: meat lover's (8), chef's salad (5), calf's liver (5), Buddha's delight (2),
  millionaire's shortbread (2), Joe's special (1), bird's nest (1). Taking the protect list from Wikidata fixes
  these.
- **A canonical dish.** The longest Wikidata dish inside a cleaned name ("chicken cacciatore" in "spicy chicken
  cacciatore") can group recipes of the same dish and link to its Wikidata item, for search or "more like this".

Wikidata cannot be the only source. It does not cover home-style names ("taco thing", "sloppy joe pie"), and some
items are products or brands (Cheez-It, Fisherman's Friend), so the list needs a filter.

## 6. Recommended approach

| Part | Where | What |
|---|---|---|
| Cleaner | `src/everflavor/dish_names.py` (new) | `clean_dish_name(title) -> dish_name, name_gloss, posted_title, removed`; word lists as named constants, each with a one-line reason |
| Protect list | `data/reference/` (small CSV) | Possessive dish and brand names: the hand list plus Wikidata's 186, checked once by a person |
| Wikidata names | notebook 04 (it already reads Wikidata for ingredient names) | Download dish labels and aliases, paced, saved with the date; optional `wikidata_dish` column |
| Columns | notebook 01 | `dish_name`, `name_gloss`, `posted_title` next to `recipe_name` |
| App | recipe cards and detail | Show the clean `dish_name` large and the original title in small text under it; show the gloss in brackets |
| Tests | `tests/test_dish_names.py` | The 300 labeled titles as fixtures; the protect list (Shepherd's Pie, General Tso's Chicken, Better Than Sex Cake) must never change |

The original `recipe_name` stays in every table. The cleaner only adds columns.

## 7. Risks

- **Removing a word that is part of the dish.** Shepherd's Pie, General Tso's Chicken, Devil's Food Cake, Meat
  Lover's Pizza, Chef's Salad, Calf's Liver, "Old Fashioned" (a cocktail), "Simple Syrup", "Quick Bread". The
  protect list and the Wikidata possessives cover the known ones; tests keep them.
- **Brands with a possessive.** "Mom's" can be a brand, a restaurant can be named after a person ("Chuy's",
  "Max & Erma's") and "Wendy's" is both a name and a chain. These are kept or dropped by list, and some will be
  wrong.
- **Food words that are also restaurant names.** Chipotle, Subway, Sonic: dropped only with a copycat word.
- **Safety.** The allergy and diet flags read the title (`flags.name_text`). They must keep reading the original
  `recipe_name`, never `dish_name`, so a removed "gluten free" or "(with peanuts)" can never change a flag. The
  diet tags the cleaner drops are claims by the poster, not checks; the app shows the back end's flags instead.
- **Hiding diet words in the name.** "Gluten Free, Dairy Free Brownies" shows as "Brownies". The original title in
  small text keeps the claim visible.
- **People's names.** The names in titles are public posts in open data; the cleaner only moves them out of the big
  name. The audit log rule (never the user's words) is not affected.
