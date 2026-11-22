# Recipe to dish linking (audit, 2026-11-21; rule L1 added 2026-11-22)

How many recipes the app links to a dish, how it links them, and where it fails. Numbers from
`scripts/knowledge/recipe_dish_links.py` on the tables of the 2026-11-22 notebook 01 run, which writes the counts
per dish to `data/knowledge/dish_recipe_counts.json`.

## How a recipe finds its dish

The recipe cards clean the posted title first (`dish_names.clean_title`: "Grandma's Best Lasagna Recipe" becomes
"lasagna"; the table keeps it as `dish_name`), then the app and the waiter use `waiter.Knowledge.find` on it:

1. an exact name;
2. else the name before "with / on / in / over / served / topped";
3. else the longest known dish name inside it. A one-word name counts only at the end, and broad words such as
   "salad" never count. The recipe's country breaks a tie. Rule L1 (below) then skips a name that is only the
   flavour of another dish.

The script uses a faster version of the same rules and first checks that both give the same dish on 3,000
random recipes.

## The numbers

| | Recipes | Share |
|---|---:|---:|
| All recipes | 291,755 | 100% |
| Linked to a dish or food | 77,560 | 26.6% |
| Exact name | 9,464 | 3.2% |
| Name before "with ..." | 7,758 | 2.7% |
| A dish name inside the name | 60,338 | 20.7% |
| Not linked | 214,195 | 73.4% |

By source: Food.com 56,228 of 218,024 (25.8%), CulinaryDB 11,057 of 35,325 (31.3%), the Hugging Face set 10,107
of 37,823 (26.7%), TheMealDB 168 of 583 (28.8%).

Dishes: 1,518 of the 3,201 dishes in the knowledge notebook have at least one recipe (47.4%); 1,683 have none
(they can only be shown as knowledge, never as a recipe). A dish with recipes has 6 at the median and 48.3 on
average; the most linked are Pork chop (1,859), Pizza (1,657), Cheesecake (1,244), Meatball (1,134) and Peanut
butter (1,130). 4,234 more recipes link to a food or drink entry (see item 3).

## Rule L1: a dish named before a kind of dish is that dish's flavour (proposed, 2026-11-22)

**Question.** A title can name a dish in the middle: "peanut butter fudge", "pumpkin pie bars", "hash brown
casserole". Is the recipe that dish?

**Decision.** No, when the word right after the name is a kind of dish (`waiter.DISH_KINDS`: fudge, bars, pie,
casserole, cookies, sauce and 92 more). The name is skipped with every name overlapping it, and the next best name
is taken if there is one ("peanut butter fudge" → Fudge, "fried fish tacos" → Taco), else none. Two exceptions,
both read from the data, never guessed:

- the dish is that kind itself: the word is in the first sentence of its summary or in its families' names
  ("French dip sandwiches": "a hot sandwich"; "pad thai noodles": a noodle dish);
- the name ends the title or is followed by another word ("peanut butter and jelly bars" stays Peanut butter).

**Why.** A recipe linked to the wrong dish shows the wrong story, origin and related dishes. Before L1, 1,876
recipes linked to Peanut butter through words such as "peanut butter blossoms" and "peanut butter bars". Better
no dish than a wrong one: an unlinked recipe still keeps its own country and joins the graph by its place.

**Effect** (measured on the 2026-11-16 tables, before the rerun): 3,573 links change; 3,171 lose a wrong dish and
402 move to the right one; none gains a link where it had none. Every change, grouped by dish and word, is in
[dish_link_review.csv](dish_link_review.csv) (1,328 groups). Claude (AI) read the 266 groups with 3 or more
recipes (2,316 of the changes) and noted the few doubtful ones; the rest are unread. Known misses: "coconut rice
pudding" now links to nothing, where a person would choose Rice pudding (the rule never takes an overlapping
name).

**Status.** Proposed by Claude (AI); a team review of the sheet is open. Tests: `tests/test_waiter.py`
(`test_a_dish_before_a_kind_of_dish_is_its_flavour_not_the_dish`).

## Where it fails

1. **Most unlinked names are general.** 45% of the unlinked names end in a broad word (salad 10,936, chicken
   7,429, soup 6,311, cake 6,215, casserole 5,116, cookies 4,929). These are not one dish, and leaving them
   unlinked is right.
2. **A dish name in the middle of a name.** 7,264 links still use a name that is not at the end of the title,
   now only where the next word is not a kind of dish ("lentil soup for students", "roast chicken and
   potatoes", but also "peanut butter banana smoothie"). A person should check a sample of these too.
3. **Foods, not dishes.** 4,234 recipes link to a food or drink entry because the name is just that word (Green
   bean, Salmon, Shrimp). The link is right; such pages have no dish facts to show. In the Food Graph these get
   their own relation, `named_for`, not `recipe_of`.
4. **Plurals.** The name cleaner makes "potatoes" "potatoe" and "sandwiches" "sandwiche". In a sample of 30,000
   recipes, fixing it linked only 14 more (Fried green tomatoes, Tres leches cake) and added a wrong one ("mojo
   rojo" to Rojões), so it is not worth a change now. Rule L1 reads "sandwiche" as "sandwich".

## Every recipe in the Food Graph (2026-11-22)

`FoodGraph.add_recipes` now adds every recipe as a node, with at most one edge, each from a source
(`scripts/knowledge/recipe_graph.py` writes the counts to `data/knowledge/recipe_graph_counts.json`):

| Edge | Recipes | Means |
|---|---:|---:|
| `recipe_of` | 73,326 | a recipe of one of our dishes |
| `named_for` | 4,234 | a recipe named after a food or drink entry ("Salmon") |
| `recipe_from` | 163,522 | no dish, but its source's labels name a place in the Food Taxonomy |
| none | 50,673 | no dish and no place the taxonomy has |

So 83% of the recipes now reach the place tree, against 27% through a dish alone. Nothing is inferred: a recipe
whose labels name no place, or a place the taxonomy lacks, stays a node without an edge.
