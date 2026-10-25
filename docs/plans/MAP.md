# Map: Where to Buy and Where to Eat in Houston

A plan for a free map in the app, for Houston, TX only. Nothing is built yet. Part of the [planner](README.md).
Written 2026-10-24 (Claude, with med27-coder); facts about tiles and licenses were read on that day.

## What the notes already say

| Source | What it says |
|---|---|
| README, "Store" output | Each recipe can come with "the nearest specialty supermarket for that cuisine". |
| README, scope | "One metro area for store search (e.g., Houston)". |
| Notebook 03, purpose | The Sourcing Agent answers "where can I buy this?" and "where can I eat this?". |
| Notebook 03, setup | `PILOT_AREA = {"name": "Houston, TX", "lat": 29.7604, "lng": -95.3698, "radius_m": 15000}`, marked as a placeholder until the team decides (section 7). |
| Notebook 03, section 3 | OpenStreetMap through Overpass is the free source; ODbL, credit "(c) OpenStreetMap contributors"; few, cached queries. Shops rarely say which country's food they sell, so `name_hint` guesses from the name ("Mercado", "Halal"). |
| Notebook 03, section 2 | Google Places is ready but waits for a key and a budget; Google's terms allow storing place IDs only. |
| `stores.suggest_where_to_buy` | An ingredient and its origin country give home-country brands and up to 5 groceries to try: same cuisine first, then the broader region (`COUNTRY_REGIONS`: an Asian market for Chinese soy sauce), never an unrelated store. Every store carries "Unverified: check with the store before you go." |
| `docs/ethics_privacy.md` | Location is used only in real time to find stores; it is not stored or shared. |
| `design/PLAN.md` | Nothing about the user is stored or sent anywhere; the page says so. |

**So the map is for:** showing where to buy the ingredients of a recipe (specialty grocers of its cuisine,
butchers, produce) and where to eat that cuisine, around Houston, always as places to try, never as a promise.

## The data we have today

`data/processed/places.parquet` (notebook 03, OpenStreetMap only, queried 2026-10-04; git-ignored):

| Fact | Value |
|---|---|
| Places | 1,543: 959 restaurants, 577 groceries, 7 butchers |
| Area | 15 km around downtown (lat 29.65 to 29.89, lng -95.52 to -95.22) |
| With a cuisine tag | 722 (almost all restaurants) |
| With a name hint | 80 (groceries: 13 Latin American, 1 Indian, 1 Korean, 1 halal) |
| Tagged halal / kosher / vegan | 10 / 4 / 8 |
| Without a name | 145 |
| Columns | `osm_id, name, lat, lng, category, cuisine, name_hint, diet_halal, diet_kosher, diet_vegan, diet_vegetarian, opening_hours, website, brand, source` |
| Size | 89 KB |

`data/processed/region_coverage_stores.csv`: 91 origin countries with `recipes, ingredients_linked_pct,
home_products_sold_in_us, nearby_places`. Examples: Mexico 133 nearby places, Italy 36, China 34, India 13,
France 10, United Kingdom 2, Canada 0.

Gaps for a map: no address column; "grocery" mixes supermarkets with convenience stores (gas stations);
no seafood shops, bakeries or farmers' markets; the 15 km circle misses much of Greater Houston (Bellaire
Boulevard's Asian markets on the west side, Hillcroft's South Asian and Middle Eastern shops are at its edge).

## What the user sees

| Part | What it does |
|---|---|
| A third tab, **"Where to buy"** (next to "Find recipes" and "Check my recipe") | A map of Houston, styled to match the pixel kitchen (flat colors, chunky pixels, the app's palette). |
| **From a recipe card** | A "Where to buy" button opens the map with that recipe's stores: groceries of its cuisine, then of its region, plus butchers or produce if the recipe needs them. A short list beside the map gives the reason for each ("Indian grocery: for garam masala"). |
| **Filters** | Groceries, restaurants, butchers, produce and markets; cuisine; "tagged halal-friendly" or "tagged kosher-friendly" in OpenStreetMap. |
| **Pins** | Small pixel icons per kind (cart, fork, cleaver, carrot). A tap shows name, address, opening hours and website when OpenStreetMap has them, and the line "Unverified: check with the store before you go." |
| **"Near me"** | Off by default. The map starts on downtown Houston. The user may type a ZIP code, or press "Use my location" (the browser asks first). |
| **Credits** | Always visible at the bottom right: "(c) OpenStreetMap contributors" and the tile credit. |

## Options compared

| Stack | Cost and key | Limits and terms | Looks (pixel style) | Offline | Streamlit fit |
|---|---|---|---|---|---|
| `st.map` / `st.pydeck_chart` (pydeck 0.9.3 is installed) | Free, no key | Carto basemap; Carto's free terms have view limits and Streamlit takes no responsibility for them | Few style options | No | Built in; clicks come back from pydeck charts |
| Folium + `streamlit-folium` (Leaflet, raster tiles) | Free, no key | `tile.openstreetmap.org` allows light interactive use only: no prefetching, no offline, a clear credit | Raster tiles; only CSS filters | No (OSM tiles forbid it) | Easiest in Python; returns clicks; two new packages |
| **MapLibre GL JS + OpenFreeMap vector tiles** | Free, no key, no registration, no cookies | No limit on views; commercial use allowed; credit "OpenFreeMap (c) OpenMapTiles Data from OpenStreetMap" | Full control: our own colors, fonts and pixel icons | No (but see next row) | A small custom component (the app already embeds `kitchen_scene.html`) |
| **MapLibre GL JS + a Protomaps PMTiles file of Houston, self-hosted** | Free; one file we keep | Our own copy; ODbL credit | Same as above | **Yes**: one file served by Streamlit itself | Same component; Streamlit's static serving (`server.enableStaticServing`) answers range requests in 1.65 (Starlette `FileResponse`) |
| Google Maps / Places | Paid after free credit; key and budget needed | Only place IDs may be stored | Google's look | No | Already coded in notebook 03, off |

Data sources:

| Source | Use | Terms |
|---|---|---|
| Overpass API (what notebook 03 uses) | One query per category for a Houston box, saved to `data/raw/osm_cache/` | Free; fair use: few, cached queries |
| Geofabrik Texas extract (`texas-latest.osm.pbf`, 692 MB, updated daily) | Fallback if Overpass times out: cut Houston with `osmium extract`, then filter the tags | ODbL |
| Nominatim (geocoding) | **Not used.** At most 1 request per second for all users together, no autocomplete, bulk use discouraged | |
| US Census ZIP code centroids (ZCTA Gazetteer file) | Typed ZIP code -> map center, looked up locally | Public domain; no service is called |

## Recommendation

**MapLibre GL JS in a Streamlit custom component, with the store pins from our own OpenStreetMap table.
Start with OpenFreeMap tiles; move to a self-hosted Houston PMTiles file once the map works.**

Why:

- **Free with no key, no budget and no sign-up**, so the whole team and the graders can run it.
- **It can look like the kitchen.** Vector tiles take our own style: the app's palette, a pixel font for labels,
  our pixel icons for pins, and a low `pixelRatio` with `image-rendering: pixelated` for chunky pixels. Raster OSM
  tiles cannot do this.
- **It can run fully local.** The PMTiles step removes every outside request for the map: better privacy (the tile
  server never learns which part of Houston someone looks at) and it works without internet.
- **No new Python package.** The JavaScript is loaded at an exact version (for example `maplibre-gl@5.x.y` and
  `pmtiles@4.x.y`, picked at step 1), or copied into `app/static/` for offline use (both are BSD-licensed).
- **Folium is the fallback** if the custom component takes too long: same data, same pins, OSM or Carto tiles,
  plainer look.

## How it plugs into Streamlit

| Piece | Where | Notes |
|---|---|---|
| Places for the map | `src/everflavor/stores.py`: a new `map_places(places, recipe=None, filters=...)` returning rows with `lat, lng, kind, name, address, reason, note` | The back end chooses the stores and writes the reason; the page only draws them (CLAUDE.md: decisions come from the back end). |
| Recipe -> store kinds | `stores.py`: a rule table `INGREDIENT_STORE_KINDS` (below) next to `COUNTRY_CUISINES` and `COUNTRY_REGIONS` | Same pattern as the other rule tables; tested in `tests/test_stores.py`. |
| The map | `app/map_view.html` (MapLibre, style JSON, pins) inside `st.components.v2.component` (bidirectional, in Streamlit 1.65) | Python sends the rows as JSON; a tap on a pin sends back only the `osm_id`. Fallback: `components.html` (one way, no tap back). |
| Tiles | Step 3: OpenFreeMap style URL. Step 6: `app/static/houston.pmtiles` with `server.enableStaticServing = true` in `.streamlit/config.toml` | The style JSON, glyphs and sprites are kept next to it for offline use. |
| Loading | `@st.cache_data` on the places table | About 1 MB of rows; loads once. |
| Colab | The app does not run in Colab; the download notebook (03) does, unchanged | Overpass needs only `requests`. |

## Recipes -> stores

| Recipe needs | Store kinds (OpenStreetMap tags) | Shown as |
|---|---|---|
| Spices, sauces, rice, noodles of a country | Grocery whose `cuisine` tag or name hint matches `COUNTRY_CUISINES`, then `COUNTRY_REGIONS` (today's `suggest_where_to_buy`) | "Indian grocery: for garam masala" |
| Meat | `shop=butcher`; `diet:halal` / `diet:kosher` when tagged | "Butcher, tagged halal-friendly in OpenStreetMap (unverified)" |
| Fish, shrimp | `shop=seafood` | "Seafood shop" |
| Fruit, vegetables, herbs | `shop=greengrocer`, `amenity=marketplace` (farmers' markets) | "Produce" |
| Bread, tortillas | `shop=bakery`; tortillerias by a new name hint "tortilleria" (no standard tag) | "Bakery" |
| Everything else | `shop=supermarket` (not `convenience`) | "Supermarket" |
| Eat the dish instead | `amenity=restaurant` with the recipe's `cuisine` | "Ethiopian restaurant" |

Rules the map keeps:

- **Only cautions, never promises.** No pin says a store has an item or is safe for an allergy. Every pin has
  the unverified line.
- **Diet words:** "tagged halal-friendly" or "tagged kosher-friendly", from OpenStreetMap tags only, never
  "halal" or "kosher".
- **Safety stays in the back end.** The map shows stores for recipes that already passed the safety gate; it never
  filters or re-checks recipes itself.

## Data: download once, refresh rarely

| Item | How | Size (Houston) |
|---|---|---|
| Places | Notebook 03 section 3, widened: a Greater Houston box (about lng -95.90 to -94.95, lat 29.45 to 30.20; team to confirm) instead of the 15 km circle; new categories `seafood`, `greengrocer`, `bakery`, `marketplace`; `convenience` split off; address tags (`addr:housenumber`, `addr:street`, `addr:postcode`) added | Estimate 5,000 to 10,000 places, under 2 MB (today: 1,543 places, 89 KB) |
| Basemap (step 6) | `pmtiles extract <daily build> houston.pmtiles --bbox=-95.90,29.45,-94.95,30.20 --maxzoom=15` | Estimate 50 to 150 MB; measure with `--dry-run` first |
| ZIP centers | Census ZCTA Gazetteer, Texas rows inside the box | Under 50 KB |
| Refresh | `REFRESH_DOWNLOADS = True` once per release (or monthly), as for the other caches | |

**Licenses and credit:**

| Data | License | Credit we show |
|---|---|---|
| OpenStreetMap places | ODbL 1.0: a database made from it must stay under ODbL if shared | "(c) OpenStreetMap contributors" with a link to openstreetmap.org/copyright, always visible on the map |
| OpenFreeMap tiles | Free, MIT software, OpenMapTiles schema | "OpenFreeMap (c) OpenMapTiles Data from OpenStreetMap" |
| Protomaps basemap | BSD (software), ODbL (data) | "Protomaps (c) OpenStreetMap" |
| MapLibre GL JS, pmtiles JS | BSD-3 | In `docs/sources.md` |
| Census ZCTA | Public domain | In `docs/sources.md` |

Our code is MIT; the places file is ODbL. If we ever commit or publish it, it needs its own ODbL note.

## Privacy

Following `docs/ethics_privacy.md` ("location is used only in real time to find stores; it is not stored or
shared"):

- **No location by default.** The map opens on downtown Houston.
- **ZIP code** is looked up in our own local table; no service is called.
- **"Use my location"** is a button; the browser asks the user first. The position stays in the browser to
  center the map and sort the list by distance. It is not sent to Python, not saved, and never in the audit log.
- **Tiles:** with OpenFreeMap, the tile server sees the visitor's IP and which part of Houston is viewed (like any
  web map). With the PMTiles file, nothing leaves the PC. The page says which one is in use.
- **No Google Places** in this plan, so no key and no request to Google.
- The page says it in one line: "Your location stays in your browser."

## Steps in order

| # | Step | Effort | Owner |
|---|---|---|---|
| 1 | Spike: a MapLibre map with OpenFreeMap tiles and today's 1,543 pins in `st.components.v2`; check that a tap returns the `osm_id`; pick the exact JS versions | 0.5 day | |
| 2 | Widen notebook 03 section 3: Houston box, new categories, addresses, convenience split; rerun section 3 only (cell by cell, `src/` frozen) | 1 day | |
| 3 | Back end: `map_places`, `INGREDIENT_STORE_KINDS`, reasons; tests in `tests/test_stores.py` | 1 day | |
| 4 | The "Where to buy" tab, the recipe-card button, filters, credits, the privacy line | 1 to 1.5 days | |
| 5 | Pixel style: a MapLibre style JSON in the app's palette, pixel pins from `design/`, chunky pixels | 1 to 2 days | team (art), Claude |
| 6 | Local tiles: Houston PMTiles extract, fonts and sprites in `app/static/`, static serving on; works with the network off | 0.5 to 1 day | |
| 7 | ZIP code box (Census table) and "Use my location" (browser only) | 0.5 day | |
| 8 | Docs: `docs/sources.md` rows, README numbers from the new run, `docs/ethics_privacy.md` line on tiles; version 0.6.0 or later (a new feature: MINOR) | 0.5 day | |

Total: about 6 to 8 days of work. Steps 1 to 4 give a working map; 5 to 7 make it ours and local.

## Open questions for the team

1. **Area:** Greater Houston box as above, the city limits, or keep the 15 km circle?
2. **Tiles:** is OpenFreeMap (outside requests) fine for the demo, or must the map be offline from day one (PMTiles)?
3. **Convenience stores:** drop them, or show them only when nothing else is near?
4. **Committing data:** keep `places.parquet` and the PMTiles file git-ignored (each person runs notebook 03),
   or commit a small Houston places file with its ODbL note so the app works right after cloning?
5. **Google Places:** stay off for good, or add later with a monthly cap for better "Ethiopian grocery" matches?
6. **Specialty grocers OpenStreetMap misses:** may the team add missing Houston shops to OpenStreetMap itself
   (the open fix), rather than to a private list?
7. **Restaurants:** show them in the first version, or only stores?
8. **Pixel look:** how far to go (pixel icons only, or the whole map pixelated)?

## Sources (read 2026-10-24)

- OpenFreeMap: <https://openfreemap.org/>
- OpenStreetMap tile usage policy: <https://operations.osmfoundation.org/policies/tiles/>
- Nominatim usage policy: <https://operations.osmfoundation.org/policies/nominatim/>
- Geofabrik Texas extract: <https://download.geofabrik.de/north-america/us/texas.html>
- Protomaps, getting started (`pmtiles extract --bbox`): <https://docs.protomaps.com/guide/getting-started>
- Streamlit `st.map` and `st.pydeck_chart` (Carto basemap): <https://docs.streamlit.io/develop/api-reference/charts/st.map>
