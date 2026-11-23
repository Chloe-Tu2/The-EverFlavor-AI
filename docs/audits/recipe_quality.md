# Recipe quality (audit, 2026-11-23)

What each recipe has and lacks, by source. Counts only: no recipe was changed or removed. Built by `scripts/knowledge/recipe_quality_audit.py`; the numbers are in `data/knowledge/recipe_quality.json`. The limits (a day of time, 50 servings, 40 ingredients, 3,000 kcal a serving) only say where a person should look.

| Check | All | Food.com | CulinaryDB | Hugging Face | TheMealDB |
|---|---:|---:|---:|---:|---:|
| Recipes | 291,755 | 218,024 | 35,325 | 37,823 | 583 |
| name missing or under 3 letters | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| name in capitals only | 149 (0%) | 0 (0%) | 11 (0%) | 137 (0%) | 1 (0%) |
| no ingredients | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| one ingredient | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| over 40 ingredients | 4 (0%) | 1 (0%) | 3 (0%) | 0 (0%) | 0 (0%) |
| no steps | 73,149 (25%) | 1 (0%) | 35,325 (100%) | 37,823 (100%) | 0 (0%) |
| steps under 40 characters | 808 (0%) | 807 (0%) | 0 (0%) | 0 (0%) | 1 (0%) |
| no servings | 117,595 (40%) | 81,687 (37%) | 35,325 (100%) | 0 (0%) | 583 (100%) |
| over 50 servings | 676 (0%) | 676 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| no time given (an estimate is shown) | 73,731 (25%) | 0 (0%) | 35,325 (100%) | 37,823 (100%) | 583 (100%) |
| over a day of time | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| no nutrition | 35,908 (12%) | 0 (0%) | 35,325 (100%) | 0 (0%) | 583 (100%) |
| nutrition not plausible | 10,396 (4%) | 8,913 (4%) | 0 (0%) | 1,483 (4%) | 0 (0%) |
| over 3,000 kcal a serving | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| no country | 65,730 (23%) | 55,245 (25%) | 4,006 (11%) | 6,479 (17%) | 0 (0%) |
| no photo of its own | 143,410 (49%) | 106,713 (49%) | 35,325 (100%) | 1,372 (4%) | 0 (0%) |
| no photo at all (neither its own nor its dish's) | 108,991 (37%) | 81,436 (37%) | 26,543 (75%) | 1,012 (3%) | 0 (0%) |
| own photo checked and rejected | 1,415 (0%) | 303 (0%) | 0 (0%) | 1,112 (3%) | 0 (0%) |
| no source link | 253,375 (87%) | 218,024 (100%) | 35,325 (100%) | 0 (0%) | 26 (4%) |
| same dish name and ingredients as another | 690 (0%) | 478 (0%) | 34 (0%) | 178 (0%) | 0 (0%) |
| **complete: ingredients, steps, servings and nutrition** | 136,336 (47%) | 136,336 (63%) | 0 (0%) | 0 (0%) | 0 (0%) |

## What it means

- The most common gaps: no source link (253,375), no photo of its own (143,410), no servings (117,595), no photo at all (neither its own nor its dish's) (108,991), no time given (an estimate is shown) (73,731).
- A recipe without steps or servings can still be recommended (its flags come from its ingredients), but its page has less to show; the planner's recipe page work should show what is missing, not hide it.
- Steps, servings and a source link are missing for whole sources (CulinaryDB and the Hugging Face set come without steps in our tables, Food.com without links), not for single recipes: filling them means a source that has them, never writing them.
- Recipes with the same cleaned dish name and the same ingredients: most are within one source (Food.com 478); whether they are the same recipe, and merging them, is for a person to check.
