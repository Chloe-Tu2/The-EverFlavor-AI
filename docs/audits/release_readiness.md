# Release readiness (2026-11-25)

Done, waiting on a person, open for Claude, per release gate in the planner. From `scripts/knowledge/atlas_health.py`.

## 0.8 release countdown

- Readiness: 6 of 9 conditions done
- Reviews left: 2, about 127 minutes in all (estimates)
- Blocked only by: human review

1. **Cuisine images: 111 of 111 rows without a verdict (14 likely wrong first, then 31 to look at, 66 probably right)**, about 37 minutes. `data/knowledge/review/cuisine_images.csv`: `verdict` yes or no, and `reviewer`
2. **Contact sheets: 72 of 72 passed sheets not yet read**, about 90 minutes. `data/raw/dish_photos_approved/sheets/` (local); a wrong photo goes in `data/reference/dish_photo_review.csv`, a finished sheet in `data/reference/contact_sheet_review.csv`

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
| world culinary coverage (%) | >= 60% | 70.7% | done |
| Africa coverage (%) | >= 50% | 54.5% | done |
| Oceania coverage (%) | >= 35% | 35.2% | done |

Risks: most open 0.8 and 0.9 conditions wait on people; review time, not data, sets the pace. Every other 1.0 target (pages complete, Walter reviewed, no open critical item) waits on the reviews above.
