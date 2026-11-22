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
| 11 | The approved dish photos are being fetched to a staging folder: check the contact sheets by eye; nothing reaches the app before `apply` | `data/raw/dish_photos_approved/sheets/` (local) |
| 12 | 357 backlog dishes need a person (country not in the place tree, not a country today, in many families) | `data/knowledge/atlas/publication_review_queue.json` |
| 13 | The Balkans and Siberia: which published source should draw them as regions? | `docs/audits/global_culinary_atlas.md` |
| 14 | Should v0.7.1 be tagged at 344aeb0, and Dependabot PR #28 merged? | GitHub |
