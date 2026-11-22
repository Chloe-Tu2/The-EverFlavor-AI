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

- **45 of 74 countries had no cuisine tag**, so the map could show no place for their dishes, among them Canada
  (6,961 linked recipes), Poland (2,151), the Czech Republic (1,317), Australia (1,244), Norway (1,022) and
  Belgium (928). **Fixed for 27 of them (2026-11-22):** each got its English demonym from Wikidata (P1549) where
  OpenStreetMap uses that word as a cuisine value 50 times or more (taginfo): afghan, argentinian, armenian,
  australian, austrian, bangladeshi, belgian, cambodian, canadian, chilean, croatian, czech, danish, ecuadorian,
  hungarian, irish, lao, malaysian, polish, portuguese, puerto_rican, russian, swedish, swiss, syrian, taiwanese,
  venezuelan. 18 more pilot places now match a country (Afghanistan 4, Venezuela 4, Puerto Rico 3, Argentina 2,
  Malaysia 2, Belgium 1, Portugal 1, Taiwan 1). Still without a tag (no demonym on Wikidata, or the word is rare
  on OpenStreetMap): Algeria, Andorra, Azerbaijan, Costa Rica, Finland, Iraq, Kenya, the Netherlands, New
  Zealand, Norway, Palestine, Saudi Arabia, Slovakia, Somalia, South Africa, Sudan, Ukraine, Uruguay. Words
  common in shop names for something else (polish, swiss, canadian, irish, lao) are not read from shop names.
- **Tags on pilot places that no country uses yet:** `salvadoran` 8, a country we have no dishes for yet; most
  others are kinds of food, not a country (pizza 226, seafood 168, barbecue 99, tex-mex 84).
- Egypt and Indonesia have a tag but no pilot place carries it.
