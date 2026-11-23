# The safety engine

How EverFlavor decides whether a recipe is safe for a person. The rules live in plain code in `src/everflavor/`;
there is no `safety/` package, so this page plays the part of its README. It describes the code as it is; it does
not change a rule.

## Purpose

Say, for one person and one recipe, which allergy, medical screen, religious or ethical diet a recipe breaks, how
serious that is and how sure we are, and which line or step caused it. **A language model never decides safety:**
the gate is plain code, its answer cannot be overridden, and the app and the AI models only show or explain it.
Flags only ever add cautions; diet labels say "halal-friendly ingredients", never "halal"; medical profiles are
screens, not advice.

## How it works

| Step | File | What it does |
|---|---|---|
| 1. Flags | `flags.py` | Keyword rules (with spellings and hidden words) mark each recipe's ingredients and name: the same rules build the recipe table, the validation checks and the filter, so they always agree |
| 2. Diets | `diets.py` | Each diet is a rule over the flags |
| 3. Profile | `restrictions.py` | Every rule a person can set, its category and how serious a match is (unsafe, not their profile, worth a look) |
| 4. Gate | `safety.py` | `UserProfile` and `check_recipe`: checks free-text lines and the dish name, and says which line broke which rule, so the Chef Agent can rewrite the recipe |
| 5. Preparation | `preparation.py` | How a dish is made as a risk of its own: raw or undercooked, fermented, and foods the steps bring in that the lines do not show |
| 6. Confidence | `confidence.py` | How sure a finding is, apart from how serious: verified, likely, possible or unknown (`data/reference/may_contain.csv`, each with a source) |
| 7. Filter | `recommend.py` | `passes_safety_filter` re-checks each recommended recipe with the same rules |

## Inputs

- A person's profile (`UserProfile`); kept on their machine, never committed (`docs/ethics_privacy.md`).
- A recipe's ingredient lines, name and steps.
- The rule tables: the flag policies (`docs/flag_review/flag_policies.csv`), the allergen words in Spanish, French
  and Italian (`docs/flag_review/allergen_words_es_fr_it.csv`, proposed, policy P26) and `may_contain.csv`.

## Outputs

For each recipe: pass or not, each finding with its rule, category, severity, confidence and the line or step
that caused it. Nothing is written to disk by the gate; the audit log records decisions, never the person's words.

## Tests

`tests/test_everflavor.py`, `test_confidence.py`, `test_preparation.py`, `test_alcohol.py`, `test_allergen_words.py`,
`test_product_cautions.py`, `test_recipe_check.py`, and the flag review rounds in `docs/flag_review/`.

## Ownership

Team EverGlow. A change to a safety rule or an allergen word needs two people, and the second is not the author
(`docs/governance/human_approval_workflow.md`). Every judgment call is a recorded policy with who decided it.

## Future work

- The second review of policy P26 (allergen words in Spanish, French and Italian):
  `docs/governance/needs_human_review.md`.
- The ingredient merges, after the team's review (`docs/flag_review/HOW_TO_REVIEW_INGREDIENT_MERGES.md`).
- Moving these files into a `safety/` package is a code change for the team to decide; this page would become its
  README.
