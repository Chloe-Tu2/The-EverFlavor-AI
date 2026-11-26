# Campaign scoreboard (2026-11-25)

Where every campaign stands, in the planner's order: the number now, the next target, the gap and what blocks it. From `scripts/knowledge/atlas_health.py`; targets for E, F and B are Claude's working targets, not release gates. **Audit only.**

Debt per country fell since the last snapshot; expansion and debt work can both go ahead.

**Debt velocity** since b710ac9+work (2026-11-25): atlas debt 558 -> 538 (-20); no culinary region 116 -> 116 (+0); no story 35 -> 26 (-9); no family 17 -> 17 (+0); one dish only 28 -> 28 (+0); no photo 45 -> 45 (+0); weak Walter 5 -> 3 (-2).

**Debt reduction efficiency:** no new dishes; +20 debt points removed (-0.11 per country)

| Campaign | Now | Next target | Gap | Blocked by |
|---|---:|---:|---:|---:|
| Q1. Regional source discovery | 116 countries without regional data | 90 (phase 1) | 26 | a second free regional source (Wikidata links few dishes, item 36) |
| F. Southern Africa 50% | 39.8% | 50% | 10.2 points | none |
| C. Oceania 35% | 35.2% | 35% | met | none |
| Q2b. New story sources | 26 countries without a story | 0 | 26 | a new free story source (Q2a, the existing sources, is largely exhausted) |
| Walter debt | 3 weak countries; average 3.61 of 5 | 0 weak | 3 | none |
| Q4. Family recovery | 17 countries without a family | 0 | 17 | none |
| Q3. Image completion | 45 countries without a photo | 0 | 45 | a person approves every photo |
| G. Manual country research | 30 UN members without a dish | 0 | 30 members | a person or a new approved source (A's automatic routes are exhausted) |
| E. Western Asia | 75.3% | 80% | 4.7 points | none |
| B. Caribbean | 57.8% | 60% | 2.2 points | none |
| D. Africa 50% (complete, maintenance) | 54.5% | 50% | met | none; keep above 50% |

## Campaign health

Status, what kind of thing blocks each campaign (data, source, policy, review, tooling or none), and Claude's working estimate of the gain and of how sure that estimate is (med27-coder, 2026-11-25); the estimates are judgments, not measurements.

| Campaign | Status | Blocked by | Expected gain | Confidence |
|---|---:|---:|---:|---:|
| Q1. Regional source discovery | active | source | high | medium |
| F. Southern Africa 50% | active | review (3 empty countries need a person's picks, item 38) | medium | medium |
| C. Oceania 35% | active | data (coverage gaps) | medium | high |
| Q2b. New story sources | active | source | high | low |
| Walter debt | active | data | medium | medium |
| Q4. Family recovery | active | data | low | medium |
| Q3. Image completion | review-driven | review | medium | high |
| G. Manual country research | active | review | medium | medium |
| E. Western Asia | backlog | none | low | medium |
| B. Caribbean | backlog | none | low | medium |
| D. Africa 50% (complete, maintenance) | complete, maintenance | none | none | high |

## Completion criteria

A campaign is complete only when every condition holds (med27-coder, 2026-11-25); complete now: D. Africa 50%. The Q1 phase 1 target of 90 is what the Wikidata links can reach (24 countries without regional data have a provisional region); phase 2 waits for a second source.

| Campaign | Condition | Now | Met |
|---|---:|---:|---:|
| Q1. Regional source discovery | countries without regional data at most 90 (phase 1, Wikidata links) | 116 | no |
| Q1. Regional source discovery | at most 50 (phase 2, needs a second regional source) | 116 | no |
| F. Southern Africa 50% | coverage at least 50% | 39.8% | no |
| F. Southern Africa 50% | average Walter score at least 4.0 | 3.5 | no |
| F. Southern Africa 50% | every covered country has regional data | all have it | yes |
| C. Oceania 35% | coverage at least 35% | 35.2% | yes |
| C. Oceania 35% | no Oceania country among the 10 highest-debt countries | Samoa, Marshall Islands | no |
| Walter debt | no country under 3 of 5 | 3 | no |
| Q2b. New story sources | no country without a story | 26 | no |
| Q4. Family recovery | no country without a family | 17 | no |
| G. Manual country research | every UN member has a dish | 163 of 193 | no |
| Q3. Image completion | no country without a photo | 45 | no |
| E. Western Asia | coverage at least 80% | 75.3% | no |
| B. Caribbean | coverage at least 60% | 57.8% | no |
| D. Africa 50% | coverage stays at least 50% | 54.5% | yes |
