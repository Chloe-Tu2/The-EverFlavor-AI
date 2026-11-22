# Audits

Read-only reports on the data: what we have, how it links up and where the gaps are. An audit changes nothing in
the app; any change it suggests is a separate step with its own tests and, where it is a judgment, a policy.

| Report | What it answers |
|---|---|
| [recipe_dish_linking.md](recipe_dish_linking.md) | How many recipes the app links to a dish, where the match fails, rule L1 (a dish named before a kind of dish is its flavour; every change in [dish_link_review.csv](dish_link_review.csv)), and every recipe as a Food Graph node |
| [coverage_world.md](coverage_world.md) | Which countries and zones are covered, over- and under-represented, the priority tiers, and where 500 new dishes would come from |
| [coverage_europe.md](coverage_europe.md), [asia](coverage_asia.md), [africa](coverage_africa.md), [americas](coverage_americas.md), [oceania](coverage_oceania.md), [middle_east](coverage_middle_east.md) | Country by country: dishes, families, variants, recipes, what is missing |
| [dish_family_gap_report.md](dish_family_gap_report.md) | Which dish families are weakly covered |
| [variant_gap_report.md](variant_gap_report.md) | Which families' missing versions would add the most |
| [culinary_regions.md](culinary_regions.md) | Regions below a country, and indigenous foodways |
| [recipe_quality.md](recipe_quality.md) | What each recipe has and lacks (steps, servings, time, nutrition, country, photo, link), by source |
| [graph_assets.md](graph_assets.md) | The waiter's context, discovery paths and map preparation read off the Food Graph |
| [dish_quality_report.md](dish_quality_report.md) | The completeness score (0-100) of every dish and what fills each gap |
| [dish_image_report.md](dish_image_report.md) | The best image each dish can show, its licence and credit, what to fetch next |
| [walter_coverage_report.md](walter_coverage_report.md) | What the waiter can tell about each dish, and what a person has checked |
| [map_validation_report.md](map_validation_report.md) | Which dishes and recipes the map can place in the pilot area |
| [taxonomy_coverage_report.md](taxonomy_coverage_report.md) | Which nodes of the place tree hold dishes and recipes |
| [country_coverage_report.md](country_coverage_report.md), [culinary_region_coverage_report.md](culinary_region_coverage_report.md) | Coverage next to depth, by country and by region |
| [publishing_rules.md](publishing_rules.md) | The rules and approval states every new dish must pass (proposed) |

The coverage reports and `data/knowledge/coverage/` are written by `scripts/knowledge/coverage_audit.py`
(countries from `scripts/knowledge/fetch_countries.py`, Wikidata). Rerun it after the data changes. The quality
sprint's reports come from `media_audit.py` (with `fetch_image_candidates.py`) and `quality_reports.py`; run
`media_audit.py`, then `quality_reports.py`, then `media_audit.py` again (its priority list reads the scores).
After notebook 01 rewrites the recipe tables, run them all in this order: `recipe_quality_audit.py`,
`recipe_dish_links.py`, `recipe_graph.py`, `coverage_audit.py`, `graph_assets.py`, then the three above.
