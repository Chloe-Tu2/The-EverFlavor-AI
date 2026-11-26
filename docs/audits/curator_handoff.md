# Curator handoff (2026-11-25)

Read this first in a new session, then [atlas_health.md](atlas_health.md), [review_impact.md](review_impact.md) and [release_readiness.md](release_readiness.md). From `scripts/knowledge/atlas_health.py`; the history is in `data/knowledge/atlas/atlas_health_history.jsonl`. **Audit only.**

## Generated at

- Date: 2026-11-25
- Time: 20:38
- Git commit: 7e58a32+work (compared with 5bae85f+work, 2026-11-25)

## Current status

- Branch: sprint/6-pick-sheets
- Campaign: Q1. Regional source discovery (the first on the campaign scoreboard, in the planner's order)
- Version: 0.7.2
- Release readiness 0.8: 4 of 9 conditions done
- Release readiness 0.9: 2 of 10 conditions done
- Release readiness 1.0: 2 of 3 coverage targets met; the rest wait on reviews

## Headline

- Coverage: 70.0%
- UN members with a dish: 163 of 193
- Atlas debt: 3.26 per country
- Regional debt: 116 countries
- Story debt: 35 countries
- Campaign: Q1. Regional source discovery
- Blocked by: source (a second free regional source (Wikidata links few dishes, item 36))

## Atlas debt

- Current debt: 558 (3.26 per country)
- Debt change: atlas debt 546 -> 558; debt per country 3.23 -> 3.26
- Top debt categories:
  1. no culinary region: 116 countries, 348 points
  2. no story: 35 countries, 70 points
  3. one dish only: 28 countries, 56 points
- Highest-debt regions (per country):
  1. Oceania / Polynesia: 8.5
  2. Oceania / Melanesia: 8.0
  3. Oceania / Micronesian Region: 7.3

## Coverage

- world culinary coverage (%): 70.0
- Africa coverage (%): 52.8
- Oceania coverage (%): 33.8
- countries with a dish: 171
- UN members with a dish: 163
- Change since the last run: countries with a dish 169 -> 171; UN members with a dish 161 -> 163

## Representation

- dish families and categories: 711
- country pages: 168
- region pages: 30
- countries with three dishes or more: 130
- Change since the last run: dish families and categories 707 -> 711; country pages 166 -> 168

## Enrichment

- entries with a story: 2761
- entries with a Wikidata origin: 4195
- Walter coverage score: 3.58
- Change since the last run: entries with a story 2758 -> 2761; entries with a Wikidata origin 4188 -> 4195

## Preservation

- Indigenous traditions tracked: 6
- Indigenous candidates: 30
- Indigenous candidates reviewed: 0
- reviewed cultural facts: 0
- Change since the last run: no change

## Governance

- Review items open: 36
- Review items added since the last run: 4
- Review items answered by a person: 3 (items 32, 33, 34)
- Change since the last run: review items open 32 -> 36

## Work completed since the last snapshot

- f21fe15 Campaign completion criteria; Q1 first, F Southern Africa active again

## What improved

- countries with a dish: 169 -> 171
- country pages: 166 -> 168
- UN members with a dish: 161 -> 163
- dish families and categories: 707 -> 711
- entries with a story: 2758 -> 2761
- entries with a Wikidata origin: 4188 -> 4195
- review items logged: 35 -> 39

## What regressed

- review items open: 32 -> 36
- atlas debt: 546 -> 558
- debt per country: 3.23 -> 3.26
- debt: no culinary region: 114 -> 116
- debt: no story: 33 -> 35
- debt: one dish only: 27 -> 28

## Human review required

Priority order (from review_impact.md):

1. Item 33 follow-up: the disputed regions and a check of the linked ones (gate debt, about 20 minutes)
2. Item 21: coverage counting rule and weights (gate 0.8, about 15 minutes)
3. Cuisine photo fallbacks (gate 0.8, about 40 minutes)
4. Items 24, 28, 29, 30: sprint moves, country scores, sprint 4 entries (gate 0.8, about 45 minutes)
5. Photo contact sheets 37 to 108 (gate 0.8, about 90 minutes)

Estimated time for these five: about 210 minutes.

## Blocked work (waiting on a person)

- 0.8: Coverage counting rule confirmed (review item 21), then world coverage shown in the app
- 0.8: Staged photos signed off (the 72 passed contact sheets), then linked: about 203 dishes become rich
- 0.8: Cuisine image fallbacks, checked by a person
- 0.8: Items 24, 28, 29 and 30 (moved dishes, country scores, sprint entries) answered
- 0.9: Region pages shown in the app
- 0.9: Indigenous tags reviewed by the rubric (item 26) before the app shows any
- 0.9: At least 100 reviewed dish facts (`data/knowledge/review/focus_review.csv`)

Impact: these hold the 0.8 and 0.9 releases. Suggested resolution: the review order above.

## Recommended next action

If a person is available: review the highest-impact item above.

If running unattended:

- Continue the current campaign as far as its review items allow.
- Quality work Claude can do alone with the most countries: **no story** (35 countries; first Rwanda, Samoa, The Bahamas, Curaçao, Malawi, Mauritania, Zambia, Central African Republic).
- Regenerate the audits, atlas health and review impact; prepare evidence packets.

## Final question

How much more of the world's food culture can EverFlavor represent, explain and preserve now than before this run? Coverage, representation, enrichment, preservation and governance above; the atlas debt per country says whether quality kept up.
