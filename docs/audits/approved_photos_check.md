# Approved dish photos: fetch and first check (2026-11-22)

The 1,739 Wikidata photos in `data/knowledge/media/approved_image_queue.json` were fetched (480 px thumbnails,
with the team's OK of 2026-11-22) to the git-ignored staging folder `data/raw/dish_photos_approved/` by
`scripts/dish_photos/fetch_approved.py`. **None is in the app yet**: `dish_photos.parquet` is unchanged until a
person checks the contact sheets and the `apply` step is finished.

## The numbers

| Step | Photos |
|---|---:|
| Fetched | 1,739 of 1,739 |
| Passed the photo check (CLIP: the photo matches its dish's name, ranks above other dishes, and is not a package or label) | 1,144 (66%) |
| Failed the photo check | 595 |

With the 1,144 that passed, once they are added: **rich dishes 505 → 619 (16% → 19%), fair 1,331 → 1,624,
thin 1,365 → 958** (the completeness score, as in [dish_completeness_report.md](dish_completeness_report.md),
which assumed all 1,739).

## The check by eye (Claude (AI), a sample)

The 109 contact sheets (16 photos each, the failed ones first) are in `data/raw/dish_photos_approved/sheets/`,
with `index.csv` naming each photo's dish.

- **Passed photos, 4 sheets read (61 photos: sheets 37, 52, 75 and 100, from just above the cutoff to the
  highest scores):** every photo shows its dish. Two are weak but right: Neccio (the chestnut crêpes being cooked
  over a fire) and Colatura di alici (a fish sauce, shown on spaghetti with its bottle). Nothing was added to
  `data/reference/dish_photo_review.csv`.
- **Failed photos, 2 sheets read (sheet 20, and the 3 failed photos on sheet 37):** the check rightly turned down
  packaged products (Mānuka honey jar, Hi-Chew, Ritter Sport). But on sheet 20 about 12 of 16 photos do show their
  dish (Ginataan, Salceson, Daktyla, Shrimp DeJonghe, Sarsiado, Szałot, Pampuchy); the wrong ones were Chinese
  steamed eggs (a soup with a dumpling), Pla ra (a basket of jars) and Berliner (a shop display). **The check is
  safe but strict:** a person could rescue many of the 595 failed photos sheet by sheet.

## What a person does next

1. Read the passed sheets (37 to 108; the sample above found no wrong photo) and add any wrong one to
   `data/reference/dish_photo_review.csv` (`keep` = `no`, with the reason).
2. Optionally read the failed sheets (0 to 37) and list the photos worth rescuing.
3. List the checked sheets in `data/reference/approved_photo_sheets_checked.txt` with who checked them, then ask
   for the `apply` step to be finished (it links each photo to its dish's recipes and appends to
   `dish_photos.parquet`), and rerun the quality reports.
