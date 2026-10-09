# Data

Everything here is made by the [notebooks](../notebooks/README.md), and almost none of it is on GitHub: the files
are too large (about 32 GB in all) and can be rebuilt at any time by running the notebooks again.
Only this README, `reference/` and the empty-folder markers (`.gitkeep`) are committed.

| Folder | What is in it | On GitHub |
|---|---|---|
| `reference/` | Small hand-made tables with their sources (`cooking_fats.csv`) | **Yes** |
| `raw/` | Original downloads, caches and samples: recipes, USDA, Open Food Facts, Wikidata, FoodKeeper, OpenStreetMap, freshness photos (32 GB) | No |
| `interim/` | The combined, cleaned recipe table (`recipes_all.parquet`) and cooking labels | No |
| `processed/` | Final tables: train / val / test splits, nutrition, knowledge, stores, variants, freshness index, charts | No |

Which notebook writes which file: [notebooks/README.md](../notebooks/README.md#run-order).
Column meanings: [docs/data_dictionary.md](../docs/data_dictionary.md). Sources and licenses: [docs/sources.md](../docs/sources.md).

**Lost or broken data?** Delete the folder's contents and run the notebook again; downloads already on disk are reused.
