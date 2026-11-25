# Curator handoff (2026-11-24)

Read this first in a new session, then [atlas_health.md](atlas_health.md) and [review_impact.md](review_impact.md). From `scripts/knowledge/atlas_health.py`; the history is in `data/knowledge/atlas/atlas_health_history.jsonl`. **Audit only.**

## What improved (first snapshot, nothing to compare yet)

- nothing measured changed

## What regressed

- nothing

## What is blocked (waiting on a person)

- 0.8.0: Coverage counting rule confirmed (review item 21), then world coverage shown in the app
- 0.8.0: Staged photos signed off (the 72 passed contact sheets), then linked: about 203 dishes become rich
- 0.8.0: Cuisine image fallbacks, checked by a person
- 0.8.0: Items 24, 28, 29 and 30 (moved dishes, country scores, sprint entries) answered
- 0.9.0: Region pages shown in the app
- 0.9.0: Indigenous tags reviewed by the rubric (item 26) before the app shows any
- 0.9.0: At least 100 reviewed dish facts (`data/knowledge/review/focus_review.csv`)

## What needs a person first

- Item 21: coverage counting rule and weights
- Cuisine photo fallbacks
- Items 24, 28, 29, 30: sprint moves, country scores, sprint 4 entries

## What should happen next (Claude)

- Quality campaign with the most countries Claude can work on alone: **no culinary region** (101 countries; first Bahrain, New Caledonia, Rwanda, Samoa, Tajikistan, The Bahamas, Central African Republic, Antigua and Barbuda).
- Coverage campaigns in the planner's order, as far as their review items allow.
- End the session by rerunning the audit chain so this page is current.
