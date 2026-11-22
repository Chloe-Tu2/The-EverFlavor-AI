# Licence compliance

How each kind of licence among our sources may be used, and what it obliges us to do. The full list of sources,
with each licence, is [docs/sources.md](../sources.md); this page groups them. It is a summary for the team, not
legal advice, and licence decisions need a person ([human_approval_workflow.md](human_approval_workflow.md)).

The code is MIT (`LICENSE`, © 2026 EverGlow Team). The MIT licence covers our code only, never the data we read.

## By kind of licence

| Licence | Sources (examples) | We must | We must not |
|---|---|---|---|
| Public domain, CC0, US government work | USDA (FoodData Central, FoodKeeper, cooking yields), Wikidata, Food.com (irkaal set) | Nothing required; we credit anyway | Claim the data as ours |
| CC BY 4.0 | Freshness image sets, Our World in Data | Credit the source, link the licence, say what we changed | Drop the credit |
| CC BY-SA (3.0, 4.0) | Wikipedia intros, many Commons photos | Credit, and share what we derive under the same licence | Put derived text under a stricter licence |
| CC BY-NC-SA 3.0 | CulinaryDB, RecipeDB | Credit, share alike, **non-commercial use only** | Use it in anything sold or ad-funded |
| ODbL | OpenStreetMap, Open Food Facts | Credit "© OpenStreetMap contributors"; share a derived database alike | Mix it into a closed database |
| Unicode License V3 | CLDR regions | Keep the copyright notice (`data/knowledge/atlas/regions.json`) | Remove the notice |
| Site or dataset terms | Food.com (Kaggle, research use), Hugging Face recipes, TheMealDB, Google Places | Follow the terms; store only what they allow (Google: place IDs only) | Use TheMealDB photos (unlicensed) |

## Open questions for the team

These are written in [needs_human_review.md](needs_human_review.md) too:

1. **Non-commercial data.** CulinaryDB and RecipeDB are non-commercial (CC BY-NC-SA), and Open-Meteo is free for
   non-commercial use. As long as EverFlavor is a class project this is fine; any commercial use later needs them
   removed or relicensed.
2. **Share-alike.** Wikipedia text (CC BY-SA) and ODbL data oblige derived works to keep those licences. The repo
   should say so next to the MIT licence, so no one reads MIT as covering the data.
3. **Hugging Face recipe photos.** Their licence is not confirmed; until it is, the image audit counts them as
   "to confirm", never as verified.
4. **Food.com (research use) and the USDA SNAP-Ed guide** ("not stated"): confirm the terms before a public launch.

## Images

Only free licences (CC0, public domain, CC BY, CC BY-SA), each photo with its author and licence in its credit
line; files with no author to credit, a non-free licence, or under 400 px are not queued
(`data/knowledge/media/approved_image_queue.json`). No image from a source with no licence (TheMealDB) and no
AI-generated image is shown as a real dish.
