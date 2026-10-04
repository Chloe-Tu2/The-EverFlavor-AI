# Flag Review: How the Labels Were Made

Section 5.12 of the notebook compares the pipeline's restriction flags with hand-made answers for blind samples of 200 recipes (50 per source). Each round is a fresh sample; no recipe appears in two rounds.

| Round | Sample | Answers | Purpose |
|---|---|---|---|
| 1 | `flag_review_sample_round1.csv` | `flag_review_labeled_round1.csv` | Found the weak spots; the keyword lists were then improved using its examples, so its scores are now optimistic |
| 2 | `flag_review_sample_round2.csv` | `flag_review_labeled_round2.csv` | Fresh sample after the first improvement; its misses led to a second, smaller fix, so its scores are now optimistic too |
| 3 | `flag_review_sample_round3.csv` | `flag_review_labeled_round3.csv` | Fresh sample after both fixes, with the six diet flags added: **the fair measure of the current flags** |

Each labeled round also has `flag_review_disagreements_round<N>.csv`: the rows where the answers and the flags disagree, for the team spot-check described in [HOW_TO_SPOT_CHECK.md](HOW_TO_SPOT_CHECK.md).

**Who labeled them:** Claude (an AI assistant), on 2026-10-04 (rounds 1-2) and 2026-10-05 (round 3), from each recipe's ingredient list and dish name. The labeler never saw the pipeline's flag values. The labels are an independent second opinion, not a human gold standard: a team member should spot-check them, starting with the rows where they disagree with the flags.

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
- **The six diet flags (round 3):** meat = meat or poultry, including broth and stock made from them (gelatin alone does not count); beef includes veal, beef stock and suet; root vegetables include potato, carrot, yam, radish, horseradish and fresh ginger (dried ground ginger does not count); onion and garlic include leek, shallot, chive, scallion and onion or garlic powder.

## Round 1 (before the improvement)

Gluten was caught in only **81%** of the recipes that contain it. Most misses were wheat implied by a product name (crackers, pastry, spaghetti, croutons, English muffin, Bisquick, stuffing mix, baguette, burger bun). Other misses: dashi (fish), za'atar (sesame), macarons (tree nut), and meat or shellfish named only in the title ("... with Mussels"). False alarms: "butter lettuce" (dairy), "sherry vinegar" (alcohol), "gluten free bread" (gluten).

**What changed in 5.4.2:** the keyword lists were extended (wheat products, cheese names, dashi, za'atar, macarons, pesto, marshmallows and more), common false alarms became exceptions, and the flags now read the recipe name as well as the ingredients. Because dish names such as "bread" or "cookies" also describe gluten-free versions, a name that says "gluten-free", "GF" or "flourless" is not used for the gluten flag; this rule came from Food.com's own gluten-free tags, not from the review samples.

## Round 2 (after the first improvement)

Scores below are from when round 2 was the newest sample. Recall is the share of recipes that really contain something and were flagged. It matters most, because a missed allergen is worse than an extra exclusion.

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

**What changed after round 2:** "soya sauce", "waffle", "pasty" and "pastina" (gluten), "ground nut" oil (peanut), snails and escargots (shellfish, not vegetarian), hummus and baba ganoush (sesame) were added, and turkey or chicken sausages no longer count as pork. Round 3 measures the result.

**Food.com's own tags (whole dataset):** our gluten flag agrees with the "gluten-free" tag on 88.4% of tagged recipes (90.5% before the changes). The extra disagreements are mostly recipes whose ingredients list plain "flour", "bread" or "pasta" without saying they are gluten-free versions; flagging them is the safe side.

## Round 3 (fair measure of the current flags)

| Flag | Recipes with it | Recall | Precision |
|---|---|---|---|
| pork | 29 | 0.97 | 0.97 |
| alcohol | 29 | 1.00 | 0.97 |
| gluten | 100 | 0.96 | 0.99 |
| dairy | 113 | 1.00 | 1.00 |
| egg | 59 | 0.98 | 1.00 |
| peanut | 9 | 1.00 | 0.90 |
| tree nut | 25 | 1.00 | 1.00 |
| fish | 19 | 1.00 | 0.86 |
| shellfish | 12 | **0.83** | 0.91 |
| soy | 10 | 1.00 | 0.91 |
| sesame | 9 | 1.00 | 1.00 |
| meat | 82 | 0.99 | 0.95 |
| beef | 28 | 1.00 | 0.97 |
| gelatin | 2 | 1.00 | 1.00 |
| honey | 11 | 1.00 | 0.92 |
| root vegetable | 47 | 1.00 | 1.00 |
| onion / garlic | 113 | 1.00 | 1.00 |
| not vegetarian | 102 | 0.98 | 0.98 |
| not vegan | 173 | 0.99 | 0.99 |

Shellfish is the one flag below 0.95 (10 of 12 found); peanut, shellfish, soy, sesame, gelatin and honey have fewer than 15 cases each, so one miss moves their score a lot. Fish precision is lower on purpose: Hugging Face recipes without a "fish-free" label are flagged. The exact rows behind every miss are in `flag_review_disagreements_round3.csv`.

## Round 3 review (section 5.13)

Every one of the 30 round 3 disagreements was traced to what set the flag (`why_flagged` in the disagreements file):

| Kind | Rows | Outcome |
|---|---|---|
| Keyword bugs | 17 | Fixed in `src/everflavor/flags.py`: jamón (pork), merguez (not pork), "sherry wine vinegar" (not alcohol), "roll" and rawa (gluten), "frozen seafood mix" (shellfish), mock caviar (not fish), portobello and swordfish "steak" (not meat), oyster mushrooms (not shellfish) |
| Hidden ingredients | 2 | Christmas pudding (gluten, egg) added to `COMPOUND_INGREDIENTS`, the list of ready-made ingredients checked against Open Food Facts |
| AI answer wrong | 4 | Fish sauce does contain fish; "maple syrup or honey" can contain honey |
| Matter of definition | 7 | Recorded as team policies in `flag_policies.csv` |

Because round 3 was used for these fixes, its scores are now optimistic; round 4 (`flag_review_sample_round4.csv`) is the fresh sample for the next measurement.

**Rules now set by team policy** (`flag_policies.csv`): two rules above were the AI labeler's own choices and are overridden by decisions a person made. Oats now count as gluten unless labeled gluten-free (P1), and gelatin counts as meat (P2). Answers in rounds 1-3 that follow the old rules show up as disagreements until they are corrected.

**New flags:** `contains_red_meat` (meat from mammals, pork included), `contains_poultry` (white meat) and `contains_processed_meat` (cured, salted, smoked or fermented meat), following USDA and WHO / IARC definitions (policies P8 and P9). Rounds 1-3 were labeled before these flags existed, so they are first measured in round 4.
