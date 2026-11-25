# Food Graph validation (2026-11-25)

`scripts/knowledge/graph_validation.py` built the Food Graph as the app does (dishes, families, versions and the place tree; recipes are counted in `data/knowledge/recipe_graph_counts.json`) and checked its links. **Nothing was changed.**

Nodes: 7,428 dishes (5,970 ours, foods and drinks included),2,414 versions, 258 families, and the places. Edges: eaten_in 5,970, in_family 4,350, origin 5,728, part_of 276, variant_of 5,426.

## Broken links (should be zero)

| Check | Found |
|---|---:|
| places that do not reach World | 0 |
| cycles in the place tree | 0 |
| cycles in families or versions | 0 |
| our dishes with no edge at all | 0 |

## Gaps (not errors: the source has no link yet)

| Gap | Found |
|---|---:|
| our dishes with no place edge (no origin and no cuisine-list place in the tree) | 0 |
| cuisine-list countries not in the place tree | 0 |
| Wikidata origins not in the place tree | 150 |
| family groups with no member left (members were list articles) | 0 |

Wikidata origins not in the tree (20 most used): People's Republic of China (160), Korea (83), Scotland (44), Levant (17), England (15), Middle East (12), Hong Kong (7), Ottoman Empire (7), Eastern Europe (7), Indian subcontinent (7), Russian Empire (6), Maghreb (5), Soviet Union (5), Europe (4), Mesoamerica (4), Scandinavia (4), Arabian Peninsula (4), Hawaii (4), Central Asia (3), North America (3).

## More than one valid place (for a person)

Both kinds can be right, so nothing is settled here: the dish keeps every place its sources give. They are listed in `data/knowledge/quality/food_graph_validation.json` and counted in `docs/governance/needs_human_review.md`.

| Case | Dishes |
|---|---:|
| Wikidata gives more than one country of origin | 316 |
| the cuisine list puts it in a country that is not its origin | 918 |
