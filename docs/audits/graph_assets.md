# Graph assets: the waiter's context, discovery paths and map preparation (2026-11-21)

Three files read straight off the Food Graph by `scripts/knowledge/graph_assets.py`, ready for features that are
not built yet (the waiter's chat in 0.8.0, Explore and World Tour, the map from a recipe). No line or link is
written by a model; each comes from a graph edge with its evidence. Nothing in the app reads them yet.

## The waiter's context (`data/knowledge/walter_context.json`)

For each of the 3,201 dishes: the lines `WalterContextService` writes from fixed templates ("Chapati is a kind of
flatbread.", "If you enjoy Chapati, you may also like Roti.", "It is from India."), and the names behind them.

- Every dish has at least one line (its place); 1,212 have only that one, 859 have two, 958 three and 172 four.
- 1,934 dishes have a "kind of" line, 1,130 a "you may also like", 227 a "versions include".
- 146 dishes have versions EverFlavor does not have yet (`variants_not_in_everflavor`), for the waiter to say
  "there are other versions" without inventing them.

## Discovery paths (`data/knowledge/discovery_paths.json`)

For each dish, the next 8 dishes to try (`GraphRecommendationService.discovery_candidates`): versions first, then
the family, the same country and the places next to it, taking turns. Each has its reason ("a version of this
dish", "from Pakistan, next to India"), its relation and its evidence (Wikidata P279, the Food Taxonomy). Every
dish has 8. Of the 25,608 links, 20,232 come from the place tree, 4,802 from versions and 574 from families, so
place, not family, drives most of discovery today.

## Map preparation (`data/knowledge/map_prep.json`)

For each country with dishes: the OpenStreetMap cuisine tag the map looks for (`stores.COUNTRY_CUISINES`), its
dishes and linked recipes, and how many places in the Greater Houston pilot area carry the tag.

- **45 of 74 countries have no cuisine tag**, so the map can show no place for their dishes, among them Canada
  (6,961 linked recipes), Poland (2,151), the Czech Republic (1,317), Australia (1,244), Norway (1,022) and
  Belgium (928).
- **Tags on pilot places that no country uses yet:** `afghan` 4, `venezuelan` 4 and `puerto_rican` 3 name
  countries we have recipes for (Afghanistan, Venezuela, Puerto Rico), and `salvadoran` 8 a country we have none
  for yet; most other tags are kinds of food, not a country (pizza 226, seafood 168, barbecue 99, tex-mex 84).
- Egypt and Indonesia have a tag but no pilot place carries it.

Adding a country's tag to `COUNTRY_CUISINES` is a small change in the app's code, left for its own reviewed step.
