# How to Verify the Flags (Human Review)

The answers in `flag_review_labeled_round*.csv` were made by an AI assistant (Claude), not by a person. An AI checking an AI is not independent, so a team member makes the final decisions. The notebook (section 5.13) gathers the evidence automatically; your part is three kinds of decisions, with no coding:

| Decision | File | Time |
|---|---|---|
| 1. Approve the flag policies | `flag_policies.csv` | about 5 minutes, once |
| 2. Approve or reject hidden-allergen suggestions | `compound_ingredients_review.csv` | about 10-15 minutes |
| 3. Check a round's disagreements and sign it off | `flag_review_disagreements_round<N>.csv`, then `human_signoff.csv` | about 10-20 minutes per round |

## Get and open the files

- **On GitHub (nothing to install):** open https://github.com/Chloe-Tu2/The-EverFlavor-AI/tree/main/docs/flag_review, click a file, then **Download raw file** (the download icon).
- **In VS Code / Antigravity:** pull the repo (`git pull`) and open the files from `docs/flag_review/`. Right-click a CSV > **Open in Data Wrangler** to see it as a table.
- **Excel or Google Sheets:** open the CSV directly (Google Sheets: File > Import > Upload). Save it back as CSV.

## 1. Policies (`flag_policies.csv`)

Some flags depend on a definition, not a fact: do oats count as gluten? Is fish "white meat"? Each row is one question with the decision, the reason and its source.

- Rows with `status` = `proposed` need you: if you agree, write `approved`, your name in `decided_by` and the date in `decided_on` (YYYY-MM-DD).
- If you disagree, change `decision` and tell the team: the keyword rules in `src/everflavor/flags.py` must then change to match.

## 2. Hidden allergens in ready-made ingredients (`compound_ingredients_review.csv`)

A recipe that lists "ranch dressing" does not list the milk and egg inside it. For each ready-made ingredient, the notebook looked up real products on Open Food Facts:

| Column | Meaning |
|---|---|
| `ingredient`, `recipes` | The ingredient and how many recipes use it |
| `products` | How many Open Food Facts products with that name were found (-1: the search failed) |
| `rule_flags` | What our keyword rules already flag |
| `declared_shares` | Share of those products whose label declares each allergen |
| `suggested_flags` | Allergens to add (declared by at least 60% of at least 5 products) |
| `team_decision` | **Your job:** `approve` or `reject` |

Only rows with `suggested_flags` need a decision. Approve when the allergen is usually in that product (milk in white chocolate). Reject when the products found are not what recipes mean (write why in `notes`). Suggestions are already applied in the code (they only add flags, the safe direction) until you reject them.

## 3. Disagreements and sign-off

Pick the latest labeled round (currently **round 3**): `flag_review_disagreements_round3.csv`. Each row is one recipe and one flag where the AI's answer and the pipeline differ:

| Column | Meaning |
|---|---|
| `recipe_name`, `ingredients` | What to read |
| `flag` | The question, for example `contains_gluten` or `vegetarian` |
| `answer` | The AI reviewer's answer: 1 = yes, 0 = no |
| `pipeline_flag` | What the pipeline says: 1 = yes, 0 = no |
| `why_flagged` | The keyword that set the flag, or where else it came from |
| `team_check` | **Your job:** `answer`, `pipeline` or `unsure` |

Write `answer` if the AI reviewer is right, `pipeline` if the pipeline is right, and `unsure` if it depends on the brand (add a note, for example `unsure: depends on the sausage`). Use the rules in [labeling_notes.md](labeling_notes.md) and the policies in `flag_policies.csv`.

When you are done, add **one row** to `human_signoff.csv`: the round, your name, the date, how many rows you checked, and any notes. The notebook's checklist ticks "signed off by a person" only when this row exists.

## Send it back

- **With git:** save the files under the same names in `docs/flag_review/`, then commit and push. The notebook keeps your decisions: a disagreements file is never overwritten once `team_check` has been started, and `team_decision` values are always kept.
- **Without git:** send the filled-in files to whoever maintains the notebook so they can commit them.

## What happens next

- Rows marked `pipeline` mean the AI answer was wrong: fix that answer in `flag_review_labeled_round<N>.csv` and re-run section 5.12, so the accuracy numbers update.
- Rows marked `answer` are real pipeline mistakes: they become keyword fixes in `src/everflavor/flags.py`, and the next fresh round (round 4) measures them.
