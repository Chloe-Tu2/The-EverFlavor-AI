# Food entry review rubric

Proposed by med27-coder, 2026-11-25, for [review item 39](needs_human_review.md): when a food entry (not a Wikidata
"dish") should count toward a country's coverage. **Status: proposed, not applied.** Coverage still counts dishes
only; a person decides each entry with this rubric, and the counting rule changes only when the item is answered.

## How the pipeline works today

- An entry is a **dish** when its Wikidata class is under "dish" (Q746549); only dishes count toward coverage,
  country scores and the atlas debt.
- Other foods (under "food", Q2095) and drinks (under "drink", Q40050) are kept in `data/knowledge/dishes.jsonl`
  as `"kind": "food or drink"` and shown in the app, but do not count.
- Ingredients and places linked from a cuisine page are dropped unless Wikidata classes them as a food.

## Tier A: counts as coverage

Prepared dishes, national dishes, meals, soups, stews, breads, desserts, confections and prepared ceremonial
foods. Evidence: the dish's own article, a cuisine page, the Wikidata class and the article's intro. Examples:
Mansaf, Hummus, Torta Tre Monti; Laplap ("the national dish of Vanuatu") once a person confirms it, since Wikidata
classes it as a food today.

## Tier B: counts after a person's review

Foods Wikidata calls a food but the sources call a dish, national foods, prepared traditional foods and other
borderline cases. The reviewer asks: is it prepared? Is it eaten as a dish? Does the source call it a dish? Does
it represent the cuisine in its own right? Examples: Footi (a sauce, Guinea), Puleleti (a confection, Tuvalu).

## Tier C: does not count

Ingredients, raw foods, single agricultural products, spices, unprepared fruits and base ingredients. Examples:
rice, cassava, cinnamon.

## Tier D: beverages, tracked apart

Drinks may count toward a country's cultural representation, never toward dish coverage. Examples: Zoomkoom,
Kuwaiti tea, coffee drinks, traditional alcohols. A future "beverage coverage" metric would count them; none exists
yet.

## Applying it

A person writes the tier and a note per entry. Claude may prepare the sheet (the entry, its Wikidata class, its
intro, the tier the wording suggests) but never assigns a tier. Until item 39 is answered, no tier changes a count.
