# Flag Review: How the Labels Were Made

Section 5.11 of the notebook compares the pipeline's 13 restriction flags with hand-made answers for blind samples of 200 recipes (50 per source). Each round is a fresh sample; no recipe appears in two rounds.

| Round | Sample | Answers | Purpose |
|---|---|---|---|
| 1 | `flag_review_sample_round1.csv` | `flag_review_labeled_round1.csv` | Found the weak spots; the keyword lists were then improved using its examples, so its scores are now optimistic |
| 2 | `flag_review_sample_round2.csv` | `flag_review_labeled_round2.csv` | Fresh sample drawn after the improvement: the fair measure of the current flags |

**Who labeled them:** Claude (an AI assistant), on 2026-10-04, from each recipe's ingredient list and dish name. The labeler never saw the pipeline's flag values. The labels are an independent second opinion, not a human gold standard: a team member should spot-check them, starting with the rows where they disagree with the flags.

## Rules used

- **What counts:** what the dish really contains. This includes the dish name: "Grilled Lamb Chops with Tzatziki" is not vegetarian even though its ingredient list only covers the sauce.
- **Hidden ingredients count:** for example, soy sauce contains wheat and soy, mayonnaise contains egg, za'atar and hummus contain sesame, dashi contains fish, oyster sauce contains shellfish, crackers, pastry, croutons, muffin mixes and noodles contain gluten, and macarons contain almond.
- **Blank = unknown:** answers that depend on the brand or region are left empty, and the scoring skips them. Examples: Worcestershire sauce (malt vinegar, which has gluten, in the UK only), "cider" (alcoholic in the UK, apple juice in the US), chocolate (often soy lecithin), gelatin (often pork), protein powder (whey or soy), Thai curry paste (sometimes shrimp paste).
- **Definitions:**
  - shellfish includes mollusks (clams, mussels, scallops, squid, conch, snails) as well as crustaceans;
  - coconut is not a tree nut (current FDA guidance); almond extract counts as almond; peanut oil counts as peanut;
  - oats are not counted as gluten unless the recipe also has wheat, barley or rye;
  - vinegars made from wine or sherry are not alcohol; vanilla extract is not counted as alcohol;
  - gelatin and marshmallows are not vegetarian; honey is vegetarian but not vegan.

## Round 1 (before the improvement)

Gluten was caught in only **81%** of the recipes that contain it. Most misses were wheat implied by a product name (crackers, pastry, spaghetti, croutons, English muffin, Bisquick, stuffing mix, baguette, burger bun). Other misses: dashi (fish), za'atar (sesame), macarons (tree nut), and meat or shellfish named only in the title ("... with Mussels"). False alarms: "butter lettuce" (dairy), "sherry vinegar" (alcohol), "gluten free bread" (gluten).

**What changed in 5.4.2:** the keyword lists were extended (wheat products, cheese names, dashi, za'atar, macarons, pesto, marshmallows and more), common false alarms became exceptions, and the flags now read the recipe name as well as the ingredients. Because dish names such as "bread" or "cookies" also describe gluten-free versions, a name that says "gluten-free", "GF" or "flourless" is not used for the gluten flag; this rule came from Food.com's own gluten-free tags, not from the review samples.

## Round 2 (fair measure of the current flags)

Recall is the share of recipes that really contain something and were flagged. It matters most, because a missed allergen is worse than an extra exclusion.

| Flag | Recipes with it | Recall | Precision |
|---|---|---|---|
| pork | 18 | 1.00 | 0.90 |
| alcohol | 21 | 1.00 | 0.95 |
| gluten | 96 | **0.96** (was 0.81) | 0.97 |
| dairy | 112 | 0.99 | 0.98 |
| egg | 52 | 0.98 | 1.00 |
| peanut | 5 | 0.80 | 1.00 |
| tree nut | 21 | 1.00 | 0.95 |
| fish | 23 | 1.00 | 0.88 |
| shellfish | 6 | 0.67 | 0.67 |
| soy | 11 | 0.91 | 0.83 |
| sesame | 6 | 0.83 | 1.00 |
| not vegetarian | 93 | 0.98 | 0.98 |
| not vegan | 170 | 0.99 | 0.99 |

Peanut, shellfish, soy and sesame have only 5 to 11 recipes each in the sample, so one miss moves their score a lot.

**Remaining misses (candidates for the next keyword update):** "soya sauce" (gluten, soy), "ground nut oil" (peanut), snails / escargots (shellfish, not vegetarian), hummus (sesame), waffles, pasty and pastini (gluten). **False alarms:** turkey kielbasa (pork), "chicken scampi" and "scalloped potatoes" (shellfish), and Hugging Face recipes without a "fish-free" or "dairy-free" label, which are flagged on purpose (the safe side). If the lists are updated with these, draw a round 3 to measure them fairly: add `3: <seed>` to `REVIEW_ROUNDS` in 5.11 and re-run the cell.

**Food.com's own tags (whole dataset):** our gluten flag agrees with the "gluten-free" tag on 88.5% of tagged recipes (90.5% before the change). The extra disagreements are mostly recipes whose ingredients list plain "flour", "bread" or "pasta" without saying they are gluten-free versions; flagging them is the safe side.
