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

The map opens from a third tab, **Map**, next to Find recipes and Check my recipe, with its own pixel icon (a map
pin) like the other tabs. Planned for later (the 0.7.1 plan in [README.md](README.md)).

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

## Making it a real store locator (research 2026-10-26)

Written 2026-10-26 (Claude, for med27-coder). A plan only: no code changed. It adds to the plan above; the
open questions above stay as they are.

### Where the Map tab is today

Since this plan was written, a first map shipped: the third tab "Map: Houston" in `app/app.py`.

- A pydeck `ScatterplotLayer` over OpenFreeMap vector tiles (`tiles.openfreemap.org/styles/liberty`), no key.
- Places from `data/processed/places.parquet`; pills for Grocers, Restaurants and Butchers.
- A toggle "Only (cuisine) places (from your search)": it matches words in the cuisine tag, name hint and name.
- A tooltip with name, kind, cuisine and "Unverified: check with the store". Credits in a caption.
- No list, no click, no ZIP box, no location, no clustering. Houston's 15 km circle only.

`stores.osm_places` asks Overpass for `nwr` with `amenity=restaurant`,
`shop=supermarket|convenience|greengrocer|deli` and `shop=butcher` `around:15000` of downtown (29.7604, -95.3698),
and caches the answer in `data/raw/osm_cache/houston_tx_<category>_15000.json`. It keeps no address tags.

### What good store locators do

Read from store-locator guides (Storemapper, Econsultancy, MetaLocator) and from how Google Maps, Yelp, H-E-B,
Whole Foods, Starbucks and Airbnb lay out their maps. The same patterns come back every time:

| Pattern | What it means for us |
|---|---|
| **A list beside the map** | The map alone is hard to read. A short list (name, kind, distance, one reason) sits beside it. |
| **Synced selection** | Click a pin: its row is highlighted and its card opens. Click a row: the map flies to the pin. |
| **5 to 10 results at a time** | The list shows the nearest 10, with "Show more". More rows confuse people. |
| **Search by ZIP, city or place** | "ZIP only" is called a frustration for people new to an area. We start with ZIP and Houston neighborhoods. |
| **"Use my location"** | A button; the browser asks first. Guides suggest auto-detecting by IP: we do not (privacy). |
| **Filters** | Kind (grocer, restaurant, butcher...), cuisine, distance, "open now", "tagged halal-friendly". |
| **Clustering** | Many pins become one bubble with a count; it splits on zoom. |
| **A details card** | Name, address, hours, website, phone, directions link, "Unverified" line. |
| **"Search this area"** | When the map is moved, a button reloads the list for the new view, not on every pan. |
| **Directions as a link** | One tap opens a map app; the locator does not route itself. |
| **Phone layout** | A "List / Map" switch, or the map with a bottom sheet of results; one-tap call and directions. |
| **Fast** | Guides say the whole flow should take under 10 seconds. |

### Three ways to build it (Streamlit 1.65.0 installed; pydeck 0.9.3)

| | pydeck (`st.pydeck_chart`, today) | `streamlit-folium` (Leaflet) | **MapLibre GL JS in `st.components.v2`** |
|---|---|---|---|
| New packages | None | `folium`, `streamlit-folium` (not installed) | None in Python; MapLibre JS at an exact version (later copied to `app/static/`) |
| Click back to Python | Yes: `on_select="rerun"` returns the selected objects per layer id | Yes: last clicked object, map bounds, zoom | Yes: `setTriggerValue` sends what we choose (`osm_id`, bounds) |
| Map bounds back ("search this area") | No | Yes, but every pan can rerun the app unless limited | Yes, only when the button is pressed |
| Clustering | Not built in (no cluster layer); only grids/hexagons or our own clustering in Python | `MarkerCluster` / `FastMarkerCluster` plugins | Built in: GeoJSON source `cluster: true`, `clusterRadius`, `clusterMaxZoom` |
| Thousands of points | Fast (WebGL) | Slow with DOM markers above a few thousand; FastMarkerCluster helps | Fast (WebGL, clusters on the GPU side) |
| Pixel-art look | Pixel PNG pins via `IconLayer`; basemap style is a URL only | Raster tiles; CSS filters only | Full style JSON: palette, pixel font, pixel pins, `pixelated` rendering |
| "Use my location" | No | Plugin (LocateControl) | Browser geolocation in our own JS; position can stay in the browser |
| Offline | No (tiles from OpenFreeMap) | No (OSM raster tiles forbid it) | Yes, with a Houston PMTiles file |
| Work | Small: already running | Medium | Medium to large: JS to write and test |

**Recommendation: MapLibre GL JS in a `st.components.v2` component (as the plan above says), reached in two
moves.** First make today's pydeck tab a real locator in Python (list, synced selection with `on_select`, ZIP
box, details card), because all of that is reused unchanged. Then swap only the map widget for MapLibre to get
clustering, "search this area", "use my location" and the pixel style. Folium stays the fallback if the custom
component stalls. Why not stop at pydeck: no clustering, no bounds, no location, and little control over the look.

### Target UX (short spec)

**Desktop (wide layout):**

- Top bar: a ZIP / neighborhood box, a "Use my location" button, kind pills, a cuisine select, a distance select
  (2, 5, 10, 25 miles), "Open now" (hidden when hours are unknown), "Tagged halal-friendly / kosher-friendly".
- Left, about one third: the list. Each row: pixel icon, name, kind and cuisine, distance, one reason
  ("Indian grocery: for garam masala"), and "Unverified". Nearest first; 10 rows, then "Show more".
- Right: the map. Clusters with counts; pixel pins when zoomed in; the selected pin is bigger and outlined.
- Clicking a row or a pin opens the card: name, address, opening hours as written in OpenStreetMap, website,
  phone, "Directions" (Google Maps link, opens a new tab), "See on OpenStreetMap" (`openstreetmap.org/<osm_id>`),
  "Report a mistake" (the OpenStreetMap note link), and "Unverified: check with the store before you go."
- When the map is moved, a "Search this area" button appears; the list changes only when it is pressed.
- Empty state: "No (kind) found here. Try a wider distance, or see the region's stores." (from the back end's
  region fallback, `COUNTRY_REGIONS`).
- Credits always visible at the bottom right of the map; one privacy line under the box.

**Phone (narrow):**

- A "List / Map" switch at the top (Streamlit has no real bottom sheet; a switch is simple and accessible).
- The map view shows one card at the bottom for the selected place, with big "Directions" and "Call" buttons.
- Filters fold into one "Filters" expander.

### Houston coverage (from `places.parquet` and the Overpass cache, 2026-10-04 query)

| Fact | Value |
|---|---|
| Places | 1,543: 959 restaurants, 577 groceries, 7 butchers |
| Groceries by OSM tag | 477 convenience (gas stations included), 93 supermarkets, 7 delis, 0 greengrocers |
| Area | A 15 km circle, about 700 km² (lat 29.653 to 29.890, lng -95.523 to -95.215) |
| Street address tagged | 1,088 of 1,543 (70%); ZIP tagged on 609 (39%) |
| Opening hours / website | 453 (29%) / 410 (27%) |
| Cuisine tag / name hint | 722 / 80 |
| Phone | 356 (23%) |
| Top grocery brands | Circle K 20, Kroger 12, Fiesta Mart 9, Shell 9, H-E-B 9, Whole Foods Market 6 |

So in real terms the circle has **93 supermarkets and 7 butchers**: too few for a locator. Most of Houston's
international grocers (Bellaire Boulevard's Asian markets in Alief, Hillcroft's South Asian and Middle Eastern
shops, Katy's and Sugar Land's Indian markets) are outside the circle or at its edge.

**How to widen to Greater Houston:**

- The metro area (Houston-Pasadena-The Woodlands) has 10 counties: Harris, Fort Bend, Montgomery, Brazoria,
  Galveston, Liberty, Waller, Chambers, Austin, San Jacinto; about 7.8 million people (2025).
- For the prototype, the box above (lng -95.90 to -94.95, lat 29.45 to 30.20, about 7,600 km²) covers all of
  the populated core of Harris, north Fort Bend (Sugar Land, Missouri City), south Montgomery (The Woodlands,
  Spring), north Brazoria (Pearland) and the north of Galveston County (League City). It leaves out the rural
  counties, which is fine for a demo.
- Query with a `(south,west,north,east)` bbox instead of `around:`; one query per category; save to the cache as
  today. Before downloading, run each query once with `out count;` to get the numbers (5 queries, once). The old
  estimate of 5,000 to 10,000 places stays until that count is run.
- Add tags: `addr:*`, `phone`, `contact:phone`, `wheelchair`, `shop` (to tell supermarkets from convenience),
  and the new kinds `shop=seafood|bakery|greengrocer`, `amenity=marketplace`.
- Overpass fair use is about 10,000 requests and 1 GB per day per user; we need about 7 requests per refresh,
  so this is far inside it. The Geofabrik Texas extract stays the fallback if Overpass times out.

**Being honest about gaps:**

- Every place keeps "Unverified: check with the store before you go."
- A small line under the list: "From OpenStreetMap, which misses some shops, especially small family-run
  grocers." With a "Report a mistake" link to OpenStreetMap (the open fix, open question 6).
- A place with no hours shows "Hours not listed", never "Closed". "Open now" shows only places with hours, and
  says how many it left out.
- Places with no name (145 today) are shown as "Unnamed (kind)" or hidden; the team picks (no new question
  needed; default: hidden from the list, kept on the map).

### ZIP search without a paid API

- Download the Census **ZCTA Gazetteer** file once (2026 national file, 1.0 MB zipped; public domain). Keep
  `GEOID, INTPTLAT, INTPTLONG` for ZCTAs inside the Houston box (a few hundred rows, under 50 KB).
- A typed 5-digit ZIP -> its center, looked up locally in `stores.py` (`zip_center(zip_code)`). No service is
  called, so it works in Colab, VS Code and Antigravity and offline.
- Say it honestly: ZCTAs are the Census's version of ZIP codes and do not match them exactly; a ZIP that is not
  in the table gets "ZIP not found in the Houston area".
- Neighborhoods ("Alief", "Montrose", "Katy") come from a small hand-written table of names and centers in the
  same file, recorded as a policy with who wrote it. No Nominatim, no Google geocoding.
- Distance is straight-line (haversine) in the back end, shown as "about 3 mi". Driving time would need a
  routing API; we leave that to the directions link.

### How it links to recipes

- A recipe card gets a "Where to buy" button. It opens the Map tab with that recipe's places.
- The places and the reason line come from the back end: `stores.suggest_where_to_buy` (the same one
  `agent_tools.where_to_buy_tool` and the crew's sourcing step use), through the planned `stores.map_places`.
  The page only draws them.
- The reason says what to look for, never that the store has it or that it is safe: "Indian grocery: may carry
  garam masala. Unverified."
- The map only shows stores for recipes that already passed the safety gate; it never filters or re-checks a
  recipe. Diet filters use OpenStreetMap tags and say "tagged halal-friendly", never "halal".
- "Where to eat it": restaurants whose cuisine tag matches the recipe's cuisine (if the team keeps restaurants,
  open question 7).

### Privacy for the locator

- **No location by default.** The map opens on downtown Houston.
- **ZIP:** looked up in our local table; it lives only in the session while the page is open.
- **"Use my location":** a button; the browser asks first. In the MapLibre step the position stays in the
  browser: the component snaps it to the nearest ZIP center from the same table and sends only that ZIP to
  Python. Nothing is saved, nothing is in the audit log. In the pydeck steps there is no location button.
- **No IP-based location**, even though store-locator guides suggest it.
- **Outside requests:** OpenFreeMap tiles (the server sees the IP and the area viewed) until the PMTiles step;
  the directions link goes to Google Maps only when the user taps it, and the card says so ("opens Google Maps").
- The page says it in one line: "Your location stays in your browser. Nothing is saved."

### Accessibility

- The list is the accessible way in: every place on the map is also a row in the list, readable by a screen
  reader and by keyboard. The map is an extra, not the only way.
- Pins and rows at least 24 by 24 CSS pixels (WCAG 2.2, 2.5.8); the selected item is shown by outline and size,
  not only by color.
- Kinds have both a pixel icon and a word ("Grocer"); colors meet 3:1 contrast against the map.
- Keyboard: Tab through the list; Enter opens the card; the map component gets `+`/`-` and arrow keys
  (MapLibre's keyboard handler) and a visible focus ring.
- Credits and the "Unverified" line are text, not part of the tile image.

### Steps in order (each one can ship alone)

| # | Step | Effort | Depends on open questions |
|---|---|---|---|
| A | Back end: `stores.map_places` (rows with kind, address, distance, reason, unverified note), `zip_center`, haversine; tests in `tests/test_stores.py` | Small | 3 (convenience), 7 (restaurants) |
| B | Data: notebook 03 section 3 widened to the Greater Houston box with `out count;` first, address/phone/shop tags, new kinds; rerun section 3 only, `src/` frozen during the run; ZCTA table | Medium | 1 (area), 3, 4 (committing data) |
| C | Locator in the current pydeck tab: list beside the map, `on_select` synced selection, details card with directions and OSM links, ZIP box, distance and kind filters, phone "List / Map" switch | Medium | 7 |
| D | "Where to buy" button on recipe cards, opening the Map tab with that recipe's places and reasons | Small | none |
| E | MapLibre component (`st.components.v2`): same rows, clustering, "Search this area", selection back as `osm_id`; pydeck stays as fallback behind a setting | Large | 2 (tiles) |
| F | "Use my location" in the component (browser only, snapped to a ZIP); "Open now" from `opening_hours` | Small | none |
| G | Pixel style JSON, pixel pins and clusters from `design/` | Medium | 8 (pixel look) |
| H | Offline: Houston PMTiles, JS and fonts in `app/static/`, static serving on | Medium | 2, 4 |
| I | Docs: `docs/sources.md` (Census ZCTA, MapLibre, Overpass), `docs/ethics_privacy.md` lines, README numbers from the new run, version bump | Small | none |

A to D give a real locator with today's tools in about 3 to 4 days. E to H make it fast, local and ours.
Open questions 5 (Google Places) and 6 (adding shops to OpenStreetMap) do not block any step.

### Sources for this section (opened 2026-10-26)

- Storemapper, 10 store locator best practices: <https://storemapper.com/blog/10-store-locator-best-practices-to-help-people-find-your-business>
- Econsultancy, store locator mobile UX: <https://econsultancy.com/store-locator-tools-which-retailers-offer-the-best-mobile-ux/>
- Streamlit `st.pydeck_chart` (`on_select`, Carto basemap): <https://docs.streamlit.io/develop/api-reference/charts/st.pydeck_chart>
- Streamlit `st.components.v2.component`: <https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component>
- streamlit-folium: <https://github.com/randyzwitch/streamlit-folium>
- deck.gl IconLayer (no built-in clustering): <https://deck.gl/docs/api-reference/layers/icon-layer>
- MapLibre style spec, GeoJSON source clustering: <https://maplibre.org/maplibre-style-spec/sources/>
- Protomaps, PMTiles with MapLibre: <https://docs.protomaps.com/pmtiles/maplibre>
- OSM attribution guidelines: <https://osmfoundation.org/wiki/Licence/Attribution_Guidelines>
- Overpass API fair use: <https://dev.overpass-api.de/overpass-doc/en/preface/commons.html>
- Census Gazetteer files: <https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html>
- Census Gazetteer record layouts: <https://www.census.gov/programs-surveys/geography/technical-documentation/records-layout/gaz-record-layouts.html>
- Google Maps URLs (no key needed): <https://developers.google.com/maps/documentation/urls/get-started>
- Greater Houston (counties, population): <https://en.wikipedia.org/wiki/Greater_Houston>
- WCAG 2.2, target size (minimum): <https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html>

## Sources (read 2026-10-24)

- OpenFreeMap: <https://openfreemap.org/>
- OpenStreetMap tile usage policy: <https://operations.osmfoundation.org/policies/tiles/>
- Nominatim usage policy: <https://operations.osmfoundation.org/policies/nominatim/>
- Geofabrik Texas extract: <https://download.geofabrik.de/north-america/us/texas.html>
- Protomaps, getting started (`pmtiles extract --bbox`): <https://docs.protomaps.com/guide/getting-started>
- Streamlit `st.map` and `st.pydeck_chart` (Carto basemap): <https://docs.streamlit.io/develop/api-reference/charts/st.map>
