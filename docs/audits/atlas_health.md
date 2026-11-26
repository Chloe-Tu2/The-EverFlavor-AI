# Atlas health (2026-11-25)

The five measures, the atlas debt and release readiness, from `scripts/knowledge/atlas_health.py` (metrics built 2026-11-25). **Audit only.** Start a session with [curator_handoff.md](curator_handoff.md); what to review first: [review_impact.md](review_impact.md).

## Headline

- Coverage: 70.6%
- UN members: 163 of 193
- Atlas debt: 3.15 per country
- Story debt: 26 countries
- Campaign: Q1. Regional source discovery
- Blocked by: source (a second free regional source (Wikidata links few dishes, item 36))

## The five measures

- **Coverage:** world culinary coverage (%) 70.6; Africa coverage (%) 54.5; Americas coverage (%) 73.4; Asia coverage (%) 81.2; Europe coverage (%) 87.8; Oceania coverage (%) 35.2; countries with a dish 171; country pages 168
- **Representation:** dish families and categories 710; countries with three dishes or more 130; countries with a story 145; Indigenous traditions tracked 6
- **Enrichment:** entries with a story (History or Origin sentences) 2,758; entries with a Wikidata origin 4,194; entries linked to a family 3,779; entries with a culinary region 644; rich dishes 531; fair dishes 1,490; thin dishes 1,847
- **Preservation:** entries with an Indigenous tradition 29; Indigenous traditions tracked 6
- **Governance:** 40 review items logged in [needs_human_review.md](../governance/needs_human_review.md), 11 answered by a person; none closed by Claude.

## Atlas debt

538 weighted debt points across 171 countries with a dish, 3.15 per country. Weights: no culinary region 3, no story 2, no family 2, one dish only 2, no photo 1, weak Walter 1. Lowering it beats adding dishes once the coverage targets are met. Debt per country is the measure to follow: a newly covered country brings its own gaps. Most countries lack culinary region data because the place tree has few regions within countries yet; that gap needs a source first (Q1 phase 0).

| Gap | Weight | Countries | Points |
|---|---:|---:|---:|
| no culinary region | 3 | 116 | 348 |
| no story | 2 | 26 | 52 |
| no family | 2 | 17 | 34 |
| one dish only | 2 | 28 | 56 |
| no photo | 1 | 45 | 45 |
| weak Walter | 1 | 3 | 3 |

### Regions with the most debt per country

| Region | Countries | Debt | Per country |
|---|---:|---:|---:|
| Oceania / Polynesia | 2 | 17 | 8.5 |
| Oceania / Melanesia | 1 | 8 | 8.0 |
| Oceania / Micronesian Region | 3 | 18 | 6.0 |
| Americas / Caribbean | 14 | 70 | 5.0 |
| Africa / Eastern Africa | 14 | 64 | 4.6 |
| Africa / Western Africa | 12 | 48 | 4.0 |
| Asia / Central Asia | 5 | 19 | 3.8 |
| Americas / Central America | 8 | 30 | 3.8 |
| Africa / Middle Africa | 6 | 19 | 3.2 |
| Asia / Western Asia | 15 | 46 | 3.1 |
| Europe / Southern Europe | 14 | 41 | 2.9 |
| Asia / Southern Asia | 9 | 26 | 2.9 |

### Country priority (the most debt first)

The full list: `data/knowledge/atlas/atlas_debt.json`.

| Country | Dishes | Debt | Gaps |
|---|---:|---:|---:|
| Samoa | 1 | 10 | no culinary region, no story, no family, one dish only, no photo |
| The Bahamas | 1 | 10 | no culinary region, no story, no family, one dish only, weak Walter |
| Curaçao | 1 | 9 | no culinary region, no story, no family, one dish only |
| Malawi | 1 | 9 | no culinary region, no story, no family, one dish only |
| Mauritania | 1 | 9 | no culinary region, no story, no family, one dish only |
| Zambia | 1 | 9 | no culinary region, no story, no family, one dish only |
| Barbados | 1 | 8 | no culinary region, no story, one dish only, no photo |
| Grenada | 1 | 8 | no culinary region, no story, one dish only, no photo |
| Guadeloupe | 1 | 8 | no culinary region, no family, one dish only, no photo |
| Marshall Islands | 1 | 8 | no culinary region, no story, one dish only, no photo |
| Mozambique | 1 | 8 | no culinary region, no story, one dish only, no photo |
| New Caledonia | 1 | 8 | no culinary region, no family, one dish only, no photo |
| Rwanda | 1 | 8 | no culinary region, no family, one dish only, no photo |
| Saint Lucia | 1 | 8 | no culinary region, no story, one dish only, no photo |
| Sierra Leone | 1 | 8 | no culinary region, no story, one dish only, no photo |
| The Gambia | 1 | 8 | no culinary region, no story, one dish only, no photo |
| Bahrain | 1 | 7 | no culinary region, no family, one dish only |
| Bhutan | 1 | 7 | no culinary region, no family, one dish only |
| Montenegro | 1 | 7 | no culinary region, no story, one dish only |
| Panama | 1 | 7 | no culinary region, no family, one dish only |
| San Marino | 1 | 7 | no culinary region, no story, one dish only |
| Tonga | 2 | 7 | no culinary region, no story, no photo, weak Walter |
| Turkmenistan | 2 | 7 | no culinary region, no story, no photo, weak Walter |
| Andorra | 1 | 6 | no culinary region, one dish only, no photo |
| Congo | 1 | 6 | no culinary region, one dish only, no photo |
| Northern Mariana Islands | 1 | 6 | no culinary region, one dish only, no photo |
| United Arab Emirates | 1 | 6 | no culinary region, one dish only, no photo |
| Central African Republic | 2 | 6 | no culinary region, no family, no photo |
| South Sudan | 2 | 6 | no culinary region, no story, no photo |
| Suriname | 2 | 6 | no culinary region, no family, no photo |

### Walter debt: the 20 weakest countries

The average of Walter's five questions their dishes answer (0 to 5); enrichment targets.

| Country | Dishes | Walter score |
|---|---:|---:|
| The Bahamas | 1 | 2.00 |
| Tonga | 2 | 2.50 |
| Turkmenistan | 2 | 2.50 |
| Bahrain | 1 | 3.00 |
| Belize | 1 | 3.00 |
| Central African Republic | 2 | 3.00 |
| Curaçao | 1 | 3.00 |
| Malawi | 1 | 3.00 |
| Mauritania | 1 | 3.00 |
| Mauritius | 3 | 3.00 |
| Monaco | 2 | 3.00 |
| Montenegro | 1 | 3.00 |
| Mozambique | 1 | 3.00 |
| New Caledonia | 1 | 3.00 |
| Rwanda | 1 | 3.00 |
| Samoa | 1 | 3.00 |
| Seychelles | 3 | 3.00 |
| South Sudan | 2 | 3.00 |
| The Gambia | 1 | 3.00 |
| Zambia | 1 | 3.00 |

## Release readiness

### 0.8.0: 6 of 9 conditions done

| Area | Condition | Readiness |
|---|---:|---:|
| Coverage | Coverage counting rule confirmed (review item 21), then world coverage shown in the app | done |
| Coverage | README dashboard (with exact counts), metrics and sprint impact reports generated automatically | done |
| Images | Staged photos signed off (the 72 passed contact sheets), then linked: about 203 dishes become rich | waiting on a person |
| Images | Cuisine image fallbacks, checked by a person | waiting on a person |
| Discovery | Related dishes in Check my recipe | done |
| Discovery | Map cuisine tags for every country OpenStreetMap has a word for (50+ uses) | done |
| Discovery | The store locator works (ZIP search, details, directions) | done |
| Reviews | Items 24, 28, 29 and 30 (moved dishes, country scores, sprint entries) answered | done |
| Release | CI green | last step |

### 0.9.0: 2 of 10 conditions done

| Area | Condition | Readiness |
|---|---:|---:|
| Knowledge | Walter's five questions, from the graph's fixed lines | open for Claude |
| Knowledge | Region pages generated for every region with a dish | done |
| Knowledge | Region pages shown in the app | waiting on a person |
| Preservation | Indigenous tags reviewed by the rubric (item 26) before the app shows any | waiting on a person |
| Enrichment | At least 100 reviewed dish facts (`data/knowledge/review/focus_review.csv`) | waiting on a person |
| Enrichment | Coverage, representation, enrichment and preservation metrics generated | done |
| Safety | Chat with the chef (CHEF_CHAT.md) with its red-team tests green | open for Claude |
| Experience | Nice-to-have: the loading screen (issues #48 to #52) | open for Claude |
| Experience | Store locator polish, if not finished in 0.8 | open for Claude |
| Release | CI green | last step |

### 1.0.0: coverage targets

| Target | Goal | Now | Readiness |
|---|---:|---:|---:|
| world culinary coverage (%) | >= 60% | 70.6% | done |
| Africa coverage (%) | >= 50% | 54.5% | done |
| Oceania coverage (%) | >= 35% | 35.2% | done |

Risks: most open 0.8 and 0.9 conditions wait on people; review time, not data, sets the pace. Every other 1.0 target (pages complete, Walter reviewed, no open critical item) waits on the reviews above.
