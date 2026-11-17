# Data

Everything here is made by the [notebooks](../notebooks/README.md), and almost none of it is on GitHub: the files
are too large (about 32 GB in all) and can be rebuilt at any time by running the notebooks again.
Only this README, `reference/`, `demo/`, `knowledge/` and the empty-folder markers (`.gitkeep`) are committed.

| Folder | What is in it | On GitHub |
|---|---|---|
| `demo/` | What the live site runs on (it has only what is in git): 3,000 recipes (Hugging Face rows) with their country where the full data has one; notebook 03's 5,473 OpenStreetMap places (ODbL, credited on the map); the USDA nutrition table and household weights (public domain) for Check my recipe's estimate. Rebuilt from the full data with `python scripts/demo_extras.py` | **Yes** |
| `reference/` | Small hand-made tables with their sources (`cooking_fats.csv`; `walter_injection_set.csv`: 71 labelled questions, attacks and real food questions, for the waiter's screen; `dish_photo_review.csv` and `recipe_photo_review.csv`: photos a person turned down, for a dish in general or for one recipe, with the reason; `specialty_ingredients.csv`: 50 specialty ingredients (harissa, gochujang, masa harina...) with their aliases, cuisines, the kinds of store that usually stock them and a sourced note (Wikipedia, CC BY-SA), each awaiting a team member's review; `place_evidence.csv`: the map's verified diet rows, entered by hand from a certifier's public list or the business's own site, with the link, the date and who checked; empty until the team adds them; `may_contain.csv`: 33 rows for 22 foods usually (likely) or sometimes (possible) made with something a profile watches, such as teriyaki sauce (sake or mirin) or satay sauce (peanuts), one row per flag, each with the Wikipedia article that says so, awaiting a team member's review; `food_taxonomy.csv`: the Food Taxonomy, 150 places from world to culinary region, every recipe country included, countries placed by the UN's geographic regions (M49), proposed for the team's review) | **Yes** |
| `raw/` | Original downloads, caches and samples: recipes, USDA, Open Food Facts, Wikidata, FoodKeeper, OpenStreetMap, freshness photos (32 GB), USDA ERS livestock data (`ers_livestock/`) and past weather (`weather/`, notebook 08) | No |
| `interim/` | The combined, cleaned recipe table (`recipes_all.parquet`) and cooking labels | No |
| `processed/` | Final tables: train / val / test splits, nutrition, knowledge, stores, variants, freshness index, meat supply and pasture seasons (`meat_supply_seasons.csv`, `pasture_seasons.csv`), charts; `foodcom_details.parquet` (Food.com prep and cook times, servings and extra nutrition, from `scripts/recipe_details.py`) | No |

Which notebook writes which file: [notebooks/README.md](../notebooks/README.md#run-order).
Column meanings: [docs/data_dictionary.md](../docs/data_dictionary.md). Sources and licenses: [docs/sources.md](../docs/sources.md).

The AI agents (`agent_tools.load_agent_data`) read these same tables; a tool whose table is missing is simply not offered.

**Out of date?** When the flag or diet rules change, `python -m everflavor.refresh` updates the saved tables in about
20-25 minutes instead of rerunning notebook 01 (about an hour) (see [notebooks/README.md](../notebooks/README.md#when-the-rules-change)); `dataset_info.json` holds the
fingerprint of the rules the data was built with.

**Lost or broken data?** Delete the folder's contents and run the notebook again; downloads already on disk are reused.
