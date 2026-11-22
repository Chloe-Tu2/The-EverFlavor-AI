# Recipe to dish linking (audit, 2026-11-21)

How many recipes the app links to a dish, how it links them, and where it fails. Read-only: nothing in the app
changed. Numbers from `scripts/knowledge/recipe_dish_links.py`, which writes the counts per dish to
`data/knowledge/dish_recipe_counts.json`.

## How a recipe finds its dish

The app (and the waiter) uses `waiter.Knowledge.find` on the recipe name: an exact name, else the name before
"with / on / in / over / served / topped", else the longest known dish name inside the title (a one-word name only
at the end; broad words such as "salad" never count). The recipe's country breaks a tie. The script uses a faster
version of the same rules and first checks that both give the same dish on 3,000 random recipes.

## The numbers

| | Recipes | Share |
|---|---:|---:|
| All recipes | 291,755 | 100% |
| Linked to a dish or food | 76,745 | 26.3% |
| Exact name | 1,613 | 0.6% |
| Name before "with ..." | 7,172 | 2.5% |
| A dish name inside the title | 67,960 | 23.3% |
| Not linked | 215,010 | 73.7% |

By source: Food.com 56,299 of 218,024 (25.8%), CulinaryDB 10,903 of 35,325 (30.9%), the Hugging Face set 9,376 of
37,823 (24.8%), TheMealDB 167 of 583 (28.6%).

Dishes: 1,525 of the 3,201 dishes in the knowledge notebook have at least one recipe (47.6%); 1,676 have none
(they can only be shown as knowledge, never as a recipe). A dish with recipes has 5 at the median and 48.6 on
average; the most linked are Pork chop (1,908), Peanut butter (1,906), Pizza (1,518), Ice cream (1,190) and
Cheesecake (1,138).

## Where it fails

1. **Most unlinked titles are general.** 43% of the unlinked titles end in a broad word (salad 10,732, chicken
   7,188, soup 5,977, cake 5,954, cookies 4,753, casserole 4,600). These are not one dish, and leaving them
   unlinked is right.
2. **A dish name in the middle of a title.** 12,764 of the "inside" links use a name that is not at the end of
   the title. Many are fine ("lentil soup for students"), but some are wrong: "peanut butter blossoms" and
   "chunky monkey cookies" link to Peanut butter (1,881 such links), "Brown Butter Chicken Jus" to Butter
   chicken. In a quick look at 15 of them, about 4 were wrong. A person should check a larger sample before the
   rule changes.
3. **Foods, not dishes.** 2,639 recipes link to a food or drink entry because the title is just that word
   (Salmon 205, Green bean 201, Shrimp 176). The link is right; such pages have no dish facts to show.
4. **Plurals.** The name cleaner makes "potatoes" "potatoe" and "sandwiches" "sandwiche". Fixing it links only
   about 0.2% more recipes (Fried green tomatoes, Tres leches cake) and adds a wrong one ("mojo rojo" to
   Rojões), so it is not worth a change now.

## What this means for the next steps

- The dish/recipe split in the Food Graph can use these links as they are for about a quarter of the recipes.
  The other three quarters stay recipes without a dish, which the graph already allows.
- Before any rule change: a hand-checked sample of the middle-of-title links (item 2), recorded as a policy.
- Coverage work can use `dish_recipe_counts.json`: a dish with no recipes is a gap in recipes, not in knowledge.
