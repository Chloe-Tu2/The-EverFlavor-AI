# More data for every model: plan

Written 2026-10-22 (Claude, with med27-coder). What each model is short of, which datasets could fill the gap, and
in what order to download them. Nothing here is downloaded yet. The project's rules hold: read each license on the
dataset's own page before downloading, record it in [docs/sources.md](../sources.md), keep the files in `data/raw/`
(never committed), and note the download date and checksum (data backlog item 6).

## Rule: open or research-use data only (med27-coder, 2026-10-24)

New data comes only from datasets with an open license (for example CC0, CC BY, CC BY-SA, ODbL, or a public
domain or government source such as USDA). No scraping of forums, social media or video comments: their terms
forbid it, the posts carry people's names, and they are not open data.

Decided (med27-coder, 2026-10-24): EverFlavor is a research project, so datasets licensed for research or non-commercial use are
allowed too, and the recipe sources below stay. A public or commercial release would need them checked again.
Scraping stays ruled out. The recipe sources and their licenses:

| Source | License today | Open? |
|---|---|---|
| Food.com (Kaggle, 218k recipes, the only times and steps) | Research use, see the dataset page | No |
| Hugging Face recipes-with-nutrition (37.8k, the demo data) | Not stated on the dataset page | Unclear |
| CulinaryDB (35k) | CC BY-NC-SA 3.0 | Open, but non-commercial |
| TheMealDB (583) | The site's terms | No |

Open candidates to replace or add to them: Wikibooks Cookbook (CC BY-SA), USDA data (public domain),
Open Food Facts (ODbL, already used), Wikidata (CC0, already used).

## What each model is short of

| Model (notebook) | Today | What limits it |
|---|---|---|
| Recipe country / cuisine (01) | Food.com, recipes-with-nutrition, CulinaryDB, TheMealDB | 131k of 230k recipes with a known country are from the US; Canada and Australia are rarely recognized; the demo site shows source-site cuisine tags that are wrong (bug report) |
| Calories and nutrients (01, 07) | USDA matches for ingredients | Automatic USDA matches pick cured products ("beef" as corned beef); few recipes keep ingredient amounts |
| Cooking method and likely fat (02) | Food.com steps, hand-checked labels | Steps from one site; few non-US cooking methods |
| Freshness from photos (05) | 6 Mendeley sets (fruit, banana, fish eyes) | Fish: the Freshness of the Fish Eyes photos score 0.76 against 0.97 for the other fish set; no meat or bread yet |
| Recipe photo check (planned, RELIABILITY item 2) | None | The demo shows site logos and wrong photos (bug report) |
| AI explanations and meal planner (09) | Our own evaluation questions | Too few questions per diet and region to measure hallucinations well |

## Candidates

| Dataset | For | Size | License (to confirm on its own page) | Notes |
|---|---|---|---|---|
| [DaFiF](https://data.mendeley.com/datasets/vx4ptwk3pb) | Freshness: fish | 2,536 photos, mackerel, tilapia, tuna, with eye and gill scores | CC BY 4.0 (already in sources.md) | Needs a label reader; the most direct fix for the weak fish results |
| [MeatScan](https://zenodo.org/records/16764338) | Freshness: beef | 10,561 photos, 25 GB | CC BY 4.0 (already in sources.md) | Already wired as opt-in in notebook 05; needs about 50 GB free while it unpacks |
| [INDoRI](https://arxiv.org/pdf/2309.10403) | Country: Indian recipes | 5,187 recipes with cuisine, category, time | Not stated in the paper: ask the authors | Indian is the region with the most recipes after the US in our data |
| [tastyR](https://r-packages.io/packages/tastyR) | Country | 2,218 Allrecipes recipes by country | CC0 for the package; Allrecipes' own terms apply to the content | Small; good for testing the country model on labeled recipes |
| [Wikibooks Cookbook](https://en.wikibooks.org/wiki/Cookbook:Cuisines) | Country: all regions | Thousands of recipes, grouped by cuisine | CC BY-SA 4.0 | Data backlog item 2; open license, needs a careful page reader |
| [RecipeDB](https://cosylab.iiitd.edu.in/recipedb/) | Country and nutrition | About 118k recipes, 74 countries, amounts and USDA nutrition | CC BY-NC-SA 3.0, no bulk download | Needs a data request to the authors (the team's decision) |
| [RecipeNLG](https://github.com/Glorf/recipenlg) | Cooking methods, amounts | 2.2 million recipes, under 1 GB | No known license; terms accepted at download | Research use only; mostly US sites, so it does not fix the region gap |
| [ISIA Food-500](https://arxiv.org/pdf/2008.05655) | Photo check | 399,726 photos, 500 dishes | Reported as CC BY 4.0 by an aggregator, not by the authors | Large; only if the zero-shot check below is not good enough |
| [Food-101](https://labelbox.com/datasets/food-101/) | Photo check | 101,000 photos, 101 dishes | Reported differently by different sites | Same as above |

Fish eye sets already in use: [Multistage Fish Eyes](https://data.mendeley.com/datasets/67nmx3mhwh) and
[Freshness of the Fish Eyes](https://data.mendeley.com/datasets/xzyx7pbr3w) (CC BY 4.0).

## Order (smallest download and biggest gain first)

1. **No download: fix what we have.** The demo data's cuisines through notebook 01's country logic (bug report),
   hand-checked USDA matches for the top automatic ones (corned beef), and Open Food Facts' EU allergens.
2. **DaFiF** (about 8 GB, downloading 2026-10-22): a label reader in notebook 05, then retrain the fish model and report per source.
3. **Photo check without new data:** a zero-shot image check (is it food, does it match the dish name) with a CLIP
   model, judged on a few hundred demo photos the team labels by hand. Download Food-101 or ISIA Food-500 only if
   that is not good enough.
4. **More regions for the country model:** Wikibooks Cookbook (open license) and tastyR first; INDoRI and RecipeDB
   after asking their authors. Report results per country, as notebook 01 already does.
5. **Hallucinations:** more evaluation questions for notebook 09, written from our own tables (every answer
   checkable against a row), per diet and region. No outside data needed.
6. **MeatScan** (25 GB) when there is disk space: beef freshness.

## Decisions for the team

- Non-commercial licenses (RecipeDB, CulinaryDB already) are fine for the capstone; a public release would need them
  out or a license check.
- Who asks the INDoRI and RecipeDB authors for data.
- Disk space for MeatScan (about 50 GB free while unpacking).
