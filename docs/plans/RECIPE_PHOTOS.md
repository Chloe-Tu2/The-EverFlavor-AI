# Recipe photos: use the ones we have, show them whole, hide the wrong ones

Plan written 2026-10-25 (Claude, with med27-coder). Builds on [RELIABILITY.md](RELIABILITY.md#2-recipe-photos)
(the options and their pros and cons). Nothing here is built yet.

## What we have

| Data | Recipes | With a photo | Where the photos are |
|---|---|---|---|
| Demo data (`data/demo`, the live site) | 1,000 (train split) | 994 | Hugging Face recipes-with-nutrition's own image links |
| Full data (`data/processed`) | 204,319 (train split) | 0: the column is not kept | Hugging Face rows (37,823) have the same image links in the raw data; TheMealDB rows (583) have a thumbnail (`strMealThumb`); Food.com and CulinaryDB have none |

The two problems the team saw: some photos are **too zoomed in** to see the dish, and some are **not the dish**
(a site logo, a different recipe, bread on top of beans).

## Downloaded (2026-10-25)

The photos the sources give are downloaded once into `data/raw/recipe_photos/` (git-ignored, 2.62 GB) with
`data/raw/recipe_photos/manifest.csv` (source, our recipe_id, recipe name, link, file, size, width, height, hashes).
Scripts: `scripts/recipe_photos/` (build_links.py, fetch.py, analyze.py; paced, resumable).

| Source | Recipes with a photo | Downloaded | Failed |
|---|---|---|---|
| Hugging Face | 37,605 (all but 260 of its rows in the full data; every demo photo is one of them) | 37,082 files | 0 |
| TheMealDB | 583 | 583 | 0 |

- **recipe_id:** Hugging Face `hf_<row>` of the pinned revision (as in `pipeline._prepare_huggingface`, names
  match for all 37,823 rows); TheMealDB `themealdb_<idMeal>` (thumbnails from its free API, test key "1").
- **Logos found:** by image hash, 27 pictures are shared by 3 or more recipes (1,107 recipes): Food Network's
  logo alone on 866 recipes (under 355 different links), Food & Wine 98, Allrecipes 20. These are hidden first
  (step 4 below), by hash, not by link.
- Most photos are 600 x 600 or 300 x 300; 24 are under 5 KB (to check).

## Photos of dishes in general (2026-10-25)

For recipes with no photo of their own, a free photo of the dish in general: Wikidata's chosen picture (P18)
for 327 dishes, from Wikimedia Commons, free licenses only (CC0, public domain, CC BY, CC BY-SA), with author
and license (`scripts/dish_photos/fetch_dish_photos.py`, files in `data/raw/dish_photos/`, table
`data/processed/dish_photos.parquet`). 33,260 recipes get one. The card says it plainly: "A photo of potato
salad in general, not this recipe", with the credit linking to the file's page.

- A dish photo is matched only when the recipe's clean name names the dish (two words or more) and the countries
  fit; brand products, diagrams and wrong dishes were deleted (13 files).
- **Review:** `data/reference/dish_photo_review.csv` turns a dish's photo down (keep = no, with the reason and who
  decided). Claude checked the 60 most used photos by eye and turned down 6 (bread pudding, chicken soup,
  vegetable soup, pie crust, clam chowder, yellow rice). The team checks the rest the same way.
- The recipe's own photo always wins; a hidden logo falls back to the dish photo.

**Second round (2026-10-26).** `fetch_dish_photos.py <stage> --extend --top 1000 --min-words 2` targets only the
124,554 recipes with no photo at all: no own photo that passes (photo_ok, clip_score -0.03 or more), no Food.com
photo link and no dish photo yet (91,470 Food.com, 31,540 CulinaryDB, 1,537 Hugging Face, 7 TheMealDB). It skips
the dishes already in the table, matches dish phrases of two words or more, keeps its caches apart and appends.

- Of the next 1,000 dishes by recipes covered, 246 have no Wikidata picture and 13 are not free; 712 photos kept
  (17 deleted: brand products, diagrams, menus, labels, logos, drawings, narrow pictures).
- They cover 4,066 more recipes; the round is a long tail (a median of 4 recipes per dish, 22 at most).
- Claude checked the 80 most used new photos by eye and turned down 8 (rice cake, chocolate bar, peanut butter,
  pork belly, chicken dish, rice dish, wacky cake, deep-dish pizza). After the review: 3,956 more recipes.
- Totals: 1,025 dish photos shown (both rounds, after review) for 37,216 recipes; 120,598 recipes still have no
  photo. The folder `data/raw/dish_photos/` is 62 MB.

## Photo check (step 5, first run 2026-10-25)

`scripts/recipe_photos/check_photos.py` (run with `python -I`; steps embed, score, sample, eval) scores every own
photo against its dish's clean name with CLIP ViT-B/32 (OpenAI weights, MIT license, `open_clip`, on the CPU;
model cached in `data/raw/clip_models/`). Results: `data/processed/photo_check.parquet` (recipe_id, clip_score,
rank_score) for 38,188 recipes (37,665 photo files, 35,864 dish names).

- **clip_score:** how much closer the photo is to `"a photo of <dish>, a type of food."` than to four generic
  food prompts. Median 0.066; below 0 the photo fits food in general better than this dish.
- **rank_score:** the share of 50 random other dish names that fit the photo worse than its own name. Median
  1.00, so it separates only the bottom of the list.
- **Time:** 36 minutes for the images, 48 minutes for the dish names and scores (a laptop CPU).
- **Sample:** `data/reference/photo_check_sample.csv`, 200 photos, 20 from each of 10 score bands. Claude
  labelled 74 by eye (6 per band and all 20 of the lowest band), `checked_by` "Claude (draft)": 7 are not the
  dish (3 site logos, a drawing, a birthday cake for cinnamon rolls, raw rice for a risotto, a party table).

**Proposed cutoff: hide when clip_score is below -0.03.** On the 74 labels: precision 1.00, recall 0.71 (5 of
the 7 wrong photos hidden, no right ones). It hides 1,270 photos: 931 are pictures shared by 3 or more recipes
(the logos step 4 hides anyway) and 339 more. Of 12 of those 339 checked by eye, 8 were wrong (raw mussels for
"Fideos with Seafood", a pig drawing for pancakes, beer and beans for "Wilted Collards", bare rocket for
"Salad Nicoise") and 3 were right (a pasta with text on it, pâté chinois, a mala dry pot): CLIP knows less
common dish names less well.

- Missed at this cutoff: a party table for "Crispy Chicken Bites" (-0.027), raw rice for the risotto (-0.009).
- rank_score below 0.5 does about as well (precision 1.00, recall 0.57, 741 photos); keep it as a second view.
- Only 7 wrong photos in the labels, so the cutoff is a first guess: the team labels the other 126 rows (and
  checks Claude's), then `check_photos.py eval` gives the new precision and recall.

## Food.com's own photos (notebook 11, 2026-10-25)

The CC0 Kaggle dataset Food.com - Recipes and Reviews (irkaal) has 217,716 of our 218,024 Food.com recipes under the
same recipe numbers (the names agree for 95.9% once punctuation is ignored; the rest differ only by HTML codes such
as `&amp;`), and **111,803 of them (51.3%) have a photo of their own**: links saved in
`data/processed/foodcom_photo_links.parquet`. Next: download them (notebook 11, `DOWNLOAD_PHOTOS`), the logo
fingerprint and the photo-matches-dish check, then the app shows them.

### Download paused (2026-10-26)

The download was stopped on request at **74,277 of 111,803 photos** (`data/raw/foodcom_photos/foodcom/`, each
try logged in `results.jsonl`). The script writes `manifest.csv` only at the end, so the app shows none of them
yet. To finish, in order:

| # | Step | Command or place | Time (estimate) |
|---|---|---|---|
| 1 | Resume the download; it skips every link already in `results.jsonl` and writes `manifest.csv` | `python -I scripts/recipe_photos/fetch.py data/raw/foodcom_links.csv data/raw/foodcom_photos` | about 2-3 hours for the last 37,500 |
| 2 | Mark logos and icons (a picture shared by 3 or more recipes, or under 5 KB) and write what the app reads | notebook 11 section 5 (`CHECK_PHOTOS = True`): `data/processed/foodcom_photos.parquet` | minutes |
| 3 | Photo-matches-dish check (CLIP, CPU) | `PHOTO_SET=foodcom python -I scripts/recipe_photos/check_photos.py embed`, then `score` | a few hours for embed |
| 4 | Restart the app and look at a few Food.com recipes | `python -m streamlit run app/app.py` | minutes |
| 5 | Record the counts here and in notebook 11, then commit (no files from `data/raw`) | this file, `notebooks/README.md` | minutes |

Steps 1 and 3 can be stopped and resumed. Even with all of them, about 120,600 recipes (mostly CulinaryDB) have no
photo; the two plans below cover them.

### CulinaryDB: another round of free photos (planned 2026-10-26)

CulinaryDB has no photos and no recipe pages to take them from, so its recipes can only get a general photo of the
dish. The plan is another, wider lookup of free images, with the same rules as before: free licences only, a credit
and a link for each photo, the "A photo of X in general, not this recipe" label, and no scraping.

| # | Step | How |
|---|---|---|
| 1 | List the CulinaryDB dishes still without a photo, grouped by clean dish name and ranked by how many recipes each covers | `dish_names.clean_title` on the recipes with no `image_url` |
| 2 | Look them up again on Wikimedia Commons, wider than the first two rounds: the dish's Wikidata picture (P18), then a Commons category or file search on the dish name, then its main ingredient for single-ingredient dishes | `scripts/dish_photos/fetch_dish_photos.py --extend`, with the new lookups added |
| 3 | Try other free image sources where the licence allows reuse (for example Openverse, CC0 and CC BY only), each recorded in `docs/sources.md` before use | a new source switch in the same script |
| 4 | Run the photo-matches-dish check on every new photo and hide those below `PHOTO_CUTOFF` | `check_photos.py` |
| 5 | Review a sample by hand (`data/reference/dish_photo_review.csv`, `keep=no` hides a photo) and record the counts here | team |

This needs the internet; it waits until we have it again.

### Placeholder picture: "Cooking up a cool picture..." (planned 2026-10-26)

Recipes with no photo at all show one small pixel-art picture instead of an empty space, in the kitchen's style.

- **The picture:** a pan on a low flame with a little steam and a covered plate beside it, with the words
  "Cooking up a cool picture..." under it. It uses the same palette and pixel grid as the kitchens and icons, so it
  works in light and dark themes.
- **Where:** `design/pixel-art/make_pixel_art.py` gets an `icon_no_photo` (like `icon_map`), saved as a PNG under
  `app/` so the app loads it with no internet.
- **In the app:** when a recipe has no photo (none, hidden by the photo check, or a logo), the card and the dish page
  show the placeholder at the same size as a photo. The alt text and the caption say there is no photo yet, so no
  one mistakes it for the dish.
- **Checks:** a test that every recipe card gets either a photo or the placeholder; look at it in the browser at
  phone and desktop widths.

This needs no internet and can be built first.

## Steps, in order

| # | Step | How | Effort |
|---|---|---|---|
| 1 | **Show the whole photo** | The card shows the photo inside a fixed 4:3 frame with `object-fit: contain` on the panel's color, so the whole picture fits instead of filling (and cropping) the frame; small photos are not blown up past their size | Small (CSS) |
| 2 | **A bigger view on the dish page** | "About this dish" shows the photo at full width with its credit and link | Small |
| 3 | **Keep the photos in the full data** | Notebook 01 keeps `image_url` for Hugging Face and TheMealDB rows (about 38,000 recipes), with the source for the credit | Small, in the next notebook 01 rerun |
| 4 | **Find shared and logo pictures** | A notebook step downloads each photo once (paced, a local cache that is not committed), takes a small fingerprint (perceptual hash) and flags pictures used by many different recipes: those are logos or placeholders | Medium |
| 5 | **Check that the photo shows the dish** | An open image-text model run locally (CLIP, for example `openai/clip-vit-base-patch32`, MIT license) scores each photo against the dish's clean name (`dish_names.py`); a hand-checked sample of about 200 photos sets the cutoff. Below it, the card shows "No photo of this dish yet" (or the pixel-art dish, planner 0.5.2 item 5) and keeps the credit link | Medium; CPU is enough for 38,000 photos in a few hours |
| 6 | **"Wrong photo?" button** | Hides the photo for everyone after a team member confirms; saves only the recipe id, nothing about the person (privacy rules) | Medium; needs a small shared store |

Steps 1 and 2 fix the zoom at once; steps 4 and 5 hide unrelated photos; step 6 catches what the checks miss.

## Rules

- Only the photos the sources already give; no AI-made photos (RELIABILITY.md: a made-up picture of a real recipe
  misleads).
- Every photo keeps its credit and a link to the recipe's page; photos belong to their sources (research use).
- A hidden photo is never replaced by another recipe's photo.

## Open questions

- Who hand-checks the 200-photo sample (and the "Wrong photo?" reports)?
- Show the pixel-art dish or the "No photo yet" card when a photo is hidden?
