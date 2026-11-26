# Curator handoff (2026-11-25)

Read this first in a new session, then [atlas_health.md](atlas_health.md), [review_impact.md](review_impact.md) and [release_readiness.md](release_readiness.md). From `scripts/knowledge/atlas_health.py`; the history is in `data/knowledge/atlas/atlas_health_history.jsonl`. **Audit only.**

## Generated at

- Date: 2026-11-25
- Time: 21:37
- Git commit: b96b8dd+work (compared with b710ac9+work, 2026-11-25)

## Current status

- Branch: policy/review-batch-24-40
- Campaign: Q1. Regional source discovery (the first on the campaign scoreboard, in the planner's order)
- Version: 0.7.2
- Release readiness 0.8: 6 of 9 conditions done
- Release readiness 0.9: 2 of 10 conditions done
- Release readiness 1.0: 3 of 3 coverage targets met; the rest wait on reviews

## Headline

- Coverage: 70.6%
- UN members with a dish: 163 of 193
- Atlas debt: 3.15 per country
- Regional debt: 116 countries
- Story debt: 26 countries
- Campaign: Q1. Regional source discovery
- Blocked by: source (a second free regional source (Wikidata links few dishes, item 36))

## Atlas debt

- Current debt: 538 (3.15 per country)
- Debt change: atlas debt 558 -> 538; debt per country 3.26 -> 3.15
- Top debt categories:
  1. no culinary region: 116 countries, 348 points
  2. one dish only: 28 countries, 56 points
  3. no story: 26 countries, 52 points
- Highest-debt regions (per country):
  1. Oceania / Polynesia: 8.5
  2. Oceania / Melanesia: 8.0
  3. Oceania / Micronesian Region: 6.0

## Coverage

- world culinary coverage (%): 70.6
- Africa coverage (%): 54.5
- Oceania coverage (%): 35.2
- countries with a dish: 171
- UN members with a dish: 163
- Change since the last run: world culinary coverage (%) 70.0 -> 70.6; Africa coverage (%) 52.8 -> 54.5; Oceania coverage (%) 33.8 -> 35.2

## Representation

- dish families and categories: 710
- country pages: 168
- region pages: 30
- countries with three dishes or more: 130
- Change since the last run: dish families and categories 711 -> 710

## Enrichment

- entries with a story: 2758
- entries with a Wikidata origin: 4194
- Walter coverage score: 3.61
- Change since the last run: entries with a story 2761 -> 2758; entries with a Wikidata origin 4195 -> 4194; Walter coverage score 3.58 -> 3.61

## Preservation

- Indigenous traditions tracked: 6
- Indigenous candidates: 30
- Indigenous candidates reviewed: 0
- reviewed cultural facts: 0
- Change since the last run: no change

## Governance

- Review items open: 29
- Review items added since the last run: 0
- Review items answered by a person: 11 (items 21, 24, 28, 29, 30, 32, 33, 34, 36, 37, 40)
- Change since the last run: review items open 36 -> 29; review items answered 4 -> 11

## Work completed since the last snapshot

- 094f8b6 Sprint 6: refresh the health reports after item 21, pin the place tree size, changelog

## What improved

- world culinary coverage (%): 70.0 -> 70.6
- Africa coverage (%): 52.8 -> 54.5
- Americas coverage (%): 72.9 -> 73.4
- Oceania coverage (%): 33.8 -> 35.2
- countries with a story: 136 -> 145
- Walter coverage score: 3.58 -> 3.61
- review items answered: 4 -> 11
- review items open: 36 -> 29
- atlas debt: 558 -> 538
- debt per country: 3.26 -> 3.15
- debt: no story: 35 -> 26
- debt: weak Walter: 5 -> 3

## What regressed

- dishes: 3871 -> 3868
- dish families and categories: 711 -> 710
- entries with a story: 2761 -> 2758
- entries with a Wikidata origin: 4195 -> 4194

## Human review required

Priority order (from review_impact.md):

1. Item 33 follow-up: the disputed regions and a check of the linked ones (gate debt, about 20 minutes)
2. Item 21: coverage counting rule and weights (gate 0.8, about 15 minutes)
3. Cuisine photo fallbacks (gate 0.8, about 40 minutes)
4. Items 24, 28, 29, 30: sprint moves, country scores, sprint 4 entries (gate 0.8, about 45 minutes)
5. Photo contact sheets 37 to 108 (gate 0.8, about 90 minutes)

Estimated time for these five: about 210 minutes.

## Blocked work (waiting on a person)

- 0.8: Staged photos signed off (the 72 passed contact sheets), then linked: about 203 dishes become rich
- 0.8: Cuisine image fallbacks, checked by a person
- 0.9: Region pages shown in the app
- 0.9: Indigenous tags reviewed by the rubric (item 26) before the app shows any
- 0.9: At least 100 reviewed dish facts (`data/knowledge/review/focus_review.csv`)

Impact: these hold the 0.8 and 0.9 releases. Suggested resolution: the review order above.

## Recommended next action

If a person is available: review the highest-impact item above.

If running unattended:

- Continue the current campaign as far as its review items allow.
- Quality work Claude can do alone with the most countries: **one dish only** (28 countries; first Samoa, The Bahamas, Curaçao, Malawi, Mauritania, Zambia, Barbados, Grenada).
- Regenerate the audits, atlas health and review impact; prepare evidence packets.

## Final question

How much more of the world's food culture can EverFlavor represent, explain and preserve now than before this run? Coverage, representation, enrichment, preservation and governance above; the atlas debt per country says whether quality kept up.
