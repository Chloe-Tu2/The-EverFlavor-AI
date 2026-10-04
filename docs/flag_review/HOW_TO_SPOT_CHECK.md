# How to Spot-Check the Flag Labels

The answers in `flag_review_labeled_round*.csv` were made by an AI assistant (Claude), not by a person. Before we trust the accuracy numbers in the README, a team member should check the cases where those answers and the pipeline's flags **disagree**: that is where one of the two is wrong. It takes about 30-45 minutes per round, and no coding.

## 1. Get the file

Pick the latest round (currently **round 3**): `docs/flag_review/flag_review_disagreements_round3.csv`.

- **On GitHub (nothing to install):** open https://github.com/Chloe-Tu2/The-EverFlavor-AI/tree/main/docs/flag_review, click the file, then **Download raw file** (the download icon).
- **In VS Code / Antigravity:** pull the repo (`git pull`) and open the file from the `docs/flag_review/` folder.

## 2. Open it

- **Excel or Google Sheets:** open the CSV directly (in Google Sheets: File > Import > Upload).
- **VS Code:** right-click the file > **Open in Data Wrangler**, or just open it (Rainbow CSV colors the columns).

Each row is one recipe and one flag:

| Column | Meaning |
|---|---|
| `recipe_name`, `ingredients` | What to read |
| `flag` | The question, for example `contains_gluten` or `vegetarian` |
| `answer` | The AI reviewer's answer: 1 = yes, 0 = no |
| `pipeline_flag` | What the pipeline says: 1 = yes, 0 = no |
| `team_check` | **Your job:** fill this in |

## 3. Fill in `team_check`

For each row, read the ingredients and the name, decide the truth, and write:

- `answer` if the AI reviewer is right,
- `pipeline` if the pipeline is right,
- `unsure` if it depends on the brand or you cannot tell (add a note after it if useful, e.g. `unsure: depends on the sausage`).

Use the rules in [labeling_notes.md](labeling_notes.md) (for example: soy sauce contains wheat, shellfish includes clams and snails, coconut is not a tree nut, honey is not vegan). If you disagree with a rule itself, write it down and tell the team.

## 4. Send it back

- **With git:** save the file in `docs/flag_review/` under the same name, then commit and push. The notebook keeps a disagreements file once `team_check` has been started, so your work is never overwritten.
- **Without git:** send the filled-in file to whoever maintains the notebook (or upload it to the team's shared folder) so they can commit it.

## What happens next

- Rows marked `pipeline` mean the AI answer was wrong: fix that answer in `flag_review_labeled_round3.csv` (same `recipe_id`, same flag column) and re-run section 5.12; the accuracy numbers update.
- Rows marked `answer` are real pipeline mistakes: they become the next keyword fixes in section 5.4.2 (and a new review round measures them).
