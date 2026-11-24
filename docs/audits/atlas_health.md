# Atlas health (2026-11-24)

The five measures, the atlas debt and release readiness, from `scripts/knowledge/atlas_health.py` (metrics built 2026-11-23). **Audit only.** What to review first: [review_impact.md](review_impact.md).

## The five measures

- **Coverage:** world culinary coverage (%) 63.7; Africa coverage (%) 44.0; Americas coverage (%) 63.8; Asia coverage (%) 76.6; Europe coverage (%) 84.1; Oceania coverage (%) 32.3; countries with a dish 154; country pages 165
- **Representation:** dish families and categories 707; countries with three dishes or more 115; countries with a story 115; Indigenous traditions tracked 6
- **Enrichment:** entries with a story (History or Origin sentences) 2,757; entries with a Wikidata origin 4,187; entries linked to a family 3,772; entries with a culinary region 644; rich dishes 529; fair dishes 1,489; thin dishes 1,845
- **Preservation:** entries with an Indigenous tradition 29; Indigenous traditions tracked 6
- **Governance:** 32 review items logged in [needs_human_review.md](../governance/needs_human_review.md); none closed by Claude.

## Atlas debt

227 debt points across 154 countries with a dish (at most 6 each). One point per gap: one dish only, no photo, no story, no family, no culinary region, weak Walter. Lowering it is the goal, more than adding dishes. Most countries have no culinary region data only because the place tree has few culinary regions below country level yet; that gap needs a source for regions first.

| Gap | Countries |
|---|---:|
| one dish only | 25 |
| no photo | 32 |
| no story | 39 |
| no family | 23 |
| no culinary region | 101 |
| weak Walter | 7 |

### Regions with the most debt per country

| Region | Countries | Debt | Per country |
|---|---:|---:|---:|
| Oceania / Melanesia | 1 | 5 | 5.0 |
| Oceania / Polynesia | 2 | 9 | 4.5 |
| Oceania / Micronesian Region | 1 | 3 | 3.0 |
| Africa / Middle Africa | 5 | 13 | 2.6 |
| Africa / Eastern Africa | 13 | 33 | 2.5 |
| Asia / Central Asia | 5 | 12 | 2.4 |
| Africa / Western Africa | 10 | 24 | 2.4 |
| Americas / Caribbean | 9 | 17 | 1.9 |
| Americas / Central America | 7 | 12 | 1.7 |
| Asia / Western Asia | 14 | 22 | 1.6 |
| Americas / South America | 12 | 15 | 1.2 |
| Asia / Southern Asia | 9 | 10 | 1.1 |

### Countries with the most debt

The full list: `data/knowledge/atlas/atlas_debt.json`.

| Country | Dishes | Debt | Gaps |
|---|---:|---:|---:|
| Bahrain | 1 | 5 | one dish only, no story, no family, no culinary region, weak Walter |
| New Caledonia | 1 | 5 | one dish only, no photo, no story, no family, no culinary region |
| Rwanda | 1 | 5 | one dish only, no photo, no story, no family, no culinary region |
| Samoa | 1 | 5 | one dish only, no photo, no story, no family, no culinary region |
| Tajikistan | 1 | 5 | one dish only, no story, no family, no culinary region, weak Walter |
| The Bahamas | 1 | 5 | one dish only, no story, no family, no culinary region, weak Walter |
| Central African Republic | 2 | 5 | no photo, no story, no family, no culinary region, weak Walter |
| Antigua and Barbuda | 1 | 4 | one dish only, no story, no family, no culinary region |
| Belize | 1 | 4 | one dish only, no story, no culinary region, weak Walter |
| Brunei | 1 | 4 | one dish only, no photo, no family, no culinary region |
| Curaçao | 1 | 4 | one dish only, no story, no family, no culinary region |
| Democratic Republic of the Congo | 1 | 4 | one dish only, no photo, no story, no family |
| Malawi | 1 | 4 | one dish only, no story, no family, no culinary region |
| Mali | 1 | 4 | one dish only, no photo, no story, no culinary region |
| Mauritania | 1 | 4 | one dish only, no story, no family, no culinary region |
| Mozambique | 1 | 4 | one dish only, no photo, no story, no culinary region |
| Niger | 1 | 4 | one dish only, no photo, no story, no family |
| Suriname | 1 | 4 | one dish only, no photo, no family, no culinary region |
| The Gambia | 1 | 4 | one dish only, no photo, no story, no culinary region |
| Zambia | 1 | 4 | one dish only, no story, no family, no culinary region |
| Tonga | 2 | 4 | no photo, no story, no culinary region, weak Walter |
| Turkmenistan | 2 | 4 | no photo, no story, no culinary region, weak Walter |
| Bhutan | 1 | 3 | one dish only, no family, no culinary region |
| Montenegro | 1 | 3 | one dish only, no story, no culinary region |
| United Arab Emirates | 1 | 3 | one dish only, no photo, no culinary region |
| Benin | 2 | 3 | no photo, no family, no culinary region |
| Chad | 2 | 3 | no story, no family, no culinary region |
| Honduras | 2 | 3 | no photo, no story, no culinary region |
| South Sudan | 2 | 3 | no photo, no story, no culinary region |
| Kenya | 3 | 3 | no story, no family, no culinary region |

## Release readiness

### 0.8.0: 4 of 9 conditions done

| Area | Condition | Readiness |
|---|---:|---:|
| Coverage | Coverage counting rule confirmed (review item 21), then world coverage shown in the app | waiting on a person |
| Coverage | README dashboard (with exact counts), metrics and sprint impact reports generated automatically | done |
| Images | Staged photos signed off (the 72 passed contact sheets), then linked: about 203 dishes become rich | waiting on a person |
| Images | Cuisine image fallbacks, checked by a person | waiting on a person |
| Discovery | Related dishes in Check my recipe | done |
| Discovery | Map cuisine tags for every country OpenStreetMap has a word for (50+ uses) | done |
| Discovery | The store locator works (ZIP search, details, directions) | done |
| Reviews | Items 24, 28, 29 and 30 (moved dishes, country scores, sprint entries) answered | waiting on a person |
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
| world culinary coverage (%) | >= 60% | 63.7% | done |
| Africa coverage (%) | >= 50% | 44.0% | open |
| Oceania coverage (%) | >= 35% | 32.3% | open |

Risks: most open 0.8 and 0.9 conditions wait on people; review time, not data, sets the pace. Every other 1.0 target (pages complete, Walter reviewed, no open critical item) waits on the reviews above.
