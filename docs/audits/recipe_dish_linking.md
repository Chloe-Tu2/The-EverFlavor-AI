# Recipe to dish linking (audit, 2026-11-21)

How many recipes the app links to a dish, how it links them, and where it fails. Read-only: nothing in the app
changed. Numbers from `scripts/knowledge/recipe_dish_links.py`, which writes the counts per dish to
`data/knowledge/dish_recipe_counts.json`.

## How a recipe finds its dish

The recipe cards clean the posted title first (`dish_names.clean_title`: "Grandma's Best Lasagna Recipe" becomes
"lasagna"; the table keeps it as `dish_name`), then the app and the waiter use `waiter.Knowledge.find` on it: an
exact name, else the name before "with / on / in / over / served / topped", else the longest known dish name
inside it (a one-word name only at the end; broad words such as "salad" never count). The recipe's country
breaks a tie. The script uses a faster version of the same rules and first checks that both give the same dish
on 3,000 random recipes.

## The numbers

| | Recipes | Share |
|---|---:|---:|
| All recipes | 291,755 | 100% |
| Linked to a dish or food | 80,741 | 27.7% |
| Exact name | 9,464 | 3.2% |
| Name before "with ..." | 7,758 | 2.7% |
| A dish name inside the name | 63,519 | 21.8% |
| Not linked | 211,014 | 72.3% |

By source: Food.com 58,750 of 218,024 (26.9%), CulinaryDB 11,271 of 35,325 (31.9%), the Hugging Face set 10,550
of 37,823 (27.9%), TheMealDB 170 of 583 (29.2%).

Dishes: 1,522 of the 3,201 dishes in the knowledge notebook have at least one recipe (47.5%); 1,679 have none
(they can only be shown as knowledge, never as a recipe). A dish with recipes has 6 at the median and 50.3 on
average; the most linked are Pork chop (1,910), Peanut butter (1,905), Pizza (1,614), Cheesecake (1,204) and
Ice cream (1,188).

## Where it fails

1. **Most unlinked names are general.** 44% of the unlinked names end in a broad word (salad 10,808, chicken
   7,426, soup 6,193, cake 6,044, cookies 4,808, casserole 4,748). These are not one dish, and leaving them
   unlinked is right.
2. **A dish name in the middle of a name.** 10,817 of the "inside" links use a name that is not at the end.
   Many are fine ("lentil soup for students"), but some are wrong: "peanut butter blossoms" and "chunky monkey
   cookies" link to Peanut butter (1,876 such links), "brown butter chicken jus" to Butter chicken. In a quick
   look at 15 of them, about 4 were wrong. A person should check a larger sample before the rule changes.
3. **Foods, not dishes.** 4,234 recipes link to a food or drink entry because the name is just that word (Green
   bean 247, Salmon 230, Shrimp 204). The link is right; such pages have no dish facts to show.
4. **Plurals.** The name cleaner makes "potatoes" "potatoe" and "sandwiches" "sandwiche". In a sample of 30,000
   recipes, fixing it linked only 14 more (Fried green tomatoes, Tres leches cake) and added a wrong one ("mojo
   rojo" to Rojões), so it is not worth a change now.

## What this means for the next steps

- The dish/recipe split in the Food Graph can use these links as they are for about a quarter of the recipes.
  The other three quarters stay recipes without a dish, which the graph already allows.
- Before any rule change: a hand-checked sample of the middle-of-name links (item 2), recorded as a policy.
- Coverage work can use `dish_recipe_counts.json`: a dish with no recipes is a gap in recipes, not in knowledge.
