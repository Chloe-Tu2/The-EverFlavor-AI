# Needs human review

Questions an AI assistant stopped at instead of guessing ([human_approval_workflow.md](human_approval_workflow.md)).
Each stays here until a person decides; then the decision is recorded where it belongs and the row is removed.
Last updated 2026-11-22 by Claude (AI).

## Privacy and security

| # | Question | Found by | Where |
|---|---|---|---|
| 1 | The User-Agent of `src/everflavor/sources.py` gives the contact `team@everglow.com`. Is it a real, team-owned address? If not, use the repository link instead, as the other scripts do | PII scan | `src/everflavor/sources.py` line 200 |
| 2 | A photographer's e-mail address was in a Commons image description stored in `data/knowledge/media/commons_meta.json` (merged in PR #36, removed in the next commit; it is public on Commons). Rewrite git history, or accept it? | PII scan | git history |
| 3 | The PII audit lists 16 phone-number and 13 street-address hits; most are numbers in an SVG drawing, test fixtures and street names in photo file names. Confirm none is a private person's | PII scan | [pii_audit_report.md](pii_audit_report.md) |
| 4a | Switch on GitHub's private vulnerability reporting (Settings > Code security), then point `SECURITY.md` at the form | Governance sprint | repository settings |
| 4 | CODEOWNERS was not created: who owns which folder (safety engine, data, app, docs) is the team's choice, and the file would request reviews automatically | Governance sprint | `.github/CODEOWNERS` |

## Licences

| # | Question | Where |
|---|---|---|
| 5 | CulinaryDB and RecipeDB (CC BY-NC-SA) and Open-Meteo are non-commercial: fine for the class project; decide before any commercial use | [license_compliance.md](license_compliance.md) |
| 6 | Add a note next to the MIT licence that it covers the code, not the data (share-alike and ODbL data keep their own licences) | `README.md`, `LICENSE` |
| 7 | Confirm the licence of the Hugging Face recipe photos (counted as "to confirm" today) | `docs/audits/image_coverage_report.md` |
| 8 | Confirm the terms of Food.com (research use) and the USDA SNAP-Ed seasonal guide ("not stated") before a public launch | `docs/sources.md` |

## Data decisions waiting for the team

| # | Question | Where |
|---|---|---|
| 9 | Rule L1 (a dish named before a kind of dish is that dish's flavour) is proposed: review the sheet, mainly the 1,062 groups with 1-2 recipes nobody has read | `docs/audits/dish_link_review.csv` |
| 10 | Policy P26 (allergen words in Spanish, French and Italian) is proposed: a second person reviews the sheet (safety rules need two) | `docs/flag_review/allergen_words_es_fr_it.csv` |
| 11 | The 1,739 approved photos are fetched (1,144 pass the photo check). Check the 72 passed contact sheets by eye (a sample of 4 found nothing wrong), decide whether to rescue failed ones, then finish `apply`; nothing reaches the app before | [approved_photos_check.md](../audits/approved_photos_check.md), `data/raw/dish_photos_approved/sheets/` (local) |
| 12 | 357 backlog dishes need a person (country not in the place tree, not a country today, in many families) | `data/knowledge/atlas/publication_review_queue.json` |
| 13 | The Balkans and Siberia: which published source should draw them as regions? | `docs/audits/global_culinary_atlas.md` |
| 14 | Should v0.7.1 be tagged at 344aeb0, and Dependabot PR #28 merged? | GitHub |
| 15 | The maintenance brief's dish quality weights add up to 110 (recipe 10, map 5, "Walter context" 10); ours add up to 100 (recipe 5, fun facts 10, no map). Keep ours, or adopt a new weighting? | [documentation_gap_report.md](documentation_gap_report.md) |
| 16 | 168 Wikidata countries of origin are not in the place tree, so those dishes get no `origin` edge. Some look like plain name forms ("People's Republic of China", 157 dishes; "Hong Kong"); others are not one country today ("Korea" 83, "Scotland" 43, "Levant", "Ottoman Empire", "Soviet Union"). Which become aliases, and which stay unplaced? | [food_graph_validation_report.md](../audits/food_graph_validation_report.md) |
| 17 | 234 dishes have more than one country of origin on Wikidata, and 914 sit in a cuisine list that is not their origin. Both can be right; should the dish page show one first, and which? | `data/knowledge/quality/food_graph_validation.json` |
| 18 | The stricter provenance check: 53 data files state no version and 27 no attribution. Should derived audit files carry a version and the credit of their sources? | [data_provenance_report.md](data_provenance_report.md) |
| 19 | CI gaps: Ruff skips `scripts/`, PyMarkdown skips the root `SECURITY.md` and `GOVERNANCE.md`, no dead-link check. Add them? (workflows not changed) | [ci_guardrails_report.md](ci_guardrails_report.md) |
| 20 | 299 draft and archive files are tracked (the pixel-art history, `docs/plans/README_0.7.1_draft.md`). Keep them in git, or move the art history to a release asset? | [repository_hygiene_report.md](repository_hygiene_report.md) |
