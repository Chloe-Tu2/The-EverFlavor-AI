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
| [dish_completeness_report.md](dish_completeness_report.md) | Rich, fair and thin dishes today, how many move up once the approved images are fetched, and what keeps the rest from rich |
| [approved_photos_check.md](approved_photos_check.md) | The approved photos fetched: how many pass the photo check, a check by eye, and the next steps |
| [dish_quality_report.md](dish_quality_report.md) | The completeness score (0-100) of every dish and what fills each gap |
| [image_coverage_report.md](image_coverage_report.md) | The best image each dish can show, its licence and credit, what to fetch next, and the images approved for collection (`approved_image_queue.json`) |
| [walter_coverage_report.md](walter_coverage_report.md) | What the waiter can tell about each dish, and what a person has checked |
| [map_validation_report.md](map_validation_report.md) | Which dishes and recipes the map can place in the pilot area |
| [taxonomy_coverage_report.md](taxonomy_coverage_report.md) | Which nodes of the place tree hold dishes and recipes |
| [taxonomy_validation_report.md](taxonomy_validation_report.md) | The place tree checked against the UN regions, and the culinary regions below a country with what they hold |
| [country_coverage_report.md](country_coverage_report.md), [culinary_region_coverage_report.md](culinary_region_coverage_report.md) | Coverage next to depth, by country and by region |
| [global_culinary_atlas.md](global_culinary_atlas.md) | Coverage by the UN's world regions (CLDR): a score per continent and subregion, the gaps, up to 500 next dishes per continent, missing versions and the review queue |
| [world_culinary_coverage.md](world_culinary_coverage.md) | **The headline metric:** how well each country's food tradition is represented (levels 1-3), by continent and subregion, and Africa country by country |
| [enrichment_impact.md](enrichment_impact.md) | Did the fetches improve the atlas? Before and after: coverage, countries, country pages, stories, families, origins, Indigenous tags (also writes `data/knowledge/atlas/atlas_metrics.json` and the README's Atlas progress block) |
| [region_knowledge.md](region_knowledge.md) | One knowledge page per food region of the place tree (`data/knowledge/atlas/regions/`): countries, coverage, representative dishes, families, Indigenous traditions |
| [country_representation.md](country_representation.md) | Three scores per country: coverage (a dish), representation (depth, families, stories, regions) and enrichment (origins, variants, related dishes, Walter's lines); the weak and uncovered countries are the next sprint's targets |
| [continent_coverage_report.md](continent_coverage_report.md) | The atlas by continent: its subregions, countries with recipes but no dish page, missing versions, the backlog by status |
| [food_graph_validation_report.md](food_graph_validation_report.md) | The Food Graph's links checked: orphans, cycles, places that do not reach World, origins the tree lacks, dishes with more than one valid place |
| [dish_enrichment_queues.md](dish_enrichment_queues.md) | The rich-dish upgrade queue (lowest effort first) and what the waiter is missing per dish |
| [publishing_rules.md](publishing_rules.md) | The rules and approval states every new dish must pass (proposed) |

The coverage reports and `data/knowledge/coverage/` are written by `scripts/knowledge/coverage_audit.py`
(countries from `scripts/knowledge/fetch_countries.py`, Wikidata). Rerun it after the data changes. The quality
sprint's reports come from `media_audit.py` (with `fetch_image_candidates.py`) and `quality_reports.py`; run
`media_audit.py`, then `quality_reports.py`, then `media_audit.py` again (its priority list reads the scores).
After notebook 01 rewrites the recipe tables, run them all in this order: `recipe_quality_audit.py`,
`recipe_dish_links.py`, `recipe_graph.py`, `coverage_audit.py`, `atlas_audit.py`, `graph_assets.py`, then the
three above, then `image_queue.py`, `completeness_report.py`, `taxonomy_validation.py`, `enrichment_queues.py`, `graph_validation.py`, `continent_report.py` and `culinary_coverage.py`. The atlas reads its regions from `data/knowledge/atlas/regions.json` (`fetch_regions.py`, once).
