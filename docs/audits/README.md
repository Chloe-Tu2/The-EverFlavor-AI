# Audits

Read-only reports on the data: what we have, how it links up and where the gaps are. An audit changes nothing in
the app; any change it suggests is a separate step with its own tests and, where it is a judgment, a policy.

| Report | What it answers |
|---|---|
| [recipe_dish_linking.md](recipe_dish_linking.md) | How many recipes the app links to a dish, and where the match fails |
| [coverage_world.md](coverage_world.md) | Which countries and zones are covered, over- and under-represented, the priority tiers, and where 500 new dishes would come from |
| [coverage_europe.md](coverage_europe.md), [asia](coverage_asia.md), [africa](coverage_africa.md), [americas](coverage_americas.md), [oceania](coverage_oceania.md), [middle_east](coverage_middle_east.md) | Country by country: dishes, families, variants, recipes, what is missing |
| [dish_family_gap_report.md](dish_family_gap_report.md) | Which dish families are weakly covered |
| [variant_gap_report.md](variant_gap_report.md) | Which families' missing versions would add the most |
| [culinary_regions.md](culinary_regions.md) | Regions below a country, and indigenous foodways |
| [graph_assets.md](graph_assets.md) | The waiter's context, discovery paths and map preparation read off the Food Graph |
| [publishing_rules.md](publishing_rules.md) | The rules and approval states every new dish must pass (proposed) |

The coverage reports and `data/knowledge/coverage/` are written by `scripts/knowledge/coverage_audit.py`
(countries from `scripts/knowledge/fetch_countries.py`, Wikidata). Rerun it after the data changes.
